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
from django.conf import settings
from django.utils import timezone

# dashboard
from dashboard.constants import TRANSPLATFORM_ENGINES, API_TOKEN_PREFIX, GIT_PLATFORMS
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
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            if rest_client.service == TRANSPLATFORM_ENGINES[4]:
                # Memsource needs token in Authorization header.
                cache_api_manager = CacheAPIManager()
                latest_token = cache_api_manager.tally_auth_token(url)
                memsource_auth_user = API_TOKEN_PREFIX.get(rest_client.service) or kwargs['auth_user']
                kwargs['headers']['Authorization'] = f"{memsource_auth_user} {latest_token}"
            if kwargs.get('auth_user') and kwargs.get('auth_token'):
                auth_tuple = ()
                if rest_client.service == TRANSPLATFORM_ENGINES[1]:
                    # Transifex need auth_tuple for HTTPBasicAuth.
                    auth_tuple = (
                        API_TOKEN_PREFIX.get(rest_client.service) or kwargs['auth_user'],
                        kwargs['auth_token']
                    )
                elif rest_client.service == TRANSPLATFORM_ENGINES[2]:
                    # Zanata needs credentials in the header.
                    kwargs['headers']['X-Auth-User'] = kwargs['auth_user']
                    kwargs['headers']['X-Auth-Token'] = kwargs['auth_token']
                elif rest_client.service == TRANSPLATFORM_ENGINES[3]:
                    # Weblate needs credentials in the headers either.
                    weblate_auth_user = API_TOKEN_PREFIX.get(rest_client.service) or kwargs['auth_user']
                    kwargs['headers']['Authorization'] = f"{weblate_auth_user} {kwargs['auth_token']}"
                kwargs.update(dict(auth_tuple=auth_tuple))
            if rest_client.service == GIT_PLATFORMS[0] and settings.GITHUB_TOKEN:
                # Setting up auth header for GitHub
                kwargs['headers']['Authorization'] = f"Bearer {settings.GITHUB_TOKEN}"
            return caller(rest_client, url, resource, *args, **kwargs)
        return inner_decorator
    return service_decorator
