# Copyright 2023 Red Hat, Inc.
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

from collections import OrderedDict

from dashboard.jobs_framework import JobCommandBase


class Get(JobCommandBase):
    """Handles all operations for GET Command"""
    def latest_build_info(self, input, kwargs):
        """Fetch latest build info from koji"""
        task_subject = "Latest Build Details"
        task_log = OrderedDict()

        package = input.get('pkg_downstream_name') or input.get('package')
        builds = self.api_resources.build_info(
            hub_url=input.get('hub_url'), tag=input.get('build_tag'), pkg=package
        )
        if len(builds) > 0:
            task_log.update(self._log_task(input['log_f'], task_subject, str(builds[0])))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'No build details found for %s.' % input.get('build_tag')
            ))

        return {'builds': builds}, {task_subject: task_log}

    def task_info(self, input, kwargs):
        """Fetch task info and results"""
        task_subject = "Task Details"
        task_log = OrderedDict()

        task_info = self.api_resources.task_info(
            hub_url=input.get('hub_url'), task_id=kwargs.get('task_id')
        )
        task_result = self.api_resources.task_result(
            hub_url=input.get('hub_url'), task_id=kwargs.get('task_id')
        )

        if kwargs.get('task_id') != task_info.get('id'):
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'No task info found for id %s.' % kwargs.get('task_id')
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, str({**task_info, **task_result})
            ))
        if task_info.get('id'):
            task_result.update(dict(task_id=task_info['id']))

        return {'task': task_result}, {task_subject: task_log}
