# Copyright 2017 Red Hat, Inc.
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

import koji
from subprocess import Popen, PIPE
from dashboard.managers.base import BaseManager

__all__ = ['KojiResources']


class KojiResources(object):
    """
    Koji Resources
    """
    def __init__(self):
        """
        Constructor
        """

        # self.establish_kticket()

        print("Koji Version: %s" % koji.API_VERSION)
        server = "http://koji.fedoraproject.org/kojihub/"
        session = koji.ClientSession(server)
        session.gssapi_login()

        active_repos = session.getActiveRepos()
        print("Active Repos: %s\n" % ", ".join(set([repo['tag_name'] for repo in active_repos])))

    def establish_kticket(self):
        """
        Get kerberos ticket in-place
        """
        userid = "transtats"
        realm = "FEDORAPROJECT.ORG"

        kinit = '/usr/bin/kinit'
        kinit_args = [kinit, '%s@%s' % (userid, realm)]
        kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        kinit.stdin.write(b'password')
        kinit.wait()


class DownstreamManager(BaseManager):
    """
    Packages Downstream Manager
    """
    pass
