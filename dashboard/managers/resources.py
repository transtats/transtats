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

# dashboard
from dashboard.constants import TRANSPLATFORM_ENGINES
from dashboard.decorators import call_service
from dashboard.converters.xml2dict import parse


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
            for release in releases:
                if '(development)' in release['fields']['description'] or \
                        '(stable)' in release['fields']['description']:
                    pick_releases.append(release['fields']['name'])
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
                modules = category.get('module')
                for module in modules:
                    if module.get('@id') == kwargs.get('package_name', ''):
                        translated, fuzzy, untranslated, total = 0, 0, 0, 0
                        if isinstance(module.get('domain'), list):
                            for domain in module.get('domain'):
                                if domain.get('@id') == 'po':
                                    translated = int(domain.get('translated'))
                                    fuzzy = int(domain.get('fuzzy'))
                                    untranslated = int(domain.get('untranslated'))
                                    total = translated + fuzzy + untranslated
                        elif isinstance(module.get('domain'), dict):
                            translated = int(module.get('domain').get('translated'))
                            fuzzy = int(module.get('domain').get('fuzzy'))
                            untranslated = int(module.get('domain').get('untranslated'))
                            total = translated + fuzzy + untranslated
                        locale_stat_dict["translated"] = translated
                        locale_stat_dict["untranslated"] = untranslated
                        locale_stat_dict["fuzzy"] = fuzzy
                        locale_stat_dict["total"] = total
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


class APIResources(TransplatformResources):
    """
    Single Entry Point to
     REST Communications
    """
    pass
