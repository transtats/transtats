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

from ..models.locales import Languages
from ..models.relstream import ReleaseStream
from ..models.transplatform import TransPlatform
from .base import BaseManager


class AppSettingsManager(BaseManager):
    """
    Application Settings Manager
    """

    def get_translation_platforms(self):
        """
        fetch all translation platforms from db
        """
        platforms = None
        try:
            platforms = self.db_session.query(TransPlatform). \
                order_by(TransPlatform.server_status.desc()).all()
        except:
            self.db_session.rollback()
            # log event, passing for now
            pass
        return platforms

    def get_transplatforms_set(self):
        """
        Creates transplatform set on the basis of status
        :return: tuple
        """
        platforms = self.get_translation_platforms()
        if not platforms:
            return
        active_platforms = [platform for platform in platforms if platform.server_status]
        inactive_platforms = list(set(platforms) - set(active_platforms))
        return active_platforms, inactive_platforms

    def get_locales(self):
        """
        fetch all languages from db
        """
        locales = None
        try:
            locales = self.db_session.query(Languages).order_by('lang_name').all()
        except:
            self.db_session.rollback()
            # log event, passing for now
            pass
        return locales

    def get_locales_set(self):
        """
        Creates locales set on the basis of status
        :return: tuple
        """
        locales = self.get_locales()
        if not locales:
            return
        active_locales = [locale for locale in locales if locale.lang_status]
        inactive_locales = list(set(locales) - set(active_locales))
        aliases = list(filter(lambda locale: locale.locale_alias is not None, locales))
        return active_locales, inactive_locales, aliases

    def get_release_streams(self):
        """
        Fetch all release streams from the db
        """
        relstreams = None
        try:
            relstreams = self.db_session.query(ReleaseStream).all()
        except:
            self.db_session.rollback()
            # log event, passing for now
            pass
        return relstreams
