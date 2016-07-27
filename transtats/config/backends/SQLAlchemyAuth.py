#
# transtats - Translation Analytics
#
# Copyright (c) 2016 Sundeep Anand <suanand@redhat.com>
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of transtats.
#
# transtats is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# transtats is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with transtats.  If not, see <http://www.gnu.org/licenses/>.

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
