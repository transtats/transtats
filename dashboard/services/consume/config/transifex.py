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

from collections import (namedtuple, OrderedDict)

http_methods = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS')
media_types = ('application/json', 'application/xml')

# based on http://docs.transifex.com/api/
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'ProjectResource': OrderedDict([
        ('/project/{project_slug}/', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': ('details',),
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ProjectsResource': OrderedDict([
        ('/projects', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'SourceDocResource': OrderedDict([
        ('/project/<project_slug>/resource/<resource_slug>/content/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'resource_slug'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'StatisticsResource': OrderedDict([
        ('/project/{project_slug}/resource/{resource_slug}/stats/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'resource_slug'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
list_projects = resource('ProjectsResource', list(resource_config_dict['ProjectsResource'].keys())[0], http_methods[0])
project_details = resource('ProjectResource', list(resource_config_dict['ProjectResource'].keys())[0], http_methods[0])
proj_trans_stats = resource('StatisticsResource', list(resource_config_dict['StatisticsResource'].keys())[0],
                            http_methods[0])
# Transtats Transifex support operates on resources listed here
resources = {
    'list_projects': list_projects,
    'project_details': project_details,
    'proj_trans_stats': proj_trans_stats,
}
