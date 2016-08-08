#
# transtats - Translation Analytics
#
# Copyright (c) 2016 Sundeep Anand <suanand@redhat.com>
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of transtats.
#
# transtats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# transtats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with transtats.  If not, see <http://www.gnu.org/licenses/>.

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
