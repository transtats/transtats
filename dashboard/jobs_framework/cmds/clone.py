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
import time
import shutil
from collections import OrderedDict
from urllib.parse import urlparse

from git import Repo

from django.conf import settings

from dashboard.constants import GIT_PLATFORMS, TRANSPLATFORM_ENGINES, GIT_REPO_TYPE
from dashboard.jobs_framework import JobCommandBase
from dashboard.managers.utilities import parse_git_url, determine_git_platform


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
        instance_url, git_owner_repo = parse_git_url(repo_clone_url)
        git_platform = determine_git_platform(instance_url)
        git_owner, git_repo = git_owner_repo
        kwargs = {}
        kwargs.update(dict(no_cache_api=True))

        git_user = settings.GITHUB_USER
        if git_platform == GIT_PLATFORMS[0]:
            git_user = self.github_user

        repositories = self.api_resources.list_repos(
            git_platform, instance_url, git_user, **kwargs
        )
        for repository in repositories:
            if repository.get('name', '') == git_repo and repository.get('fork'):
                return True
        return False

    def _delete_fork(self, repo_clone_url):
        instance_url, git_owner_repo = parse_git_url(repo_clone_url)
        git_platform = determine_git_platform(instance_url)
        git_owner, git_repo = git_owner_repo
        kwargs = {}
        kwargs.update(dict(no_cache_api=True))

        git_user = settings.GITHUB_USER
        if git_platform == GIT_PLATFORMS[0]:
            git_user = self.github_user

        delete_repo_resp = self.api_resources.delete_repo(
            git_platform, instance_url, *(git_user, git_repo), **kwargs
        )
        return delete_repo_resp

    def _create_fork(self, repo_clone_url):
        instance_url, git_owner_repo = parse_git_url(repo_clone_url)
        git_platform, kwargs = determine_git_platform(instance_url), {}
        create_fork_api_response = self.api_resources.create_fork(
            git_platform, instance_url, *git_owner_repo, **kwargs
        )
        return create_fork_api_response.get("html_url", "")

    def git_repository(self, input, kwargs):
        """Clone GIT repository"""
        task_subject = "Clone Repository"
        task_log = OrderedDict()

        src_tar_dir = os.path.join(self.sandbox_path, input['package'])
        if os.path.isdir(src_tar_dir) and os.listdir(src_tar_dir):
            shutil.rmtree(src_tar_dir, ignore_errors=True)

        clone_kwargs = {}
        clone_kwargs.update(dict(config='http.sslVerify=false'))
        if kwargs.get('recursive'):
            clone_kwargs.update(dict(recursive=True))
        if kwargs.get('branch') and not kwargs.get('type') == TRANSPLATFORM_ENGINES[3]:
            clone_kwargs.update(dict(branch=kwargs['branch']))

        repo_clone_url = input['upstream_repo_url']
        if kwargs.get('type') and kwargs['type'] == GIT_REPO_TYPE[1] \
                and input.get('upstream_l10n_repo_url'):
            repo_clone_url = input['upstream_l10n_repo_url']

        if kwargs.get("fork"):
            # delete the fork if exists already
            if self._is_fork_exist(repo_clone_url):
                self._delete_fork(repo_clone_url)
            # create a new fork and proceed cloning
            fork_url = self._create_fork(repo_clone_url)
            if fork_url:
                # forked repo takes time for setting up in GitHub
                time.sleep(2)
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
            if input.get('pkg_tp_auth_token') and input['pkg_tp_auth_token'] in trace_back:
                trace_back = trace_back.replace(input['pkg_tp_auth_token'], 'XXX')
            task_log.update(self._log_task(
                input['log_f'], task_subject, 'Cloning failed. Details: %s' % trace_back
            ))
            raise Exception("Cloning '%s' branch failed. Details: %s" % (kwargs.get('branch', ''), e.stderr))
        else:
            if vars(clone_result).get('git_dir'):
                task_log.update(self._log_task(
                    input['log_f'], task_subject, os.listdir(src_tar_dir),
                    text_prefix='Cloning git repo completed.'
                ))
        return {'src_tar_dir': src_tar_dir}, {task_subject: task_log}
