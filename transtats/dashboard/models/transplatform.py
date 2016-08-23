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

from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime

Base = declarative_base()


class TransPlatform(Base):
    """
    Translation Platforms Model
    """
    __tablename__ = 'transplatform'

    platform_id = Column(Integer, primary_key=True, autoincrement=True)
    engine_name = Column(String(50))
    subject = Column(String(50))
    api_url = Column(String(200))
    platform_slug = Column(String(10), unique=True)
    server_status = Column(Boolean)
    projects_json = Column(JSONB)
    projects_lastupdated = Column(DateTime)
