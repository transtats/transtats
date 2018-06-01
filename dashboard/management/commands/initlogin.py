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

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = 'Creates SuperUser Accounts'

    def handle(self, *args, **options):
        if User.objects.count() == 0:
            for user in settings.ADMINS:
                username = user[0].strip()
                email = user[1]
                password = settings.ADMIN_INITIAL_PASSWORD
                print('Creating account for %s (%s)' % (username, email))
                admin = User.objects.create_superuser(
                    email=email, username=username, password=password
                )
                admin.is_active = True
                admin.is_admin = True
                admin.save()
        else:
            print('SuperUser account can only be created if no Accounts exist.')
