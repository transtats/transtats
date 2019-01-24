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
import json
import yaml
from collections import OrderedDict
from django import template
from urllib.parse import urlparse

from dashboard.constants import BRANCH_MAPPING_KEYS, TS_JOB_TYPES
from dashboard.managers.graphs import GraphManager, ReportsManager
from dashboard.managers.jobs import JobTemplateManager
from dashboard.managers.packages import PackagesManager
from dashboard.managers.inventory import ReleaseBranchManager


register = template.Library()


@register.filter
def get_item(dict_object, key):
    if not isinstance(dict_object, dict):
        return ''
    return dict_object.get(key)


@register.filter
def join_by(sequence, delimiter):
    return delimiter.join(sequence)


@register.filter
def js_id_safe(id_value):
    return id_value.replace("@", "-at-")


@register.filter
def url_parse(url_value):
    return urlparse(url_value).netloc


@register.inclusion_tag(
    os.path.join("packages", "_package_details.html")
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
    os.path.join("packages", "_branch_mapping.html")
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
             'branch_mapping': package_details.release_branch_mapping_json,
             'mapping_lastupdated': package_details.release_branch_map_last_updated,
             'mapping_keys': BRANCH_MAPPING_KEYS}
        )
    return return_value


@register.inclusion_tag(
    os.path.join("packages", "_stats_diff.html")
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
        stats_diff = package_details.stats_diff_json or {}
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
    os.path.join("packages", "_tabular_form.html")
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
    os.path.join("releases", "_workload_combined.html")
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
    os.path.join("releases", "_workload_combined.html")
)
def tag_workload_combined(relbranch):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    headers, workload = graph_manager.get_workload_combined(relbranch)
    return_value.update(dict(headers=headers))
    return_value.update(dict(packages=workload.items()))
    return return_value


@register.inclusion_tag(
    os.path.join("releases", "_workload_detailed.html")
)
def tag_workload_detailed(relbranch):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    headers, workload = graph_manager.get_workload_detailed(relbranch)
    return_value.update(dict(headers=headers))
    return_value.update(dict(packages=workload.items()))
    return return_value


@register.inclusion_tag(
    os.path.join("releases", "_releases_summary.html")
)
def tag_releases_summary():
    return_value = OrderedDict()
    reports_manager = ReportsManager()
    releases_summary = reports_manager.get_reports('releases')
    if releases_summary:
        report = releases_summary.get().report_json_str
        release_report_json = json.loads(report) if isinstance(report, str) else {}
        pkg_manager = PackagesManager()
        lang_locale_dict = {lang: locale for locale, lang in pkg_manager.get_locale_lang_tuple()}
        for release, summary in release_report_json.items():
            if summary.get('languages'):
                release_report_json[release]['languages'] = \
                    OrderedDict(sorted(summary['languages'].items()))
        return_value.update(dict(
            relsummary=release_report_json,
            last_updated=releases_summary.get().report_updated,
            lang_locale=lang_locale_dict
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
            pkgsummary=json.loads(packages_summary.get().report_json_str),
            last_updated=packages_summary.get().report_updated,
            package_count=package_manager.count_packages(),
        ))
    return return_value


@register.inclusion_tag(
    os.path.join("jobs", "_job_form.html")
)
def tag_job_form(template_type):
    return_value = OrderedDict()
    job_template_manager = JobTemplateManager()
    filter_kwargs = {}
    if template_type in TS_JOB_TYPES:
        filter_kwargs['job_template_type'] = template_type
    templates = job_template_manager.get_job_templates(**filter_kwargs)
    if templates and len(templates) > 0:
        if len(templates) == 1:
            return_value['job_template'] = templates[0]
            return_value['yml_file'] = yaml.dump(
                templates[0].job_template_json, default_flow_style=False
            ).replace("\'", "")
            return_value['job_params'] = templates[0].job_template_params
        return_value['job_templates'] = templates.values()
    package_manager = PackagesManager()
    release_streams = \
        package_manager.get_release_streams(
            only_active=True, fields=('product_build_system',)
        )
    available_build_systems = []
    for relstream in release_streams:
        available_build_systems.append(relstream.product_build_system)
    if available_build_systems:
        return_value['build_systems'] = available_build_systems
    packages = package_manager.get_package_name_tuple(check_mapping=True)
    if packages:
        return_value['packages'] = packages
    relbranch_manager = ReleaseBranchManager()
    release_branches = relbranch_manager.get_relbranch_name_slug_tuple()
    if release_branches:
        return_value['releases'] = release_branches
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
