#
# transanalytics - Translation Analytics
#
# Copyright (c) 2016 Sundeep Anand <suanand@redhat.com>
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of transanalytics.
#
# transanalytics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# transanalytics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with transanalytics.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import url
from django.views.generic.base import TemplateView
from . import views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="home.html"), name="home"),
    url(r'^register$', TemplateView.as_view(template_name="register.html"), name="register"),
]
