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

# Transtats exposes following API URL(s)

from django.conf.urls import url
from dashboard.services.expose.views import (
    PingServer, PackageStatus, GraphRuleCoverage, ReleaseStatus, ReleaseStatusDetail,
    PackageExist, ReleaseStatusLocale, RunJob, JobLog, PackageHealth, AddPackage
)


api_urls = [
    url(r'^ping$', PingServer.as_view(), name='api_ping_server'),
    url(r'^package/(?P<package_name>[\w-]+)/exist$', PackageExist.as_view(), name='api_package_exist'),
    url(r'^package/(?P<package_name>[\w-]+)/health', PackageHealth.as_view(), name='api_package_health'),
    url(r'^package/create$', AddPackage.as_view(), name='api_package_new'),
    url(r'^package/(?P<package_name>[\w-]+)$', PackageStatus.as_view(), name='api_package_status'),
    url(r'^coverage/(?P<coverage_rule>[\w-]+)$', GraphRuleCoverage.as_view(), name='api_custom_graph'),
    url(r'^release/(?P<release_stream>[\w-]+)$', ReleaseStatus.as_view(),
        name='api_release_status'),
    url(r'^release/(?P<release_stream>[\w-]+)/detail$', ReleaseStatusDetail.as_view(),
        name='api_release_status_detail'),
    url(r'^release/(?P<release_stream>[\w-]+)/locale/(?P<locale>[\w_]+)$',
        ReleaseStatusLocale.as_view(), name='api_release_status_locale'),
    url(r'^job/run$', RunJob.as_view(), name='api_job_run'),
    url(r'^job/(?P<job_id>[0-9a-f-]+)/log$', JobLog.as_view(), name='api_job_log'),
]
