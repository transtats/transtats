# Copyright 2020 Red Hat, Inc.
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

# django
from django.utils import timezone

# dashboard
from dashboard.constants import TRANSPLATFORM_ENGINES
from dashboard.models import CacheAPI
from dashboard.services.consume.cache import CacheAPIManager


def cache_api_response():
    """
    decorator to check db for API response
    :return: response dict
    """
    def response_decorator(caller):
        def inner_decorator(obj, base_url, resource, *args, **kwargs):
            try:
                fields = ['expiry', 'response_raw']
                filter_params = {
                    'base_url': base_url,
                    'resource': resource,
                }
                cache = CacheAPI.objects.only(*fields).filter(**filter_params).first() or []
            except Exception as e:
                # log error
                pass
            else:
                if timezone.now() > cache[0]:
                    return cache[1]
            return caller(obj, base_url, resource, *args, **kwargs)
        return inner_decorator
    return response_decorator


def set_api_auth():
    """
    decorator to set authentication for API calls
    :return:
    """
    def service_decorator(caller):
        def inner_decorator(rest_client, url, resource, *args, **kwargs):
            auth_tuple = tuple()
            if 'headers' not in kwargs:
                kwargs['headers'] = dict()
            if kwargs.get('auth_user') and kwargs.get('auth_token'):
                if rest_client.service == TRANSPLATFORM_ENGINES[1] or \
                        rest_client.service == TRANSPLATFORM_ENGINES[3]:
                    # Tx and Weblate need auth_tuple for HTTPBasicAuth
                    auth_tuple = (kwargs['auth_user'], kwargs['auth_token'])
                elif rest_client.service == TRANSPLATFORM_ENGINES[2]:
                    # Zanata needs credentials in the header
                    kwargs['headers']['X-Auth-User'] = kwargs['auth_user']
                    kwargs['headers']['X-Auth-Token'] = kwargs['auth_token']
                elif rest_client.service == TRANSPLATFORM_ENGINES[4]:
                    # Memsource needs active token as an extension
                    cache_api_manager = CacheAPIManager()
                    latest_token = cache_api_manager.tally_auth_token(url)
                    kwargs.update(dict(
                        auth_token_ext="token={}".format(latest_token)
                    ))
            kwargs.update(dict(auth_tuple=auth_tuple))
            return caller(rest_client, url, resource, *args, **kwargs)
        return inner_decorator
    return service_decorator
