# Copyright 2020 Red Hat, Inc.
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

from collections import (namedtuple, OrderedDict)

http_methods = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS')
media_types = ('application/json', 'application/xml')

# based on https://docs.gitlab.com/ee/api/api_resources.html
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'ProjectID': OrderedDict([
        ('/projects/{owner}%2F{repo}', {
            http_methods[0]: {
                'path_params': ('owner', 'repo'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ListBranches': OrderedDict([
        ('/projects/{id}/repository/branches', {
            http_methods[0]: {
                'path_params': ('id', ),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
project_id = resource('ProjectID', list(resource_config_dict['ProjectID'].keys())[0], http_methods[0])
list_branches = resource('ListBranches', list(resource_config_dict['ListBranches'].keys())[0], http_methods[0])

# Transtats Github support operates on resources listed here
resources = {
    'project_id': project_id,
    'list_branches': list_branches,
}
