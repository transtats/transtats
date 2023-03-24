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
import time
from collections import OrderedDict

from dashboard.jobs_framework import JobCommandBase


class Filter(JobCommandBase):
    """Handles all operations for FILTER Command"""

    @staticmethod
    def _determine_podir(files: list, domain: str) -> (bool, int):
        """
        PODIRs can have a set of folder hierarchy
            - locale/ru/{gettext_domain}.po
            - locale/ru/LC_MESSAGES/{gettext_domain}.mo
        """
        if not domain:
            return False, 0
        for file in files:
            file_path_parts = file.split(os.sep)
            expected_domain = file_path_parts[-1].split('.')[0]
            if expected_domain != domain:
                return False, 0
            if file_path_parts[-3] == 'locale':
                return True, -2
            elif file_path_parts[-4] == 'locale' and \
                    file_path_parts[-2] == 'LC_MESSAGES':
                return True, -3
        return False, 0

    @staticmethod
    def _test_multiple_trans_dir(t_files, is_podir):
        trans_dirs = []
        for trans_file in t_files:
            trans_dir = trans_file.rsplit(os.sep, 1)[0]
            if is_podir:
                trans_dir = trans_file.rsplit(os.sep, 3)[0]
            if trans_dir not in trans_dirs:
                trans_dirs.append(trans_dir)
        return len(trans_dirs) > 1, trans_dirs

    def files(self, input, kwargs):
        """Filter files from tarball"""
        file_ext = 'po'
        result_dict = {}
        if input.get('trans_file_ext') and input['trans_file_ext'] != file_ext:
            file_ext = input['trans_file_ext'].lstrip(".")
        if kwargs.get('ext'):
            file_ext = kwargs['ext'].lower()

        task_subject = "Filter %s files" % file_ext.upper()
        task_log = OrderedDict()

        if input.get('patches', []):
            time.sleep(1)

        try:
            trans_files = []
            search_dir = input['extract_dir'] if 'extract_dir' in input else input['src_tar_dir']
            if kwargs.get('dir') and isinstance(kwargs.get('dir'), str):
                search_dir = os.path.join(search_dir, *kwargs['dir'].split(os.sep))
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.%s' % file_ext):
                        trans_files.append(os.path.join(root, file))
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in filtering {} files: {}'.format(file_ext, str(e))
            ))
        else:
            is_podir, locale_index = self._determine_podir(trans_files, kwargs.get('domain'))
            is_multiple_trans_dir, trans_dirs = self._test_multiple_trans_dir(trans_files, is_podir)
            if is_multiple_trans_dir:
                trans_dirs = [trans_dir.replace(search_dir, "") if trans_dir.replace(search_dir, "") else trans_dir
                              for trans_dir in trans_dirs]
                task_log.update(self._log_task(
                    input['log_f'], task_subject, [t_dir.lstrip(os.sep) for t_dir in trans_dirs],
                    text_prefix="[WARN] Translations are found in {} directories. "
                                "Setting 'dir' may help.".format(len(trans_dirs))
                ))
            task_log.update(self._log_task(
                input['log_f'], task_subject, trans_files,
                text_prefix='%s %s files filtered' % (len(trans_files), file_ext.upper())
            ))
            result_dict.update({'trans_files': trans_files, 'file_ext': file_ext})
            if is_podir:
                result_dict.update(dict(podir=True))
                result_dict.update(dict(locale_index=locale_index))
        return result_dict, {task_subject: task_log}
