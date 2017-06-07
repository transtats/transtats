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

# Application inventories:
#       Languages,
#       Translation Platforms,
#       Release Streams, and Branches
#       Packages

# python
import io
import re
import difflib
import operator
from collections import OrderedDict
from uuid import uuid4

# third party
import requests
from slugify import slugify

# django
from django.utils import timezone

# dashboard
from dashboard.managers.base import BaseManager
from dashboard.models import (
    TransPlatform, Languages, LanguageSet,
    ReleaseStream, StreamBranches, Packages, SyncStats
)
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, ZANATA_SLUGS,
    TRANSIFEX_SLUGS, RELSTREAM_SLUGS
)
from dashboard.managers.utilities import (
    parse_project_details_json, parse_ical_file
)


__all__ = ['InventoryManager', 'SyncStatsManager', 'PackagesManager',
           'ReleaseBranchManager', 'PackageBranchMapping']


class InventoryManager(BaseManager):
    """
    Manage application inventories
    """

    def get_locales(self, only_active=None, pick_locales=None):
        """
        fetch all languages from db
        """
        filter_kwargs = {}
        if only_active:
            filter_kwargs.update(dict(lang_status=True))
        if pick_locales:
            filter_kwargs.update(dict(locale_id__in=pick_locales))

        locales = []
        try:
            locales = Languages.objects.filter(**filter_kwargs) \
                .order_by('lang_name').order_by('-lang_status')
        except Exception as e:
            self.app_logger(
                'ERROR', "locales could not be fetched for " +
                         str(filter_kwargs) + " kwargs, details: " + str(e)
            )
        return locales

    def get_locale_alias(self, locale):
        """
        Fetch alias of a locale
        :param locale: str
        :return: alias: str
        """
        locale_qset = self.get_locales(pick_locales=[locale])
        return locale_qset.get().locale_alias if locale_qset else locale

    def get_locale_lang_tuple(self, locales=None):
        """
        Creates locale
        """
        locales = self.get_locales(pick_locales=locales) \
            if locales else self.get_locales(only_active=True)
        return tuple([(locale.locale_id, locale.lang_name)
                      for locale in locales])

    def get_locales_set(self):
        """
        Creates locales set on the basis of status
        :return: tuple
        """
        locales = self.get_locales()
        if not locales:
            return
        active_locales = [locale for locale in locales if locale.lang_status]
        inactive_locales = list(set(locales) - set(active_locales))
        aliases = list(filter(lambda locale: locale.locale_alias is not None, locales))
        return active_locales, inactive_locales, aliases

    def get_langset(self, langset_slug, fields=None):
        """
        fetch desired language set from db
        """
        langset = None
        fetch_fields = []
        if fields and isinstance(fields, (tuple, list)):
            fetch_fields.extend(fields)
        try:
            langset = LanguageSet.objects.only(*fetch_fields).filter(lang_set_slug=langset_slug).first()
        except Exception as e:
            self.app_logger(
                'ERROR', "language set could not be fetched for " +
                         langset_slug + ", details: " + str(e)
            )
            pass
        return langset

    def get_langsets(self, fields=None):
        """
        fetch all language sets from db
        """
        langsets = None
        filter_fields = fields if isinstance(fields, (tuple, list)) else ()
        filter_kwargs = {}
        try:
            langsets = LanguageSet.objects.only(*filter_fields).filter(**filter_kwargs).all()
        except Exception as e:
            self.app_logger(
                'ERROR', "language sets could not be fetched, details: " + str(e)
            )
        return langsets

    def get_locale_groups(self, locale):
        """
        fetch list of langlist, a locale belongs to
        """
        groups_locale_belongs_to = []
        lang_sets = self.get_langsets()
        for langset in lang_sets:
            if locale in langset.locale_ids:
                groups_locale_belongs_to.append(langset.lang_set_slug)
        return {locale: groups_locale_belongs_to}

    def get_all_locales_groups(self):
        """
        get_locale_groups for all available locales
        """
        all_locales_groups = {}
        for locale in self.get_locales():
            all_locales_groups.update(self.get_locale_groups(locale.locale_id))
        return all_locales_groups

    def get_relbranch_locales(self, release_branch):
        """
        Fetch locales specific to release branch
        """
        required_locales = []
        try:
            release_branch_specific_lang_set = \
                StreamBranches.objects.only('lang_set').filter(relbranch_slug=release_branch).first()
            required_lang_set = self.get_langset(
                release_branch_specific_lang_set.lang_set, fields=('locale_ids')
            )
            required_locales = required_lang_set.locale_ids if required_lang_set else []
        except Exception as e:
            self.app_logger(
                'ERROR', ("locales could not be fetched for " +
                          release_branch + " release branch, details: " + str(e))
            )
        return required_locales

    def get_translation_platforms(self, engine=None, only_active=None):
        """
        fetch all translation platforms from db
        """
        filter_kwargs = {}
        if engine:
            filter_kwargs.update(dict(engine_name=engine))
        if only_active:
            filter_kwargs.update(dict(server_status=True))

        platforms = None
        try:
            platforms = TransPlatform.objects.filter(**filter_kwargs) \
                .order_by('platform_id')
        except Exception as e:
            self.app_logger(
                'ERROR', "translation platforms could not be fetched, details: " + str(e)
            )
        return platforms

    def get_transplatforms_set(self):
        """
        Creates transplatform set on the basis of status
        :return: tuple
        """
        platforms = self.get_translation_platforms()
        if not platforms:
            return
        active_platforms = [platform for platform in platforms if platform.server_status]
        inactive_platforms = list(set(platforms) - set(active_platforms))
        return active_platforms, inactive_platforms

    def get_transplatform_slug_url(self):
        """
        Get slug and api_url for active transplatform
        :return: tuple
        """
        active_platforms = self.get_translation_platforms(only_active=True)
        return tuple([(platform.platform_slug, platform.api_url)
                      for platform in active_platforms]) or ()

    def get_release_streams(self, stream_slug=None, only_active=None):
        """
        Fetch all release streams from the db
        """
        filter_kwargs = {}
        if only_active:
            filter_kwargs.update(dict(relstream_status=True))
        if stream_slug:
            filter_kwargs.update(dict(relstream_slug=stream_slug))

        relstreams = None
        try:
            relstreams = ReleaseStream.objects.filter(**filter_kwargs) \
                .order_by('relstream_id')
        except Exception as e:
            self.app_logger(
                'ERROR', "release streams could not be fetched, details: " + str(e)
            )
        return relstreams

    def get_relstream_slug_name(self):
        """
        Get slug and name for active relstream
        :return: tuple
        """
        active_streams = self.get_release_streams(only_active=True)
        return tuple([(stream.relstream_slug, stream.relstream_name)
                      for stream in active_streams]) or ()


class SyncStatsManager(BaseManager):
    """
    Sync Translation Stats Manager
    """

    def get_sync_stats(self, pkgs=None, fields=None, versions=None):
        """
        fetch sync translation stats from db
        :return: resultset
        """
        sync_stats = None
        required_params = fields if fields and isinstance(fields, (list, tuple)) \
            else ('package_name', 'project_version', 'stats_raw_json')
        kwargs = {}
        kwargs.update(dict(sync_visibility=True))
        if pkgs:
            kwargs.update(dict(package_name__in=pkgs))
        if versions:
            kwargs.update(dict(project_version__in=versions))

        try:
            sync_stats = SyncStats.objects.only(*required_params).filter(**kwargs).all()
        except Exception as e:
            self.app_logger(
                'ERROR', "Sync stats could not be fetched, details: " + str(e)
            )
        return sync_stats

    def filter_stats_for_required_locales(self, transplatform_slug, stats_json, locales):
        """
        Filter stats json for required locales
        :param transplatform_slug: str
        :param stats_json: dict
        :param locales: list
        :return: stats list, missing locales tuple
        """
        trans_stats = []
        locales_found = []

        if transplatform_slug in ZANATA_SLUGS:
            if not stats_json.get('stats'):
                return trans_stats, ()
            for stats_param in stats_json['stats']:
                stats_param_locale = stats_param.get('locale', '')
                for locale_tuple in locales:
                    if (stats_param_locale in locale_tuple) or \
                            (stats_param_locale.replace('-', '_') in locale_tuple):
                        trans_stats.append(stats_param)
                    else:
                        locales_found.append(locale_tuple)

        elif transplatform_slug in TRANSIFEX_SLUGS:
            for locale_tuple in locales:
                if stats_json.get(locale_tuple[0]):
                    trans_stats.append({locale_tuple[0]: stats_json[locale_tuple[0]]})
                    locales_found.append(locale_tuple)
                elif stats_json.get(locale_tuple[1]):
                    trans_stats.append({locale_tuple[1]: stats_json[locale_tuple[1]]})
                    locales_found.append(locale_tuple)

        return trans_stats, tuple(set(locales) - set(locales_found))

    def extract_locale_translated(self, transplatform_slug, stats_dict_list):
        """
        Compute %age of translation for each locale
        :param transplatform_slug:str
        :param stats_dict_list:list
        :return:locale translated list
        """
        locale_translated = []

        if transplatform_slug in ZANATA_SLUGS:
            for stats_dict in stats_dict_list:
                translation_percent = \
                    round((stats_dict.get('translated') * 100) / stats_dict.get('total'), 2) \
                    if stats_dict.get('total') > 0 else 0
                locale_translated.append([stats_dict.get('locale'), translation_percent])
        elif transplatform_slug in TRANSIFEX_SLUGS:
            for stats_dict in stats_dict_list:
                for locale, stat_params in stats_dict.items():
                    locale_translated.append([locale, int(stat_params.get('completed')[:-1])])

        return locale_translated


class PackagesManager(InventoryManager):
    """
    Packages Manager
    """

    syncstats_manager = SyncStatsManager()

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
            packages = Packages.objects.only(*fields).filter(**kwargs) \
                .order_by('-transtats_lastupdated')
        except Exception as e:
            self.app_logger(
                'ERROR', "Packages could not be fetched, details: " + str(e)
            )
        return packages

    def get_relbranch_specific_pkgs(self, release_branch, fields=None):
        """
        fetch release branch specific packages from db
        """
        packages = ()
        fields_required = fields if fields else ()
        try:
            packages = Packages.objects.only(*fields_required) \
                .filter(release_branch_mapping__has_key=release_branch) \
                .order_by('-transtats_lastupdated')
        except Exception as e:
            self.app_logger(
                'ERROR', ("release branch specific package could not be fetched for " +
                          release_branch + " release branch, details: " + str(e))
            )
        return packages

    def count_packages(self):
        """
        packages count
        """
        packages = self.get_packages()
        return packages.count() if packages else 0

    def get_package_name_tuple(self, check_mapping=False):
        """
        returns (package_name, upstream_name) tuple (only sync'd ones)
        """
        packages = self.get_packages()
        name_list = [(package.package_name, package.upstream_name) for package in packages
                     if package.transtats_lastupdated]
        if check_mapping:
            name_list = [(package.package_name, package.package_name) for package in packages
                         if package.transtats_lastupdated and package.package_name_mapping]
        return tuple(sorted(name_list))

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
            # derive transplatform project URL
            platform = TransPlatform.objects.only('engine_name', 'api_url') \
                .filter(platform_slug=kwargs['transplatform_slug']).get()
            # get rest handle
            rest_handle = self.rest_client(platform.engine_name, platform.api_url)
            resp_dict = None
            if platform.engine_name == TRANSPLATFORM_ENGINES[0]:
                resp_dict = rest_handle.process_request(
                    'project_details', kwargs['package_name'], ext=True
                )
                if resp_dict and resp_dict.get('json_content'):
                    tx_org_slug = resp_dict['json_content']['organization']['slug']
                    kwargs['transplatform_url'] = platform.api_url + "/" + tx_org_slug + "/" + kwargs['package_name']
            elif platform.engine_name == TRANSPLATFORM_ENGINES[1]:
                kwargs['transplatform_url'] = platform.api_url + "/project/view/" + kwargs['package_name']
                resp_dict = rest_handle.process_request('project_details', kwargs['package_name'])

            if kwargs.get('update_stats') == 'stats':
                kwargs.pop('update_stats')
                # fetch project details from transplatform and save in db
                if resp_dict and resp_dict.get('json_content'):
                    kwargs['package_details_json'] = resp_dict['json_content']
                    kwargs['details_json_lastupdated'] = timezone.now()
                    # fetch project_version stats from transplatform and save in db
                    project, versions = parse_project_details_json(platform.engine_name, resp_dict['json_content'])
                    for version in versions:
                        # extension for Zanata should be true, otherwise false
                        extension = True if platform.engine_name == TRANSPLATFORM_ENGINES[1] else False
                        response_dict = rest_handle.process_request(
                            'proj_trans_stats', project, version, extension
                        )
                        if response_dict and response_dict.get('json_content'):
                            if self._save_version_stats(
                                project, version, response_dict['json_content']
                            ):
                                kwargs['transtats_lastupdated'] = timezone.now()

            if 'update_stats' in kwargs:
                del kwargs['update_stats']

            kwargs['transplatform_slug'] = platform
            kwargs['transplatform_name'] = kwargs['package_name']
            kwargs['upstream_name'] = kwargs['upstream_url'].split('/')[-1]
            # save in db
            new_package = Packages(**kwargs)
            new_package.save()
        except:
            # log event, pass for now
            # todo - implement error msg handling
            return False
        else:
            return True

    def _save_version_stats(self, project, version, stats_json):
        """
        Save version's translation stats in db
        :param project: transplatform project
        :param version: transplatform project's version
        :param stats_json: translation stats dict
        :return: boolean
        """
        try:
            existing_sync_stat = SyncStats.objects.filter(package_name=project,
                                                          project_version=version).first()
            sync_uuid = uuid4()
            if not existing_sync_stat:
                params = {}
                params.update(dict(package_name=project))
                params.update(dict(job_uuid=sync_uuid))
                params.update(dict(project_version=version))
                params.update(dict(stats_raw_json=stats_json))
                params.update(dict(sync_iter_count=1))
                params.update(dict(sync_visibility=True))
                new_sync_stats = SyncStats(**params)
                new_sync_stats.save()
            else:
                SyncStats.objects.filter(package_name=project, project_version=version).update(
                    job_uuid=sync_uuid, stats_raw_json=stats_json,
                    sync_iter_count=existing_sync_stat.sync_iter_count + 1
                )
        except Exception as e:
            self.app_logger(
                'ERROR', "version stats could not be saved, details: " + str(e))
        else:
            return True
        return False

    def _get_project_ids_names(self, engine, projects):
        ids = []
        names = []
        if isinstance(projects, list) and engine == TRANSPLATFORM_ENGINES[1]:
            for project in projects:
                ids.append(project['id'])
                names.append(project['name'])
        elif isinstance(projects, dict) and engine == TRANSPLATFORM_ENGINES[0]:
            ids.append(projects.get('slug'))
            names.append(projects.get('name'))
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
        # get transplatform projects from db
        platform = TransPlatform.objects.only('engine_name', 'api_url', 'projects_json') \
            .filter(platform_slug=kwargs['transplatform_slug']).get()
        projects_json = platform.projects_json
        # if not found in db, fetch transplatform projects from API
        if not projects_json:
            rest_handle = self.rest_client(platform.engine_name, platform.api_url)
            response_dict = None
            if platform.engine_name == TRANSPLATFORM_ENGINES[0]:
                response_dict = rest_handle.process_request(
                    'project_details', package_name.lower()
                )
            if platform.engine_name == TRANSPLATFORM_ENGINES[1]:
                response_dict = rest_handle.process_request('list_projects')
            if response_dict and response_dict.get('json_content'):
                # save projects_json in db
                TransPlatform.objects.filter(api_url=platform.api_url).update(
                    projects_json=response_dict['json_content'], projects_lastupdated=timezone.now()
                )
                projects_json = response_dict['json_content']

        ids, names = self._get_project_ids_names(platform.engine_name, projects_json)
        if package_name in ids:
            return package_name
        elif package_name in names:
            return ids[names.index(package_name)]
        else:
            return False

    def _get_lang_id_name_dict(self, release_branch=None):
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
        :return: dict {project_version: stats_dict}
        """
        trans_stats_dict = OrderedDict()
        package_desc = ''
        # 1st, get active locales for which stats are to be shown
        #      or, choose release branch specific locales
        lang_id_name = self._get_lang_id_name_dict(specify_branch) \
            if apply_branch_mapping and specify_branch else self._get_lang_id_name_dict()
        # 2nd, filter stats json for required locales
        package_details = self.get_packages([package_name])[0]  # this must be a list
        if not package_details.transtats_lastupdated:
            return trans_stats_dict
        if package_details.package_details_json.get('description'):
            package_desc = package_details.package_details_json['description']
        pkg_stats_versions = self.syncstats_manager.get_sync_stats([package_name])
        for pkg_stats_version in pkg_stats_versions:
            trans_stats_list, missing_locales = \
                self.syncstats_manager.filter_stats_for_required_locales(
                    package_details.transplatform_slug_id,
                    pkg_stats_version.stats_raw_json, list(lang_id_name)
                )
            if 'test' not in pkg_stats_version.project_version:
                trans_stats_dict[pkg_stats_version.project_version] = \
                    self.syncstats_manager.extract_locale_translated(package_details.transplatform_slug_id,
                                                                     trans_stats_list)
        if apply_branch_mapping and package_details.release_branch_mapping:
            branch_mapping = package_details.release_branch_mapping
            for relbranch, transplatform_version in branch_mapping.items():
                trans_stats_dict[relbranch] = trans_stats_dict.get(transplatform_version, [])
        return lang_id_name, trans_stats_dict, package_desc

    def _get_rest_handle_and_pkg(self, package_name):
        """
        Returns REST handle for a package
        """
        package = self.get_packages([package_name]).get()
        rest_handle = self.rest_client(package.transplatform_slug.engine_name,
                                       package.transplatform_slug.api_url)
        # extension for Transifex should be true, otherwise false
        extension = (True if package.transplatform_slug.engine_name == TRANSPLATFORM_ENGINES[0] else False)
        return rest_handle, extension, package

    def sync_update_package_details(self, package_name):
        """
        Sync with translation platform and update details in db for a package
        :param package_name: str
        :return: boolean
        """
        update_pkg_status = False
        rest_handle, ext, package = self._get_rest_handle_and_pkg(package_name)
        # Package name can be diff from its id/slug, hence extracting from url
        transplatform_project_name = package.transplatform_url.split('/')[-1]
        project_details_response_dict = rest_handle.process_request(
            'project_details', transplatform_project_name, ext=ext
        )
        if project_details_response_dict and project_details_response_dict.get('json_content'):
            try:
                Packages.objects.filter(transplatform_url=package.transplatform_url).update(
                    package_details_json=project_details_response_dict['json_content'],
                    details_json_lastupdated=timezone.now()
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
        rest_handle, ext, package = self._get_rest_handle_and_pkg(package_name)
        project, versions = parse_project_details_json(
            package.transplatform_slug.engine_name, package.package_details_json
        )
        for version in versions:
            proj_trans_stats_response_dict = rest_handle.process_request(
                'proj_trans_stats', project, version, ext
            )
            if proj_trans_stats_response_dict and proj_trans_stats_response_dict.get('json_content'):
                if self._save_version_stats(
                        project, version, proj_trans_stats_response_dict['json_content']
                ):
                    Packages.objects.filter(transplatform_url=package.transplatform_url).update(
                        transtats_lastupdated=timezone.now())
                    update_stats_status = True
        return update_stats_status

    def build_branch_mapping(self, package_name):
        """
        Creates Branch mapping for the Package
        :param package_name: str
        :return: boolean
        """
        kwargs = {}
        branch_mapping_dict = PackageBranchMapping(package_name).branch_mapping
        kwargs['package_name_mapping'] = {package_name: ''}
        kwargs['release_branch_mapping'] = branch_mapping_dict
        kwargs['mapping_lastupdated'] = timezone.now()
        try:
            Packages.objects.filter(package_name=package_name).update(**kwargs)
        except Exception as e:
            self.app_logger(
                'ERROR', "Package branch mapping could not be saved, details: " + str(e))
        else:
            return True
        return False

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


class ReleaseBranchManager(InventoryManager):
    """
    Release Stream Branch Manager
    """

    def get_release_branches(self, relstream=None, relbranch=None, fields=None):
        """
        Get release stream branches from db
        :param relstream: release stream slug
        :param fields: fields tuple/list which are to be fetched
        :return:relbranch queryset
        """
        required_fields = []
        if fields and isinstance(fields, (list, tuple)):
            required_fields.extend(fields)

        filter_kwargs = {}
        if relstream:
            filter_kwargs.update(dict(relstream_slug=relstream))
        if relbranch:
            filter_kwargs.update(dict(relbranch_slug=relbranch))

        relbranches = None
        try:
            relbranches = StreamBranches.objects.only(*required_fields).filter(**filter_kwargs)
        except Exception as e:
            self.app_logger(
                'ERROR', "Release branches could not be fetched, details: " + str(e))
        return relbranches

    def get_relbranch_name_slug_tuple(self):
        """
        Get release branch slug and name tuple
        :return: (('master', 'master'), )
        """
        release_branches = self.get_release_branches(
            fields=('relbranch_slug', 'relbranch_name', 'track_trans_flag')
        )
        return tuple([(branch.relbranch_slug, branch.relbranch_name)
                      for branch in release_branches if branch.track_trans_flag])

    def get_branches_of_relstreams(self, release_streams):
        """
        Retrieve all branches of input release streams
        :param release_streams: release stream slugs
        :return: dict
        """
        if not release_streams:
            return
        branches_of_relstreams = {}
        fields = ('relstream_slug', 'relbranch_slug')
        try:
            relbranches = StreamBranches.objects.only(*fields).filter(
                relstream_slug__in=release_streams).all()
        except Exception as e:
            self.app_logger(
                'ERROR', "Branches of release streams could not be fetched, details: " + str(e))
        else:
            if relbranches:
                stream_branches = [{i.relstream_slug: i.relbranch_slug} for i in relbranches]
                for r_stream in release_streams:
                    branches_of_relstreams[r_stream] = []
                    for relbranch in stream_branches:
                        branches_of_relstreams[r_stream].extend(
                            [branch for stream, branch in relbranch.items() if stream == r_stream]
                        )
        return branches_of_relstreams

    def get_calender_events_dict(self, ical_url, relstream_slug):
        """
        Fetches iCal contents over http and converts into dict
        :param ical_url: caldendar url
        :return: events dict_list
        """
        try:
            rest_response = requests.get(ical_url, verify=False)
        except Exception as e:
            self.app_logger(
                'ERROR', "No calender events found, details: " + str(e))
            return {}
        else:
            ical_contents_array = [line.strip() for line in io.StringIO(rest_response.text)]
            return parse_ical_file(ical_contents_array, relstream_slug)

    def parse_events_for_required_milestones(self, relstream_slug, relbranch_slug,
                                             ical_events, required_events):
        """
        Parse ical events for required milestones
        :param: relbranch_slug: str
        :param ical_events: ical events dict
        :param required_events: list
        :return: schedule dict of a release branch, False if fails
        """
        DELIMITER = ":"
        branch_schedule_dict = OrderedDict()

        if relstream_slug == RELSTREAM_SLUGS[0]:
            try:
                for event in required_events:
                    for event_dict in ical_events:
                        if (event.lower() in event_dict.get('SUMMARY').lower() and
                                relbranch_slug in event_dict.get('SUMMARY').lower()):
                            key = DELIMITER.join(event_dict.get('SUMMARY').split(DELIMITER)[1:])
                            branch_schedule_dict[key] = event_dict.get('DTEND', '')

            except Exception as e:
                self.app_logger(
                    'WARNING', "Parsing failed for " + relstream_slug + ", details: " + str(e))
                return False
        elif relstream_slug == RELSTREAM_SLUGS[1]:
            try:
                for event in required_events:
                    for event_dict in ical_events:
                        if event.lower() in event_dict.get('SUMMARY').lower():
                            branch_schedule_dict[event_dict.get('SUMMARY')] = \
                                (event_dict.get('DUE', '') or event_dict.get('DTSTART', ''))[:8]
            except Exception as e:
                self.app_logger(
                    'WARNING', "Parsing failed for " + relstream_slug + ", details: " + str(e))
                return False
        return branch_schedule_dict

    def validate_branch(self, relstream, **kwargs):
        """
        Validate iCal URL for a branch
        :return: boolean
        """
        if 'calendar_url' not in kwargs:
            return False
        ical_url = kwargs.get('calendar_url')
        relbranch_slug = slugify(kwargs.get('relbranch_name', ''))
        release_stream = self.get_release_streams(stream_slug=relstream).get()
        ical_events = self.get_calender_events_dict(ical_url, release_stream.relstream_slug)
        required_events = release_stream.major_milestones
        return relbranch_slug, \
            self.parse_events_for_required_milestones(
                release_stream.relstream_slug, relbranch_slug, ical_events, required_events)

    def add_relbranch(self, relstream_slug, **kwargs):
        """
        Save release branch in db
        :param relstream_slug: str
        :param post_params: dict
        :return: boolean
        """
        if not relstream_slug:
            return False
        required_params = ('relbranch_name', 'lang_set', 'current_phase',
                           'calendar_url', 'schedule_json', 'relbranch_slug')
        if not set(required_params) <= set(kwargs.keys()):
            return False
        if not (kwargs['relbranch_name'] and kwargs['calendar_url']):
            return False
        flags = kwargs.pop('enable_flags') if 'enable_flags' in kwargs else []
        try:
            kwargs['relstream_slug'] = relstream_slug
            kwargs['scm_branch'] = None
            kwargs['created_on'] = timezone.now()
            kwargs['sync_calendar'] = True if 'sync_calendar' in flags else False
            kwargs['notifications_flag'] = True if 'notifications_flag' in flags else False
            kwargs['track_trans_flag'] = True if 'track_trans_flag' in flags else False
            new_relstream_branch = StreamBranches(**kwargs)
            new_relstream_branch.save()
        except Exception as e:
            self.app_logger(
                'ERROR', "Release branch could not be added, details: " + str(e))
            return False
        else:
            return True


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

    syncstats_manager = SyncStatsManager()
    relbranch_manager = ReleaseBranchManager()

    def __init__(self, package_name):
        self.package_name = package_name
        try:
            self.package = Packages.objects.filter(package_name=self.package_name).first()
        except Exception as e:
            # log event, passing for now
            pass
        else:
            pkg_stats = self.syncstats_manager.get_sync_stats(pkgs=[package_name], fields=('project_version',))
            self.original_versions = [pkg_stat.project_version for pkg_stat in pkg_stats]
            self.transplatform_versions = [version.lower() for version in self.original_versions]
            self.release_branches_dict = self.relbranch_manager.get_branches_of_relstreams(self.package.release_streams)
            self.release_branches_list = []
            self.release_streams_list = []
            [self.release_branches_list.extend(branches) for _, branches in self.release_branches_dict.items()]
            [self.release_streams_list.extend([stream]) for stream, _ in self.release_branches_dict.items()
             if stream not in self.release_streams_list]

    def _get_stream_branch_belongs_to(self, branch):
        """
        Get stream to which a branch belongs to
        """
        for stream, branches in self.release_branches_dict.items():
            if branch in branches:
                return stream
        return ''

    def _sort_and_match_version_nm(self, release_branch):
        """
        Sort versions matching stream and then try to match version number
        """
        belonging_stream = self._get_stream_branch_belongs_to(release_branch).lower()
        relevant_versions = [version for version in self.transplatform_versions if belonging_stream in version]
        version_numbers = re.findall(r'\d+', release_branch)
        if len(version_numbers) >= 1:
            expected_version = [relevant_version for relevant_version in relevant_versions
                                if version_numbers[0] in relevant_version]
            if len(expected_version) >= 1:
                return True, expected_version[0]
        return False, ''

    def _check_release_version(self, branch, shortform=None, versions=None):
        """
        Match version numbers
        """
        short_form = shortform if shortform else ''
        version_numbers = re.findall(r'\d+', branch)
        if len(version_numbers) >= 1:
            short_form += str(version_numbers[0])
        match_versions = versions if versions and isinstance(versions, (list, tuple)) \
            else self.transplatform_versions
        return [version for version in match_versions if short_form in version]

    def _compare_with_short_names(self, release_branch):
        """
        Try short forms combined with version number
        """
        belonging_stream = self._get_stream_branch_belongs_to(release_branch).lower()
        short_form = belonging_stream
        if belonging_stream == RELSTREAM_SLUGS[1]:
            short_form = 'f'
        expected_version = self._check_release_version(release_branch, shortform=short_form)
        if len(expected_version) >= 1:
            return True, expected_version[0]
        return False, ''

    def _return_origin_version(self, matched_version):
        return self.original_versions[self.transplatform_versions.index(matched_version)]

    def calculate_branch_mapping(self, branch):
        """
        Calculates branch mapping for a branch

        Algorithm:
        1. try with difflib, check version and return first found
        2. sort versions matching stream and then try to match version number
        3. try short forms combined with version number
        4. todo: fetch release dates and try matching with that
        5. try finding default version: 'master' may be
        6. if nothing works, return blank

        This seems working for Zanata, todo - need to check with others too.
        """
        match1 = difflib.get_close_matches(branch, self.transplatform_versions)
        if len(match1) >= 1:
            match_found = self._check_release_version(branch, versions=match1)
            if len(match_found) >= 1:
                return self._return_origin_version(match_found[0])

        status1, match2 = self._sort_and_match_version_nm(branch)
        if status1:
            return self._return_origin_version(match2)

        status2, match3 = self._compare_with_short_names(branch)
        if status2:
            return self._return_origin_version(match3)

        if 'master' in self.transplatform_versions:
            return self._return_origin_version('master')
        elif 'default' in self.transplatform_versions:
            return self._return_origin_version('default')
        elif 'devel' in self.transplatform_versions:
            return self._return_origin_version('devel')
        else:
            return ''

    def branch_stats(self, release_branch):
        """
        Generates stats for a specific release branch
        :param release_branch: release branch slug
        :return: dict
        """
        if not release_branch:
            return {}
        transplatform_version = self.branch_mapping.get(release_branch)
        pkg_stats_query_set = self.syncstats_manager.get_sync_stats(
            pkgs=[self.package_name], versions=[transplatform_version]
        )
        pkg_stats_json = pkg_stats_query_set.first().stats_raw_json \
            if pkg_stats_query_set else {}
        return pkg_stats_json

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
                           self.release_branches_list, self.release_streams_list)
        valid_params = [param for param in required_params if param]

        if len(required_params) == len(valid_params):
            for branch in self.release_branches_list:
                branch_mapping_dict[branch] = self.calculate_branch_mapping(branch)

        return branch_mapping_dict
