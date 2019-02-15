# Copyright 2019 Red Hat, Inc.
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

from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from django.utils import timezone

from dashboard.managers.packages import PackagesManager
from dashboard.managers.graphs import ReportsManager


logger = get_task_logger(__name__)


@periodic_task(
    run_every=(crontab(minute='*/10')),
    name="sync_packages_with_platform",
    ignore_result=True
)
def task_sync_packages_with_platform():
    """
    sync all packages with translation platform
    """

    package_manager = PackagesManager()
    reports_manager = ReportsManager()

    def _sync_package(pkg):
        package_manager.sync_update_package_stats(pkg)

    all_packages = package_manager.get_packages().filter(
        platform_last_updated__lte=timezone.now() - timedelta(hours=0)
    ).order_by('platform_url')
    for package in all_packages:
        th = threading.Thread(
            target=_sync_package, args=(package.package_name,)
        )
        th.start()
        th.join()
        time.sleep(2)

    reports_manager.analyse_releases_status()
    logger.info("%s Packages sync'd with Translation Platform" % len(all_packages))
