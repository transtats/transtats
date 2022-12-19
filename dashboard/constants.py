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

# IMP: always APPEND tuples with new values
# this defines scope of the application

# Supported translation platforms
TRANSPLATFORM_ENGINES = ('damnedlies', 'transifex', 'zanata', 'weblate', 'phrase')
TP_BRANCH_CALLING_NAME = (
    (TRANSPLATFORM_ENGINES[0], 'Branches'),
    (TRANSPLATFORM_ENGINES[1], 'Resources'),
    (TRANSPLATFORM_ENGINES[2], 'Versions'),
    (TRANSPLATFORM_ENGINES[3], 'Components'),
    (TRANSPLATFORM_ENGINES[4], 'Jobs'),
)

API_TOKEN_PREFIX = {
    TRANSPLATFORM_ENGINES[1]: "api",
    TRANSPLATFORM_ENGINES[3]: "Token",
    TRANSPLATFORM_ENGINES[4]: "ApiToken",
}

DAMNEDLIES_SLUGS = ('DMLSPUB', )
MEMSOURCE_SLUGS = ('MSRCPUB', )
TRANSIFEX_SLUGS = ('TNFXPUB', )
WEBLATE_SLUGS = ('WLTEPUB', 'WLTEFED')
ZANATA_SLUGS = ('ZNTAPUB', 'ZNTAFED', 'ZNTAJBS', 'ZNTARHT', 'ZNTAVDR')

# Supported products
RELSTREAM_SLUGS = ('RHEL', 'fedora', 'RHV', 'satellite', 'console')

# Environment variables
DB_ENV_VARS = ('DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWD',
               'DATABASE_HOST', 'TRANSIFEX_USER', 'TRANSIFEX_PASSWD')

# Job Types
TS_JOB_TYPES = ('synctransplatform', 'syncrelschedule', 'syncupstream', 'syncdownstream',
                'syncbuildtags', 'stringchange', 'verifytrans', 'pushtrans', 'pulltrans',
                'dpushtrans', 'pulltransmerge')

TS_CI_JOBS = (TS_JOB_TYPES[7], TS_JOB_TYPES[8], TS_JOB_TYPES[9], TS_JOB_TYPES[10])
PIPELINE_CONFIG_EVENTS = ('Push Translations', 'Pull Translations', 'Update Source')
JOB_MULTIPLE_BRANCHES_VAR = "%RESPECTIVE%"

# Branch Mapping Keys
BRANCH_MAPPING_KEYS = ('platform_version', 'buildsys', 'buildsys_tag', 'upstream_release')

# Supported Build Systems
BUILD_SYSTEMS = ('brew', 'koji')

# Supported File Formats
TRANSLATION_FILE_FORMATS = ('po', 'json')

# YML Jobs Execution Types
JOB_EXEC_TYPES = ('sequential', 'parallel')

# Translation Workload Table Headers
WORKLOAD_HEADERS = ('Total', 'Translated', 'Untranslated', 'Remaining')

# Calendar Verbs
CALENDAR_VERBS = ('BEGIN:VEVENT', 'END:VEVENT', 'BEGIN:VTODO', 'END:VTODO')

# Git Repositories
GIT_PLATFORMS = ('GitHub', 'GitLab', 'Pagure')
GIT_REPO_TYPE = ('default', 'localization', TRANSPLATFORM_ENGINES[3], TRANSPLATFORM_ENGINES[1],
                 TRANSPLATFORM_ENGINES[2])

SYS_EMAIL_ADDR = "system@transtats.org"
RH_EMAIL_ADDR = "transtats@redhat.com"
