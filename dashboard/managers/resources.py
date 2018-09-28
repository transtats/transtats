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

# Process and cache REST resource's responses here.

from subprocess import Popen, PIPE
from collections import OrderedDict
try:
    import koji
except Exception as e:
    raise Exception("koji could not be imported, details: %s" % e)

# dashboard
from dashboard.constants import TRANSPLATFORM_ENGINES, BUILD_SYSTEMS
from dashboard.converters.xml2dict import parse
from dashboard.decorators import call_service


__all__ = ['APIResources']


class TransplatformResources(object):
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

    def _execute_method(self, api_config, *args, **kwargs):
        """
        Executes located method with required params
        """
        try:
            if api_config.get('ext'):
                kwargs.update(dict(ext=True))
            service_resource = api_config['resources'][0]
            if len(api_config['resources']) > 1:
                kwargs.update(dict(more_resources=api_config['resources'][1:]))
            return api_config['method'](
                api_config['base_url'], service_resource, *args, **kwargs
            )
        except (KeyError, Exception):
            # log error
            pass
        return {}

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

    def build_tags(self, hub_url):
        """
        Get build tags
        """
        active_repos = self._session(hub_url).getActiveRepos()
        tag_starts_with = 'rhel' if BUILD_SYSTEMS[0] in hub_url else ''
        build_tags = [repo.get('tag_name') for repo in active_repos
                      if repo.get('tag_name', '').startswith(tag_starts_with)]
        if BUILD_SYSTEMS[1] in hub_url:
            # fedora koji specific changes
            pre_processed_tags = [tag[:-6] if tag.endswith('-build') else tag
                                  for tag in list(set(build_tags))]
            processed_tags = [tag for tag in pre_processed_tags
                              if not tag.startswith('module-')]
        else:
            processed_tags = list(set(build_tags))
        return sorted(processed_tags)[::-1]

    def build_info(self, hub_url, tag, pkg):
        return self._session(hub_url).getLatestBuilds(tag, package=pkg)

    def get_build(self, hub_url, build_id):
        return self._session(hub_url).getBuild(build_id)

    def list_RPMs(self, hub_url, build_id):
        return self._session(hub_url).listRPMs(buildID=build_id)

    def get_path_info(self, build=None, srpm=None):
        if build and not srpm:
            path = koji.pathinfo.build(build)
            return path[0] if isinstance(path, list) and len(path) > 0 else path
        elif srpm and not build:
            return koji.pathinfo.rpm(srpm)


class APIResources(KojiResources,
                   TransplatformResources):
    """
    Single Entry Point to
     REST Communications
    """
    pass
