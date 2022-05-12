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

import os
import ast
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
import threading

# django
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.forms.utils import ErrorList
from django.http import (
    HttpResponse, HttpResponseRedirect, JsonResponse, Http404
)
from django.shortcuts import render
from django.template import Context, Template
from django.views.generic import (
    TemplateView, ListView, FormView, DetailView
)
from django.views.generic.edit import (CreateView, UpdateView, DeleteView)
from django.urls import reverse, reverse_lazy

# dashboard

from dashboard.constants import (
    TS_JOB_TYPES, TRANSPLATFORM_ENGINES, RELSTREAM_SLUGS,
    WEBLATE_SLUGS, TRANSIFEX_SLUGS, TS_CI_JOBS, PIPELINE_CONFIG_EVENTS,
    JOB_MULTIPLE_BRANCHES_VAR, TP_BRANCH_CALLING_NAME, SYS_EMAIL_ADDR
)
from dashboard.forms import (
    NewPackageForm, UpdatePackageForm, NewReleaseBranchForm, NewGraphRuleForm,
    NewLanguageForm, UpdateLanguageForm, LanguageSetForm, PackagePipelineForm,
    NewTransPlatformForm, UpdateTransPlatformForm, UpdateGraphRuleForm,
    CreateCIPipelineForm
)
from dashboard.managers.inventory import (
    InventoryManager, ReleaseBranchManager, SyncStatsManager
)
from dashboard.managers.packages import PackagesManager
from dashboard.managers.pipelines import (
    CIPipelineManager, PipelineConfigManager
)
from dashboard.managers.jobs import (
    YMLBasedJobManager, JobsLogManager, TransplatformSyncManager,
    ReleaseScheduleSyncManager, BuildTagsSyncManager, JobTemplateManager
)
from dashboard.managers.graphs import (
    GraphManager, ReportsManager, GeoLocationManager
)
from dashboard.models import (
    Job, Language, LanguageSet, Platform, Visitor, Package,
    GraphRule, SyncStats, CacheBuildDetails, CIPipeline, PipelineConfig
)


class ManagersMixin(object):
    """
    Managers Mixin
    """
    inventory_manager = InventoryManager()
    packages_manager = PackagesManager()
    jobs_log_manager = JobsLogManager()
    jobs_template_manager = JobTemplateManager()
    release_branch_manager = ReleaseBranchManager()
    graph_manager = GraphManager()
    reports_manager = ReportsManager()
    geo_location_manager = GeoLocationManager()
    ci_pipeline_manager = CIPipelineManager()
    pipeline_config_manager = PipelineConfigManager()

    def get_summary(self):
        """
        Application Inventory Stats
        """
        locales_set = self.inventory_manager.get_locales_set()
        summary = {}
        summary['locales_len'] = len(locales_set[0]) \
            if isinstance(locales_set, tuple) and len(locales_set) > 0 else 0
        platforms = self.inventory_manager.get_transplatform_slug_url()
        summary['platforms_len'] = len(platforms) if platforms else 0
        # relstreams = self.inventory_manager.get_relstream_slug_name()
        # summary['products_len'] = len(relstreams) if relstreams else 0
        # relbranches = self.release_branch_manager.get_release_branches()
        # summary['releases_len'] = relbranches.count() if relbranches else 0
        summary['packages_len'] = self.packages_manager.count_packages()
        jobs_templates_count = self.jobs_template_manager.get_job_templates().count()
        summary['jobs_templates_len'] = jobs_templates_count
        # coverage = self.graph_manager.get_graph_rules(only_active=True)
        # summary['graph_rules_len'] = coverage.count() if coverage else 0
        return summary

    @staticmethod
    def log_visitor(http_meta):
        """
        log visitors
        """
        x_forwarded_for = http_meta.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[-1].strip() \
            if x_forwarded_for else http_meta.get('REMOTE_ADDR')
        http_params = {}
        match_params = {
            'visitor_ip': ip,
            'visitor_user_agent': http_meta.get('HTTP_USER_AGENT')
        }
        http_params.update(match_params)
        http_params['visitor_accept'] = http_meta.get('HTTP_ACCEPT')
        http_params['visitor_encoding'] = http_meta.get('HTTP_ACCEPT_ENCODING')
        http_params['visitor_language'] = http_meta.get('HTTP_ACCEPT_LANGUAGE')
        http_params['visitor_host'] = http_meta.get('REMOTE_HOST')
        try:
            Visitor.objects.update_or_create(
                **match_params, defaults=http_params
            )
        except Exception as e:
            pass


class TranStatusPackageView(ManagersMixin, TemplateView):
    """
    Translation Status Package View
    """
    template_name = "packages/package_view.html"

    def get(self, request, *args, **kwargs):
        response = super(TranStatusPackageView, self).get(
            request, *args, **kwargs)
        if not self.packages_manager.is_package_exist(
                kwargs.get('package_name', '')):
            raise Http404("Package does not exist.")
        return response

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context = super(TranStatusPackageView, self).get_context_data(**kwargs)
        packages = self.packages_manager.get_package_name_tuple()
        langs = self.inventory_manager.get_locale_lang_tuple()
        if packages:
            context['packages'] = packages
        if langs:
            context['languages'] = sorted(langs, key=lambda x: x[1])
        return context


class TranStatusReleasesView(ManagersMixin, TemplateView):
    """
    Translation Status Releases View
    This view is for current landing page.
    """
    template_name = "releases/release_list.html"

    def get(self, request, *args, **kwargs):
        http_meta = self.request.META.copy()
        self.log_visitor(http_meta)
        return super(TranStatusReleasesView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context = super(TranStatusReleasesView, self).get_context_data(**kwargs)
        relbranches = self.release_branch_manager.get_relbranch_name_slug_tuple()
        context['releases'] = relbranches
        products = self.inventory_manager.get_release_streams()
        if self.request.tenant in RELSTREAM_SLUGS:
            products = products.filter(**{'product_slug': self.request.tenant})
        context['relstreams'] = products
        product_releases = self.release_branch_manager.get_branches_of_relstreams(products)
        p_releases_dict = {}
        if product_releases is not None and isinstance(product_releases, dict):
            for product, releases in product_releases.items():
                p_releases_dict[product] = len(releases) or 0
        context['p_releases_dict'] = p_releases_dict if p_releases_dict \
            else {p.product_slug: 0 for p in products}
        context.update(self.get_summary())
        return context


class TranStatusReleaseView(ManagersMixin, TemplateView):
    """
    Translation Status Release View
    """
    template_name = "releases/release_view.html"

    def get_context_data(self, **kwargs):
        context = super(TranStatusReleaseView, self).get_context_data(**kwargs)
        if not self.release_branch_manager.is_relbranch_exist(
                kwargs.get('release_branch', '')):
            raise Http404("Release does not exist.")
        langs = self.inventory_manager.get_locale_lang_tuple()
        if langs:
            context['languages'] = sorted(langs, key=lambda x: x[1])
        relbranches = self.release_branch_manager.get_relbranch_name_slug_tuple()
        context['releases'] = relbranches
        release_stream = self.release_branch_manager.get_release_branches(
            relbranch=kwargs.get('release_branch'), fields=['product_slug']).get()
        if release_stream:
            context['release_stream'] = release_stream.product_slug.product_slug
        context['release_branch'] = kwargs.get('release_branch')
        return context


class TransCoverageView(ManagersMixin, TemplateView):
    """
    Translation Coverage View
    """
    template_name = "coverage/coverage_rule_view.html"

    def get(self, request, *args, **kwargs):
        rule = self.graph_manager.get_graph_rules(
            graph_rule=kwargs.get('coverage_rule', '')
        )
        if not rule:
            raise Http404("Coverage rule does not exist.")
        elif not rule.get().rule_visibility_public and \
                not request.user.is_authenticated:
            raise PermissionDenied
        return super(TransCoverageView, self).get(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        """
        context = super(TransCoverageView, self).get_context_data(**kwargs)
        graph_rules = self.graph_manager.get_graph_rules(only_active=True)
        if graph_rules:
            context['rules'] = graph_rules
        return context


class LanguagesSettingsView(ManagersMixin, ListView):
    """
    Languages List View
    """
    template_name = "languages/language_list.html"
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
        if isinstance(locales_set, tuple) and len(locales_set) >= 3:
            active_locales, inactive_locales, aliases = locales_set
            context['active_locales_len'] = len(active_locales)
            context['inactive_locales_len'] = len(inactive_locales)
            context['aliases_len'] = len(aliases)
            context['language_sets'] = language_sets
            context['langset_color_dict'] = langset_color_dict
            context['locale_groups'] = locale_groups
        return context


class LanguageDetailView(ManagersMixin, DetailView):
    """
    Languages Detail View
    """
    template_name = "languages/language_view.html"
    context_object_name = 'language'
    model = Language
    slug_field = 'locale_id'
    slug_url_kwarg = 'locale_id'

    def get_context_data(self, **kwargs):
        context = super(LanguageDetailView, self).get_context_data(**kwargs)
        locale_lang_tuple = self.inventory_manager.get_locale_lang_tuple()
        release_summary = self.reports_manager.get_reports('releases')
        if release_summary:
            release_summary = release_summary.get()
        language_teams = \
            self.inventory_manager.get_platform_language_team_contact(
                kwargs['object'].locale_id
            )
        if language_teams:
            context["language_teams"] = language_teams
        context["locale_lang"] = locale_lang_tuple
        if release_summary:
            release_report_json = release_summary.report_json
            if self.request.tenant in RELSTREAM_SLUGS:
                release_report_json = {k: v for k, v in release_summary.report_json.items()
                                       if self.request.tenant.lower() in v.get('slug').lower()}
            context["release_summary"] = release_report_json
            context["last_updated"] = release_summary.report_updated
        return context


class LanguageReleaseView(ManagersMixin, TemplateView):
    """
    Language Release View
    """

    template_name = "languages/language_release_view.html"

    def get_context_data(self, **kwargs):
        context = super(LanguageReleaseView, self).get_context_data(**kwargs)
        language_query = \
            self.inventory_manager.get_locales(pick_locales=[kwargs['locale']])
        if language_query:
            context["language"] = language_query.get()
        return context


class TransPlatformSettingsView(ManagersMixin, ListView):
    """
    Translation Platform Settings View
    """
    template_name = "platforms/platform_list.html"
    context_object_name = 'platforms'

    def get_queryset(self):
        return self.inventory_manager.get_translation_platforms()

    def get_context_data(self, **kwargs):
        context = super(TransPlatformSettingsView, self).get_context_data(**kwargs)
        platforms_set = self.inventory_manager.get_transplatforms_set()
        if isinstance(platforms_set, tuple):
            active_platforms, inactive_platforms = platforms_set
            context['active_platforms_len'] = len(active_platforms)
            context['inactive_platforms_len'] = len(inactive_platforms)
        # Join supported platform names with ',' and make it titlecase
        context['transplatform_engines'] = ', '.join(TRANSPLATFORM_ENGINES).title()
        return context


class StreamBranchesSettingsView(ManagersMixin, TemplateView):
    """
    Stream Branches Settings View
    """
    template_name = "releases/product_release_list.html"

    def get_context_data(self, **kwargs):
        context = super(StreamBranchesSettingsView, self).get_context_data(**kwargs)
        relstream_slug = kwargs.get('stream_slug')
        if relstream_slug:
            try:
                release_stream = self.inventory_manager.get_release_streams(stream_slug=relstream_slug).get()
                release_branches = self.release_branch_manager.get_release_branches(relstream=relstream_slug)
            except Exception:
                raise Http404("Product does not exist.")
            else:
                context['relstream'] = release_stream
                context['relbranches'] = release_branches
        return context


class NewReleaseBranchView(ManagersMixin, FormView):
    """
    New Release Branch View
    """
    template_name = "releases/product_release_new.html"

    def _get_relstream(self):
        try:
            release_stream = self.inventory_manager.get_release_streams(
                stream_slug=self.kwargs.get('stream_slug'), only_active=True
            ).get()
        except Exception:
            raise Http404("Product does not exist.")
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
        kwargs.update({'action_url': reverse('settings-stream-branches-new', args=[release_stream.product_slug])})
        kwargs.update({'phases_choices': tuple([(phase, phase) for phase in release_stream.product_phases])})
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
        required_params = ('release_name', 'current_phase', 'lang_set', 'calendar_url')
        if not set(required_params) <= set(post_params.keys()):
            return render(request, self.template_name, {'form': form})
        relbranch_slug, schedule_json = \
            self.release_branch_manager.validate_branch(relstream, **post_params)
        if not schedule_json:
            errors = form._errors.setdefault('calendar_url', ErrorList())
            errors.append("Please check calendar URL, could not parse required dates!")
        if schedule_json:
            success_url = reverse('settings-stream-branches-new', args=[relstream])
            post_params['schedule_json_str'] = json.dumps(schedule_json)
            post_params['release_slug'] = relbranch_slug
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


class PackageSettingsView(ManagersMixin, ListView):
    """
    Packages Settings View
    """
    template_name = "packages/package_list.html"
    context_object_name = 'packages'

    def get_queryset(self):
        return self.packages_manager.get_packages()


class NewPackageView(ManagersMixin, FormView):
    """
    New Package Form View
    """
    template_name = "packages/package_new.html"

    def get_success_url(self):
        return reverse('package-new')

    def get_initial(self):
        initials = {}
        if self.request.tenant == RELSTREAM_SLUGS[0] or self.request.tenant == RELSTREAM_SLUGS[1]:
            initials.update(dict(transplatform_slug=WEBLATE_SLUGS[1]))
        if self.request.tenant == RELSTREAM_SLUGS[3]:
            initials.update(dict(transplatform_slug=TRANSIFEX_SLUGS[0]))
        default_product = self.request.tenant
        initials.update(dict(release_streams=default_product))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        active_platforms = \
            self.inventory_manager.get_transplatform_slug_url()
        active_streams = self.inventory_manager.get_relstream_slug_name()
        kwargs.update({'platform_choices': active_platforms})
        kwargs.update({'products_choices': active_streams})
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
            messages.add_message(request, messages.ERROR, (
                'One of the required fields is missing.'))
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
                t = threading.Thread(
                    target=self.packages_manager.refresh_package,
                    args=[post_params['package_name']]
                )
                t.daemon = True
                t.start()
            return HttpResponseRedirect(self.get_success_url())
        return render(request, self.template_name, {'form': form, 'POST': 'invalid'})


class UpdatePackageView(ManagersMixin, SuccessMessageMixin, UpdateView):
    """
    Update Package view
    """
    template_name = 'packages/package_update.html'
    model = Package
    slug_field = 'package_name'
    form_class = UpdatePackageForm
    success_message = '%(package_name)s was updated successfully!'

    def get(self, request, *args, **kwargs):
        if kwargs.get('slug') and not request.user.is_staff:
            pkg = self.packages_manager.get_packages(pkgs=[kwargs['slug']]).get()
            if not pkg.created_by == request.user.email and \
                    not request.user.is_superuser:
                raise PermissionDenied
        return super(UpdatePackageView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('package-update', args=[self.object.package_name])


class DeletePackageView(ManagersMixin, SuccessMessageMixin, DeleteView):
    """
    Delete Package view
    """
    template_name = 'packages/package_delete.html'
    model = Package
    slug_field = 'package_name'
    success_message = '%(package_name)s was removed successfully!'

    def get(self, request, *args, **kwargs):
        if kwargs.get('slug') and not request.user.is_superuser:
            raise PermissionDenied
        return super(DeletePackageView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('settings-packages')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # delete all associated jobs
        Job.objects.filter(job_remarks=self.object.package_name).delete()
        # delete all related sync stats and pipelines
        SyncStats.objects.filter(package_name=self.object).delete()
        CIPipeline.objects.filter(ci_package=self.object).delete()
        # delete all cached build details
        CacheBuildDetails.objects.filter(package_name=self.object).delete()
        # now, remove the package
        self.object.delete()
        # return to packages list view
        return HttpResponseRedirect(self.get_success_url())


class GraphRulesSettingsView(ManagersMixin, ListView):
    """
    Graph Rules Settings View
    """
    template_name = "coverage/coverage_rule_list.html"
    context_object_name = 'rules'

    def get_queryset(self):
        return self.graph_manager.get_graph_rules(only_active=True)


class NewGraphRuleView(ManagersMixin, FormView):
    """
    New Graph Rule View
    """
    template_name = "coverage/coverage_rule_new.html"

    def get_success_url(self):
        return reverse('settings-graph-rules-new')

    def get_initial(self):
        initials = {}
        initials.update(dict(rule_relbranch='main'))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        pkgs = self.packages_manager.get_package_name_tuple(check_mapping=True)
        langs = self.inventory_manager.get_locale_lang_tuple()
        release_branches_tuple = \
            self.release_branch_manager.get_relbranch_name_slug_tuple()
        b_tags = []
        build_system_tags = self.inventory_manager.get_relstream_build_tags()
        for release, tags in build_system_tags.items():
            for tag in tags:
                b_tags.append((tag, tag))
        kwargs.update({'packages': pkgs})
        kwargs.update({'languages': langs})
        kwargs.update({'branches': release_branches_tuple})
        kwargs.update({'tags': tuple(b_tags)})
        kwargs.update({'initial': self.get_initial()})
        if data:
            kwargs.update({'data': data})
        return NewGraphRuleForm(**kwargs)

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_data)
        post_params = form.cleaned_data
        # check for required params
        required_params = ('rule_name', 'rule_relbranch', 'rule_packages',
                           'tags_selection', 'lang_selection')
        if not set(required_params) <= set(post_params.keys()):
            return render(request, self.template_name, {'form': form})
        elif post_params.get('tags_selection') == 'pick' and post_params.get('rule_build_tags'):
            post_params['rule_build_tags'] = []
        elif post_params.get('tags_selection') == 'select' and not post_params.get('rule_build_tags'):
            errors = form._errors.setdefault('rule_build_tags', ErrorList())
            errors.append("Please select build tags to be included in coverage rule.")
            return render(request, self.template_name, {'form': form})
        elif post_params.get('lang_selection') == 'select' and not post_params.get('rule_langs'):
            errors = form._errors.setdefault('rule_langs', ErrorList())
            errors.append("Please select languages to be included in coverage rule.")
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
        tags_not_participate = self.graph_manager.validate_tags_product_participation(
            post_params['rule_relbranch'], post_params['rule_build_tags']
        )
        if tags_not_participate and len(tags_not_participate) >= 1:
            errors = form._errors.setdefault('rule_build_tags', ErrorList())
            err_msg = ("Build Tag " + tags_not_participate[0] + " does not belong to " +
                       post_params['rule_relbranch'] + " release.")
            errors.append(err_msg)
        if rule_slug and not pkgs_not_participate and not tags_not_participate:
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
                    'Great! Coverage rule added successfully.'
                ))
            return HttpResponseRedirect(self.get_success_url())
        return render(request, self.template_name, {'form': form, 'POST': 'invalid'})


class UpdateGraphRuleView(ManagersMixin, SuccessMessageMixin, UpdateView):
    """
    Update Graph Rule view
    """
    template_name = 'coverage/coverage_rule_update.html'
    model = GraphRule
    slug_field = 'rule_name'
    form_class = UpdateGraphRuleForm
    success_message = '%(rule_name)s was updated successfully!'

    def get(self, request, *args, **kwargs):
        if kwargs.get('slug') and not request.user.is_staff:
            rule = self.graph_manager.get_graph_rules(graph_rule=kwargs['slug'],
                                                      only_active=True).get()
            if not rule.created_by == request.user.email and \
                    not request.user.is_superuser:
                raise PermissionDenied
        return super(UpdateGraphRuleView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('graph-rule-update', args=[self.kwargs['slug']])


class DeleteGraphRuleView(DeleteView):
    """
    Delete Graph Rule View
    """
    template_name = 'coverage/coverage_rule_delete.html'
    model = GraphRule
    slug_field = 'rule_name'
    success_url = reverse_lazy('settings-graph-rules')

    def get_object(self, queryset=None):

        obj = super(DeleteGraphRuleView, self).get_object()
        if not obj.created_by == self.request.user.email and \
                not self.request.user.is_superuser:
            raise PermissionDenied
        return obj


class JobsView(ManagersMixin, TemplateView):
    """
    Predefined Jobs View
    """
    template_name = "jobs/jobs_home.html"

    def get_context_data(self, **kwargs):
        context = super(JobsView, self).get_context_data(**kwargs)
        jobs_count, last_ran_on, last_ran_type = \
            self.jobs_log_manager.get_joblog_stats()
        context['jobs_count'] = jobs_count
        context['job_last_ran_on'] = last_ran_on
        context['job_last_ran_type'] = last_ran_type
        packages = self.packages_manager.get_package_name_tuple()
        if packages:
            context['packages'] = packages
        return context


class CleanUpJobs(ManagersMixin, TemplateView):
    """
    Predefined Jobs View
    """
    template_name = "jobs/jobs_cleanup.html"

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        sync_stat_to_hide = []
        for k, v in post_data.items():
            if '|' in k:
                sync_stat_to_hide.append(tuple(k.split('|')))
        if sync_stat_to_hide:
            sync_stats_manager = SyncStatsManager()
            for stat in sync_stat_to_hide:
                sync_stats_manager.toggle_visibility(
                    stats_source=stat[0], project_version=stat[1]
                )
        return render(request, self.template_name, self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        context = super(CleanUpJobs, self).get_context_data(**kwargs)
        sync_stats_manager = SyncStatsManager()
        sync_stats = sync_stats_manager.get_sync_stats()
        if sync_stats:
            sync_stats = sync_stats.order_by().values(
                'project_version', 'source'
            ).distinct().exclude(project_version="Upstream").order_by('project_version')
        context['sync_stats'] = sync_stats
        return context


class YMLBasedJobs(JobsView):
    """
    YML Based Jobs View
    """
    template_name = "jobs/jobs_yml_based.html"


class JobsLogsView(ManagersMixin, ListView):
    """
    Logs List View
    """
    template_name = "jobs/logs.html"
    context_object_name = 'logs'

    def get_queryset(self):
        job_logs = self.jobs_log_manager.get_job_logs()
        return job_logs[:50]


class JobsArchiveView(ManagersMixin, ListView):
    """
    Archive List View
    """
    template_name = "jobs/archive.html"
    context_object_name = 'logs'

    def get_queryset(self):
        job_logs = self.jobs_log_manager.get_job_logs()
        return job_logs[50:]


class JobsLogsPackageView(ManagersMixin, ListView):
    """
    Logs List per Package View
    """
    template_name = "jobs/logs.html"
    context_object_name = 'logs'

    def get_queryset(self):
        job_logs = []
        pkg_name = self.request.resolver_match.kwargs.get('package_name')
        if pkg_name:
            job_logs = self.jobs_log_manager.get_job_logs(
                remarks=pkg_name, result=True
            )
        return job_logs


class JobDetailView(DetailView):
    """
    Job Log Detail View
    """
    template_name = "jobs/log_detail.html"
    context_object_name = 'log'
    model = Job
    slug_field = 'job_uuid'
    slug_url_kwarg = 'job_id'


class PipelineDetailView(DetailView):
    """
    Pipeline Detail View
    """
    template_name = "ci/pipeline_jobs.html"
    context_object_name = 'ci_pipeline'
    model = CIPipeline
    slug_field = 'ci_pipeline_uuid'
    slug_url_kwarg = 'pipeline_id'


class PipelineHistoryView(ManagersMixin, PipelineDetailView):
    """
    Pipeline Sync Logs View
    """
    template_name = "ci/pipeline_history.html"

    def get_context_data(self, **kwargs):
        context_data = super(PipelineHistoryView, self).get_context_data(**kwargs)
        sync_logs = self.jobs_log_manager.get_job_logs(
            remarks=self.object.ci_package.package_name, no_pipeline=False)
        if sync_logs:
            context_data["logs"] = sync_logs.filter(**dict(ci_pipeline=self.object))
        return context_data


class PipelineConfigurationView(ManagersMixin, PipelineDetailView):
    """
    Pipeline Configurations View
    """
    template_name = "ci/pipeline_configuration.html"

    def get_context_data(self, **kwargs):
        context_data = super(PipelineConfigurationView, self).get_context_data(**kwargs)
        context_data['pipeline_config_events'] = PIPELINE_CONFIG_EVENTS
        return context_data


class NewLanguageView(SuccessMessageMixin, CreateView):
    """
    New language view
    """
    template_name = "languages/language_new.html"
    form_class = NewLanguageForm
    success_message = '%(lang_name)s was added successfully!'

    def get_success_url(self):
        return reverse('language-new')


class UpdateLanguageView(SuccessMessageMixin, UpdateView):
    """
    Update language view
    """
    template_name = 'languages/language_update.html'
    model = Language
    form_class = UpdateLanguageForm
    success_message = '%(lang_name)s was updated successfully!'

    def get_success_url(self):
        return reverse('language-update', args=[self.object.locale_id])


class NewLanguageSetView(SuccessMessageMixin, CreateView):
    """
    New language set view
    """
    template_name = "languages/language_set_new.html"
    form_class = LanguageSetForm
    success_message = '%(lang_set_name)s was added successfully!'

    def get_success_url(self):
        return reverse('language-set-new')


class UpdateLanguageSetView(SuccessMessageMixin, UpdateView):
    """
    Update language set view
    """
    template_name = "languages/language_set_update.html"
    model = LanguageSet
    form_class = LanguageSetForm
    slug_field = 'lang_set_slug'
    success_message = '%(lang_set_name)s was updated successfully!'

    def get_success_url(self):
        return reverse('language-set-update', args=[self.object.lang_set_slug])


class NewTransPlatformView(SuccessMessageMixin, CreateView):
    """
    New TransPlatform view
    """
    template_name = "platforms/platform_new.html"
    form_class = NewTransPlatformForm
    success_message = '%(platform_slug)s was added successfully!'

    def get_success_url(self):
        return reverse('transplatform-new')


class UpdateTransPlatformView(SuccessMessageMixin, UpdateView):
    """
    Update TransPlatform view
    """
    template_name = "platforms/platform_update.html"
    form_class = UpdateTransPlatformForm
    success_message = '%(platform_slug)s was updated successfully!'
    model = Platform
    slug_field = 'platform_slug'

    def get_success_url(self):
        return reverse('transplatform-update', args=[self.object.platform_slug])


class AddPackageCIPipeline(ManagersMixin, FormView):
    """
    Add Package CI Pipeline View
    """
    template_name = 'ci/add_pipeline.html'
    success_message = '%(ci_pipeline_uuid)s was added successfully!'

    def get(self, request, *args, **kwargs):
        if kwargs.get('slug') and not request.user.is_staff:
            pkg = self.packages_manager.get_packages(pkgs=[kwargs['slug']]).get()
            if not pkg.created_by == request.user.email and \
                    not request.user.is_superuser:
                raise PermissionDenied
        return super(AddPackageCIPipeline, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(AddPackageCIPipeline, self).get_context_data(**kwargs)
        if self.kwargs.get("slug"):
            context_data["package_name"] = self.kwargs.get("slug")
        return context_data

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        package_model_object = self.packages_manager.get_packages(
            [self.kwargs['slug']])
        if not package_model_object:
            return kwargs
        package = package_model_object.get()
        ci_platforms = self.inventory_manager.get_translation_platforms(ci=True)
        ci_platform_choices = tuple([(platform.platform_id, platform.__str__)
                                     for platform in ci_platforms])
        kwargs.update(dict(ci_platform_choices=ci_platform_choices))
        pkg_releases = self.packages_manager.get_package_releases(
            package_name=package.package_name
        )
        pkg_release_choices = tuple([(release.release_id, release.__str__)
                                     for release in pkg_releases])
        pkg_platform_branches = self.packages_manager.git_branches(
            package.package_name, package.platform_slug.engine_name
        )
        pkg_platform_branch_choices = \
            tuple([(branch, branch) for branch in pkg_platform_branches])
        kwargs.update(dict(pkg_platform_branch_choices=pkg_platform_branch_choices))
        pkg_branch_display_name = dict(TP_BRANCH_CALLING_NAME).get(
            package.platform_slug.engine_name, 'Branch')
        if pkg_branch_display_name.endswith("s"):
            pkg_branch_display_name = pkg_branch_display_name.rstrip("s")
        elif pkg_branch_display_name.endswith("es"):
            pkg_branch_display_name = pkg_branch_display_name.rstrip("es")
        kwargs.update(dict(pkg_branch_display_name=pkg_branch_display_name))
        kwargs.update(dict(pkg_release_choices=pkg_release_choices))
        kwargs.update(dict(package_name=package.package_name))
        kwargs.update(dict(package_platform=package.platform_slug.engine_name))
        if data:
            kwargs.update({'data': data})
        return PackagePipelineForm(**kwargs)

    def get_success_url(self):
        return reverse('package-add-ci-pipeline', args=[self.kwargs.get('slug')])

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_data)

        context_data = dict()
        context_data['form'] = form
        package_name = self.kwargs.get('slug')
        context_data.update(dict(package_name=package_name))

        if form.is_valid():
            post_params = form.cleaned_data
            # Assumption: Project URL starts with Platform API URL (which is saved in db)
            if post_params['ci_platform'].api_url not in post_params['ci_project_web_url']:
                errors = form._errors.setdefault('ci_project_web_url', ErrorList())
                errors.append("Project URL does NOT belong to the selected platform.")
                return render(request, self.template_name, context=context_data)
            post_params['ci_package'] = self.packages_manager.get_packages(
                pkgs=[package_name]).get()
            p_uuid, p_details = self.ci_pipeline_manager.ci_platform_project_details(
                post_params['ci_platform'], post_params['ci_project_web_url']
            )
            if not p_details:
                errors = form._errors.setdefault('ci_project_web_url', ErrorList())
                errors.append("Project details could not be fetched for the given URL.")
                return render(request, self.template_name, context=context_data)
            post_params['ci_project_details_json_str'] = json.dumps(p_details)
            if p_details.get('project_jobs'):
                post_params['ci_platform_jobs_json_str'] = json.dumps(p_details['project_jobs'])

            if not post_params["ci_pipeline_auto_create_config"]:
                if not self.ci_pipeline_manager.save_ci_pipeline(post_params):
                    messages.add_message(request, messages.ERROR, (
                        'Alas! Something unexpected happened. Please try adding pipeline again!'
                    ))
                else:
                    messages.add_message(request, messages.SUCCESS, (
                        'Great! CI Pipeline added successfully.'
                    ))
            else:
                new_pipeline_obj, _ = \
                    self.ci_pipeline_manager.save_ci_pipeline(post_params, get_obj=True)
                if not new_pipeline_obj:
                    messages.add_message(request, messages.ERROR, (
                        'Alas! Something unexpected happened. Please try adding pipeline again!'
                    ))
                else:
                    for event in PIPELINE_CONFIG_EVENTS:
                        pipeline_config_args = []
                        pipeline_config_kwargs = {}
                        pipeline_config_args.extend([
                            new_pipeline_obj.ci_package.platform_slug.engine_name,
                            post_params["ci_pipeline_default_branch"],
                            [post_params["ci_pipeline_default_branch"]],
                            ",".join(new_pipeline_obj.ci_project_details_json.get("targetLangs", [])),
                            SYS_EMAIL_ADDR
                        ])
                        pipeline_config_kwargs.update(dict(chkCopyConfig='true'))
                        pipeline_config_kwargs.update(dict(ciPipeline=str(new_pipeline_obj.ci_pipeline_uuid)))
                        pipeline_config_kwargs.update(dict(pipelineAction=event))
                        pipeline_config_kwargs.update(dict(package=new_pipeline_obj.ci_package.package_name))
                        pipeline_config_kwargs.update(dict(package=new_pipeline_obj.ci_package.package_name))
                        pipeline_config_kwargs.update(dict(is_default=True))
                        pipeline_config_kwargs.update(dict(uploadImportSettings='project'))
                        prepend_branch = 'true' if request.tenant == RELSTREAM_SLUGS[3] else 'false'
                        pipeline_config_kwargs.update(dict(downloadPrependBranch=prepend_branch))
                        pipeline_config_kwargs.update(dict(uploadPrependBranch=prepend_branch))
                        pipeline_config_kwargs.update(dict(uploadUpdate='false'))

                        if not self.pipeline_config_manager.process_save_pipeline_config(
                                *pipeline_config_args, **pipeline_config_kwargs
                        ):
                            messages.add_message(request, messages.WARNING, (
                                'CI Pipeline added successfully. However, Saving default Configurations failed.'
                            ))
                        else:
                            messages.add_message(request, messages.SUCCESS, (
                                'Great! CI Pipeline and default Configurations are added successfully.'
                            ))
            return HttpResponseRedirect(self.get_success_url())
        return render(request, self.template_name, context=context_data)


class TerritoryView(ManagersMixin, TemplateView):
    """
    Territory View
    """
    template_name = "geolocation/territory_view.html"

    def get_context_data(self, **kwargs):
        context = super(TerritoryView, self).get_context_data(**kwargs)
        country_name = self.request.GET.get('name', '')
        if country_name:
            context['country_name'] = country_name
        territory_locales, territory_languages, two_char_country_code = \
            self.geo_location_manager.get_locales_from_territory_id(
                kwargs.get('country_code', '')
            )
        if two_char_country_code:
            context['two_char_country_code'] = two_char_country_code
        if territory_locales and territory_languages:
            territory_locale_language = dict(zip(territory_locales,
                                                 territory_languages))
            context['territory_locales'] = territory_locale_language
        territory_timezones = \
            self.geo_location_manager.get_timezones_from_territory_id(
                kwargs.get('country_code', '')
            )
        if territory_timezones:
            context['territory_timezones'] = territory_timezones
        keyboards, input_methods = \
            self.geo_location_manager.get_keyboards_from_territory_id(
                kwargs.get('country_code', '')
            )
        if keyboards:
            context['territory_keyboards'] = keyboards
        if input_methods:
            context['territory_input_methods'] = input_methods
        return context


class PipelinesView(ManagersMixin, ListView):
    """
    Pipelines View
    """
    template_name = "ci/list_pipelines.html"
    context_object_name = 'pipelines'

    def get_queryset(self):
        tenant_releases = \
            self.release_branch_manager.get_release_branches(relstream=self.request.tenant)
        active_pipelines = self.ci_pipeline_manager.get_ci_pipelines(releases=tenant_releases)
        return active_pipelines.filter(
            ci_release__track_trans_flag=True
        ).order_by('ci_package_id').order_by('ci_release__release_name')


class ReleasePipelinesView(ManagersMixin, ListView):
    """
    Release Pipelines View
    """
    template_name = "ci/list_pipelines.html"
    context_object_name = 'pipelines'

    def get_queryset(self):
        tenant_releases = \
            self.release_branch_manager.get_release_branches(relstream=self.request.tenant)
        active_pipelines = self.ci_pipeline_manager.get_ci_pipelines(releases=tenant_releases)
        return active_pipelines.filter(
            ci_release__release_slug=self.kwargs['release_slug']
        ).order_by('ci_package__package_name')


class AddCIPipeline(ManagersMixin, FormView):
    """
    Add CI Pipeline View
    """
    template_name = 'ci/add_pipeline.html'
    success_message = '%(ci_pipeline_uuid)s was added successfully!'

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super(AddCIPipeline, self).get(request, *args, **kwargs)

    def get_form(self, form_class=None, data=None):

        def _sort_choices_by_name(choices):
            """
            sort choices by name of a form field
            :param choices: list of tuples
            :return: sorted list of tuples
            """
            return sorted(choices, key=lambda choice: choice[1])

        kwargs = {}
        ci_platforms = self.inventory_manager.get_translation_platforms(ci=True)
        ci_platform_choices = tuple([(platform.platform_id, platform.__str__)
                                     for platform in ci_platforms])
        kwargs.update(dict(ci_platform_choices=ci_platform_choices))
        packages = self.packages_manager.get_packages()
        releases = self.release_branch_manager.get_release_branches()
        package_choices = tuple([(package.package_id, package.package_name) for package in packages])
        release_choices = tuple([(release.release_id, release.__str__) for release in releases])
        kwargs.update(dict(package_choices=_sort_choices_by_name(package_choices)))
        kwargs.update(dict(release_choices=release_choices))
        if data:
            kwargs.update({'data': data})
        return CreateCIPipelineForm(**kwargs)

    def get_success_url(self):
        return reverse('add-ci-pipeline')

    def post(self, request, *args, **kwargs):
        post_data = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_data)

        context_data = dict()
        context_data['form'] = form

        if form.is_valid():
            post_params = form.cleaned_data
            # Assumption: Project URL starts with Platform API URL (which is saved in db)
            if post_params['ci_platform'].api_url not in post_params['ci_project_web_url']:
                errors = form._errors.setdefault('ci_project_web_url', ErrorList())
                errors.append("Project URL does NOT belong to the selected platform.")
                return render(request, self.template_name, context=context_data)
            if post_params['ci_release'] not in self.packages_manager.get_package_releases(
                    package_name=post_params['ci_package'].package_name):
                errors = form._errors.setdefault('ci_release', ErrorList())
                errors.append("Release does NOT belong to the selected package.")
                return render(request, self.template_name, context=context_data)
            p_uuid, p_details = self.ci_pipeline_manager.ci_platform_project_details(
                post_params['ci_platform'], post_params['ci_project_web_url']
            )
            if not p_details:
                errors = form._errors.setdefault('ci_project_web_url', ErrorList())
                errors.append("Project details could not be fetched for the given URL.")
                return render(request, self.template_name, context=context_data)
            post_params['ci_project_details_json_str'] = json.dumps(p_details)
            if p_details.get('project_jobs'):
                post_params['ci_platform_jobs_json_str'] = json.dumps(p_details['project_jobs'])
            if not self.ci_pipeline_manager.save_ci_pipeline(post_params):
                messages.add_message(request, messages.ERROR, (
                    'Alas! Something unexpected happened. Please try adding pipeline again!'
                ))
            else:
                messages.add_message(request, messages.SUCCESS, (
                    'Great! CI Pipeline added successfully.'
                ))
            return HttpResponseRedirect(self.get_success_url())
        return render(request, self.template_name, context=context_data)


def schedule_job(request):
    """
    Handles job schedule AJAX POST request
    """
    message = "&nbsp;&nbsp;<span class='text-warning'>Request could not be processed.</span>"
    if request.is_ajax():
        job_type = request.POST.dict().get('job')
        active_user = getattr(request, 'user', None)
        active_user_email = active_user.email \
            if active_user and not active_user.is_anonymous else 'anonymous@transtats.org'
        if job_type == TS_JOB_TYPES[0]:
            transplatform_sync_manager = TransplatformSyncManager(**{'active_user_email': active_user_email})
            job_uuid = transplatform_sync_manager.syncstats_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='pficon pficon-ok'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/jobs/logs'>" + str(job_uuid) + "</a>"
                transplatform_sync_manager.sync_trans_stats()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
        elif job_type == TS_JOB_TYPES[1]:
            relschedule_sync_manager = ReleaseScheduleSyncManager(**{'active_user_email': active_user_email})
            job_uuid = relschedule_sync_manager.syncschedule_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='pficon pficon-ok'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/jobs/logs'>" + str(job_uuid) + "</a>"
                relschedule_sync_manager.sync_release_schedule()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
        elif job_type in (TS_JOB_TYPES[2], TS_JOB_TYPES[3], TS_JOB_TYPES[5], TS_JOB_TYPES[6], TS_JOB_TYPES[7],
                          TS_JOB_TYPES[8], TS_JOB_TYPES[9], 'YMLbasedJob'):

            if job_type in TS_CI_JOBS and 'anonymous' in active_user_email:
                message = "&nbsp;&nbsp;<span class='text-warning'>Please login to continue.</span>"
                return HttpResponse(message, status=403)
            job_params = request.POST.dict().get('params')
            if not job_params:
                message = "&nbsp;&nbsp;<span class='text-danger'>Job params missing.</span>"
                return HttpResponse(message, status=500)
            req_params, fields = [str(param).upper() for param in ast.literal_eval(job_params)], []
            fields.extend(req_params + ['YML_FILE'])
            not_available = [field for field in fields if not request.POST.dict().get(field)]
            if len(not_available) > 0:
                message = "&nbsp;&nbsp;<span class='text-danger'>Provide value for %s</span>" % not_available[0]
                return HttpResponse(message, status=500)
            else:
                fields.append('DRY_RUN')
                fields.append('SCRATCH')
                job_manager = YMLBasedJobManager(
                    **{field: request.POST.dict().get(field) for field in fields},
                    **{'params': req_params, 'type': job_type},
                    **{'active_user_email': active_user_email}
                )
                try:
                    job_uuid = job_manager.execute_job()
                except Exception:
                    message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
                    return HttpResponse(message, status=500)
                else:
                    if not request.POST.dict().get('SCRATCH', '') == 'ScratchRun':
                        message = "&nbsp;&nbsp;<span class='text-success'>Success. Job URL: " \
                                  "<a href='/jobs/log/" + str(job_uuid) + "/detail'" \
                                  " data-toggle='tooltip' title='Copy this link to share!'>" + \
                                  str(job_uuid) + "</a></span>"
                    else:
                        message = "&nbsp;&nbsp;<span class='text-success'>Success.</span>"
        elif job_type == TS_JOB_TYPES[4]:
            buildtags_sync_manager = BuildTagsSyncManager(**{'active_user_email': active_user_email})
            job_uuid = buildtags_sync_manager.syncbuildtags_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='pficon pficon-ok'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/jobs/logs'>" + str(job_uuid) + "</a>"
                buildtags_sync_manager.sync_build_tags()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
    return HttpResponse(message)


def read_file_logs(request):
    message = ''
    if request.is_ajax():
        post_params = request.POST.dict()
        job_params = [str(param).upper() for param in ast.literal_eval(post_params.get('params', ''))]
        job_manager = YMLBasedJobManager(
            **{'params': job_params, 'type': post_params.get('job', 'YMLbasedJob')}
        )
        suffix = job_manager.job_suffix(
            [post_params.get(param, '') for param in job_params][:3]
        )
        log_file_path = job_manager.job_log_file + ".%s.%s" % (suffix, job_manager.type)
        log_file = Path(log_file_path)
        if log_file.is_file():
            with open(log_file_path) as f:
                content = f.readlines()
                content = [x.strip() for x in content]
                message = "<br/>".join(content)
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
            ERR_MSG = "Something unexpected happened while mapping branches."
            try:
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
            except Exception as e:
                return HttpResponse(status=500, content=ERR_MSG, content_type="text/html")
        elif task_type == "latestBuilds" and post_params.get('package'):
            ERR_MSG = "Something unexpected happened while fetching latest builds."
            try:
                if package_manager.fetch_latest_builds(post_params['package']):
                    context = Context(
                        {'META': request.META, 'package_name': post_params['package']}
                    )
                    template_string = """
                        {% load tag_latest_builds from custom_tags %}
                        {% tag_latest_builds package_name %}
                    """
                    return HttpResponse(Template(template_string).render(context))
            except Exception as e:
                return HttpResponse(status=500, content=ERR_MSG, content_type="text/html")
        elif task_type == "statsDiff" and post_params.get('package'):
            graph_manager = GraphManager()
            pkg = post_params['package']
            package_stats = graph_manager.get_trans_stats_by_package(pkg)
            ERR_MSG = "Make sure all mapped versions/tags are sync'd for stats."
            package_branch_mapping = graph_manager.package_manager.get_pkg_branch_mapping(pkg)
            if package_stats and package_branch_mapping:
                try:
                    graph_manager.package_manager.calculate_stats_diff(
                        pkg, package_stats, package_branch_mapping
                    )
                except Exception as e:
                    return HttpResponse(status=500, content=ERR_MSG, content_type="text/html")
                else:
                    context = Context(
                        {'META': request.META,
                         'package_name': post_params['package']}
                    )
                    template_string = """
                                        {% load tag_stats_diff from custom_tags %}
                                        {% tag_stats_diff package_name %}
                                    """
                    return HttpResponse(Template(template_string).render(context))
            else:
                return HttpResponse(status=500, content=ERR_MSG, content_type="text/html")
        elif task_type == "syncPlatform" and post_params.get('package'):
            if package_manager.refresh_package(post_params['package']):
                return HttpResponse(status=200)
        elif task_type == "details" and post_params.get('package'):
            context = Context(
                {'META': request.META,
                 'package_name': post_params['package'],
                 'user': request.user}
            )
            template_string = """
                    {% load tag_package_details from custom_tags %}
                    {% tag_package_details package_name user %}
            """
            return HttpResponse(Template(template_string).render(context))
    return HttpResponse(status=500)


def export_packages(request, **kwargs):
    """
    Exports packages to CSV
    """
    if request.method == 'GET' and kwargs.get('format', '') == 'csv':
        file_name = "ts-packages-%s.csv" % datetime.today().strftime('%d-%m-%Y')
        packages_manager = PackagesManager()
        required_fields = ['package_name', 'upstream_url', 'platform_url',
                           'products', 'release_branch_mapping']
        packages = packages_manager.get_packages(pkg_params=required_fields)
        response = HttpResponse(content_type='text/csv', status=200)
        response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
        writer = csv.writer(response)
        writer.writerow([field.replace('_', ' ').title() for field in required_fields])
        for package in packages:
            writer.writerow(
                [package.package_name, package.upstream_url,
                 package.platform_url, ', '.join(package.products),
                 package.release_branch_mapping if package.release_branch_mapping
                 else ''])
        return response
    return HttpResponse(status=500)


def release_graph(request):
    """
    Generates release graph
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
        elif post_params.get('relbranch') and post_params.get('threshold'):
            context = Context(
                {'META': request.META,
                 'relbranch': post_params['relbranch'],
                 'threshold': post_params['threshold']}
            )
            template_string = """
                {% load tag_threshold_based from custom_tags %}
                {% tag_threshold_based relbranch threshold %}
            """
            return HttpResponse(Template(template_string).render(context))
        elif post_params.get('relbranch'):
            graph_manager = GraphManager()
            graph_dataset = graph_manager.get_workload_graph_data(post_params['relbranch'])
    return JsonResponse(graph_dataset)


def generate_reports(request):
    """
    Generates Reports
    """
    if request.is_ajax():
        post_params = request.POST.dict()
        report_subject = post_params.get('subject', '')
        reports_manager = ReportsManager()
        if report_subject == 'releases':
            try:
                releases_summary = reports_manager.analyse_releases_status()
            except Exception as e:
                return HttpResponse(status=500)
            if releases_summary:
                context = Context(
                    {'META': request.META,
                     'relsummary': releases_summary,
                     'last_updated': datetime.now(),
                     'tenant': request.tenant
                     }
                )
                template_string = """
                                {% load tag_releases_summary from custom_tags %}
                                {% tag_releases_summary tenant %}
                            """
                return HttpResponse(Template(template_string).render(context))
        if report_subject == 'packages':
            packages_summary = reports_manager.analyse_packages_status()
            if packages_summary:
                context = Context(
                    {'META': request.META,
                     'pkgsummary': packages_summary,
                     'last_updated': datetime.now()}
                )
                template_string = """
                                    {% load tag_packages_summary from custom_tags %}
                                    {% tag_packages_summary %}
                                """
                return HttpResponse(Template(template_string).render(context))
        if report_subject == 'location':
            country_code = post_params.get('country_code', '')
            location_summary = reports_manager.refresh_stats_required_by_territory()
            if location_summary:
                context = Context(
                    {'META': request.META,
                     'location_summary': location_summary,
                     'last_updated': datetime.now(),
                     'country_code': country_code}
                )
                template_string = """
                                    {% load tag_location_summary from custom_tags %}
                                    {% tag_location_summary country_code %}
                                """
                return HttpResponse(Template(template_string).render(context))
    return HttpResponse(status=500)


def get_build_tags(request):
    """
    Get Build System Tags
    """
    if request.is_ajax():
        post_params = request.POST.dict()
        product_build = post_params.get('buildsys', '')
        product_slug, build_system = tuple(product_build.split('-'))
        inventory_manager = InventoryManager()
        tags = inventory_manager.get_build_tags(
            build_system, product_slug
        )
        if tags:
            context = Context(
                {'META': request.META,
                 'build_tags': tags,
                 'product': product_slug,
                 'buildsys': build_system}
            )
            template_string = """
                                {% load tag_build_tags from custom_tags %}
                                {% tag_build_tags buildsys product %}
                            """
            return HttpResponse(Template(template_string).render(context))
    return HttpResponse(status=500)


def get_repo_branches(request):
    """
    Get Repository Branch(es)
    """

    if request.is_ajax():
        post_params = request.POST.dict()
        package = post_params.get('package', '')
        repo_type = post_params.get('repoType', '')
        context = Context(
            {'META': request.META,
             'package': package,
             'repo_type': repo_type}
        )
        template_string = """
                            {% load tag_repo_branches from custom_tags %}
                            {% tag_repo_branches package repo_type %}
                        """
        return HttpResponse(Template(template_string).render(context))
    return HttpResponse(status=500)


def job_template(request):
    """
    Select Job Template
    """
    if request.is_ajax():
        post_params = request.POST.dict()
        selected_template = post_params.get('template', '')
        context = Context(
            {'META': request.META,
             'job_template': selected_template}
        )
        template_string = """
                            {% load tag_job_form from custom_tags %}
                            {% tag_job_form job_template %}
                        """
        return HttpResponse(Template(template_string).render(context))
    return HttpResponse(status=500)


def change_lang_status(request):
    """
    Enable or disable language. Checks the given parameters, if all parameters are correct then changes status
    of the language. The request should be an ajax call having data in following format,

        {'language': <locale_id>, 'status': <'enable'/'disable'>}

    :param request: Request object
    :returns: HttpResponse object
    """
    if request.is_ajax():
        post_params = request.POST.dict()
        language = post_params.get('language', '')
        new_lang_status = post_params.get('status', '')
        inventory_manager = InventoryManager()
        available_languages = [language.locale_id for language in inventory_manager.get_locales()]
        if language and new_lang_status:
            if language not in available_languages:
                return HttpResponse('Language not available', status=422)
            if new_lang_status not in ['enable', 'disable']:
                return HttpResponse("Status should be 'enable' or 'disable'", status=422)
            try:
                language_object = Language.objects.get(locale_id=language)
                language_object.lang_status = True if new_lang_status == 'enable' else False
                language_object.save()
            except Exception as status_change_error:
                return HttpResponse("Something went wrong.", status=500)
            else:
                return HttpResponse("language {0}d successfully!".format(new_lang_status), status=202)
        else:
            return HttpResponse("Parameters missing", status=422)
    else:
        return HttpResponse("Not an ajax call", status=400)


def hide_ci_pipeline(request):
    """
    Hide CI Pipeline
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)
    post_params = request.POST.dict()
    package_owner = post_params.get('user', '')
    ci_pipeline_id = post_params.get('pipeline_id', '')
    if not package_owner and not ci_pipeline_id:
        return HttpResponse("Invalid Parameters", status=422)
    if not request.user.email == package_owner and not request.user.is_staff:
        return HttpResponse("Access Denied", status=403)
    ci_pipeline_manager = CIPipelineManager()
    # delete all associated jobs
    Job.objects.filter(ci_pipeline_id=ci_pipeline_id).delete()
    # delete all associated pipeline configs
    PipelineConfig.objects.filter(ci_pipeline_id=ci_pipeline_id).delete()
    if ci_pipeline_manager.toggle_visibility(ci_pipeline_id):
        return HttpResponse("Pipeline successfully removed.", status=202)
    return HttpResponse(status=500)


def refresh_ci_pipeline(request):
    """
    Refresh CI Pipeline
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)
    post_params = request.POST.dict()
    package_owner = post_params.get('user', '')
    ci_pipeline_id = post_params.get('pipeline_id', '')
    if not package_owner and not ci_pipeline_id:
        return HttpResponse("Invalid Parameters", status=422)
    ci_pipeline_manager = CIPipelineManager()
    if ci_pipeline_manager.refresh_ci_pipeline(ci_pipeline_id):
        return HttpResponse("Pipeline successfully refreshed.", status=202)
    return HttpResponse(status=500)


def get_target_langs(request):
    """
    Get Target Languages for a CI Pipeline
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)

    post_params = request.POST.dict()
    ci_pipeline = post_params.get('ci_pipeline', '')
    context = Context(
        {'META': request.META,
         'ci_pipeline': ci_pipeline}
    )
    template_string = """
                        {% load tag_target_langs from custom_tags %}
                        {% tag_target_langs ci_pipeline %}
                    """
    return HttpResponse(Template(template_string).render(context))


def get_workflow_steps(request):
    """
    Get Workflow Steps for a CI Pipeline
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)

    post_params = request.POST.dict()
    ci_pipeline = post_params.get('ci_pipeline', '')
    context = Context(
        {'META': request.META,
         'ci_pipeline': ci_pipeline}
    )
    template_string = """
                        {% load tag_workflow_steps_dropdown from custom_tags %}
                        {% tag_workflow_steps_dropdown ci_pipeline %}
                    """
    return HttpResponse(Template(template_string).render(context))


def get_pipeline_job_template(request):
    """
    Get Job Template for a CI Pipeline Event
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)

    post_params = request.POST.dict()
    pipeline_action = post_params.get('pipelineAction', '')
    pipeline_uuid = post_params.get('pipelineUUID', '')
    context = Context(
        {'META': request.META,
         'tenant': request.tenant,
         'pipeline_action': pipeline_action,
         'pipeline_uuid': pipeline_uuid}
    )
    template_string = """
                            {% load tag_pipeline_job_params from custom_tags %}
                            {% tag_pipeline_job_params tenant pipeline_uuid pipeline_action %}
                        """
    return HttpResponse(Template(template_string).render(context))


def ajax_save_pipeline_config(request):
    """
    Save Pipeline Configuration
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)

    post_params = request.POST.dict().copy()
    pipeline_repo_type = post_params.get('cloneType') or \
        post_params.get('downloadType') or \
        post_params.get('uploadType')
    pipeline_repo_branch = post_params.get('cloneBranch') or \
        post_params.get('downloadBranch') or \
        post_params.get('uploadBranch')
    if not pipeline_repo_branch:
        return HttpResponse("No branch selected.", status=500)
    pipeline_target_langs = post_params.get('downloadTargetLangs') or \
        post_params.get('uploadTargetLangs')
    if not pipeline_target_langs:
        return HttpResponse("No target_langs selected.", status=500)
    pipeline_config_manager = PipelineConfigManager()
    pipeline_branches = pipeline_repo_branch.split(",")
    if "," in pipeline_repo_branch and len(pipeline_branches) > 1:
        if post_params.get('downloadBranch'):
            post_params['downloadBranch'] = JOB_MULTIPLE_BRANCHES_VAR
        if post_params.get('uploadBranch'):
            post_params['uploadBranch'] = JOB_MULTIPLE_BRANCHES_VAR
        pipeline_repo_branch = JOB_MULTIPLE_BRANCHES_VAR
    u_email = request.user.email
    if pipeline_config_manager.process_save_pipeline_config(
            pipeline_repo_type, pipeline_repo_branch, pipeline_branches,
            pipeline_target_langs, u_email, **post_params
    ):
        return HttpResponse("Pipeline configuration saved.", status=201)
    return HttpResponse("Saving pipeline configuration failed.", status=500)


def ajax_run_pipeline_config(request):
    """
    Save Pipeline Configuration
    :param request: Request object
    :return: HttpResponse object
    """
    ajax_run_pipeline_config.message = \
        "&nbsp;<span class='text-warning'>See History.</span>"
    ajax_run_pipeline_config.failed_jobs_count = 0

    def _execute_job(*args):
        job_data, t_params, job_type, temp_path = args
        job_manager = YMLBasedJobManager(
            **job_data, **{'params': [p.upper() for p in t_params],
                           'type': job_type},
            **{'active_user_email': request.user.email},
            **{'sandbox_path': temp_path},
            **{'job_log_file': temp_path + '.log'}
        )

        try:
            if os.path.isdir(temp_path):
                shutil.rmtree(temp_path)
            os.mkdir(temp_path)
            job_log_id = job_manager.execute_job()
            ajax_run_pipeline_config.message = "&nbsp;&nbsp;<span class='pficon pficon-ok'></span>" + \
                "&nbsp;<span class='text-success'>Success</span>. " + \
                "See the <a href='/jobs/log/{}/detail'>Log</a> and History.".format(str(job_log_id))
        except Exception as _:
            ajax_run_pipeline_config.failed_jobs_count += 1
            return HttpResponse("Something went wrong. See History.", status=500)
        finally:
            shutil.rmtree(temp_path)

    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)

    post_params = request.POST.dict().copy()
    pipeline_config_manager = PipelineConfigManager()
    pipeline_config = pipeline_config_manager.get_pipeline_configs(
        pipeline_config_ids=[post_params.get('pipeline_config_id')]).first()

    for branch in pipeline_config.pipeline_config_repo_branches:
        respective_job_template = pipeline_config_manager.get_job_action_template(
            pipeline_config.ci_pipeline, pipeline_config.pipeline_config_event)

        t_params = respective_job_template.job_template_params
        job_data = {param.upper(): '' for param in t_params}
        job_data.update(dict(
            YML_FILE=pipeline_config.pipeline_config_yaml.replace('%RESPECTIVE%', branch)
        ))
        job_type = pipeline_config.pipeline_config_json.get('job', {}).get('type')
        job_pkg = pipeline_config.pipeline_config_json.get('job', {}).get('package')
        temp_path = 'false/{0}/'.format("-".join([job_pkg, job_type, branch]))

        if 'PACKAGE_NAME' in job_data:
            job_data['PACKAGE_NAME'] = job_pkg
        if 'REPO_BRANCH' in job_data:
            job_data['REPO_BRANCH'] = branch

        t = threading.Thread(
            target=_execute_job,
            args=[job_data, t_params, job_type, temp_path],
        )
        t.daemon = True
        t.start()
        t.join()

    no_of_branches = len(pipeline_config.pipeline_config_repo_branches)
    if no_of_branches > 1:
        no_of_jobs_succeed = no_of_branches - ajax_run_pipeline_config.failed_jobs_count
        ajax_run_pipeline_config.message = \
            f"<span class='text-success'>{no_of_jobs_succeed}</span> jobs succeed out of {no_of_branches}. " \
            f"<span class='text-danger'>{ajax_run_pipeline_config.failed_jobs_count}</span> failed. See History."

    return HttpResponse(ajax_run_pipeline_config.message, status=200)


def ajax_toggle_pipeline_config(request):
    """
    Toggle Pipeline Configuration
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)

    post_params = request.POST.dict().copy()
    pipeline_config_manager = PipelineConfigManager()
    if pipeline_config_manager.toggle_pipeline_configuration(
            pipeline_config_id=post_params.get('p_config_id')):
        return HttpResponse("Ok", status=204)
    return HttpResponse("Something went wrong.", status=500)


def ajax_delete_pipeline_config(request):
    """
    Delete Pipeline Configuration
    :param request: Request object
    :return: HttpResponse object
    """
    if not request.is_ajax():
        return HttpResponse("Not an Ajax Call", status=400)

    post_params = request.POST.dict().copy()
    pipeline_config_manager = PipelineConfigManager()
    if pipeline_config_manager.delete_pipeline_configuration(
            pipeline_config_id=post_params.get('p_config_id')):
        return HttpResponse("Ok", status=204)
    return HttpResponse("Something went wrong.", status=500)
