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


class AppSettingsView(ListView):
    """
    Application Settings List View
    """
    template_name = "settings/summary.html"

    def get_queryset(self):
        settings_manager = AppSettingsManager(self.request)
        return settings_manager.get_translation_platforms()


class TransPlatformSettingsView(TemplateView):
    """
    Translation Platform Settings View
    """
    template_name = "settings/transplatforms.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        :param kwargs:
        :return: context_data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)

        app_settings_manager = AppSettingsManager(self.request)
        platforms = app_settings_manager.get_translation_platforms()

        context_data['platforms'] = platforms
        return context_data


class LanguagesSettingsView(TemplateView):
    """
    Languages Settings View
    """
    template_name = "settings/languages.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        :param kwargs:
        :return: context_data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)

        app_settings_manager = AppSettingsManager(self.request)
        locales = app_settings_manager.get_locales()

        context_data['locales'] = locales
        return context_data


class ReleaseStreamSettingsView(TemplateView):
    """
    Release Streams Settings View
    """
    template_name = "settings/release_streams.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        :param kwargs:
        :return: context_data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)

        app_settings_manager = AppSettingsManager(self.request)
        relstreams = app_settings_manager.get_release_streams()

        context_data['relstreams'] = relstreams
        return context_data


class PackageSettingsView(TemplateView):
    """
    Release Streams Settings View
    """
    template_name = "settings/packages.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        :param kwargs:
        :return: context_data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)

        app_settings_manager = AppSettingsManager(self.request)
        packages = app_settings_manager.get_packages()

        context_data['packages'] = packages
        return context_data
