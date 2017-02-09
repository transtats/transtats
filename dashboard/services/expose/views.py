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

# django
from django.http import HttpResponse

# django third party
from rest_framework.views import APIView
from rest_framework.response import Response


class PingServer(APIView):
    """
    Ping Server API View
    """
    def get(self, request):
        """
        GET response
        :param request: Request object
        :return: Custom JSON
        """
        response_text = {'ping': 'pong'}
        if 'callback' in request.query_params and request.query_params.get('callback'):
            response_text = '%s(%s);' % (request.query_params['callback'], response_text)
            return HttpResponse(response_text, 'application/javascript')
        return Response(response_text)
