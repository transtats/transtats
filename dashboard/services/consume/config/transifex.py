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
media_types = ('application/json', 'application/xml', 'application/binary')

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
    'ProjectsResourcePOST': OrderedDict([
        ('/projects', {
            http_methods[1]: {
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
                'request_media_type': None,
                'response_media_type': None,
            },
        }),
    ]),
    'SourceDocResourcePOST': OrderedDict([
        ('/project/<project_slug>/resources/', {
            http_methods[1]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': None,
                'response_media_type': None,
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
    'TranslationsResource': OrderedDict([
        ('/project/{project_slug}/resource/{resource_slug}/translation/{lang}/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'resource_slug', 'lang'),
                'query_params': ('file',),
                'request_media_type': None,
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'TranslationsResourcePUT': OrderedDict([
        ('/project/{project_slug}/resource/{resource_slug}/translation/{lang}/', {
            http_methods[2]: {
                'path_params': ('project_slug', 'resource_slug', 'lang'),
                'query_params': None,
                'request_media_type': None,
                'response_media_type': None,
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
list_projects = resource('ProjectsResource', list(resource_config_dict['ProjectsResource'].keys())[0], http_methods[0])
project_details = resource('ProjectResource', list(resource_config_dict['ProjectResource'].keys())[0], http_methods[0])
project_trans_stats = resource('StatisticsResource', list(resource_config_dict['StatisticsResource'].keys())[0],
                               http_methods[0])
project_source_file = resource('SourceDocResource', list(resource_config_dict['SourceDocResource'].keys())[0],
                               http_methods[0])
create_resource = resource('SourceDocResourcePOST', list(resource_config_dict['SourceDocResourcePOST'].keys())[0],
                           http_methods[1])
project_trans_file = resource('TranslationsResource', list(resource_config_dict['TranslationsResource'].keys())[0],
                              http_methods[0])
upload_trans_file = resource('TranslationsResourcePUT', list(resource_config_dict['TranslationsResourcePUT'].keys())[0],
                             http_methods[2])
create_project = resource('ProjectsResourcePOST', list(resource_config_dict['ProjectsResource'].keys())[0],
                          http_methods[1])
# Transtats Transifex support operates on resources listed here
resources = {
    'list_projects': list_projects,
    'project_details': project_details,
    'project_trans_stats': project_trans_stats,
    'project_source_file': project_source_file,
    'create_resource': create_resource,
    'project_trans_file': project_trans_file,
    'upload_trans_file': upload_trans_file,
    'create_project': create_project,
}
