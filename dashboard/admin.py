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
    TRANSIFEX_SLUGS, ZANATA_SLUGS, DAMNEDLIES_SLUGS
)
from dashboard.models import (
    Language, LanguageSet, Platform, Product, Release, Package, Visitor
)
from dashboard.managers.inventory import InventoryManager

ENGINE_CHOICES = tuple([(engine, engine.upper())
                        for engine in TRANSPLATFORM_ENGINES])

RELSTR_CHOICES = tuple([(relstream, relstream)
                        for relstream in RELSTREAM_SLUGS])

all_platform_slugs = []
all_platform_slugs.extend(TRANSIFEX_SLUGS)
all_platform_slugs.extend(ZANATA_SLUGS)
all_platform_slugs.extend(DAMNEDLIES_SLUGS)
SLUG_CHOICES = tuple([(slug, slug) for slug in all_platform_slugs])


class PlatformAdminForm(forms.ModelForm):
    engine_name = forms.ChoiceField(
        choices=ENGINE_CHOICES, label="Platform Engine",
        help_text="Platform engine helps system to determine specific API/tasks."
    )

    platform_slug = forms.ChoiceField(
        choices=SLUG_CHOICES, label="Platform SLUG",
        help_text="Please identify SLUG carefully. Example: ZNTAPUB should be for zanata public instance.",
    )


class ProductAdminForm(forms.ModelForm):
    product_slug = forms.ChoiceField(
        choices=RELSTR_CHOICES, label="Product SLUG",
        help_text="System identifies product by this SLUG.",
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


@admin.register(Language)
class LanguagesAdmin(admin.ModelAdmin):
    search_fields = ('lang_name', )


@admin.register(LanguageSet)
class LanguageSetAdmin(admin.ModelAdmin):
    form = LanguageSetAdminForm
    search_fields = ('lang_set_name', )


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    form = PlatformAdminForm
    exclude = ('projects_json_str', 'projects_last_updated')
    search_fields = ('subject', )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    search_fields = ('product_name', )


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    search_fields = ('release_slug', )
    exclude = ('release_slug', 'created_on', 'schedule_json_str')


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    search_fields = ('package_name', )
    exclude = ('package_details_json_str', 'details_json_last_updated',
               'name_map_last_updated', 'release_branch_map_last_updated',
               'platform_last_updated', 'upstream_last_updated',
               'downstream_last_updated')


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):

    actions = None
    list_display_links = None
    list_display = ('visitor_ip', 'visitor_user_agent', 'visitor_accept', 'visitor_encoding',
                    'visitor_language', 'first_visit_time', 'last_visit_time')
    search_fields = ('visitor_user_agent',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
