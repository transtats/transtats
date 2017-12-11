# Copyright 2017 Red Hat, Inc.
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
#
# This file contains other data used for tests

from datetime import timedelta
from json import loads


class mock_response:
    """
    Mock object for patched response.get
    """
    rest_text = None
    rest_url = None

    @property
    def status_code(self):
        return 200

    @property
    def ok(self):
        return True

    @property
    def headers(self):
        return {}

    @property
    def elapsed(self):
        return timedelta(0, 1, 764054)

    @property
    def text(self):
        return self.resp_text

    @property
    def url(self):
        return self.resp_url

    def json(self):
        return loads(self.resp_text)


class mock_response_add_package(mock_response):
    """
    Mock object for 'mock_values.mock_requests_get_add_package'
    """
    resp_text = '{"id":"authconfig",' \
                '"defaultType":"Gettext",' \
                '"name":"authconfig",' \
                '"description":"A simple tool for configuration of user identity and authentication",' \
                '"sourceViewURL":"https://pagure.io/authconfig",' \
                '"sourceCheckoutURL":"https://pagure.io/authconfig.git",' \
                '"iterations":[{"id":"master","links":[{"href":"iterations/i/master","rel":"self",' \
                '"type":"application/vnd.zanata.project.iteration+json"}],' \
                '"status":"ACTIVE","projectType":"Gettext"}],"status":"ACTIVE"}'
    resp_url = 'https://fedora.zanata.org/rest/projects/p/authconfig'


class mock_response_validate_package(mock_response):
    """
    Mock object for 'mock_values.mock_request_get_validate_package'
    """
    resp_text = '[{"id":"candlepin",' \
                '"name":"candlepin",' \
                '"links":[{"rel":"self","href":"p/candlepin","type":"application/vnd.zanata.project+json"}],' \
                '"status":"ACTIVE",' \
                '"defaultType":"Gettext"}]'
    resp_url = 'https://translate.zanata.org/rest/projects'
