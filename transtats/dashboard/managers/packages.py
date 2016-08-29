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
        required_params = ('package_name', 'upstream_url', 'transplatform_slug',
                           'release_streams', 'trans_pkg_name')
        if not set(required_params) < set(kwargs.keys()):
            return

        if not (kwargs['package_name'] and kwargs['upstream_url'] and kwargs['trans_pkg_name']):
            return

        try:
            # todo
            # fetch project details from transplatform and save in db

            # derive transplatform project URL
            platform_url = self.db_session.query(TransPlatform.api_url). \
                filter_by(platform_slug=kwargs['transplatform_slug']).one()[0]
            kwargs['transplatform_url'] = platform_url + "/project/view/" + kwargs.pop('trans_pkg_name')
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

    def _get_project_ids_names(self, projects):
        ids = []
        names = []
        for project in projects:
            ids.append(project['id'])
            names.append(project['name'])
        return ids, names

    def validate_package(self, **kwargs):
        """
        Validates existence of a package at a transplatform
        :param kwargs: dict
        :return: str, Boolean
        """
        if not (kwargs.get('package_name')):
            return
        package_name = kwargs['package_name']
        # get transplatform projects from db
        platform = self.db_session.query(
            TransPlatform.engine_name, TransPlatform.api_url,
            TransPlatform.projects_json). \
            filter_by(platform_slug=kwargs['transplatform_slug']).one()
        projects_json = platform.projects_json
        # if not found in db, fetch transplatform projects from API
        if not projects_json:
            rest_handle = self.rest_client(platform.engine_name, platform.api_url)
            response_dict = rest_handle.process_request('list_projects')
            if response_dict and response_dict.get('json_content'):
                projects_json = response_dict['json_content']

        ids, names = self._get_project_ids_names(projects_json)
        if package_name in ids:
            return package_name
        elif package_name in names:
            return ids[names.index(package_name)]
        else:
            return False
