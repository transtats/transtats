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

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class ReleaseStream(Base):
    """
    Release Stream Model
    """
    __tablename__ = 'relstream'

    relstream_id = Column(Integer, primary_key=True, autoincrement=True)
    relstream_name = Column(String(50))
    relstream_slug = Column(String(10), unique=True)
    relstream_server = Column(String(200), unique=True)
    relstream_built = Column(String(10))
    srcpkg_format = Column(String(10))
    top_url = Column(String(200))
    web_url = Column(String(200))
    krb_service = Column(String(50))
    auth_type = Column(String(50))
    amqp_server = Column(String(200))
    msgbus_exchange = Column(String(20))
    relstream_status = Column(String(10))
