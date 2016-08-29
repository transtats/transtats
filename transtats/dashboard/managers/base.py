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
import uuid

from ..models.jobs import Jobs
from ..services.consume.restclient import RestClient


class BaseManager(object):
    """
    Base Manager: create app context, process view request object
    """

    db_session = None

    def __init__(self, *args, **kwargs):
        # the first argument needs to be view request
        self.db_session = args[0].db_session

    def rest_client(self, engine_name, base_url):
        """
        Instantiate RestClient
        :param engine_name: str
        :param base_url: str
        :return: RestClient
        """
        if engine_name and base_url:
            return RestClient(engine_name, base_url)
        return


class JobManager(BaseManager):
    """
    Job Base Manager: transplatform sync, relstream validation etc.
    """
    job_type = None
    uuid = None
    start_time = None
    log_json = {}
    job_result = False
    job_remarks = None

    def _new_job_id(self):
        """
        a UUID based on the host ID and current time
        """
        return uuid.uuid4()

    def __init__(self, http_request, job_type):
        """
        Entry point for initiating new job
        :param http_request: object
        :param job_type: string
        """
        super(JobManager, self).__init__(http_request)
        self.job_type = job_type
        self.uuid = self._new_job_id()
        self.start_time = datetime.now()

    def create_job(self):
        kwargs = {}
        kwargs.update(dict(job_uuid=self.uuid))
        kwargs.update(dict(job_type=self.job_type))
        kwargs.update(dict(job_start_time=self.start_time))
        try:
            new_job = Jobs(**kwargs)
            self.db_session.add(new_job)
            self.db_session.commit()
        except:
            self.db_session.rollback()
            # log event, pass for now
            return False
        else:
            return True
