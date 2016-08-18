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

    id = Column(Integer, primary_key=True, autoincrement=True)
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
