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
from django.views.generic.edit import FormMixin

# dashboard
from .forms.packages import NewPackageForm
from .managers.inventory import (
    InventoryManager, PackagesManager
)
from .managers.jobs import (
    JobsLogManager, TransplatformSyncManager
)


class ManagersMixin(object):
    """
    Managers Mixin
    """
    inventory_manager = InventoryManager()
    packages_manager = PackagesManager()
    jobs_log_manager = JobsLogManager()


class HomeTemplateView(ManagersMixin, TemplateView):
    """
    Home Page Template View
    """
    template_name = "home.html"

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


class AppSettingsView(TemplateView):
    """
    Application Settings List View
    """
    template_name = "settings/summary.html"


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
    context_object_name = 'packages'
    success_url = '/settings/packages/new'

    def get_queryset(self):
        return self.packages_manager.get_packages()

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
        post_params = {k: v[0] if len(v) == 1 else v for k, v in request.POST.lists()}
        form = self.get_form(data=post_params)
        # process form_data to get them saved in db
        filter_params = ('csrfmiddlewaretoken', 'addPackage')
        [post_params.pop(key) for key in filter_params]
        if not isinstance(post_params.get('release_streams'), (list, tuple, set)):
            post_params['release_streams'] = [post_params['release_streams']]
        # end processing
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
            transplatform_sync_manager = TransplatformSyncManager(job_type)
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
        packages_manager = PackagesManager()
        graph_dataset = packages_manager.get_trans_stats(package)
    return JsonResponse(graph_dataset)
