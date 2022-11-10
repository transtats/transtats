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

import inspect
import logging
from urllib.parse import urlparse

# dashboard
from dashboard.services.resources import APIResources
from dashboard.constants import GIT_PLATFORMS


__all__ = ['BaseManager']


class BaseManager(object):
    """
    Base Manager:
        create app context
        facilitate common methods
        application logger
    """

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):

        for attrib, value in kwargs.items():
            if value:
                setattr(self, str(attrib), value)

        self.api_resources = APIResources()

    def app_logger(self, log_level, log_msg):
        """Custom application logger"""
        level_map = {
            'DEBUG': 10, 'INFO': 20, 'WARNING': 30,
            'ERROR': 40, 'CRITICAL': 50
        }

        func = inspect.currentframe().f_back.f_code
        log_message = "%s in %s:%i %s" % (func.co_name, func.co_filename,
                                          func.co_firstlineno, log_msg)
        self.logger.log(level_map.get(log_level, 10), log_message)

    @staticmethod
    def _parse_git_url(git_url):
        """
        Parses Git URL for instance_url, owner and repo
        :param git_url: git repository URL
        :return: instance_url, owner_repo tuple
        """
        parsed_url = urlparse(git_url)
        instance_url = "{}://{}".format(parsed_url.scheme, parsed_url.netloc)
        owner_repo = tuple(filter(None, parsed_url.path.split('/')))
        if owner_repo:
            # handle .git extension for upstream url
            owner_repo = [item[:-4] if item.endswith(".git")
                          else item for item in owner_repo]
            return instance_url, owner_repo
        return instance_url, ()

    @staticmethod
    def _determine_git_platform(instance_url):
        for platform in GIT_PLATFORMS:
            if platform.lower() in instance_url:
                return platform
        return ''
