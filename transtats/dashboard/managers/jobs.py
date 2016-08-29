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

from datetime import datetime

from .base import JobManager
from ..models.jobs import Jobs
from ..models.package import Packages
from ..models.syncstats import SyncStats
from ..models.transplatform import TransPlatform


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
            transplatforms = self.db_session.query(TransPlatform.engine_name, TransPlatform.api_url) \
                .filter_by(server_status=True).all()
        except Exception as e:
            self.db_session.rollback()
            self.log_json['Projects'].update(
                {str(datetime.now()): 'Fetch transplatform from db failed. Details: ' + str(e)}
            )
            self.job_result = False
        else:
            self.log_json['Projects'].update(
                {str(datetime.now()): str(len(transplatforms)) + ' translation platforms fetched from db.'}
            )
            for platform in transplatforms:
                rest_handle = self.rest_client(platform[0], platform[1])
                response_dict = rest_handle.process_request('list_projects')
                if response_dict and response_dict.get('json_content'):
                    # save projects json in db
                    try:
                        self.db_session.query(TransPlatform) \
                            .filter_by(api_url=platform[1]) \
                            .update({'projects_json': response_dict['json_content'],
                                     'projects_lastupdated': datetime.now()})
                        self.db_session.commit()
                    except Exception as e:
                        self.db_session.rollback()
                        self.log_json['Projects'].update(
                            {str(datetime.now()): 'Projects JSON for ' + platform[1] +
                                                  ' failed to get saved in db. Details: ' + str(e)}
                        )
                        self.job_result = False
                    else:
                        self.log_json['Projects'].update(
                            {str(datetime.now()): 'Projects JSON for ' + platform[1] + ' saved in db.'}
                        )
                        self.job_result = True
        return self.job_result

    def update_project_details(self):
        """
        Update project details json in db
        """
        self.log_json['Project-Details'] = {}
        try:
            project_urls = self.db_session.query(
                TransPlatform.engine_name, TransPlatform.api_url, Packages.transplatform_url
            ).filter(Packages.transplatform_slug == TransPlatform.platform_slug).all()
        except Exception as e:
            self.db_session.rollback()
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
                    transplatform_project_name = url.transplatform_url.split('/')[-1]
                    rest_handle = self.rest_client(url.engine_name, url.api_url)
                    response_dict = rest_handle.process_request('project_details',
                                                                transplatform_project_name)
                    if response_dict and response_dict.get('json_content'):
                        try:
                            self.db_session.query(Packages).filter_by(transplatform_url=url.transplatform_url) \
                                .update({'package_details_json': response_dict['json_content'],
                                         'details_json_lastupdated': datetime.now()})
                            self.db_session.commit()
                        except Exception as e:
                            self.db_session.rollback()
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

    def _parse_project_details_json(self, json_dict):
        """
        Parse project details json
        """
        return json_dict.get('id'), \
            [version.get('id') for version in json_dict.get('iterations', [])]

    def update_trans_stats(self):
        """
        Update translation stats for each project-version in db
        """
        self.log_json['Translation-Stats'] = {}
        try:
            project_details = self.db_session.query(
                TransPlatform.engine_name, TransPlatform.api_url, Packages.package_details_json
            ).filter(Packages.transplatform_slug == TransPlatform.platform_slug).all()
        except Exception as e:
            self.db_session.rollback()
            self.log_json['Translation-Stats'].update(
                {str(datetime.now()): 'Fetch Project Details from db failed. Details: ' + str(e)}
            )
            self.job_result = False
        else:
            self.log_json['Translation-Stats'].update(
                {str(datetime.now()): str(len(project_details)) + ' packages fetched from db.'}
            )
            for project_detail in project_details:
                rest_handle = self.rest_client(project_detail.engine_name, project_detail.api_url)
                project, versions = self._parse_project_details_json(project_detail.package_details_json)
                for version in versions:
                    response_dict = rest_handle.process_request(
                        'proj_trans_stats', project, version, extension="?detail=true&word=false"
                    )
                    if response_dict and response_dict.get('json_content'):
                        try:
                            existing_sync_stat = self.db_session.query(SyncStats). \
                                filter_by(package_name=project, project_version=version).first()
                            if not existing_sync_stat:
                                params = {}
                                params.update(dict(package_name=project))
                                params.update(dict(job_uuid=self.uuid))
                                params.update(dict(project_version=version))
                                params.update(dict(stats_raw_json=response_dict['json_content']))
                                params.update(dict(sync_iter_count=1))
                                params.update(dict(sync_visibility=True))
                                new_sync_stats = SyncStats(**params)
                                self.db_session.add(new_sync_stats)
                            else:
                                self.db_session.query(SyncStats).filter_by(
                                    package_name=project, project_version=version
                                ).update(
                                    {'job_uuid': self.uuid, 'stats_raw_json': response_dict['json_content'],
                                     'sync_iter_count': existing_sync_stat.sync_iter_count + 1}
                                )
                            self.db_session.query(Packages).filter_by(
                                transplatform_url=project_detail.api_url + "/project/view/" + project
                            ).update({'transtats_lastupdated': datetime.now()})
                            self.db_session.commit()
                        except Exception as e:
                            self.db_session.rollback()
                            self.log_json['Translation-Stats'].update(
                                {str(datetime.now()): 'Transtats JSON for project: ' + project + 'of version: ' +
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
            self.db_session.query(Jobs).filter_by(job_uuid=self.uuid).update(
                {'job_end_time': datetime.now(), 'job_log_json': self.log_json,
                 'job_result': self.job_result}
            )
            self.db_session.commit()
        except:
            self.db_session.rollback()
            return False
        else:
            return True
