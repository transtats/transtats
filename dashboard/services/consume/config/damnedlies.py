# Copyright 2017 Red Hat, Inc.
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

# based on https://wiki.gnome.org/DamnedLies
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'TeamsResource': OrderedDict([
        ('/teams/json', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ModulesResource': OrderedDict([
        ('/module/json', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ReleasesResource': OrderedDict([
        ('/releases/json', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ReleaseDetailsResource': OrderedDict([
        ('/releases/{release_name}/xml', {
            http_methods[0]: {
                'path_params': ('release_name', ),
                'query_params': None,
                'request_media_type': media_types[1],
                'response_media_type': media_types[1],
            },
        }),
    ]),
    'ReleaseStatisticsResource': OrderedDict([
        ('/languages/{locale}/{release_name}/xml', {
            http_methods[0]: {
                'path_params': ('locale', 'release_name'),
                'query_params': None,
                'request_media_type': media_types[1],
                'response_media_type': media_types[1],
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
# Transtats DamnedLies support operates on resources listed here
resources = {
    'teams': teams,
    'modules': modules,
    'releases': releases,
    'release_details': release_details,
    'release_trans_stats': release_trans_stats
}
