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
import functools

# django
from django.db.models import Case, Value, When
from django.utils import timezone

# dashboard
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, RELSTREAM_SLUGS,
    PIPELINE_CONFIG_EVENTS, GIT_REPO_TYPE
)
from dashboard.managers.packages import PackagesManager
from dashboard.managers import BaseManager
from dashboard.models import CIPipeline, CIPlatformJob, PipelineConfig


__all__ = ['CIPipelineManager', 'PipelineConfigManager']


class CIPipelineManager(BaseManager):
    """Continuous Integration Pipeline Manager"""

    package_manager = PackagesManager()

    def get_ci_pipelines(self, fields=None, packages=None, platforms=None,
                         releases=None, uuids=None, pipeline_ids=None, track_trans=None):
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
        if track_trans:
            kwargs.update(dict(ci_release__track_trans_flag=True))

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
        response_dict = {}
        kwargs = {}
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
                    pipeline_params = {}
                    pipeline_params['ci_pipeline_uuid'] = ci_pipeline.ci_pipeline_uuid
                    pipeline_params['ci_project_web_url'] = ci_pipeline.ci_project_web_url
                    pipeline_params['ci_project_details_json_str'] = json.dumps(resp_dict)
                    pipeline_params['ci_platform_jobs_json_str'] = json.dumps(
                        resp_dict.get('project_jobs', {})
                    )
                    pipeline_params['ci_pipeline_last_updated'] = timezone.now()
                    if self.update_ci_pipeline(pipeline_params):
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

    def create_ci_pipeline(self, ci_pipeline_params: dict, get_obj: bool = False) -> bool or CIPipeline:
        """
        Creates CI Pipeline in db
        :param ci_pipeline_params: dict
        :param get_obj: bool
        :return: boolean
        """
        if not ci_pipeline_params:
            return False

        try:
            ci_pipeline_params['ci_pipeline_visibility'] = True
            new_pipeline = CIPipeline(**ci_pipeline_params)
            new_pipeline.save()
            if get_obj:
                return new_pipeline
        except Exception as e:
            self.app_logger(
                'ERROR', "CI Pipeline could not be created, details: " + str(e)
            )
            return False
        else:
            return True

    def update_ci_pipeline(self, ci_pipeline_params: dict) -> bool:
        """
        Updates CI Pipeline in db
        :param ci_pipeline_params: dict
        :return: boolean
        """
        if not ci_pipeline_params:
            return False

        match_params = {}
        match_params.update(dict(ci_pipeline_uuid=ci_pipeline_params['ci_pipeline_uuid']))
        match_params.update(dict(ci_project_web_url=ci_pipeline_params['ci_project_web_url']))

        try:
            CIPipeline.objects.filter(**match_params).update(**ci_pipeline_params)
        except Exception as e:
            self.app_logger('ERROR', "CI Pipeline could not be updated, details: " + str(e))
            return False
        else:
            return True

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

    def ci_lang_job_map(self, pipelines, workflow_step='default'):
        """
        Get CI Platform Target Language: Job UID map
        :param pipelines: Query Objects
        :param workflow_step: Str
        :return: dict
        """
        ci_lang_job_map = {}
        if not pipelines:
            return ci_lang_job_map
        for pipeline in pipelines:
            if pipeline.ci_platform_jobs_json:
                ci_lang_job_map[pipeline.ci_pipeline_uuid] = {}
                for job_detail in pipeline.ci_platform_jobs_json:
                    if job_detail.get('targetLang') and job_detail.get('uid') and job_detail.get('filename'):

                        if not job_detail.get('workflowStep'):
                            ci_lang_job_map[pipeline.ci_pipeline_uuid].update(
                                {job_detail['uid']: (job_detail['targetLang'], job_detail['filename'])}
                            )
                        elif workflow_step == 'default' and job_detail.get('workflowLevel') == 1:
                            ci_lang_job_map[pipeline.ci_pipeline_uuid].update(
                                {job_detail['uid']: (job_detail['targetLang'], job_detail['filename'])}
                            )
                        elif job_detail.get('workflowStep') and \
                                job_detail.get('workflowStep').get('name') == workflow_step:
                            ci_lang_job_map[pipeline.ci_pipeline_uuid].update(
                                {job_detail['uid']: (job_detail['targetLang'], job_detail['filename'])}
                            )

        return ci_lang_job_map

    def get_ci_platform_workflow_steps(self, pipeline_uuid):
        """
        Get CI Platform Workflow Step
        :param pipeline_uuid: str
        :return: list
        """

        def unique(sequence):
            seen = set()
            return [x for x in sequence if not (x in seen or seen.add(x))]

        workflow_steps = []
        if not pipeline_uuid:
            return workflow_steps
        ci_pipeline = self.get_ci_pipelines(uuids=[pipeline_uuid])
        if not ci_pipeline:
            return workflow_steps
        ci_pipeline = ci_pipeline.get()
        return unique([p_job['workflowStep'].get('name', 'default') if p_job.get('workflowStep')
                       else 'default' for p_job in ci_pipeline.ci_platform_jobs_json])


class PipelineConfigManager(CIPipelineManager):
    """Pipeline Configurations Manager"""

    def get_pipeline_configs(self, fields=None, ci_pipelines=None, pipeline_config_ids=None):
        """
        fetch ci pipeline(s) from db
        :return: queryset
        """
        pipeline_configs = None
        required_params = fields if fields and isinstance(fields, (list, tuple)) \
            else ('pipeline_config_id', 'ci_pipeline', 'pipeline_config_event', 'pipeline_config_repo_branches',
                  'pipeline_config_active', 'pipeline_config_created_on', 'pipeline_config_updated_on',
                  'pipeline_config_last_accessed', 'pipeline_config_created_by')
        kwargs = {}
        if ci_pipelines:
            kwargs.update(dict(ci_pipeline__in=ci_pipelines))
        if pipeline_config_ids:
            kwargs.update(dict(pipeline_config_id__in=pipeline_config_ids))
        try:
            pipeline_configs = PipelineConfig.objects.only(*required_params).filter(**kwargs).all()
        except Exception as e:
            self.app_logger(
                'ERROR', "Pipeline Configs could not be fetched, details: " + str(e)
            )
        return pipeline_configs

    def save_pipeline_config(self, config_params):
        """
        Save Pipeline Config in db
        :param config_params: dict
        :return: boolean
        """
        if not config_params:
            return
        try:
            pipeline_config = PipelineConfig(**config_params)
            pipeline_config.save()
        except Exception as e:
            self.app_logger(
                'ERROR', "Pipeline Config could not be saved, details: " + str(e)
            )
        else:
            return True
        return False

    def _pipeline_config_html_form(self, pipeline, action, tenant):
        """
        Pipeline Configuration HTML form fields
        :param pipeline: Pipeline Object
        :param action: str
        :param tenant: str or None
        :return: dict
        """

        upstream_repo_type = GIT_REPO_TYPE[0]
        if pipeline.ci_package.upstream_l10n_url:
            upstream_repo_type = GIT_REPO_TYPE[1]

        upstream_repo_branches = self.package_manager.git_branches(
            package_name=pipeline.ci_package.package_name,
            repo_type=upstream_repo_type
        )

        repo_branches = self.package_manager.git_branches(
            package_name=pipeline.ci_package.package_name,
            repo_type=pipeline.ci_package.platform_slug.engine_name
        )

        if pipeline.ci_pipeline_default_branch and \
                pipeline.ci_pipeline_default_branch in repo_branches:
            repo_branches = [pipeline.ci_pipeline_default_branch]

        def _format_val(field_id, value_str):
            return "<strong id={}>{}</strong>".format(field_id, str(value_str))

        def _format_choices(field_id, values):
            html_select = ""
            html_select += "<select name='{}' id='{}'>".format(field_id, field_id)
            for value in values:
                html_select += "<option value='{}'>{}</option>".format(value, value)
            html_select += "</select>"
            return html_select

        def _format_checkboxes(field_id, values):
            html_select = ""
            counter = 0
            for value in values:
                counter += 1
                html_select += "<label class='checkbox-inline'>" \
                               "<input id='{}' class='checkbox-inline' type='checkbox' value='{}' {}>" \
                               "{}</label>".format(field_id + str(counter), value, "checked", value)
            return html_select

        def _choose_checkboxes_or_dropdown(field_id, values):
            if tenant == RELSTREAM_SLUGS[3]:
                return _format_checkboxes(field_id, values)
            return _format_choices(field_id, values)

        prepend_branch_field = "<input id='prependBranch' name='prependBranch' type='checkbox'>"
        if tenant == RELSTREAM_SLUGS[3]:
            prepend_branch_field = "<input id='prependBranch' name='prependBranch' type='checkbox' checked>"

        prepend_package_field = "<input id='prependPackage' name='prependPackage' type='checkbox'>"
        if tenant == RELSTREAM_SLUGS[4]:
            prepend_package_field = "<input id='prependPackage' name='prependPackage' type='checkbox' checked>"

        upload_update_field = "<input id='uploadUpdate' name='uploadUpdate' type='checkbox'>"
        if action == PIPELINE_CONFIG_EVENTS[2]:
            upload_update_field = "<input id='uploadUpdate' name='uploadUpdate' type='checkbox' checked>"

        filter_dir = ''
        file_filter_ext = pipeline.ci_package.translation_file_ext or ''
        if file_filter_ext:
            file_filter_ext = file_filter_ext.upper()

        upload_pre_hook, copy_div_val = '', ''
        if tenant == RELSTREAM_SLUGS[4]:
            file_filter_ext, filter_dir = 'JSON', 'locales'
            copy_div_val = 'src/locales'
            upload_pre_hook = 'copy_template_for_target_langs'

        key_val_map = {
            "ci_pipeline": _format_val("ciPipeline", pipeline.ci_pipeline_uuid),
            "package": _format_val("packageName", pipeline.ci_package.package_name),
            "clone.type": _format_val("cloneType", upstream_repo_type),
            "clone.branch": _format_choices("repoCloneBranch", upstream_repo_branches),
            "clone.recursive": "<input type='checkbox' id='cloneRecursive' name='cloneRecursive'>",
            "filter.domain": "<input id='filterDomain' type='text' value='{}'>".format(
                pipeline.ci_package.package_name),
            "filter.ext": "<input id='filterExt' type='text' value='{}'>".format(file_filter_ext),
            "filter.dir": "<input id='filterDir' type='text' value='{}'>".format(filter_dir),
            "download.target_langs": _format_checkboxes(
                'downloadTargetLangs', pipeline.ci_project_details_json.get("targetLangs", [])),
            "download.type": _format_val("downloadType", pipeline.ci_package.platform_slug.engine_name),
            "download.branch": _choose_checkboxes_or_dropdown("downloadRepoBranch", repo_branches),
            "download.workflow_step": _format_choices(
                "workflowStep", self.get_ci_platform_workflow_steps(pipeline.ci_pipeline_uuid)
            ),
            "download.prepend_branch": prepend_branch_field,
            "download.prepend_package": prepend_package_field,
            "upload.type": _format_val("uploadType", pipeline.ci_package.platform_slug.engine_name),
            "upload.branch": _choose_checkboxes_or_dropdown("uploadRepoBranch", repo_branches),
            "upload.target_langs": _format_checkboxes(
                'uploadTargetLangs', pipeline.ci_project_details_json.get("targetLangs", [])),
            "upload.prehook": "<input id='preHook' type='text' value='{}'>".format(upload_pre_hook),
            "upload.import_settings": "<input id='importSettings' type='text' value='project'>",
            "copy.dir": f"<input id='copyDir' type='text' value='{copy_div_val}'>",
            "upload.update": upload_update_field,
            "pullrequest.type": _format_val("pullrequestType", upstream_repo_type),
            "pullrequest.branch": _format_choices("repoPullRequestBranch", upstream_repo_branches),
            "upload.prepend_branch": prepend_branch_field,
            "upload.prepend_package": prepend_package_field,
        }
        return key_val_map

    @staticmethod
    def __true_false_type(str_val):
        type_conv_map = {
            "true": True,
            "True": True,
            "false": False,
            "False": False
        }
        return type_conv_map.get(str_val)

    def _pipeline_config_values(self, config_values):
        """
        Pipeline Configuration YAML values
        :param config_values: dict
        :return: dict
        """

        key_val_map = {
            "ci_pipeline": config_values.get('ciPipeline', ''),
            "package": config_values.get('package', ''),
            "clone.type": config_values.get('cloneType', ''),
            "clone.branch": config_values.get('cloneBranch', ''),
            "clone.recursive": self.__true_false_type(config_values.get('cloneRecursive', '')),
            "filter.domain": config_values.get('filterDomain', ''),
            "filter.ext": config_values.get('filterExt', ''),
            "filter.dir": config_values.get('filterDir', ''),
            "download.target_langs": config_values.get('downloadTargetLangs', '').split(','),
            "download.type": config_values.get('downloadType', ''),
            "download.branch": config_values.get('downloadBranch', ''),
            "download.workflow_step": config_values.get('downloadWorkflowStep', ''),
            "download.prepend_branch": self.__true_false_type(config_values.get('downloadPrependBranch', '')),
            "download.prepend_package": self.__true_false_type(config_values.get('downloadPrependPackage', '')),
            "upload.type": config_values.get('uploadType', ''),
            "upload.branch": config_values.get('uploadBranch', ''),
            "upload.target_langs": config_values.get('uploadTargetLangs', '').split(','),
            "upload.prehook": config_values.get('uploadPreHook', ''),
            "upload.import_settings": config_values.get('uploadImportSettings', ''),
            "upload.update": self.__true_false_type(config_values.get('uploadUpdate', '')),
            "upload.prepend_branch": self.__true_false_type(config_values.get('uploadPrependBranch', '')),
            "upload.prepend_package": self.__true_false_type(config_values.get('uploadPrependPackage', '')),
            "copy.dir": config_values.get('copyDir', ''),
            "pullrequest.type": config_values.get("pullrequestType", ''),
            "pullrequest.branch": config_values.get("repoPullRequestBranch", ''),
        }
        return key_val_map

    @staticmethod
    def get_job_action_template(pipeline, action):
        job_action_map = {
            PIPELINE_CONFIG_EVENTS[0]: pipeline.ci_push_job_template,
            PIPELINE_CONFIG_EVENTS[1]: pipeline.ci_pull_job_template,
            PIPELINE_CONFIG_EVENTS[2]: pipeline.ci_push_job_template
        }
        return job_action_map.get(action)

    def format_pipeline_config(self, pipeline, action, output_format=None, tenant=None, **kwargs):
        """
        Formats Job Template for the Pipeline Configurations
        :param pipeline: Pipeline Object
        :param action: str
        :param output_format: str (html_form or values)
        :param tenant: str or None
        :return: dict
        """
        key_val_map = {}
        if not pipeline and not action:
            return key_val_map

        respective_job_template_json = self.get_job_action_template(pipeline, action).job_template_json or {}
        pipeline_config = respective_job_template_json.copy()

        if output_format and output_format == 'html_form':
            key_val_map = self._pipeline_config_html_form(
                pipeline=pipeline, action=action, tenant=tenant
            )
        if output_format and output_format == 'values':
            key_val_map = self._pipeline_config_values(config_values=kwargs)

        def _traverse_steps(task_steps):
            counter = 0
            for t_step in task_steps:
                for step_cmd, step_params in t_step.items():
                    inner_counter = 0
                    for step_param in step_params:
                        for param, value in step_param.items():
                            niddle = "{}.{}".format(step_cmd, param)
                            if niddle in key_val_map:
                                task_steps[counter][step_cmd][inner_counter][param] = \
                                    key_val_map[niddle]
                        inner_counter = inner_counter + 1
                counter = counter + 1
            return task_steps

        # lets parse job_template and fill values
        for k, v in pipeline_config.items():
            if isinstance(v, dict):
                for p, q in v.items():
                    if p in key_val_map:
                        pipeline_config[k][p] = key_val_map[p]
                    if p == "tasks":
                        pipeline_config[k][p] = _traverse_steps(q)
        return pipeline_config

    def process_save_pipeline_config(self, *args, **kwargs):
        """
        Process data and save pipeline configuration
        :param args: list
        :param args: dict
        :return: boolean
        """
        repo_type, repo_branch, pipeline_branches, target_langs, u_email = args

        copy_config = kwargs.get('chkCopyConfig')
        pipeline_uuid = kwargs.get('ciPipeline', '')
        pipeline_action = kwargs.get('pipelineAction', '')
        ci_pipeline = self.get_ci_pipelines(uuids=[pipeline_uuid]).get()

        def _save_pipeline_config(*params):
            pc_kwargs = {}
            pc_kwargs.update(dict(ci_pipeline=params[0]))
            pc_kwargs.update(dict(pipeline_config_event=params[1]))
            pc_kwargs.update(dict(pipeline_config_active=True))
            pc_kwargs.update(dict(pipeline_config_json_str=params[2]))
            pc_kwargs.update(dict(pipeline_config_repo_branches=params[3]))
            if target_langs and isinstance(target_langs, str):
                pc_kwargs.update(dict(pipeline_config_target_lang=target_langs.split(',')))
            pc_kwargs.update(dict(pipeline_config_created_on=timezone.now()))
            pc_kwargs.update(dict(pipeline_config_created_by=params[4]))
            pc_kwargs.update(dict(pipeline_config_is_default=kwargs.get("is_default", False)))
            return self.save_pipeline_config(pc_kwargs)

        if not self.__true_false_type(copy_config):
            pipeline_config = self.format_pipeline_config(pipeline=ci_pipeline, action=pipeline_action,
                                                          output_format='values', **kwargs)
            return _save_pipeline_config(
                ci_pipeline, pipeline_action, json.dumps(pipeline_config), pipeline_branches, u_email
            )
        else:
            save_results = []
            for action in PIPELINE_CONFIG_EVENTS:
                kwargs['downloadType'] = repo_type
                kwargs['downloadBranch'] = repo_branch
                kwargs['downloadTargetLangs'] = target_langs
                kwargs['uploadType'] = repo_type
                kwargs['uploadBranch'] = repo_branch
                kwargs['uploadTargetLangs'] = target_langs

                if action == PIPELINE_CONFIG_EVENTS[1]:
                    workflow_steps = self.get_ci_platform_workflow_steps(
                        pipeline_uuid=ci_pipeline.ci_pipeline_uuid
                    )
                    kwargs['downloadWorkflowStep'] = workflow_steps[0] \
                        if isinstance(workflow_steps, list) and len(workflow_steps) >= 1 else 'Translation'
                if action == PIPELINE_CONFIG_EVENTS[2]:
                    kwargs['uploadUpdate'] = 'true'

                pipeline_config = self.format_pipeline_config(pipeline=ci_pipeline, action=action,
                                                              output_format='values', **kwargs)
                save_results.append(_save_pipeline_config(
                    ci_pipeline, action, json.dumps(pipeline_config), pipeline_branches, u_email
                ))
            return functools.reduce(lambda a, b: a and b, save_results) if save_results else False

    def toggle_pipeline_configuration(self, pipeline_config_id):
        """
        Deactivate or Activate Pipeline Configuration
        :param pipeline_config_id: number
        :return: boolean
        """
        if not pipeline_config_id:
            return False
        filter_kwargs = {}
        filter_kwargs.update(dict(pipeline_config_id=pipeline_config_id))
        try:
            PipelineConfig.objects.filter(**filter_kwargs).update(
                pipeline_config_active=Case(
                    When(pipeline_config_active=True, then=Value(False)),
                    When(pipeline_config_active=False, then=Value(True)),
                    default=Value(False)
                )
            )
        except Exception as e:
            self.app_logger(
                'ERROR', "Pipeline Configuration could not be toggled, details: " + str(e)
            )
        else:
            return True
        return False

    def delete_pipeline_configuration(self, pipeline_config_id):
        """
        Delete Pipeline Configuration
        :param pipeline_config_id: number
        :return: boolean
        """
        if not pipeline_config_id:
            return False
        filter_kwargs = {}
        filter_kwargs.update(dict(pipeline_config_id=pipeline_config_id))
        try:
            PipelineConfig.objects.filter(**filter_kwargs).delete()
        except Exception as e:
            self.app_logger(
                'ERROR', "Pipeline Configuration could not be deleted, details: " + str(e)
            )
        else:
            return True
        return False
