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
media_types = ('application/json', 'application/xml', 'application/binary')

# based on https://docs.weblate.org/en/latest/api.html
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'ProjectsResource': OrderedDict([
        ('/projects/', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
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
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'StatisticsResource': OrderedDict([
        ('/projects/{project_slug}/statistics/', {
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
        ('/translations/{project_slug}/{component_slug}/{locale}/file/', {
            http_methods[0]: {
                'path_params': ('project_slug', 'component_slug', 'locale'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'TranslationResourcePOST': OrderedDict([
        # curl -X POST \
        #     -F file=@strings.xml \
        #     -H "Authorization: Token TOKEN" \
        #     http://example.com/api/translations/hello/android/cs/file/
        ('/translations/{project_slug}/{component_slug}/{locale}/file/', {
            http_methods[1]: {
                'path_params': ('project_slug', 'component_slug', 'locale'),
                'query_params': None,
                'response_media_type': media_types[0],
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
list_projects = resource('ProjectsResource', list(resource_config_dict['ProjectsResource'].keys())[0], http_methods[0])
project_details = resource('ProjectResource', list(resource_config_dict['ProjectResource'].keys())[0], http_methods[0])
list_components = resource('ComponentsResource', list(resource_config_dict['ComponentsResource'].keys())[0],
                           http_methods[0])
project_components = resource('ComponentResource', list(resource_config_dict['ComponentResource'].keys())[0],
                              http_methods[0])
component_details = resource('ComponentResource', list(resource_config_dict['ComponentResource'].keys())[1],
                             http_methods[0])
source_doc = resource('SourceDocResource', list(resource_config_dict['SourceDocResource'].keys())[0], http_methods[0])
project_stats = resource('StatisticsResource', list(resource_config_dict['StatisticsResource'].keys())[0],
                         http_methods[0])
project_component_stats = resource('StatisticsResource', list(resource_config_dict['StatisticsResource'].keys())[1],
                                   http_methods[0])
locale_stats = resource('TranslationResource', list(resource_config_dict['TranslationResource'].keys())[0],
                        http_methods[0])
translated_doc = resource('TranslationResource', list(resource_config_dict['TranslationResource'].keys())[1],
                          http_methods[0])
upload_translation = resource(
    'TranslationResourcePOST', list(resource_config_dict['TranslationResourcePOST'].keys())[0], http_methods[1]
)
# Transtats Weblate support operates on resources listed here
resources = {
    'list_projects': list_projects,
    'project_details': project_details,
    'list_components': list_components,
    'project_components': project_components,
    'component_details': component_details,
    'source_doc': source_doc,
    'project_stats': project_stats,
    'project_component_stats': project_component_stats,
    'locale_stats': locale_stats,
    'translated_doc': translated_doc,
    'upload_translation': upload_translation
}
