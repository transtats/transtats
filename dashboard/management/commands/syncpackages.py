# Copyright 2018 Red Hat, Inc.
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

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dashboard.constants import TS_JOB_TYPES, BRANCH_MAPPING_KEYS
from dashboard.managers.packages import PackagesManager
from dashboard.managers.graphs import (GraphManager, ReportsManager)
from dashboard.managers.jobs import (
    JobTemplateManager, YMLBasedJobManager
)


class Command(BaseCommand):

    help = 'Sync packages with their respective translation platform.'

    graph_manager = GraphManager()
    package_manager = PackagesManager()
    reports_manager = ReportsManager()
    job_template_manager = JobTemplateManager()

    def _sync_package(self, pkg):
        self.package_manager.sync_update_package_stats(pkg)

    def sync_with_platform(self):

        all_packages = self.package_manager.get_packages().filter(
            platform_last_updated__lte=timezone.now() - timedelta(hours=6)
        ).order_by('platform_url')
        for package in all_packages:
            th = threading.Thread(
                target=self._sync_package, args=(package.package_name, )
            )
            th.start()
            th.join()
            time.sleep(2)

        self.reports_manager.analyse_releases_status()
        self.reports_manager.analyse_packages_status()

    def _update_diff(self, package):
        try:
            package_stats = self.graph_manager.get_trans_stats_by_package(
                package.package_name
            )
            self.graph_manager.package_manager.calculate_stats_diff(
                package.package_name, package_stats,
                package.release_branch_mapping_json
            )
        except Exception:
            # pass for now
            pass

    def _sync_build_system(self, template, params):

        if self.package_manager.is_package_build_latest(params):
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
                os.rmdir(temp_path)

    def sync_with_build_system(self):

        job_template = None
        all_packages = self.package_manager.get_packages().filter(
            release_branch_mapping__isnull=False
        )
        job_templates = self.job_template_manager.get_job_templates(
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
                        target=self._sync_build_system,
                        args=(job_template, candidate,)
                    )
                    th.start()
                    th.join()
                    time.sleep(5)

                self._update_diff(package)

        self.reports_manager.analyse_packages_status()
        self.reports_manager.refresh_stats_required_by_territory()

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '--platform',
            action='store_true',
            help='Sync packages with translation platform only.',
        )

        parser.add_argument(
            '--build-system',
            action='store_true',
            help='Sync packages with build system only.',
        )

    def handle(self, *args, **options):

        cmd_combinations_options = [
            'platform',
            'build_system',
            'default_both'
        ]

        cmd_combinations = {
            cmd_combinations_options[0]: self.sync_with_platform,
            cmd_combinations_options[1]: self.sync_with_build_system,
            cmd_combinations_options[2]: [self.sync_with_platform,
                                          self.sync_with_build_system]
        }

        if options.get(cmd_combinations_options[0]):
            cmd_combinations.get(cmd_combinations_options[0])()
        elif options.get(cmd_combinations_options[1]):
            cmd_combinations.get(cmd_combinations_options[1])()
        else:
            [m() for m in cmd_combinations.get(cmd_combinations_options[2])]
