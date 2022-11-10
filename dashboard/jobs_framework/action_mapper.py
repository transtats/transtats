# Copyright 2018 Red Hat, Inc.
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

# Currently, it is implemented as...
# Every command has its own class and task gets matched
#   with most appropriate method therein

import re
import os
import shutil
import time
import difflib
from requests.auth import HTTPBasicAuth
import requests
import polib
import tarfile

from collections import OrderedDict
from datetime import datetime
from git import Repo
from inspect import getmembers, isfunction
from pyrpm.spec import Spec
from shlex import split
from shutil import copy2, rmtree
from subprocess import Popen, PIPE, call
from urllib.parse import urlparse

from django.conf import settings

# dashboard
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, BRANCH_MAPPING_KEYS,
    BUILD_SYSTEMS, API_TOKEN_PREFIX
)
from dashboard.converters.specfile import RpmSpecFile
from dashboard.managers import BaseManager

__all__ = ['ActionMapper']


class JobCommandBase(BaseManager):

    comma_delimiter = ","
    double_underscore_delimiter = "__"

    def __init__(self):

        kwargs = {
            'sandbox_path': 'dashboard/sandbox/',
        }
        super(JobCommandBase, self).__init__(**kwargs)

    def _format_log_text(self, delimiter, text, text_prefix):
        log_text = ''
        if isinstance(text, str):
            log_text = text
        if isinstance(text, (list, tuple)):
            log_text = delimiter.join(text)
        if text_prefix:
            log_text = " :: " + text_prefix + delimiter + log_text
        return log_text

    def _log_task(self, log_f, subject, text, text_prefix=None):
        if ".log" not in log_f:
            raise Exception("Log file is not formatted.")
        with open(log_f, 'a+') as the_file:
            text_to_write = \
                '\n<b>' + subject + '</b> ...\n%s\n' % \
                                    self._format_log_text(" \n ", text, text_prefix)
            the_file.write(text_to_write)
        return {str(datetime.now()): '%s' % self._format_log_text(", ", text, text_prefix)}

    def _run_shell_cmd(self, command):
        process = Popen(command, stdout=PIPE, shell=True)
        while True:
            line = process.stdout.readline().rstrip()
            if not line:
                break
            yield line

    def find_dir(self, dirname, path):
        for root, dirs, files in os.walk(path):
            if root[len(path) + 1:].count(os.sep) < 2:
                if dirname in dirs:
                    return os.path.join(root, dirname)

    def format_target_langs(self, langs):
        target_langs = []
        if isinstance(langs, (list, tuple)):
            target_langs = langs
        elif isinstance(langs, str):
            target_langs = langs.split(self.comma_delimiter) \
                if self.comma_delimiter in langs \
                else [langs]
        return target_langs

    @staticmethod
    def _format_locale(locale, alias_zh=False):

        zh_alias = {
            'CN': 'Hans',
            'TW': 'Hant'
        }

        parsed_locale = re.split(r'[_.@]', locale)
        if '_' in locale and len(parsed_locale) >= 2:
            lang = parsed_locale[0].lower()
            territory = parsed_locale[1].upper()
            if alias_zh and zh_alias.get(territory):
                territory = zh_alias[territory]
            return "{}_{}".format(lang, territory)
        return locale


class Get(JobCommandBase):
    """Handles all operations for GET Command"""
    def latest_build_info(self, input, kwargs):
        """Fetch latest build info from koji"""
        task_subject = "Latest Build Details"
        task_log = OrderedDict()

        package = input.get('pkg_downstream_name') or input.get('package')
        builds = self.api_resources.build_info(
            hub_url=input.get('hub_url'), tag=input.get('build_tag'), pkg=package
        )
        if len(builds) > 0:
            task_log.update(self._log_task(input['log_f'], task_subject, str(builds[0])))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'No build details found for %s.' % input.get('build_tag')
            ))

        return {'builds': builds}, {task_subject: task_log}

    def task_info(self, input, kwargs):
        """Fetch task info and results"""
        task_subject = "Task Details"
        task_log = OrderedDict()

        task_info = self.api_resources.task_info(
            hub_url=input.get('hub_url'), task_id=kwargs.get('task_id')
        )
        task_result = self.api_resources.task_result(
            hub_url=input.get('hub_url'), task_id=kwargs.get('task_id')
        )

        if kwargs.get('task_id') != task_info.get('id'):
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'No task info found for id %s.' % kwargs.get('task_id')
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, str({**task_info, **task_result})
            ))
        if task_info.get('id'):
            task_result.update(dict(task_id=task_info['id']))

        return {'task': task_result}, {task_subject: task_log}


class Download(JobCommandBase):
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
            platform_pot_url = platform_pot_urls.get(input['pkg_tp_engine']).format(**url_kwargs)
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
                    platform_pot_url = platform_pot_urls.get(input['pkg_tp_engine']).format(**url_kwargs)
                    platform_pot_path = self._download_file(
                        platform_pot_url,
                        self.sandbox_path + 'platform.' + input.get('i18n_domain') + '.pot',
                        headers=headers
                    )
                probable_versions = ('main', 'master', 'default', input['package'])
                while_loop_counter = 0
                while platform_pot_path == '404' and while_loop_counter < len(probable_versions):
                    url_kwargs['version'] = probable_versions[while_loop_counter]
                    platform_pot_url = platform_pot_urls.get(input['pkg_tp_engine']).format(**url_kwargs)
                    platform_pot_path = self._download_file(
                        platform_pot_url,
                        self.sandbox_path + 'platform.' + input.get('i18n_domain') + '.pot',
                        headers=headers
                    )
                    while_loop_counter += 1
                if platform_pot_path == '404':
                    raise Exception('POT file could not be located at platform.')
                try:
                    polib.pofile(platform_pot_path)
                except Exception:
                    raise
            except Exception as e:
                err_msg = 'POT download failed. Details: %s' % str(e)
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
        if kwargs.get('ext'):
            file_ext = kwargs['ext'].lower()

        download_folder = os.path.join(
            self.sandbox_path, kwargs['dir'] if kwargs.get('dir') else 'downloads'
        )

        platform_project = input.get('ci_project_uid') or input.get('package')
        if kwargs.get('target_langs'):
            target_langs = self.format_target_langs(langs=kwargs['target_langs'])

        if input.get('ci_project_uid') and \
                not set(target_langs).issubset(set([i[0] for i in ci_lang_job_map.values()])):
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
            elif not kwargs.get('prepend_branch'):
                ci_lang_job_map = {k: v for k, v in ci_lang_job_map.items()
                                   if self.double_underscore_delimiter not in v[1]}

            project_version = list({k for k, v in ci_lang_job_map.items() for x in v if t_lang in x}) or \
                input.get('repo_branch') or \
                input.get('pkg_branch_map', {}).get(input.get('ci_release'), {}).get('platform_version')

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
                service_args.append(self._format_locale(t_lang))
                service_kwargs.update(dict(ext=True))

            # Weblate
            if platform_engine == TRANSPLATFORM_ENGINES[3]:
                service_args.append(self._format_locale(t_lang, alias_zh=kwargs.get('alias_zh', False)))

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
                    downloaded_file_name = "{}.{}".format(t_lang, file_ext)
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


class Clone(JobCommandBase):
    """Handles all operations for CLONE Command"""

    def _format_weblate_git_url(self, input_params):
        clone_url = input_params['upstream_repo_url']
        parsed_url = urlparse(clone_url)
        return "{}://{}:{}@{}".format(
            parsed_url.scheme, input_params['pkg_tp_auth_usr'],
            input_params['pkg_tp_auth_token'], parsed_url.netloc + parsed_url.path
        )

    def _is_fork_exist(self, repo_clone_url):
        instance_url, git_owner_repo = self._parse_git_url(repo_clone_url)
        git_platform = self._determine_git_platform(instance_url)
        git_owner, git_repo = git_owner_repo
        kwargs = {}
        kwargs.update(dict(no_cache_api=True))
        repositories = self.api_resources.list_repos(
            git_platform, instance_url, settings.GITHUB_USER, **kwargs
        )
        for repository in repositories:
            if repository.get('name', '') == git_repo and repository.get('fork'):
                return True
        return False

    def _delete_fork(self, repo_clone_url):
        instance_url, git_owner_repo = self._parse_git_url(repo_clone_url)
        git_platform = self._determine_git_platform(instance_url)
        git_owner, git_repo = git_owner_repo
        kwargs = {}
        kwargs.update(dict(no_cache_api=True))
        delete_repo_resp = self.api_resources.delete_repo(
            git_platform, instance_url, *(settings.GITHUB_USER, git_repo), **kwargs
        )
        return delete_repo_resp

    def _create_fork(self, repo_clone_url):
        instance_url, git_owner_repo = self._parse_git_url(repo_clone_url)
        git_platform, kwargs = self._determine_git_platform(instance_url), {}
        create_fork_api_response = self.api_resources.create_fork(
            git_platform, instance_url, *git_owner_repo, **kwargs
        )
        return create_fork_api_response.get("html_url", "")

    def git_repository(self, input, kwargs):
        """Clone GIT repository"""
        task_subject = "Clone Repository"
        task_log = OrderedDict()

        src_tar_dir = os.path.join(self.sandbox_path, input['package'])

        clone_kwargs = {}
        clone_kwargs.update(dict(config='http.sslVerify=false'))
        if kwargs.get('recursive'):
            clone_kwargs.update(dict(recursive=True))
        if kwargs.get('branch') and not kwargs.get('type') == TRANSPLATFORM_ENGINES[3]:
            clone_kwargs.update(dict(branch=kwargs['branch']))

        repo_clone_url = input['upstream_repo_url']
        if kwargs.get("fork"):
            # delete the fork if exists already
            fork_exists = self._is_fork_exist(repo_clone_url)
            if fork_exists:
                self._delete_fork(repo_clone_url)
            # create a new fork and proceed cloning
            fork_url = self._create_fork(repo_clone_url)
            if fork_url:
                repo_clone_url = fork_url

        if kwargs.get('type') == TRANSPLATFORM_ENGINES[3]:
            repo_clone_url = self._format_weblate_git_url(input)

        try:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Start cloning %s repository.' % repo_clone_url
            ))
            clone_result = Repo.clone_from(
                repo_clone_url, src_tar_dir, **clone_kwargs
            )
        except Exception as e:
            trace_back = str(e)
            # hide auth_token in logs
            if input['pkg_tp_auth_token'] in trace_back:
                trace_back = trace_back.replace(input['pkg_tp_auth_token'], 'XXX')
            task_log.update(self._log_task(
                input['log_f'], task_subject, 'Cloning failed. Details: %s' % trace_back
            ))
            raise Exception("Cloning '%s' branch failed." % kwargs.get('branch', 'main'))
        else:
            if vars(clone_result).get('git_dir'):
                task_log.update(self._log_task(
                    input['log_f'], task_subject, os.listdir(src_tar_dir),
                    text_prefix='Cloning git repo completed.'
                ))
            return {'src_tar_dir': src_tar_dir}, {task_subject: task_log}


class Generate(JobCommandBase):
    """Handles all operations for GENERATE Command"""

    def _verify_command(self, command):
        """
        verify given command against commands.acl file
        :param command: str
        :return: filtered command
        """
        sh_commands = [command]
        if ';' in command:
            sh_commands = [cmd.strip() for cmd in command.split(';')]
        elif '&&' in command:
            sh_commands = [cmd.strip() for cmd in command.split('&&')]
        with open(os.path.join(
                'dashboard', 'jobs_framework', 'commands.acl'), 'r'
        ) as acl_values:
            allowed_base_commands = acl_values.read().splitlines()
            not_allowed = [cmd for cmd in sh_commands if cmd.split()[0] not in allowed_base_commands]
            if not_allowed and len(not_allowed) >= 1:
                raise Exception('Invalid command: %s' % not_allowed[0])
        return command

    def pot_file(self, input, kwargs):
        """
        Generates POT file
            as per the given command
        """
        task_subject = "Generate POT File"
        task_log = OrderedDict()
        pot_file_path = ''

        if kwargs.get('cmd'):
            command = self._verify_command(kwargs['cmd'])
            po_dir = self.find_dir('po', input['src_tar_dir'])
            if not po_dir:
                po_dir = self.find_dir('locale', input['src_tar_dir']) or ''
            pot_file = os.path.join(
                po_dir, '%s.pot' % kwargs.get('domain', input['package'])
            )
            if os.path.exists(pot_file) and kwargs.get('overwrite'):
                os.unlink(pot_file)
            try:
                os.chdir(input['src_tar_dir'])
                generate_pot = Popen(command, stdout=PIPE, shell=True)
                output, error = generate_pot.communicate()
            except Exception as e:
                os.chdir(input['base_dir'])
                task_log.update(self._log_task(
                    input['log_f'], task_subject,
                    'POT file generation failed %s' % str(e)
                ))
            else:
                os.chdir(input['base_dir'])
                if os.path.isfile(pot_file):
                    pot_file_path = pot_file
                    task_log.update(self._log_task(
                        input['log_f'], task_subject, output.decode("utf-8"),
                        text_prefix='POT file generated successfully. [ %s.pot ]' %
                                    kwargs.get('domain', input['package'])
                    ))
                else:
                    error_response = 'POT file generation failed with command: %s' % command
                    task_log.update(self._log_task(
                        input['log_f'], task_subject, error_response)
                    )
                    raise Exception(error_response)
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, 'Command to generate POT missing.'
            ))
        return {'src_pot_file': pot_file_path,
                'i18n_domain': kwargs.get('domain', input['package'])}, \
               {task_subject: task_log}


class Unpack(JobCommandBase):
    """Handles all operations for UNPACK Command"""

    def srpm(self, input, kwargs):
        """
        SRPM is a headers + cpio file
            - its extraction currently is dependent on cpio command
        """

        task_subject = "Unpack SRPM"
        task_log = OrderedDict()

        try:
            command = "rpm2cpio " + os.path.join(
                input['base_dir'], input['srpm_path']
            )
            command = split(command)
            rpm2cpio = Popen(command, stdout=PIPE)
            extract_dir = os.path.join(self.sandbox_path, input['package'])
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            command = "cpio -idm -D %s" % extract_dir
            command = split(command)
            call(command, stdin=rpm2cpio.stdout)
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'SRPM Extraction Failed %s' % str(e)
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, os.listdir(extract_dir),
                text_prefix='SRPM Extracted Successfully'
            ))
            return {'extract_dir': extract_dir}, {task_subject: task_log}

    def _determine_tar_dir(self, params):
        for root, dirs, files in os.walk(params['extract_dir']):
            for directory in dirs:
                if directory == params['package']:
                    return os.path.join(root, directory)
            return root

    def tarball(self, input, kwargs):
        """Untar source tarball"""

        task_subject = "Unpack tarball"
        task_log = OrderedDict()

        try:
            src_tar_dir = None
            with tarfile.open(input['src_tar_file']) as tar_file:
                tar_members = tar_file.getmembers()
                if len(tar_members) > 0:
                    src_tar_dir = os.path.join(
                        input['extract_dir'], tar_members[0].get_info().get('name', '')
                    )
                tar_file.extractall(path=input['extract_dir'])

            if input['related_tarballs']:
                for r_tarball in input['related_tarballs']:
                    with tarfile.open(r_tarball) as tar_file:
                        tar_file.extractall(path=src_tar_dir)

        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Tarball Extraction Failed %s' % str(e)
            ))
        else:
            if not os.path.isdir(src_tar_dir):
                src_tar_dir = self._determine_tar_dir(input)
            task_log.update(self._log_task(
                input['log_f'], task_subject, os.listdir(src_tar_dir),
                text_prefix='Tarball [ %s ] Extracted Successfully' % input['src_tar_file'].split('/')[-1]
            ))
            return {'src_tar_dir': src_tar_dir, 'src_translations': input['src_translations'],
                    'spec_obj': input['spec_obj'], 'spec_sections': input['spec_sections']},\
                   {task_subject: task_log}


class Load(JobCommandBase):
    """Handles all operations for LOAD Command"""

    def spec_file(self, input, kwargs):
        """locate and load spec file"""
        task_subject = "Load Spec file"
        task_log = OrderedDict()

        try:
            root_dir = ''
            spec_file = ''
            tarballs = []
            src_translations = []
            src_tar_file = None
            related_tarballs = []
            for root, dirs, files in os.walk(input['extract_dir']):
                root_dir = root
                for file in files:
                    if file.endswith('.spec') and not file.startswith('.'):
                        spec_file = os.path.join(root, file)
                    zip_ext = ('.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz')
                    # assuming translations are not packaged in tests tarball
                    if file.endswith(zip_ext) and 'test' not in file:
                        tarballs.append(file)
                    translation_ext = ('.po', )
                    if file.endswith(translation_ext):
                        src_translations.append(file)
            spec_obj = Spec.from_file(spec_file)

            if len(tarballs) > 0:
                probable_tarball = spec_obj.sources[0].split('/')[-1]

                replacements = {
                    "%{name}": spec_obj.name,
                    "%{version}": spec_obj.version,
                    "%{realname}": spec_obj.name,
                    "%{realversion}": spec_obj.version
                }

                for replacement_key, replacement_val in replacements.items():
                    if replacement_key in probable_tarball:
                        probable_tarball = probable_tarball.replace(
                            replacement_key, replacement_val)
                src_tar_file = os.path.join(root_dir, probable_tarball) \
                    if probable_tarball in tarballs \
                    else os.path.join(root_dir, tarballs[0])

            if len(src_translations) > 0:
                src_translations = list(map(
                    lambda x: os.path.join(root_dir, x), src_translations
                ))
            spec_sections = RpmSpecFile(os.path.join(input['base_dir'], spec_file))

            version_release = spec_obj.release[:spec_obj.release.index('%')]
            release_related_tarballs = [tarball for tarball in tarballs
                                        if version_release in tarball and tarball in spec_obj.sources]
            if release_related_tarballs:
                related_tarballs = [os.path.join(root_dir, x) for x in release_related_tarballs]
            # look for translation specific tarball
            po_tarball_name = '{0}-{1}'.format(input['package'], 'po')
            translation_related_tarballs = [tarball for tarball in tarballs
                                            if po_tarball_name in tarball and tarball in spec_obj.sources]
            if translation_related_tarballs and len(translation_related_tarballs) > 0:
                index_in_prep = '-a {0}'.format(spec_obj.sources.index(translation_related_tarballs[0]))
                prep_lines = spec_sections.section.get('prep', {}).get(input['package'], [])
                if index_in_prep in " ".join(
                        [prep_line for prep_line in prep_lines if prep_line.startswith('%')]):
                    related_tarballs.append(os.path.join(root_dir, translation_related_tarballs[0]))
                elif input['package'] in " ".join(
                        [prep_line for prep_line in prep_lines if prep_line.startswith('tar -x')]):
                    related_tarballs.append(os.path.join(root_dir, translation_related_tarballs[0]))
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Loading Spec file failed %s' % str(e)
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, spec_obj.sources,
                text_prefix='Spec file loaded, Sources'
            ))
            return {
                'spec_file': spec_file, 'src_tar_file': src_tar_file, 'spec_obj': spec_obj,
                'src_translations': src_translations, 'spec_sections': spec_sections,
                'related_tarballs': related_tarballs
            }, {task_subject: task_log}


class Apply(JobCommandBase):
    """Handles all operations for APPLY Command"""

    def _apply_prep(self, input, prep_section, tar_dir, w_log, sub):
        file_ext = '.po'
        prep_steps = []
        relevant_prep_steps = {}
        po_related_sources = {i: j for i, j in input['spec_obj'].sources_dict.items() if file_ext in j}

        for i, j in po_related_sources.items():
            source_step = [step for step in prep_section if i.upper() in step]
            if len(source_step) > 0:
                relevant_prep_steps[j] = source_step[0]

        for i, j in relevant_prep_steps.items():
            src_po = [po for po in input['src_translations'] if i in po]
            if len(src_po) > 0:
                cmd_parts = j.split()
                if cmd_parts[0] in ('cp', 'install') and file_ext in cmd_parts[-1]:
                    copy_args = src_po[0], os.path.join(tar_dir, cmd_parts[-1])
                    prep_steps.append("{0} {1} {2}".format(cmd_parts[0], *copy_args))
                    copy2(*copy_args)

        if len(prep_steps) > 0:
            w_log.update(self._log_task(
                input['log_f'], sub, prep_steps,
                text_prefix='%s prep command(s) ran' % len(prep_steps)
            ))

    def patch(self, input, kwargs):

        task_subject = "Apply Patches"
        task_log = OrderedDict()

        tar_dir = {'src_tar_dir': input['src_tar_dir']}

        patches_from_spec = input['spec_obj'].patches
        if patches_from_spec:
            tar_dir.update(dict(patches=patches_from_spec))

        if input['src_translations']:
            s_sections = input['spec_sections']
            self._apply_prep(
                input, s_sections.getSection('prep'), input['src_tar_dir'],
                task_log, task_subject
            )

        try:
            patches = []
            src_trans = input['src_translations']
            for root, dirs, files in os.walk(input['extract_dir']):
                for file in files:
                    if file.endswith('.patch'):
                        patches.append(os.path.join(root, file))

            if not patches and not src_trans:
                task_log.update(self._log_task(input['log_f'], task_subject, 'No patches found.'))
                return tar_dir

            # apply patches
            [copy2(patch, input['src_tar_dir']) for patch in patches]
            os.chdir(input['src_tar_dir'])
            for patch in patches:
                err_msg = "Perhaps you used the wrong -p"
                command_std_output = "Perhaps you used the wrong -p or --strip option?"
                p_value = 0
                p_value_limit = 5
                while err_msg in command_std_output and p_value < p_value_limit:
                    command = "patch -p" + str(p_value) + " -i " + patch.split('/')[-1]
                    command = split(command)
                    patch_output = Popen(command, stdout=PIPE)
                    command_std_output = patch_output.stdout.read().decode("utf-8")
                    patch_output.kill()
                    p_value += 1
        except Exception as e:
            os.chdir(input['base_dir'])
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in applying patches: %s' % str(e)
            ))
        else:
            os.chdir(input['base_dir'])
            task_log.update(self._log_task(
                input['log_f'], task_subject, patches,
                text_prefix='%s patches applied' % len(patches)
            ))

        return tar_dir, {task_subject: task_log}


class Filter(JobCommandBase):
    """Handles all operations for FILTER Command"""

    @staticmethod
    def _determine_podir(files, domain):
        if not domain:
            return False
        for file in files:
            file_path_parts = file.split(os.sep)
            expected_locale = file_path_parts[-1].split('.')[0]
            super_dir = file_path_parts[-3]
            if expected_locale == domain and super_dir == 'locale':
                return True
        return False

    @staticmethod
    def _test_multiple_trans_dir(t_files, is_podir):
        trans_dirs = []
        for trans_file in t_files:
            trans_dir = trans_file.rsplit(os.sep, 1)[0]
            if is_podir:
                trans_dir = trans_file.rsplit(os.sep, 3)[0]
            if trans_dir not in trans_dirs:
                trans_dirs.append(trans_dir)
        return len(trans_dirs) > 1, trans_dirs

    def files(self, input, kwargs):
        """Filter files from tarball"""
        file_ext = 'po'
        result_dict = {}
        if kwargs.get('ext'):
            file_ext = kwargs['ext'].lower()

        task_subject = "Filter %s files" % file_ext.upper()
        task_log = OrderedDict()

        if input.get('patches', []):
            time.sleep(1)

        try:
            trans_files = []
            search_dir = input['extract_dir'] if 'extract_dir' in input else input['src_tar_dir']
            if kwargs.get('dir') and isinstance(kwargs.get('dir'), str):
                search_dir = os.path.join(search_dir, *kwargs['dir'].split(os.sep))
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.%s' % file_ext):
                        trans_files.append(os.path.join(root, file))
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in filtering {} files: {}'.format(file_ext, str(e))
            ))
        else:
            is_podir = self._determine_podir(trans_files, kwargs.get('domain'))
            is_multiple_trans_dir, trans_dirs = self._test_multiple_trans_dir(trans_files, is_podir)
            if is_multiple_trans_dir:
                trans_dirs = [trans_dir.replace(search_dir, "") if trans_dir.replace(search_dir, "") else trans_dir
                              for trans_dir in trans_dirs]
                task_log.update(self._log_task(
                    input['log_f'], task_subject, [t_dir.lstrip(os.sep) for t_dir in trans_dirs],
                    text_prefix="[WARN] Translations are found in {} directories. "
                                "Setting 'dir' may help.".format(len(trans_dirs))
                ))
            task_log.update(self._log_task(
                input['log_f'], task_subject, trans_files,
                text_prefix='%s %s files filtered' % (len(trans_files), file_ext.upper())
            ))
            result_dict.update({'trans_files': trans_files, 'file_ext': file_ext})
            if is_podir:
                result_dict.update(dict(podir=True))

        return result_dict, {task_subject: task_log}


class Upload(JobCommandBase):
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

    def simplify_plural_forms_in_po_header(self, input: dict, task_log: dict) -> None:
        """
        Pre hook: simplify_plural_forms_in_po_header
            - change Plural-Forms to 'nplurals=1; plural=0;' in PO header.
        """
        task_subject = "Upload Prehook: simplify_plural_forms_in_po_header"
        simple_plural_form = "nplurals=1; plural=0;"

        if not input.get('trans_files'):
            return

        for trans_file in input['trans_files']:
            try:
                po_file = polib.pofile(trans_file)
            except IOError as e:
                task_log.update(self._log_task(input['log_f'], task_subject, str(e)))
                continue
            except Exception as e:
                task_log.update(self._log_task(
                    input['log_f'], task_subject, f'{trans_file} is not a PO file. Details {e}')
                )
                continue
            else:
                po_file.metadata['Plural-Forms'] = simple_plural_form
                po_file.save()

    def copy_template_for_target_langs(self, input: dict, task_log: dict) -> None:
        """
        Pre hook: copy_template_for_target_langs
            - copy a template for all the target langs
        """
        task_subject = "Upload Prehook: copy_template_for_target_langs"

        if not input.get('trans_files'):
            task_log.update(self._log_task(
                input['log_f'], task_subject, 'No template found.')
            )
            return

        first_trans_file = input['trans_files'][0]
        if isinstance(first_trans_file, str) and \
                'template' in first_trans_file.lower() or 'pot' in first_trans_file.lower():
            translation_template = first_trans_file
            task_log.update(self._log_task(
                input['log_f'], task_subject, translation_template, text_prefix='Template collected'
            ))

            target_langs = []
            if input.get('ci_target_langs'):
                target_langs = self.format_target_langs(langs=input['ci_target_langs'])

            source_file = os.path.join(input['base_dir'], translation_template)
            for lang in target_langs:
                translation_lang_file = translation_template
                if 'template' in translation_template:
                    translation_lang_file = translation_template.replace('template', lang)
                if 'pot' in translation_template:
                    translation_lang_file = translation_template.replace('pot', 'po')
                dist_file = os.path.join(input['base_dir'], translation_lang_file)
                # copy template to language file
                shutil.copyfile(source_file, dist_file)
                # add an entry in input values
                input['trans_files'].append(translation_lang_file)

            task_log.update(self._log_task(
                input['log_f'], task_subject, '{} files copied for {}.'.format(
                    len(target_langs), ", ".join(target_langs))
            ))

    def push_files(self, input, kwargs):
        """
        Push translations to a Platform
            - Preference to CI Platform over translation
        """
        task_subject = "Push translations files"
        task_log = OrderedDict()

        if kwargs.get('prehook'):
            pre_hook = kwargs['prehook']
            pre_hook_fn = getattr(self, pre_hook, None)
            if pre_hook_fn:
                pre_hook_fn(input, task_log)

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
            target_langs = self.format_target_langs(langs=kwargs['target_langs'])

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

                file_name = file_path.split(os.sep)[-1]
                if input.get('podir'):
                    file_ext = file_path.split(os.sep)[-1].split('.')[1]
                    file_name = "{}.{}".format(file_path.split(os.sep)[-2], file_ext)
                platform_engine = input.get('pkg_ci_engine') or input.get('pkg_tp_engine')
                platform_api_url = input.get('pkg_ci_url') or input.get('pkg_tp_url')
                platform_auth_user = input.get('pkg_ci_auth_usr') or input.get('pkg_tp_auth_usr')
                platform_auth_token = input.get('pkg_ci_auth_token') or input.get('pkg_tp_auth_token')

                if kwargs.get('update') and input.get('ci_lang_job_map') \
                        and lang not in set([i[0] for i in ci_lang_job_map.values()]):
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
                        os.rename(os.path.join(input['base_dir'], input['download_dir'], file_name),
                                  os.path.join(input['base_dir'], input['download_dir'], new_filename))
                        file_name = new_filename

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
            target_langs = self.format_target_langs(langs=input['target_langs'])

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
                    lang = self._format_locale(lang, alias_zh=kwargs.get('alias_zh', False))

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


class Calculate(JobCommandBase):
    """Handles all operations for CALCULATE Command"""

    def stats(self, input, kwargs):
        """Calculate stats from filtered translations"""

        task_subject = "Calculate Translation Stats"
        task_log = OrderedDict()

        try:
            trans_stats = {}
            if input.get('build_system') and input.get('build_tag'):
                trans_stats['id'] = input['build_system'] + ' - ' + input['build_tag']
            elif input.get('upstream_repo_url'):
                trans_stats['id'] = 'Upstream'
            trans_stats['stats'] = []
            for po_file in input['trans_files']:
                try:
                    po = polib.pofile(po_file)
                except Exception as e:
                    task_log.update(self._log_task(
                        input['log_f'], task_subject,
                        'Something went wrong while parsing %s: %s' % (po_file, str(e))
                    ))
                else:
                    temp_trans_stats = {}
                    temp_trans_stats['unit'] = "MESSAGE"
                    temp_trans_stats['locale'] = po_file.split(os.sep)[-2] if input.get('podir') \
                        else po_file.split(os.sep)[-1].split('.')[0]
                    temp_trans_stats['translated'] = len(po.translated_entries())
                    temp_trans_stats['untranslated'] = len(po.untranslated_entries())
                    temp_trans_stats['fuzzy'] = len(
                        [f_entry for f_entry in po.fuzzy_entries() if not f_entry.obsolete]
                    )
                    temp_trans_stats['total'] = temp_trans_stats['translated'] + \
                        temp_trans_stats['untranslated'] + temp_trans_stats['fuzzy']
                    trans_stats['stats'].append(temp_trans_stats.copy())
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in calculating stats: %s' % str(e)
            ))
        else:
            task_log.update(self._log_task(
                input['log_f'], task_subject, str(trans_stats), text_prefix='Calculated Stats'
            ))
            return {'trans_stats': trans_stats}, {task_subject: task_log}

    def diff(self, input, kwargs):
        """Calculate diff between two"""
        task_subject = "Calculate Differences"
        task_log = OrderedDict()
        diff_lines = ''
        diff_msg = ''
        diff_count = 0

        try:
            src_pot = input.get('src_pot_file')
            platform_pot = input.get('platform_pot_path')

            src_pot_obj, platform_pot_obj = polib.pofile(src_pot), polib.pofile(platform_pot)
            src_pot_dict = {ut_entry.msgid: ut_entry for ut_entry in src_pot_obj.untranslated_entries()}
            platform_pot_dict = {ut_entry.msgid: ut_entry
                                 for ut_entry in platform_pot_obj.untranslated_entries()}
            diff_entries = {k: src_pot_dict[k] for k in set(src_pot_dict) - set(platform_pot_dict)}
            if not diff_entries:
                task_log.update(self._log_task(
                    input['log_f'], task_subject, "No new or updated messages found."
                ))
            else:
                diff_msg = "".join(["line %s\n%s\n%s\n\n" %
                                    (str(entry.linenum), "\n".join(
                                        [" ".join(i) for i in entry.occurrences]
                                    ), entry.msgid) for msg, entry in diff_entries.items()])
                diff_count = len(set(diff_entries))
            if src_pot and platform_pot:
                git_diff_command = 'git diff --no-index %s %s' % (platform_pot, src_pot)
                calculated_diff = Popen(git_diff_command, stdout=PIPE, shell=True)
                output, error = calculated_diff.communicate()
                diff_lines = output.decode("utf-8")
        except Exception as e:
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Something went wrong in calculating diff: %s' % str(e)
            ))
        else:
            if diff_count > 0:
                task_log.update(self._log_task(
                    input['log_f'], task_subject, '%s messages differ.\n\n%s' % (str(diff_count), diff_msg),
                    text_prefix='Calculated Diff'
                ))
        return {'pot_diff': diff_msg, 'full_diff': diff_lines, 'diff_count': diff_count}, {task_subject: task_log}


class Copy(JobCommandBase):
    """Handles all operations for COPY Command"""

    def downloaded_files(self, input, kwargs):
        """Copy downloaded files to provided dir"""

        task_subject = "Copy Downloaded Files"
        task_log = OrderedDict()

        if not kwargs.get('dir'):
            task_log.update(self._log_task(
                input['log_f'], task_subject,
                'Dir value was empty, nothing to copy.'
            ))
            return input, {task_subject: task_log}

        # copy files
        return {}, {task_subject: task_log}


class Pullrequest(JobCommandBase):
    """Handles all operations for PULLREQUEST Command"""

    def github_repo(self, input, kwargs):
        """Prepare merge request and submit"""

        task_subject = "Pull Request"
        task_log = OrderedDict()

        # Prepare Merge Request
        # Submit a GitHub Pull Request
        return {}, {task_subject: task_log}


class ActionMapper(BaseManager):
    """YML Parsed Objects to Actions Mapper"""
    COMMANDS = [
        'GET',          # Call some method
        'DOWNLOAD',     # Download some resource
        'UNPACK',       # Extract an archive
        'LOAD',         # Load into python object
        'FILTER',       # Filter files recursively
        'APPLY',        # Apply patch on source tree
        'CALCULATE',    # Do some maths/try formulae
        'CLONE',        # Clone source repository
        'GENERATE',     # Exec command to create
        'UPLOAD',       # Upload some resource
        'COPY',         # Copy files from one dir to another
        'PULLREQUEST',  # Create and submit pull request
    ]

    def __init__(self,
                 tasks_structure,
                 job_base_dir,
                 build_tag,
                 package,
                 server_url,
                 build_system,
                 release_slug,
                 repo_branch,
                 ci_pipeline_uuid,
                 upstream_url,
                 trans_file_ext,
                 pkg_upstream_name,
                 pkg_downstream_name,
                 pkg_branch_map,
                 pkg_tp_engine,
                 pkg_tp_auth_usr,
                 pkg_tp_auth_token,
                 pkg_tp_url,
                 pkg_ci_engine,
                 pkg_ci_url,
                 pkg_ci_auth_usr,
                 pkg_ci_auth_token,
                 ci_release,
                 ci_target_langs,
                 ci_project_uid,
                 ci_lang_job_map,
                 job_log_file):
        super(ActionMapper, self).__init__()
        self.tasks = tasks_structure
        self.tag = build_tag
        self.pkg = package
        self.hub = server_url
        self.base_dir = job_base_dir
        self.buildsys = build_system
        self.release = release_slug
        self.repo_branch = repo_branch
        self.ci_pipeline_uuid = ci_pipeline_uuid
        self.upstream_url = upstream_url
        self.trans_file_ext = trans_file_ext
        self.pkg_upstream_name = pkg_upstream_name
        self.pkg_downstream_name = pkg_downstream_name
        self.pkg_branch_map = pkg_branch_map
        self.pkg_tp_engine = pkg_tp_engine
        self.pkg_tp_auth_usr = pkg_tp_auth_usr
        self.pkg_tp_auth_token = pkg_tp_auth_token
        self.pkg_tp_url = pkg_tp_url
        self.pkg_ci_engine = pkg_ci_engine
        self.pkg_ci_url = pkg_ci_url
        self.pkg_ci_auth_usr = pkg_ci_auth_usr
        self.pkg_ci_auth_token = pkg_ci_auth_token
        self.ci_release = ci_release
        self.ci_target_langs = ci_target_langs
        self.ci_project_uid = ci_project_uid
        self.ci_lang_job_map = ci_lang_job_map
        self.log_f = job_log_file
        self.cleanup_resources = {}
        self.__build = None
        self.__result = None
        self.__log = OrderedDict()

    def skip(self, abc, pqr, xyz):
        try:
            command = abc.__doc__.strip().split()[-2]
        except Exception as e:
            pass
        else:
            raise Exception('Action mapping failed for %s command.' % command)

    def set_actions(self):
        count = 0
        self.tasks.status = False
        current_node = self.tasks.head
        while current_node is not None:
            count += 1
            cmd = current_node.command or ''
            if cmd.upper() in self.COMMANDS:
                current_node.set_namespace(cmd.title())
            available_methods = [member[0] for member in getmembers(eval(cmd.title()))
                                 if isfunction(member[1])]
            cur_node_task = current_node.task
            if isinstance(cur_node_task, list) and len(cur_node_task) > 0:
                if isinstance(current_node.task[0], dict):
                    cur_node_task = current_node.task[0].get('name', '')
                if len(cur_node_task) > 1:
                    [current_node.set_kwargs(kwarg)
                     for kwarg in current_node.task[1:] if isinstance(kwarg, dict)]
            elif not isinstance(cur_node_task, str):
                cur_node_task = str(current_node.task)
            probable_method = difflib.get_close_matches(
                cur_node_task.lower(), available_methods
            )
            if isinstance(probable_method, list) and len(probable_method) > 0:
                current_node.set_method(probable_method[0])
            current_node = current_node.next

    def execute_tasks(self):
        count = 0
        current_node = self.tasks.head
        initials = {
            'build_tag': self.tag, 'package': self.pkg, 'hub_url': self.hub,
            'base_dir': self.base_dir, 'build_system': self.buildsys, 'log_f': self.log_f,
            'upstream_repo_url': self.upstream_url, 'trans_file_ext': self.trans_file_ext,
            'pkg_branch_map': self.pkg_branch_map, 'pkg_tp_engine': self.pkg_tp_engine,
            'release_slug': self.release, 'pkg_tp_auth_usr': self.pkg_tp_auth_usr,
            'pkg_tp_url': self.pkg_tp_url, 'pkg_tp_auth_token': self.pkg_tp_auth_token,
            'pkg_upstream_name': self.pkg_upstream_name, 'ci_pipeline_uuid': self.ci_pipeline_uuid,
            'pkg_ci_engine': self.pkg_ci_engine, 'pkg_ci_url': self.pkg_ci_url,
            'pkg_ci_auth_usr': self.pkg_ci_auth_usr, 'pkg_ci_auth_token': self.pkg_ci_auth_token,
            'ci_release': self.ci_release, 'ci_target_langs': self.ci_target_langs,
            'ci_project_uid': self.ci_project_uid, 'ci_lang_job_map': self.ci_lang_job_map,
            'pkg_downstream_name': self.pkg_downstream_name, 'repo_branch': self.repo_branch
        }

        while current_node is not None:
            if count == 0:
                current_node.input = initials
            elif current_node.previous.output:
                current_node.input = {**initials, **current_node.previous.output}
            count += 1
            current_node.output, current_node.log = getattr(
                eval(current_node.get_namespace()),
                current_node.get_method(), self.skip
            )(eval(current_node.get_namespace())(), current_node.input, current_node.kwargs)

            if current_node.log:
                self.__log.update(current_node.log)

            self.tasks.status = bool(current_node.output)
            if current_node.output and 'builds' in current_node.output:
                if not current_node.output['builds']:
                    break
                else:
                    self.__build = current_node.output.get('builds')
            if current_node.output and 'srpm_path' in current_node.output:
                d = {'srpm_path': current_node.output.get('srpm_path')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and 'src_tar_dir' in current_node.output:
                d = {'src_tar_dir': current_node.output.get('src_tar_dir')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and 'extract_dir' in current_node.output:
                d = {'extract_dir': current_node.output.get('extract_dir')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and 'src_pot_file' in current_node.output:
                d = {'src_pot_file': current_node.output.get('src_pot_file')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and 'platform_pot_path' in current_node.output:
                d = {'platform_pot_path': current_node.output.get('platform_pot_path')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and 'download_dir' in current_node.output:
                d = {'download_dir': current_node.output.get('download_dir')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and \
                    'trans_stats' in current_node.output or \
                    'pot_diff' in current_node.output or \
                    'push_files_resp' in current_node.output:
                self.__result = current_node.output.get('trans_stats')
                if not self.__result:
                    self.__result = current_node.output.copy()
            current_node = current_node.next

    @property
    def build(self):
        return self.__build or {}

    @property
    def result(self):
        return self.__result

    @property
    def log(self):
        return self.__log

    @property
    def status(self):
        return self.tasks.status

    def clean_workspace(self):
        """Remove downloaded SRPM, and its stuffs"""
        try:
            if self.cleanup_resources.get('srpm_path'):
                os.remove(self.cleanup_resources.get('srpm_path'))
            if self.cleanup_resources.get('platform_pot_path'):
                os.remove(self.cleanup_resources.get('platform_pot_path'))
            if self.cleanup_resources.get('src_tar_dir'):
                rmtree(self.cleanup_resources.get('src_tar_dir'), ignore_errors=True)
            if self.cleanup_resources.get('extract_dir'):
                rmtree(self.cleanup_resources.get('extract_dir'), ignore_errors=True)
            if self.cleanup_resources.get('download_dir'):
                rmtree(self.cleanup_resources.get('download_dir'), ignore_errors=True)
        except OSError as e:
            self.app_logger('ERROR', "Failed to clean sandbox! Due to %s" % e)
