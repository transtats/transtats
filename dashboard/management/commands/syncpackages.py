# Copyright 2018 Red Hat, Inc.
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
import time
import threading
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dashboard.managers.packages import PackagesManager
from dashboard.managers.graphs import ReportsManager


class Command(BaseCommand):

    help = 'Sync packages with respective translation platform'

    package_manager = PackagesManager()
    reports_manager = ReportsManager()

    def _sync_package(self, pkg):
        self.package_manager.sync_update_package_stats(pkg)

    def handle(self, *args, **options):

        all_packages = self.package_manager.get_packages().filter(
            transtats_lastupdated__lte=timezone.now() - timedelta(days=1)
        ).order_by('transplatform_url')

        for package in all_packages:
            th = threading.Thread(target=self._sync_package, args=(package, ))
            th.start()
            th.join()
            time.sleep(2)

        self.reports_manager.analyse_releases_status()
