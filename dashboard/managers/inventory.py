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
    TransPlatform, Languages, ReleaseStream,
    StreamBranches, Packages, SyncStats
)
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, ZANATA_SLUGS,
    TRANSIFEX_SLUGS, RELSTREAM_SLUGS
)
from dashboard.managers.utilities import (
    parse_project_details_json, parse_ical_file
)


__all__ = ['InventoryManager', 'SyncStatsManager',
           'PackagesManager', 'ReleaseBranchManager']


class InventoryManager(BaseManager):
    """
    Manage application inventories
    """

    def get_locales(self, only_active=None):
        """
        fetch all languages from db
        """
        filter_kwargs = {}
        if only_active:
            filter_kwargs.update(dict(lang_status=True))

        locales = None
        try:
            locales = Languages.objects.filter(**filter_kwargs) \
                .order_by('lang_name').order_by('-lang_status')
        except:
            # log event, passing for now
            pass
        return locales

    def get_locale_lang_tuple(self):
        """
        Creates locale
        """
        locales = self.get_locales(only_active=True)
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
        except:
            # log event, passing for now
            pass
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
        except:
            # log event, passing for now
            pass
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

    def get_sync_stats(self, pkgs=None):
        """
        fetch sync translation stats from db
        :return: resultset
        """
        sync_stats = None
        required_params = ('package_name', 'project_version', 'stats_raw_json')
        try:
            sync_stats = SyncStats.objects.only(*required_params) \
                .filter(package_name__in=pkgs, sync_visibility=True).all() \
                if pkgs else SyncStats.objects.only(*required_params).all()
        except:
            # log event, passing for now
            pass
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

    def get_packages(self, pkgs=None):
        """
        fetch packages from db
        """
        packages = None
        try:
            packages = Packages.objects.filter(package_name__in=pkgs) \
                .order_by('-transtats_lastupdated') if pkgs else \
                Packages.objects.all().order_by('-transtats_lastupdated')
        except:
            # log event, passing for now
            pass
        return packages

    def count_packages(self):
        """
        packages count
        """
        packages = self.get_packages()
        return packages.count() if packages else 0

    def get_package_name_tuple(self):
        """
        returns (package_name, upstream_name) tuple (only sync'd ones)
        """
        packages = self.get_packages()
        return tuple([(package.package_name, package.upstream_name)
                      for package in packages if package.transtats_lastupdated])

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
                    sync_uuid = uuid4()
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
                            params = {}
                            params.update(dict(package_name=project))
                            params.update(dict(job_uuid=sync_uuid))
                            params.update(dict(project_version=version))
                            params.update(dict(stats_raw_json=response_dict['json_content']))
                            params.update(dict(sync_iter_count=1))
                            params.update(dict(sync_visibility=True))
                            sync_stats_obj, created = SyncStats.objects.update_or_create(**params)
                            if created:
                                kwargs['transtats_lastupdated'] = timezone.now()

            if 'update_stats' in kwargs:
                del kwargs['update_stats']

            kwargs['lang_set'] = 'default'
            kwargs['transplatform_slug'] = platform
            kwargs['transplatform_name'] = kwargs['package_name']
            kwargs['upstream_name'] = kwargs['upstream_url'].split('/')[-1]
            # save in db
            new_package = Packages(**kwargs)
            new_package.save()
        except:
            # log event, pass for now
            # todo implement error msg handling
            return False
        else:
            return True

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
                response_dict = rest_handle.process_request('project_details',
                                                            package_name.lower())
            if platform.engine_name == TRANSPLATFORM_ENGINES[1]:
                response_dict = rest_handle.process_request('list_projects')
            if response_dict and response_dict.get('json_content'):
                projects_json = response_dict['json_content']

        ids, names = self._get_project_ids_names(platform.engine_name, projects_json)
        if package_name in ids:
            return package_name
        elif package_name in names:
            return ids[names.index(package_name)]
        else:
            return False

    def get_trans_stats(self, package_name):
        """
        fetch stats of a package for all enabled languages
        :param package_name: str
        :return: dict {project_version: stats_dict}
        """
        trans_stats_dict = OrderedDict()
        package_desc = ''
        # 1st, get active locales for which stats are to be shown
        active_locales = self.get_locales_set()[0]
        lang_id_name = {(lang.locale_id, lang.locale_alias): lang.lang_name
                        for lang in active_locales}
        lang_id_name = OrderedDict(sorted(lang_id_name.items(), key=operator.itemgetter(1)))
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
            trans_stats_dict[pkg_stats_version.project_version] = \
                self.syncstats_manager.extract_locale_translated(package_details.transplatform_slug_id,
                                                                 trans_stats_list)

        return lang_id_name, trans_stats_dict, package_desc


class ReleaseBranchManager(InventoryManager):
    """
    Release Stream Branch Manager
    """

    def get_release_branches(self, relstream=None):
        """
        Get release stream branches from db
        :param relstream: release stream slug
        :return:
        """
        filter_kwargs = {}
        if relstream:
            filter_kwargs.update(dict(relstream_slug=relstream))

        relbranches = None
        try:
            relbranches = StreamBranches.objects.filter(**filter_kwargs)
        except:
            # log event, passing for now
            pass
        return relbranches

    def get_calender_events_dict(self, ical_url, relstream_slug):
        """
        Fetches iCal contents over http and converts into dict
        :param ical_url: caldendar url
        :return: events dict_list
        """
        try:
            rest_response = requests.get(ical_url, verify=False)
        except:
            # log event
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

            except:
                # log event, pass for now
                return False
        elif relstream_slug == RELSTREAM_SLUGS[1]:
            try:
                for event in required_events:
                    for event_dict in ical_events:
                        if event.lower() in event_dict.get('SUMMARY').lower():
                            branch_schedule_dict[event_dict.get('SUMMARY')] = \
                                (event_dict.get('DUE', '') or event_dict.get('DTSTART', ''))[:8]
            except:
                # log event, pass for now
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
        required_params = ('relbranch_name', 'current_phase', 'calendar_url',
                           'schedule_json', 'relbranch_slug')
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
        except:
            # log event, pass for now
            return False
        else:
            return True
