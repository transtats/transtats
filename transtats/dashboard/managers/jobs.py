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

from .base import JobManager


class TransplatformSyncManager(JobManager):
    """
    Translation Platform Sync Manager
    """

    def syncstats_initiate_job(self):
        """
        Creates a Sync Job
        """
        if self.create_job():
            return self.uuid
        return None

    def sync_trans_stats(self):
        """
        Run Sync process in sequential steps
        """
        stages = (
            self.fetch_trans_projects,
        )

        [method() for method in stages]

    def fetch_trans_projects(self):
        """
        Update projects json for transplatform
        """
        pass
