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

import io
import os
from shlex import split
from shutil import rmtree
from subprocess import Popen, PIPE, call
import tarfile

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# third party
import requests
import polib
from pyrpm.spec import Spec

# django
from django.conf import settings

# dashboard
from dashboard.engine.action_mapper import ActionMapper
from dashboard.engine.ds import TaskList
from dashboard.engine.parser import YMLPreProcessor, YMLJobParser
from dashboard.managers.base import BaseManager
from dashboard.managers.inventory import InventoryManager

__all__ = ['DownstreamManager']


class DownstreamManager(BaseManager):
    """
    Packages Downstream Manager
    """

    sandbox_path = 'dashboard/sandbox/'
    job_log_file = sandbox_path + 'downstream.log'
    translation_file_extension = '.po'
    trans_stats = None

    def _write_to_file(self, text_to_write):
        with open(self.job_log_file, 'a+') as the_file:
            the_file.write(text_to_write)

    def _download_srpm(self, srpm_link):
        req = requests.get(srpm_link)
        self.srpm_path = self.sandbox_path + srpm_link.split('/')[-1]
        try:
            with open(self.srpm_path, 'wb') as f:
                f.write(req.content)
                return True
        except:
            return False

    def get_latest_build(self):
        self.builds = self.api_resources.latest_build_info(
            hub_url=self.hub_url, tag=self.tag, pkg=self.package
        )
        if len(self.builds) > 0:
            self._write_to_file('\n<b>Latest Build Details</b> ...\n%s\n'
                                % str(self.builds[0]))
        else:
            self._write_to_file('\n<b>Latest Build Details</b> ...\n%s\n'
                                % 'No build details found.')

    def fetch_SRPM(self):
        """
        Locate and download required SRPM
        """
        if self.builds and len(self.builds) > 0:
            latest_build = self.builds[0]
            build_id = latest_build.get('id', 0)
            build_info = self.api_resources.get_build(hub_url=self.hub_url, build_id=build_id)
            rpms = self.api_resources.list_RPMs(hub_url=self.hub_url, build_id=build_id)
            src_rpm = [rpm for rpm in rpms if rpm.get('arch') == 'src'][0]
            self.srpm_download_url = os.path.join(
                self.api_resources.get_path_info(build=build_info),
                self.api_resources.get_path_info(srpm=src_rpm)
            ).replace('/mnt/koji', 'https://kojipkgs.fedoraproject.org')
            if self._download_srpm(self.srpm_download_url):
                self._write_to_file(
                    '\n<b>SRPM Successfully Downloaded from </b> ...\n%s\n'
                    % self.srpm_download_url
                )

    def unpack_SRPM(self):
        """
        SRPM is a headers + cpio file
            - its extraction currently is dependent on cpio command
        """
        try:
            command = "rpm2cpio " + os.path.join(
                os.path.dirname(settings.BASE_DIR), self.srpm_path
            )
            command = split(command)
            rpm2cpio = Popen(command, stdout=PIPE)
            self.extract_dir = os.path.join(self.sandbox_path, self.package)
            if not os.path.exists(self.extract_dir):
                os.makedirs(self.extract_dir)
            command = "cpio -idm -D %s" % self.extract_dir
            command = split(command)
            call(command, stdin=rpm2cpio.stdout)
            self._write_to_file(
                '\n<b>SRPM Extracted Successfully</b> ...\n%s\n'
                % " \n".join(os.listdir(self.extract_dir))
            )
        except Exception as e:
            self._write_to_file(
                '\n<b>SRPM Extraction Failed</b> ...\n%s\n' % e
            )

    def load_spec_file(self):
        """
        locate and load spec file
        """
        try:
            for root, dirs, files in os.walk(self.extract_dir):
                for file in files:
                    if file.endswith('.spec'):
                        self.spec_file = os.path.join(root, file)
                    zip_ext = ('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')
                    if file.endswith(zip_ext):
                        self.src_tar_file = os.path.join(root, file)
            self.spec_obj = Spec.from_file(self.spec_file)
            self._write_to_file(
                '\n<b>Spec file loaded, Sources</b> ...\n%s\n'
                % " \n".join(self.spec_obj.sources)
            )
        except Exception as e:
            self._write_to_file(
                '\n<b>Loading Spec file Failed</b> ...\n%s\n' % e
            )

    def untar_tarball(self):
        """
        Untar source tarball
        """
        try:
            with tarfile.open(self.src_tar_file) as tar_file:
                tar_members = tar_file.getmembers()
                if len(tar_members) > 0:
                    self.src_tar_dir = os.path.join(
                        self.extract_dir, tar_members[0].get_info().get('name', '')
                    )
                tar_file.extractall(path=self.extract_dir)
            self._write_to_file(
                '\n<b>Tarball Extracted Successfully</b> ...\n%s\n'
                % " \n".join(os.listdir(self.src_tar_dir))
            )
        except Exception as e:
            self._write_to_file(
                '\n<b>Tarball Extraction Failed</b> ...\n%s\n' % e
            )

    def filter_translations(self):
        """
        Filter PO files from tarball
        """
        try:
            self.trans_files = []
            for root, dirs, files in os.walk(self.src_tar_dir):
                    for file in files:
                        if file.endswith(self.translation_file_extension):
                            self.trans_files.append(os.path.join(root, file))

            self._write_to_file(
                '\n<b>%s PO files filtered</b> ...\n%s\n' % (len(self.trans_files), " \n".join(self.trans_files))
            )
        except Exception as e:
            self._write_to_file('\n<b>Something went wrong in filtering PO files</b> ...\n%s\n' % e)

    def calculate_stats(self):
        """
        Calculate stats from filtered translations
        """
        try:
            self.trans_stats = {}
            for po_file in self.trans_files:
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

            self._write_to_file(
                '\n<b>Calculated Stats</b> ...\n%s\n' % str(self.trans_stats)
            )
        except Exception as e:
            self._write_to_file('\n<b>Something went wrong in calculating stats</b> ...\n%s\n' % e)

    def skip(self):
        pass

    def _bootstrap(self, build_system):
        inventory_manager = InventoryManager()
        release_streams = \
            inventory_manager.get_release_streams(built=build_system)
        release_stream = release_streams.get()
        if release_stream:
            self.hub_url = release_stream.relstream_server

    def execute_job(self):
        """
        1. PreProcess YML and replace variables with input_values
            - Example: %PACKAGE_NAME%
        2. Parse processed YML and build Job object
        3. Select data structure for tasks and instantiate one
            - Example: Linked list should be used for sequential tasks
        3. Discover namespace and method for each task and fill in TaskNode
        4. Perform actions (execute tasks) and return responses
        """

        yml_preprocessed = YMLPreProcessor(self.YML_FILE, **{
            'PACKAGE_NAME': self.PACKAGE_NAME, 'BUILD_TAG': self.BUILD_TAG
        }).output

        if yml_preprocessed:
            yml_job = YMLJobParser(yml_stream=io.StringIO(yml_preprocessed))
            self.package = yml_job.package
            self.tag = yml_job.tags[0] if len(yml_job.tags) > 0 else None
            self._bootstrap(yml_job.buildsys)
            # for sequential jobs, tasks should be pushed to linked list
            # and output of previous task should be input for next task
            if yml_job.execution == 'sequential':
                self.tasks_ds = TaskList()

            if os.path.exists(self.job_log_file):
                os.remove(self.job_log_file)
            if self.tag and self.package and self.hub_url:
                tasks = yml_job.tasks
                for task in tasks:
                    self.tasks_ds.add_task(task)

                steps = ActionMapper(self.tasks_ds).actions
                for step in steps:
                    getattr(self, step, self.skip)()

    def clean_workspace(self):
        """
        Remove downloaded SRPM, and its stuffs
        """
        try:
            os.remove(self.job_log_file)
            os.remove(self.srpm_path)
            rmtree(self.extract_dir, ignore_errors=True)
        except OSError as e:
            self.app_logger('ERROR', "Failed to clean sandbox!")
