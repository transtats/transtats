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

from django.conf.urls import url
from django.views.generic.base import TemplateView
from .views.home import HomeTemplateView
from .views.settings import (
    AppSettingsView, TransPlatformSettingsView, LanguagesSettingsView
)

urlpatterns = [
    url(r'^$', HomeTemplateView.as_view(), name="home"),
    url(r'^register$', TemplateView.as_view(template_name="register.html"), name="register"),
    url(r'^features$', TemplateView.as_view(template_name="features.html"), name="features"),
    url(r'^settings$', AppSettingsView.as_view(), name="settings"),
    url(r'^settings/translation-platforms$', TransPlatformSettingsView.as_view(), name="settings-trans-platforms"),
    url(r'^settings/release-streams$', TemplateView.as_view(template_name="settings/release_streams.html"),
        name="settings-release-streams"),
    url(r'^settings/packages$', TemplateView.as_view(template_name="settings/packages.html"),
        name="settings-packages"),
    url(r'^settings/languages$', LanguagesSettingsView.as_view(), name="settings-languages"),
    url(r'^settings/notification$', TemplateView.as_view(template_name="settings/notification.html"),
        name="settings-notification"),
    url(r'^settings/scheduler$', TemplateView.as_view(template_name="settings/scheduler.html"),
        name="settings-scheduler"),
    url(r'^settings/stats-views$', TemplateView.as_view(template_name="settings/stats_views.html"),
        name="settings-stats-views"),
]
