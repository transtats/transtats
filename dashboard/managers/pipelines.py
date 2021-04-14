# Copyright 2020 Red Hat, Inc.
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

import json

# django
from django.db.models import Case, Value, When
from django.utils import timezone

# dadhboard
from dashboard.constants import TRANSPLATFORM_ENGINES
from dashboard.managers.packages import PackagesManager
from dashboard.managers import BaseManager
from dashboard.models import CIPipeline, CIPlatformJob


__all__ = ['CIPipelineManager']


class CIPipelineManager(BaseManager):
    """
    Continuous Integration Pipeline Manager
    """

    package_manager = PackagesManager()

    def get_ci_pipelines(self, fields=None, packages=None, platforms=None,
                         releases=None, uuids=None, pipeline_ids=None):
        """
        fetch ci pipeline(s) from db
        :return: queryset
        """
        ci_pipelines = None
        required_params = fields if fields and isinstance(fields, (list, tuple)) \
            else ('ci_pipeline_uuid', 'ci_package', 'ci_platform', 'ci_release',
                  'ci_push_job_template', 'ci_pull_job_template', 'ci_project_web_url')
        kwargs = {}
        kwargs.update(dict(ci_pipeline_visibility=True))
        if packages:
            kwargs.update(dict(ci_package__in=packages))
        if platforms:
            kwargs.update(dict(ci_platform__in=platforms))
        if releases:
            kwargs.update(dict(ci_release__in=releases))
        if uuids:
            kwargs.update(dict(ci_pipeline_uuid__in=uuids))
        if pipeline_ids:
            kwargs.update(dict(ci_pipeline_id__in=pipeline_ids))

        try:
            ci_pipelines = CIPipeline.objects.only(*required_params).filter(**kwargs).all()
        except Exception as e:
            self.app_logger(
                'ERROR', "CI Pipelines could not be fetched, details: " + str(e)
            )
        return ci_pipelines

    def ci_platform_project_details(self, ci_platform, project_url):
        """
        Return CI Platform Project Details
            Assuming either project slug/uuid forms the last part of project_url
            Or, project_url is the project slug/uuid
        :param ci_platform: object
        :param project_url: str
        :return: json
        """
        if not ci_platform and not project_url:
            return '', {}
        project_uuid = project_url
        if ci_platform.engine_name == TRANSPLATFORM_ENGINES[4] and "/" in project_url:
            project_uuid = project_url.split("/")[-1:][0]
        response_dict = dict()
        kwargs = dict()
        kwargs.update(dict(no_cache_api=True))
        response_dict = self.api_resources.fetch_project_details(
            ci_platform.engine_name, ci_platform.api_url, project_uuid, **kwargs
        ) or response_dict
        return project_uuid, response_dict

    def refresh_ci_pipeline(self, pipeline_id, toggle_visibility=True):
        """
        Refresh a CI Pipeline
        :param pipeline_id: int
        :param toggle_visibility: boolean
        :return: boolean
        """
        ci_pipeline = self.get_ci_pipelines(pipeline_ids=[pipeline_id])
        if ci_pipeline:
            ci_pipeline = ci_pipeline.get()
            _, resp_dict = self.ci_platform_project_details(
                ci_pipeline.ci_platform, ci_pipeline.ci_project_web_url
            )
            if resp_dict:
                if 'errorCode' in resp_dict and 'errorDescription' in resp_dict:
                    project_uid = ci_pipeline.ci_project_web_url.split("/")[-1:][0]
                    if project_uid in resp_dict.get('errorDescription') and \
                            'not found' in resp_dict.get('errorDescription'):
                        if toggle_visibility and self.toggle_visibility(pipeline_id):
                            return True
                else:
                    pipeline_params = dict()
                    pipeline_params['ci_project_web_url'] = ci_pipeline.ci_project_web_url
                    pipeline_params['ci_project_details_json_str'] = json.dumps(resp_dict)
                    pipeline_params['ci_platform_jobs_json_str'] = json.dumps(
                        resp_dict.get('project_jobs', {})
                    )
                    pipeline_params['ci_pipeline_last_updated'] = timezone.now()
                    if self.save_ci_pipeline(pipeline_params):
                        return True
        return False

    def refresh_pkg_pipelines(self, package_name):
        """
        Refresh CI Pipelines that belong to a package
        :param package_name: str
        """
        pipelines = self.get_ci_pipelines(
            packages=self.package_manager.get_packages(pkgs=[package_name])
        )
        for pipeline in pipelines or []:
            self.refresh_ci_pipeline(pipeline_id=pipeline.ci_pipeline_id,
                                     toggle_visibility=False)

    def save_ci_pipeline(self, ci_pipeline):
        """
        Save CI Pipeline in db
        :param ci_pipeline: dict
        :return: boolean
        """
        if not ci_pipeline:
            return

        match_params = {}
        match_params.update(dict(
            ci_project_web_url=ci_pipeline.get('ci_project_web_url'))
        )

        try:
            ci_pipeline['ci_pipeline_visibility'] = True
            CIPipeline.objects.update_or_create(
                **match_params, defaults=ci_pipeline
            )
        except Exception as e:
            self.app_logger(
                'ERROR', "CI Pipeline could not be saved, details: " + str(e)
            )
        else:
            return True
        return False

    def toggle_visibility(self, pipeline_id):
        """
        Toggle CI Pipeline Visibility
        :param pipeline_id: int
        :return: boolean
        """
        filter_kwargs = {}
        filter_kwargs.update(dict(ci_pipeline_id=pipeline_id))
        try:
            CIPipeline.objects.filter(**filter_kwargs).update(
                ci_pipeline_visibility=Case(
                    When(ci_pipeline_visibility=True, then=Value(False)),
                    When(ci_pipeline_visibility=False, then=Value(True)),
                    default=Value(True)
                )
            )
        except Exception as e:
            self.app_logger(
                'ERROR', "CI Pipeline visibility could not be toggled, details: " + str(e)
            )
        else:
            return True
        return False

    def get_ci_platform_jobs(self, ci_pipelines=None):
        """
        fetch ci pipeline(s) from db
        :return: queryset
        """
        ci_platform_jobs = None
        kwargs = {}
        kwargs.update(dict(ci_platform_job_visibility=True))
        if ci_pipelines:
            kwargs.update(dict(ci_pipeline__in=ci_pipelines))

        try:
            ci_platform_jobs = CIPlatformJob.objects.filter(**kwargs).all()
        except Exception as e:
            self.app_logger(
                'ERROR', "CI Pipelines could not be fetched, details: " + str(e)
            )
        return ci_platform_jobs

    def save_ci_platform_job(self, platform_job):
        """
        Save CI Platform Job in db
        :param platform_job: dict
        :return: boolean
        """
        if not platform_job:
            return
        try:
            ci_platform_job = CIPlatformJob(**platform_job)
            ci_platform_job.save()
        except Exception as e:
            self.app_logger(
                'ERROR', "CI Platform Job could not be saved, details: " + str(e)
            )
        else:
            return True
        return False

    def ci_lang_job_map(self, pipelines):
        """
        Get CI Platform Target Language: Job UID map
        :param pipelines: Query Objects
        :return: dict
        """
        ci_lang_job_map = dict()
        if not pipelines:
            return ci_lang_job_map
        for pipeline in pipelines:
            if pipeline.ci_platform_jobs_json:
                ci_lang_job_map[pipeline.ci_pipeline_uuid] = dict()
                for job_detail in pipeline.ci_platform_jobs_json:
                    if job_detail.get('targetLang') and job_detail.get('uid'):
                        ci_lang_job_map[pipeline.ci_pipeline_uuid].update(
                            {job_detail['targetLang']: job_detail['uid']}
                        )
        return ci_lang_job_map
