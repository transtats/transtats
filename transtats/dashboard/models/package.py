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

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class Packages(Base):
    """
    Packages Model
    """
    __tablename__ = 'packages'

    package_id = Column(Integer, primary_key=True, autoincrement=True)
    package_name = Column(String(200), unique=True)
    upstream_url = Column(String(500), nullable=False)
    transplatform_slug = Column(String(10))
    transplatform_url = Column(String(500))
    release_streams = Column(ARRAY(String(100)), default=[])
    lang_set = Column(String(50))
    transtats_lastupdated = Column(DateTime, nullable=True)
    package_details_json = Column(JSONB, nullable=True)
    details_json_lastupdated = Column(DateTime, nullable=True)
