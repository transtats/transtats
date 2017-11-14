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

# Application description
APP_DESC = "Language translation status of packages across releases"

# Supported translation platforms
TRANSPLATFORM_ENGINES = ('damnedlies', 'transifex', 'zanata')
DAMNEDLIES_SLUGS = ('DMLSPUB', )
TRANSIFEX_SLUGS = ('TNFXPUB', )
# Supported Zanata Instances
ZANATA_SLUGS = ('ZNTAPUB', 'ZNTAFED', 'ZNTAJBS', 'ZNTARHT', 'ZNTAVDR')

# Supported products
RELSTREAM_SLUGS = ('RHEL', 'fedora')

# Environment variables
DB_ENV_VARS = ('DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWD',
               'DATABASE_HOST', 'TRANSIFEX_USER', 'TRANSIFEX_PASSWD')

# Job Types
TS_JOB_TYPES = ('synctransplatform', 'syncrelschedule', 'syncupstream', 'syncdownstream')
