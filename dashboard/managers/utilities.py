# Copyright 2016 Red Hat, Inc.
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

# Common functions/utilities

# dashboard
from ..services.constants import TRANSPLATFORM_ENGINES


def parse_project_details_json(engine, json_dict):
    """
    Parse project details json
    """
    project = ''
    versions = []
    if engine == TRANSPLATFORM_ENGINES[0]:
        project = json_dict.get('slug')
        versions = [version.get('slug') for version in json_dict.get('resources', [])]
    elif engine == TRANSPLATFORM_ENGINES[1]:
        project = json_dict.get('id')
        versions = [version.get('id') for version in json_dict.get('iterations', [])]
    return project, versions
