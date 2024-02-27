# Copyright 2017 Red Hat, Inc.
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

# python
import yaml

# django
from django.urls import reverse
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

# django third party
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

# application
from transtats import __release__
from dashboard.managers.inventory import ReleaseBranchManager
from dashboard.managers.graphs import GraphManager
from dashboard.managers.jobs import (
    JobTemplateManager, JobsLogManager, YMLBasedJobManager
)


class InventoryManagerMixin(object):
    """Required Manager"""
    inventory_manager = ReleaseBranchManager()


class GraphManagerMixin(object):
    """Required Manager"""
    graph_manager = GraphManager()


class JobManagerMixin(object):
    """Required Managers"""
    job_log_manager = JobsLogManager()
    job_template_manager = JobTemplateManager()


class PingServer(APIView):
    """Ping Server API"""

    def get(self, request):
        """Ping Transtats Server."""
        response_text = {"server": "Transtats " + __release__}
        if 'callback' in request.query_params and request.query_params.get('callback'):
            response_text = '%s(%s);' % (request.query_params['callback'], response_text)
            return HttpResponse(response_text, 'application/javascript')
        return Response(response_text)


class PackageExist(GraphManagerMixin, APIView):
    """Package Exist API"""
    def get(self, request, **kwargs):
        """Determine, if the package exist in Transtats or not."""
        response_text = {}
        if kwargs.get('package_name'):
            package = kwargs['package_name']
            response_text = {package: self.graph_manager.package_manager.is_package_exist(
                package_name=package)}
        return Response(response_text)


class PackageHealth(GraphManagerMixin, APIView):
    """Package Health API"""
    def get(self, request, **kwargs):
        """Get package health"""
        response_text = {}
        if kwargs.get('package_name'):
            package = kwargs['package_name']
            package_obj = \
                self.graph_manager.package_manager.get_packages(
                    pkgs=[package])
            if not package_obj:
                return Response({package: "Not found"})
            package_obj = package_obj.get()
            if package_obj.stats_diff_health:
                response_text = {package: "Translation platform statistics "
                                          "are in sync with the build system."}
            else:
                response_text = {package: package_obj.stats_diff_json}
        return Response(response_text)


class PackageStatus(GraphManagerMixin, APIView):
    """Package Translation Status API"""

    def _process_stats_data(self, trans_stats_data):
        """
        convert graph_ready material to api_ready
        :param trans_stats_data: graph_ready data
        :return: dict
        """
        formatted_data = {}
        translation_data = {}
        if trans_stats_data.get('pkg_desc'):
            formatted_data['description'] = trans_stats_data['pkg_desc']
        ticks = trans_stats_data.get('ticks')
        labels = {}
        [labels.update({index: val}) for index, val in ticks]
        graph_data = trans_stats_data.get('graph_data', {})
        for branch, data in graph_data.items():
            new_trans_data = {}
            for index, stat in data:
                new_trans_data.update({labels.get(index): stat})
            translation_data[branch] = new_trans_data
        formatted_data['translation_stats'] = translation_data
        formatted_data['percentage_calculated_on'] = "Messages"
        return formatted_data

    @method_decorator(cache_page(60 * 60 * 6))
    def get(self, request, **kwargs):
        """Translation status of a package at various places."""
        response_text = {}
        if kwargs.get('package_name'):
            package = kwargs['package_name']
            package_exist = \
                self.graph_manager.package_manager.get_packages(pkgs=[package])
            if package_exist:
                translation_stats = self.graph_manager.get_trans_stats_by_package(
                    package, prepend_source=True
                )
                response_text = {package: self._process_stats_data(translation_stats)}
            else:
                response_text = {package: "Not Found"}
        return Response(response_text)


class AddPackage(GraphManagerMixin, APIView):
    """Add New Package API"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, **kwargs):
        """
        API to add new package. Requires authentication token.
        Params:
            package_name: Package Name as it is in Translation Platform
            upstream_url: Upstream Source Repository URL
            upstream_l10n_url: Upstream Localization URL
            transplatform_slug: translation platform SLUG
            release_streams: comma separated values
        """

        data_received = self.request.data.copy()
        if 'multipart/form-data' in self.request.headers.get('Content-Type'):
            data_received = self.request.data.dict().copy()
        active_user = getattr(request, 'user', None)
        active_user_email = active_user.email \
            if active_user and not active_user.is_anonymous else 'anonymous'
        if not data_received and self.request.POST:
            data_received = self.request.POST.copy()

        required_params = ('package_name', 'upstream_url', 'transplatform_slug', 'release_streams')
        if not set(required_params) <= set(data_received):
            return Response({"error": "Insufficient params provided."}, status=400)

        data_received['release_streams'] = \
            list(map(str.strip, data_received['release_streams'].split(',')))

        if self.graph_manager.package_manager.validate_package(**data_received):
            data_received['created_by'] = active_user_email
            if self.graph_manager.package_manager.add_package(**data_received):
                response_text = {data_received['package_name']: "Package added Successfully."}
            else:
                response_text = {data_received['package_name']: "Some error occurred while adding the package."}
        else:
            response_text = {data_received['package_name']: "Package validation failed."}
        return Response(response_text)


class GraphRuleCoverage(GraphManagerMixin, APIView):
    """Graph Rule Coverage API"""

    @method_decorator(cache_page(60 * 60 * 6))
    def get(self, request, **kwargs):
        """Translation coverage of multiple packages for a product release in selected languages."""
        response_text = {}
        if kwargs.get('coverage_rule'):
            rule = kwargs['coverage_rule']
            rule_exist = self.graph_manager.get_graph_rules(graph_rule=rule)
            if rule_exist and rule_exist.first().rule_visibility_public:
                translation_stats, _, _, _, release = self.graph_manager.get_trans_stats_by_rule(rule)
                translation_stats.update({'release': release})
                translation_stats.update({'coverage_rule': rule})
                response_text = {'coverage': translation_stats}
            else:
                response_text = {rule: "Not Found"}
        return Response(response_text)


class ReleaseStatus(InventoryManagerMixin, GraphManagerMixin, APIView):
    """Release Status API"""

    def _process_stats_data(self, trans_stats_data):
        """
        convert graph_ready material to api_ready
        :param trans_stats_data: graph_ready data
        :return: dict
        """
        if not isinstance(trans_stats_data, dict):
            return {}
        for package, stats in trans_stats_data.items():
            stats["Remaining"] = float("{0:.2f}".format(stats.get("Remaining")))
        trans_stats_data["Calculated on"] = "Messages"
        return trans_stats_data

    @method_decorator(cache_page(60 * 60 * 6))
    def get(self, request, **kwargs):
        """Translation status of a product release for linked packages."""
        response_text = {}
        if kwargs.get('release_stream'):
            release = kwargs['release_stream']
            if not self.inventory_manager.is_relbranch_exist(release):
                response_text = {release: "Release not found"}
            else:
                estimate = self.graph_manager.get_workload_combined(release)
                if isinstance(estimate, tuple) and len(estimate) > 1:
                    response_text = {release: self._process_stats_data(estimate[1])} \
                        if estimate[1] else {release: "Release not found"}
                else:
                    response_text = {release: "Release status could not be determined."}
        return Response(response_text)


class ReleaseStatusDetail(ReleaseStatus):
    """Release Status Detail API"""

    @method_decorator(cache_page(60 * 60 * 6))
    def get(self, request, **kwargs):
        """Detailed (language-wise) translation status of a product release."""
        response_text = {}
        if kwargs.get('release_stream'):
            release = kwargs['release_stream']
            release_branch = \
                self.graph_manager.branch_manager.get_release_branches(relbranch=release)
            if release_branch:
                detailed_workload_data = \
                    self.graph_manager.get_workload_combined_detailed(release)
                for lang, pkg_stat in detailed_workload_data.items():
                    detailed_workload_data[lang] = self._process_stats_data(pkg_stat)
                detailed_workload_data["Release"] = release
                response_text = detailed_workload_data
            else:
                response_text = {release: "Release not found"}
        return Response(response_text)


class ReleaseStatusLocale(ReleaseStatus):
    """Release Status Locale API View"""

    @method_decorator(cache_page(60 * 60 * 6))
    def get(self, request, **kwargs):
        """Translation status of a product release in a particular language."""
        response_text = {}
        if kwargs.get('release_stream') and kwargs.get('locale'):
            release = kwargs['release_stream']
            locale = kwargs['locale']
            locale_alias = self.inventory_manager.get_locale_alias(locale)
            if locale == locale_alias:
                locale = self.inventory_manager.get_alias_locale(locale)
            relbranch_locales = self.inventory_manager.get_relbranch_locales(release)
            if not relbranch_locales:
                return Response({release: "Release seems not configured yet."}, status=412)
            if locale not in relbranch_locales:
                return Response({locale: "Does not belong to language set %s is mapped to."
                                % release}, status=412)
            estimate = self.graph_manager.get_workload_estimate(release, locale=locale)
            if isinstance(estimate, tuple) and len(estimate) > 1:
                if not estimate[1]:
                    response_text = {release: "Release not found"}
                else:
                    response_text = {release: self._process_stats_data(estimate[1])}
                    response_text[release]['locale'] = locale
            else:
                response_text = {release: "Release status could not be determined."}
        return Response(response_text)


class RunJob(JobManagerMixin, APIView):
    """Run YML Job API"""

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def post(self, request, **kwargs):
        """API to run YML Jobs. Requires authentication token."""
        data_received = self.request.data.copy()
        active_user = getattr(request, 'user', None)
        active_user_email = active_user.email \
            if active_user and not active_user.is_anonymous else 'anonymous'
        if not data_received:
            data_received = self.request.POST.copy()
        query_params = self.request.query_params.copy()
        if data_received and data_received.get('job_type'):
            input_job_type = data_received['job_type']
            job_templates = self.job_template_manager.get_job_templates(
                job_template_type=input_job_type
            )
            job_template = job_templates.first() \
                if job_templates and len(job_templates) > 0 else {}
            if job_template:
                job_params = list(job_template.job_template_params)
                unavailable_params = [param for param in job_params if not data_received.get(param)]
                if not unavailable_params:
                    fields = [param.upper() for param in job_params] + ['YML_FILE']
                    job_data = {param.upper(): data_received.get(param) for param in job_params}
                    job_data.update({
                        'YML_FILE': yaml.dump(job_template.job_template_json,
                                              default_flow_style=False).replace("\'", "")
                    })
                    if query_params and query_params.get('DRY_RUN'):
                        job_data.update({'DRY_RUN': query_params['DRY_RUN']})
                        fields.append('DRY_RUN')
                    job_params = [param.upper() for param in job_params]
                    job_manager = YMLBasedJobManager(
                        **{field: job_data.get(field) for field in fields},
                        **{'params': job_params, 'type': input_job_type},
                        **{'active_user_email': active_user_email}
                    )
                    try:
                        job_uuid, _ = job_manager.execute_job()
                    except Exception as e:
                        return Response({
                            "Exception": "Something went wrong while job execution."
                        }, status=500)
                    else:
                        response_text, response_code = {
                            "Success": "Job created and logged. URL: %s" %
                                       self.request.get_raw_uri().replace(
                                           self.request.get_full_path(), reverse(
                                               'log-detail', kwargs={'job_id': str(job_uuid)}))}, 200
                        response_text.update(dict(job_id=str(job_uuid)))
                else:
                    response_text, response_code = {
                        "job_params": "Required params: %s not found." % ", ".join(unavailable_params)
                    }, 412
            else:
                response_text, response_code = {
                    "job_type": "Job template not found."
                }, 412
        else:
            response_text, response_code = {"job_type": "Empty job type"}, 412

        return Response(response_text, status=response_code)


class JobLog(JobManagerMixin, APIView):
    """Job Log API"""

    @method_decorator(cache_page(60 * 60 * 6))
    def get(self, request, **kwargs):
        """Fetch details about a YML job ran successfully in Transtats."""
        response_text = {}
        response_code = None
        if kwargs.get('job_id'):
            job = self.job_log_manager.get_job_detail(kwargs['job_id'])
            if job and job.job_visible_on_url:
                response_text['id'] = str(job.job_uuid)
                response_text['type'] = job.job_type
                response_text['start_time'] = job.job_start_time.strftime("%Y-%m-%d %H:%M:%S")
                response_text['end_time'] = job.job_end_time.strftime("%Y-%m-%d %H:%M:%S")
                response_text['result'] = job.job_result
                response_text['remarks'] = job.job_remarks
                response_text['YML_input'] = job.job_yml_text
                response_text['log_output'] = job.job_log_json
                response_code = 200
            else:
                response_text = {kwargs['job_id']: "Job not found"}
                response_code = 412
        return Response(response_text, status=response_code)
