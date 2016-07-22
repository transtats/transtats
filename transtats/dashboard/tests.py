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

from django.test import TestCase

# Create your tests here.

from selenium import webdriver
from socket import error as SocketError
import errno

try:
    browser = webdriver.Firefox()
    browser.get('http://127.0.0.1:8000/')
except SocketError as e:
    if e.errno != errno.ECONNRESET:
        raise   # Not error we are looking for
    pass   # Handle error here.
else:
    assert 'transtats' in browser.title
