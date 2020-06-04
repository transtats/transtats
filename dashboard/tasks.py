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

from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from django.utils import timezone

from dashboard.constants import TS_JOB_TYPES, BRANCH_MAPPING_KEYS
from dashboard.managers.packages import PackagesManager
from dashboard.managers.jobs import JobTemplateManager, YMLBasedJobManager
from dashboard.managers.graphs import (
    GraphManager, ReportsManager, GeoLocationManager
)


logger = get_task_logger(__name__)


@periodic_task(
    run_every=(crontab(minute=0, hour='19')),
    name="sync_packages_with_platform",
    ignore_result=True
)
def task_sync_packages_with_platform():
    """
    sync all packages with translation platform
    """

    package_manager = PackagesManager()
    reports_manager = ReportsManager()

    def _sync_package(pkg):
        package_manager.sync_update_package_stats(pkg)

    all_packages = package_manager.get_packages().filter(
        platform_last_updated__lte=timezone.now() - timedelta(hours=18)
    ).order_by('platform_url')
    for package in all_packages:
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


@periodic_task(
    run_every=(crontab(minute=0, hour='7')),
    name="sync_packages_with_build_system",
    ignore_result=True
)
def task_sync_packages_with_build_system():
    """
    sync all packages with build system
    """

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

    def _sync_build_system(template, params):

        if package_manager.is_package_build_latest(params):
            return

        t_params = template.job_template_params
        if len(t_params) == len(params):
            job_data = {field.upper(): param
                        for field, param in zip(t_params, params)}
            job_data.update({
                'YML_FILE': yaml.dump(template.job_template_json,
                                      default_flow_style=False).replace("\'", "")
            })
            job_data.update({'SCRATCH': True})

            temp_path = 'false/{0}/'.format('-'.join(params))
            job_manager = YMLBasedJobManager(
                **job_data, **{'params': [p.upper() for p in t_params],
                               'type': TS_JOB_TYPES[3]},
                **{'active_user_email': 'system@transtats.org'},
                **{'sandbox_path': temp_path},
                **{'job_log_file': temp_path + '.log'}
            )

            try:
                if os.path.isdir(temp_path):
                    shutil.rmtree(temp_path)
                os.mkdir(temp_path)
                job_manager.execute_job()
            except Exception as e:
                # pass for now
                pass
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
