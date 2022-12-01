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
import json
from uuid import uuid4
from collections import OrderedDict

# third party
import requests
from slugify import slugify
from natsort import natsorted

# django
from django.conf import settings
from django.db.models import Case, Value, When
from django.utils import timezone

# dashboard
from dashboard.managers import BaseManager
from dashboard.models import (
    Platform, Language, LanguageSet, Product, Release,
    SyncStats, PlatformProjectTemplates
)
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, ZANATA_SLUGS, DAMNEDLIES_SLUGS,
    TRANSIFEX_SLUGS, RELSTREAM_SLUGS, WEBLATE_SLUGS,
    BUILD_SYSTEMS, MEMSOURCE_SLUGS
)
from dashboard.managers.utilities import parse_ical_file


__all__ = ['InventoryManager', 'SyncStatsManager', 'ReleaseBranchManager']


class InventoryManager(BaseManager):
    """Manage application inventories"""

    def get_locales(self, only_active=None, pick_locales=None, pick_alias=None):
        """fetch all languages from db"""
        filter_kwargs = {}
        if only_active:
            filter_kwargs.update(dict(lang_status=True))
        if pick_locales:
            filter_kwargs.update(dict(locale_id__in=pick_locales))
        if pick_alias:
            filter_kwargs.update(dict(locale_alias__in=pick_alias))

        locales = []
        try:
            locales = Language.objects.filter(**filter_kwargs) \
                .order_by('lang_name').order_by('-lang_status')
        except Exception as e:
            self.app_logger(
                'ERROR', "locales could not be fetched for " +
                         str(filter_kwargs) + " kwargs, details: " + str(e)
            )
        return locales

    def get_active_locales_count(self):
        """Return count of active locales"""
        try:
            return Language.objects.filter(lang_status=True).count()
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
        """Creates locale"""
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
        """fetch desired language set from db"""
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
        return langset

    def get_langsets(self, fields=None):
        """fetch all language sets from db"""
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
        """fetch list of langlist, a locale belongs to"""
        groups_locale_belongs_to = []
        lang_sets = self.get_langsets()
        for langset in lang_sets:
            if locale in langset.locale_ids:
                groups_locale_belongs_to.append(langset.lang_set_slug)
        return {locale: groups_locale_belongs_to}

    def get_all_locales_groups(self):
        """get_locale_groups for all available locales"""
        all_locales_groups = {}
        for locale in self.get_locales():
            all_locales_groups.update(self.get_locale_groups(locale.locale_id))
        return all_locales_groups

    def get_relbranch_locales(self, release_branch):
        """Fetch locales specific to release branch"""
        required_locales = []
        try:
            release_branch_specific_lang_set = \
                Release.objects.filter(release_slug=release_branch).first()
            required_lang_set = release_branch_specific_lang_set.language_set_slug
            required_locales = required_lang_set.locale_ids if required_lang_set else []
        except Exception as e:
            self.app_logger(
                'ERROR', ("locales could not be fetched for " +
                          release_branch + " release, details: " + str(e))
            )
        return required_locales

    def get_translation_platforms(self, engine=None, only_active=None, ci=None, slug=None):
        """fetch all translation platforms from db"""
        filter_kwargs = {}
        if engine:
            filter_kwargs.update(dict(engine_name=engine))
        if only_active:
            filter_kwargs.update(dict(server_status=True))
        if ci:
            filter_kwargs.update(dict(ci_status=True))
        if ci is False:
            filter_kwargs.update(dict(ci_status=False))
        if slug:
            filter_kwargs.update(dict(platform_slug=slug))

        platforms = None
        try:
            platforms = Platform.objects.filter(**filter_kwargs) \
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

    def get_engine_from_slug(self, platform_slug):
        """
        return platform's engine related to provided slug
        :param platform_slug: str
        :return: str
        """
        count = 0
        platform_relation = {}
        platform_slugs = [DAMNEDLIES_SLUGS, TRANSIFEX_SLUGS,
                          ZANATA_SLUGS, WEBLATE_SLUGS, MEMSOURCE_SLUGS]

        for engine in TRANSPLATFORM_ENGINES:
            platform_relation.update({engine: platform_slugs[count]})
            count += 1

        engine = [i for i, j in platform_relation.items() if platform_slug in j]
        return engine[0] if isinstance(engine, list) and len(engine) > 0 else ''

    def get_transplatform_slug_url(self, ci=None):
        """
        Get slug and api_url for active transplatform
        :return: tuple
        """
        active_platforms = self.get_translation_platforms(only_active=True, ci=ci)
        return tuple([(platform.platform_slug, platform.api_url)
                      for platform in active_platforms]) or ()

    def _get_lang_contact(self, platform, language):
        """
        Get language team contact information
        :param platform: translation platform query object
        :param language: language query object
        :return: contact url: str
        """
        contact_url = platform.api_url
        niddle = language.locale_alias \
            if language.locale_alias else language.locale_id

        if platform.engine_name in (TRANSPLATFORM_ENGINES[1],
                                    TRANSPLATFORM_ENGINES[2]):
            niddle = niddle.replace('_', '-')

        if platform.engine_name == TRANSPLATFORM_ENGINES[0]:
            contact_url += '/teams/{0}'.format(niddle)
        elif platform.engine_name == TRANSPLATFORM_ENGINES[1]:
            contact_url += '/explore/people/?lang={0}'.format(niddle)
        elif platform.engine_name == TRANSPLATFORM_ENGINES[2]:
            contact_url += '/language/view/{0}'.format(niddle)
        elif platform.engine_name == TRANSPLATFORM_ENGINES[3]:
            contact_url += '/languages/{0}/'.format(niddle)
        return contact_url

    def get_platform_language_team_contact(self, locale):
        """
        Get language team contact information
        :param locale: str
        :return: dict
        """
        language_team_contact = {}
        if not locale:
            return language_team_contact
        language_query = self.get_locales(pick_locales=[locale])
        if language_query:
            language = language_query.get()
            platforms = self.get_translation_platforms(only_active=True)

            for platform in platforms:
                language_team_contact[platform.api_url] = \
                    self._get_lang_contact(platform, language)
        return language_team_contact

    def create_platform_project(self, project_slug, repo_url, platform_slug):
        """
        Create a Project at Translation Platform
        :param project_slug: str
        :param repo_url: str
        :param platform_slug: str
        :return: dict
        """
        request_kwargs = {}
        platform = Platform.objects.filter(platform_slug=platform_slug).get()
        if platform.engine_name == TRANSPLATFORM_ENGINES[1]:
            # Transifex payload for new project
            request_kwargs['data'] = '{"slug":"%s","name":"%s","source_language_code":"en",' \
                                     '"description":"%s", "repository_url": "%s"}' % \
                                     (project_slug, project_slug, project_slug, repo_url)
        request_kwargs.update(dict(
            auth_user=platform.auth_login_id, auth_token=platform.auth_token_key
        ))

        api_response = None
        try:
            api_response = self.api_resources.create_project(
                translation_platform=platform.engine_name,
                instance_url=platform.api_url, **request_kwargs
            )
        except Exception as e:
            self.logger("Something unexpected happened while creating a project "
                        "at platform, details: " + str(e))

        return api_response

    def get_release_streams(self, stream_slug=None, only_active=None,
                            built=None, fields=None):
        """Fetch all products from the db"""
        filter_kwargs = {}
        if only_active:
            filter_kwargs.update(dict(product_status=True))
        if stream_slug:
            filter_kwargs.update(dict(product_slug=stream_slug))
        if built:
            filter_kwargs.update(dict(product_build_system=built))
        filter_fields = fields if isinstance(fields, (tuple, list)) else ()
        relstreams = None
        try:
            relstreams = Product.objects.only(*filter_fields).filter(**filter_kwargs) \
                .order_by('product_id')
        except Exception as e:
            self.app_logger(
                'ERROR', "products could not be fetched, details: " + str(e)
            )
        return relstreams

    def get_relstream_slug_name(self):
        """
        Get slug and name for active product
        :return: tuple
        """
        active_streams = self.get_release_streams(only_active=True)
        return tuple([(stream.product_slug, stream.product_name)
                      for stream in active_streams]) or ()

    def get_relstream_build_tags(self, stream_slug=None):
        build_tags = {}
        products = self.get_release_streams(stream_slug=stream_slug) \
            if stream_slug else self.get_release_streams(only_active=True)
        for product in products:
            build_tags[product.product_slug] = \
                product.product_build_tags or []
        return build_tags

    def get_build_tags(self, buildsys, product_slug):
        release_stream = self.get_release_streams(
            stream_slug=product_slug, built=buildsys
        )
        if release_stream:
            return release_stream.first().product_build_tags or [' ']
        return []

    def get_relstream_buildsys(self, relstream):
        release_stream = self.get_release_streams(stream_slug=relstream)
        if release_stream:
            return release_stream.first().product_build_system
        return ''

    def get_project_templates(self, platform=None):
        """Get Platform Project Templates from db"""
        filter_kwargs = {}
        if platform:
            filter_kwargs.update(dict(platform=platform))

        try:
            pp_templates = PlatformProjectTemplates.objects.filter(**filter_kwargs)
        except Exception as e:
            self.app_logger(
                'ERROR', "Platform project templates could not be fetched, details: " + str(e)
            )
        else:
            return pp_templates

    def create_or_update_project_template(self, platform: Platform,
                                          default_template_uid: str,
                                          project_templates_dict: dict = None) -> bool:
        """
        Save Platform Project Templates to db
        :param platform: platform db model
        :param default_template_uid: str
        :param project_templates_dict: project_templates dict
        :return: boolean
        """
        if not platform and not default_template_uid:
            raise TypeError()
        default_params = {}
        match_params = {
            'platform': platform
        }
        default_params.update(match_params)
        default_params['default_project_template'] = default_template_uid
        if project_templates_dict and not isinstance(project_templates_dict, dict):
            raise TypeError()
        if project_templates_dict:
            default_params['project_template_json_str'] = json.dumps(project_templates_dict)
        try:
            PlatformProjectTemplates.objects.update_or_create(
                **match_params, defaults=default_params
            )
        except Exception as e:
            self.app_logger(
                'ERROR', "Platform project templates could not be saved or updated, details: " + str(e)
            )
            return False
        else:
            return True

    def fetch_latest_platform_project_templates(self, platform_slug: str) -> list:
        """Fetch project templates from CI platforms by calling API"""
        if not platform_slug:
            raise TypeError()
        latest_project_templates = []
        ci_platforms = self.get_translation_platforms(ci=True)
        ci_platform_qs = ci_platforms.filter(platform_slug=platform_slug)
        if not ci_platform_qs:
            return latest_project_templates
        ci_platform = ci_platform_qs.get()
        latest_project_templates = self.api_resources.fetch_project_templates(
            ci_platform.engine_name, ci_platform.api_url
        )
        return latest_project_templates

    @staticmethod
    def filter_uid_name_from_project_templates(project_templates: list) -> dict:
        """
        Filter UID and Name from Platform Project Templates
        :param project_templates: dict
        : returns: dict
        """
        if not isinstance(project_templates, list):
            raise ValueError()
        filtered_uid_name = {}
        for template in project_templates:
            try:
                filtered_uid_name[template['uid']] = template['templateName']
            except KeyError:
                continue
        return filtered_uid_name


class SyncStatsManager(BaseManager):
    """Sync Translation Stats Manager"""

    def get_sync_stats(self, pkgs=None, fields=None, versions=None, sources=None):
        """
        fetch sync translation stats from db
        :return: queryset
        """
        sync_stats = None
        required_params = fields if fields and isinstance(fields, (list, tuple)) \
            else ('package_name', 'project_version', 'source', 'stats_raw_json_str')
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

    def filter_stats_for_required_locales(self, transplatform_slug, stats_json, locales, source):
        """
        Filter stats json for required locales
        :param transplatform_slug: str
        :param stats_json: dict
        :param locales: list
        :param source: stats source
        :return: stats list, missing locales tuple
        """
        trans_stats = []
        missing_locales = []

        locale_key = 'locale'
        if source == TRANSPLATFORM_ENGINES[3]:
            locale_key = 'code'

        t_platform_group = []
        t_platform_group.extend(ZANATA_SLUGS)
        t_platform_group.extend(DAMNEDLIES_SLUGS)
        t_platform_group.extend(WEBLATE_SLUGS)

        if transplatform_slug in t_platform_group:
            if not stats_json.get('stats'):
                return trans_stats, ()
            for stats_param in stats_json['stats']:
                stats_param_locale = stats_param.get(locale_key, '')
                for locale_tuple in locales:
                    if stats_param_locale and (
                            (stats_param_locale in locale_tuple) or
                            (stats_param_locale.replace('-', '_') in locale_tuple) or
                            (stats_param_locale.replace('_', '-') in locale_tuple)
                    ):
                        stats_param['source'] = source
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
                elif stats_json.get('stats'):
                    for stats_param in stats_json['stats']:
                        stats_param_locale = stats_param.get(locale_key, '')
                        for locale_tuple_1 in locales:
                            if (stats_param_locale in locale_tuple_1) or \
                                    (stats_param_locale.replace('-', '_') in locale_tuple_1):
                                stats_param['source'] = source
                                trans_stats.append(stats_param)
                            else:
                                missing_locales.append(locale_tuple_1)

        return trans_stats, tuple(set(locales) - set(missing_locales))

    def extract_locale_translated(self, transplatform_slug, stats_dict_list, source):
        """
        Compute %age of translation for each locale
        :param transplatform_slug:str
        :param stats_dict_list:list
        :return:locale translated list
        """
        locale_translated = []

        locale_key = 'locale'
        if source == TRANSPLATFORM_ENGINES[3]:
            locale_key = 'code'

        if transplatform_slug in TRANSIFEX_SLUGS:
            for stats_dict in stats_dict_list:
                if 'translated' in stats_dict and 'total' in stats_dict:
                    translation_percent = \
                        round((stats_dict.get('translated', 0) * 100) / stats_dict.get('total', 0), 2) \
                        if stats_dict.get('total', 0) > 0 else 0
                    locale_translated.append([stats_dict.get(locale_key, ''), translation_percent])
                for locale, stat_params in stats_dict.items():
                    if isinstance(stat_params, dict):
                        locale_translated.append([locale, int(stat_params.get('completed')[:-1])])
        else:
            for stats_dict in stats_dict_list:
                translation_percent = \
                    round((stats_dict.get('translated', 0) * 100) / stats_dict.get('total', 0), 2) \
                    if stats_dict.get('total', 0) > 0 else 0
                locale_translated.append([stats_dict.get(locale_key, ''), translation_percent])
        locale_translated.append(['source', source])
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
                params.update(dict(stats_raw_json_str=json.dumps(stats_json)))
                if isinstance(p_stats, dict):
                    params.update(dict(stats_processed_json_str=json.dumps(p_stats)))
                params.update(dict(sync_iter_count=1))
                params.update(dict(sync_visibility=True))
                new_sync_stats = SyncStats(**params)
                new_sync_stats.save()
            else:
                SyncStats.objects.filter(**filter_kwargs).update(
                    job_uuid=sync_uuid, stats_raw_json_str=json.dumps(stats_json),
                    stats_processed_json_str=json.dumps(p_stats) if isinstance(p_stats, dict) else {},
                    sync_iter_count=existing_sync_stat.sync_iter_count + 1
                )
        except Exception as e:
            self.app_logger(
                'ERROR', "version stats could not be saved, details: " + str(e))
        else:
            return True
        return False

    def toggle_visibility(self, package=None, stats_source=None, project_version=None):
        """
        Toggle visibility of statistics to false or true
        :param package: Package Name: str
        :param stats_source: str
        :param project_version: str
        :return: boolean
        """
        filter_kwargs = {}
        if package:
            filter_kwargs.update(dict(package_name=package))
        if stats_source:
            filter_kwargs.update(dict(source=stats_source))
        if project_version:
            filter_kwargs.update(dict(project_version=project_version))
        try:
            SyncStats.objects.filter(**filter_kwargs).update(
                sync_visibility=Case(
                    When(sync_visibility=True, then=Value(False)),
                    When(sync_visibility=False, then=Value(True)),
                    default=Value(True)
                )
            )
        except Exception as e:
            self.app_logger(
                'ERROR', "version stats could not be saved, details: " + str(e))
        else:
            return True
        return False

    def get_build_system_stats(self):
        """
        The build system statistics
        :return: queryset
        """
        build_sys_stats = self.get_sync_stats(sources=BUILD_SYSTEMS)
        return build_sys_stats


class ReleaseBranchManager(InventoryManager):
    """Release Stream Branch Manager"""

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
            filter_kwargs.update(dict(product_slug=relstream))
        if relbranch:
            filter_kwargs.update(dict(release_slug=relbranch))

        relbranches = None
        try:
            relbranches = Release.objects.only(*required_fields).filter(**filter_kwargs).order_by('-release_slug')
        except Exception as e:
            self.app_logger(
                'ERROR', "Release branches could not be fetched, details: " + str(e))
        return relbranches

    def is_relbranch_exist(self, release_branch):
        """Checks release branch existence"""
        if self.get_release_branches(relbranch=release_branch):
            return True
        return False

    def get_product_by_release(self, release_slug):
        """
        Get Product by release
        :param release_slug: str
        :return: product query obj
        """
        if not release_slug:
            return
        release = self.get_release_branches(relbranch=release_slug)
        if release:
            product = release.get().product_slug
            return product
        return

    def get_relbranch_name_slug_tuple(self):
        """
        Get release branch slug and name tuple
        :return: (('main', 'main'), )
        """
        release_branches = self.get_release_branches(
            fields=('release_slug', 'release_name', 'track_trans_flag')
        )
        return tuple([(branch.release_slug, branch.release_name)
                      for branch in release_branches if branch.track_trans_flag])

    def get_branches_of_relstreams(self, release_streams, track_trans_flag=None):
        """
        Retrieve all branches of input release streams (products)
        :param release_streams: release stream slugs
        :return: dict
        """
        if not release_streams:
            return
        branches_of_relstreams = {}
        fields = ('product_slug', 'release_slug')
        filters = {}
        filters.update(dict(product_slug__in=release_streams))
        if track_trans_flag:
            filters.update(dict(track_trans_flag=True))
        try:
            relbranches = Release.objects.only(*fields).filter(**filters).all()
        except Exception as e:
            self.app_logger(
                'ERROR', "Releases of product could not be fetched, details: " + str(e))
        else:
            if relbranches:
                stream_branches = [{i.product_slug.product_slug: i.release_slug} for i in relbranches]
                for r_stream in release_streams:
                    if not isinstance(r_stream, str):
                        r_stream = r_stream.product_slug
                    branches_of_relstreams[r_stream] = []
                    for relbranch in stream_branches:
                        branches_of_relstreams[r_stream].extend(
                            [branch for stream, branch in relbranch.items() if stream == r_stream]
                        )
        return branches_of_relstreams

    def get_calendar_events_dict(self, ical_url, product_slug):
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
            return parse_ical_file(ical_contents_array, product_slug)

    def parse_events_for_required_milestones(self, product_slug, relbranch_slug,
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

        if product_slug in (RELSTREAM_SLUGS[0], RELSTREAM_SLUGS[2], RELSTREAM_SLUGS[3], RELSTREAM_SLUGS[4]):
            try:
                for event in required_events:
                    for event_dict in ical_events:
                        if (event.lower() in event_dict.get('SUMMARY').lower() and
                                relbranch_slug in event_dict.get('SUMMARY').lower().replace('_', '-')):
                            key = DELIMITER.join(event_dict.get('SUMMARY').split(DELIMITER)[1:])
                            branch_schedule_dict[key] = event_dict.get('DTEND', '')

            except Exception as e:
                self.app_logger(
                    'WARNING', "Parsing failed for " + product_slug + ", details: " + str(e))
                return False
        elif product_slug == RELSTREAM_SLUGS[1]:
            try:
                for event in required_events:
                    for event_dict in ical_events:
                        if event.lower() in event_dict.get('SUMMARY').lower():
                            branch_schedule_dict[event_dict.get('SUMMARY')] = \
                                (event_dict.get('DUE', '') or event_dict.get('DTSTART', ''))[:8]
            except Exception as e:
                self.app_logger(
                    'WARNING', "Parsing failed for " + product_slug + ", details: " + str(e))
                return False
        return branch_schedule_dict

    def validate_branch(self, product, **kwargs):
        """
        Validate iCal URL for a branch
        :return: boolean
        """
        if 'calendar_url' not in kwargs:
            return False
        ical_url = kwargs.get('calendar_url')
        relbranch_slug = slugify(kwargs.get('release_name', ''))
        release_stream = self.get_release_streams(stream_slug=product).get()
        ical_events = self.get_calendar_events_dict(ical_url, release_stream.product_slug)
        required_events = release_stream.major_milestones
        return relbranch_slug, \
            self.parse_events_for_required_milestones(
                release_stream.product_slug, relbranch_slug, ical_events, required_events)

    def add_relbranch(self, product_slug, **kwargs):
        """
        Save release branch in db
        :param product_slug: str
        :param post_params: dict
        :return: boolean
        """
        if not product_slug:
            return False
        required_params = ('release_name', 'lang_set', 'current_phase',
                           'calendar_url', 'schedule_json_str', 'release_slug')
        if not set(required_params) <= set(kwargs.keys()):
            return False
        if not (kwargs['release_name'] and kwargs['calendar_url']):
            return False
        flags = kwargs.pop('enable_flags') if 'enable_flags' in kwargs else []
        product = self.get_release_streams(stream_slug=product_slug).first()
        language_set = self.get_langset(langset_slug=kwargs.pop('lang_set'))
        try:
            kwargs['language_set_slug'] = language_set
            kwargs['product_slug'] = product
            kwargs['scm_branch'] = kwargs.get('scm_branch')
            kwargs['created_on'] = timezone.now()
            kwargs['sync_calendar'] = 'sync_calendar' in flags
            kwargs['notifications_flag'] = 'notifications_flag' in flags
            kwargs['track_trans_flag'] = 'track_trans_flag' in flags
            new_release_branch = Release(**kwargs)
            new_release_branch.save()
        except Exception as e:
            self.app_logger(
                'ERROR', "Release branch could not be added, details: " + str(e))
            return False
        else:
            return True

    def get_latest_release(self, tenant):
        """
        Returns latest release query object
            - releases for which translation tracking is ON
        :return: query obj
        """
        product_slug = RELSTREAM_SLUGS[1] if settings.FAS_AUTH else RELSTREAM_SLUGS[0] \
            if tenant == "default" else tenant

        releases = self.get_release_branches(relstream=product_slug)
        if releases and len(releases) > 0:
            latest_release_slug = natsorted(
                [r.release_slug for r in releases if r.track_trans_flag], reverse=True
            )[0]
            latest_release = self.get_release_branches(relbranch=latest_release_slug).get()
            return latest_release.release_slug, latest_release.release_name

    def get_relbranch_scm_branch(self, release_slug):
        """
        Returns SCM branch of a release
        :param release_slug: str
        :return: str or None
        """
        if not release_slug:
            return
        release = self.get_release_branches(relbranch=release_slug)
        if release:
            return release.get().scm_branch
        return
