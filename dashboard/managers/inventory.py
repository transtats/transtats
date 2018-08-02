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
#       Release Streams are Products,
#       Release Branches are Releases

# python
import io
from uuid import uuid4
from collections import OrderedDict

# third party
import requests
from slugify import slugify

# django
from django.utils import timezone

# dashboard
from dashboard.managers import BaseManager
from dashboard.models import (
    TransPlatform, Languages, LanguageSet,
    ReleaseStream, StreamBranches, SyncStats
)
from dashboard.constants import (
    ZANATA_SLUGS, DAMNEDLIES_SLUGS, TRANSIFEX_SLUGS, RELSTREAM_SLUGS
)
from dashboard.managers.utilities import parse_ical_file


__all__ = ['InventoryManager', 'SyncStatsManager', 'ReleaseBranchManager']


class InventoryManager(BaseManager):
    """
    Manage application inventories
    """

    def get_locales(self, only_active=None, pick_locales=None, pick_alias=None):
        """
        fetch all languages from db
        """
        filter_kwargs = {}
        if only_active:
            filter_kwargs.update(dict(lang_status=True))
        if pick_locales:
            filter_kwargs.update(dict(locale_id__in=pick_locales))
        if pick_alias:
            filter_kwargs.update(dict(locale_alias__in=pick_alias))

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

    def get_active_locales_count(self):
        """
        Return count of active locales
        """
        try:
            return Languages.objects.filter(lang_status=True).count()
        except Exception as e:
            self.app_logger(
                'ERROR', "locales count could not be fetched, details: " + str(e)
            )
            return 0

    def get_locale_alias(self, locale):
        """
        Fetch alias of a locale
        :param locale: str
        :return: alias: str
        """
        locale_qset = self.get_locales(pick_locales=[locale])
        return locale_qset.get().locale_alias if locale_qset else locale

    def get_alias_locale(self, alias):
        """
        Fetch locale of a alias
        :param alias: str
        :return: locale: str
        """
        locale_qset = self.get_locales(pick_alias=[alias])
        return locale_qset.get().locale_id if locale_qset else alias

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
            return ()
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

    def get_release_streams(self, stream_slug=None, only_active=None,
                            built=None, fields=None):
        """
        Fetch all release streams from the db
        """
        filter_kwargs = {}
        if only_active:
            filter_kwargs.update(dict(relstream_status=True))
        if stream_slug:
            filter_kwargs.update(dict(relstream_slug=stream_slug))
        if built:
            filter_kwargs.update(dict(relstream_built=built))
        filter_fields = fields if isinstance(fields, (tuple, list)) else ()
        relstreams = None
        try:
            relstreams = ReleaseStream.objects.only(*filter_fields).filter(**filter_kwargs) \
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

    def get_relstream_build_tags(self, stream_slug=None):
        build_tags = {}
        release_streams = self.get_release_streams(stream_slug=stream_slug) \
            if stream_slug else self.get_release_streams(only_active=True)
        for release_stream in release_streams:
            build_tags[release_stream.relstream_slug] = \
                release_stream.relstream_built_tags or []
        return build_tags

    def get_build_tags(self, buildsys):
        release_stream = self.get_release_streams(built=buildsys)
        if release_stream:
            return release_stream.first().relstream_built_tags or [' ']
        return []

    def get_relstream_buildsys(self, relstream):
        release_stream = self.get_release_streams(stream_slug=relstream)
        if release_stream:
            return release_stream.first().relstream_built
        return ''


class SyncStatsManager(BaseManager):
    """
    Sync Translation Stats Manager
    """

    def get_sync_stats(self, pkgs=None, fields=None, versions=None, sources=None):
        """
        fetch sync translation stats from db
        :return: resultset
        """
        sync_stats = None
        required_params = fields if fields and isinstance(fields, (list, tuple)) \
            else ('package_name', 'project_version', 'source', 'stats_raw_json')
        kwargs = {}
        kwargs.update(dict(sync_visibility=True))
        if pkgs:
            kwargs.update(dict(package_name__in=pkgs))
        if versions:
            kwargs.update(dict(project_version__in=versions))
        if sources:
            kwargs.update(dict(source__in=sources))

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
        missing_locales = []

        if transplatform_slug in ZANATA_SLUGS or transplatform_slug in DAMNEDLIES_SLUGS:
            if not stats_json.get('stats'):
                return trans_stats, ()
            for stats_param in stats_json['stats']:
                stats_param_locale = stats_param.get('locale', '')
                for locale_tuple in locales:
                    if (stats_param_locale in locale_tuple) or \
                            (stats_param_locale.replace('-', '_') in locale_tuple):
                        trans_stats.append(stats_param)
                    else:
                        missing_locales.append(locale_tuple)

        elif transplatform_slug in TRANSIFEX_SLUGS:
            for locale_tuple in locales:
                if stats_json.get(locale_tuple[0]):
                    trans_stats.append({locale_tuple[0]: stats_json[locale_tuple[0]]})
                    missing_locales.append(locale_tuple)
                elif stats_json.get(locale_tuple[1]):
                    trans_stats.append({locale_tuple[1]: stats_json[locale_tuple[1]]})
                    missing_locales.append(locale_tuple)

        return trans_stats, tuple(set(locales) - set(missing_locales))

    def extract_locale_translated(self, transplatform_slug, stats_dict_list):
        """
        Compute %age of translation for each locale
        :param transplatform_slug:str
        :param stats_dict_list:list
        :return:locale translated list
        """
        locale_translated = []

        if transplatform_slug in TRANSIFEX_SLUGS:
            for stats_dict in stats_dict_list:
                for locale, stat_params in stats_dict.items():
                    locale_translated.append([locale, int(stat_params.get('completed')[:-1])])
        else:
            for stats_dict in stats_dict_list:
                translation_percent = \
                    round((stats_dict.get('translated', 0) * 100) / stats_dict.get('total', 0), 2) \
                    if stats_dict.get('total', 0) > 0 else 0
                locale_translated.append([stats_dict.get('locale', ''), translation_percent])
        return locale_translated

    def save_version_stats(self, project, version, stats_json, stats_source, p_stats=None):
        """
        Save version's translation stats in db
        :param project: transplatform project
        :param version: transplatform project's version
        :param stats_json: translation stats dict
        :param stats_source: platform engine or build system
        :param p_stats: processed stats dict
        :return: boolean
        """

        filter_kwargs = dict(package_name=project,
                             project_version=version,
                             source=stats_source)
        try:
            existing_sync_stat = SyncStats.objects.filter(**filter_kwargs).first()
            sync_uuid = uuid4()
            if not existing_sync_stat:
                params = {}
                params.update(dict(package_name=project))
                params.update(dict(job_uuid=sync_uuid))
                params.update(dict(project_version=version))
                params.update(dict(source=stats_source))
                params.update(dict(stats_raw_json=stats_json))
                if isinstance(p_stats, dict):
                    params.update(dict(stats_processed_json=p_stats))
                params.update(dict(sync_iter_count=1))
                params.update(dict(sync_visibility=True))
                new_sync_stats = SyncStats(**params)
                new_sync_stats.save()
            else:
                SyncStats.objects.filter(**filter_kwargs).update(
                    job_uuid=sync_uuid, stats_raw_json=stats_json,
                    stats_processed_json=p_stats if isinstance(p_stats, dict) else {},
                    sync_iter_count=existing_sync_stat.sync_iter_count + 1
                )
        except Exception as e:
            self.app_logger(
                'ERROR', "version stats could not be saved, details: " + str(e))
        else:
            return True
        return False


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

    def is_relbranch_exist(self, release_branch):
        """
        Checks release branch existence
        """
        if self.get_release_branches(relbranch=release_branch):
            return True
        return False

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

    def get_calendar_events_dict(self, ical_url, relstream_slug):
        """
        Fetches iCal contents over http and converts into dict
        :param ical_url: calendar url
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
        ical_events = self.get_calendar_events_dict(ical_url, release_stream.relstream_slug)
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
