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

from ..models.transplatform import TransPlatform
from .base import BaseManager


class TransPlatformManager(BaseManager):
    """
    Translation Platform Manager
    """

    def get_active_transplatforms(self):
        """
        Fetch slug and api_url for all active transplatforms
        :return: tuple
        """
        platforms = None
        try:
            platforms = self.db_session.query(TransPlatform.platform_slug, TransPlatform.api_url) \
                .filter_by(server_status=True).all()
        except:
            self.db_session.rollback()
            # log event, passing for now
            pass
        return tuple(platforms) if platforms else ()
