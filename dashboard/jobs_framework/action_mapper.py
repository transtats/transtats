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

# Currently, it is implemented as:
# Every command has its own class under cmds folder and
#   the task gets paired with the most appropriate method therein.

import os
import difflib

from collections import OrderedDict
from inspect import getmembers, isfunction
from shutil import rmtree

# dashboard
from dashboard.jobs_framework.cmds.apply import Apply
from dashboard.jobs_framework.cmds.calculate import Calculate
from dashboard.jobs_framework.cmds.copy import Copy
from dashboard.jobs_framework.cmds.clone import Clone
from dashboard.jobs_framework.cmds.download import Download
from dashboard.jobs_framework.cmds.filter import Filter
from dashboard.jobs_framework.cmds.generate import Generate
from dashboard.jobs_framework.cmds.get import Get
from dashboard.jobs_framework.cmds.load import Load
from dashboard.jobs_framework.cmds.pullrequest import Pullrequest
from dashboard.jobs_framework.cmds.unpack import Unpack
from dashboard.jobs_framework.cmds.upload import Upload
from dashboard.jobs_framework import BaseManager

__all__ = ['ActionMapper']


class ActionMapper(BaseManager):
    """YML Parsed Objects to Actions Mapper"""
    COMMANDS = {
        'GET': Get,                     # Fetch information
        'DOWNLOAD': Download,           # Download resources
        'UNPACK': Unpack,               # Extract an archive
        'LOAD': Load,                   # Load into python object
        'FILTER': Filter,               # Filter files recursively
        'APPLY': Apply,                 # Apply patch on source tree
        'CALCULATE': Calculate,         # Do some maths/try formulae
        'CLONE': Clone,                 # Clone source repository
        'GENERATE': Generate,           # Exec commands to create
        'UPLOAD': Upload,               # Upload resources
        'COPY': Copy,                   # Copy files from one dir to another
        'PULLREQUEST': Pullrequest,     # Create and submit pull request
    }

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
                 upstream_l10n_url,
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
        self.upstream_l10n_url = upstream_l10n_url
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
        except IndexError:
            self.__log.update({"ERROR": "something failed in skip"})
        else:
            raise Exception('Action mapping failed for %s command.' % command)

    def set_actions(self):
        count = 0
        self.tasks.status = False
        current_node = self.tasks.head
        while current_node is not None:
            count += 1
            cmd = current_node.command.upper() or ''
            if cmd in self.COMMANDS:
                current_node.set_namespace(self.COMMANDS[cmd])
            available_methods = [member[0] for member in getmembers(self.COMMANDS[cmd])
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
            'pkg_downstream_name': self.pkg_downstream_name, 'repo_branch': self.repo_branch,
            'upstream_l10n_repo_url': self.upstream_l10n_url
        }

        while current_node is not None:
            if count == 0:
                current_node.input = initials
            elif current_node.previous.output:
                current_node.input = {**initials, **current_node.previous.output}
            count += 1
            current_node.output, current_node.log = getattr(
                current_node.get_namespace(),
                current_node.get_method(), self.skip
            )(current_node.get_namespace()(), current_node.input, current_node.kwargs)

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
