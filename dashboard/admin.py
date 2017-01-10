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
from dashboard.constants import (
    TRANSPLATFORM_ENGINES, RELSTREAM_SLUGS,
    TRANSIFEX_SLUGS, ZANATA_SLUGS,
)
from dashboard.models import (
    Languages, TransPlatform, ReleaseStream
)

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


@admin.register(Languages)
class LanguagesAdmin(admin.ModelAdmin):
    search_fields = ('lang_name', )


@admin.register(TransPlatform)
class TransPlatformAdmin(admin.ModelAdmin):
    form = TransPlatformAdminForm
    exclude = ('projects_json', 'projects_lastupdated')
    search_fields = ('subject', )


@admin.register(ReleaseStream)
class ReleaseStreamAdmin(admin.ModelAdmin):
    form = ReleaseStreamAdminForm
    search_fields = ('relstream_name', )
