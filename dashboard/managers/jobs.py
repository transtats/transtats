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
import shutil
import time
from collections import OrderedDict
from datetime import datetime
from uuid import uuid4

# django
from django.conf import settings
from django.utils import timezone

# dashboard
from dashboard.constants import TS_JOB_TYPES, JOB_EXEC_TYPES
from dashboard.engine.action_mapper import ActionMapper
from dashboard.engine.ds import TaskList
from dashboard.engine.parser import YMLPreProcessor, YMLJobParser
from dashboard.managers.base import BaseManager
from dashboard.managers.packages import PackagesManager
from dashboard.managers.inventory import ReleaseBranchManager
from dashboard.models import (
    TransPlatform, Packages, ReleaseStream, StreamBranches,
    JobTemplates, Jobs
)


__all__ = ['JobTemplateManager', 'JobManager', 'JobsLogManager',
           'TransplatformSyncManager', 'ReleaseScheduleSyncManager',
           'BuildTagsSyncManager', 'YMLBasedJobManager']


class JobTemplateManager(BaseManager):
    """
    Job Templates Manager
    """
    def get_job_templates(self, *fields, **filters):
        """
        Get Job Templates from db
        :param fields: template fields to fetch
        :param filters: Any filters to apply
        :return: Query sets
        """
        job_templates = []
        try:
            job_templates = JobTemplates.objects.only(*fields).filter(**filters)
        except Exception as e:
            self.app_logger(
                'ERROR', "Job templates could not be fetched for " +
                         str(filters) + " filters, details: " + str(e)
            )
        return job_templates


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
        self.output_json = {}
        self.job_type = job_type
        self.uuid = self._new_job_id()
        self.start_time = timezone.now()
        self.job_params = {}
        self.job_yml = None
        self.job_template = None
        self.visible_on_url = False

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
            Jobs.objects.update_or_create(
                **match_params, defaults=kwargs
            )
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
                job_result=self.job_result,
                job_remarks=self.job_remarks,
                job_output_json=self.output_json,
                job_template=self.job_template,
                job_yml_text=self.job_yml,
                job_params_json=self.job_params,
                job_visible_on_url=self.visible_on_url
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

    def get_job_detail(self, job_id):
        """
        Fetch just one job
        :param job_id: Job ID: uuid
        :return: Job object
        """
        job_log = None
        if not job_id:
            return job_log
        try:
            job_log = Jobs.objects.filter(job_uuid=job_id).first()
        except:
            # log event, passing for now
            pass
        return job_log

    def get_joblog_stats(self):
        """
        Stats about jobs log
        """
        last_ran_on = None
        last_ran_type = None
        jobs_logs = self.get_job_logs()
        jobs_count = jobs_logs.count()
        successful_jobs = jobs_logs.filter(**{'job_result': True})
        if successful_jobs.count() > 0:
            last_ran_on = successful_jobs[0].job_end_time
            last_ran_type = successful_jobs[0].job_type
        return jobs_count, last_ran_on, last_ran_type


class TransplatformSyncManager(BaseManager):
    """
    Translation Platform Sync Manager
    """

    def __init__(self, *args, **kwargs):
        """
        entry point
        """
        super(TransplatformSyncManager, self).__init__(self, *args, **kwargs)
        self.job_manager = JobManager(TS_JOB_TYPES[0])

    def syncstats_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.job_manager.create_job(user_email=self.active_user_email):
            return self.job_manager.uuid
        return None

    def sync_trans_stats(self):
        """
        Run Sync process in sequential steps
        """
        stages = (
            self.update_trans_projects,
            self.update_project_details,
            self.job_manager.mark_job_finish,
        )

        [method() for method in stages]

    def update_trans_projects(self):
        """
        Update projects json for transplatform in db
        """
        self.job_manager.log_json['Projects'] = OrderedDict()
        try:
            transplatforms = TransPlatform.objects.only('engine_name', 'api_url',
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
                        TransPlatform.objects.filter(api_url=platform.api_url).update(
                            projects_json=response_dict, projects_lastupdated=timezone.now()
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
                    project_details_resp_dict = self.api_resources.fetch_project_details(
                        url.transplatform_slug.engine_name, url.transplatform_slug.api_url, url.package_name,
                        **(dict(auth_user=url.transplatform_slug.auth_login_id,
                                auth_token=url.transplatform_slug.auth_token_key))
                    )
                    if project_details_resp_dict:
                        try:
                            Packages.objects.filter(transplatform_url=url.transplatform_url).update(
                                package_details_json=project_details_resp_dict,
                                details_json_lastupdated=timezone.now()
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
    """
    Release Schedule Sync Manager
    """

    def __init__(self, *args, **kwargs):
        """
        entry point
        """
        super(ReleaseScheduleSyncManager, self).__init__(self, *args, **kwargs)
        self.job_manager = JobManager(TS_JOB_TYPES[1])
        self.release_branch_manager = ReleaseBranchManager()

    def syncschedule_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.job_manager.create_job(user_email=self.active_user_email):
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
                ical_events = self.release_branch_manager.get_calendar_events_dict(
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


class BuildTagsSyncManager(BaseManager):
    """
    Build Tags Sync Manager
    """

    def __init__(self, *args, **kwargs):
        """
        entry point
        """
        super(BuildTagsSyncManager, self).__init__(self, *args, **kwargs)
        self.job_manager = JobManager(TS_JOB_TYPES[4])
        self.release_branch_manager = ReleaseBranchManager()

    def syncbuildtags_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.job_manager.create_job(user_email=self.active_user_email):
            return self.job_manager.uuid
        return None

    def sync_build_tags(self):
        """
        Run Sync process in sequential steps
        """
        stages = (
            self.update_build_system_tags,
            self.job_manager.mark_job_finish,
        )

        [method() for method in stages]

    def update_build_system_tags(self):
        """
        Update build system tags
        """
        SUBJECT = 'Build System Tags'
        self.job_manager.log_json[SUBJECT] = OrderedDict()

        active_release_streams = \
            self.release_branch_manager.get_release_streams(only_active=True)

        self.job_manager.log_json[SUBJECT].update(
            {str(datetime.now()): str(len(active_release_streams)) + ' releases fetched from db.'}
        )

        for relstream in active_release_streams or []:
            hub_server_url = relstream.relstream_server
            # # for brew several configuration needs to be set
            # # before we access its hub for info, #todo
            # if relstream.relstream_built == 'koji':
            try:
                tags = self.api_resources.build_tags(hub_url=hub_server_url)
            except Exception as e:
                self.job_manager.log_json[SUBJECT].update(
                    {str(datetime.now()): 'Failed to fetch build tags of %s. Details: %s' %
                                          (relstream.relstream_built, str(e))}
                )
                self.job_manager.job_result = False
            else:
                if tags:
                    relbranch_update_result = ReleaseStream.objects.filter(
                        relstream_slug=relstream.relstream_slug
                    ).update(relstream_built_tags=tags,
                             relstream_built_tags_lastupdated=timezone.now())
                    if relbranch_update_result:
                        self.job_manager.log_json[SUBJECT].update(
                            {str(datetime.now()): '%s build tags of %s saved in db.' %
                                                  (str(len(tags)), relstream.relstream_built)}
                        )
                        self.job_manager.job_result = True
        return self.job_manager.job_result


class YMLBasedJobManager(BaseManager):
    """
    Single Entry Point for
        - all YML based Jobs: syncupstream, syncdownstream, stringchange
        - this should be the base class to handle YML Jobs
    """

    sandbox_path = 'dashboard/sandbox/'
    job_log_file = sandbox_path + '.log'

    package_manager = PackagesManager()

    @staticmethod
    def job_suffix(args):
        return "-".join(args)

    def __init__(self, *args, **kwargs):
        """
        Set Job Environment here
        """
        super(YMLBasedJobManager, self).__init__(**kwargs)
        self.suffix = self.job_suffix(
            [getattr(self, param, '') for param in self.params]
        )

    def _bootstrap(self, package=None, build_system=None):
        if build_system:
            try:
                release_streams = \
                    self.package_manager.get_release_streams(built=build_system)
                release_stream = release_streams.get()
            except Exception as e:
                self.app_logger(
                    'ERROR', "Release stream could not be found, details: " + str(e)
                )
                raise Exception('Build Server URL could NOT be located for %s.' % build_system)
            else:
                self.hub_url = release_stream.relstream_server
        if package:
            try:
                package_details = \
                    self.package_manager.get_packages([package])
                package_detail = package_details.get()
            except Exception as e:
                self.app_logger(
                    'ERROR', "Package could not be found, details: " + str(e)
                )
                raise Exception('Upstream URL could NOT be located for %s.' % package)
            else:
                self.upstream_repo_url = package_detail.upstream_url \
                    if package_detail.upstream_url.endswith('.git') \
                    else package_detail.upstream_url + ".git"
                t_ext = package_detail.translation_file_ext
                file_ext = t_ext if t_ext.startswith('.') else '.' + t_ext
                self.trans_file_ext = file_ext.lower()
                self.pkg_upstream_name = package_detail.upstream_name
                self.pkg_tp_engine = package_detail.transplatform_slug.engine_name
                self.pkg_tp_url = package_detail.transplatform_slug.api_url
                self.pkg_tp_auth_usr = package_detail.transplatform_slug.auth_login_id
                self.pkg_tp_auth_token = package_detail.transplatform_slug.auth_token_key
                self.pkg_branch_map = package_detail.release_branch_mapping

    def _save_result_in_db(self, stats_dict):
        """
        Save derived stats in db from YML Job
        :param stats_dict: translation stats calculated
        """
        if not self.package_manager.is_package_exist(package_name=self.package):
            raise Exception("Stats NOT saved. Package does not exist.")
        stats_version, stats_source = '', ''
        if self.type == TS_JOB_TYPES[2]:
            stats_version, stats_source = 'Upstream', 'upstream'
        elif self.type == TS_JOB_TYPES[3]:
            stats_version, stats_source = self.buildsys + ' - ' + self.tag, self.buildsys

        try:
            self.package_manager.syncstats_manager.save_version_stats(
                self.package, stats_version, stats_dict, stats_source
            )
            if stats_source == 'upstream':
                self.package_manager.update_package(self.package, {
                    'upstream_lastupdated': timezone.now()
                })
            # If its for rawhide, update downstream sync time for the package
            if getattr(self, 'tag', '') == 'rawhide':
                self.package_manager.update_package(self.package, {
                    'downstream_lastupdated': timezone.now()
                })
        except Exception as e:
            self.app_logger(
                'ERROR', "Package could not be updated, details: " + str(e)
            )
            raise Exception('Stats could NOT be saved in db.')

    def _wipe_workspace(self):
        """
        This makes sandbox clean for a new job to run
        """
        # remove log file if exists
        if os.path.exists(self.job_log_file):
            os.remove(self.job_log_file)
        for file in os.listdir(self.sandbox_path):
            file_path = os.path.join(self.sandbox_path, file)
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                elif os.path.isfile(file_path) and not file_path.endswith('.py') \
                        and '.log.' not in file_path:
                    os.unlink(file_path)
            except Exception as e:
                pass

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
        self.buildsys = yml_job.buildsys
        if isinstance(yml_job.tags, list) and len(yml_job.tags) > 0:
            self.tag = yml_job.tags[0]
        elif isinstance(yml_job.tags, str):
            self.tag = yml_job.tags

        if self.type != yml_job.job_type:
            raise Exception('Selected job type differs to that of YML.')

        if (self.type == TS_JOB_TYPES[2] or self.type == TS_JOB_TYPES[5]) and self.package:
            self._bootstrap(package=self.package)
            self.release = yml_job.release
        elif self.type == TS_JOB_TYPES[3] and self.buildsys:
            self._bootstrap(build_system=self.buildsys)
        # for sequential jobs, tasks should be pushed to linked list
        # and output of previous task should be input for next task
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
            getattr(self, 'upstream_repo_url', ''),
            getattr(self, 'trans_file_ext', ''),
            getattr(self, 'pkg_upstream_name', ''),
            getattr(self, 'pkg_branch_map', {}),
            getattr(self, 'pkg_tp_engine', ''),
            getattr(self, 'pkg_tp_auth_usr', ''),
            getattr(self, 'pkg_tp_auth_token', ''),
            getattr(self, 'pkg_tp_url', ''),
            log_file
        )
        action_mapper.set_actions()
        # lets execute collected tasks
        try:
            action_mapper.execute_tasks()
        except Exception as e:
            job_manager.job_result = False
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
            job_manager.log_json = action_mapper.log
            action_mapper.clean_workspace()
            job_manager.mark_job_finish()
            time.sleep(4)
        # if not a dry run, save results is db
        if action_mapper.result and not getattr(self, 'DRY_RUN', None):
            self._save_result_in_db(action_mapper.result)
        if os.path.exists(log_file):
            os.unlink(log_file)
        return self.job_id
