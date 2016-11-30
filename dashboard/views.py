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
from django.contrib import messages
from django.forms.utils import ErrorList
from django.http import (
    HttpResponse, HttpResponseRedirect, JsonResponse
)
from django.shortcuts import render
from django.views.generic import (
    TemplateView, ListView, FormView
)

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


class ManagersMixin(object):
    """
    Managers Mixin
    """
    inventory_manager = InventoryManager()
    packages_manager = PackagesManager()
    jobs_log_manager = JobsLogManager()
    release_branch_manager = ReleaseBranchManager()
    graph_manager = GraphManager()


class HomeTemplateView(ManagersMixin, TemplateView):
    """
    Home Page Template View
    """
    template_name = "stats/index.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)
        context_data['description'] = \
            "translation position of the package for downstream"

        packages = self.packages_manager.get_packages()
        if packages:
            context_data['packages'] = packages
        return context_data


class CustomGraphView(ManagersMixin, TemplateView):
    """
    Home Page Template View
    """
    template_name = "stats/custom_graph.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)
        context_data['description'] = \
            "translation position of the package for downstream"

        graph_rules = self.graph_manager.get_graph_rules(only_active=True)
        if graph_rules:
            context_data['rules'] = graph_rules
        return context_data


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
        if isinstance(locales_set, tuple):
            active_locales, inactive_locales, aliases = locales_set
            context['active_locales_len'] = len(active_locales)
            context['inactive_locales_len'] = len(inactive_locales)
            context['aliases_len'] = len(aliases)
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
            context['relstream'] = \
                self.inventory_manager.get_release_streams(stream_slug=relstream_slug).get()
            context['relbranches'] = \
                self.release_branch_manager.get_release_branches(relstream=relstream_slug)
        return context


class NewReleaseBranchView(ManagersMixin, FormView):
    """
    New Release Branch View
    """
    template_name = "settings/relbranch_new.html"

    def _get_relstream(self):
        return self.inventory_manager.get_release_streams(
            stream_slug=self.kwargs.get('stream_slug'), only_active=True
        ).get()

    def get_context_data(self, **kwargs):
        context = super(NewReleaseBranchView, self).get_context_data(**kwargs)
        context['relstream'] = self._get_relstream()
        return context

    def get_initial(self):
        initials = {}
        initials.update(dict(enable_flags=['track_trans_flag', 'sync_calendar']))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        release_stream = self._get_relstream()
        kwargs.update({'action_url': 'release-stream/' + release_stream.relstream_slug + '/branches/new'})
        kwargs.update({'phases_choices': tuple([(phase, phase) for phase in release_stream.relstream_phases])})
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
        required_params = ('relbranch_name', 'current_phase', 'calendar_url')
        if not set(required_params) <= set(post_params.keys()):
            return render(request, self.template_name, {'form': form})
        relbranch_slug, schedule_json = \
            self.release_branch_manager.validate_branch(relstream, **post_params)
        if not schedule_json:
            errors = form._errors.setdefault('calendar_url', ErrorList())
            errors.append("Please check calendar URL, could not parse required dates!")
        if schedule_json:
            success_url = '/settings/release-stream/' + relstream + '/branches/new'
            post_params['schedule_json'] = schedule_json
            post_params['relbranch_slug'] = relbranch_slug
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
    success_url = '/settings/packages/new'

    def get_initial(self):
        initials = {}
        initials.update(dict(transplatform_slug='ZNTAFED'))
        initials.update(dict(release_streams='RHEL'))
        initials.update(dict(lang_set='default'))
        initials.update(dict(update_stats='stats'))
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
    success_url = '/settings/graph-rules/new'

    def get_initial(self):
        initials = {}
        initials.update(dict(rule_relbranch='master'))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        pkgs = self.packages_manager.get_package_name_tuple()
        langs = self.inventory_manager.get_locale_lang_tuple()
        kwargs.update({'packages': pkgs})
        kwargs.update({'languages': langs})
        kwargs.update({'initial': self.get_initial()})
        if data:
            kwargs.update({'data': data})
        return NewGraphRuleForm(**kwargs)

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_data)
        post_params = form.cleaned_data
        # check for required params
        required_params = ('rule_name', 'rule_packages', 'rule_langs', 'rule_relbranch')
        if not set(required_params) <= set(post_params.keys()):
            return render(request, self.template_name, {'form': form})
        rule_slug = self.graph_manager.slugify_graph_rule_name(post_params['rule_name'])
        if not rule_slug:
            errors = form._errors.setdefault('rule_name', ErrorList())
            errors.append("This name cannot be slugify. Please try again.")
        if rule_slug:
            post_params['rule_name'] = rule_slug
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


def schedule_job(request):
    """
    Handles job schedule AJAX POST request
    """
    message = "&nbsp;&nbsp;<span class='text-warning'>Request could not be processed.</span>"
    if request.is_ajax():
        job_type = request.POST.dict().get('job')
        if job_type == 'synctransplatform':
            transplatform_sync_manager = TransplatformSyncManager(job_type)
            job_uuid = transplatform_sync_manager.syncstats_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='glyphicon glyphicon-check' style='color:green'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/settings/logs'>" + str(job_uuid) + "</a>"
                transplatform_sync_manager.sync_trans_stats()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
        elif job_type == 'syncrelschedule':
            relschedule_sync_manager = ReleaseScheduleSyncManager(job_type)
            job_uuid = relschedule_sync_manager.syncschedule_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='glyphicon glyphicon-check' style='color:green'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/settings/logs'>" + str(job_uuid) + "</a>"
                relschedule_sync_manager.sync_release_schedule()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
            pass
    return HttpResponse(message)


def graph_data(request):
    """
    Prepares and dispatch graph data
    """
    graph_dataset = {}
    if request.is_ajax():
        graph_manager = GraphManager()
        if 'package' in request.POST.dict():
            package = request.POST.dict().get('package')
            graph_dataset = graph_manager.get_trans_stats_by_package(package)
        if 'graph_rule' in request.POST.dict():
            graph_rule = request.POST.dict().get('graph_rule')
            graph_dataset = graph_manager.get_trans_stats_by_rule(graph_rule)
    return JsonResponse(graph_dataset)
