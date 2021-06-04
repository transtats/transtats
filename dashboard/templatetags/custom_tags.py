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
import pytz
import yaml
from datetime import datetime
from collections import OrderedDict
from django import template

from dashboard.constants import BRANCH_MAPPING_KEYS, TS_JOB_TYPES, GIT_REPO_TYPE
from dashboard.managers.graphs import (
    GraphManager, ReportsManager, GeoLocationManager
)
from dashboard.managers.jobs import JobTemplateManager, JobsLogManager
from dashboard.managers.packages import PackagesManager
from dashboard.managers.inventory import ReleaseBranchManager
from dashboard.managers.pipelines import CIPipelineManager


register = template.Library()


@register.filter
def get_item(dict_object, key):
    if not isinstance(dict_object, dict):
        return ''
    return dict_object.get(key)


@register.filter
def id_from_email(email):
    if isinstance(email, str) and '@' in email:
        parts = email.split('@')
        if parts and len(parts) > 0:
            return parts[0]
    return email


@register.filter
def pop_item(dict_object, key):
    if not isinstance(dict_object, dict):
        return ''
    return dict_object.pop(key)


@register.filter
def join_by(sequence, delimiter):
    return delimiter.join(sequence)


@register.filter
def js_id_safe(id_value):
    return id_value.replace("@", "-at-")


@register.filter
def underscore_to_space(string_object):
    return string_object.replace("_", " ")


@register.filter
def subtract(value, arg):
    try:
        return round(value - arg, 2)
    except FloatingPointError:
        return value - arg


@register.filter
def tz_date(timezone):
    try:
        tz_datetime = \
            datetime.now(pytz.timezone(timezone)).time()
    except:
        # pass for now
        return ":"
    return "{}:{}:{}".format(tz_datetime.hour,
                             tz_datetime.minute,
                             tz_datetime.second)


@register.filter
def percent(value):
    """
    find percentage from stats
    :param value: tuple (untranslated, translated, total)
    :return: percentage
    """
    try:
        return int((value[1] * 100) / value[2])
    except Exception:
        return 0


@register.filter
def parse_memsource_time(date_time):
    if not isinstance(date_time, str):
        return date_time
    return str(datetime.strptime(
        date_time, '%Y-%m-%dT%H:%M:%S+0000'
    ))


@register.filter
def is_pkg_exist(pkg_name):
    package_manager = PackagesManager()
    return package_manager.is_package_exist(pkg_name)


@register.filter
def locale_to_languages(locales):
    package_manager = PackagesManager()
    locale_lang = package_manager.get_locale_lang_tuple(locales)
    return [item[1] for item in locale_lang]


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
    release_manager = ReleaseBranchManager()
    return_value = OrderedDict()
    try:
        package_details = package_manager.get_packages([package]).get()
    except:
        # log event, passing for now
        pass
    else:
        branch_mapping = {}
        if package_details.release_branch_mapping_json:
            branch_mapping = package_details.release_branch_mapping_json.copy()
            for k, v in package_details.release_branch_mapping_json.items():
                branch_mapping[k]['product'] = \
                    release_manager.get_product_by_release(k).product_slug

        return_value.update(
            {'package_name': package_details.package_name,
             'branch_mapping':
                 branch_mapping if branch_mapping else package_details.release_branch_mapping_json,
             'mapping_lastupdated': package_details.release_branch_map_last_updated,
             'mapping_keys': BRANCH_MAPPING_KEYS}
        )
    return return_value


@register.inclusion_tag(
    os.path.join("packages", "_latest_builds.html")
)
def tag_latest_builds(package):
    package_manager = PackagesManager()
    return_value = OrderedDict()
    try:
        package_details = package_manager.get_packages([package]).get()
    except:
        # log event, passing for now
        pass
    else:
        return_value.update(
            {
                'package_name': package,
                'latest_builds': package_details.package_latest_builds_json.copy(),
                'builds_lastupdated': package_details.package_latest_builds_last_updated
            }
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
    stats_dict = graph_manager.get_trans_stats_by_package(
        package, prepend_source=True
    )
    headers = stats_dict['ticks']
    stats_data = stats_dict['graph_data']
    return_value.update(
        {'headers': [lang for index, lang in headers],
         'stats_data': stats_data,
         'pkg_desc': stats_dict['pkg_desc']}
    )
    return return_value


@register.inclusion_tag(
    os.path.join("releases", "_workload_per_lang.html")
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
    os.path.join("releases", "_threshold_based.html")
)
def tag_threshold_based(relbranch, threshold):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    if threshold and not isinstance(threshold, int):
        threshold = int(threshold)
    headers, workload, locales = graph_manager.get_threshold_based(
        relbranch, threshold
    )
    return_value.update(dict(headers=headers))
    return_value.update(dict(languages=workload))
    return_value.update(dict(locales=locales))
    return_value.update(dict(threshold=threshold))
    return_value.update(dict(release=relbranch))
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
    available_build_systems = {}
    for relstream in release_streams:
        available_build_systems.update({relstream.product_slug: relstream.product_build_system})
    if available_build_systems:
        return_value['build_systems'] = available_build_systems
    packages = package_manager.get_package_name_tuple(check_mapping=True)
    if packages:
        return_value['packages'] = packages
    relbranch_manager = ReleaseBranchManager()
    release_branches = relbranch_manager.get_relbranch_name_slug_tuple()
    if release_branches:
        return_value['releases'] = release_branches
    ci_pipeline_manager = CIPipelineManager()
    ci_pipelines = ci_pipeline_manager.get_ci_pipelines()
    if ci_pipelines:
        return_value['ci_pipelines'] = ci_pipelines.all()
    return_value['git_repo_types'] = GIT_REPO_TYPE
    return return_value


@register.inclusion_tag(
    os.path.join("jobs", "_build_tags.html")
)
def tag_build_tags(buildsys, product):
    return_value = OrderedDict()
    package_manager = PackagesManager()
    tags = package_manager.get_build_tags(
        buildsys=buildsys, product_slug=product
    )
    return_value.update(dict(
        build_tags=tags
    ))
    return return_value


@register.inclusion_tag(
    os.path.join("jobs", "_repo_branches.html")
)
def tag_repo_branches(package_name, repo_type):
    return_value = OrderedDict()
    package_manager = PackagesManager()
    branches = package_manager.git_branches(
        package_name, repo_type
    )
    return_value.update(dict(branches=branches))
    return return_value


@register.inclusion_tag(
    os.path.join("jobs", "_job_analysis.html")
)
def tag_job_analysis(job_details):
    return_value = OrderedDict()
    job_log_manager = JobsLogManager()
    analysed_data = \
        job_log_manager.analyse_job_data(job_details)
    return_value.update(dict(
        job_info=analysed_data
    ))
    return return_value


@register.inclusion_tag(
    os.path.join("coverage", "_coverage_table.html")
)
def tag_coverage_view(coverage_rule):
    return_value = OrderedDict()
    graph_manager = GraphManager()
    rule_data, pkg_len, locale_len, tag_len, release_name = \
        graph_manager.get_trans_stats_by_rule(coverage_rule)
    return_value.update(dict(
        coverage_rule=coverage_rule,
        rule_data=rule_data,
        package_len=pkg_len,
        locale_len=locale_len,
        build_tag_len=tag_len,
        release=release_name
    ))
    return return_value


@register.inclusion_tag(
    os.path.join("coverage", "_sync_from_coverage.html")
)
def tag_sync_from_coverage(stats, package, release, tag):
    return_value = OrderedDict()
    if not isinstance(stats, str):
        return return_value
    if isinstance(stats, str) and not stats.startswith('Not Synced with'):
        return return_value
    package_manager = PackagesManager()
    release_manager = ReleaseBranchManager()
    try:
        package_details = package_manager.get_packages([package]).get()
    except:
        # log event, passing for now
        pass
    else:
        branch_mapping = {}
        if package_details.release_branch_mapping_json:
            branch_mapping = package_details.release_branch_mapping_json.copy()
            if release in branch_mapping:
                branch_mapping = branch_mapping.get(release)
                branch_mapping['product'] = \
                    release_manager.get_product_by_release(release).product_slug
        return_value.update(dict(
            mapping=branch_mapping,
            package=package,
            tag=tag,
        ))
    return return_value


@register.inclusion_tag(
    os.path.join("releases", "_release_map_view.html")
)
def tag_release_map_view():
    return_value = OrderedDict()
    release_manager = ReleaseBranchManager()
    latest_release = release_manager.get_latest_release()
    geo_location_manager = GeoLocationManager()
    territory_stats = \
        geo_location_manager.get_territory_build_system_stats()
    if territory_stats:
        return_value["territory_stats"] = territory_stats
    if territory_stats and latest_release:
        return_value["latest_release"] = latest_release
    return return_value


@register.inclusion_tag(
    os.path.join("releases", "_trending_languages.html")
)
def tag_trending_languages():
    return_value = OrderedDict()
    reports_manager = ReportsManager()
    releases_summary = reports_manager.get_reports('releases')
    release_manager = ReleaseBranchManager()
    latest_release = release_manager.get_latest_release()
    pkg_manager = PackagesManager()
    lang_locale_dict = {lang: locale for locale, lang in pkg_manager.get_locale_lang_tuple()}

    if releases_summary and latest_release:
        releases_summary = releases_summary.get()
        trending_languages = reports_manager.get_trending_languages(
            releases_summary.report_json, *latest_release
        )
        if trending_languages and isinstance(trending_languages, (list, tuple)):
            return_value["trending_languages"] = trending_languages[:9]
            return_value["lang_locale_dict"] = lang_locale_dict
            return_value["latest_release"] = latest_release
    return return_value


@register.inclusion_tag(
    os.path.join("releases", "_outofsync_packages.html")
)
def tag_outofsync_packages():
    return_value = OrderedDict()
    package_manager = PackagesManager()
    all_packages = package_manager.get_packages()
    outofsync_packages = \
        [i.package_name for i in all_packages if not i.stats_diff_health]
    if all_packages and outofsync_packages:
        return_value["insync_packages"] = \
            (all_packages.count() - len(outofsync_packages)) or 0
    return_value["outofsync_packages"] = len(outofsync_packages) or 0
    return_value["total_packages"] = all_packages.count() or 0
    return return_value


@register.inclusion_tag(
    os.path.join("geolocation", "_territory_summary.html")
)
def tag_location_summary(country_code):
    return_value = OrderedDict()
    geo_location_manager = GeoLocationManager()
    territory_stats, last_updated = \
        geo_location_manager.get_territory_summary(country_code)
    if territory_stats:
        return_value["territory_stats"] = territory_stats
    if last_updated:
        return_value["last_updated"] = last_updated
    return_value["country_code"] = country_code
    return return_value


@register.inclusion_tag(
    os.path.join("ci", "_ci_pipeline.html")
)
def tag_ci_pipelines(request, package_name):
    return_value = OrderedDict()
    package_manager = PackagesManager()
    ci_pipeline_manager = CIPipelineManager()
    pipelines = ci_pipeline_manager.get_ci_pipelines(
        packages=package_manager.get_packages(pkgs=[package_name])
    )
    return_value['request'] = request
    return_value['pipelines'] = pipelines
    return return_value


@register.inclusion_tag(
    os.path.join("jobs", "_target_langs.html")
)
def tag_target_langs(ci_pipeline):
    return_value = OrderedDict()
    if not ci_pipeline:
        return return_value
    ci_pipeline_manager = CIPipelineManager()
    pipelines = ci_pipeline_manager.get_ci_pipelines(
        uuids=[ci_pipeline])
    pipeline = pipelines.first()
    if pipeline:
        return_value['target_langs'] = \
            pipeline.ci_project_details_json.get('targetLangs') or []
    return return_value


@register.inclusion_tag(
    os.path.join("ci", "_pipeline_workflow_steps.html")
)
def tag_pipeline_workflow_steps(pipeline_jobs):
    return_value = OrderedDict()
    p_jobs_group = dict()
    for pipeline_job in pipeline_jobs:
        workflow_step = pipeline_job.get('workflowStep')
        if not workflow_step:
            # As workflowStep is a project level settings
            # it is safe to determine just by first (one) job
            return_value['platform_jobs'] = pipeline_jobs
            return return_value
        workflow_name = pipeline_job.get('workflowStep', {}).get('name')
        if workflow_name not in p_jobs_group:
            p_jobs_group[workflow_name] = []
        p_jobs_group[workflow_name].append(pipeline_job)
    return_value['platform_job_groups'] = p_jobs_group
    return return_value


@register.inclusion_tag(
    os.path.join("jobs", "_workflow_steps.html")
)
def tag_workflow_steps_dropdown(ci_pipeline):
    return_value = OrderedDict()
    if not ci_pipeline:
        return return_value
    ci_pipeline_manager = CIPipelineManager()
    workflow_steps = ci_pipeline_manager.get_ci_platform_workflow_steps(
        pipeline_uuid=ci_pipeline
    )
    return_value['workflow_steps'] = workflow_steps
    return return_value
