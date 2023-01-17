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
import tarfile
from shlex import split
from subprocess import Popen, PIPE, call
from collections import OrderedDict

from dashboard.jobs_framework import JobCommandBase


class Unpack(JobCommandBase):
    """Handles all operations for UNPACK Command"""

    def srpm(self, input, kwargs):
        """
        SRPM is a headers + cpio file
            - its extraction currently is dependent on cpio command
        """

        task_subject = "Unpack SRPM"
        task_log = OrderedDict()

        try:
            command = "rpm2cpio " + os.path.join(
                input['base_dir'], input['srpm_path']
            )
            command = split(command)
            rpm2cpio = Popen(command, stdout=PIPE)
            extract_dir = os.path.join(self.sandbox_path, input['package'])
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            command = "cpio -idm -D %s" % extract_dir
            command = split(command)
            call(command, stdin=rpm2cpio.stdout)
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'SRPM Extraction Failed %s' % str(e)
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, os.listdir(extract_dir),
                text_prefix='SRPM Extracted Successfully'
            ))
            return {'extract_dir': extract_dir}, {task_subject: task_log}

    def _determine_tar_dir(self, params):
        for root, dirs, files in os.walk(params['extract_dir']):
            for directory in dirs:
                if directory == params['package']:
                    return os.path.join(root, directory)
            return root

    def tarball(self, input, kwargs):
        """Untar source tarball"""

        task_subject = "Unpack tarball"
        task_log = OrderedDict()

        try:
            src_tar_dir = None
            with tarfile.open(input['src_tar_file']) as tar_file:
                tar_members = tar_file.getmembers()
                if len(tar_members) > 0:
                    src_tar_dir = os.path.join(
                        input['extract_dir'], tar_members[0].get_info().get('name', '')
                    )
                tar_file.extractall(path=input['extract_dir'])

            if input['related_tarballs']:
                for r_tarball in input['related_tarballs']:
                    with tarfile.open(r_tarball) as tar_file:
                        tar_file.extractall(path=src_tar_dir)

            # specific operation as per gem files
            if input['src_tar_file'].endswith('.gem') and tar_members and \
                    'data.tar.gz' in [tar.get_info().get('name', '') for tar in tar_members]:
                gem_data_tar_file = os.path.join(input['extract_dir'], 'data.tar.gz')
                src_tar_dir = os.path.join(input['extract_dir'], 'data')
                with tarfile.open(gem_data_tar_file) as tar_file:
                    tar_file.extractall(path=src_tar_dir)

        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Tarball Extraction Failed %s' % str(e)
            ))
        else:
            if not os.path.isdir(src_tar_dir):
                src_tar_dir = self._determine_tar_dir(input)
            task_log.update(self._log_task(
                input['log_f'], task_subject, os.listdir(src_tar_dir),
                text_prefix='Tarball [ %s ] Extracted Successfully' % input['src_tar_file'].split('/')[-1]
            ))
            return {'src_tar_dir': src_tar_dir, 'src_translations': input['src_translations'],
                    'spec_obj': input['spec_obj'], 'spec_sections': input['spec_sections']},\
                   {task_subject: task_log}
