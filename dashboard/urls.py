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
from django.conf import settings
from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.base import TemplateView, RedirectView

# dashboard
from dashboard.services.urls import api_urls
from dashboard.views import (
    TranStatusPackagesView, TranStatusPackageView, TranStatusReleasesView, TranStatusReleaseView,
    # TODO: To be removed
    # TransPlatformSettingsView, LanguagesSettingsView, ReleaseStreamSettingsView, PackageSettingsView,
    # JobsView, JobsLogsView, JobsLogsPackageView, JobsArchiveView, NewPackageView, TransCoverageView,
    # StreamBranchesSettingsView, get_build_tags, NewReleaseBranchView, GraphRulesSettingsView, NewGraphRuleView,
    # JobDetailView, refresh_package, job_template, release_graph, schedule_job, graph_data, tabular_data,
    # export_packages, generate_reports, read_file_logs
    # TransPlatformSettingsView, LanguagesSettingsView, ReleaseStreamSettingsView, PackageSettingsView, JobsView,
    # JobsLogsView, JobsArchiveView, NewPackageView, TransCoverageView, StreamBranchesSettingsView, get_build_tags,
    # NewReleaseBranchView, GraphRulesSettingsView, NewGraphRuleView, JobDetailView, refresh_package, job_template,
    # release_graph, schedule_job, graph_data, tabular_data, export_packages, generate_reports, read_file_logs,
    TransPlatformSettingsView, LanguagesSettingsView, ReleaseStreamSettingsView, PackageSettingsView,
    JobsView, JobsLogsView, JobsArchiveView, NewPackageView, UpdatePackageView, TransCoverageView,
    StreamBranchesSettingsView, NewReleaseBranchView, GraphRulesSettingsView, NewGraphRuleView,
    NewLanguageView, UpdateLanguageView, NewLanguageSetView, UpdateLanguageSetView, NewTransPlatformView,
    UpdateTransPlatformView, JobDetailView, refresh_package, release_graph, schedule_job, graph_data, tabular_data,
    export_packages, generate_reports, read_file_logs, get_build_tags, change_lang_status, job_template
)

LOGIN_URL = "oidc_authentication_init" if settings.FAS_AUTH else "admin:index"


ajax_urls = [
    url(r'^schedule-job$', schedule_job, name="ajax-schedule-job"),
    url(r'^graph-data$', graph_data, name="ajax-graph-data"),
    url(r'^tabular-data$', tabular_data, name="ajax-tabular-data"),
    url(r'^refresh-package$', refresh_package, name="ajax-refresh-package"),
    url(r'^release-graph$', release_graph, name="ajax-release-graph"),
    url(r'^generate-reports$', generate_reports, name="ajax-releases-report"),
    url(r'^read-file-logs$', read_file_logs, name="ajax-read-logs"),
    url(r'^build-tags$', get_build_tags, name="ajax-build-tags"),
    url(r'^job-template$', job_template, name="ajax-job-template"),
    url(r'^change-lang-status$', login_required(change_lang_status, login_url=LOGIN_URL),
        name="ajax-change-lang-status"),
]

app_jobs_urls = [
    url(r'^$', JobsView.as_view(), name="jobs"),
    url(r'^logs$', JobsLogsView.as_view(), name="jobs-logs"),
    url(r'^archive$', JobsArchiveView.as_view(), name="jobs-archive"),
    url(r'^yml-based$', TemplateView.as_view(template_name="jobs/jobs_yml_based.html"),
        name="jobs-yml-based"),
    url(r'^log/(?P<job_id>[0-9a-f-]+)/detail$', JobDetailView.as_view(), name="log-detail"),
    url(r'^logs/package/(?P<package_name>[\w\-\+]+)$', JobsLogsPackageView.as_view(),
        name="jobs-logs-package")
]

app_setting_urls = [
    url(r'^$', RedirectView.as_view(permanent=False, url='/settings/languages'), name="settings"),
    url(r'^languages$', RedirectView.as_view(permanent=True, url='/languages')),
    url(r'^translation-platforms$', RedirectView.as_view(permanent=True, url='/translation-platforms')),
    url(r'^product/(?P<stream_slug>\w+)/', include([
        url(r'^releases$', StreamBranchesSettingsView.as_view(), name="settings-stream-branches"),
        url(r'^releases/new$', staff_member_required(NewReleaseBranchView.as_view()),
            name="settings-stream-branches-new")
    ])),
    url(r'^products$', ReleaseStreamSettingsView.as_view(), name="settings-release-streams"),
    url(r'^packages$', RedirectView.as_view(permanent=True, url='/packages')),
    url(r'^notification$', TemplateView.as_view(template_name="settings/notification.html"),
        name="settings-notification"),
    url(r'^graph-rules/new$', login_required(NewGraphRuleView.as_view(), login_url=LOGIN_URL),
        name="settings-graph-rules-new"),
    url(r'^graph-rules$', GraphRulesSettingsView.as_view(), name="settings-graph-rules")
]

trans_status_urls = [
    url(r'^$', RedirectView.as_view(permanent=False, url='/translation-status/releases'),
        name="trans-status"),
    url(r'^packages$', TranStatusPackagesView.as_view(), name="trans-status-packages"),
    url(r'^releases$', TranStatusReleasesView.as_view(), name="trans-status-releases"),
    url(r'^release/(?P<release_branch>[\w\-\+]+)$', TranStatusReleaseView.as_view(),
        name="trans-status-release")
]

packages_urls = [
    url(r'^$', PackageSettingsView.as_view(), name="settings-packages"),
    url(r'^new$', login_required(NewPackageView.as_view(), login_url=LOGIN_URL), name="package-new"),
    url(r'^view/(?P<package_name>[\w\-\+]+)$', TranStatusPackageView.as_view(), name="package-view"),
    url(r'^edit/(?P<slug>[\w-]+)$', login_required(UpdatePackageView.as_view(), login_url=LOGIN_URL),
        name="package-update"),
    url(r'^export/(?P<format>[\w+]+)$', export_packages, name="packages-export"),
]

languages_urls = [
    url(r'^$', LanguagesSettingsView.as_view(), name="settings-languages"),
    url(r'^new$', login_required(NewLanguageView.as_view(), login_url=LOGIN_URL),
        name="language-new"),
    url(r'^edit/(?P<pk>\w+)$', login_required(UpdateLanguageView.as_view(), login_url=LOGIN_URL),
        name="language-update"),
    url(r'^set/new$', login_required(NewLanguageSetView.as_view(), login_url=LOGIN_URL),
        name="language-set-new"),
    url(r'^set/edit/(?P<slug>[\w-]+)$', login_required(UpdateLanguageSetView.as_view(), login_url=LOGIN_URL),
        name="language-set-update"),
]

transplatforms_urls = [
    url(r'^$', TransPlatformSettingsView.as_view(), name="settings-trans-platforms"),
    url(r'^new$', login_required(NewTransPlatformView.as_view(), login_url=LOGIN_URL), name="transplatform-new"),
    url(r'^edit/(?P<slug>[\w-]+)$', login_required(UpdateTransPlatformView.as_view(), login_url=LOGIN_URL),
        name="transplatform-update"),
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
    url(r'^quick-start$', TemplateView.as_view(template_name="howto.html"), name="howto"),
    url(r'^health$', RedirectView.as_view(permanent=False, url='/api/ping?format=json')),
    # packages section urls
    url(r'^packages/', include(packages_urls)),
    # languages section urls
    url(r'^languages/', include(languages_urls)),
    # trans platforms section urls
    url(r'^translation-platforms/', include(transplatforms_urls)),
]
