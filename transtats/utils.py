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

"""Some base utilities/classes."""
import logging

# third party
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

# django imports
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseRedirect
from django.urls import reverse


class TranstatsOIDCBackend(OIDCAuthenticationBackend):
    """OIDC Authentication Backend Wrapper"""

    logger = logging.getLogger(__name__)

    def filter_users_by_claims(self, claims):
        """Find users by matching username=sub."""
        # The claims.get and None-case were dropped, since if there is no sub,
        # the OpenID Connect specification was broken.
        return self.UserModel.objects.filter(username=claims['sub'])

    def create_user(self, claims):
        """ Create a new user from the retrieved claims. """
        email = claims.get('email')

        return self.UserModel.objects.create_user(claims['sub'], email=email)

    def authenticate(self, request, **kwargs):
        """Handles SuspiciousOperation, route to the OIDC code flow."""

        try:
            return super(TranstatsOIDCBackend, self).authenticate(request, **kwargs)
        except SuspiciousOperation:
            HttpResponseRedirect(reverse('admin:index'))
        except Exception as e:
            self.logger.log(40, str(e))
            raise Exception(str(e))

    def get_token(self, payload):
        payload.update({"redirect_uri": payload.get("redirect_uri").replace("http:", "https:")})
        return super().get_token(payload)
