# Copyright 2023 Red Hat, Inc.
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

import re
import os
from collections import OrderedDict

from dashboard.constants import TRANSPLATFORM_ENGINES
from dashboard.jobs_framework.mixins import JobHooksMixin
from dashboard.jobs_framework import JobCommandBase


class Upload(JobHooksMixin, JobCommandBase):
    """Handles all operations for UPLOAD Command"""

    @staticmethod
    def _collect_files(t_files, file_ext, target_langs, podir=False):
        collected_files = {}

        def __file_filter_helper(z_file, z_lang):
            z_file_lang = z_file.split(os.sep)[-1].replace('.{}'.format(file_ext), '')
            if podir:
                z_file_lang = z_file.split(os.sep)[-2]
            return z_lang in z_file_lang or z_lang in z_file_lang.lower()

        for x_lang in target_langs:
            for x_file in t_files:
                if __file_filter_helper(x_file, x_lang):
                    collected_files[x_lang] = x_file

        return collected_files

    def push_files(self, input, kwargs):
        """
        Push translations to a Platform
            - Preference to CI Platform over translation
        """
        task_subject = "Push translations files"
        task_log = OrderedDict()

        # locate and execute pre-hook function
        if kwargs.get('prehook'):
            pre_hook = kwargs['prehook']
            pre_hook_fn = getattr(self, pre_hook, None)
            if pre_hook_fn:
                pre_hook_fn(input, self._log_task, task_log)

        job_post_resp = OrderedDict()
        platform_project = input.get('ci_project_uid') or input.get('package')

        file_ext = 'po'
        if input.get('file_ext'):
            file_ext = input['file_ext'].lower()
        if kwargs.get('ext'):
            file_ext = kwargs['ext'].lower()
        ci_lang_job_map = input.get('ci_lang_job_map', {})

        target_langs = []
        if kwargs.get('target_langs'):
            target_langs = self.language_formatter.format_target_langs(langs=kwargs['target_langs'])

        if target_langs and input.get('ci_pipeline_uuid') and input.get('ci_target_langs'):
            if not set(target_langs).issubset(set(input['ci_target_langs'])):
                raise Exception("Provided target langs do NOT belong to the CI Pipeline.")

        # filter files to be uploaded
        collected_files = self._collect_files(
            input.get('trans_files', []), file_ext, target_langs, podir=input.get('podir')
        )

        if collected_files and len(collected_files) > 0:
            task_log.update(self._log_task(
                input['log_f'], task_subject, str(collected_files),
                text_prefix='%s %s files collected' % (len(collected_files), file_ext.upper())
            ))

            # let's try pushing the collected files, one by one
            for lang, file_path in collected_files.items():
                api_kwargs = {}
                with open(file_path, 'rb') as f:
                    api_kwargs['data'] = f.read()

                file_path_except_name, file_name = os.path.split(file_path)
                if input.get('podir'):
                    file_ext = file_path.split(os.sep)[-1].split('.')[1]
                    file_name = "{}.{}".format(file_path.split(os.sep)[-2], file_ext)
                platform_engine = input.get('pkg_ci_engine') or input.get('pkg_tp_engine')
                platform_api_url = input.get('pkg_ci_url') or input.get('pkg_tp_url')
                platform_auth_user = input.get('pkg_ci_auth_usr') or input.get('pkg_tp_auth_usr')
                platform_auth_token = input.get('pkg_ci_auth_token') or input.get('pkg_tp_auth_token')

                if kwargs.get('update') and input.get('ci_lang_job_map') \
                        and lang not in {i[0] for i in ci_lang_job_map.values()}:
                    raise Exception("Job ID NOT found for lang: {}. Please refresh the pipeline.".format(lang))

                api_kwargs['headers'] = {}
                api_kwargs['auth_user'] = platform_auth_user
                api_kwargs['auth_token'] = platform_auth_token

                if platform_engine == TRANSPLATFORM_ENGINES[4]:
                    memsource_kwargs = {}
                    if kwargs.get('update'):
                        # narrow down ci_lang_job_map by filter
                        if kwargs.get('prepend_branch') and input.get('repo_branch'):
                            ci_lang_job_map = {k: v for k, v in ci_lang_job_map.items() for x in v if
                                               input['repo_branch'] in x}
                        elif not kwargs.get('prepend_branch'):
                            ci_lang_job_map = {k: v for k, v in ci_lang_job_map.items()
                                               if self.double_underscore_delimiter not in v[1]}
                        # lang related jobs
                        job_uid = [k for k, v in ci_lang_job_map.items() for x in v if lang in x]
                        if isinstance(job_uid, list) and len(job_uid) > 0:
                            job_uid = job_uid[0]

                        if not job_uid:
                            raise Exception("Job ID NOT found. Please refresh the pipeline.")
                        memsource_kwargs.update(dict(jobs=[{"uid": job_uid}]))
                        memsource_kwargs.update(dict(preTranslate="false"))
                    else:
                        memsource_kwargs.update(dict(targetLangs=[lang]))
                        if isinstance(kwargs.get('import_settings'), str):
                            if kwargs.get('import_settings', '') == 'project':
                                task_log.update(self._log_task(
                                    input['log_f'], task_subject, '[INFO] Using Project Import Settings.'
                                ))
                                memsource_kwargs.update(dict(useProjectFileImportSettings="true"))
                            elif re.match(r"^[a-zA-Z0-9]{22}$", kwargs.get('import_settings', '')):
                                import_setting_uid = kwargs['import_settings']
                                import_setting_resp = self.api_resources.import_setting_details(
                                    platform_engine, platform_api_url, import_setting_uid, **api_kwargs
                                )
                                if not import_setting_resp:
                                    raise Exception("Invalid ImportSetting: {}".format(import_setting_uid))

                                if import_setting_resp.get('uid') == import_setting_uid:
                                    task_log.update(self._log_task(
                                        input['log_f'], task_subject, '[INFO] Using Import Settings: {} - {}'.format(
                                            import_setting_resp.get('name', ''), import_setting_resp.get('uid', '')
                                        )
                                    ))
                                    memsource_kwargs.update(dict(importSettings=dict(uid=import_setting_uid)))

                    if input.get('repo_branch') and kwargs.get('prepend_branch'):
                        new_filename = "{}{}{}".format(input.get('repo_branch'),
                                                       self.double_underscore_delimiter,
                                                       file_name)
                        new_file_path = os.path.join(file_path_except_name, new_filename)
                        os.rename(file_path, new_file_path)
                        file_name, file_path = new_filename, new_file_path

                    if kwargs.get('prepend_package'):
                        new_filename = "{}{}{}".format(input.get('package'),
                                                       self.double_underscore_delimiter,
                                                       file_name)
                        new_file_path = os.path.join(file_path_except_name, new_filename)
                        os.rename(file_path, new_file_path)
                        file_name, file_path = new_filename, new_file_path

                    api_kwargs['headers']["Memsource"] = str(memsource_kwargs)
                    api_kwargs['headers']["Content-Disposition"] = 'attachment; filename="{}"'.format(file_name)

                try:
                    upload_status, upload_resp = self.api_resources.update_source(
                        platform_engine, platform_api_url, platform_project, **api_kwargs) \
                        if kwargs.get('update') else self.api_resources.push_translations(
                        platform_engine, platform_api_url, platform_project, **api_kwargs)
                except Exception as e:
                    task_log.update(self._log_task(
                        input['log_f'], task_subject,
                        'Something went wrong in uploading: %s' % str(e)
                    ))
                else:
                    t_prefix = '{} uploaded for {}'.format(file_name, lang) if upload_status \
                        else 'Could not upload: {} for {}'.format(file_name, lang)
                    task_log.update(self._log_task(
                        input['log_f'], task_subject, str(upload_resp), text_prefix=t_prefix
                    ))
                    upload_resp.update(dict(project=dict(uid=platform_project)))
                    if upload_status:
                        job_post_resp[lang] = upload_resp
                    else:
                        raise Exception(
                            "Push failed for lang {}. {} response: {}".format(
                                lang, platform_engine.title(), upload_resp
                            )
                        )
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, '[WARN] Files could not be collected to upload. '
                                              'Filename should have either locale or template.'
            ))

        return {'push_files_resp': {platform_project: job_post_resp}}, {task_subject: task_log}

    def submit_translations(self, input, kwargs):
        """
        Submit finished translations (downloaded from a CI Platform)
            to a translation platform or an upstream
        """
        task_subject = "Submit translations"
        task_log = OrderedDict()

        trans_submit_resp = OrderedDict()
        platform_project = input.get('package')

        if not kwargs.get('type'):
            raise Exception("Please provide REPO_TYPE.")
        repo_type = kwargs.get('type')

        if not kwargs.get('branch') and not input.get('repo_branch'):
            raise Exception("Please provide REPO_BRANCH.")
        repo_branch = kwargs.get('branch') or input.get('repo_branch')

        file_ext = 'po'
        if kwargs.get('ext'):
            file_ext = kwargs['ext'].lower()

        target_langs = []
        if input.get('target_langs'):
            target_langs = self.language_formatter.format_target_langs(langs=input['target_langs'])

        if target_langs and input.get('ci_pipeline_uuid') and input.get('ci_target_langs'):
            if not set(target_langs).issubset(set(input['ci_target_langs'])):
                raise Exception("Provided target langs do NOT belong to CI Pipeline.")

        # filter files to be submitted
        collected_files = self._collect_files(
            input.get('trans_files', []), file_ext, target_langs
        )

        if collected_files and len(collected_files) > 0:
            task_log.update(self._log_task(
                input['log_f'], task_subject, str(collected_files),
                text_prefix='%s %s files collected' % (len(collected_files), file_ext.upper())
            ))

            # let's try uploading the collected files, one by one
            for lang, file_path in collected_files.items():
                api_kwargs = {}

                file_name = file_path.split(os.sep)[-1]

                # where repo_type belongs to translation platform(s)
                # todo: extend support for scm repositories
                if repo_type in TRANSPLATFORM_ENGINES:

                    api_kwargs['data'], api_kwargs['files'] = {}, {}
                    platform_engine, platform_api_url, platform_auth_user, platform_auth_token = \
                        input.get('pkg_tp_engine'), input.get('pkg_tp_url'), \
                        input.get('pkg_tp_auth_usr'), input.get('pkg_tp_auth_token')

                    # format lang zh_cn to zh_CN, alias_zh could be used for weblate
                    lang = self.language_formatter.format_locale(lang, alias_zh=kwargs.get('alias_zh', False))

                    with open(file_path, 'rb') as f:
                        api_kwargs['files'] = dict(file=f.read())

                    if platform_engine == TRANSPLATFORM_ENGINES[3]:
                        # multipart/form upload
                        api_kwargs['data']['overwrite'] = "yes"
                        api_kwargs['data']['conflicts'] = kwargs.get('conflicts', 'replace-translated')
                        api_kwargs['data']['method'] = kwargs.get('method', 'translate')

                    api_kwargs['auth_user'] = platform_auth_user
                    api_kwargs['auth_token'] = platform_auth_token

                    try:
                        submit_status, submit_resp = self.api_resources.push_translations(
                            platform_engine, platform_api_url, platform_project,
                            repo_branch, lang, **api_kwargs
                        )
                    except Exception as e:
                        task_log.update(self._log_task(
                            input['log_f'], task_subject,
                            'Something went wrong in uploading: %s' % str(e)
                        ))
                    else:
                        t_prefix = '{} uploaded for {}'.format(file_name, lang) if submit_status \
                            else 'Could not upload: {} for {}'.format(file_name, lang)
                        task_log.update(self._log_task(
                            input['log_f'], task_subject, str(submit_resp), text_prefix=t_prefix
                        ))
                        if submit_status:
                            trans_submit_resp[lang] = submit_resp
                        else:
                            raise Exception(
                                "Submit failed for lang {} of branch {}. {} response: {} ".format(
                                    lang, repo_branch, platform_engine.title(), submit_resp)
                            )

        return {'submit_translations': trans_submit_resp}, {task_subject: task_log}
