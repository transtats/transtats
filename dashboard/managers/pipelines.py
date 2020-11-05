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

# dadhboard
from dashboard.constants import TRANSPLATFORM_ENGINES
from dashboard.managers import BaseManager
from dashboard.models import CIPipeline


class CIPipelineManager(BaseManager):
    """
    Continuous Integration Pipeline Manager
    """

    def get_ci_pipelines(self, fields=None, packages=None, platforms=None, releases=None):
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
        response_dict = self.api_resources.fetch_project_details(
            ci_platform.engine_name, ci_platform.api_url, project_uuid
        ) or response_dict
        return project_uuid, response_dict

    def save_ci_pipeline(self, ci_pipeline):
        """
        Save CI Pipeline in db
        :param ci_pipeline: dict
        :return: boolean
        """
        if not ci_pipeline:
            return
        try:
            pipeline = CIPipeline(**ci_pipeline)
            pipeline.save()
        except Exception as e:
            self.app_logger(
                'ERROR', "CI Pipeline could not be saved, details: " + str(e)
            )
        else:
            return True
        return False
