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
try:
    import koji
except Exception as e:
    raise Exception("koji could not be imported, details: %s" % e)
from shlex import split
from shutil import rmtree
from subprocess import Popen, PIPE, call
import tarfile
from yaml import load, YAMLError
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
from dashboard.managers.base import BaseManager

__all__ = ['DownstreamManager']


class KojiResources(object):
    """
    Koji Resources
    """

    def __init__(self):
        """
        Setup self, for koji_resources
        """
        print("Koji Version: %s" % koji.API_VERSION)
        self.server = "https://koji.fedoraproject.org/kojihub/"
        self.session = koji.ClientSession(self.server)
        # self.session.gssapi_login()

    def establish_kerberos_ticket(self):
        """
        Get kerberos ticket in-place
        """
        userid = "transtats"
        realm = "FEDORAPROJECT.ORG"

        kinit = '/usr/bin/kinit'
        kinit_args = [kinit, '%s@%s' % (userid, realm)]
        kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        kinit.stdin.write(b'secret')
        kinit.wait()


class YMLPreProcessor(object):
    """
    Load and form YML, fill values
    """

    delimiter = '%'

    def __init__(self, YML_Source, **vars):
        for attrib, value in vars.items():
            setattr(self, str(attrib), value)
        self.YML = YML_Source
        self.variables = [segment for segment in self.YML.split()
                          if segment.startswith(self.delimiter) and
                          segment.endswith(self.delimiter)]

    @property
    def output(self):
        in_process_text = self.YML
        for variable in self.variables:
            in_process_text = in_process_text.replace(
                variable, getattr(self, variable.replace(self.delimiter, ''), '')
            )
        return in_process_text


class YMLJobParser(object):
    """
    Parse YML and build objects
    """
    test_yml_path = 'dashboard/tests/testdata/test.yml'

    def __init__(self, yml_stream=None):

        stream = yml_stream if yml_stream else open(self.test_yml_path)
        try:
            parsed_data = load(stream)
        except YAMLError as exc:
            # log error
            pass
        else:
            if isinstance(parsed_data, dict):
                self.data = parsed_data.get('job', {})

    @property
    def buildsys(self):
        return self.data.get('buildsys', '')

    @property
    def exception(self):
        return self.data.get('exception', '')

    @property
    def job_name(self):
        return self.data.get('name', '')

    @property
    def job_type(self):
        return self.data.get('type', '')

    @property
    def package(self):
        return self.data.get('package', '')

    @property
    def return_type(self):
        return self.data.get('return_type', '')

    @property
    def tags(self):
        return self.data.get('tags', [])

    @property
    def tasks(self):
        return self.data.get('tasks', [])


class ActionMapper(object):
    """
    YML Parsed Objects to Actions Mapper
    """
    KEYWORDS = [
        'GET',      # Call some koji method
        'FETCH'     # Download some resource
    ]

    def __init__(self, tasks):
        self.tasks = tasks

    @property
    def actions(self):
        actions = []
        actions_dict = {
            'GET latest builds': 'get_latest_build',
            'FETCH SRPM': 'fetch_SRPM',
            'Unpack SRPM': 'unpack_SRPM',
            'Load Spec File': 'load_spec_file',
            'Untar tarball': 'untar_tarball',
            'Filter PO files': 'filter_translations',
            'Calculate Stats': 'calculate_stats'
        }
        for action in self.tasks:
            executable = actions_dict.get(action)
            if executable:
                actions.append(executable)
        return actions


class DownstreamManager(BaseManager):
    """
    Packages Downstream Manager
    """

    koji_resources = KojiResources()
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
        self.builds = self.koji_resources.session.getLatestBuilds(
            self.tag, package=self.package)
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
            build_info = self.koji_resources.session.getBuild(build_id)
            rpms = self.koji_resources.session.listRPMs(buildID=build_id)
            src_rpm = [rpm for rpm in rpms if rpm.get('arch') == 'src'][0]
            self.srpm_download_url = os.path.join(
                koji.pathinfo.build(build_info), koji.pathinfo.rpm(src_rpm)
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

    def lets_do_some_stuff(self):
        """
        1. Process YML and fill values
        2. Parse processed YML and build objects
        3. Map objects to respective actions
        4. Perform actions and return responses
        """

        # active_repos = self.koji_resources.session.getActiveRepos()
        # if active_repos:
        #     self._write_to_file("Active Repos: %s\n" % ", ".join(
        #         set([repo['tag_name'] for repo in active_repos])))

        yml_preprocessed = YMLPreProcessor(self.YML_FILE, **{
            'PACKAGE_NAME': self.PACKAGE_NAME, 'BUILD_TAG': self.BUILD_TAG
        }).output

        if yml_preprocessed:
            yml_job = YMLJobParser(yml_stream=io.StringIO(yml_preprocessed))
            self.package = yml_job.package
            self.tag = yml_job.tags[0] if len(yml_job.tags) > 0 else None

            if os.path.exists(self.job_log_file):
                os.remove(self.job_log_file)
            if self.tag and self.package:
                tasks = yml_job.tasks
                steps = ActionMapper(tasks).actions
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
