# Copyright 2016 Red Hat, Inc.
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

# django
from django import forms
from django.contrib import admin

# dashboard
from dashboard.forms import TextArrayField
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, RELSTREAM_SLUGS,
    TRANSIFEX_SLUGS, ZANATA_SLUGS,
)
from dashboard.models import (
    Languages, LanguageSet, TransPlatform, ReleaseStream,
    StreamBranches, Packages
)
from dashboard.managers.inventory import InventoryManager

ENGINE_CHOICES = tuple([(engine, engine.upper())
                        for engine in TRANSPLATFORM_ENGINES])

RELSTR_CHOICES = tuple([(relstream, relstream)
                        for relstream in RELSTREAM_SLUGS])

all_platform_slugs = []
all_platform_slugs.extend(TRANSIFEX_SLUGS)
all_platform_slugs.extend(ZANATA_SLUGS)
SLUG_CHOICES = tuple([(slug, slug) for slug in all_platform_slugs])


class TransPlatformAdminForm(forms.ModelForm):
    engine_name = forms.ChoiceField(
        choices=ENGINE_CHOICES, label="Platform Engine",
        help_text="Platform engine helps system to determine specific API/tasks."
    )

    platform_slug = forms.ChoiceField(
        choices=SLUG_CHOICES, label="Platform SLUG",
        help_text="Please identify SLUG carefully. Example: ZNTAPUB should be for zanata public instance.",
    )


class ReleaseStreamAdminForm(forms.ModelForm):
    relstream_slug = forms.ChoiceField(
        choices=RELSTR_CHOICES, label="Release Stream SLUG",
        help_text="System identifies release stream by this SLUG.",
    )


class LanguageSetAdminForm(forms.ModelForm):

    locale_choices = ()

    def __init__(self, *args, **kwargs):
        inventory_manager = InventoryManager()
        self.locale_choices = tuple([(locale.locale_id, locale.lang_name)
                                     for locale in inventory_manager.get_locales()])
        super(LanguageSetAdminForm, self).__init__(*args, **kwargs)
        self.fields['locale_ids'].choices = self.locale_choices

    locale_ids = TextArrayField(
        label='Select Locales', widget=forms.CheckboxSelectMultiple,
        choices=locale_choices, help_text="Selected locales will be included."
    )


class StreamBranchesAdminForm(forms.ModelForm):

    lang_set_choices = ()

    def __init__(self, *args, **kwargs):
        inventory_manager = InventoryManager()
        lang_sets = inventory_manager.get_langsets(['lang_set_slug', 'lang_set_name'])
        self.lang_set_choices = tuple([(lang_set.lang_set_slug, lang_set.lang_set_name)
                                       for lang_set in lang_sets])
        super(StreamBranchesAdminForm, self).__init__(*args, **kwargs)
        self.fields['lang_set'].choices = self.lang_set_choices

    lang_set = forms.ChoiceField(
        choices=lang_set_choices, label="Language Set",
        help_text="Select language set to link with this branch.",
    )


@admin.register(Languages)
class LanguagesAdmin(admin.ModelAdmin):
    search_fields = ('lang_name', )


@admin.register(LanguageSet)
class LanguageSetAdmin(admin.ModelAdmin):
    form = LanguageSetAdminForm
    search_fields = ('lang_set_name', )


@admin.register(TransPlatform)
class TransPlatformAdmin(admin.ModelAdmin):
    form = TransPlatformAdminForm
    exclude = ('projects_json', 'projects_lastupdated')
    search_fields = ('subject', )


@admin.register(ReleaseStream)
class ReleaseStreamAdmin(admin.ModelAdmin):
    form = ReleaseStreamAdminForm
    search_fields = ('relstream_name', )


@admin.register(StreamBranches)
class StreamBranchesAdmin(admin.ModelAdmin):
    form = StreamBranchesAdminForm
    search_fields = ('relbranch_slug', )
    exclude = ('relstream_slug', 'created_on', 'schedule_json')


@admin.register(Packages)
class PackagesAdmin(admin.ModelAdmin):
    search_fields = ('package_name', )
    exclude = ('package_details_json', 'details_json_lastupdated',
               'package_name_mapping', 'release_branch_mapping',
               'mapping_lastupdated', 'transtats_lastupdated')
