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
media_types = ('application/json', 'application/xml', 'application/vnd.github+json')

# based on https://developer.github.com/v3/#current-version
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'ListBranches': OrderedDict([
        ('/repos/{owner}/{repo}/branches', {
            http_methods[0]: {
                'path_params': ('owner', 'repo'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'DeleteRepository': OrderedDict([
        ('/repos/{owner}/{repo}', {
            http_methods[3]: {
                'path_params': ('owner', 'repo'),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'ListPullRequests': OrderedDict([
        ('/repos/{owner}/{repo}/pulls', {
            http_methods[0]: {
                'path_params': ('owner', 'repo'),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'CreatePullRequests': OrderedDict([
        ('/repos/{owner}/{repo}/pulls', {
            http_methods[1]: {
                'path_params': ('owner', 'repo'),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'ListRepos': OrderedDict([
        ('/users/{owner}/repos', {
            http_methods[0]: {
                'path_params': ('owner', ),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'ListForks': OrderedDict([
        ('/repos/{owner}/{repo}/forks', {
            http_methods[0]: {
                'path_params': ('owner', 'repo'),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'CreateForks': OrderedDict([
        ('/repos/{owner}/{repo}/forks', {
            http_methods[1]: {
                'path_params': ('owner', 'repo'),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[2],
            },
        }),
    ]),
    'UserDetails': OrderedDict([
        ('/user', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[2],
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
list_branches = resource('ListBranches', list(resource_config_dict['ListBranches'].keys())[0], http_methods[0])
delete_repository = resource(
    'DeleteRepository', list(resource_config_dict['DeleteRepository'].keys())[0], http_methods[3]
)
list_pull_requests = resource(
    'ListPullRequests', list(resource_config_dict['ListPullRequests'].keys())[0], http_methods[0]
)
create_pull_requests = resource(
    'CreatePullRequests', list(resource_config_dict['CreatePullRequests'].keys())[0], http_methods[1]
)
list_repos = resource('ListRepos', list(resource_config_dict['ListRepos'].keys())[0], http_methods[0])
list_forks = resource('ListForks', list(resource_config_dict['ListForks'].keys())[0], http_methods[0])
create_forks = resource('CreateForks', list(resource_config_dict['CreateForks'].keys())[0], http_methods[1])
user_details = resource('UserDetails', list(resource_config_dict['UserDetails'].keys())[0], http_methods[0])

# Transtats GitHub support operates on resources listed here
resources = {
    'list_branches': list_branches,
    'delete_repository': delete_repository,
    'list_pull_requests': list_pull_requests,
    'create_pull_requests': create_pull_requests,
    'list_repos': list_repos,
    'list_forks': list_forks,
    'create_forks': create_forks,
    'user_details': user_details,
}
