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
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView

# dashboard
from dashboard.services.expose.views import (
    PingServer, PackageStatus, GraphRuleCoverage,
    TranslationWorkload, TranslationWorkloadDetail
)
from dashboard.views import (
    TranStatusTextView, TranStatusGraphView, AppSettingsView,
    TransPlatformSettingsView, LanguagesSettingsView,
    ReleaseStreamSettingsView, PackageSettingsView,
    LogsSettingsView, NewPackageView, StreamBranchesSettingsView,
    NewReleaseBranchView, TransCoverageView, GraphRulesSettingsView,
    NewGraphRuleView, PackageConfigView, refresh_package, workload_graph,
    WorkloadEstimationView, WorkloadDetailedView, WorkloadCombinedView,
    schedule_job, graph_data, tabular_data, export_packages
)


api_urls = [
    url(r'^ping$', PingServer.as_view(), name='api_ping_server'),
    url(r'^status/(?P<package_name>[\w-]+)/$', PackageStatus.as_view(), name='api_package_status'),
    url(r'^coverage/(?P<graph_rule>[\w-]+)/$', GraphRuleCoverage.as_view(), name='api_custom_graph'),
    url(r'^workload/(?P<release_stream>[\w-]+)/$', TranslationWorkload.as_view(),
        name='api_release_workload'),
    url(r'^workload/(?P<release_stream>[\w-]+)/detail$', TranslationWorkloadDetail.as_view(),
        name='api_release_workload_detail'),
]

ajax_urls = [
    url(r'^schedule-job$', schedule_job, name="ajax-schedule-job"),
    url(r'^graph-data$', graph_data, name="ajax-graph-data"),
    url(r'^tabular-data$', tabular_data, name="ajax-tabular-data"),
    url(r'^refresh-package$', refresh_package, name="ajax-refresh-package"),
    url(r'^workload-graph$', workload_graph, name="ajax-workload-graph"),
]

app_setting_urls = [
    url(r'^$', AppSettingsView.as_view(), name="settings"),
    url(r'^translation-platforms$', TransPlatformSettingsView.as_view(), name="settings-trans-platforms"),
    url(r'^release-stream/(?P<stream_slug>\w+)/', include([
        url(r'^branches$', StreamBranchesSettingsView.as_view(), name="settings-stream-branches"),
        url(r'^branches/new$', NewReleaseBranchView.as_view(), name="settings-stream-branches-new")
    ])),
    url(r'^release-streams$', ReleaseStreamSettingsView.as_view(), name="settings-release-streams"),
    url(r'^package/(?P<package_name>[\w\-\+]+)/', include([
        url(r'^config$', PackageConfigView.as_view(), name="settings-package-config"),
    ])),
    url(r'^packages/new$', NewPackageView.as_view(), name="settings-packages-new"),
    url(r'^packages/export/(?P<format>[\w+]+)$', export_packages, name="packages-export"),
    url(r'^packages$', PackageSettingsView.as_view(), name="settings-packages"),
    url(r'^languages$', LanguagesSettingsView.as_view(), name="settings-languages"),
    url(r'^notification$', TemplateView.as_view(template_name="settings/notification.html"),
        name="settings-notification"),
    url(r'^jobs$', login_required(TemplateView.as_view(template_name="settings/jobs.html"),
                                  login_url="admin:index"), name="settings-jobs"),
    url(r'^graph-rules/new$', NewGraphRuleView.as_view(), name="settings-graph-rules-new"),
    url(r'^graph-rules$', GraphRulesSettingsView.as_view(), name="settings-graph-rules"),
    url(r'^logs$', LogsSettingsView.as_view(), name="settings-logs"),
]

urlpatterns = [
    url(r'^api/', include(api_urls)),
    url(r'^ajax/', include(ajax_urls)),
    url(r'^settings/', include(app_setting_urls)),
    url(r'^$', TranStatusTextView.as_view(), name="home"),
    url(r'^trans-status$', TranStatusGraphView.as_view(), name="graph-view"),
    url(r'^trans-coverage$', TransCoverageView.as_view(), name="custom-graph"),
    url(r'^trans-workload-combined$', WorkloadCombinedView.as_view(), name="workload-combined"),
    url(r'^trans-workload$', WorkloadEstimationView.as_view(), name="workload"),
    url(r'^trans-workload-detailed$', WorkloadDetailedView.as_view(), name="workload-detailed"),
    url(r'^how-to$', TemplateView.as_view(template_name="howto.html"), name="howto"),
]
