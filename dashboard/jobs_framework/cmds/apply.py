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
from shlex import split
from shutil import copy2
from subprocess import Popen, PIPE
from collections import OrderedDict

from dashboard.jobs_framework import JobCommandBase


class Apply(JobCommandBase):
    """Handles all operations for APPLY Command"""

    def _apply_prep(self, input, prep_section, tar_dir, w_log, sub):
        file_ext = '.po'
        prep_steps = []
        relevant_prep_steps = {}
        po_related_sources = {i: j for i, j in input['spec_obj'].sources_dict.items() if file_ext in j}

        for i, j in po_related_sources.items():
            source_step = [step for step in prep_section if i.upper() in step]
            if len(source_step) > 0:
                relevant_prep_steps[j] = source_step[0]

        for i, j in relevant_prep_steps.items():
            src_po = [po for po in input['src_translations'] if i in po]
            if len(src_po) > 0:
                cmd_parts = j.split()
                if cmd_parts[0] in ('cp', 'install') and file_ext in cmd_parts[-1]:
                    copy_args = src_po[0], os.path.join(tar_dir, cmd_parts[-1])
                    prep_steps.append("{0} {1} {2}".format(cmd_parts[0], *copy_args))
                    copy2(*copy_args)

        if len(prep_steps) > 0:
            w_log.update(self._log_task(
                input['log_f'], sub, prep_steps,
                text_prefix='%s prep command(s) ran' % len(prep_steps)
            ))

    def patch(self, input, kwargs):

        task_subject = "Apply Patches"
        task_log = OrderedDict()

        tar_dir = {'src_tar_dir': input['src_tar_dir']}

        patches_from_spec = input['spec_obj'].patches
        if patches_from_spec:
            tar_dir.update(dict(patches=patches_from_spec))

        if input['src_translations']:
            s_sections = input['spec_sections']
            self._apply_prep(
                input, s_sections.getSection('prep'), input['src_tar_dir'],
                task_log, task_subject
            )

        try:
            patches = []
            src_trans = input['src_translations']
            for root, dirs, files in os.walk(input['extract_dir']):
                for file in files:
                    if file.endswith('.patch'):
                        patches.append(os.path.join(root, file))

            if not patches and not src_trans:
                task_log.update(self._log_task(input['log_f'], task_subject, 'No patches found.'))
                return tar_dir, {task_subject: task_log}

            # apply patches
            [copy2(patch, input['src_tar_dir']) for patch in patches]
            os.chdir(input['src_tar_dir'])
            for patch in patches:
                err_msg = "Perhaps you used the wrong -p"
                command_std_output = "Perhaps you used the wrong -p or --strip option?"
                p_value = 0
                p_value_limit = 5
                while err_msg in command_std_output and p_value < p_value_limit:
                    command = "patch -p" + str(p_value) + " -i " + patch.split('/')[-1]
                    command = split(command)
                    patch_output = Popen(command, stdout=PIPE)
                    command_std_output = patch_output.stdout.read().decode("utf-8")
                    patch_output.kill()
                    p_value += 1
        except Exception as e:
            os.chdir(input['base_dir'])
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in applying patches: %s' % str(e)
            ))
        else:
            os.chdir(input['base_dir'])
            task_log.update(self._log_task(
                input['log_f'], task_subject, patches,
                text_prefix='%s patches applied' % len(patches)
            ))

        return tar_dir, {task_subject: task_log}
