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
media_types = ('application/json', 'application/vnd.zanata.projects+json', 'application/vnd.zanata.Version+json',
               'application/vnd.zanata.project.iteration+json', 'application/vnd.zanata.glossary+json',
               'application/vnd.zanata.project.locales+json', 'application/xml')

# based on http://zanata.org/zanata-platform/rest-api-docs/
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'AccountResource': OrderedDict(),
    'AsynchronousProcessResource': OrderedDict(),
    'CopyTransResource': OrderedDict(),
    'FileResource': OrderedDict(),
    'GlossaryResource': OrderedDict([
        ('/glossary', {
            http_methods[2]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[4],
            },
            http_methods[3]: {
                'path_params': None,
                'query_params': None,
                'response_media_type': media_types[4],
            },
        }),
    ]),
    'ProjectIterationLocalesResource': OrderedDict([
        ('/projects/p/{projectSlug}/iterations/i/{iterationSlug}/locales', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug'),
                'query_params': None,
                'response_media_type': media_types[5],
            },
        }),
    ]),
    'ProjectIterationResource': OrderedDict([
        ('/projects/p/{projectSlug}/iterations/i/{iterationSlug}', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug'),
                'query_params': None,
                'response_media_type': media_types[3],
            },
            http_methods[2]: {
                'path_params': ('projectSlug', 'iterationSlug'),
                'query_params': None,
                'request_media_type': media_types[3],
                'response_media_type': media_types[0],
            },
        }),
        ('/projects/p/{projectSlug}/iterations/i/{iterationSlug}/config', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug'),
                'query_params': None,
                'request_media_type': media_types[6],
                'response_media_type': media_types[6],
            },
        })]
    ),
    'ProjectLocalesResource': OrderedDict([
        ('/projects/p/{projectSlug}/locales', {
            http_methods[0]: {
                'path_params': ('projectSlug',),
                'query_params': None,
                'response_media_type': media_types[5],
            },
        }),
    ]),
    'ProjectResource': OrderedDict([
        ('/projects/p/{projectSlug}', {
            http_methods[0]: {
                'path_params': ('projectSlug',),
                'query_params': None,
                'response_media_type': media_types[0],
            },
            http_methods[2]: {
                'path_params': ('projectSlug',),
                'query_params': None,
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
                'response_media_type': media_types[1],
            },
        }),
    ]),
    'SourceDocResource': OrderedDict([
        ('/projects/p/{projectSlug}/iterations/i/{iterationSlug}/r', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug'),
                'query_params': None,
                'response_media_type': media_types[0],
            },
            http_methods[1]: {
                'path_params': ('projectSlug', 'iterationSlug'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        ('/projects/p/{projectSlug}/iterations/i/{iterationSlug}/r/{id}', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug', 'id'),
                'query_params': None,
                'response_media_type': media_types[0],
            },
            http_methods[2]: {
                'path_params': ('projectSlug', 'iterationSlug', 'id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
            http_methods[3]: {
                'path_params': ('projectSlug', 'iterationSlug', 'id'),
                'query_params': None,
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'StatisticsResource': OrderedDict([
        ('/stats/proj/{projectSlug}/iter/{iterationSlug}', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug'),
                'query_params': ('detail=true', 'word=false'),
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        ('/stats/proj/{projectSlug}/iter/{iterationSlug}/doc/{docId}', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug', 'docId'),
                'query_params': None,
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'TranslatedDocResource': OrderedDict([
        ('/projects/p/{projectSlug}/iterations/i/{iterationSlug}/r/{id}/translations/{locale}', {
            http_methods[0]: {
                'path_params': ('projectSlug', 'iterationSlug', 'id', 'locale'),
                'query_params': None,
                'response_media_type': media_types[0],
            },
            http_methods[2]: {
                'path_params': ('projectSlug', 'iterationSlug', 'id', 'locale'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'TranslationMemoryResource': OrderedDict(),
    'VersionResource': OrderedDict([
        ('/version', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'response_media_type': media_types[2],
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
server_version = resource('VersionResource', list(resource_config_dict['VersionResource'].keys())[0], http_methods[0])
list_projects = resource('ProjectsResource', list(resource_config_dict['ProjectsResource'].keys())[0], http_methods[0])
project_details = resource('ProjectResource', list(resource_config_dict['ProjectResource'].keys())[0], http_methods[0])
get_iteration = resource('ProjectIterationResource', list(resource_config_dict['ProjectIterationResource'].keys())[0],
                         http_methods[0])
list_files = resource('SourceDocResource', list(resource_config_dict['SourceDocResource'].keys())[0], http_methods[0])
retrieve_template = resource('SourceDocResource', list(resource_config_dict['SourceDocResource'].keys())[1], http_methods[0])
retrieve_translation = resource('TranslatedDocResource', list(resource_config_dict['TranslatedDocResource'].keys())[0],
                                http_methods[0])
project_locales = resource('ProjectLocalesResource', list(resource_config_dict['ProjectLocalesResource'].keys())[0],
                           http_methods[0])
iteration_locales = resource('ProjectIterationLocalesResource',
                             list(resource_config_dict['ProjectIterationLocalesResource'].keys())[0], http_methods[0])
proj_trans_stats = resource('StatisticsResource', list(resource_config_dict['StatisticsResource'].keys())[0], http_methods[0])
doc_trans_stats = resource('StatisticsResource', list(resource_config_dict['StatisticsResource'].keys())[1], http_methods[0])
project_config = resource('ProjectIterationResource', list(resource_config_dict['ProjectIterationResource'].keys())[1],
                          http_methods[0])
# Transtats Zanata support operates on resources listed here
resources = {
    'server_version': server_version,
    'list_projects': list_projects,
    'project_details': project_details,
    'get_iteration': get_iteration,
    'list_files': list_files,
    'retrieve_template': retrieve_template,
    'retrieve_translation': retrieve_translation,
    'project_locales': project_locales,
    'iteration_locales': iteration_locales,
    'proj_trans_stats': proj_trans_stats,
    'doc_trans_stats': doc_trans_stats,
    'project_config': project_config,
}
