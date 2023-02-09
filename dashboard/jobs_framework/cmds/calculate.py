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
import polib
from subprocess import Popen, PIPE
from collections import OrderedDict

from dashboard.jobs_framework import JobCommandBase


class Calculate(JobCommandBase):
    """Handles all operations for CALCULATE Command"""

    def stats(self, input, kwargs):
        """Calculate stats from filtered translations"""

        task_subject = "Calculate Translation Stats"
        task_log = OrderedDict()

        try:
            trans_stats = {}
            if input.get('build_system') and input.get('build_tag'):
                trans_stats['id'] = input['build_system'] + ' - ' + input['build_tag']
            elif input.get('upstream_repo_url'):
                trans_stats['id'] = 'Upstream'
            trans_stats['stats'] = []
            for po_file in input['trans_files']:
                try:
                    po = polib.mofile(po_file) if po_file.endswith('mo') else polib.pofile(po_file)
                except Exception as e:
                    task_log.update(self._log_task(
                        input['log_f'], task_subject,
                        'Something went wrong while parsing %s: %s' % (po_file, str(e))
                    ))
                else:
                    temp_trans_stats = {}
                    temp_trans_stats['unit'] = "MESSAGE"
                    temp_trans_stats['locale'] = po_file.split(os.sep)[input.get('locale_index', -2)] \
                        if input.get('podir') else po_file.split(os.sep)[-1].split('.')[0]
                    temp_trans_stats['translated'] = len(po.translated_entries())
                    temp_trans_stats['untranslated'] = len(po.untranslated_entries())
                    temp_trans_stats['fuzzy'] = len(
                        [f_entry for f_entry in po.fuzzy_entries() if not f_entry.obsolete]
                    )
                    temp_trans_stats['total'] = temp_trans_stats['translated'] + \
                        temp_trans_stats['untranslated'] + temp_trans_stats['fuzzy']
                    trans_stats['stats'].append(temp_trans_stats.copy())
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in calculating stats: %s' % str(e)
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, str(trans_stats), text_prefix='Calculated Stats'
            ))
            return {'trans_stats': trans_stats}, {task_subject: task_log}

    def diff(self, input, kwargs):
        """Calculate diff between two"""
        task_subject = "Calculate Differences"
        task_log = OrderedDict()
        diff_lines = ''
        diff_msg = ''
        diff_count = 0

        try:
            src_pot = input.get('src_pot_file')
            platform_pot = input.get('platform_pot_path')

            src_pot_obj, platform_pot_obj = polib.pofile(src_pot), polib.pofile(platform_pot)
            src_pot_dict = {ut_entry.msgid: ut_entry for ut_entry in src_pot_obj.untranslated_entries()}
            platform_pot_dict = {ut_entry.msgid: ut_entry
                                 for ut_entry in platform_pot_obj.untranslated_entries()}
            diff_entries = {k: src_pot_dict[k] for k in set(src_pot_dict) - set(platform_pot_dict)}
            if not diff_entries:
                task_log.update(self._log_task(
                    input['log_f'], task_subject, "No new or updated messages found."
                ))
            else:
                diff_msg = "".join(["line %s\n%s\n%s\n\n" %
                                    (str(entry.linenum), "\n".join(
                                        [" ".join(i) for i in entry.occurrences]
                                    ), entry.msgid) for msg, entry in diff_entries.items()])
                diff_count = len(set(diff_entries))
            if src_pot and platform_pot:
                git_diff_command = 'git diff --no-index %s %s' % (platform_pot, src_pot)
                calculated_diff = Popen(git_diff_command, stdout=PIPE, shell=True)
                output, error = calculated_diff.communicate()
                diff_lines = output.decode("utf-8")
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in calculating diff: %s' % str(e)
            ))
        else:
            if diff_count > 0:
                task_log.update(self._log_task(
                    input['log_f'], task_subject, '%s messages differ.\n\n%s' % (str(diff_count), diff_msg),
                    text_prefix='Calculated Diff'
                ))
        return {'pot_diff': diff_msg, 'full_diff': diff_lines, 'diff_count': diff_count}, {task_subject: task_log}
