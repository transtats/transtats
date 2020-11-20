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

# Service Layer: Process and cache REST resource's responses here.

from subprocess import Popen, PIPE
from collections import OrderedDict
try:
    import koji
except Exception as e:
    raise Exception("koji could not be imported, details: %s" % e)
from urllib.parse import urlparse

# dashboard
from dashboard.constants import (
    GIT_PLATFORMS, TRANSPLATFORM_ENGINES, BUILD_SYSTEMS, RELSTREAM_SLUGS
)
from dashboard.converters.xml2dict import parse
from dashboard.services.consume import call_service


__all__ = ['APIResources']


class ResourcesBase(object):
    """
    Base class for resources
    """
    @staticmethod
    def _execute_method(api_config, *args, **kwargs):
        """
        Executes located method with required params
        """
        try:
            if api_config.get('ext'):
                kwargs.update(dict(ext=True))
            service_resource = api_config['resources'][0]
            if len(api_config['resources']) > 1:
                kwargs.update(dict(more_resources=api_config['resources'][1:]))
            if api_config.get('combine_results'):
                kwargs['combine_results'] = []
            return api_config['method'](
                api_config['base_url'], service_resource, *args, **kwargs
            )
        except (KeyError, Exception):
            # log error
            pass
        return {}


class GitPlatformResources(ResourcesBase):
    """
    Git Platform related Resources
    """

    @staticmethod
    @call_service(GIT_PLATFORMS[0])
    def _fetch_github_repo_branches(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        git_branches = []
        if isinstance(response.get('json_content'), list):
            git_branches = [branch.get('name', '')
                            for branch in response.get('json_content')]
        return git_branches

    @staticmethod
    @call_service(GIT_PLATFORMS[1])
    def _gitlab_repo_branches_by_id(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        project_id = response.get('json_content', {}).get("id", int())

        if kwargs.get('more_resources'):
            for next_resource in kwargs['more_resources']:
                if next_resource == 'list_branches':
                    return GitPlatformResources._fetch_gitlab_repo_branches(
                        base_url, next_resource, *[project_id], **kwargs
                    )
        return project_id

    @staticmethod
    @call_service(GIT_PLATFORMS[1])
    def _fetch_gitlab_repo_branches(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        git_branches = []
        if isinstance(response.get('json_content'), list):
            git_branches = [branch.get('name', '')
                            for branch in response.get('json_content')]
        return git_branches

    @staticmethod
    @call_service(GIT_PLATFORMS[2])
    def _fetch_pagure_repo_branches(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content', {}).get('branches', [])

    def fetch_repo_branches(self, git_platform, instance_url, *args, **kwargs):
        """
        Fetches all projects or modules json from API
        :param git_platform: Git Platform API URL
        :param instance_url: Git Platform Instance URL
        :param args: URL Params: list
        :param kwargs: Keyword Args: dict
        :return: list
        """
        method_mapper = {
            GIT_PLATFORMS[0]: {
                'method': self._fetch_github_repo_branches,
                'base_url': 'https://api.github.com',
                'resources': ['list_branches'],
            },
            GIT_PLATFORMS[1]: {
                'method': self._gitlab_repo_branches_by_id,
                'base_url': instance_url,
                'resources': ['project_id', 'list_branches'],
            },
            GIT_PLATFORMS[2]: {
                'method': self._fetch_pagure_repo_branches,
                'base_url': instance_url,
                'resources': ['list_branches'],
            },
        }
        selected_config = method_mapper[git_platform]
        return self._execute_method(selected_config, *args, **kwargs)


class TransplatformResources(ResourcesBase):
    """
    Translation Platform related Resources
    """

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[0])
    def _fetch_damnedlies_projects(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[1])
    def _fetch_transifex_projects(base_url, resource, *url_params, **kwargs):
        # transifex returns list of projects owned by auth-user only
        # hence, response can vary here.
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[2])
    def _fetch_zanata_projects(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[3])
    def _fetch_weblate_projects(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        if response.get('json_content', {}).get('results'):
            kwargs['combine_results'].extend(response['json_content']['results'])
        if response.get('json_content', {}).get('next'):
            next_api_url = urlparse(response['json_content']['next'])
            if next_api_url.query:
                kwargs['ext'] = next_api_url.query
            TransplatformResources._fetch_weblate_projects(
                base_url, resource, *url_params, **kwargs
            )
        return kwargs['combine_results']

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[4])
    def _fetch_memsource_projects(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        if response.get("json_content").get("content"):
            kwargs['combine_results'].extend(response['json_content']['content'])
        resp_page_number = response.get("json_content").get("pageNumber", 0)
        resp_total_pages = response.get("json_content").get("totalPages", 0)
        if resp_page_number < resp_total_pages:
            kwargs['ext'] = "{}={}".format("pageNumber", resp_page_number + 1)
            TransplatformResources._fetch_memsource_projects(
                base_url, resource, *url_params, **kwargs
            )
        return kwargs['combine_results']

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[0])
    def _fetch_damnedlies_releases(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        pick_releases = []
        if response and response.get('json_content'):
            releases = response['json_content']
            first_stable_pk = None
            for release in releases:
                if '(development)' in release['fields']['description']:
                    pick_releases.append(release['fields']['name'])
                elif '(stable)' in release['fields']['description']:
                    pick_releases.append(release['fields']['name'])
                    first_stable_pk = release['pk']
                elif first_stable_pk and release['pk'] == first_stable_pk - 1:
                    pick_releases.append(release['fields']['name'])
                    first_stable_pk = None
        return {'releases': pick_releases}

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[0])
    def _fetch_damnedlies_project_details(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        projects = response.get('json_content')
        required_project = {}
        for project in projects:
            if project.get('fields', {}).get('name', '') == url_params[0]:
                required_project = project
        if kwargs.get('more_resources'):
            for next_resource in kwargs['more_resources']:
                if next_resource == 'releases':
                    required_project.update(
                        TransplatformResources._fetch_damnedlies_releases(
                            base_url, next_resource, *url_params, **kwargs
                        )
                    )
        return required_project

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[1])
    def _fetch_transifex_project_details(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[2])
    def _fetch_zanata_project_details(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[3])
    def _fetch_weblate_project_details(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        resp_json_content = response.get('json_content')
        if kwargs.get('more_resources'):
            for next_resource in kwargs['more_resources']:
                if next_resource == 'project_components':
                    resp_json_content['components'] = \
                        TransplatformResources._fetch_weblate_project_components(
                            base_url, next_resource, *url_params, **kwargs)
        return resp_json_content

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[3])
    def _fetch_weblate_project_components(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        if response.get('json_content', {}).get('results'):
            kwargs['combine_results'].extend(response['json_content']['results'])
        if response.get('json_content', {}).get('next'):
            next_api_url = urlparse(response['json_content']['next'])
            if next_api_url.query:
                kwargs['ext'] = next_api_url.query
            TransplatformResources._fetch_weblate_project_components(
                base_url, resource, *url_params, **kwargs
            )
        return kwargs['combine_results']

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[4])
    def _fetch_memsource_project_details(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    def _locate_damnedlies_stats(module_stat):
        translated, fuzzy, untranslated, total = 0, 0, 0, 0
        if isinstance(module_stat.get('domain'), list):
            for domain in module_stat.get('domain'):
                if domain.get('@id') == 'po':
                    translated = int(domain.get('translated'))
                    fuzzy = int(domain.get('fuzzy'))
                    untranslated = int(domain.get('untranslated'))
                    total = translated + fuzzy + untranslated
        elif isinstance(module_stat.get('domain'), dict):
            translated = int(module_stat.get('domain').get('translated'))
            fuzzy = int(module_stat.get('domain').get('fuzzy'))
            untranslated = int(module_stat.get('domain').get('untranslated'))
            total = translated + fuzzy + untranslated
        return translated, fuzzy, untranslated, total

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[0])
    def _fetch_damnedlies_locale_release_stats(base_url, resource, *url_params, **kwargs):
        locale_stat_dict = {}
        locale_stat_dict["unit"] = "MESSAGE"
        locale_stat_dict["locale"] = url_params[0]
        response = kwargs.get('rest_response', {})
        if response.get('content'):
            json_content = parse(response['content'])
            gnome_module_categories = json_content['stats']['category'] or []
            for category in gnome_module_categories:
                stats_tuple = ()
                modules = category.get('module')
                if isinstance(modules, list):
                    for module in modules:
                        if module.get('@id') == kwargs.get('package_name', ''):
                            stats_tuple = \
                                TransplatformResources._locate_damnedlies_stats(module)
                elif isinstance(modules, OrderedDict):
                    if modules.get('@id') == kwargs.get('package_name', ''):
                        stats_tuple = \
                            TransplatformResources._locate_damnedlies_stats(modules)
                if stats_tuple:
                    locale_stat_dict["translated"] = stats_tuple[0]
                    locale_stat_dict["untranslated"] = stats_tuple[1]
                    locale_stat_dict["fuzzy"] = stats_tuple[2]
                    locale_stat_dict["total"] = stats_tuple[3]
        return locale_stat_dict

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[1])
    def _fetch_transifex_proj_tran_stats(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[2])
    def _fetch_zanata_proj_tran_stats(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[3])
    def _fetch_weblate_proj_tran_stats(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        if response.get('json_content', {}).get('results'):
            kwargs['combine_results'].extend(response['json_content']['results'])
        if response.get('json_content', {}).get('next'):
            next_api_url = urlparse(response['json_content']['next'])
            if next_api_url.query:
                kwargs['ext'] = next_api_url.query
            TransplatformResources._fetch_weblate_proj_tran_stats(
                base_url, resource, *url_params, **kwargs
            )
        return dict(id=url_params[1], stats=kwargs['combine_results'])

    @staticmethod
    @call_service(TRANSPLATFORM_ENGINES[4])
    def _push_memsource_translations(base_url, resource, *url_params, **kwargs):
        response = kwargs.get('rest_response', {})
        return response.get('json_content')

    def fetch_all_projects(self, translation_platform, instance_url, *args, **kwargs):
        """
        Fetches all projects or modules json from API
        :param translation_platform: Translation Platform API
        :param instance_url: Translation Platform Server URL
        :param args: URL Params: list
        :param kwargs: Keyword Args: dict
        :return: list
        """
        method_mapper = {
            TRANSPLATFORM_ENGINES[0]: {
                'method': self._fetch_damnedlies_projects,
                'base_url': instance_url,
                'resources': ['modules'],
            },
            TRANSPLATFORM_ENGINES[1]: {
                'method': self._fetch_transifex_projects,
                'base_url': instance_url,
                'resources': ['list_projects'],
            },
            TRANSPLATFORM_ENGINES[2]: {
                'method': self._fetch_zanata_projects,
                'base_url': instance_url,
                'resources': ['list_projects'],
            },
            TRANSPLATFORM_ENGINES[3]: {
                'method': self._fetch_weblate_projects,
                'base_url': instance_url,
                'resources': ['list_projects'],
                'combine_results': True,
            },
            TRANSPLATFORM_ENGINES[4]: {
                'method': self._fetch_memsource_projects,
                'base_url': instance_url,
                'resources': ['list_projects'],
                'combine_results': True,
            }
        }
        selected_config = method_mapper[translation_platform]
        return self._execute_method(selected_config, *args, **kwargs)

    def fetch_project_details(self, translation_platform, instance_url, *args, **kwargs):
        """
        Fetches single project details json from API
        :param translation_platform: Translation Platform API
        :param instance_url: Translation Platform Server URL
        :param args: URL Params: list
        :param kwargs: Keyword Args: dict
        :return: dict
        """
        method_mapper = {
            TRANSPLATFORM_ENGINES[0]: {
                'method': self._fetch_damnedlies_project_details,
                'base_url': instance_url,
                'resources': ['modules', 'releases'],
                'project': args[0],
            },
            TRANSPLATFORM_ENGINES[1]: {
                'method': self._fetch_transifex_project_details,
                'base_url': instance_url,
                'resources': ['project_details'],
                'project': args[0],
                'ext': True,
            },
            TRANSPLATFORM_ENGINES[2]: {
                'method': self._fetch_zanata_project_details,
                'base_url': instance_url,
                'resources': ['project_details'],
                'project': args[0],
            },
            TRANSPLATFORM_ENGINES[3]: {
                'method': self._fetch_weblate_project_details,
                'base_url': instance_url,
                'resources': ['project_details', 'project_components'],
                'combine_results': True,
                'project': args[0],
            },
            TRANSPLATFORM_ENGINES[4]: {
                'method': self._fetch_memsource_project_details,
                'base_url': instance_url,
                'resources': ['project_details'],
                'project': args[0],
            }
        }
        selected_config = method_mapper[translation_platform]
        return self._execute_method(selected_config, *args, **kwargs)

    def fetch_translation_statistics(self, translation_platform, instance_url, *args, **kwargs):
        """
        Fetches single project version translation statistics json from API
        :param translation_platform: Translation Platform API
        :param instance_url: Translation Platform Server URL
        :param args: URL Params: list
        :param kwargs: Keyword Args: dict
        :return: dict
        """
        method_mapper = {
            TRANSPLATFORM_ENGINES[0]: {
                'method': self._fetch_damnedlies_locale_release_stats,
                'base_url': instance_url,
                'resources': ['release_trans_stats'],
                'locale': args[0],
                'version': args[1],
                'package': kwargs.get('package_name', ''),
            },
            TRANSPLATFORM_ENGINES[1]: {
                'method': self._fetch_transifex_proj_tran_stats,
                'base_url': instance_url,
                'resources': ['proj_trans_stats'],
                'project': args[0],
                'version': args[1],

            },
            TRANSPLATFORM_ENGINES[2]: {
                'method': self._fetch_zanata_proj_tran_stats,
                'base_url': instance_url,
                'resources': ['proj_trans_stats'],
                'project': args[0],
                'version': args[1],
                'ext': True,
            },
            TRANSPLATFORM_ENGINES[3]: {
                'method': self._fetch_weblate_proj_tran_stats,
                'base_url': instance_url,
                'resources': ['project_component_stats'],
                'project': args[0],
                'version': args[1],
                'combine_results': True,
            }
        }
        selected_config = method_mapper[translation_platform]
        return self._execute_method(selected_config, *args, **kwargs)

    def push_translations(self, translation_platform, instance_url, *args, **kwargs):
        """
        Push translations to CI Platform
        :param translation_platform: Translation Platform API
        :param instance_url: Translation Platform Server URL
        :param args: URL Params: list
        :param kwargs: Keyword Args: dict
        :return: dict
        """
        method_mapper = {
            TRANSPLATFORM_ENGINES[4]: {
                'method': self._push_memsource_translations,
                'base_url': instance_url,
                'resources': ['create_job'],
            }
        }
        selected_config = method_mapper[translation_platform]
        return self._execute_method(selected_config, *args, **kwargs)


class KojiResources(object):
    """
    Koji Resources
    """

    @staticmethod
    def _session(hub):
        krb_service = ''
        if BUILD_SYSTEMS[0] in hub:
            krb_service = 'brewhub'
        elif BUILD_SYSTEMS[1] in hub:
            krb_service = 'kojihub'
        return koji.ClientSession(
            hub, opts={'krbservice': krb_service, 'no_ssl_verify': True}
        )
        # self.session.gssapi_login()

    def establish_kerberos_ticket(self):
        """
        Get kerberos ticket in-place
        """
        userid = "transtats"
        realm = "FEDORAPROJECT.ORG"

        kinit = '/usr/bin/kinit'
        kinit_args = [kinit, '%s@%s' % (userid, realm)]
        kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        kinit.stdin.write(b'secret')
        kinit.wait()

    def build_tags(self, hub_url, product):
        """
        Get build tags
        """
        all_tags = []
        active_repos = self._session(hub_url).getActiveRepos()
        tag_starts_with = ''

        if BUILD_SYSTEMS[0] in hub_url:
            all_tags = self._session(hub_url).listTags()
            if product.product_slug == RELSTREAM_SLUGS[0]:
                tag_starts_with = 'rhel'
            elif product.product_slug == RELSTREAM_SLUGS[2]:
                tag_starts_with = 'rhevm'
        elif product.product_slug == RELSTREAM_SLUGS[1]:
            tag_starts_with = 'f'

        build_tags = [repo.get('tag_name') for repo in active_repos
                      if repo.get('tag_name', '').startswith(tag_starts_with)]
        if all_tags:
            build_tags.extend(
                [tag.get('name') for tag in all_tags
                 if tag.get('name', '').startswith(tag_starts_with) and
                 ('-candidate' in tag.get('name', '') or
                 '-snapshot-' in tag.get('name', ''))]
            )
        if BUILD_SYSTEMS[1] in hub_url:
            # fedora koji specific changes
            processed_tags = list(set(
                [tag[:tag.find('-')] for tag in build_tags if '-' in tag]
            ))
        else:
            processed_tags = list(set(
                [tag for tag in build_tags if 'alt' not in tag]
            ))
        return sorted(processed_tags, reverse=True)

    def build_info(self, hub_url, tag, pkg):
        return self._session(hub_url).getLatestBuilds(tag, package=pkg)

    def get_build(self, hub_url, build_id):
        return self._session(hub_url).getBuild(build_id)

    def list_RPMs(self, hub_url, build_id):
        return self._session(hub_url).listRPMs(buildID=build_id)

    def package_id(self, hub_url, pkg):
        return self._session(hub_url).getPackageID(pkg)

    def list_builds(self, hub_url, pkg_id):
        pkg_builds = self._session(hub_url).listBuilds(packageID=pkg_id)
        try:
            return sorted(pkg_builds, key=lambda x: x['build_id'])
        except Exception as e:
            # passing for now
            pass
        return pkg_builds or []

    def list_tags(self, hub_url, build_id):
        build_tags = self._session(hub_url).listTags(build=build_id)
        return [tag['name'] for tag in build_tags if tag.get('name')]

    def get_path_info(self, build=None, srpm=None):
        if build and not srpm:
            path = koji.pathinfo.build(build)
            return path[0] if isinstance(path, list) and len(path) > 0 else path
        elif srpm and not build:
            return koji.pathinfo.rpm(srpm)


class APIResources(GitPlatformResources,
                   KojiResources,
                   TransplatformResources):
    """
    Single Entry Point to
     REST Communications
    """
    pass
