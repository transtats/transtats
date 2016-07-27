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

import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password,
)
from django.contrib.auth.models import update_last_login, user_logged_in
user_logged_in.disconnect(update_last_login)

Base = declarative_base()


def random_characters(string_length=10):
    random = str(uuid.uuid4()).replace('-', '')
    return random[0:string_length]


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    salt = Column(String(10))
    password = Column(String(128))

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_password(self, password):
        if not self.salt:
            self.salt = random_characters(10)
        self.password = make_password(password, salt=self.salt)
