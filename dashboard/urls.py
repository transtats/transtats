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
from django.conf.urls import url, include
from django.views.generic.base import TemplateView

# dashboard
from .views import (
    HomeTemplateView, AppSettingsView, TransPlatformSettingsView,
    LanguagesSettingsView, ReleaseStreamSettingsView, PackageSettingsView,
    LogsSettingsView, schedule_job, graph_data
)

ajax_urls = [
    url(r'^schedule-job$', schedule_job, name="ajax-schedule-job"),
    url(r'^graph-data$', graph_data, name="ajax-graph-data")
]

app_setting_urls = [
    url(r'^$', AppSettingsView.as_view(), name="settings"),
    url(r'^translation-platforms$', TransPlatformSettingsView.as_view(), name="settings-trans-platforms"),
    url(r'^release-streams$', ReleaseStreamSettingsView.as_view(), name="settings-release-streams"),
    url(r'^packages$', PackageSettingsView.as_view(), name="settings-packages"),
    url(r'^languages$', LanguagesSettingsView.as_view(), name="settings-languages"),
    url(r'^notification$', TemplateView.as_view(template_name="settings/notification.html"),
        name="settings-notification"),
    url(r'^scheduler$', TemplateView.as_view(template_name="settings/scheduler.html"),
        name="settings-scheduler"),
    url(r'^stats-views$', TemplateView.as_view(template_name="settings/stats_views.html"),
        name="settings-stats-views"),
    url(r'^logs$', LogsSettingsView.as_view(), name="settings-logs"),
]

urlpatterns = [
    url(r'^$', HomeTemplateView.as_view(), name="home"),
    url(r'^admin', TemplateView.as_view(template_name="login.html"), name="admin-login"),
    url(r'^register$', TemplateView.as_view(template_name="register.html"), name="register"),
    url(r'^features$', TemplateView.as_view(template_name="features.html"), name="features"),
    url(r'^settings/', include(app_setting_urls)),
    url(r'^ajax/', include(ajax_urls))
]
