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
from collections import OrderedDict
from datetime import datetime
from uuid import uuid4

# django
from django.utils import timezone

# dashboard
from dashboard.constants import TRANSPLATFORM_ENGINES
from dashboard.managers.base import BaseManager
from dashboard.managers.inventory import ReleaseBranchManager
from dashboard.managers.utilities import parse_project_details_json
from dashboard.models import (
    TransPlatform, Packages, Jobs, SyncStats, StreamBranches
)


__all__ = ['JobManager', 'JobsLogManager', 'TransplatformSyncManager',
           'ReleaseScheduleSyncManager']


class JobManager(object):
    """
    Base Manager for Jobs
    """
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
        self.start_time = None
        self.log_json = OrderedDict()
        self.job_result = False
        self.job_remarks = None
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


class TransplatformSyncManager(BaseManager):
    """
    Translation Platform Sync Manager
    """

    def __init__(self, job_type):
        """
        entry point
        """
        super(TransplatformSyncManager, self).__init__()
        self.job_manager = JobManager(job_type)

    def syncstats_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.job_manager.create_job():
            return self.job_manager.uuid
        return None

    def sync_trans_stats(self):
        """
        Run Sync process in sequential steps
        """
        stages = (
            self.update_trans_projects,
            self.update_project_details,
            self.update_trans_stats,
            self.job_manager.mark_job_finish,
        )

        [method() for method in stages]

    def update_trans_projects(self):
        """
        Update projects json for transplatform in db
        """
        self.job_manager.log_json['Projects'] = OrderedDict()
        try:
            transplatforms = TransPlatform.objects.only('engine_name', 'api_url') \
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
                rest_handle = self.rest_client(platform.engine_name, platform.api_url)
                response_dict = rest_handle.process_request('list_projects')
                if response_dict and response_dict.get('json_content'):
                    # save projects json in db
                    try:
                        TransPlatform.objects.filter(api_url=platform.api_url).update(
                            projects_json=response_dict['json_content'], projects_lastupdated=timezone.now()
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
        """
        Update project details json in db
        """
        self.job_manager.log_json['Project-Details'] = OrderedDict()
        try:
            project_urls = Packages.objects.select_related()
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
                            self.job_manager.log_json['Project-Details'].update(
                                {str(datetime.now()): 'Project Details JSON for ' + transplatform_project_name +
                                                      ' failed to get saved in db. Details: ' + str(e)}
                            )
                            self.job_manager.job_result = False
                        else:
                            self.job_manager.log_json['Project-Details'].update(
                                {str(datetime.now()): 'Project Details JSON for ' +
                                                      transplatform_project_name + ' saved in db.'}
                            )
                            self.job_manager.job_result = True
        return self.job_manager.job_result

    def update_trans_stats(self):
        """
        Update translation stats for each project-version in db
        """
        self.job_manager.log_json['Translation-Stats'] = OrderedDict()
        try:
            packages = Packages.objects.select_related()
        except Exception as e:
            self.job_manager.log_json['Translation-Stats'].update(
                {str(datetime.now()): 'Fetch Project Details from db failed. Details: ' + str(e)}
            )
            self.job_manager.job_result = False
        else:
            self.job_manager.log_json['Translation-Stats'].update(
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
                                params.update(dict(job_uuid=self.job_manager.uuid))
                                params.update(dict(project_version=version))
                                params.update(dict(stats_raw_json=response_dict['json_content']))
                                params.update(dict(sync_iter_count=1))
                                params.update(dict(sync_visibility=True))
                                new_sync_stats = SyncStats(**params)
                                new_sync_stats.save()
                            else:
                                SyncStats.objects.filter(package_name=project, project_version=version).update(
                                    job_uuid=self.job_manager.uuid, stats_raw_json=response_dict['json_content'],
                                    sync_iter_count=existing_sync_stat.sync_iter_count + 1
                                )
                            Packages.objects.filter(transplatform_url=package.transplatform_url).update(
                                transtats_lastupdated=timezone.now())
                        except Exception as e:
                            self.job_manager.log_json['Translation-Stats'].update(
                                {str(datetime.now()): 'Transtats JSON for project: ' + project + ' of version: ' +
                                                      version + ' failed to get saved in db. Details: ' + str(e)}
                            )
                            self.job_manager.job_result = False
                        else:
                            self.job_manager.log_json['Translation-Stats'].update(
                                {str(datetime.now()): 'Transtats JSON for project: ' + project + ' of version: ' +
                                                      version + ' saved in db.'}
                            )
                            self.job_manager.job_result = True
        return self.job_manager.job_result


class ReleaseScheduleSyncManager(BaseManager):
    """
    Release Schedule Sync Manager
    """

    def __init__(self, job_type):
        """
        entry point
        """
        super(ReleaseScheduleSyncManager, self).__init__()
        self.job_manager = JobManager(job_type)
        self.release_branch_manager = ReleaseBranchManager()

    def syncschedule_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.job_manager.create_job():
            return self.job_manager.uuid
        return None

    def sync_release_schedule(self):
        """
        Run Sync process in sequential steps
        """
        stages = (
            self.update_event_dates,
            self.job_manager.mark_job_finish,
        )

        [method() for method in stages]

    def update_event_dates(self):
        """
        Update schedule_json for all release branches
        """
        SUBJECT = 'Release Branches'
        self.job_manager.log_json[SUBJECT] = OrderedDict()

        try:
            relbranches = StreamBranches.objects.only('relbranch_slug', 'relstream_slug', 'calendar_url') \
                .filter(sync_calendar=True).all()
        except Exception as e:
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): 'Fetch relbranches from db failed. Details: ' + str(e)}
            )
            self.job_result = False
        else:
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): str(len(relbranches)) + ' release branches fetched from db.'}
            )
            for relbranch in relbranches:
                ical_events = self.release_branch_manager.get_calender_events_dict(
                    relbranch.calendar_url, relbranch.relstream_slug)
                release_stream = self.release_branch_manager.get_release_streams(
                    stream_slug=relbranch.relstream_slug).get()
                required_events = release_stream.major_milestones
                schedule_dict = \
                    self.release_branch_manager.parse_events_for_required_milestones(
                        relbranch.relstream_slug, relbranch.relbranch_slug, ical_events, required_events
                    )
                if schedule_dict:
                    relbranch_update_result = StreamBranches.objects.filter(
                        relbranch_slug=relbranch.relbranch_slug
                    ).update(schedule_json=schedule_dict)
                    if relbranch_update_result:
                        self.job_manager.log_json[SUBJECT].update(
                            {str(datetime.now()): 'Release schedule for ' + relbranch.relbranch_slug +
                                                  ' branch updated in db.'}
                        )
                        self.job_manager.job_result = True
                else:
                    self.job_manager.log_json[SUBJECT].update(
                        {str(datetime.now()): 'Release schedule for ' + relbranch.relbranch_slug +
                                              ' failed to get saved in db.'}
                    )
                    self.job_manager.job_result = False
        return self.job_manager.job_result
