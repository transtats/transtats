#
# transtats - Translation Analytics
#
# Copyright (c) 2016 Sundeep Anand <suanand@redhat.com>
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of transtats.
#
# transtats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# transtats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with transtats.  If not, see <http://www.gnu.org/licenses/>.

from collections import (namedtuple, OrderedDict)

middle_url = '/seam/resource/restv1'
http_methods = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS')
media_types = ('application/json', 'application/vnd.zanata.projects+json', 'application/vnd.zanata.Version+json',
               'application/vnd.zanata.project.iteration+json', 'application/vnd.zanata.glossary+json',
               'application/vnd.zanata.project.locales+json', 'application/xml')

# based on https://zanata.ci.cloudbees.com/job/zanata-api-site/site/zanata-common-api/rest-api-docs/index.html
# please add, modify resource details here, and make entry in service-to-resource mappings and in zpc_services
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
                'query_params': None,
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
list_project = resource('ProjectResource', list(resource_config_dict['ProjectResource'].keys())[0], http_methods[0])
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
# Transanalytics Zanata support operates on services listed here
zpc_services = {
    'server_version': server_version,
    'list_projects': list_projects,
    'list_project': list_project,
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


class ServiceConfig(object):
    def __init__(self, service):
        if service not in zpc_services:
            raise Exception('Invalid Service')
        else:
            self._config_dict = resource_config_dict
            self._middle_url = middle_url
            self._service = zpc_services[service]
            for attrib, value in (self._config_dict[self._service.rest_resource]
                                  [self._service.mount_point][self._service.http_method].items()):
                setattr(self, str(attrib), value)

    @property
    def resource_group(self):
        return self._service.rest_resource

    @property
    def mount_points(self):
        return list(self._config_dict[self._service.rest_resource].keys())

    @property
    def resource(self):
        return self._middle_url + self._service.mount_point

    @property
    def mount_point(self):
        return self._service.mount_point

    @property
    def http_method(self):
        return self._service.http_method
