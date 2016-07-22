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

from ..models.transplatform import TransPlatform
from .base import BaseManager


class TransPlatformManager(BaseManager):
    """
    Translation Platform Manager
    """

    def get_translation_platform(self):
        """
        fetch translation platforms from db, zanata as of now!
        """
        platform = {}
        translation_platform = self.db_session.query(TransPlatform).filter_by(engine_name='zanata').first()
        if translation_platform:
            platform['url'] = translation_platform.api_url
            platform['engine'] = translation_platform.engine_name
            platform['state'] = translation_platform.server_status
        return platform
