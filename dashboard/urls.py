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
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.base import TemplateView, RedirectView

# dashboard
from dashboard.services.expose.views import (
    PingServer, PackageStatus, GraphRuleCoverage, ReleaseStatus, ReleaseStatusDetail
)
from dashboard.views import (
    TranStatusPackagesView, TranStatusPackageView, TranStatusReleasesView, TranStatusReleaseView,
    TransPlatformSettingsView, LanguagesSettingsView, ReleaseStreamSettingsView, PackageSettingsView,
    JobsView, JobsLogsView, JobsArchiveView, NewPackageView, TransCoverageView, StreamBranchesSettingsView,
    NewReleaseBranchView, GraphRulesSettingsView, NewGraphRuleView, refresh_package, release_graph,
    schedule_job, graph_data, tabular_data, export_packages, generate_reports, read_file_logs
)


api_urls = [
    url(r'^ping$', PingServer.as_view(), name='api_ping_server'),
    url(r'^package/(?P<package_name>[\w-]+)/$', PackageStatus.as_view(), name='api_package_status'),
    url(r'^coverage/(?P<graph_rule>[\w-]+)/$', GraphRuleCoverage.as_view(), name='api_custom_graph'),
    url(r'^release/(?P<release_stream>[\w-]+)/$', ReleaseStatus.as_view(),
        name='api_release_status'),
    url(r'^release/(?P<release_stream>[\w-]+)/detail$', ReleaseStatusDetail.as_view(),
        name='api_release_status_detail'),
]

ajax_urls = [
    url(r'^schedule-job$', schedule_job, name="ajax-schedule-job"),
    url(r'^graph-data$', graph_data, name="ajax-graph-data"),
    url(r'^tabular-data$', tabular_data, name="ajax-tabular-data"),
    url(r'^refresh-package$', refresh_package, name="ajax-refresh-package"),
    url(r'^release-graph$', release_graph, name="ajax-release-graph"),
    url(r'^generate-reports$', generate_reports, name="ajax-releases-report"),
    url(r'^read-file-logs$', read_file_logs, name="ajax-read-logs"),
]

app_jobs_urls = [
    url(r'^$', JobsView.as_view(), name="jobs"),
    url(r'^logs$', JobsLogsView.as_view(), name="jobs-logs"),
    url(r'^archive$', JobsArchiveView.as_view(), name="jobs-archive"),
    url(r'^yml-based$', TemplateView.as_view(template_name="jobs/jobs_yml_based.html"),
        name="jobs-yml-based")
]

app_setting_urls = [
    url(r'^$', RedirectView.as_view(permanent=False, url='/settings/languages'), name="settings"),
    url(r'^languages$', LanguagesSettingsView.as_view(), name="settings-languages"),
    url(r'^translation-platforms$', TransPlatformSettingsView.as_view(), name="settings-trans-platforms"),
    url(r'^product/(?P<stream_slug>\w+)/', include([
        url(r'^releases$', StreamBranchesSettingsView.as_view(), name="settings-stream-branches"),
        url(r'^releases/new$', staff_member_required(NewReleaseBranchView.as_view()),
            name="settings-stream-branches-new")
    ])),
    url(r'^products$', ReleaseStreamSettingsView.as_view(), name="settings-release-streams"),
    url(r'^packages/new$', login_required(NewPackageView.as_view(),
                                          login_url="oidc_authentication_init"),
        name="settings-packages-new"),
    url(r'^packages/export/(?P<format>[\w+]+)$', export_packages, name="packages-export"),
    url(r'^packages$', PackageSettingsView.as_view(), name="settings-packages"),
    url(r'^notification$', TemplateView.as_view(template_name="settings/notification.html"),
        name="settings-notification"),
    url(r'^graph-rules/new$', login_required(NewGraphRuleView.as_view(),
                                             login_url="oidc_authentication_init"),
        name="settings-graph-rules-new"),
    url(r'^graph-rules$', GraphRulesSettingsView.as_view(), name="settings-graph-rules")
]

trans_status_urls = [
    url(r'^$', RedirectView.as_view(permanent=False, url='/translation-status/releases'),
        name="trans-status"),
    url(r'^packages$', TranStatusPackagesView.as_view(), name="trans-status-packages"),
    url(r'^package/(?P<package_name>[\w\-\+]+)$', TranStatusPackageView.as_view(),
        name="trans-status-package"),
    url(r'^releases$', TranStatusReleasesView.as_view(), name="trans-status-releases"),
    url(r'^release/(?P<release_branch>[\w\-\+]+)$', TranStatusReleaseView.as_view(),
        name="trans-status-release")
]

urlpatterns = [
    url(r'^api/', include(api_urls)),
    url(r'^ajax/', include(ajax_urls)),
    url(r'^settings/', include(app_setting_urls)),
    url(r'^jobs/', include(app_jobs_urls)),
    # landing URLs
    url(r'^$', RedirectView.as_view(permanent=False, url='/translation-status/'), name="home"),
    url(r'^translation-status/', include(trans_status_urls)),
    url(r'^translation-coverage/$', TransCoverageView.as_view(), name="custom-graph"),
    url(r'^how-to$', TemplateView.as_view(template_name="howto.html"), name="howto"),
    url(r'^health$', RedirectView.as_view(permanent=False, url='/api/ping?format=json')),
]
