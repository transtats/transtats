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

from django.contrib import messages
from django.forms.utils import ErrorList
from django.http import (
    HttpResponse, HttpResponseRedirect, JsonResponse
)
from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormMixin

from ..forms.packages import NewPackageForm
from ..managers.jobs import TransplatformSyncManager
from ..managers.settings import AppSettingsManager
from ..managers.packages import PackagesManager
from ..managers.relstream import ReleaseStreamManager
from ..managers.transplatform import TransPlatformManager
from ..utilities import get_manager


class AppSettingsView(TemplateView):
    """
    Application Settings List View
    """
    template_name = "settings/summary.html"


class TransPlatformSettingsView(ListView):
    """
    Translation Platform Settings View
    """
    template_name = "settings/transplatforms.html"
    context_object_name = 'platforms'

    def get_queryset(self):
        app_settings_manager = get_manager(AppSettingsManager, self)
        platforms = app_settings_manager.get_translation_platforms()
        return platforms

    def get_context_data(self, **kwargs):
        context = super(TransPlatformSettingsView, self).get_context_data(**kwargs)
        app_settings_manager = get_manager(AppSettingsManager, self)
        platforms_set = app_settings_manager.get_transplatforms_set()
        if isinstance(platforms_set, tuple):
            active_platforms, inactive_platforms = platforms_set
            context['active_platforms_len'] = len(active_platforms)
            context['inactive_platforms_len'] = len(inactive_platforms)
        return context


class LanguagesSettingsView(ListView):
    """
    Languages Settings View
    """
    template_name = "settings/languages.html"
    context_object_name = 'locales'

    def get_queryset(self):
        app_settings_manager = get_manager(AppSettingsManager, self)
        locales = app_settings_manager.get_locales()
        return locales

    def get_context_data(self, **kwargs):
        context = super(LanguagesSettingsView, self).get_context_data(**kwargs)
        app_settings_manager = get_manager(AppSettingsManager, self)
        locales_set = app_settings_manager.get_locales_set()
        if isinstance(locales_set, tuple):
            active_locales, inactive_locales, aliases = locales_set
            context['active_locales_len'] = len(active_locales)
            context['inactive_locales_len'] = len(inactive_locales)
            context['aliases_len'] = len(aliases)
        return context


class ReleaseStreamSettingsView(ListView):
    """
    Release Streams Settings View
    """
    template_name = "settings/release_streams.html"
    context_object_name = 'relstreams'

    def get_queryset(self):
        app_settings_manager = get_manager(AppSettingsManager, self)
        relstreams = app_settings_manager.get_release_streams()
        return relstreams


class LogsSettingsView(ListView):
    """
    Logs Settings View
    """
    template_name = "settings/logs.html"
    context_object_name = 'logs'

    def get_queryset(self):
        app_settings_manager = get_manager(AppSettingsManager, self)
        job_logs = app_settings_manager.get_job_logs()
        return job_logs


class PackageSettingsView(FormMixin, ListView):
    """
    Packages Settings View
    """
    template_name = "settings/packages.html"
    context_object_name = 'packages'
    success_url = '/settings/packages'

    def get_queryset(self):
        packages_manager = get_manager(PackagesManager, self)
        packages = packages_manager.get_packages()
        return packages

    def get_initial(self):
        initials = {}
        initials.update(dict(transplatform_slug='ZNTAFED'))
        initials.update(dict(release_streams='RHEL'))
        initials.update(dict(lang_set='default'))
        initials.update(dict(update_stats='stats'))
        return initials

    def get_form(self, form_class=None, data=None):
        kwargs = {}
        transplatform_manager = get_manager(TransPlatformManager, self)
        active_platforms = transplatform_manager.get_active_transplatforms()
        relstream_manager = get_manager(ReleaseStreamManager, self)
        active_streams = relstream_manager.get_active_relstreams()
        kwargs.update({'transplatform_choices': active_platforms})
        kwargs.update({'relstream_choices': active_streams})
        kwargs.update({'initial': self.get_initial()})
        if data:
            kwargs.update({'data': data})
        return NewPackageForm(**kwargs)

    def post(self, request, *args, **kwargs):
        packages_manager = get_manager(PackagesManager, self)
        post_params = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_params)
        # process form_data to get them saved in db
        filter_params = ('csrfmiddlewaretoken', 'addPackage')
        [post_params.pop(key) for key in filter_params]
        if not isinstance(post_params.get('release_streams'), (list, tuple, set)):
            post_params['release_streams'] = [post_params['release_streams']]
        # end processing
        validate_package = packages_manager.validate_package(**post_params)
        if not validate_package:
            errors = form._errors.setdefault('package_name', ErrorList())
            errors.append("Not found at selected translation platform")
        if validate_package and form.is_valid():
            post_params['package_name'] = validate_package
            if not packages_manager.add_package(**post_params):
                messages.add_message(request, messages.ERROR, (
                    'Alas! Something unexpected happened. Please try adding your package again!'
                ))
            return HttpResponseRedirect(self.success_url)
        return render(request, self.template_name,
                      {'form': form, 'packages': self.get_queryset(), 'POST': 'invalid'})


def schedule_job(request):
    """
    Handles job schedule AJAX POST request
    """
    message = "&nbsp;&nbsp;<span class='text-warning'>Request could not be processed.</span>"
    if request.is_ajax():
        job_type = request.POST.dict().get('job')
        if job_type == 'synctransplatform':
            transplatform_sync_manager = TransplatformSyncManager(request, job_type)
            job_uuid = transplatform_sync_manager.syncstats_initiate_job()
            if job_uuid:
                message = "&nbsp;&nbsp;<span class='glyphicon glyphicon-check' style='color:green'></span>" + \
                          "&nbsp;Job created and logged! UUID: <a href='/settings/logs'>" + str(job_uuid) + "</a>"
                transplatform_sync_manager.sync_trans_stats()
            else:
                message = "&nbsp;&nbsp;<span class='text-danger'>Alas! Something unexpected happened.</span>"
    return HttpResponse(message)


def graph_data(request):
    """
    Prepares and dispatch graph data
    """
    graph_dataset = {}
    if request.is_ajax():
        package = request.POST.dict().get('package')
        packages_manager = PackagesManager(request)
        graph_dataset = packages_manager.get_trans_stats(package)
    return JsonResponse(graph_dataset)
