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

from django.conf import settings

from transtats import __appname__, __version__, __description__, __title__


def app_info(request):
    """
    Application Info
    """
    return {
        "app_name": __appname__,
        "app_version": __version__,
        "app_desc": __description__,
        "app_title": __title__,
        "auth": "fas" if settings.FAS_AUTH else "default",
        "client_config_file": "transtats.conf"
    }
