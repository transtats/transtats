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

from ..services.consume.restclient import RestClient


class BaseManager(object):
    """
    Base Manager: create app context, process view request object
    """

    def __init__(self, *args, **kwargs):

        for attrib, value in kwargs.items():
            if value:
                setattr(self, str(attrib), value)

    @staticmethod
    def rest_client(engine_name, base_url):
        """
        Instantiate RestClient
        :param engine_name: str
        :param base_url: str
        :return: RestClient
        """
        if engine_name and base_url:
            return RestClient(engine_name, base_url)
        return
