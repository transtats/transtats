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

from collections import (namedtuple, OrderedDict)

http_methods = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS')
media_types = ('application/json', 'application/xml', 'application/octet-stream')

# based on https://cloud.memsource.com/web/docs/api
# please add, modify resource details here, and make entry in service-to-resource mappings and in services
resource_config_dict = {
    'AuthResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/auth/login
        ('/auth/login', {
            http_methods[1]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ProjectsResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/projects
        ('/projects', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ProjectResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}
        ('/projects/{project_slug}', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/workflowSteps
        ('/projects/{project_slug}/workflowSteps', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/providers
        ('/projects/{project_slug}/providers', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/termBases
        ('/projects/{project_slug}/termBases', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/transMemories
        ('/projects/{project_slug}/transMemories', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v2/projects/{projectUid}/analyses
        ('/projects/{project_slug}/analyses', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/importSettings
        ('/projects/{project_slug}/importSettings', {
            http_methods[0]: {
                'path_params': ('project_slug',),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'JobResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}
        ('/projects/{project_slug}/jobs/{job_id}', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/segments
        ('/projects/{project_slug}/jobs/{job_id}/segments', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/statusChanges
        ('/projects/{project_slug}/jobs/{job_id}/statusChanges', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/translationResources
        ('/projects/{project_slug}/jobs/{job_id}/translationResources', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/original
        ('/projects/{project_slug}/jobs/{job_id}/original', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[2],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/preview
        ('/projects/{project_slug}/jobs/{job_id}/preview', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[2],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/targetFile
        ('/projects/{project_slug}/jobs/{job_id}/targetFile', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[2],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/previewUrl
        ('/projects/{project_slug}/jobs/{job_id}/previewUrl', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/{jobUid}/workflowStep
        ('/projects/{project_slug}/jobs/{job_id}/workflowStep', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v2/projects/{projectUid}/jobs
        ('/projects/{project_slug}/jobs', {
            http_methods[0]: {
                'path_params': ('project_slug', ),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v2/projects/{projectUid}/jobs/{jobUid}/analyses
        ('/projects/{project_slug}/jobs/{job_id}/analyses', {
            http_methods[0]: {
                'path_params': ('project_slug', 'job_id'),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ImportSettingsResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/importSettings
        ('/importSettings', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/importSettings/{uid}
        ('/importSettings/{import_setting_uid}', {
            http_methods[0]: {
                'path_params': ('import_setting_uid', ),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'JobResourcePOST': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs
        ('/projects/{project_slug}/jobs', {
            http_methods[1]: {
                'path_params': ('project_slug', ),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[0],
            },
        }),
        # https://cloud.memsource.com/web/api2/v1/projects/{projectUid}/jobs/source
        ('/projects/{project_slug}/jobs/source', {
            http_methods[1]: {
                'path_params': ('project_slug', ),
                'query_params': None,
                'request_media_type': media_types[2],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ProjectTemplatesResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/projectTemplates
        ('/projectTemplates', {
            http_methods[0]: {
                'path_params': None,
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'ProjectTemplateResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v1/projectTemplates/{projectTemplateUid}
        ('/projectTemplates/{project_template_uid}', {
            http_methods[0]: {
                'path_params': ('project_template_uid', ),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
    'CreateProjectFromTemplateResource': OrderedDict([
        # https://cloud.memsource.com/web/api2/v2/projects/applyTemplate/{templateUid}
        ('/projects/applyTemplate/{template_uid}', {
            http_methods[1]: {
                'path_params': ('template_uid', ),
                'query_params': None,
                'request_media_type': media_types[0],
                'response_media_type': media_types[0],
            },
        }),
    ]),
}

resource = namedtuple('service', 'rest_resource mount_point http_method')
# service-to-resource mappings
request_token = resource('AuthResource', list(resource_config_dict['AuthResource'].keys())[0], http_methods[1])
list_projects = resource('ProjectsResource', list(resource_config_dict['ProjectsResource'].keys())[0], http_methods[0])
project_details = resource('ProjectResource', list(resource_config_dict['ProjectResource'].keys())[0], http_methods[0])
project_workflow_steps = resource(
    'ProjectResource', list(resource_config_dict['ProjectResource'].keys())[1], http_methods[0]
)
project_providers = resource(
    'ProjectResource', list(resource_config_dict['ProjectResource'].keys())[2], http_methods[0]
)
project_term_bases = resource(
    'ProjectResource', list(resource_config_dict['ProjectResource'].keys())[3], http_methods[0]
)
project_trans_memories = resource(
    'ProjectResource', list(resource_config_dict['ProjectResource'].keys())[4], http_methods[0]
)
project_analyses = resource(
    'ProjectResource', list(resource_config_dict['ProjectResource'].keys())[5], http_methods[0]
)
project_import_settings = resource(
    'ProjectResource', list(resource_config_dict['ProjectResource'].keys())[6], http_methods[0]
)
project_jobs = resource('JobResource', list(resource_config_dict['JobResource'].keys())[9], http_methods[0])
job_details = resource('JobResource', list(resource_config_dict['JobResource'].keys())[0], http_methods[0])
job_segments = resource('JobResource', list(resource_config_dict['JobResource'].keys())[1], http_methods[0])
job_status_changes = resource('JobResource', list(resource_config_dict['JobResource'].keys())[2], http_methods[0])
job_translation_resources = resource(
    'JobResource', list(resource_config_dict['JobResource'].keys())[3], http_methods[0]
)
job_original_file = resource('JobResource', list(resource_config_dict['JobResource'].keys())[4], http_methods[0])
job_preview_file = resource('JobResource', list(resource_config_dict['JobResource'].keys())[5], http_methods[0])
job_download_target_file = resource(
    'JobResource', list(resource_config_dict['JobResource'].keys())[6], http_methods[0]
)
job_pdf_preview = resource('JobResource', list(resource_config_dict['JobResource'].keys())[7], http_methods[0])
job_workflow_step = resource('JobResource', list(resource_config_dict['JobResource'].keys())[8], http_methods[0])
job_analyses = resource('JobResource', list(resource_config_dict['JobResource'].keys())[10], http_methods[0])
list_import_settings = resource(
    'ImportSettingsResource', list(resource_config_dict['ImportSettingsResource'].keys())[0], http_methods[0]
)
import_setting_details = resource(
    'ImportSettingsResource', list(resource_config_dict['ImportSettingsResource'].keys())[1], http_methods[0]
)
create_job = resource('JobResourcePOST', list(resource_config_dict['JobResourcePOST'].keys())[0], http_methods[1])
update_source = resource('JobResourcePOST', list(resource_config_dict['JobResourcePOST'].keys())[1], http_methods[1])
list_project_templates = resource(
    'ProjectTemplatesResource', list(resource_config_dict['ProjectTemplatesResource'].keys())[0], http_methods[0]
)
project_template_details = resource(
    'ProjectTemplateResource', list(resource_config_dict['ProjectTemplateResource'].keys())[0], http_methods[0]
)
create_project_from_template = resource(
    'CreateProjectFromTemplateResource',
    list(resource_config_dict['CreateProjectFromTemplateResource'].keys())[0], http_methods[1]
)

# Transtats Memsource support operates on resources listed here
resources = {
    'request_token': request_token,
    'list_projects': list_projects,
    'project_details': project_details,
    'project_workflow_steps': project_workflow_steps,
    'project_providers': project_providers,
    'project_term_bases': project_term_bases,
    'project_trans_memories': project_trans_memories,
    'project_analyses': project_analyses,
    'project_import_settings': project_import_settings,
    'project_jobs': project_jobs,
    'job_details': job_details,
    'job_segments': job_segments,
    'job_status_changes': job_status_changes,
    'job_translation_resources': job_translation_resources,
    'job_original_file': job_original_file,
    'job_preview_file': job_preview_file,
    'job_download_target_file': job_download_target_file,
    'job_pdf_preview': job_pdf_preview,
    'job_workflow_step': job_workflow_step,
    'job_analyses': job_analyses,
    'list_import_settings': list_import_settings,
    'import_setting_details': import_setting_details,
    'create_job': create_job,
    'update_source': update_source,
    'list_project_templates': list_project_templates,
    'project_template_details': project_template_details,
    'create_project_from_template': create_project_from_template,
}
