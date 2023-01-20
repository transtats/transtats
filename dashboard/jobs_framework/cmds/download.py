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

import os
import polib
from requests.auth import HTTPBasicAuth
import requests
from collections import OrderedDict

from dashboard.constants import (
    BUILD_SYSTEMS, TRANSPLATFORM_ENGINES, BRANCH_MAPPING_KEYS, API_TOKEN_PREFIX
)
from dashboard.jobs_framework.mixins import LanguageFormatterMixin
from dashboard.jobs_framework import JobCommandBase


class Download(LanguageFormatterMixin, JobCommandBase):
    """Handles all operations for DOWNLOAD Command"""

    def _download_file(self, file_link, file_path=None, headers=None, auth=None):
        req = requests.get(file_link, headers=headers, auth=auth)
        if req.status_code == 404:
            return '404'
        if not file_path:
            file_path = self.sandbox_path + file_link.split('/')[-1]
        try:
            with open(file_path, 'wb') as f:
                f.write(req.content)
                return file_path
        except FileNotFoundError:
            return ''
        except Exception:
            return ''

    def srpm(self, input, kwargs):

        task_subject = "Download SRPM"
        task_log = OrderedDict()

        builds = input.get('builds')
        task = input.get('task')

        pkgs_download_server_url = ''
        srpm_downloaded_path, srpm_download_url = '', ''
        if input.get('build_system', '') == BUILD_SYSTEMS[0]:
            pkgs_download_server_url = 'http://download.eng.bos.redhat.com/brewroot'
        elif input.get('build_system', '') == BUILD_SYSTEMS[1]:
            pkgs_download_server_url = 'https://kojipkgs.fedoraproject.org'

        if builds and len(builds) > 0 and 'hub_url' in input:
            latest_build = builds[0]
            build_id = latest_build.get('id', 0)
            build_info = self.api_resources.get_build(hub_url=input['hub_url'], build_id=build_id)
            rpms = self.api_resources.list_RPMs(hub_url=input['hub_url'], build_id=build_id)
            src_rpm = [rpm for rpm in rpms if rpm.get('arch') == 'src'][0]
            srpm_download_url = os.path.join(
                self.api_resources.get_path_info(build=build_info),
                self.api_resources.get_path_info(srpm=src_rpm)
            ).replace('/mnt/koji', pkgs_download_server_url)

        if task and 'hub_url' in input and task.get('task_id'):
            srpm = ''
            if task.get('srpms'):
                srpm = task.get('srpms', [])[0].split(os.sep)[-1]
            if task.get('srpm'):
                srpm = task.get('srpm', '').split(os.sep)[-1]
            srpm_download_url = os.path.join(
                self.api_resources.get_path_info(task=task['task_id']), srpm
            ).replace('/mnt/koji', pkgs_download_server_url)

        srpm_downloaded_path = self._download_file(srpm_download_url)
        if srpm_downloaded_path == '404':
            raise Exception('SRPM download failed. URL returns 404 NOT FOUND error.')
        if srpm_downloaded_path:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Successfully downloaded from %s' % srpm_download_url
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'SRPM could not be downloaded from %s' % srpm_download_url
            ))
        return {'srpm_path': srpm_downloaded_path}, {task_subject: task_log}

    def platform_pot_file(self, input, kwargs):

        task_subject = "Download platform POT file"
        task_log = OrderedDict()

        doc_prefix = ''
        if kwargs.get('dir'):
            doc_prefix = requests.utils.requote_uri(kwargs['dir'])

        platform_pot_urls = {
            TRANSPLATFORM_ENGINES[0]:
                '{platform_url}/POT/{project}.{version}/{project}.{version}.pot',
            TRANSPLATFORM_ENGINES[1]:
                '{platform_url}/api/2/project/{project}/resource/{version}/content/?file',
            TRANSPLATFORM_ENGINES[2]:
                '{platform_url}/rest/file/source/{project}/{version}/pot?docId={domain}',
            TRANSPLATFORM_ENGINES[3]:
                '{platform_url}/api/components/{project}/{version}/new_template/',
            TRANSPLATFORM_ENGINES[4]:
                '{platform_url}/api2/v1/projects/{project}/jobs/{version}/original',
        }

        if not (input.get('pkg_branch_map') or {}).get(input.get('release_slug')):
            err_msg = "No branch mapping for %s package of %s release." % (
                input['package'], input.get('release_slug', 'given release')
            )
            task_log.update(self._log_task(
                input['log_f'], task_subject, err_msg
            ))
            raise Exception(err_msg)

        # ToDO: 'version' for memsource
        url_kwargs = {
            'platform_url': input['pkg_tp_url'],
            'project': input['package'],
            'version': input.get('pkg_branch_map', {}).get(input.get('release_slug'), {}).get(
                BRANCH_MAPPING_KEYS[0], ''),
            'domain': doc_prefix + input.get('i18n_domain', '')
        }

        platform_pot_path = ''
        if input.get('pkg_tp_engine'):
            platform_pot_url = platform_pot_urls.get(input['pkg_tp_engine'], '').format(**url_kwargs)
            auth = None
            headers = {}
            if input.get('pkg_tp_auth_usr') and input.get('pkg_tp_auth_token') \
                    and input['pkg_tp_engine'] == TRANSPLATFORM_ENGINES[1]:
                auth = HTTPBasicAuth(*(API_TOKEN_PREFIX.get(input['pkg_tp_engine']),
                                       input['pkg_tp_auth_token']))
            if input.get('pkg_tp_auth_usr') and input.get('pkg_tp_auth_token') \
                    and input['pkg_tp_engine'] == TRANSPLATFORM_ENGINES[2]:
                headers['X-Auth-User'] = input['pkg_tp_auth_usr']
                headers['X-Auth-Token'] = input['pkg_tp_auth_token']
            if input.get('pkg_tp_auth_usr') and input.get('pkg_tp_auth_token') \
                    and input['pkg_tp_engine'] == TRANSPLATFORM_ENGINES[3]:
                headers['Authorization'] = "{} {}".format(
                    API_TOKEN_PREFIX.get(input['pkg_tp_engine']),
                    input['pkg_tp_auth_token']
                )
            try:
                platform_pot_path = self._download_file(
                    platform_pot_url,
                    self.sandbox_path + 'platform.' + input.get('i18n_domain') + '.pot',
                    headers=headers, auth=auth
                )
                if platform_pot_path == '404' and input.get('pkg_upstream_name') and \
                    input['package'] != input.get('pkg_upstream_name', '') and \
                        input['package'] == input.get('i18n_domain'):
                    url_kwargs['domain'] = doc_prefix + input['pkg_upstream_name']
                    platform_pot_url = platform_pot_urls.get(input['pkg_tp_engine'], '').format(**url_kwargs)
                    platform_pot_path = self._download_file(
                        platform_pot_url,
                        self.sandbox_path + 'platform.' + input.get('i18n_domain') + '.pot',
                        headers=headers
                    )
                probable_versions = ('main', 'master', 'default', input['package'])
                while_loop_counter = 0
                while platform_pot_path == '404' and while_loop_counter < len(probable_versions):
                    url_kwargs['version'] = probable_versions[while_loop_counter]
                    platform_pot_url = platform_pot_urls.get(input['pkg_tp_engine'], '').format(**url_kwargs)
                    platform_pot_path = self._download_file(
                        platform_pot_url,
                        self.sandbox_path + 'platform.' + input.get('i18n_domain') + '.pot',
                        headers=headers
                    )
                    while_loop_counter += 1
                if platform_pot_path == '404':
                    raise Exception('POT file could not be located at platform.')
                # load POT file
                polib.pofile(platform_pot_path)
            except Exception as e:
                err_msg = f'POT download failed. Details: {e}'
                task_log.update(self._log_task(input['log_f'], task_subject, err_msg))
                raise Exception(err_msg)
            else:
                task_log.update(self._log_task(
                    input['log_f'], task_subject,
                    'POT downloaded successfully. URL: %s' % platform_pot_url
                ))
        return {'platform_pot_path': platform_pot_path}, {task_subject: task_log}

    def pull_translations(self, input, kwargs):
        """
        Download translations from a Platform
            - Preference to CI Platform over translation
        """

        task_subject = "Download translations"
        task_log = OrderedDict()

        target_langs = []
        translated_files = []
        ci_lang_job_map = input.get('ci_lang_job_map', {})

        file_ext = 'po'
        if input.get('trans_file_ext') and input['trans_file_ext'] != file_ext:
            file_ext = input['trans_file_ext'].lstrip(".")
        if kwargs.get('ext'):
            file_ext = kwargs['ext'].lower()

        download_folder = os.path.join(
            self.sandbox_path, kwargs['dir'] if kwargs.get('dir') else 'downloads'
        )

        platform_project = input.get('ci_project_uid') or input.get('package')
        if kwargs.get('target_langs'):
            target_langs = self.format_target_langs(langs=kwargs['target_langs'])

        if input.get('ci_project_uid') and \
                not set(target_langs).issubset({i[0] for i in ci_lang_job_map.values()}):
            raise Exception('Job UID could NOT be found for target langs.')

        if not target_langs and kwargs.get('target_langs'):
            target_langs = kwargs['target_langs']

        for t_lang in target_langs:

            platform_engine = input.get('pkg_ci_engine') or input.get('pkg_tp_engine')
            platform_api_url = input.get('pkg_ci_url') or input.get('pkg_tp_url')
            platform_auth_user = input.get('pkg_ci_auth_usr') or input.get('pkg_tp_auth_usr')
            platform_auth_token = input.get('pkg_ci_auth_token') or input.get('pkg_tp_auth_token')

            service_kwargs = {}
            service_kwargs['auth_user'] = platform_auth_user
            service_kwargs['auth_token'] = platform_auth_token

            if kwargs.get('prepend_branch') and input.get('repo_branch'):
                ci_lang_job_map = {k: v for k, v in ci_lang_job_map.items() for x in v if input['repo_branch'] in x}
            elif kwargs.get('prepend_package'):
                ci_lang_job_map = {k: v for k, v in ci_lang_job_map.items() for x in v if input['package'] in x}
            elif not kwargs.get('prepend_branch') and not kwargs.get('prepend_package'):
                ci_lang_job_map = {k: v for k, v in ci_lang_job_map.items()
                                   if self.double_underscore_delimiter not in v[1]}

            project_version = list({k for k, v in ci_lang_job_map.items() for x in v if t_lang in x}) or \
                input.get('repo_branch') or \
                input.get('pkg_branch_map', {}).get(input.get('ci_release'), {}).get('platform_version')

            remote_file_names = list({v[1] for k, v in ci_lang_job_map.items() for x in v if t_lang in x})
            remote_file_name = remote_file_names[0] if remote_file_names else "{}.{}".format(t_lang, file_ext)

            if isinstance(project_version, list) and len(project_version) > 0:
                project_version = project_version[0]

            if not input.get('ci_project_uid') and kwargs.get('branch'):
                project_version = kwargs.get('branch')

            service_kwargs.update(dict(no_cache_api=True))

            service_args = []
            service_args.append(platform_project)
            service_args.append(project_version)

            # Transifex
            if platform_engine == TRANSPLATFORM_ENGINES[1]:
                service_args.append(self.format_locale(t_lang))
                service_kwargs.update(dict(ext=True))

            # Weblate
            if platform_engine == TRANSPLATFORM_ENGINES[3]:
                service_args.append(self.format_locale(t_lang, alias_zh=kwargs.get('alias_zh', False)))

            try:
                pull_status, pull_resp = self.api_resources.pull_translations(
                    platform_engine, platform_api_url, *service_args, **service_kwargs
                )
            except Exception as e:
                task_log.update(self._log_task(
                    input['log_f'], task_subject,
                    'Something went wrong in pulling: %s' % str(e)
                ))
            else:
                if pull_status:
                    downloaded_file_name = remote_file_name

                    # clean file name a bit, remove prepends
                    if kwargs.get('prepend_package') and input['package'] in downloaded_file_name and \
                            self.double_underscore_delimiter in downloaded_file_name:
                        task_log.update(self._log_task(
                            input['log_f'], task_subject, '{} to be downloaded and renamed.'.format(
                                downloaded_file_name)
                        ))
                        downloaded_file_name = downloaded_file_name.replace(input['package'], '').replace(
                            self.double_underscore_delimiter, '')

                    d_file_path = os.path.join(download_folder, downloaded_file_name)
                    try:
                        if not os.path.exists(download_folder):
                            os.makedirs(download_folder)
                        with open(d_file_path, 'wb') as f:
                            f.write(pull_resp)
                    except Exception as e:
                        task_log.update(self._log_task(
                            input['log_f'], task_subject,
                            'Something went wrong in writing: %s' % d_file_path
                        ))
                    else:
                        task_log.update(self._log_task(
                            input['log_f'], task_subject, '{} downloaded successfully.'.format(
                                downloaded_file_name)
                        ))
                    translated_files.append(d_file_path)
                else:
                    task_log.update(self._log_task(
                        input['log_f'], task_subject,
                        'Something went wrong in pulling translation file for {}: {}'.format(
                            t_lang, str(pull_resp)
                        )
                    ))
                    raise Exception(
                        "Pull failed for lang {}. {} response: {}".format(
                            t_lang, platform_engine.title(), pull_resp)
                    )

        return {'download_dir': download_folder, 'trans_files': translated_files,
                'target_langs': target_langs}, {task_subject: task_log}

    def translation_files(self, input, kwargs):
        """Download translations from a translation Platform"""
        input_params = input.copy()
        eliminate_items = ['ci_project_uid', 'pkg_ci_engine', 'pkg_ci_url',
                           'pkg_ci_auth_usr', 'pkg_ci_auth_token', 'ci_lang_job_map']
        for item in eliminate_items:
            input_params.pop(item)
        return self.pull_translations(input_params, kwargs)
