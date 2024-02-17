# Copyright 2019 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import shutil
import time
import threading
import yaml

from datetime import timedelta
from random import randrange

from celery import shared_task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from fedora_messaging import config as fedmsg_config
from fedora_messaging import api as fedmsg_api
from fedora_messaging import message as fedmsg_msg

from dashboard.constants import (
    TS_JOB_TYPES, BRANCH_MAPPING_KEYS, WEBLATE_SLUGS, SYS_EMAIL_ADDR
)
from dashboard.managers.packages import PackagesManager
from dashboard.managers.jobs import JobTemplateManager, YMLBasedJobManager
from dashboard.managers.graphs import (
    GraphManager, ReportsManager, GeoLocationManager
)
from dashboard.managers.pipelines import CIPipelineManager


logger = get_task_logger(__name__)


@shared_task()
def task_sync_packages_with_platform():
    """sync all packages with translation platform"""

    logger.info("Starting task_sync_packages_with_platform ..")

    package_manager = PackagesManager()
    reports_manager = ReportsManager()
    pipeline_manager = CIPipelineManager()

    def _sync_package(pkg):
        package_manager.sync_update_package_stats(pkg)
        package_manager.fetch_latest_builds(pkg)
        pipeline_manager.refresh_pkg_pipelines(pkg)

    all_packages = []

    packages_except_weblate_fedora = package_manager.get_packages().filter(
        platform_last_updated__lte=timezone.now() - timedelta(hours=12)
    ).order_by('platform_url').exclude(platform_slug_id=WEBLATE_SLUGS[1])

    weblate_fedora_packages = package_manager.get_packages().filter(
        platform_last_updated__lte=timezone.now() - timedelta(hours=22),
        platform_slug_id=WEBLATE_SLUGS[1]
    ).order_by('platform_url')

    if packages_except_weblate_fedora:
        all_packages.extend(packages_except_weblate_fedora)
    if weblate_fedora_packages:
        all_packages.extend(weblate_fedora_packages)

    for package in all_packages:
        logger.info("Attempting sync for {}.".format(package))

        th = threading.Thread(
            target=_sync_package, args=(package.package_name,)
        )
        th.start()
        th.join()
        time.sleep(randrange(5, 10))

    logger.info("%s Packages sync'd with Translation Platform" % len(all_packages))
    if reports_manager.analyse_releases_status():
        logger.info("Releases Summary Updated")
    if reports_manager.analyse_packages_status():
        logger.info("Packages Summary Updated")


@shared_task()
def task_sync_packages_with_build_system():
    """sync all packages with build system"""

    logger.info("Starting task_sync_packages_with_build_system ..")

    package_manager = PackagesManager()
    graph_manager = GraphManager()
    reports_manager = ReportsManager()
    job_template_manager = JobTemplateManager()
    location_manager = GeoLocationManager()

    def _update_diff(package):
        try:
            package_stats = graph_manager.get_trans_stats_by_package(
                package.package_name
            )
            graph_manager.package_manager.calculate_stats_diff(
                package.package_name, package_stats,
                package.release_branch_mapping_json
            )
        except Exception:
            # pass for now
            pass

    def _post_fedora_messaging(package_name, build_sys, build_tag, job_uuid):
        """Post to fedora messaging system."""
        server_domain = "http://localhost:8080"
        if os.environ.get("DEPLOY_ENV") == "prod":
            server_domain = "https://transtats.fedoraproject.org"
        elif os.environ.get("DEPLOY_ENV") == "staging":
            server_domain = "https://transtats.stg.fedoraproject.org"

        fedmsg_config.conf.load_config("deploy/docker/conf/transtats.toml")
        job_url = f"{server_domain}{reverse('log-detail', args=[job_uuid])}"
        api_url = f"{server_domain}{reverse('api_job_log', args=[job_uuid])}"
        topic_msg = fedmsg_msg.Message(
            topic=u'org.fedoraproject.transtats.build_system.sync_job_run',
            headers={u'package': package_name,
                     u'build_system': build_sys,
                     u'build_tag': build_tag},
            body={u'url': job_url, u'api_url': api_url}
        )
        fedmsg_api.publish(topic_msg)

    def _sync_build_system(template, params):

        if package_manager.is_package_build_latest(params):
            return

        # TODO: derive latest releases from ReleaseManager
        is_job_logged: bool = params[2] in ('f41', 'f42', 'f43')

        t_params = template.job_template_params
        if len(t_params) == len(params):
            job_data = {field.upper(): param
                        for field, param in zip(t_params, params)}
            job_data.update({
                'YML_FILE': yaml.dump(template.job_template_json,
                                      default_flow_style=False).replace("\'", "")
            })

            if is_job_logged:
                job_data.update({'SCRATCH': False})
            else:
                job_data.update({'SCRATCH': True})

            temp_path = 'false/{0}/'.format('-'.join(params))
            job_manager = YMLBasedJobManager(
                **job_data, **{'params': [p.upper() for p in t_params],
                               'type': TS_JOB_TYPES[3]},
                **{'active_user_email': SYS_EMAIL_ADDR},
                **{'sandbox_path': temp_path},
                **{'job_log_file': temp_path + '.log'}
            )

            try:
                if os.path.isdir(temp_path):
                    shutil.rmtree(temp_path)
                os.mkdir(temp_path)
                job_uuid = job_manager.execute_job()
            except Exception as e:
                # pass for now
                pass
            else:
                if settings.FAS_AUTH and is_job_logged:
                    _post_fedora_messaging(params[0], params[1], params[2], job_uuid)
            finally:
                shutil.rmtree(temp_path)

    job_template = None
    all_packages = package_manager.get_packages().filter(
        release_branch_mapping__isnull=False
    )
    job_templates = job_template_manager.get_job_templates(
        job_template_type=TS_JOB_TYPES[3]
    )
    if job_templates:
        job_template = job_templates.first()

    if all_packages and job_template:
        for package in all_packages:
            logger.info("Attempting sync for {}.".format(package))

            candidates = []
            mapping = package.release_branch_mapping_json or {}

            for release, map_dict in mapping.items():
                candidates.append((
                    package.package_name,
                    map_dict.get(BRANCH_MAPPING_KEYS[1]),
                    map_dict.get(BRANCH_MAPPING_KEYS[2])
                ))

            for candidate in candidates:
                th = threading.Thread(
                    target=_sync_build_system,
                    args=(job_template, candidate,)
                )
                th.start()
                th.join()
                time.sleep(randrange(5, 10))

            _update_diff(package)

    logger.info("%s Packages sync'd with Build System" % len(all_packages))
    if reports_manager.analyse_packages_status():
        logger.info("Packages Summary Updated")
    time.sleep(5)
    if reports_manager.refresh_stats_required_by_territory():
        logger.info("Location Summary Updated")
    time.sleep(5)
    if location_manager.save_territory_build_system_stats():
        logger.info("Territory Summary Updated")
