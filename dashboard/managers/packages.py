# Copyright 2018 Red Hat, Inc.
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

# Application inventories:
#       Packages

# python
import re
import json
import difflib
import operator
from collections import OrderedDict
from functools import reduce

# django
from django.utils import timezone

# dashboard
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, DAMNEDLIES_SLUGS,
    RELSTREAM_SLUGS, BRANCH_MAPPING_KEYS,
)
from dashboard.managers.inventory import (
    InventoryManager, SyncStatsManager, ReleaseBranchManager
)
from dashboard.models import Platform, Package, CacheBuildDetails
from dashboard.managers.utilities import parse_project_details_json


__all__ = ['PackagesManager', 'PackageBranchMapping']


class PackagesManager(InventoryManager):
    """
    Packages Manager
    """

    PROCESS_STATS = True
    syncstats_manager = SyncStatsManager()
    release_manager = ReleaseBranchManager()

    def get_packages(self, pkgs=None, pkg_params=None):
        """
        fetch packages from db
        """
        packages = None
        fields = pkg_params if isinstance(pkg_params, (list, tuple)) else []
        kwargs = {}
        if pkgs:
            kwargs.update(dict(package_name__in=pkgs))
        try:
            packages = Package.objects.only(*fields).filter(**kwargs) \
                .order_by('-platform_last_updated')
        except Exception as e:
            self.app_logger(
                'ERROR', "Packages could not be fetched, details: " + str(e)
            )
        return packages

    def is_package_exist(self, package_name):
        """
        check package existence
        """
        if self.get_packages(pkgs=[package_name]):
            return True
        return False

    def update_package(self, package_name, fields):
        """
        Update a package with certain fields
        """
        try:
            Package.objects.filter(package_name=package_name).update(**fields)
        except Exception as e:
            self.app_logger(
                'ERROR', "Package could not be updated, details: " + str(e)
            )

    def get_relbranch_specific_pkgs(self, release_branch, fields=None):
        """
        fetch release branch specific packages from db
        """
        packages = ()
        fields_required = fields if fields else ()
        try:
            packages = Package.objects.only(*fields_required) \
                .filter(release_branch_mapping__icontains=release_branch) \
                .order_by('-platform_last_updated')
        except Exception as e:
            self.app_logger(
                'ERROR', ("release branch specific package could not be fetched for " +
                          release_branch + " release branch, details: " + str(e))
            )
        return packages

    def get_release_specific_package_stats(self, release_branch):
        """
        Fetch processed stats for all packages of a release
        :param release_branch: str
        :return: package stats: dict
        """
        packages_stats = {}
        release_packages = self.get_relbranch_specific_pkgs(
            release_branch, fields=['package_name', 'release_branch_mapping']
        )
        branch_locales = self.get_relbranch_locales(release_branch)
        locales_count_match = True \
            if len(branch_locales) == self.get_active_locales_count() else False
        for package in release_packages:
            version = package.release_branch_mapping_json[release_branch][BRANCH_MAPPING_KEYS[0]]
            package_stats = self.syncstats_manager.get_sync_stats(
                pkgs=[package.package_name],
                fields=['stats_raw_json_str', 'stats_processed_json_str'],
                versions=[version]
            ).first()
            if package_stats:
                processed_stats = {}
                if not package_stats.stats_processed_json:
                    if package_stats.stats_raw_json.get('stats'):
                        processed_stats = self._process_response_stats_json(
                            package_stats.stats_raw_json['stats'])

                    if package.platform_slug.engine_name == TRANSPLATFORM_ENGINES[1] and not processed_stats:
                        processed_stats = self._process_response_stats_json_tx(
                            package_stats.stats_raw_json)
                else:
                    processed_stats = package_stats.stats_processed_json
                package_processed_stats = processed_stats
                packages_stats[package.package_name] = package_processed_stats \
                    if locales_count_match else {locale: package_processed_stats.get(locale, {})
                                                 for locale in branch_locales}
        return packages_stats

    def get_trans_stats_by_rule(self, coverage_rule):
        """
        Get translation stats by rule args: release, packages, locales, tags
        :param coverage_rule: coverage rule query object
        :return: stats dict
        """
        if not coverage_rule:
            return
        packages = self.get_packages(pkgs=coverage_rule.rule_packages)
        locales = coverage_rule.rule_languages
        tags = coverage_rule.rule_build_tags
        release = coverage_rule.rule_release_slug_id

        locale_lang_dict = dict(self.get_locale_lang_tuple(locales))

        trans_stats_by_rule = {}

        for package in packages:
            versions = []
            versions.extend(tags)

            trans_stats_by_rule[package.package_name] = {
                "translation_platform": {},
                "build_system": {
                    tag: {"Statistics": "Not Synced with Build System for {0}".format(tag)}
                    for tag in tags
                }
            }

            if package.release_branch_mapping_json and package.release_branch_mapping_json.get(release):

                branch_map = package.release_branch_mapping_json
                platform_version = branch_map[release].get(BRANCH_MAPPING_KEYS[0])
                build_system_version = branch_map[release].get(BRANCH_MAPPING_KEYS[2])

                package_stats = self.syncstats_manager.get_sync_stats(
                    pkgs=[package.package_name],
                    fields=['stats_raw_json_str', 'stats_processed_json_str',
                            'project_version', 'source']
                )

                for p_stats in package_stats:
                    processed_stats = {}
                    not_found = {'Total': 'Not Found', 'Translated': 'Not Found',
                                 'Untranslated': 'Not Found', 'Remaining': 'N/A'}

                    if not p_stats.stats_processed_json:
                        if p_stats.stats_raw_json.get('stats'):
                            processed_stats = self._process_response_stats_json(
                                p_stats.stats_raw_json['stats'])

                        if p_stats.source == TRANSPLATFORM_ENGINES[1] and not processed_stats:
                            processed_stats = self._process_response_stats_json_tx(
                                p_stats.stats_raw_json)
                    else:
                        processed_stats = p_stats.stats_processed_json
                    package_processed_stats = {
                        locale_lang_dict.get(locale, locale):
                            processed_stats.get(locale, not_found) for locale in locales}

                    if p_stats.project_version == platform_version:
                        trans_stats_by_rule[package.package_name]["translation_platform"].update(package_processed_stats)
                    elif p_stats.project_version == "{0} - {1}".format(p_stats.source, build_system_version) and \
                            build_system_version in tags:
                        trans_stats_by_rule[package.package_name]["build_system"][build_system_version] = \
                            package_processed_stats
                    ext_tags = [tag for tag in tags if tag in p_stats.project_version]
                    if ext_tags and len(ext_tags) == 1:
                        trans_stats_by_rule[package.package_name]["build_system"][ext_tags[0]] = \
                            package_processed_stats

                if not trans_stats_by_rule[package.package_name]["translation_platform"]:
                    tp_not_sync_msg = "Not Synced with Translation Platform for {0}".format(platform_version) \
                        if platform_version else "Not Synced with Translation Platform"
                    trans_stats_by_rule[package.package_name]["translation_platform"].update({
                        "Translation Stats": tp_not_sync_msg
                    })
        return trans_stats_by_rule

    def count_packages(self):
        """
        packages count
        """
        packages = self.get_packages()
        return packages.count() if packages else 0

    def get_package_name_tuple(self, t_status=False, check_mapping=False):
        """
        returns (package_name, upstream_name) tuple (only sync'd ones)
        """
        packages = self.get_packages()
        name_list = [(package.package_name, package.upstream_name) for package in packages]
        if t_status:
            name_list = [(package.package_name, package.upstream_name) for package in packages
                         if package.platform_last_updated or package.upstream_last_updated]
        elif check_mapping:
            name_list = [(package.package_name, package.package_name) for package in packages
                         if package.platform_last_updated and package.release_branch_mapping]
        return tuple(sorted(name_list))

    def get_project_details(self, transplatform, package_name):
        """
        Get platform-wise project details
        """
        resp_dict = None
        platform_url = None
        if transplatform.engine_name == TRANSPLATFORM_ENGINES[0]:
            platform_url = transplatform.api_url + "/module/" + package_name + "/"
            resp_dict = self.api_resources.fetch_project_details(
                transplatform.engine_name, transplatform.api_url, package_name
            )
        elif transplatform.engine_name == TRANSPLATFORM_ENGINES[1]:
            resp_dict = self.api_resources.fetch_project_details(
                transplatform.engine_name, transplatform.api_url, package_name,
                **dict(ext=True, auth_user=transplatform.auth_login_id, auth_token=transplatform.auth_token_key)
            )
            if resp_dict:
                tx_org_slug = resp_dict['organization']['slug']
                platform_url = transplatform.api_url + "/" + tx_org_slug + "/" + package_name
        elif transplatform.engine_name == TRANSPLATFORM_ENGINES[2]:
            platform_url = transplatform.api_url + "/project/view/" + package_name
            resp_dict = self.api_resources.fetch_project_details(
                transplatform.engine_name, transplatform.api_url, package_name,
                **dict(auth_user=transplatform.auth_login_id, auth_token=transplatform.auth_token_key)
            )
        elif transplatform.engine_name == TRANSPLATFORM_ENGINES[3]:
            resp_dict = self.api_resources.fetch_project_details(
                transplatform.engine_name, transplatform.api_url, package_name
            )
            platform_url = transplatform.api_url + "/projects/" + package_name
        return platform_url, resp_dict

    def add_package(self, **kwargs):
        """
        add package to db
        :param kwargs: dict
        :return: boolean
        """
        required_params = ('package_name', 'upstream_url', 'transplatform_slug', 'release_streams')
        if not set(required_params) <= set(kwargs.keys()):
            return

        if not (kwargs['package_name'] and kwargs['upstream_url']):
            return

        try:
            # derive translation platform project URL
            platform = Platform.objects.only('engine_name', 'api_url') \
                .filter(platform_slug=kwargs.pop('transplatform_slug')).get()
            kwargs['platform_url'], resp_dict = \
                self.get_project_details(platform, kwargs['package_name'])
            if resp_dict:
                # save project details in db
                kwargs['package_details_json_str'] = json.dumps(resp_dict)
                kwargs['details_json_last_updated'] = timezone.now()

            if 'update_stats' in kwargs:
                del kwargs['update_stats']

            kwargs['platform_slug'] = platform
            kwargs['products'] = kwargs.pop('release_streams')
            kwargs['platform_name'] = kwargs['package_name']
            kwargs['upstream_name'] = kwargs['upstream_url'].split('/')[-1]
            # save in db
            new_package = Package(**kwargs)
            new_package.save()
        except:
            # log event, pass for now
            # todo - implement error msg handling
            return False
        else:
            return True

    def _get_project_ids_names(self, engine, projects):
        ids = []
        names = []
        if isinstance(projects, list) and engine == TRANSPLATFORM_ENGINES[0]:
            for project in projects:
                ids.append(project['fields']['name'])
        elif isinstance(projects, dict) and engine == TRANSPLATFORM_ENGINES[1]:
            ids.append(projects.get('slug'))
            names.append(projects.get('name'))
        elif isinstance(projects, list) and engine == TRANSPLATFORM_ENGINES[2]:
            for project in projects:
                ids.append(project['id'])
                names.append(project['name'])
        elif isinstance(projects, list) and engine == TRANSPLATFORM_ENGINES[3]:
            for project in projects:
                ids.append(project.get('slug'))
                names.append(project.get('name'))
        return ids, names

    def validate_package(self, **kwargs):
        """
        Validates existence of a package at a transplatform
        :param kwargs: dict
        :return: package_name: str, Boolean
        """
        if not (kwargs.get('package_name')):
            return
        package_name = kwargs['package_name']
        transplatform_fields = ('engine_name', 'api_url', 'projects_json_str',
                                'auth_login_id', 'auth_token_key')
        # get transplatform projects from db
        platform = Platform.objects.only(*transplatform_fields) \
            .filter(platform_slug=kwargs['transplatform_slug']).get()
        projects_json = platform.projects_json
        # if not found in db, fetch transplatform projects from API
        if not projects_json:
            response_dict = None
            auth_dict = dict(
                auth_user=platform.auth_login_id, auth_token=platform.auth_token_key
            )
            if platform.engine_name == TRANSPLATFORM_ENGINES[1]:
                response_dict = self.api_resources.fetch_project_details(
                    platform.engine_name, platform.api_url, package_name.lower(), **auth_dict
                )
            elif platform.engine_name in (TRANSPLATFORM_ENGINES[0],
                                          TRANSPLATFORM_ENGINES[2],
                                          TRANSPLATFORM_ENGINES[3]):
                response_dict = self.api_resources.fetch_all_projects(
                    platform.engine_name, platform.api_url, **auth_dict
                ) or {}
                # save all_projects_json in db - faster validation next times
                # except transifex, as there we have project level details
                Platform.objects.filter(api_url=platform.api_url).update(
                    projects_json_str=json.dumps(response_dict),
                    projects_last_updated=timezone.now()
                )
            if response_dict:
                projects_json = response_dict
        ids, names = self._get_project_ids_names(platform.engine_name, projects_json)
        if package_name in ids:
            return package_name
        elif package_name in names:
            return ids[names.index(package_name)]
        else:
            return False

    def get_lang_id_name_dict(self, release_branch=None):
        """
        Generates {(locale, alias): language_name} dict
        """
        active_locales = self.get_locales(
            pick_locales=self.get_relbranch_locales(release_branch)
        ) if release_branch else self.get_locales_set()[0]
        lang_id_name = dict([((lang.locale_id, lang.locale_alias), lang.lang_name)
                             for lang in active_locales])
        return OrderedDict(sorted(lang_id_name.items(), key=operator.itemgetter(1)))

    def get_trans_stats(self, package_name, apply_branch_mapping=False, specify_branch=None):
        """
        fetch stats of a package for all enabled languages
        :param package_name: str
        :param apply_branch_mapping: boolean
        :param specify_branch: release branch name
        :return: dict {project_version: stats_dict}
        """
        trans_stats_dict = OrderedDict()
        package_desc = ''
        # 1st, get active locales for which stats are to be shown
        #      or, choose release branch specific locales
        lang_id_name = self.get_lang_id_name_dict(specify_branch) \
            if apply_branch_mapping and specify_branch else self.get_lang_id_name_dict()
        # 2nd, filter stats json for required locales
        if self.is_package_exist(package_name):
            package_details = self.get_packages([package_name]).get()
            if not (package_details.platform_last_updated or package_details.upstream_last_updated):
                return lang_id_name, trans_stats_dict, package_desc
            if package_details.package_details_json and package_details.package_details_json.get('description'):
                package_desc = package_details.package_details_json['description']
            pkg_stats_versions = self.syncstats_manager.get_sync_stats(pkgs=[package_name])
            for pkg_stats_version in pkg_stats_versions:
                trans_stats_list, missing_locales = \
                    self.syncstats_manager.filter_stats_for_required_locales(
                        package_details.platform_slug_id,
                        pkg_stats_version.stats_raw_json, list(lang_id_name),
                        pkg_stats_version.source
                    )
                if 'test' not in pkg_stats_version.project_version \
                        and 'extras' not in pkg_stats_version.project_version:
                    trans_stats_dict[pkg_stats_version.project_version] = \
                        self.syncstats_manager.extract_locale_translated(package_details.platform_slug_id,
                                                                         trans_stats_list,
                                                                         pkg_stats_version.source)
            if apply_branch_mapping and package_details.release_branch_mapping:
                branch_mapping = package_details.release_branch_mapping_json
                for relbranch, branch_mapping in branch_mapping.items():
                    trans_stats_dict[relbranch] = trans_stats_dict.get(branch_mapping.get(BRANCH_MAPPING_KEYS[0]), [])
        return lang_id_name, trans_stats_dict, package_desc

    def _get_pkg_and_ext(self, package_name):
        package = self.get_packages([package_name]).get()
        # extension for Transifex should be true, otherwise false
        extension = (True if package.platform_slug.engine_name == TRANSPLATFORM_ENGINES[0] else False)
        return package, extension

    def sync_update_package_details(self, package_name):
        """
        Sync with translation platform and update details in db for a package
        :param package_name: str
        :return: boolean
        """
        update_pkg_status = False
        package, ext = self._get_pkg_and_ext(package_name)
        platform = package.platform_slug
        project_details_response_dict = self.api_resources.fetch_project_details(
            platform.engine_name, platform.api_url, package_name,
            **(dict(auth_user=platform.auth_login_id, auth_token=platform.auth_token_key))
        )
        if project_details_response_dict:
            try:
                Package.objects.filter(platform_url=package.platform_url).update(
                    package_details_json_str=json.dumps(project_details_response_dict),
                    details_json_last_updated=timezone.now()
                )
            except Exception as e:
                self.app_logger(
                    'ERROR', "Package update failed, details: " + str(e))
            else:
                update_pkg_status = True
        return update_pkg_status

    def sync_update_package_stats(self, package_name):
        """
        Sync with translation platform and update trans stats in db for a package
        :param package_name: str
        :return: boolean
        """
        update_stats_status = False
        package, ext = self._get_pkg_and_ext(package_name)
        project, versions = parse_project_details_json(
            package.platform_slug.engine_name, package.package_details_json
        )
        for version in versions:
            proj_trans_stats_response_dict = {}
            if package.platform_slug.engine_name == TRANSPLATFORM_ENGINES[0]:
                # this is a quick fix for chinese in DamnedLies modules
                locales = [locale.locale_alias if 'zh' not in locale.locale_id else locale.locale_id
                           for locale in self.get_locales(only_active=True)]
                locales_stats_list = []
                for locale in locales:
                    locale_stats = self.api_resources.fetch_translation_statistics(
                        package.platform_slug.engine_name, package.platform_slug.api_url,
                        locale, version, **dict(package_name=package_name)
                    )
                    if locale_stats:
                        locales_stats_list.append(locale_stats)
                proj_trans_stats_response_dict.update({"id": version, "stats": locales_stats_list})
            else:
                proj_trans_stats_response_dict = self.api_resources.fetch_translation_statistics(
                    package.platform_slug.engine_name, package.platform_slug.api_url, project, version,
                    **dict(auth_user=package.platform_slug.auth_login_id,
                           auth_token=package.platform_slug.auth_token_key)
                )
            if proj_trans_stats_response_dict:
                processed_stats = {}
                # Process and Update locale-wise stats
                if self.PROCESS_STATS and proj_trans_stats_response_dict.get('stats'):
                    processed_stats = self._process_response_stats_json(
                        proj_trans_stats_response_dict['stats'], package.platform_slug.engine_name)

                if self.PROCESS_STATS and package.platform_slug.engine_name == TRANSPLATFORM_ENGINES[1] \
                        and not processed_stats:
                    processed_stats = self._process_response_stats_json_tx(
                        proj_trans_stats_response_dict)

                if self.syncstats_manager.save_version_stats(
                        package, version, proj_trans_stats_response_dict,
                        package.platform_slug.engine_name, p_stats=processed_stats
                ):
                    Package.objects.filter(platform_url=package.platform_url).update(
                        platform_last_updated=timezone.now())
                    update_stats_status = True
        # this makes sense if we create branch-mapping just after package sync
        self.build_branch_mapping(package_name)
        return update_stats_status

    @staticmethod
    def get_pkg_branch_mapping(pkg):
        return PackageBranchMapping(pkg).branch_mapping

    def build_branch_mapping(self, package_name):
        """
        Creates Branch mapping for the Package
        :param package_name: str
        :return: boolean
        """
        kwargs = {}
        branch_mapping_dict = self.get_pkg_branch_mapping(package_name)
        if not branch_mapping_dict:
            return False
        kwargs['package_name_mapping_json_str'] = json.dumps({package_name: ''})
        kwargs['release_branch_mapping'] = json.dumps(branch_mapping_dict)
        kwargs['release_branch_map_last_updated'] = timezone.now()
        try:
            Package.objects.filter(package_name=package_name).update(**kwargs)
        except Exception as e:
            self.app_logger(
                'ERROR', "Package branch mapping could not be saved, details: " + str(e))
        else:
            return True
        return False

    def filter_n_reduce_stats(self, locale_key, locale, locale_alias, stats_json):
        """
        Filter and reduce multiple statistics for single language
        :param locale_key: str
        :param locale: str
        :param locale_alias: str
        :param stats_json: dict
        :return: list
        """
        filter_n_reduced_stat = []

        def _reduce_stats_for_a_locale(stats):
            return [reduce(
                lambda x, y: x if x.get('translated', 0) > y.get('translated', 0)
                else y, stats
            )]

        filter_stat_locale = list(filter(
            lambda x: x[locale_key] == locale or
            x[locale_key].replace('-', '_') == locale,
            stats_json
        ))
        filter_stat_alias = list(filter(
            lambda x: x[locale_key] == locale_alias or
            x[locale_key].replace('_', '-') == locale_alias,
            stats_json
        ))

        if filter_stat_locale and len(filter_stat_locale) > 1:
            filter_stat_locale = _reduce_stats_for_a_locale(filter_stat_locale)

        if filter_stat_alias and len(filter_stat_alias) > 1:
            filter_stat_alias = _reduce_stats_for_a_locale(filter_stat_alias)

        if filter_stat_locale and filter_stat_alias:
            filter_n_reduced_stat = _reduce_stats_for_a_locale(
                filter_stat_locale + filter_stat_alias
            )
        elif filter_stat_locale and not filter_stat_alias:
            filter_n_reduced_stat = filter_stat_locale
        elif filter_stat_alias and not filter_stat_locale:
            filter_n_reduced_stat = filter_stat_alias

        return filter_n_reduced_stat

    def _process_response_stats_json(self, stats_json, engine=None):

        locale_key = 'locale'
        if engine and engine == TRANSPLATFORM_ENGINES[3]:
            locale_key = 'code'

        lang_id_name = self.get_lang_id_name_dict() or []
        processed_stats_json = {}
        for locale, l_alias in list(lang_id_name.keys()):
            filter_stat = {}
            try:
                filter_stat = self.filter_n_reduce_stats(
                    locale_key, locale, l_alias, stats_json
                )
            except Exception as e:
                self.app_logger(
                    'ERROR', "Error while filtering stats, details: " + str(e))
            else:
                filter_stat = filter_stat[0] \
                    if isinstance(filter_stat, list) and len(filter_stat) > 0 else {}
            processed_stats_json[locale] = {}
            processed_stats_json[locale]['Total'] = filter_stat.get('total', 0)
            processed_stats_json[locale]['Translated'] = filter_stat.get('translated', 0)
            processed_stats_json[locale]['Untranslated'] = \
                filter_stat.get('untranslated', 0) or \
                processed_stats_json[locale]['Total'] - processed_stats_json[locale]['Translated']
            remaining = 0
            try:
                remaining = (filter_stat.get('untranslated', processed_stats_json[locale]['Untranslated']) /
                             filter_stat.get('total', processed_stats_json[locale]['Total'])) * 100
            except ZeroDivisionError:
                # log error, pass for now
                pass
            processed_stats_json[locale]['Remaining'] = round(remaining, 2)
        return processed_stats_json

    def _process_response_stats_json_tx(self, stats_json):
        lang_id_name = self.get_lang_id_name_dict() or []

        processed_stats_json = {}
        for lang_alias_tuple in lang_id_name.keys():
            for locale, stats in stats_json.items():
                if locale in lang_alias_tuple:
                    filter_stats = {}
                    filter_stats['Translated'] = stats.get('translated_entities', 0)
                    filter_stats['Untranslated'] = stats.get('untranslated_entities', 0)
                    total_entities = stats.get('translated_entities', 0) + stats.get('untranslated_entities', 0)
                    filter_stats['Total'] = total_entities
                    remaining = 0
                    try:
                        remaining = (stats.get('untranslated_entities', 0.0) /
                                     total_entities) * 100
                    except ZeroDivisionError:
                        # log error, pass for now
                        pass
                    filter_stats['Remaining'] = round(remaining, 2)
                    processed_stats_json.update({lang_alias_tuple[0]: filter_stats})
        return processed_stats_json

    def refresh_package(self, package_name):
        """
        Sync Stats and Rebuild Mapping
        :param package_name: str
        :return: boolean
        """
        if not package_name:
            return False

        status = []
        steps = (
            self.sync_update_package_details,
            self.sync_update_package_stats
        )

        for method in steps:
            status.append(method(package_name))
        return True if [i for i in status if i] else False

    def _formats_stats_diff(self, lang_sequence, stats_diff_dict):
        lang_dict = {}
        [lang_dict.update({index: lang}) for index, lang in lang_sequence]
        formatted_stats_dict = OrderedDict()
        for branch, stats_diff in stats_diff_dict.items():
            formatted_stats_dict[branch] = {}
            buildsys_diff = stats_diff['buildsys']
            platform_diff_dict = dict(stats_diff['platform'])
            for lang_index, stat in buildsys_diff:
                formatted_stats_dict[branch][lang_dict.get(lang_index)] = \
                    (platform_diff_dict.get(lang_index, 0) - stat
                     if platform_diff_dict.get(lang_index, 0) > stat else 0)
        return formatted_stats_dict

    @staticmethod
    def _filter_pkg_branch_map(mapping):

        if not mapping:
            return {}
        mapping_dict = mapping.copy()
        for release, map_value in mapping.items():
            for k, v in map_value.items():
                if not map_value.get(k):
                    mapping_dict.pop(release)
        return mapping_dict

    def calculate_stats_diff(self, package, graph_ready_stats, pkg_branch_map):
        """
        Calculates and stores translation stats differences
         - first look for 100% in the build system
            - if not, then look for anything to pull from translation platform
        :param package: str
        :param graph_ready_stats: dict
        :param pkg_branch_map: dict
        :return: languages list and stats diff dict
        """

        pkg_branch_map = self._filter_pkg_branch_map(pkg_branch_map)

        stats_diff_dict = OrderedDict()
        stats_data = graph_ready_stats.get('graph_data', {})
        languages = graph_ready_stats.get('ticks', [])
        for branch, mapping in pkg_branch_map.items():
            stats_diff_dict[branch] = {}
            platform_stats = stats_data.get(mapping[BRANCH_MAPPING_KEYS[0]], [])
            buildsys_stats = stats_data.get(
                mapping[BRANCH_MAPPING_KEYS[1]] + " - " + mapping[BRANCH_MAPPING_KEYS[2]], []
            )
            # Ignoring after-decimal differences for now
            first_set = set(map(tuple, [(index, round(stat)) for index, stat in platform_stats]))
            second_set = set(map(tuple, [(index, round(stat)) for index, stat in buildsys_stats]))
            if first_set and second_set:
                platform_diff = first_set.difference(second_set)
                buildsys_diff = second_set.difference(first_set)
                # filter 100% translated languages from buildsys_diff
                buildsys_diff = set(map(tuple, [(i, j) for i, j in buildsys_diff if j < 100]))
                stats_diff_dict[branch]['platform'] = platform_diff
                stats_diff_dict[branch]['buildsys'] = buildsys_diff
            else:
                raise Exception("Make sure all mapped versions/tags are sync'd for stats.")
        polished_stats_diff = self._formats_stats_diff(languages, stats_diff_dict)
        if package and polished_stats_diff:
            self.update_package(package, {'stats_diff': json.dumps(polished_stats_diff)})
        return polished_stats_diff

    def is_package_build_latest(self, params):
        """
        Determine if new build is available for the package
        :param params: package_name, build_system, build_tag
        :return: boolean - True or False
        """
        if not isinstance(params, (list, tuple)) and not len(params) == 3:
            return
        package_name, build_system, build_tag = params
        product_hub_url = ''
        product = self.get_release_streams(built=build_system)
        if product:
            product_hub_url = product.first().product_server

        try:
            builds = self.api_resources.build_info(
                hub_url=product_hub_url,
                tag=build_tag,
                pkg=package_name
            )

            latest_build = {}
            if builds and len(builds) > 0:
                latest_build = builds[0]

            kwargs = {}
            package_qs = self.get_packages(pkgs=[package_name])
            kwargs.update(dict(package_name=package_qs.get()))
            kwargs.update(dict(build_system=build_system))
            kwargs.update(dict(build_tag=build_tag))

            try:
                cache_build_detail = CacheBuildDetails.objects.filter(**kwargs)
            except Exception as e:
                return False
            else:
                if cache_build_detail and \
                        cache_build_detail.first().build_details_json == latest_build:
                    return True
        except Exception:
            return False

        return

    def get_build_system_stats_by_release(self, release=None):
        """
        Get Build System Stats by Release
        :param release:
        :return:
        """
        releases = self.release_manager.get_release_branches(relbranch=release)
        build_system_stats_query_set = self.syncstats_manager.get_build_system_stats()
        stats_by_release = {release.release_slug: {} for release in releases}

        for sync_stats in build_system_stats_query_set:
            if isinstance(sync_stats.stats_raw_json, dict) and sync_stats.stats_raw_json.get('stats'):
                processed_stats = self._process_response_stats_json(sync_stats.stats_raw_json['stats'])
                pkg_branch_map = sync_stats.package_name.release_branch_mapping_json

                respective_release = [r for r, d in pkg_branch_map.items()
                                      if d and d.get(BRANCH_MAPPING_KEYS[2]) in sync_stats.project_version]
                if respective_release and len(respective_release) > 0:
                    pkg_release = respective_release[0]
                    if pkg_release in stats_by_release and not stats_by_release.get(pkg_release):
                        stats_by_release[pkg_release] = processed_stats
                    else:
                        for r_locale, r_stats in stats_by_release[pkg_release].items():
                            for k, v in r_stats.items():
                                if not k == 'Remaining':
                                    stats_by_release[pkg_release][r_locale][k] += \
                                        processed_stats.get(r_locale, {}).get(k, 0)

        if release and release in stats_by_release:
            return stats_by_release.get(release, {})
        return stats_by_release


class PackageBranchMapping(object):
    """
    Creates Branch Mapping
    """
    package = None
    package_name = None
    original_versions = None
    transplatform_versions = None
    release_branches_dict = None
    release_branches_list = None
    release_streams_list = None
    release_build_tags_dict = None

    syncstats_manager = SyncStatsManager()
    relbranch_manager = ReleaseBranchManager()

    def __init__(self, package_name):
        self.package_name = package_name
        try:
            self.package = Package.objects.filter(package_name=self.package_name).first()
        except Exception as e:
            # log event, passing for now
            pass
        else:
            pkg_stats = self.syncstats_manager.get_sync_stats(pkgs=[package_name], fields=('project_version',))
            self.original_versions = [pkg_stat.project_version for pkg_stat in pkg_stats]
            self.transplatform_versions = [
                pkg_stat.project_version.lower() for pkg_stat in self.syncstats_manager.get_sync_stats(
                    pkgs=[package_name], fields=('project_version',), sources=TRANSPLATFORM_ENGINES
                ) if isinstance(pkg_stat.project_version, str)]
            self.release_branches_dict = self.relbranch_manager.get_branches_of_relstreams(
                self.package.products, track_trans_flag=True)
            self.release_branches_list = []
            self.release_streams_list = []
            self.release_build_tags_dict = {}
            [self.release_branches_list.extend(branches) for _, branches in self.release_branches_dict.items()]
            [self.release_streams_list.extend([stream]) for stream, _ in self.release_branches_dict.items()
             if stream not in self.release_streams_list]
            for release_stream in self.release_streams_list:
                build_tags = self.relbranch_manager.get_relstream_build_tags(stream_slug=release_stream)
                if build_tags:
                    self.release_build_tags_dict.update(build_tags)

    def _get_stream_branch_belongs_to(self, branch):
        """
        Get stream to which a branch belongs to
        """
        for stream, branches in self.release_branches_dict.items():
            if branch in branches:
                return stream
        return ''

    def _sort_and_match_version_nm(self, release_branch, from_branches):
        """
        Sort versions matching stream and then try to match version number
        """
        belonging_stream = self._get_stream_branch_belongs_to(release_branch).lower()
        relevant_versions = [version for version in from_branches if belonging_stream in version]
        version_numbers = re.findall(r'\d+', release_branch)
        if len(version_numbers) >= 1:
            expected_version = [relevant_version for relevant_version in relevant_versions
                                if version_numbers[0] in relevant_version]
            if len(expected_version) >= 1:
                return True, expected_version[0]
        return False, ''

    def _check_release_version(self, branch, versions, shortform=None):
        """
        Match version numbers
        """
        short_form = shortform if shortform else ''
        version_numbers = re.findall(r'\d+', branch)
        if len(version_numbers) >= 1:
            short_form += str(version_numbers[0])
        return [version for version in versions if short_form in version]

    def _compare_with_short_names(self, release_branch, from_branches):
        """
        Try short forms combined with version number
        """
        belonging_stream = self._get_stream_branch_belongs_to(release_branch).lower()
        short_form = belonging_stream
        if belonging_stream == RELSTREAM_SLUGS[1]:
            short_form = 'f'
        expected_version = self._check_release_version(
            release_branch, from_branches, shortform=short_form
        )
        if len(expected_version) >= 1:
            return True, expected_version[0]
        return False, ''

    def _return_original_version(self, matched_version):
        required_version = [version for version in self.original_versions
                            if version.lower() == matched_version]
        return required_version[0] if len(required_version) == 1 else matched_version

    def calculate_branch_mapping(self, branch, from_branches):
        """
        Calculates branch mapping for a branch

        Algorithm:
        1. try with difflib, check version and return first found
        2. sort versions matching stream and then try to match version number
        3. try short forms combined with version number
        4. todo: fetch release dates and try matching with that
        5. try finding default version: 'master' may be
        6. if nothing works, return blank
        """
        match1 = difflib.get_close_matches(branch, from_branches)
        if len(match1) >= 1:
            match_found = self._check_release_version(branch, match1)
            if len(match_found) >= 1:
                return self._return_original_version(match_found[0])

        status1, match2 = self._sort_and_match_version_nm(branch, from_branches)
        if status1:
            return self._return_original_version(match2)

        status2, match3 = self._compare_with_short_names(branch, from_branches)
        if status2:
            return self._return_original_version(match3)

        probable_branches = ['default', 'master', 'head', 'rawhide', 'devel', 'app',
                             'core', 'translations', 'programs', self.package_name]

        for version in probable_branches:
            if version in from_branches:
                return self._return_original_version(version)

        for version in from_branches:
            closest_ver = difflib.get_close_matches(version, probable_branches)
            if isinstance(closest_ver, list) and len(closest_ver) > 0:
                return self._return_original_version(version)

        for version in from_branches:
            if self.package_name in version:
                return self._return_original_version(version)

        return ''

    @property
    def versions(self):
        return self.transplatform_versions

    @property
    def release_branches(self):
        return self.release_branches_list

    @property
    def branch_mapping(self):
        """
        Creates branch mapping based on rule
        :return: dict
        """
        branch_mapping_dict = {}
        required_params = (self.transplatform_versions, self.release_branches_dict,
                           self.release_streams_list, self.release_build_tags_dict)
        valid_params = [param for param in required_params if param]

        if len(required_params) == len(valid_params):
            for stream, branches in self.release_branches_dict.items():
                for branch in branches:
                    branch_mapping_dict[branch] = {}
                    branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[0]] = \
                        self.calculate_branch_mapping(branch, self.transplatform_versions)
                    branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[1]] = \
                        self.relbranch_manager.get_relstream_buildsys(stream)
                    branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[2]] = \
                        self.calculate_branch_mapping(branch, sorted(
                            self.release_build_tags_dict[stream]))

                    if not branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[0]] \
                            and self.package.platform_slug_id in DAMNEDLIES_SLUGS:
                        release_stream = self.relbranch_manager.get_release_streams(
                            stream_slug=stream,
                            built=branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[1]],
                            fields=('product_server',)
                        )
                        if release_stream:
                            release_stream_hub_url = release_stream.get().product_server or ''
                            build_info = self.relbranch_manager.api_resources.build_info(
                                hub_url=release_stream_hub_url,
                                tag=branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[2]],
                                pkg=self.package_name
                            )
                            if build_info and isinstance(build_info, list) and len(build_info) > 0:
                                version_from_latest_build = build_info[0].get('version')
                                seek_version = "-".join(version_from_latest_build.split('.')[0:2])
                                for version in self.transplatform_versions:
                                    if seek_version in version:
                                        branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[0]] = version
                                # seek next (nearest) version
                                if not branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[0]]:
                                    version_x, version_y = version_from_latest_build.split('.')[0:2]
                                    first_place_matched_versions = \
                                        [version for version in self.transplatform_versions
                                         if version_x in version]
                                    if first_place_matched_versions and len(first_place_matched_versions) > 0:
                                        probable_versions = [int(version.split('-')[0:3][2])
                                                             for version in first_place_matched_versions]
                                        version_y = int(version_y)
                                        located_version = max(probable_versions, key=lambda x: abs(x + version_y))
                                        if located_version:
                                            required_version = [ver for ver in first_place_matched_versions
                                                                if str(located_version) in ver]
                                            if required_version and len(required_version) > 0:
                                                branch_mapping_dict[branch][BRANCH_MAPPING_KEYS[0]] = required_version[0]
        return branch_mapping_dict
