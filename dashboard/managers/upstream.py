# Copyright 2017 Red Hat, Inc.
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
from collections import OrderedDict
from datetime import datetime
from shutil import rmtree

from git import Repo
import polib

from django.utils import timezone

from dashboard.constants import TS_JOB_TYPES
from dashboard.managers.base import BaseManager
from dashboard.managers.jobs import JobManager
from dashboard.models import Packages


__all__ = ['UpstreamManager']


class UpstreamManager(BaseManager):
    """
    Packages Upstream (Source Tree) Manager

    SCM is limited to Git and format is limited to PO files
    - may be expand scm from git to hg, svn, bzr and other
    - may be expand format from PO to ini, ts, bundle, resx etc
    """

    task_data = None
    trans_stats = None

    def __init__(self, pkg, repo_url, sandbox, t_ext):
        """
        Upstream manager constructor
        """
        file_ext = t_ext if t_ext.startswith('.') else '.' + t_ext

        kwargs = {
            'package_name': pkg,
            'upstream_repo_url': repo_url,
            'sandbox_path': os.path.join(sandbox, pkg),
            'translation_file_extension': file_ext.lower()
        }
        super(UpstreamManager, self).__init__(**kwargs)
        self.job_manager = JobManager(TS_JOB_TYPES[2])
        self.job_manager.job_remarks = self.package_name
        self.task_data = {}
        self.trans_stats = {}

    def syncupstream_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.job_manager.create_job():
            return self.job_manager.uuid
        return None

    def upstream_trans_stats(self):
        """
        Run in sequential steps
        """
        get_stats_first = (
            self.clone_git_repo,
            self.filter_files_collect_stats
        )

        [method() for method in get_stats_first]

        if self.trans_stats:
            self.save_in_db()
        else:
            self.job_manager.job_result = False

        wrap_up = (
            self.clean_workspace,
            self.job_manager.mark_job_finish,
        )

        [method() for method in wrap_up]
        return self.job_manager.job_result

    def clone_git_repo(self):
        """
        Clone upstream git repo to local sandbox path
        """
        SUBJECT = "Clone Repository"
        self.job_manager.log_json[SUBJECT] = OrderedDict()

        try:
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): "Start cloning git repository.."}
            )
            clone_result = Repo.clone_from(self.upstream_repo_url, self.sandbox_path)
        except Exception as e:
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): 'Cloning failed. Details: ' + str(e)}
            )
        else:
            if vars(clone_result).get('git_dir'):
                self.job_manager.log_json[SUBJECT].update(
                    {str(datetime.now()): "Cloning git repo completed."}
                )
                self.task_data.update(vars(clone_result).copy())
                self.job_manager.job_result = True

    def filter_files_collect_stats(self):
        """
        It collects translation stats for all available locale
        """
        SUBJECT = "Filter files and Collect Stats"
        self.job_manager.log_json[SUBJECT] = OrderedDict()

        trans_files = []
        if self.sandbox_path in self.task_data.get('working_dir', {}):
            for root, dirs, files in os.walk(self.sandbox_path):
                for file in files:
                    if file.endswith(self.translation_file_extension):
                        trans_files.append(os.path.join(root, file))

        self.job_manager.log_json[SUBJECT].update(
            {str(datetime.now()): "%s %s files filtered." % (
                str(len(trans_files)), self.translation_file_extension[1:]
            )}
        )

        for po_file in trans_files:
            po = polib.pofile(po_file)
            if po:
                temp_trans_stats = {}
                locale = po_file.split('/')[-1].split('.')[0]
                temp_trans_stats[locale] = {}
                temp_trans_stats[locale]['translated'] = len(po.translated_entries())
                temp_trans_stats[locale]['untranslated'] = len(po.untranslated_entries())
                temp_trans_stats[locale]['fuzzy'] = len(po.fuzzy_entries())
                temp_trans_stats[locale]['translated_percent'] = po.percent_translated()
                self.trans_stats.update(temp_trans_stats.copy())

        if self.trans_stats:
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): "Locale wise translation stats collected for " + self.package_name + "."}
            )
            self.job_manager.job_result = True

    def save_in_db(self):
        """
        Save translation stats in db
        """
        SUBJECT = "Save in DB"
        self.job_manager.log_json[SUBJECT] = OrderedDict()

        try:
            Packages.objects.filter(package_name=self.package_name).update(
                upstream_latest_stats=self.trans_stats,
                upstream_lastupdated=timezone.now()
            )
        except Exception as e:
            self.job_manager.job_result = False
            err_msg = "Package update failed, details: " + str(e)
            self.app_logger('ERROR', err_msg)
            self.job_manager.log_json[SUBJECT].update({str(datetime.now()): err_msg})
        else:
            self.job_manager.job_result = True
            self.job_manager.log_json[SUBJECT].update(
                {str(datetime.now()): "Upstream stats saved in db."}
            )

    def clean_workspace(self):
        """
        Remove sandbox_path
        """
        try:
            rmtree(self.sandbox_path, ignore_errors=True)
        except OSError as e:
            self.app_logger('ERROR', "Failed to clean sandbox!")
