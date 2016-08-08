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
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class Packages(Base):
    """
    Packages Model
    """
    __tablename__ = 'packages'

    package_id = Column(Integer, primary_key=True)
    package_name = Column(String(200), unique=True)
    upstream_url = Column(String(200), unique=True)
    transplatform_slug = Column(String(10))
    transplatform_url = Column(String(200))
    release_stream_slug = Column(String(10))
    lang_set = Column(String(50))
    transtats_lastupdated = Column(DateTime)
