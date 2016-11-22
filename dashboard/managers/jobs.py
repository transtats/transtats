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

# Jobs: Repositories Sync, Stats Validation

# python
from datetime import datetime
from uuid import uuid4

# django
from django.utils import timezone

# dashboard
from .base import BaseManager
from ..models import (
    TransPlatform, Packages, Jobs, SyncStats
)
from ..services.constants import (
    TRANSPLATFORM_ENGINES, ZANATA_SLUGS, TRANSIFEX_SLUGS
)
from .utilities import parse_project_details_json


class JobManager(BaseManager):
    """
    Base Manager for Jobs
    """
    job_type = None
    uuid = None
    start_time = None
    log_json = {}
    job_result = False
    job_remarks = None

    def _new_job_id(self):
        """
        a UUID based on the host ID and current time
        """
        return uuid4()

    def __init__(self, job_type):
        """
        Entry point for initiating new job
        :param http_request: object
        :param job_type: string
        """
        super(JobManager, self).__init__()
        self.job_type = job_type
        self.uuid = self._new_job_id()
        self.start_time = timezone.now()

    def create_job(self):
        kwargs = {}
        kwargs.update(dict(job_uuid=self.uuid))
        kwargs.update(dict(job_type=self.job_type))
        kwargs.update(dict(job_start_time=self.start_time))
        try:
            new_job = Jobs(**kwargs)
            new_job.save()
        except:
            # log event, pass for now
            return False
        else:
            return True


class JobsLogManager(BaseManager):
    """
    Maintains Job Logs
    """

    def get_job_logs(self):
        """
        Fetch all job logs from the db
        """
        job_logs = None
        try:
            job_logs = Jobs.objects.all().order_by('-job_start_time')
        except:
            # log event, passing for now
            pass
        return job_logs

    def get_joblog_stats(self):
        """
        Stats about jobs log
        """
        last_ran_on = None
        last_ran_type = None
        jobs_logs = self.get_job_logs()
        jobs_count = jobs_logs.count()
        if jobs_count > 0:
            last_ran_on = jobs_logs[0].job_end_time
            last_ran_type = jobs_logs[0].job_type
        return jobs_count, last_ran_on, last_ran_type


class TransplatformSyncManager(JobManager):
    """
    Translation Platform Sync Manager
    """

    def syncstats_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.create_job():
            return self.uuid
        return None

    def sync_trans_stats(self):
        """
        Run Sync process in sequential steps
        """
        stages = (
            self.update_trans_projects,
            self.update_project_details,
            self.update_trans_stats,
            self.mark_job_finish,
        )

        [method() for method in stages]

    def update_trans_projects(self):
        """
        Update projects json for transplatform in db
        """
        self.log_json['Projects'] = {}
        try:
            transplatforms = TransPlatform.objects.only('engine_name', 'api_url') \
                .filter(server_status=True).all()
        except Exception as e:
            self.log_json['Projects'].update(
                {str(datetime.now()): 'Fetch transplatform from db failed. Details: ' + str(e)}
            )
            self.job_result = False
        else:
            self.log_json['Projects'].update(
                {str(datetime.now()): str(len(transplatforms)) + ' translation platforms fetched from db.'}
            )
            for platform in transplatforms:
                rest_handle = self.rest_client(platform.engine_name, platform.api_url)
                response_dict = rest_handle.process_request('list_projects')
                if response_dict and response_dict.get('json_content'):
                    # save projects json in db
                    try:
                        TransPlatform.objects.filter(api_url=platform.api_url).update(
                            projects_json=response_dict['json_content'], projects_lastupdated=timezone.now()
                        )
                    except Exception as e:
                        self.log_json['Projects'].update(
                            {str(datetime.now()): 'Projects JSON for ' + platform.api_url +
                                                  ' failed to get saved in db. Details: ' + str(e)}
                        )
                        self.job_result = False
                    else:
                        self.log_json['Projects'].update(
                            {str(datetime.now()): 'Projects JSON for ' + platform.api_url + ' saved in db.'}
                        )
                        self.job_result = True
                else:
                    self.log_json['Projects'].update(
                        {str(datetime.now()): 'Projects JSON for ' + platform.api_url + ' could not be fetched.'}
                    )
        return self.job_result

    def update_project_details(self):
        """
        Update project details json in db
        """
        self.log_json['Project-Details'] = {}
        try:
            project_urls = Packages.objects.select_related()
        except Exception as e:
            self.log_json['Project-Details'].update(
                {str(datetime.now()): 'Fetch Project URLs from db failed. Details: ' + str(e)}
            )
            self.job_result = False
        else:
            self.log_json['Project-Details'].update(
                {str(datetime.now()): str(len(project_urls)) + ' Project URLs fetched from db.'}
            )
            if project_urls and len(project_urls) > 0:
                for url in project_urls:
                    # Package name can be diff from its id/slug, hence extracting from url
                    transplatform_project_name = url.transplatform_url.split('/')[-1]
                    rest_handle = self.rest_client(url.transplatform_slug.engine_name,
                                                   url.transplatform_slug.api_url)
                    # extension for Transifex should be true, otherwise false
                    ext = True if url.transplatform_slug.engine_name == TRANSPLATFORM_ENGINES[0] else False
                    response_dict = rest_handle.process_request(
                        'project_details', transplatform_project_name, ext=ext
                    )
                    if response_dict and response_dict.get('json_content'):
                        try:
                            Packages.objects.filter(transplatform_url=url.transplatform_url).update(
                                package_details_json=response_dict['json_content'],
                                details_json_lastupdated=timezone.now()
                            )
                        except Exception as e:
                            self.log_json['Project-Details'].update(
                                {str(datetime.now()): 'Project Details JSON for ' + transplatform_project_name +
                                                      ' failed to get saved in db. Details: ' + str(e)}
                            )
                            self.job_result = False
                        else:
                            self.log_json['Project-Details'].update(
                                {str(datetime.now()): 'Project Details JSON for ' +
                                                      transplatform_project_name + ' saved in db.'}
                            )
                            self.job_result = True
        return self.job_result

    def update_trans_stats(self):
        """
        Update translation stats for each project-version in db
        """
        self.log_json['Translation-Stats'] = {}
        try:
            packages = Packages.objects.select_related()
        except Exception as e:
            self.log_json['Translation-Stats'].update(
                {str(datetime.now()): 'Fetch Project Details from db failed. Details: ' + str(e)}
            )
            self.job_result = False
        else:
            self.log_json['Translation-Stats'].update(
                {str(datetime.now()): str(len(packages)) + ' packages fetched from db.'}
            )
            for package in packages:
                transplatform_engine = package.transplatform_slug.engine_name
                rest_handle = self.rest_client(transplatform_engine, package.transplatform_slug.api_url)
                project, versions = parse_project_details_json(
                    transplatform_engine, package.package_details_json
                )
                for version in versions:
                    # extension for Zanata should be true, otherwise false
                    extension = True if transplatform_engine == TRANSPLATFORM_ENGINES[1] else False
                    response_dict = rest_handle.process_request(
                        'proj_trans_stats', project, version, extension
                    )
                    if response_dict and response_dict.get('json_content'):
                        try:
                            existing_sync_stat = SyncStats.objects.filter(package_name=project,
                                                                          project_version=version).first()
                            if not existing_sync_stat:
                                params = {}
                                params.update(dict(package_name=project))
                                params.update(dict(job_uuid=self.uuid))
                                params.update(dict(project_version=version))
                                params.update(dict(stats_raw_json=response_dict['json_content']))
                                params.update(dict(sync_iter_count=1))
                                params.update(dict(sync_visibility=True))
                                new_sync_stats = SyncStats(**params)
                                new_sync_stats.save()
                            else:
                                SyncStats.objects.filter(package_name=project, project_version=version).update(
                                    job_uuid=self.uuid, stats_raw_json=response_dict['json_content'],
                                    sync_iter_count=existing_sync_stat.sync_iter_count + 1
                                )
                            Packages.objects.filter(transplatform_url=package.transplatform_url).update(
                                transtats_lastupdated=timezone.now())
                        except Exception as e:
                            self.log_json['Translation-Stats'].update(
                                {str(datetime.now()): 'Transtats JSON for project: ' + project + ' of version: ' +
                                                      version + ' failed to get saved in db. Details: ' + str(e)}
                            )
                            self.job_result = False
                        else:
                            self.log_json['Translation-Stats'].update(
                                {str(datetime.now()): 'Transtats JSON for project: ' + project + ' of version: ' +
                                                      version + ' saved in db.'}
                            )
                            self.job_result = True
        return self.job_result

    def mark_job_finish(self):
        """
        Update job with finish details
        """
        try:
            Jobs.objects.filter(job_uuid=self.uuid).update(
                job_end_time=timezone.now(),
                job_log_json=self.log_json,
                job_result=self.job_result
            )
        except:
            return False
        else:
            return True


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
