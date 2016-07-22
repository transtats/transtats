#
# transtats - Translation Analytics
#
# Copyright (c) 2016 Sundeep Anand <suanand@redhat.com>
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of transtats.
#
# transtats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# transtats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with transtats.  If not, see <http://www.gnu.org/licenses/>.

from django.views.generic import TemplateView

from ..managers.transplatform import TransPlatformManager


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

        transplatform_manager = TransPlatformManager(self.request)
        platform_details = transplatform_manager.get_translation_platform()

        context_data['some_string'] = "Hey! I m writing the web!! Super Cool :)"
        context_data['platform_details'] = platform_details
        return context_data
