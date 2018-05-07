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

import os
from collections import OrderedDict
from django import template

from dashboard.constants import BRANCH_MAPPING_KEYS
from dashboard.managers.graphs import GraphManager, ReportsManager
from dashboard.managers.packages import PackagesManager


register = template.Library()


@register.filter
def get_item(dict_object, key):
    return dict_object.get(key)


@register.filter
def join_by(sequence, delimiter):
    return delimiter.join(sequence)


@register.inclusion_tag(
    os.path.join("stats", "_package_details.html")
)
def tag_package_details(package_name, user):
    package_manager = PackagesManager()
    return_value = OrderedDict()
    try:
        package = package_manager.get_packages([package_name]).get()
        pkg_details = package.package_details_json
        if pkg_details and pkg_details.get('description'):
            return_value.update(
                {'package_desc': pkg_details['description']}
            )
    except:
        # log event, passing for now
        pass
    else:
        return_value.update(
            {'package': package,
             'user': user}
        )
    return return_value


@register.inclusion_tag(
    os.path.join("stats", "_branch_mapping.html")
)
def tag_branch_mapping(package):
    package_manager = PackagesManager()
    return_value = OrderedDict()
    try:
        package_details = package_manager.get_packages([package]).get()
    except:
        # log event, passing for now
        pass
    else:
        return_value.update(
            {'package_name': package_details.package_name,
             'branch_mapping': package_details.release_branch_mapping,
             'mapping_lastupdated': package_details.mapping_lastupdated,
             'mapping_keys': BRANCH_MAPPING_KEYS}
        )
    return return_value


@register.inclusion_tag(
    os.path.join("stats", "_stats_diff.html")
)
def tag_stats_diff(package):
    package_manager = PackagesManager()
    return_value = OrderedDict()
    try:
        package_details = package_manager.get_packages([package]).get()
    except:
        # log event, passing for now
        pass
    else:
        stats_diff = package_details.stats_diff or {}
        langs_out_of_sync = {}
        for branch, diff in stats_diff.items():
            langs_out_of_sync[branch] = {}
            for lang, diff_percent in diff.items():
                langs_out_of_sync[branch][lang] = diff_percent
        return_value.update(
            {'package_name': package_details.package_name,
             'stats_diff': langs_out_of_sync}
        )
    return return_value


@register.inclusion_tag(
    os.path.join("stats", "_tabular_form.html")
)
def tag_tabular_form(package):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    stats_dict = graph_manager.get_trans_stats_by_package(package)
    headers = stats_dict['ticks']
    stats_data = stats_dict['graph_data']
    return_value.update(
        {'headers': [lang for index, lang in headers],
         'stats_data': stats_data,
         'pkg_desc': stats_dict['pkg_desc']}
    )
    return return_value


@register.inclusion_tag(
    os.path.join("stats", "_workload_combined.html")
)
def tag_workload_per_lang(relbranch, lang_id):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    headers, workload = \
        graph_manager.get_workload_estimate(relbranch,
                                            locale=lang_id)
    return_value.update(dict(headers=headers))
    return_value.update(dict(packages=workload.items()))
    return return_value


@register.inclusion_tag(
    os.path.join("stats", "_workload_combined.html")
)
def tag_workload_combined(relbranch):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    headers, workload = graph_manager.get_workload_combined(relbranch)
    return_value.update(dict(headers=headers))
    return_value.update(dict(packages=workload.items()))
    return return_value


@register.inclusion_tag(
    os.path.join("stats", "_workload_detailed.html")
)
def tag_workload_detailed(relbranch):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    headers, workload = graph_manager.get_workload_detailed(relbranch)
    return_value.update(dict(headers=headers))
    return_value.update(dict(packages=workload.items()))
    return return_value


@register.inclusion_tag(
    os.path.join("stats", "_releases_summary.html")
)
def tag_releases_summary():
    return_value = OrderedDict()
    reports_manager = ReportsManager()
    releases_summary = reports_manager.get_reports('releases')
    if releases_summary:
        release_report_json = releases_summary.get().report_json
        for release, summary in release_report_json.items():
            if summary.get('languages'):
                release_report_json[release]['languages'] = \
                    OrderedDict(sorted(summary['languages'].items()))
        return_value.update(dict(
            relsummary=release_report_json,
            last_updated=releases_summary.get().report_updated
        ))
    return return_value


@register.inclusion_tag(
    os.path.join("packages", "_packages_summary.html")
)
def tag_packages_summary():
    return_value = OrderedDict()
    package_manager = PackagesManager()
    reports_manager = ReportsManager()
    packages_summary = reports_manager.get_reports('packages')
    if packages_summary:
        return_value.update(dict(
            pkgsummary=packages_summary.get().report_json,
            last_updated=packages_summary.get().report_updated,
            package_count=package_manager.count_packages(),
        ))
    return return_value


@register.inclusion_tag(
    os.path.join("jobs", "_build_tags.html")
)
def tag_build_tags(buildsys):
    return_value = OrderedDict()
    package_manager = PackagesManager()
    tags = package_manager.get_build_tags(buildsys=buildsys)
    return_value.update(dict(
        build_tags=tags
    ))
    return return_value
