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

from django.views.generic import TemplateView
from ..managers.packages import PackagesManager
from ..utilities import get_manager


class HomeTemplateView(TemplateView):
    """
    Home Page Template View
    """
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        """
        Build the Context Data
        :param kwargs:
        :return: context_data
        """
        context_data = super(TemplateView, self).get_context_data(**kwargs)
        context_data['description'] = \
            "translation position of the package for downstream"

        packages_manager = get_manager(PackagesManager, self)
        packages = packages_manager.get_packages()
        if packages:
            context_data['packages'] = packages
        return context_data
