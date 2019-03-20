# Copyright 2019 Red Hat, Inc.
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

# based on https://docs.weblate.org/en/latest/api.html
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'ProjectsResource': OrderedDict([
        ('/projects/', {
            http_methods[0]: {
                'path_params': None,
                'query_params': ('page',),
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ProjectResource': OrderedDict([
        ('/projects/{project_slug}/', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ComponentsResource': OrderedDict([
        ('/components/', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ComponentResource': OrderedDict([
        ('/projects/{project_slug}/components/', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        ('/components/{project_slug}/{component_slug}/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'component_slug'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'SourceDocResource': OrderedDict([
        ('/components/{project_slug}/{component_slug}/new_template/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'component_slug'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'StatisticsResource': OrderedDict([
        ('/components/{project_slug}/statistics/', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        ('/components/{project_slug}/{component_slug}/statistics/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'component_slug'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'TranslationResource': OrderedDict([
        ('/translations/{project_slug}/{component_slug}/{locale}/statistics/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'component_slug', 'locale'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
teams = resource('TeamsResource', list(resource_config_dict['TeamsResource'].keys())[0], http_methods[0])
modules = resource('ModulesResource', list(resource_config_dict['ModulesResource'].keys())[0], http_methods[0])
releases = resource('ReleasesResource', list(resource_config_dict['ReleasesResource'].keys())[0], http_methods[0])
release_details = resource('ReleaseDetailsResource', list(resource_config_dict['ReleaseDetailsResource'].keys())[0],
                           http_methods[0])
release_trans_stats = resource('ReleaseStatisticsResource',
                               list(resource_config_dict['ReleaseStatisticsResource'].keys())[0], http_methods[0])
# Transtats Weblate support operates on resources listed here
resources = {
    'teams': teams,
    'modules': modules,
    'releases': releases,
    'release_details': release_details,
    'release_trans_stats': release_trans_stats
}
