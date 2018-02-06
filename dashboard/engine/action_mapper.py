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

__all__ = ['ActionMapper']


class ActionMapper(object):
    """
    YML Parsed Objects to Actions Mapper
    """
    COMMANDS = [
        'GET',          # Call some method
        'DOWNLOAD',     # Download some resource
        'UNPACK',       # Extract an archive
        'LOAD',         # Load into python object
        'FILTER',       # Filter files recursively
        'CALCULATE'     # Apply some maths/formulae
    ]

    def __init__(self, tasks_structure):
        self.tasks = tasks_structure

    @property
    def actions(self):
        actions = []
        actions_dict = {
            'get: latest build info': 'get_latest_build',
            'download: SRPM': 'fetch_SRPM',
            'unpack: SRPM': 'unpack_SRPM',
            'load: Spec file': 'load_spec_file',
            'unpack: tarball': 'untar_tarball',
            'filter: PO files': 'filter_translations',
            'calculate: Stats': 'calculate_stats'
        }

        count = 0
        current_node = self.tasks.head

        while current_node is not None:
            count += 1
            action = "%s: %s" % (current_node.command,
                                 current_node.task)
            executable = actions_dict.get(action)
            if executable:
                actions.append(executable)
            current_node = current_node.next
        return actions
