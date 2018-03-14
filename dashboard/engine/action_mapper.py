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
# todo - make tasks more generic
#   like: in filter cmd, extension can be passed as param

import os
import difflib
import requests
import polib
import tarfile
from shlex import split
from shutil import copy2, rmtree
from pyrpm.spec import Spec
from subprocess import Popen, PIPE, call
from inspect import getmembers, isfunction
# dashboard
from dashboard.constants import BUILD_SYSTEMS
from dashboard.managers.base import BaseManager

__all__ = ['ActionMapper']


class JobCommandBase(BaseManager):

    def __init__(self):

        kwargs = {
            'sandbox_path': 'dashboard/sandbox/',
        }
        super(JobCommandBase, self).__init__(**kwargs)

    def _write_to_file(self, log_f, text_to_write):
        with open(log_f, 'a+') as the_file:
            the_file.write(text_to_write)


class Get(JobCommandBase):
    """
    Handles all operations for GET Command
    """
    def latest_build_info(self, input):
        """
        Fetch latest build info from koji
        """
        builds = self.api_resources.build_info(
            hub_url=input.get('hub_url'), tag=input.get('build_tag'),
            pkg=input.get('package')
        )
        if len(builds) > 0:
            self._write_to_file(input['log_f'],
                                '\n<b>Latest Build Details</b> ...\n%s\n'
                                % str(builds[0]))
        else:
            self._write_to_file(input['log_f'],
                                '\n<b>Latest Build Details</b> ...\n%s\n'
                                % 'No build details found for %s.'
                                % input.get('build_tag'))
        return {'builds': builds}


class Download(JobCommandBase):

    def _download_srpm(self, srpm_link):
        req = requests.get(srpm_link)
        srpm_path = self.sandbox_path + srpm_link.split('/')[-1]
        try:
            with open(srpm_path, 'wb') as f:
                f.write(req.content)
                return srpm_path
        except:
            return ''

    def srpm(self, input):
        builds = input.get('builds')

        pkgs_download_server_url = ''
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
            srpm_downloaded_path = self._download_srpm(srpm_download_url)
            if srpm_downloaded_path:
                self._write_to_file(
                    input['log_f'],
                    '\n<b>SRPM Successfully Downloaded from </b> ...\n%s\n'
                    % srpm_download_url
                )
            else:
                self._write_to_file(
                    input['log_f'],
                    '\n<b>SRPM could not be downloaded from </b> ...\n%s\n'
                    % srpm_download_url
                )
            return {'srpm_path': srpm_downloaded_path}


class Unpack(JobCommandBase):

    def srpm(self, input):
        """
        SRPM is a headers + cpio file
            - its extraction currently is dependent on cpio command
        """
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
            self._write_to_file(
                input['log_f'], '\n<b>SRPM Extraction Failed</b> ...\n%s\n' % e
            )
        else:
            self._write_to_file(
                input['log_f'],
                '\n<b>SRPM Extracted Successfully</b> ...\n%s\n'
                % " \n".join(os.listdir(extract_dir))
            )
            return {'extract_dir': extract_dir}

    def _determine_tar_dir(self, params):
        for root, dirs, files in os.walk(params['extract_dir']):
            for directory in dirs:
                if directory == params['package']:
                    return os.path.join(root, directory)
            return root

    def tarball(self, input):
        """
        Untar source tarball
        """
        try:
            src_tar_dir = None
            with tarfile.open(input['src_tar_file']) as tar_file:
                tar_members = tar_file.getmembers()
                if len(tar_members) > 0:
                    src_tar_dir = os.path.join(
                        input['extract_dir'], tar_members[0].get_info().get('name', '')
                    )
                tar_file.extractall(path=input['extract_dir'])
        except Exception as e:
            self._write_to_file(
                input['log_f'], '\n<b>Tarball Extraction Failed</b> ...\n%s\n' % e
            )
        else:
            if not os.path.isdir(src_tar_dir):
                src_tar_dir = self._determine_tar_dir(input)
            self._write_to_file(
                input['log_f'],
                '\n<b>Tarball Extracted Successfully</b> ...\n%s\n'
                % " \n".join(os.listdir(src_tar_dir))
            )
            return {'src_tar_dir': src_tar_dir}


class Load(JobCommandBase):

    def spec_file(self, input):
        """
        locate and load spec file
        """
        try:
            spec_file = ''
            src_tar_file = None
            for root, dirs, files in os.walk(input['extract_dir']):
                for file in files:
                    if file.endswith('.spec') and not file.startswith('.'):
                        spec_file = os.path.join(root, file)
                    zip_ext = ('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')
                    if file.endswith(zip_ext):
                        src_tar_file = os.path.join(root, file)
            spec_obj = Spec.from_file(spec_file)
        except Exception as e:
            self._write_to_file(
                input['log_f'], '\n<b>Loading Spec file Failed</b> ...\n%s\n' % e
            )
        else:
            self._write_to_file(
                input['log_f'],
                '\n<b>Spec file loaded, Sources</b> ...\n%s\n'
                % " \n".join(spec_obj.sources)
            )
            return {
                'spec_file': spec_file, 'src_tar_file': src_tar_file,
                'spec_obj': spec_obj
            }


class Apply(JobCommandBase):

    def patch(self, input):
        tar_dir = {'src_tar_dir': input['src_tar_dir']}
        try:
            patches = []
            for root, dirs, files in os.walk(input['extract_dir']):
                    for file in files:
                        if file.endswith('.patch'):
                            patches.append(os.path.join(root, file))

            if not patches:
                self._write_to_file(input['log_f'], '\n<b>No patches found.</b>\n')
                return tar_dir

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
            self._write_to_file(
                input['log_f'], '\n<b>Something went wrong in applying patches</b> ...\n%s\n' % e
            )
        else:
            os.chdir(input['base_dir'])
            self._write_to_file(
                input['log_f'], '\n<b>%s patches applied</b> ...\n%s\n' % (len(patches), " \n".join(patches))
            )
        finally:
            return tar_dir


class Filter(JobCommandBase):

    def po_files(self, input):
        """
        Filter PO files from tarball
        """
        try:
            trans_files = []
            for root, dirs, files in os.walk(input['src_tar_dir']):
                    for file in files:
                        if file.endswith('.po'):
                            trans_files.append(os.path.join(root, file))
        except Exception as e:
            self._write_to_file(
                input['log_f'], '\n<b>Something went wrong in filtering PO files</b> ...\n%s\n' % e
            )
        else:
            self._write_to_file(
                input['log_f'],
                '\n<b>%s PO files filtered</b> ...\n%s\n' % (len(trans_files), " \n".join(trans_files))
            )
            return {'trans_files': trans_files}


class Calculate(JobCommandBase):

    def stats(self, input):
        """
        Calculate stats from filtered translations
        """
        try:
            trans_stats = {}
            trans_stats['id'] = input.get('build_system', '') + ' - ' + input.get('build_tag', '')
            trans_stats['stats'] = []
            for po_file in input['trans_files']:
                po = polib.pofile(po_file)
                if po:
                    temp_trans_stats = {}
                    temp_trans_stats['unit'] = "MESSAGE"
                    locale = po_file.split('/')[-1].split('.')[0]
                    temp_trans_stats['locale'] = locale
                    temp_trans_stats['translated'] = len(po.translated_entries())
                    temp_trans_stats['untranslated'] = len(po.untranslated_entries())
                    temp_trans_stats['fuzzy'] = len(po.fuzzy_entries())
                    temp_trans_stats['total'] = len(po.translated_entries()) + \
                        len(po.untranslated_entries()) + len(po.fuzzy_entries())
                    trans_stats['stats'].append(temp_trans_stats.copy())
        except Exception as e:
            self._write_to_file(
                input['log_f'], '\n<b>Something went wrong in calculating stats</b> ...\n%s\n' % e
            )
        else:
            self._write_to_file(
                input['log_f'], '\n<b>Calculated Stats</b> ...\n%s\n' % str(trans_stats)
            )
            return {'trans_stats': trans_stats}


class ActionMapper(BaseManager):
    """
    YML Parsed Objects to Actions Mapper
    """
    COMMANDS = [
        'GET',          # Call some method
        'DOWNLOAD',     # Download some resource
        'UNPACK',       # Extract an archive
        'LOAD',         # Load into python object
        'FILTER',       # Filter files recursively
        'APPLY',        # Apply patch on source tree
        'CALCULATE'     # Do some maths/try formulae
    ]

    def __init__(self,
                 tasks_structure,
                 build_tag,
                 package,
                 server_url,
                 job_base_dir,
                 build_system,
                 job_log_file):
        super(ActionMapper, self).__init__()
        self.tasks = tasks_structure
        self.tag = build_tag
        self.pkg = package
        self.hub = server_url
        self.base_dir = job_base_dir
        self.buildsys = build_system
        self.log_f = job_log_file
        self.cleanup_resources = {}
        self.__stats = None

    def skip(self, abc, xyz):
        pass

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
            probable_method = difflib.get_close_matches(
                current_node.task.lower(), available_methods
            )
            if isinstance(probable_method, list) and len(probable_method) > 0:
                current_node.set_method(probable_method[0])
            current_node = current_node.next

    def execute_tasks(self):
        count = 0
        current_node = self.tasks.head
        initials = {
            'build_tag': self.tag, 'package': self.pkg, 'hub_url': self.hub,
            'base_dir': self.base_dir, 'build_system': self.buildsys, 'log_f': self.log_f
        }

        while current_node is not None:
            if count == 0:
                current_node.input = initials
            elif current_node.previous.output:
                current_node.input = {**initials, **current_node.previous.output}
            count += 1
            current_node.output = getattr(
                eval(current_node.get_namespace()),
                current_node.get_method(), self.skip
            )(eval(current_node.get_namespace())(), current_node.input)

            self.tasks.status = True if current_node.output else False
            if current_node.output and 'builds' in current_node.output:
                if not current_node.output['builds']:
                    break
            if current_node.output and 'srpm_path' in current_node.output:
                d = {'srpm_path': current_node.output.get('srpm_path')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and 'extract_dir' in current_node.output:
                d = {'extract_dir': current_node.output.get('extract_dir')}
                initials.update(d)
                self.cleanup_resources.update(d)
            if current_node.output and 'trans_stats' in current_node.output:
                self.__stats = current_node.output.get('trans_stats')
            current_node = current_node.next

    @property
    def result(self):
        return self.__stats

    @property
    def status(self):
        return self.tasks.status

    def clean_workspace(self):
        """
        Remove downloaded SRPM, and its stuffs
        """
        try:
            if self.cleanup_resources.get('srpm_path'):
                os.remove(self.cleanup_resources.get('srpm_path'))
            if self.cleanup_resources.get('extract_dir'):
                rmtree(self.cleanup_resources.get('extract_dir'), ignore_errors=True)
        except OSError as e:
            self.app_logger('ERROR', "Failed to clean sandbox! Due to %s" % e)
