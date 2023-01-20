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
from subprocess import Popen, PIPE

from dashboard.jobs_framework import JobCommandBase


class Generate(JobCommandBase):
    """Handles all operations for GENERATE Command"""

    def _verify_command(self, command):
        """
        verify given command against commands.acl file
        :param command: str
        :return: filtered command
        """
        sh_commands = [command]
        if ';' in command:
            sh_commands = [cmd.strip() for cmd in command.split(';')]
        elif '&&' in command:
            sh_commands = [cmd.strip() for cmd in command.split('&&')]
        with open(os.path.join(
                'dashboard', 'jobs_framework', 'commands.acl'), 'r'
        ) as acl_values:
            allowed_base_commands = acl_values.read().splitlines()
            not_allowed = [cmd for cmd in sh_commands if cmd.split()[0] not in allowed_base_commands]
            if not_allowed and len(not_allowed) >= 1:
                raise Exception('Invalid command: %s' % not_allowed[0])
        return command

    def pot_file(self, input, kwargs):
        """
        Generates POT file
            as per the given command
        """
        task_subject = "Generate POT File"
        task_log = OrderedDict()
        pot_file_path = ''

        if kwargs.get('cmd'):
            command = self._verify_command(kwargs['cmd'])
            po_dir = self.find_dir('po', input['src_tar_dir'])
            if not po_dir:
                po_dir = self.find_dir('locale', input['src_tar_dir']) or ''
            pot_file = os.path.join(
                po_dir, '%s.pot' % kwargs.get('domain', input['package'])
            )
            if os.path.exists(pot_file) and kwargs.get('overwrite'):
                os.unlink(pot_file)
            try:
                os.chdir(input['src_tar_dir'])
                generate_pot = Popen(command, stdout=PIPE, shell=True)
                output, error = generate_pot.communicate()
            except Exception as e:
                os.chdir(input['base_dir'])
                task_log.update(self._log_task(
                    input['log_f'], task_subject,
                    'POT file generation failed %s' % str(e)
                ))
            else:
                os.chdir(input['base_dir'])
                if os.path.isfile(pot_file):
                    pot_file_path = pot_file
                    task_log.update(self._log_task(
                        input['log_f'], task_subject, output.decode("utf-8"),
                        text_prefix='POT file generated successfully. [ %s.pot ]' %
                                    kwargs.get('domain', input['package'])
                    ))
                else:
                    error_response = 'POT file generation failed with command: %s' % command
                    task_log.update(self._log_task(
                        input['log_f'], task_subject, error_response)
                    )
                    raise Exception(error_response)
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, 'Command to generate POT missing.'
            ))
        return {'src_pot_file': pot_file_path,
                'i18n_domain': kwargs.get('domain', input['package'])}, \
               {task_subject: task_log}
