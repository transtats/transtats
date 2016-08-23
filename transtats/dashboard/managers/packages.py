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

from datetime import datetime

from ..models.package import Packages
from ..models.transplatform import TransPlatform
from .base import BaseManager


class PackagesManager(BaseManager):
    """
    Packages Manager
    """

    def get_packages(self):
        """
        fetch packages from db
        """
        packages = None
        try:
            packages = self.db_session.query(Packages).order_by('transtats_lastupdated').all()
        except:
            self.db_session.rollback()
            # log event, passing for now
            pass
        return packages

    def add_package(self, **kwargs):
        """
        add package to db
        :param kwargs: dict
        :return: boolean
        """
        required_params = ('package_name', 'upstream_url', 'transplatform_slug', 'release_streams')
        if not set(required_params) < set(kwargs.keys()):
            return

        if not (kwargs.get('package_name') and kwargs.get('upstream_url')):
            return

        try:
            # todo
            # fetch project details from transplatform and save in db

            # derive transplatform project URL
            platform_url = self.db_session.query(TransPlatform.api_url). \
                filter_by(platform_slug=kwargs['transplatform_slug']).one()[0]
            kwargs['transplatform_url'] = platform_url + "/project/view/" + kwargs['package_name']
            kwargs['lang_set'] = 'default'
            # save in db
            new_package = Packages(**kwargs)
            self.db_session.add(new_package)
            self.db_session.commit()
        except:
            self.db_session.rollback()
            # log event, pass for now
            return False
        else:
            return True
