# Copyright 2022 Red Hat, Inc.
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
import re
import polib
import shutil
from typing import Callable


class LanguageFormatterMixin(object):
    """Language Formatter Mixin"""

    comma_delimiter = ","

    def format_target_langs(self, langs):
        target_langs = []
        if isinstance(langs, (list, tuple)):
            target_langs = langs
        elif isinstance(langs, str):
            target_langs = langs.split(self.comma_delimiter) \
                if self.comma_delimiter in langs \
                else [langs]
        return target_langs

    def format_locale(self, locale, alias_zh=False):

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


class JobHooksMixin(object):
    """
    Job Hooks

    fn name is the hook name, which can be used in YAML
    params: input: dict, log_task_fn: Callable, task_log: dict
        should be constant for all the hooks
    """

    language_formatter = LanguageFormatterMixin()

    def copy_template_for_target_langs(self, input: dict, log_task_fn: Callable, task_log: dict) -> None:
        """
        Pre hook: copy_template_for_target_langs
            - copy a template for all the target langs
        """
        task_subject = "Upload Prehook: copy_template_for_target_langs"

        if not input.get('trans_files'):
            task_log.update(log_task_fn(
                input['log_f'], task_subject, 'No template found.')
            )
            return

        first_trans_file = input['trans_files'][0]
        if isinstance(first_trans_file, str) and \
                'template' in first_trans_file.lower() or 'pot' in first_trans_file.lower():
            translation_template = first_trans_file
            task_log.update(log_task_fn(
                input['log_f'], task_subject, translation_template, text_prefix='Template collected'
            ))

            target_langs = []
            if input.get('ci_target_langs'):
                target_langs = self.language_formatter.format_target_langs(langs=input['ci_target_langs'])

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

            task_log.update(log_task_fn(
                input['log_f'], task_subject, '{} files copied for {}.'.format(
                    len(target_langs), ", ".join(target_langs))
            ))

    def simplify_plural_forms_in_po_header(self, input: dict, log_task_fn: Callable, task_log: dict) -> None:
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
                task_log.update(log_task_fn(input['log_f'], task_subject, str(e)))
                continue
            except Exception as e:
                task_log.update(log_task_fn(
                    input['log_f'], task_subject, f'{trans_file} is not a PO file. Details {e}')
                )
                continue
            else:
                po_file.metadata['Plural-Forms'] = simple_plural_form
                po_file.save()
