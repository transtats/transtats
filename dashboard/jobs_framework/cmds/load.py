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
from pyrpm.spec import Spec
from collections import OrderedDict

from dashboard.converters.specfile import RpmSpecFile
from dashboard.jobs_framework import JobCommandBase


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
                    zip_ext = ('.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.gem')
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
                    "%{realversion}": spec_obj.version,
                    "%{gem_name}": getattr(spec_obj, "gem_name", ''),
                    "%{?prerelease}": "." + getattr(spec_obj, "prereleasesource", ''),
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
