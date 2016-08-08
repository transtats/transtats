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

from ..models.locales import Languages
from ..models.relstream import ReleaseStream
from ..models.transplatform import TransPlatform
from ..models.package import Packages
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
            platforms = self.db_session.query(TransPlatform).all()
        except:
            # log event, passing for now
            pass
        return platforms

    def get_locales(self):
        """
        fetch all languages from db
        """
        locales = None
        try:
            locales = self.db_session.query(Languages).order_by('lang_name').all()
        except:
            # log event, passing for now
            pass
        return locales

    def get_release_streams(self):
        relstreams = None
        try:
            relstreams = self.db_session.query(ReleaseStream).all()
        except:
            # log event, passing for now
            pass
        return relstreams

    def get_packages(self):
        packages = None
        try:
            packages = self.db_session.query(Packages).order_by('transtats_lastupdated').all()
        except:
            # log event, passing for now
            pass
        return packages
