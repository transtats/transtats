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

import json
from git import Repo
from collections import OrderedDict
from urllib.parse import urlparse
from django.conf import settings

from dashboard.constants import GIT_PLATFORMS, RH_EMAIL_ADDR, GIT_REPO_TYPE
from dashboard.managers.utilities import parse_git_url, determine_git_platform

from dashboard.jobs_framework import JobCommandBase


class Pullrequest(JobCommandBase):
    """Handles all operations for PULLREQUEST Command"""

    def git_repo(self, input, kwargs):
        """Prepare merge request and submit"""

        task_subject = "Pull Request"
        task_log = OrderedDict()

        repo_clone_url = input['upstream_repo_url']
        if kwargs.get('type') and kwargs['type'] == GIT_REPO_TYPE[1] \
                and input.get('upstream_l10n_repo_url'):
            repo_clone_url = input['upstream_l10n_repo_url']
        instance_url, git_owner_repo = parse_git_url(repo_clone_url)
        git_platform = determine_git_platform(instance_url)

        # Prepare Merge Request
        modified_repo = Repo(input['src_tar_dir'])

        git_user = settings.GITHUB_USER
        if git_platform == GIT_PLATFORMS[0]:
            git_user = self.github_user

        modified_repo.config_writer().set_value(
            "user", "name", git_user).release()
        modified_repo.config_writer().set_value(
            "user", "email", RH_EMAIL_ADDR).release()
        for copied_file in input['copied_files']:
            modified_repo.index.add(copied_file)
        commit_object = modified_repo.index.commit("Add or Update Translations")

        if commit_object and commit_object.hexsha:
            task_log.update(self._log_task(
                input['log_f'], task_subject, input['copied_files'],
                text_prefix=f"Files have been committed. SHA: {commit_object.hexsha}"
            ))

        # set git push origin url
        git_api_token = ""
        if git_platform == GIT_PLATFORMS[0]:
            git_api_token = settings.GITHUB_TOKEN
        origin_urls = list(modified_repo.remotes.origin.urls)
        if not origin_urls:
            raise Exception('Push URL cannot be blank.')
        origin_url = origin_urls[0]
        origin_url_parts = urlparse(origin_url)
        origin_url_with_token = "{}://{}:x-oauth-basic@{}{}".format(
            origin_url_parts.scheme, git_api_token, origin_url_parts.netloc, origin_url_parts.path
        )
        modified_repo.remotes.origin.set_url(origin_url_with_token)

        # push contents to GitHub
        push_results = modified_repo.remotes.origin.push()
        push_summary = push_results[0].summary if push_results else ""

        if push_summary:
            task_log.update(self._log_task(
                input['log_f'], task_subject, f"Files have been pushed to {git_platform}."
            ))

        # Submit a Git Pull Request
        pull_request_api_payload = {}
        if git_platform == GIT_PLATFORMS[0]:
            pull_request_api_payload['title'] = commit_object.summary
            pull_request_api_payload['body'] = "Translations for {} languages.".format(
                ", ".join(input['ci_target_langs'])
            )
            pull_request_branch_from = modified_repo.active_branch.name
            pull_request_api_payload['head'] = "{}:{}".format(
                self.github_user, pull_request_branch_from
            )
            pull_request_branch_to = kwargs['branch']
            pull_request_api_payload['base'] = pull_request_branch_to

        kwargs = dict()
        kwargs['data'] = json.dumps(pull_request_api_payload)
        kwargs.update(dict(no_cache_api=True))
        api_resp_status, create_pull_request_resp = self.api_resources.create_merge_request(
            git_platform, instance_url, *git_owner_repo, **kwargs
        )

        pull_request_url = ''
        if api_resp_status:
            pull_request_url = create_pull_request_resp['html_url']
            task_log.update(self._log_task(
                input['log_f'], task_subject, f"Pull request has been created. Visit {pull_request_url}"
            ))
        else:
            create_pull_request_failure_reason = create_pull_request_resp
            if git_platform == GIT_PLATFORMS[0]:
                try:
                    create_pull_request_failure_reason = create_pull_request_resp['errors'][0]['message']
                except (IndexError, KeyError):
                    task_log.update(self._log_task(
                        input['log_f'], task_subject, "GitHub response parsing failed."
                    ))

            task_log.update(self._log_task(
                input['log_f'], task_subject, f"Pull request could not be created. "
                                              f"{create_pull_request_failure_reason}"
            ))
        return {'pull_request_url': pull_request_url}, {task_subject: task_log}
