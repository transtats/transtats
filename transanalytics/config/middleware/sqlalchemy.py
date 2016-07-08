#
# transanalytics - Translation Analytics
#
# Copyright (c) 2016 Sundeep Anand <suanand@redhat.com>
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of transanalytics.
#
# transanalytics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# transanalytics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with transanalytics.  If not, see <http://www.gnu.org/licenses/>.

from ..settings import base


class MySQLAlchemySessionMiddleware(object):
    def process_request(self, request):
        request.db_session = base.Session()

    def process_response(self, request, response):
        try:
            session = request.db_session
        except AttributeError:
            return response
        try:
            session.commit()
            return response
        except:
            session.rollback()
            raise

    def process_exception(self, request, exception):
        try:
            session = request.db_session
        except AttributeError:
            return
        session.rollback()
