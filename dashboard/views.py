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

import csv
from datetime import datetime

# django
from django.contrib import messages
from django.forms.utils import ErrorList
from django.http import (
    HttpResponse, HttpResponseRedirect, JsonResponse, Http404
)
from django.shortcuts import render
from django.template import Context, Template
from django.views.generic import (
    TemplateView, ListView, FormView
)
from django.urls import reverse

# dashboard
from dashboard.forms import (
    NewPackageForm, NewReleaseBranchForm, NewGraphRuleForm
)
from dashboard.managers.inventory import (
    InventoryManager, PackagesManager, ReleaseBranchManager
)
from dashboard.managers.jobs import (
    JobsLogManager, TransplatformSyncManager,
    ReleaseScheduleSyncManager
)
from dashboard.managers.graphs import GraphManager
from dashboard.managers.upstream import UpstreamManager
from dashboard.constants import APP_DESC, TS_JOB_TYPES


class ManagersMixin(object):
    """
    Managers Mixin
    """
    inventory_manager = InventoryManager()
    packages_manager = PackagesManager()
    jobs_log_manager = JobsLogManager()
    release_branch_manager = ReleaseBranchManager()
    graph_manager = GraphManager()


class TranStatusTextView(ManagersMixin, TemplateView):
    """
    Translation Status Text View
    """
    template_name = "stats/text_based.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)
        context_data['description'] = APP_DESC
        packages = self.packages_manager.get_package_name_tuple(t_status=True)
        if packages:
            context_data['packages'] = packages
        return context_data


class TranStatusGraphView(ManagersMixin, TemplateView):
    """
    Translation Status Graph View
    """
    template_name = "stats/graph_based.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)
        context_data['description'] = APP_DESC
        packages = self.packages_manager.get_package_name_tuple()
        langs = self.inventory_manager.get_locale_lang_tuple()
        if packages:
            context_data['packages'] = packages
        if langs:
            context_data['languages'] = sorted(langs, key=lambda x: x[1])
        return context_data


class TransCoverageView(ManagersMixin, TemplateView):
    """
    Translation Coverage View
    """
    template_name = "stats/custom_graph.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)
        context_data['description'] = APP_DESC
        graph_rules = self.graph_manager.get_graph_rules(only_active=True)
        if graph_rules:
            context_data['rules'] = graph_rules
        return context_data


class WorkloadEstimationView(ManagersMixin, TemplateView):
    """
    Workload Estimation View
    """
    template_name = "stats/workload_lang_wise.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context_data = super(WorkloadEstimationView, self).get_context_data(**kwargs)
        relbranches = self.release_branch_manager.get_relbranch_name_slug_tuple()
        context_data['description'] = APP_DESC
        context_data['relbranches'] = relbranches
        return context_data


class WorkloadCombinedView(ManagersMixin, TemplateView):
    """
    All languages combined workload estimation view
    """
    template_name = "stats/workload_combined.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context_data = super(WorkloadCombinedView, self).get_context_data(**kwargs)
        relbranches = self.release_branch_manager.get_relbranch_name_slug_tuple()
        context_data['description'] = APP_DESC
        context_data['relbranches'] = relbranches
        return context_data


class WorkloadDetailedView(WorkloadCombinedView):
    """
    Detailed Workload Estimation View
    """
    template_name = "stats/workload_detailed.html"


class AppSettingsView(ManagersMixin, TemplateView):
    """
    Application Settings List View
    """
    template_name = "settings/summary.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context = super(TemplateView, self).get_context_data(**kwargs)
        locales_set = self.inventory_manager.get_locales_set()
        context['locales'] = len(locales_set[0]) \
            if isinstance(locales_set, tuple) else 0
        platforms = self.inventory_manager.get_transplatform_slug_url()
        context['platforms'] = len(platforms) if platforms else 0
        relstreams = self.inventory_manager.get_relstream_slug_name()
        context['streams'] = len(relstreams) if relstreams else 0
        relbranches = self.release_branch_manager.get_release_branches()
        context['branches'] = relbranches.count() if relbranches else 0
        context['packages'] = self.packages_manager.count_packages()
        jobs_count, last_ran_on, last_ran_type = \
            self.jobs_log_manager.get_joblog_stats()
        context['jobs_count'] = jobs_count
        context['job_last_ran_on'] = last_ran_on
        context['job_last_ran_type'] = last_ran_type
        graph_rules = self.graph_manager.get_graph_rules(only_active=True)
        context['graph_rules'] = graph_rules.count() if graph_rules else 0
        return context


class LanguagesSettingsView(ManagersMixin, ListView):
    """
    Languages Settings View
    """
    template_name = "settings/languages.html"
    context_object_name = 'locales'

    def get_queryset(self):
        return self.inventory_manager.get_locales()

    def get_context_data(self, **kwargs):
        context = super(LanguagesSettingsView, self).get_context_data(**kwargs)
        locales_set = self.inventory_manager.get_locales_set()
        language_sets = self.inventory_manager.get_langsets()
        langset_color_dict = {}
        for langset in language_sets:
            langset_color_dict.update({langset.lang_set_slug: langset.lang_set_color})
        locale_groups = self.inventory_manager.get_all_locales_groups()
        if isinstance(locales_set, tuple):
            active_locales, inactive_locales, aliases = locales_set
            context['active_locales_len'] = len(active_locales)
            context['inactive_locales_len'] = len(inactive_locales)
            context['aliases_len'] = len(aliases)
            context['language_sets'] = language_sets
            context['langset_color_dict'] = langset_color_dict
            context['locale_groups'] = locale_groups
        return context


class TransPlatformSettingsView(ManagersMixin, ListView):
    """
    Translation Platform Settings View
    """
    template_name = "settings/transplatforms.html"
    context_object_name = 'platforms'

    def get_queryset(self):
        return self.inventory_manager.get_translation_platforms()

    def get_context_data(self, **kwargs):
        context = super(TransPlatformSettingsView, self).get_context_data(**kwargs)
        platforms_set = self.inventory_manager.get_translation_platforms()
        if isinstance(platforms_set, tuple):
            active_platforms, inactive_platforms = platforms_set
            context['active_platforms_len'] = len(active_platforms)
            context['inactive_platforms_len'] = len(inactive_platforms)
        return context


class ReleaseStreamSettingsView(ManagersMixin, ListView):
    """
    Release Streams Settings View
    """
    template_name = "settings/release_streams.html"
    context_object_name = 'relstreams'

    def get_queryset(self):
        return self.inventory_manager.get_release_streams()


class StreamBranchesSettingsView(ManagersMixin, TemplateView):
    """
    Stream Branches Settings View
    """
    template_name = "settings/stream_branches.html"

    def get_context_data(self, **kwargs):
        context = super(StreamBranchesSettingsView, self).get_context_data(**kwargs)
        relstream_slug = kwargs.get('stream_slug')
        if relstream_slug:
            try:
                release_stream = self.inventory_manager.get_release_streams(stream_slug=relstream_slug).get()
                release_branches = self.release_branch_manager.get_release_branches(relstream=relstream_slug)
            except:
                raise Http404("ReleaseStream matching query does not exist.")
            else:
                context['relstream'] = release_stream
                context['relbranches'] = release_branches
        return context


class NewReleaseBranchView(ManagersMixin, FormView):
    """
    New Release Branch View
    """
    template_name = "settings/relbranch_new.html"

    def _get_relstream(self):
        try:
            release_stream = self.inventory_manager.get_release_streams(
                stream_slug=self.kwargs.get('stream_slug'), only_active=True
            ).get()
        except:
            raise Http404("ReleaseStream matching query does not exist.")
        else:
            return release_stream

    def _get_langsets(self):
        return self.inventory_manager.get_langsets()

    def get_context_data(self, **kwargs):
        context = super(NewReleaseBranchView, self).get_context_data(**kwargs)
        context['relstream'] = self._get_relstream()
        return context

    def get_initial(self):
        initials = {}
        initials.update(dict(lang_set='default'))
        initials.update(dict(enable_flags=['track_trans_flag', 'sync_calendar']))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        release_stream = self._get_relstream()
        lang_sets = self._get_langsets()
        kwargs.update({'action_url': reverse('settings-stream-branches-new', args=[release_stream.relstream_slug])})
        kwargs.update({'phases_choices': tuple([(phase, phase) for phase in release_stream.relstream_phases])})
        kwargs.update({'langset_choices': tuple([(set.lang_set_slug, set.lang_set_name) for set in lang_sets])})
        kwargs.update({'initial': self.get_initial()})
        if data:
            kwargs.update({'data': data})
        return NewReleaseBranchForm(**kwargs)

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_data)
        post_params = form.cleaned_data
        relstream = kwargs.get('stream_slug')
        # Check for required params
        required_params = ('relbranch_name', 'current_phase', 'lang_set', 'calendar_url')
        if not set(required_params) <= set(post_params.keys()):
            return render(request, self.template_name, {'form': form})
        relbranch_slug, schedule_json = \
            self.release_branch_manager.validate_branch(relstream, **post_params)
        if not schedule_json:
            errors = form._errors.setdefault('calendar_url', ErrorList())
            errors.append("Please check calendar URL, could not parse required dates!")
        if schedule_json:
            success_url = reverse('settings-stream-branches-new', args=[relstream])
            post_params['schedule_json'] = schedule_json
            post_params['relbranch_slug'] = relbranch_slug
            active_user = getattr(request, 'user', None)
            if active_user:
                post_params['created_by'] = active_user.email
            if not self.release_branch_manager.add_relbranch(relstream, **post_params):
                messages.add_message(request, messages.ERROR, (
                    'Alas! Something unexpected happened. Please try adding release branch again!'
                ))
            else:
                messages.add_message(request, messages.SUCCESS, (
                    'Great! Release branch added successfully.'
                ))
            return HttpResponseRedirect(success_url)
        return render(request, self.template_name, {
            'form': form, 'relstream': self._get_relstream(), 'POST': 'invalid'
        })


class LogsSettingsView(ManagersMixin, ListView):
    """
    Logs Settings View
    """
    template_name = "settings/logs.html"
    context_object_name = 'logs'

    def get_queryset(self):
        job_logs = self.jobs_log_manager.get_job_logs()
        return job_logs


class PackageSettingsView(ManagersMixin, ListView):
    """
    Packages Settings View
    """
    template_name = "settings/packages.html"
    context_object_name = 'packages'

    def get_queryset(self):
        return self.packages_manager.get_packages()


class NewPackageView(ManagersMixin, FormView):
    """
    New Package Form View
    """
    template_name = "settings/package_new.html"
    success_url = "/settings/packages/new"

    def get_initial(self):
        initials = {}
        initials.update(dict(transplatform_slug='ZNTAFED'))
        initials.update(dict(release_streams='RHEL'))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        active_platforms = \
            self.inventory_manager.get_transplatform_slug_url()
        active_streams = self.inventory_manager.get_relstream_slug_name()
        kwargs.update({'transplatform_choices': active_platforms})
        kwargs.update({'relstream_choices': active_streams})
        kwargs.update({'initial': self.get_initial()})
        if data:
            kwargs.update({'data': data})
        return NewPackageForm(**kwargs)

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_data)
        post_params = form.cleaned_data
        # Check for required fields
        required_params = ('package_name', 'upstream_url', 'transplatform_slug', 'release_streams')
        if not set(required_params) <= set(post_params.keys()):
            return render(request, self.template_name, {'form': form})
        # Validate package with translation platform
        validate_package = self.packages_manager.validate_package(**post_params)
        if not validate_package:
            errors = form._errors.setdefault('package_name', ErrorList())
            errors.append("Not found at selected translation platform")
        if validate_package and form.is_valid():
            post_params['package_name'] = validate_package
            active_user = getattr(request, 'user', None)
            if active_user:
                post_params['created_by'] = active_user.email
            if not self.packages_manager.add_package(**post_params):
                messages.add_message(request, messages.ERROR, (
                    'Alas! Something unexpected happened. Please try adding your package again!'
                ))
            else:
                messages.add_message(request, messages.SUCCESS, (
                    'Great! Package added successfully.'
                ))
            return HttpResponseRedirect(self.success_url)
        return render(request, self.template_name, {'form': form, 'POST': 'invalid'})


class GraphRulesSettingsView(ManagersMixin, ListView):
    """
    Graph Rules Settings View
    """
    template_name = "settings/graph_rules.html"
    context_object_name = 'rules'

    def get_queryset(self):
        return self.graph_manager.get_graph_rules()


class NewGraphRuleView(ManagersMixin, FormView):
    """
    New Graph Rule View
    """
    template_name = "settings/graphrule_new.html"
    success_url = "/settings/graph-rules/new"

    def get_initial(self):
        initials = {}
        initials.update(dict(rule_relbranch='master'))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        pkgs = self.packages_manager.get_package_name_tuple(check_mapping=True)
        langs = self.inventory_manager.get_locale_lang_tuple()
        release_branches_tuple = \
            self.release_branch_manager.get_relbranch_name_slug_tuple()
        kwargs.update({'packages': pkgs})
        kwargs.update({'languages': langs})
        kwargs.update({'branches': release_branches_tuple})
        kwargs.update({'initial': self.get_initial()})
        if data:
            kwargs.update({'data': data})
        return NewGraphRuleForm(**kwargs)

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_data)
        post_params = form.cleaned_data
        # check for required params
        required_params = ('rule_name', 'rule_relbranch', 'rule_packages', 'lang_selection')
        if not set(required_params) <= set(post_params.keys()):
            return render(request, self.template_name, {'form': form})
        elif post_params.get('lang_selection') == 'select' and not post_params.get('rule_langs'):
            errors = form._errors.setdefault('rule_langs', ErrorList())
            errors.append("Please select languages to be included in graph rule.")
            return render(request, self.template_name, {'form': form})
        rule_slug = self.graph_manager.slugify_graph_rule_name(post_params['rule_name'])
        if not rule_slug:
            errors = form._errors.setdefault('rule_name', ErrorList())
            errors.append("This name cannot be slugify. Please try again.")
        pkgs_not_participate = self.graph_manager.validate_package_branch_participation(
            post_params['rule_relbranch'], post_params['rule_packages']
        )
        if pkgs_not_participate and len(pkgs_not_participate) >= 1:
            errors = form._errors.setdefault('rule_packages', ErrorList())
            err_msg = ("Translation progress of " + pkgs_not_participate[0] +
                       " is not being tracked for " + post_params['rule_relbranch'])
            errors.append(err_msg)
        if rule_slug and not pkgs_not_participate:
            post_params['rule_name'] = rule_slug
            active_user = getattr(request, 'user', None)
            if active_user:
                post_params['created_by'] = active_user.email
            if not self.graph_manager.add_graph_rule(**post_params):
                messages.add_message(request, messages.ERROR, (
                    'Alas! Something unexpected happened. Please try adding your rule again!'
                ))
            else:
                messages.add_message(request, messages.SUCCESS, (
                    'Great! Graph rule added successfully.'
                ))
            return HttpResponseRedirect(self.success_url)
        return render(request, self.template_name, {'form': form, 'POST': 'invalid'})


class PackageConfigView(ManagersMixin, TemplateView):
    """
    Package Configuration View
    """
    template_name = "settings/package_config.html"

    def get_context_data(self, **kwargs):
        context = super(PackageConfigView, self).get_context_data(**kwargs)
        queried_package_name = kwargs['package_name'] \
            if 'package_name' in kwargs and kwargs.get('package_name') else ''
        if queried_package_name:
            context['package_name'] = queried_package_name
            try:
                package_details = self.packages_manager.get_packages([queried_package_name]).get()
            except:
                raise Http404("Package matching query does not exist.")
            else:
                pkg_details = package_details.package_details_json
                if pkg_details and pkg_details.get('description'):
                    context['package_details'] = pkg_details['description']
                context['last_sync'] = package_details.transtats_lastupdated
                context['name_mapping'] = package_details.package_name_mapping
        return context


def schedule_job(request):
    """
    Handles job schedule AJAX POST request
    """
    message = "&nbsp;&nbsp;<span class='text-warning'>Request could not be processed.</span>"
    if request.is_ajax():
        job_type = request.POST.dict().get('job')
        if job_type == TS_JOB_TYPES[0]:
            transplatform_sync_manager = TransplatformSyncManager()
            job_uuid = transplatform_sync_manager.syncstats_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='glyphicon glyphicon-check' style='color:green'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/settings/logs'>" + str(job_uuid) + "</a>"
                transplatform_sync_manager.sync_trans_stats()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
        elif job_type == TS_JOB_TYPES[1]:
            relschedule_sync_manager = ReleaseScheduleSyncManager()
            job_uuid = relschedule_sync_manager.syncschedule_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='glyphicon glyphicon-check' style='color:green'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/settings/logs'>" + str(job_uuid) + "</a>"
                relschedule_sync_manager.sync_release_schedule()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
    return HttpResponse(message)


def tabular_data(request):
    """
    Prepares and dispatch tabular data
    """
    if request.is_ajax():
        post_params = request.POST.dict()
        if 'package' in request.POST.dict():
            context = Context(
                {'META': request.META,
                 'package_name': post_params['package']}
            )
            template_string = """
                {% load tag_tabular_form from custom_tags %}
                {% tag_tabular_form package_name %}
            """
            return HttpResponse(Template(template_string).render(context))
    return HttpResponse(status=500)


def graph_data(request):
    """
    Prepares and dispatch graph data
    """
    graph_dataset = {}
    if request.is_ajax():
        graph_manager = GraphManager()
        if 'package' in request.POST.dict() and 'locale' in request.POST.dict():
            package = request.POST.dict().get('package')
            locale = request.POST.dict().get('locale')
            graph_dataset = graph_manager.get_stats_by_pkg_per_lang(package, locale)
        elif 'package' in request.POST.dict():
            package = request.POST.dict().get('package')
            graph_dataset = graph_manager.get_trans_stats_by_package(package)
        elif 'graph_rule' in request.POST.dict():
            graph_rule = request.POST.dict().get('graph_rule')
            graph_dataset = graph_manager.get_trans_stats_by_rule(graph_rule)
    return JsonResponse(graph_dataset)


def refresh_package(request):
    """
    Package sync and re-build mappings
    """
    if request.is_ajax():
        post_params = request.POST.dict()
        package_manager = PackagesManager()
        task_type = post_params.get('task', '')
        if task_type == "mapBranches" and post_params.get('package'):
            if package_manager.build_branch_mapping(post_params['package']):
                context = Context(
                    {'META': request.META,
                     'package_name': post_params['package']}
                )
                template_string = """
                    {% load tag_branch_mapping from custom_tags %}
                    {% tag_branch_mapping package_name %}
                """
                return HttpResponse(Template(template_string).render(context))
        elif task_type == "syncUpstream" and post_params.get('package'):
            input_package_name = post_params['package']
            package = package_manager.get_packages([input_package_name], ['package_name', 'upstream_url']).get()
            if package:
                upstream_repo = package.upstream_url if package.upstream_url.endswith('.git') \
                    else package.upstream_url + ".git"
                upstream_sync_manager = UpstreamManager(package.package_name, upstream_repo,
                                                        'dashboard/sandbox', package.translation_file_ext)
                job_uuid = upstream_sync_manager.syncupstream_initiate_job()
                if job_uuid and upstream_sync_manager.upstream_trans_stats():
                    return HttpResponse(status=200)
        elif task_type == "syncPlatform" and post_params.get('package'):
            if package_manager.refresh_package(post_params['package']):
                return HttpResponse(status=200)
    return HttpResponse(status=500)


def export_packages(request, **kwargs):
    """
    Exports packages to CSV
    """
    if request.method == 'GET' and kwargs.get('format', '') == 'csv':
        file_name = "ts-packages-%s.csv" % datetime.today().strftime('%d-%m-%Y')
        packages_manager = PackagesManager()
        required_fields = ['package_name', 'upstream_url', 'transplatform_url',
                           'release_streams', 'release_branch_mapping']
        packages = packages_manager.get_packages(pkg_params=required_fields)
        response = HttpResponse(content_type='text/csv', status=200)
        response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
        writer = csv.writer(response)
        writer.writerow([field.replace('_', ' ').title() for field in required_fields])
        for package in packages:
            writer.writerow(
                [package.package_name, package.upstream_url,
                 package.transplatform_url, ', '.join(package.release_streams),
                 package.release_branch_mapping if package.release_branch_mapping
                 else ''])
        return response
    return HttpResponse(status=500)


def workload_graph(request):
    """
    Generates workload graph
    """
    graph_dataset = {}
    if request.is_ajax():
        post_params = request.POST.dict()
        if post_params.get('relbranch') and post_params.get('lang'):
            context = Context(
                {'META': request.META,
                 'relbranch': post_params['relbranch'],
                 'locale': post_params['lang']}
            )
            template_string = """
                {% load tag_workload_per_lang from custom_tags %}
                {% tag_workload_per_lang relbranch locale %}
            """
            return HttpResponse(Template(template_string).render(context))
        elif post_params.get('relbranch') and post_params.get('combine'):
            context = Context(
                {'META': request.META,
                 'relbranch': post_params['relbranch']}
            )
            template_string = """
                {% load tag_workload_combined from custom_tags %}
                {% tag_workload_combined relbranch %}
            """
            return HttpResponse(Template(template_string).render(context))
        elif post_params.get('relbranch') and post_params.get('detail'):
            context = Context(
                {'META': request.META,
                 'relbranch': post_params['relbranch']}
            )
            template_string = """
                {% load tag_workload_detailed from custom_tags %}
                {% tag_workload_detailed relbranch %}
            """
            return HttpResponse(Template(template_string).render(context))
        elif post_params.get('relbranch'):
            graph_manager = GraphManager()
            graph_dataset = graph_manager.get_workload_graph_data(post_params['relbranch'])
    return JsonResponse(graph_dataset)
