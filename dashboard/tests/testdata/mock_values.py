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
# This file contains mock functions used for tests

from dashboard.tests.testdata.test_data import mock_response_add_package, mock_response_validate_package


def mock_requests_get_add_package(uri, **kwargs):
    """
    Mock function to patch requests.get for test_add_package
    :param uri: uri of api end point
    :return: mock response object
    """
    response = mock_response_add_package()
    return response


def mock_requests_get_validate_package(uri, **kwargs):
    """
    Mock function to patch requests.get for test_validate_package
    :param uri: uri of api end point
    :return: mock response object
    """
    response = mock_response_validate_package()
    return response
