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

from sqlalchemy.orm.exc import NoResultFound
from transtats.config.settings.base import Session
from transtats.dashboard.models.user import User


class SQLAlchemyUserBackend(object):
    supports_anonymous_user = True
    supports_inactive_user = True

    def __init__(self):
        self.session = Session()

    def authenticate(self, username=None, password=None):
        try:
            user = self.session.query(User).filter_by(username=username).one()
            if user.check_password(password):
                return user
        except NoResultFound:
            return None

    def get_user(self, user_id):
        try:
            user = self.session.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            return None
        return user
