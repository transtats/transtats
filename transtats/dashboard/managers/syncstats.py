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

from ..models.syncstats import SyncStats
from .base import BaseManager


class SyncStatsManager(BaseManager):
    """
    Sync Translation Stats Manager
    """

    def get_sync_stats(self, pkgs=None):
        """
        fetch sync translation stats from db
        :return: resultset
        """
        sync_stats = None
        required_params = (SyncStats.package_name, SyncStats.project_version,
                           SyncStats.stats_raw_json)
        try:
            sync_stats = self.db_session.query(*required_params) \
                .filter(SyncStats.package_name.in_(pkgs)) \
                .filter_by(sync_visibility=True).all() if pkgs else \
                self.db_session.query(*required_params).all()
        except:
            self.db_session.rollback()
            # log event, passing for now
            pass
        return sync_stats

    def filter_stats_for_required_locales(self, stats_json, locales):
        """
        Filter stats json for required locales
        :param stats_json: dict
        :param locales: list
        :return: stats list, missing locales
        """
        if not stats_json.get('stats'):
            return {}
        trans_stats = []
        locales_found = []
        for stats_param in stats_json['stats']:
            stats_param_locale = stats_param.get('locale', '')
            for locale_tuple in locales:
                if (stats_param_locale in locale_tuple) or \
                        (stats_param_locale.replace('-', '_') in locale_tuple):
                    trans_stats.append(stats_param)
                else:
                    locales_found.append(locale_tuple)
        return trans_stats, tuple(set(locales) - set(locales_found))
