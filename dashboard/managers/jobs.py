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
import io
import os
import json
import shutil
import time
from collections import OrderedDict
from datetime import datetime
from uuid import uuid4
from urllib.parse import urlparse
from yaml import load, FullLoader

# django
from django.conf import settings
from django.utils import timezone

# dashboard
from dashboard.constants import (
    TS_JOB_TYPES, JOB_EXEC_TYPES, GIT_REPO_TYPE, SYS_EMAIL_ADDR
)
from dashboard.jobs_framework.action_mapper import ActionMapper
from dashboard.jobs_framework.ds import TaskList
from dashboard.jobs_framework.parser import YMLPreProcessor, YMLJobParser
from dashboard.managers import BaseManager
from dashboard.managers.packages import PackagesManager
from dashboard.managers.inventory import ReleaseBranchManager
from dashboard.managers.pipelines import CIPipelineManager
from dashboard.models import (
    Platform, Package, Product, Release, JobTemplate, Job,
    CacheBuildDetails
)


__all__ = ['JobTemplateManager', 'JobManager', 'JobsLogManager',
           'TransplatformSyncManager', 'ReleaseScheduleSyncManager',
           'BuildTagsSyncManager', 'YMLBasedJobManager']


class JobTemplateManager(BaseManager):
    """Job Templates Manager"""
    def get_job_templates(self, *fields, **filters):
        """
        Get Job Templates from db
        :param fields: template fields to fetch
        :param filters: Any filters to apply
        :return: Query sets
        """
        job_templates = []
        try:
            job_templates = JobTemplate.objects.only(*fields).filter(**filters).order_by('job_template_id')
        except Exception as e:
            self.app_logger(
                'ERROR', "Job templates could not be fetched for " +
                         str(filters) + " filters, details: " + str(e)
            )
        return job_templates


class JobManager(object):
    """Base Manager for Jobs"""
    def _new_job_id(self):
        """a UUID based on the host ID and current time"""
        return uuid4()

    def __init__(self, job_type):
        """
        Entry point for initiating new job
        :param http_request: object
        :param job_type: string
        """
        self.start_time = None
        self.log_json = OrderedDict()
        self.job_result = False
        self.job_remarks = None
        self.output_json = {}
        self.job_type = job_type
        self.uuid = self._new_job_id()
        self.start_time = timezone.now()
        self.job_params = {}
        self.job_yml = None
        self.job_template = None
        self.visible_on_url = False
        self.ci_pipeline = None

    def create_job(self, user_email=None):
        match_params = {}
        match_params.update(dict(job_uuid=self.uuid))
        kwargs = {}
        kwargs.update(match_params)
        kwargs.update(dict(job_type=self.job_type))
        kwargs.update(dict(job_start_time=self.start_time))
        if user_email:
            kwargs.update(dict(triggered_by=user_email))
        try:
            Job.objects.update_or_create(
                **match_params, defaults=kwargs
            )
        except Exception:
            # log event, pass for now
            return False
        else:
            return True

    def mark_job_finish(self, remove=None):
        """Update job with finish details"""
        try:
            if remove:
                Job.objects.filter(job_uuid=self.uuid).delete()
            else:
                Job.objects.filter(job_uuid=self.uuid).update(
                    job_end_time=timezone.now(),
                    job_log_json_str=json.dumps(self.log_json),
                    job_result=self.job_result,
                    job_remarks=self.job_remarks,
                    job_output_json_str=json.dumps(self.output_json),
                    job_template=self.job_template,
                    job_yml_text=self.job_yml,
                    job_params_json_str=json.dumps(self.job_params),
                    job_visible_on_url=self.visible_on_url,
                    ci_pipeline=self.ci_pipeline
                )
        except Exception:
            return False
        else:
            return True


class JobsLogManager(BaseManager):
    """Maintains Job Logs"""

    package_manager = PackagesManager()

    def get_job_logs(self, remarks=None, result=None, no_pipeline=True):
        """Fetch all job logs from the db"""
        job_logs = None
        filters = {}
        if remarks:
            filters.update(dict(job_remarks=remarks))
        if result:
            filters.update(dict(job_result=True))
        if no_pipeline:
            filters.update(dict(ci_pipeline__isnull=True))
        else:
            filters.update(dict(ci_pipeline__isnull=False))
        job_logs = Job.objects.filter(**filters).order_by('-job_start_time')
        return job_logs

    def get_job_detail(self, job_id):
        """
        Fetch just one job
        :param job_id: Job ID: uuid
        :return: Job object
        """
        job_log = None
        if not job_id:
            return job_log
        job_log = Job.objects.filter(job_uuid=job_id).first()
        return job_log

    def get_joblog_stats(self):
        """Stats about jobs log"""
        last_ran_on = None
        last_ran_type = None
        jobs_logs = self.get_job_logs()
        jobs_count = jobs_logs.count()
        successful_jobs = jobs_logs.filter(**{'job_result': True})
        if successful_jobs.count() > 0:
            last_ran_on = successful_jobs[0].job_end_time
            last_ran_type = successful_jobs[0].job_type
        return jobs_count, last_ran_on, last_ran_type

    def analyse_job_data(self, job_data):
        """
        Analyses job output (of a package) to emit meaningful data
        :param job_data: dict
        :return: dict or None
        """
        if not job_data:
            return
        analysable_fields = ['Latest Build Details',
                             'Calculate Translation Stats']
        fields_to_analyse = [field for field in job_data.keys()
                             if field in analysable_fields]

        field_heading = ['Language',
                         'Total',
                         'Translated',
                         'Fuzzy',
                         'Untranslated',
                         'Complete']

        if not fields_to_analyse and not len(fields_to_analyse) > 0:
            return

        try:
            analysed_data = {}
            total_no_of_messages = []

            for field in fields_to_analyse:
                if field == analysable_fields[0]:
                    build_details = list(job_data.get(analysable_fields[0], {}).values())
                    if build_details and len(build_details) > 0:
                        build_details = load(build_details[0], Loader=FullLoader)
                    if isinstance(build_details, dict):
                        analysed_data.update({
                            'meta_data': {
                                'package': build_details.get('package_name', ''),
                                'nvr': build_details.get('nvr', ''),
                                'built_on': build_details.get('completion_time', '')
                            }
                        })
                elif field == analysable_fields[1]:
                    stats_json_data = list(job_data.get(analysable_fields[1], {}).values())
                    if stats_json_data and len(stats_json_data) > 0:
                        data = {}
                        for json_data in stats_json_data:
                            if '{' in json_data:
                                data = load(json_data[json_data.find('{'):],
                                            Loader=FullLoader)
                        stats_json = data.get('stats', {})
                        if stats_json and isinstance(stats_json, list):

                            lang_id_name = self.package_manager.get_lang_id_name_dict() or []
                            locale_lang_dict = dict(self.package_manager.get_locale_lang_tuple())
                            locale_key = 'locale'

                            processed_stats = []
                            analysed_data['stats'] = []
                            for locale, l_alias in list(lang_id_name.keys()):
                                filter_stat = []
                                stats_chunk = []

                                try:
                                    filter_stat = self.package_manager.filter_n_reduce_stats(
                                        locale_key, locale, l_alias, stats_json
                                    )
                                except Exception as e:
                                    self.app_logger(
                                        'ERROR', "Error while filtering stats, details: " + str(e))
                                else:
                                    filter_stat = filter_stat[0] \
                                        if isinstance(filter_stat, list) and len(filter_stat) > 0 else {}

                                stats_chunk.append(locale_lang_dict.get(locale, locale))
                                if filter_stat.get('total') and filter_stat.get('total') > 0:
                                    total_no_of_messages.append(filter_stat.get('total'))
                                stats_chunk.append(filter_stat.get('total', 0))
                                stats_chunk.append(filter_stat.get('translated', 0))
                                stats_chunk.append(filter_stat.get('fuzzy', 0))
                                stats_chunk.append(filter_stat.get('untranslated', 0))
                                completion_percentage = 0
                                try:
                                    completion_percentage = int((filter_stat.get('translated', 0) * 100 /
                                                                 filter_stat.get('total', 0)))
                                except ZeroDivisionError as e:
                                    self.app_logger(
                                        'ERROR', "Error while calculating completion_percentage, details: " + str(e)
                                    )
                                stats_chunk.append(completion_percentage)
                                if stats_chunk:
                                    non_zero_stats = [i for i in stats_chunk[1:] if i > 0]
                                    if non_zero_stats and len(non_zero_stats) > 0:
                                        processed_stats.append(stats_chunk)

                            analysed_data['stats'].extend(processed_stats)
                        analysed_data.update(dict(headings=field_heading))
        except Exception as e:
            self.app_logger(
                'ERROR', "Error while analysing job data, details: " + str(e))
            return
        if len(set(total_no_of_messages)) > 1:
            analysed_data['pot_differ'] = "Total number of messages differ across languages."
        return analysed_data


class TransplatformSyncManager(BaseManager):
    """Translation Platform Sync Manager"""

    def __init__(self, *args, **kwargs):
        """entry point"""
        super(TransplatformSyncManager, self).__init__(self, *args, **kwargs)
        self.job_manager = JobManager(TS_JOB_TYPES[0])

    def syncstats_initiate_job(self):
        """Creates a Sync Job"""
        if self.job_manager.create_job(user_email=self.active_user_email):
            return self.job_manager.uuid
        return None

    def sync_trans_stats(self):
        """Run Sync process in sequential steps"""
        stages = (
            self.update_trans_projects,
            self.update_project_details,
            self.job_manager.mark_job_finish,
        )

        [method() for method in stages]

    def update_trans_projects(self):
        """Update projects json for transplatform in db"""
        self.job_manager.log_json['Projects'] = OrderedDict()
        try:
            transplatforms = Platform.objects.only('engine_name', 'api_url',
                                                   'auth_login_id', 'auth_token_key') \
                .filter(server_status=True).all()
        except Exception as e:
            self.job_manager.log_json['Projects'].update(
                {str(datetime.now()): 'Fetch transplatform from db failed. Details: ' + str(e)}
            )
            self.job_manager.job_result = False
        else:
            self.job_manager.log_json['Projects'].update(
                {str(datetime.now()): str(len(transplatforms)) + ' translation platforms fetched from db.'}
            )
            for platform in transplatforms:
                response_dict = self.api_resources.fetch_all_projects(
                    platform.engine_name, platform.api_url, **dict(
                        auth_user=platform.auth_login_id, auth_token=platform.auth_token_key
                    )
                )
                if response_dict:
                    # save projects json in db
                    try:
                        Platform.objects.filter(api_url=platform.api_url).update(
                            projects_json_str=json.dumps(response_dict),
                            projects_last_updated=timezone.now()
                        )
                    except Exception as e:
                        self.job_manager.log_json['Projects'].update(
                            {str(datetime.now()): 'Projects JSON for ' + platform.api_url +
                                                  ' failed to get saved in db. Details: ' + str(e)}
                        )
                        self.job_manager.job_result = False
                    else:
                        self.job_manager.log_json['Projects'].update(
                            {str(datetime.now()): 'Projects JSON for ' + platform.api_url + ' saved in db.'}
                        )
                        self.job_manager.job_result = True
                else:
                    self.job_manager.log_json['Projects'].update(
                        {str(datetime.now()): 'Projects JSON for ' + platform.api_url + ' could not be fetched.'}
                    )
        return self.job_manager.job_result

    def update_project_details(self):
        """Update project details json in db"""
        self.job_manager.log_json['Project-Details'] = OrderedDict()
        try:
            project_urls = Package.objects.select_related()
        except Exception as e:
            self.job_manager.log_json['Project-Details'].update(
                {str(datetime.now()): 'Fetch Project URLs from db failed. Details: ' + str(e)}
            )
            self.job_manager.job_result = False
        else:
            self.job_manager.log_json['Project-Details'].update(
                {str(datetime.now()): str(len(project_urls)) + ' Project URLs fetched from db.'}
            )
            if project_urls and len(project_urls) > 0:
                for url in project_urls:
                    project_details_resp_dict = self.api_resources.fetch_project_details(
                        url.platform_slug.engine_name, url.platform_slug.api_url, url.package_name,
                        **(dict(auth_user=url.platform_slug.auth_login_id,
                                auth_token=url.platform_slug.auth_token_key))
                    )
                    if project_details_resp_dict:
                        try:
                            Package.objects.filter(platform_url=url.platform_url).update(
                                package_details_json_str=json.dumps(project_details_resp_dict),
                                details_json_last_updated=timezone.now()
                            )
                        except Exception as e:
                            self.job_manager.log_json['Project-Details'].update(
                                {str(datetime.now()): 'Project Details JSON for ' + url.package_name +
                                                      ' failed to get saved in db. Details: ' + str(e)}
                            )
                            self.job_manager.job_result = False
                        else:
                            self.job_manager.log_json['Project-Details'].update(
                                {str(datetime.now()): 'Project Details JSON for ' +
                                                      url.package_name + ' saved in db.'}
                            )
                            self.job_manager.job_result = True
        return self.job_manager.job_result


class ReleaseScheduleSyncManager(BaseManager):
    """Release Schedule Sync Manager"""

    def __init__(self, *args, **kwargs):
        """entry point"""
        super(ReleaseScheduleSyncManager, self).__init__(self, *args, **kwargs)
        self.job_manager = JobManager(TS_JOB_TYPES[1])
        self.release_branch_manager = ReleaseBranchManager()

    def syncschedule_initiate_job(self):
        """Creates a Sync Job"""
        if self.job_manager.create_job(user_email=self.active_user_email):
            return self.job_manager.uuid
        return None

    def sync_release_schedule(self):
        """Run Sync process in sequential steps"""
        stages = (
            self.update_event_dates,
            self.job_manager.mark_job_finish,
        )

        [method() for method in stages]

    def update_event_dates(self):
        """Update schedule_json for all release branches"""
        SUBJECT = 'Release Branches'
        self.job_manager.log_json[SUBJECT] = OrderedDict()

        try:
            relbranches = Release.objects.only('release_slug', 'product_slug', 'calendar_url') \
                .filter(sync_calendar=True).all()
        except Exception as e:
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): 'Fetch release branches from db failed. Details: ' + str(e)}
            )
            self.job_result = False
        else:
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): str(len(relbranches)) + ' release branches fetched from db.'}
            )
            for relbranch in relbranches:
                product_slug = relbranch.product_slug.product_slug
                ical_events = self.release_branch_manager.get_calendar_events_dict(
                    relbranch.calendar_url, product_slug)
                release_stream = self.release_branch_manager.get_release_streams(
                    stream_slug=product_slug).get()
                required_events = release_stream.major_milestones
                schedule_dict = \
                    self.release_branch_manager.parse_events_for_required_milestones(
                        product_slug, relbranch.release_slug, ical_events, required_events
                    )
                if schedule_dict:
                    relbranch_update_result = Release.objects.filter(
                        release_slug=relbranch.release_slug
                    ).update(schedule_json_str=json.dumps(schedule_dict))
                    if relbranch_update_result:
                        self.job_manager.log_json[SUBJECT].update(
                            {str(datetime.now()): 'Release schedule for ' + relbranch.release_slug +
                                                  ' branch updated in db.'}
                        )
                        self.job_manager.job_result = True
                else:
                    self.job_manager.log_json[SUBJECT].update(
                        {str(datetime.now()): 'Release schedule for ' + relbranch.release_slug +
                                              ' failed to get saved in db.'}
                    )
                    self.job_manager.job_result = False
        return self.job_manager.job_result


class BuildTagsSyncManager(BaseManager):
    """Build Tags Sync Manager"""

    def __init__(self, *args, **kwargs):
        """entry point"""
        super(BuildTagsSyncManager, self).__init__(self, *args, **kwargs)
        self.job_manager = JobManager(TS_JOB_TYPES[4])
        self.release_branch_manager = ReleaseBranchManager()

    def syncbuildtags_initiate_job(self):
        """Creates a Sync Job"""
        if self.job_manager.create_job(user_email=self.active_user_email):
            return self.job_manager.uuid
        return None

    def sync_build_tags(self):
        """Run Sync process in sequential steps"""
        stages = (
            self.update_build_system_tags,
            self.job_manager.mark_job_finish,
        )

        [method() for method in stages]

    def update_build_system_tags(self):
        """Update build system tags"""
        SUBJECT = 'Build System Tags'
        self.job_manager.log_json[SUBJECT] = OrderedDict()

        active_release_streams = \
            self.release_branch_manager.get_release_streams(only_active=True)

        self.job_manager.log_json[SUBJECT].update(
            {str(datetime.now()): str(len(active_release_streams)) + ' releases fetched from db.'}
        )

        for relstream in active_release_streams or []:
            hub_server_url = relstream.product_server
            # # for brew several configuration needs to be set
            # # before we access its hub for info, #todo
            # if relstream.product_build_system == 'koji':
            try:
                tags = self.api_resources.build_tags(
                    hub_url=hub_server_url, product=relstream
                )
            except Exception as e:
                self.job_manager.log_json[SUBJECT].update(
                    {str(datetime.now()): 'Failed to fetch build tags of %s. Details: %s' %
                                          (relstream.product_build_system, str(e))}
                )
                self.job_manager.job_result = False
            else:
                if tags:
                    relbranch_update_result = Product.objects.filter(
                        product_slug=relstream.product_slug
                    ).update(product_build_tags=tags,
                             product_build_tags_last_updated=timezone.now())
                    if relbranch_update_result:
                        self.job_manager.log_json[SUBJECT].update(
                            {str(datetime.now()): '%s build tags of %s saved in db.' %
                                                  (str(len(tags)), relstream.product_build_system)}
                        )
                        self.job_manager.job_result = True
        return self.job_manager.job_result


class YMLBasedJobManager(BaseManager):
    """
    Base class to handle YAML Jobs

    Single Entry Point for
        - YAML based Jobs
            - syncupstream
            - syncdownstream
            - stringchange
            - pushtrans
            - pulltrans
            - dpushtrans
            - pulltransmerge
    """

    sandbox_path = 'dashboard/sandbox/'
    job_log_file = sandbox_path + '.log'

    package_manager = PackagesManager()
    ci_pipeline_manager = CIPipelineManager()

    @staticmethod
    def job_suffix(args):
        return "-".join(args)

    def __init__(self, *args, **kwargs):
        """Set Job Environment here"""
        super(YMLBasedJobManager, self).__init__(**kwargs)
        self.suffix = self.job_suffix(
            [getattr(self, param, '') for param in self.params][:3]
        )
        self.job_log_file = self.sandbox_path + '.log'

    def _get_package(self):
        package_details = \
            self.package_manager.get_packages([self.package])
        return package_details.get()

    def _get_ci_pipeline(self):
        ci_pipeline_details = \
            self.ci_pipeline_manager.get_ci_pipelines(
                uuids=[self.ci_pipeline_uuid])
        return ci_pipeline_details.get()

    @staticmethod
    def _check_git_ext(upstream_url):
        # required for cloning
        return upstream_url if upstream_url.endswith('.git') else upstream_url + ".git"

    def _weblate_git_url(self, package):
        platform_url = package.platform_slug.api_url
        parsed_url = urlparse(platform_url)
        return "{}://{}/git/{}/{}/".format(
            parsed_url.scheme, parsed_url.netloc,
            package.package_name, self.REPO_BRANCH
        )

    def __bootstrap(self, package=None, build_system=None, ci_pipeline=None):
        """
        Creates required env (values) as per job category.
        """
        if build_system:
            try:
                release_streams = \
                    self.package_manager.get_release_streams(built=build_system)
                release_stream = release_streams.first()
            except Exception as e:
                self.app_logger(
                    'ERROR', "Release stream could not be found, details: " + str(e)
                )
                raise Exception('Build Server URL could NOT be located for %s.' % build_system)
            else:
                self.hub_url = release_stream.product_server
        if package:
            try:
                package_detail = self._get_package()
            except Exception as e:
                self.app_logger(
                    'ERROR', "Package could not be found, details: " + str(e)
                )
                # downstreamsync can be run for a package not in Transtats.
                if self.type != TS_JOB_TYPES[3]:
                    raise Exception('Upstream URL could NOT be located for %s package.' % package)
            else:
                upstream_repo_url = package_detail.upstream_url
                upstream_l10n_url = package_detail.upstream_l10n_url
                if getattr(self, 'REPO_TYPE', '') and self.REPO_TYPE == GIT_REPO_TYPE[1]:
                    if not package_detail.upstream_l10n_url:
                        raise Exception('Localization repo URL not found.')
                    upstream_repo_url = package_detail.upstream_l10n_url
                if getattr(self, 'REPO_TYPE', '') and self.REPO_TYPE == GIT_REPO_TYPE[2]:
                    if not self.REPO_TYPE == package_detail.platform_slug.engine_name:
                        raise Exception('Package Platform is NOT Weblate.')
                    self.upstream_repo_url = self._weblate_git_url(package_detail)
                else:
                    self.upstream_repo_url = self._check_git_ext(upstream_repo_url)
                    if upstream_l10n_url:
                        self.upstream_l10n_url = self._check_git_ext(upstream_l10n_url)
                t_ext = package_detail.translation_file_ext
                file_ext = t_ext if t_ext.startswith('.') else '.' + t_ext
                self.trans_file_ext = file_ext.lower()
                self.pkg_upstream_name = package_detail.upstream_name
                self.pkg_downstream_name = package_detail.downstream_name
                self.pkg_tp_engine = package_detail.platform_slug.engine_name
                self.pkg_tp_url = package_detail.platform_slug.api_url
                self.pkg_tp_auth_usr = package_detail.platform_slug.auth_login_id
                self.pkg_tp_auth_token = package_detail.platform_slug.auth_token_key
                self.pkg_branch_map = package_detail.release_branch_mapping_json
        if ci_pipeline:
            try:
                ci_pipeline_detail = self._get_ci_pipeline()
            except Exception as e:
                self.app_logger(
                    'ERROR', "CI Pipeline could not be found, details: " + str(e)
                )
                raise Exception('CI pipeline could NOT be located for UUID %s.' % ci_pipeline)
            else:
                if self.package != ci_pipeline_detail.ci_package.package_name:
                    raise Exception('CI Pipeline does NOT belong to the package.')
                self.pkg_ci_engine = ci_pipeline_detail.ci_platform.engine_name
                self.pkg_ci_url = ci_pipeline_detail.ci_platform.api_url
                self.pkg_ci_auth_usr = ci_pipeline_detail.ci_platform.auth_login_id
                self.pkg_ci_auth_token = ci_pipeline_detail.ci_platform.auth_token_key
                self.ci_release = ci_pipeline_detail.ci_release.release_slug
                self.ci_target_langs = ci_pipeline_detail.ci_project_details_json.get('targetLangs', [])
                self.ci_project_uid = ci_pipeline_detail.ci_project_details_json.get('uid', '')
                self.ci_pipeline_id = ci_pipeline_detail.ci_pipeline_id
                pipeline_workflow_step = getattr(self, 'WORKFLOW_STEP', 'default')
                ci_lang_job_map = self.ci_pipeline_manager.ci_lang_job_map(
                    pipelines=[ci_pipeline_detail], workflow_step=pipeline_workflow_step)
                if ci_lang_job_map.get(ci_pipeline_detail.ci_pipeline_uuid):
                    self.ci_lang_job_map = ci_lang_job_map[ci_pipeline_detail.ci_pipeline_uuid]

    def _save_stats_in_db(self, stats_dict, build_details):
        """
        Save derived stats in db from YML Job
        :param stats_dict: translation stats calculated
        """
        if not self.package_manager.is_package_exist(package_name=self.package):
            raise Exception("Derived stats could NOT be saved. Check Dry Run.")
        stats_version, stats_source = '', ''
        if self.type == TS_JOB_TYPES[2]:
            stats_version, stats_source = 'Upstream', 'upstream'
        elif self.type == TS_JOB_TYPES[3]:
            stats_version, stats_source = self.buildsys + ' - ' + self.tag, self.buildsys

        try:
            self.package_manager.syncstats_manager.save_version_stats(
                self._get_package(), stats_version, stats_dict, stats_source
            )
            if stats_source == 'upstream':
                self.package_manager.update_package(self.package, {
                    'upstream_last_updated': timezone.now()
                })
            # If it's for rawhide, update downstream sync time for the package
            if getattr(self, 'tag', ''):
                self.package_manager.update_package(self.package, {
                    'downstream_last_updated': timezone.now()
                })
            # If invoked by system user, cache build details
            if self.active_user_email == SYS_EMAIL_ADDR and \
                    self.type == TS_JOB_TYPES[3]:
                cache_params = {}
                match_params = {
                    'package_name': self._get_package(),
                    'build_system': self.buildsys,
                    'build_tag': self.tag
                }
                cache_params.update(match_params)
                latest_build = {}
                if isinstance(build_details, list) and build_details and len(build_details) > 0:
                    latest_build = build_details[0]
                cache_params['build_details_json_str'] = json.dumps(latest_build)
                CacheBuildDetails.objects.update_or_create(
                    package_name=self._get_package(), build_system=self.buildsys,
                    build_tag=self.tag, defaults=cache_params
                )
        except Exception as e:
            self.app_logger(
                'ERROR', "Package could not be updated, details: " + str(e)
            )
            raise Exception('Derived stats could NOT be saved in db.')

    def _save_push_results_in_db(self, job_details):
        """Save jobs which are created/updated in CI Platform for a project"""
        try:
            for platform_project, jobs in job_details.items():
                if platform_project != self.ci_project_uid:
                    raise Exception('Save: CI Pipeline UID did NOT match.')
                # disable storing push_resp_data in CIPlatformJob, temporarily
                # and just refreshing the pipeline_details

                # for lang, job_details in jobs.items():
                #     platform_job = dict()
                #     platform_job['ci_pipeline'] = self._get_ci_pipeline()
                #     platform_job['ci_platform_job_json_str'] = json.dumps(job_details)
                #     self.ci_pipeline_manager.save_ci_platform_job(platform_job)
                self.ci_pipeline_manager.refresh_ci_pipeline(self.ci_pipeline_id)
        except Exception as e:
            self.app_logger(
                'ERROR', "Platform job could not be updated, details: " + str(e)
            )
            raise Exception('Details could NOT be saved in db.')

    def _wipe_workspace(self):
        """This makes sandbox clean for a new job to run"""
        # remove log file if exists
        if os.path.exists(self.job_log_file):
            os.remove(self.job_log_file)
        for file in os.listdir(self.sandbox_path):
            file_path = os.path.join(self.sandbox_path, file)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            elif os.path.isfile(file_path) and not file_path.endswith('.py') \
                    and '.log.' not in file_path:
                os.unlink(file_path)

    def execute_job(self):
        """
        1. PreProcess YML and replace variables with input_values
            - Example: %PACKAGE_NAME%
        2. Parse processed YML and build Job object
        3. Select data structure for tasks and instantiate one
            - Example: Linked list should be used for sequential tasks
        3. Discover namespace and method for each task and fill in TaskNode
        4. Perform actions (execute tasks) and return responses
        """
        self._wipe_workspace()

        yml_preprocessed = YMLPreProcessor(self.YML_FILE, **{
            param: getattr(self, param, '') for param in self.params
        }).output

        self.job_base_dir = os.path.dirname(settings.BASE_DIR)
        yml_job = YMLJobParser(yml_stream=io.StringIO(yml_preprocessed))

        try:
            self.yml_job_name = yml_job.job_name
        except AttributeError:
            raise Exception('Input YML could not be parsed.')

        self.package = yml_job.package
        self.release = yml_job.release
        self.buildsys = yml_job.buildsys
        self.repo_branch = getattr(self, 'REPO_BRANCH', '')
        self.ci_pipeline_uuid = yml_job.ci_pipeline
        if isinstance(yml_job.tags, list) and len(yml_job.tags) > 0:
            self.tag = yml_job.tags[0]
        elif isinstance(yml_job.tags, str):
            self.tag = yml_job.tags

        if self.type != yml_job.job_type:
            raise Exception('Selected job type differs to that of YML.')

        # bootstrap the job
        self.__bootstrap(package=self.package,
                         build_system=self.buildsys,
                         ci_pipeline=self.ci_pipeline_uuid)

        # for sequential jobs, tasks should be pushed to linked list
        # and output of previous task will be input for next task
        if JOB_EXEC_TYPES[0] in yml_job.execution:
            self.tasks_ds = TaskList()
        else:
            raise Exception('%s exec type is NOT supported yet.' % yml_job.execution)

        # lets create a job
        job_manager = JobManager(self.type)
        if job_manager.create_job(user_email=self.active_user_email):
            self.job_id = job_manager.uuid
            job_manager.job_remarks = self.package
        # and set tasks
        tasks = yml_job.tasks
        for task in tasks:
            self.tasks_ds.add_task(task)
        log_file = self.job_log_file + ".%s.%s" % (self.suffix, self.type)
        if os.path.exists(log_file):
            os.unlink(log_file)
        action_mapper = ActionMapper(
            self.tasks_ds,
            self.job_base_dir,
            getattr(self, 'tag', ''),
            getattr(self, 'package', ''),
            getattr(self, 'hub_url', ''),
            getattr(self, 'buildsys', ''),
            getattr(self, 'release', ''),
            getattr(self, 'repo_branch', ''),
            getattr(self, 'ci_pipeline_uuid', ''),
            getattr(self, 'upstream_repo_url', ''),
            getattr(self, 'upstream_l10n_url', ''),
            getattr(self, 'trans_file_ext', ''),
            getattr(self, 'pkg_upstream_name', ''),
            getattr(self, 'pkg_downstream_name', ''),
            getattr(self, 'pkg_branch_map', {}),
            getattr(self, 'pkg_tp_engine', ''),
            getattr(self, 'pkg_tp_auth_usr', ''),
            getattr(self, 'pkg_tp_auth_token', ''),
            getattr(self, 'pkg_tp_url', ''),
            getattr(self, 'pkg_ci_engine', ''),
            getattr(self, 'pkg_ci_url', ''),
            getattr(self, 'pkg_ci_auth_usr', ''),
            getattr(self, 'pkg_ci_auth_token', ''),
            getattr(self, 'ci_release', ''),
            getattr(self, 'ci_target_langs', []),
            getattr(self, 'ci_project_uid', ''),
            getattr(self, 'ci_lang_job_map', {}),
            log_file
        )
        action_mapper.set_actions()
        # lets execute collected tasks
        try:
            action_mapper.execute_tasks()
        except Exception as e:
            job_manager.job_result = False
            setattr(self, 'exception', e)
            raise Exception(e)
        else:
            job_manager.output_json = action_mapper.result
            job_manager.job_params.update(
                {param: getattr(self, param, '') for param in self.params}
            )
            job_template_manager = JobTemplateManager()
            templates = job_template_manager.get_job_templates(**{
                'job_template_type': self.type
            })
            if templates and len(templates) > 0:
                template_obj = templates.first()
                job_manager.job_template = template_obj
            job_manager.visible_on_url = True
            job_manager.job_result = True
        finally:
            job_manager.job_yml = yml_preprocessed
            if getattr(self, 'exception', ''):
                action_mapper.log.update(dict(
                    Exception={str(datetime.now()): '%s' % getattr(self, 'exception', '')}))
            job_manager.log_json = action_mapper.log
            if getattr(self, 'ci_pipeline_uuid', ''):
                job_manager.ci_pipeline = self._get_ci_pipeline()
            action_mapper.clean_workspace()
            if not getattr(self, 'SCRATCH', None):
                job_manager.mark_job_finish()
            else:
                job_manager.mark_job_finish(remove=True)
            time.sleep(3)
        # if not a dry run, save results is db
        if action_mapper.result and not getattr(self, 'DRY_RUN', None):
            if self.type in (TS_JOB_TYPES[2], TS_JOB_TYPES[3]):
                self._save_stats_in_db(action_mapper.result, action_mapper.build)
            if self.type in ([TS_JOB_TYPES[7], TS_JOB_TYPES[9]]):
                self._save_push_results_in_db(action_mapper.result.get('push_files_resp', {}))
        if os.path.exists(log_file):
            os.unlink(log_file)
        return self.job_id
