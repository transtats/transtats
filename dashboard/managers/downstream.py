# Copyright 2017 Red Hat, Inc.
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

import io
import os
import shutil
import time
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
# django
from django.conf import settings
from django.utils import timezone
# dashboard
from dashboard.constants import JOB_EXEC_TYPES
from dashboard.engine.action_mapper import ActionMapper
from dashboard.engine.ds import TaskList
from dashboard.engine.parser import YMLPreProcessor, YMLJobParser
from dashboard.managers.base import BaseManager
from dashboard.managers.inventory import PackagesManager

__all__ = ['DownstreamManager']


class DownstreamManager(BaseManager):
    """
    Packages Downstream Manager
    """

    sandbox_path = 'dashboard/sandbox/'
    job_log_file = sandbox_path + 'downstream.log'

    package_manager = PackagesManager()

    def _bootstrap(self, build_system):
        try:
            release_streams = \
                self.package_manager.get_release_streams(built=build_system)
            release_stream = release_streams.get()
        except Exception as e:
            self.app_logger(
                'ERROR', "Release stream could not be found, details: " + str(e)
            )
            raise Exception('Build Server URL could NOT be located for %s.' % self.buildsys)
        else:
            self.hub_url = release_stream.relstream_server

    def _save_result_in_db(self, stats_dict):
        if not self.package_manager.is_package_exist(package_name=self.package):
            raise Exception("Stats NOT saved. Package does not exist.")
        try:
            self.package_manager.save_version_stats(
                self.package, self.buildsys + ' - ' + self.tag, stats_dict, self.buildsys
            )
            # If its for rawhide, update downstream sync time for the package
            if self.tag == 'rawhide':
                self.package_manager.update_package(self.package, {
                    'downstream_lastupdated': timezone.now()
                })
        except Exception as e:
            self.app_logger(
                'ERROR', "Package could not be updated, details: " + str(e)
            )
            raise Exception('Stats could NOT be saved in db.')

    def _wipe_workspace(self):
        """
        This makes sandbox clean for a new job to run
        """
        # remove log file if exists
        if os.path.exists(self.job_log_file):
            os.remove(self.job_log_file)
        for file in os.listdir(self.sandbox_path):
            file_path = os.path.join(self.sandbox_path, file)
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                elif os.path.isfile(file_path) and not file_path.endswith('.py') \
                        and '.log.' not in file_path:
                    os.unlink(file_path)
            except Exception as e:
                pass

    @staticmethod
    def job_suffix(*args):
        return "-".join(args)

    def execute_job(self):
        """
        1. PreProcess YML and replace variables with input_values
            - Example: %PACKAGE_NAME%
        2. Parse processed YML and build Job object
        3. Select data structure for tasks and instantiate one
            - Example: Linked list should be used for sequential tasks
        3. Discover namespace and method for each task and fill in TaskNode
        4. Perform actions (execute tasks) and return responses
        """
        self._wipe_workspace()

        yml_preprocessed = YMLPreProcessor(self.YML_FILE, **{
            'PACKAGE_NAME': self.PACKAGE_NAME,
            'BUILD_SYSTEM': self.BUILD_SYSTEM,
            'BUILD_TAG': self.BUILD_TAG
        }).output

        if yml_preprocessed:
            self.job_base_dir = os.path.dirname(settings.BASE_DIR)
            yml_job = YMLJobParser(yml_stream=io.StringIO(yml_preprocessed))
            self.package = yml_job.package
            self.buildsys = yml_job.buildsys
            self.tag = yml_job.tags[0] if len(yml_job.tags) > 0 else None
            suffix = self.job_suffix(self.package, self.buildsys, self.tag)
            self._bootstrap(self.buildsys)
            # for sequential jobs, tasks should be pushed to linked list
            # and output of previous task should be input for next task
            if JOB_EXEC_TYPES[0] in yml_job.execution:
                self.tasks_ds = TaskList()
            else:
                raise Exception('%s exec type is NOT supported yet.' % yml_job.execution)
            if self.tag and self.package and self.hub_url and self.job_base_dir:
                tasks = yml_job.tasks
                for task in tasks:
                    self.tasks_ds.add_task(task)
                log_file = self.job_log_file + "." + suffix
                if os.path.exists(log_file):
                    os.unlink(log_file)
                action_mapper = ActionMapper(
                    self.tasks_ds, self.tag, self.package,
                    self.hub_url, self.job_base_dir, self.buildsys, log_file
                )
                action_mapper.set_actions()
                # lets execute collected tasks
                try:
                    action_mapper.execute_tasks()
                except Exception as e:
                    raise Exception(e)
                finally:
                    action_mapper.clean_workspace()
                    time.sleep(4)
                if action_mapper.result and not getattr(self, 'DRY_RUN', None):
                    self._save_result_in_db(action_mapper.result)
                if os.path.exists(log_file):
                    os.unlink(log_file)
