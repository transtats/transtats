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

from django.views.generic import ListView, TemplateView
from ..managers.settings import AppSettingsManager
from ..managers.packages import PackagesManager


class AppSettingsView(TemplateView):
    """
    Application Settings List View
    """
    template_name = "settings/summary.html"


class TransPlatformSettingsView(ListView):
    """
    Translation Platform Settings View
    """
    template_name = "settings/transplatforms.html"
    context_object_name = 'platforms'

    def get_queryset(self):
        app_settings_manager = AppSettingsManager(self.request)
        platforms = app_settings_manager.get_translation_platforms()
        return platforms

    def get_context_data(self, **kwargs):
        context = super(TransPlatformSettingsView, self).get_context_data(**kwargs)
        app_settings_manager = AppSettingsManager(self.request)
        platforms_set = app_settings_manager.get_transplatforms_set()
        if isinstance(platforms_set, tuple):
            active_platforms, inactive_platforms = platforms_set
            context['active_platforms_len'] = len(active_platforms)
            context['inactive_platforms_len'] = len(inactive_platforms)
        return context


class LanguagesSettingsView(ListView):
    """
    Languages Settings View
    """
    template_name = "settings/languages.html"
    context_object_name = 'locales'

    def get_queryset(self):
        app_settings_manager = AppSettingsManager(self.request)
        locales = app_settings_manager.get_locales()
        return locales

    def get_context_data(self, **kwargs):
        context = super(LanguagesSettingsView, self).get_context_data(**kwargs)
        app_settings_manager = AppSettingsManager(self.request)
        locales_set = app_settings_manager.get_locales_set()
        if isinstance(locales_set, tuple):
            active_locales, inactive_locales, aliases = locales_set
            context['active_locales_len'] = len(active_locales)
            context['inactive_locales_len'] = len(inactive_locales)
            context['aliases_len'] = len(aliases)
        return context


class ReleaseStreamSettingsView(ListView):
    """
    Release Streams Settings View
    """
    template_name = "settings/release_streams.html"
    context_object_name = 'relstreams'

    def get_queryset(self):
        app_settings_manager = AppSettingsManager(self.request)
        relstreams = app_settings_manager.get_release_streams()
        return relstreams


class PackageSettingsView(ListView):
    """
    Packages Settings View
    """
    template_name = "settings/packages.html"
    context_object_name = 'packages'

    def get_queryset(self):
        packages_manager = PackagesManager(self.request)
        packages = packages_manager.get_packages()
        return packages
