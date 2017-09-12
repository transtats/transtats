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

# django
from django.http import HttpResponse

# django third party
from rest_framework.views import APIView
from rest_framework.response import Response

# application
from transtats import __version__
from dashboard.managers.graphs import GraphManager


class APIMixin(object):
    """
    Required Managers
    """
    graph_manager = GraphManager()


class PingServer(APIView):
    """
    Ping Server API View
    """

    def get(self, request):
        """
        GET response
        :param request: Request object
        :return: Custom JSON
        """
        response_text = {"server": "Transtats " + __version__}
        if 'callback' in request.query_params and request.query_params.get('callback'):
            response_text = '%s(%s);' % (request.query_params['callback'], response_text)
            return HttpResponse(response_text, 'application/javascript')
        return Response(response_text)


class PackageStatus(APIMixin, APIView):
    """
    Package Translation Status API View
    """

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

    def get(self, request, **kwargs):
        """
        GET response
        :param request: Request object
        :param kwargs: Keyword Arguments
        :return: Custom JSON
        """
        response_text = {}
        if kwargs.get('package_name'):
            package = kwargs['package_name']
            package_exist = \
                self.graph_manager.package_manager.get_packages(pkgs=[package])
            if package_exist:
                translation_stats = self.graph_manager.get_trans_stats_by_package(package)
                response_text = {package: self._process_stats_data(translation_stats)}
            else:
                response_text = {package: "Not Found"}
        return Response(response_text)


class GraphRuleCoverage(APIMixin, APIView):
    """
    Graph Rule Coverage API View
    """

    def _process_stats_data(self, graph_rule, trans_stats_data):
        """
        convert graph_ready material to api_ready
        :param: graph rule
        :param trans_stats_data: graph_ready data
        :return: dict
        """
        formatted_data = {}
        translation_data = {}
        if graph_rule:
            formatted_data['graph_rule'] = graph_rule
        if trans_stats_data.get('branch'):
            formatted_data['branch'] = trans_stats_data['branch']
        ticks = trans_stats_data.get('ticks')
        labels = {}
        [labels.update({index: val}) for index, val in ticks]
        graph_data = trans_stats_data.get('graph_data', {})
        for unit in graph_data:
            temp_stat = {}
            stat = unit.get('data', [])
            for index, val in stat:
                temp_stat.update({labels.get(index): val})
            translation_data[unit.get('label', 'label')] = temp_stat
        formatted_data['translation_stats'] = translation_data
        return formatted_data

    def get(self, request, **kwargs):
        """
        GET response
        :param request: Request object
        :param kwargs: Keyword Arguments
        :return: Custom JSON
        """
        response_text = {}
        if kwargs.get('graph_rule'):
            rule = kwargs['graph_rule']
            rule_exist = self.graph_manager.get_graph_rules(graph_rule=rule)
            if rule_exist:
                translation_stats = self.graph_manager.get_trans_stats_by_rule(rule)
                response_text = {'coverage': self._process_stats_data(rule, translation_stats)}
            else:
                response_text = {rule: "Not Found"}
        return Response(response_text)


class TranslationWorkload(APIMixin, APIView):
    """
    Translation Workload API View
    """

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

    def get(self, request, **kwargs):
        """
        GET response
        :param request: Request object
        :param kwargs: Keyword Arguments
        :return: Custom JSON
        """
        response_text = {}
        if kwargs.get('release_stream'):
            release = kwargs['release_stream']
            estimate = self.graph_manager.get_workload_combined(release)
            if isinstance(estimate, tuple) and len(estimate) > 1:
                response_text = {release: self._process_stats_data(estimate[1])} \
                    if estimate[1] else {release: "Release branch not found"}
            else:
                response_text = {release: "Workload could not be calculated"}
        return Response(response_text)


class TranslationWorkloadDetail(TranslationWorkload):
    """
    Translation Workload Detail API View
    """

    def get(self, request, **kwargs):
        """
        GET response
        :param request: Request object
        :param kwargs: Keyword Arguments
        :return: Custom JSON
        """
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
                response_text = {release: "Release branch not found"}
        return Response(response_text)
