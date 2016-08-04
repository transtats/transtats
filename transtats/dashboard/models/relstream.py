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

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class ReleaseStream(Base):
    """
    Release Stream Model
    """
    __tablename__ = 'relstream'

    relstream_id = Column(Integer, primary_key=True)
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
