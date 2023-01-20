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

import os
from collections import OrderedDict
from shutil import copy2

from dashboard.jobs_framework import JobCommandBase


class Copy(JobCommandBase):
    """Handles all operations for COPY Command"""

    def downloaded_files(self, input, kwargs):
        """Copy downloaded files to provided dir"""

        task_subject = "Copy Downloaded Files"
        task_log = OrderedDict()

        if not kwargs.get('dir'):
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Dir value was empty, copying to root.'
            ))
            kwargs['dir'] = ''

        # copy files
        copy_target_dir = os.path.join(input['src_tar_dir'], kwargs['dir'])
        downloaded_translation_files = input['trans_files']

        copied_files = []
        for trans_file in downloaded_translation_files:
            source = os.path.join(input['base_dir'], trans_file)
            destination_dir = os.path.join(input['base_dir'], copy_target_dir)
            copied_file_path = copy2(source, destination_dir)
            copied_file = list(filter(None, copied_file_path.split(os.sep)))[-1]
            copied_files.append(os.path.join(kwargs['dir'], copied_file))

        task_log.update(self._log_task(
            input['log_f'], task_subject, copied_files,
            text_prefix=f"{len(copied_files)} files copied to the repository."
        ))
        return {'copied_files': copied_files,
                'repo_dir': input['src_tar_dir']}, {task_subject: task_log}
