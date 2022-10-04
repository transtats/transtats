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

import json
import iso8601
import requests
from datetime import timedelta

# django
from django.utils import timezone

# dashboard
from dashboard.constants import TRANSPLATFORM_ENGINES
from dashboard.models import CacheAPI, Platform

from dashboard.services.consume.config.memsource import \
    resources as memsource_resources, media_types as memsource_media_types


class CacheAPIManager(object):
    """Class to handle db interface to services"""

    EXPIRY_MIN = 60

    def save_api_response(self, req_base_url, req_resource, resp_content,
                          resp_content_json, *req_args, **req_kwargs):
        """Save API responses in db"""
        cache_params = {}
        match_params = {
            'base_url': req_base_url,
            'resource': req_resource,
        }
        cache_params.update(match_params)
        cache_params['request_args'] = req_args
        cache_params['request_kwargs'] = str(req_kwargs)
        cache_params['response_content'] = resp_content
        cache_params['response_content_json_str'] = json.dumps(resp_content_json)
        cache_params['expiry'] = timezone.now() + timedelta(minutes=self.EXPIRY_MIN)
        try:
            CacheAPI.objects.update_or_create(
                base_url=req_base_url, resource=req_resource, defaults=cache_params
            )
        except Exception as e:
            # log error
            pass

    def get_cached_response(self, base_url, resource):
        """
        Check cached response in db
        :param base_url:
        :param resource:
        :return:
        """
        try:
            fields = ['expiry', 'response_content', 'response_content_json_str']
            filter_params = {
                'base_url': base_url,
                'resource': resource,
            }
            cache = CacheAPI.objects.only(*fields).filter(**filter_params).first()
        except Exception as e:
            # log error
            pass
        else:
            if cache:
                if cache.expiry > timezone.now():
                    return cache.response_content, cache.response_content_json
        return False, False

    def tally_auth_token(self, server_url):
        """
        Tally auth token if it is still valid,
            if not get a new one, and save
        :return: api_auth_token: str
        """
        try:
            filter_params = dict(api_url=server_url)
            platform = Platform.objects.filter(**filter_params).first()
        except Exception as e:
            # log error
            pass
        else:
            # API auth token is still valid
            if platform and platform.engine_name == TRANSPLATFORM_ENGINES[4]:
                if platform.token_status and \
                        platform.token_api_json and \
                        platform.auth_login_id == \
                        platform.token_api_json.get("user", {}).get("userName", ""):
                    return platform.token_api_json.get("token", "")
                else:
                    # either no or invalid API auth token, prepare and call API
                    config = memsource_resources.get('request_token')
                    payload = {}
                    payload.update(dict(userName=platform.auth_login_id))
                    payload.update(dict(password=platform.auth_token_key))
                    headers = {}
                    headers['Accept'] = memsource_media_types[0]
                    headers['Content-Type'] = memsource_media_types[0]

                    auth_api_url = platform.api_url + "/api2/v1" + config.mount_point
                    response = requests.post(url=auth_api_url, json=payload, headers=headers)
                    if response.ok:
                        response_json = response.json()
                        token_expiry = iso8601.parse_date(response_json.get("expires", ""))
                        try:
                            # save in db and return token
                            Platform.objects.filter(**filter_params).update(
                                token_api_json_str=json.dumps(response.json()),
                                token_expiry=token_expiry
                            )
                        except Exception as e:
                            # log error
                            pass
                        return response_json.get("token", "")
        return ''
