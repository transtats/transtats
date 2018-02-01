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
#
# This file contains fixture data used for tests

from fixture import DataSet
from dashboard.constants import RELSTREAM_SLUGS


class LanguagesData(DataSet):
    class Meta:
        django_model = 'dashboard.Languages'

    class lang_ja:
        locale_id = 'ja_JP'
        lang_name = 'Japanese'
        locale_alias = 'ja'
        lang_status = True

    class lang_fr:
        locale_id = 'fr_FR'
        lang_name = 'French'
        locale_alias = 'fr'
        lang_status = False

    class lang_ru:
        locale_id = 'ru_RU'
        lang_name = 'Russian'
        locale_alias = 'ru'
        lang_status = True

    class lang_ko:
        locale_id = 'ko_KR'
        lang_name = 'Korean'
        locale_alias = 'ko'
        lang_status = True


class LanguageSetData(DataSet):
    class Meta:
        django_model = 'dashboard.LanguageSet'

    class lang_set_custom:
        lang_set_name = 'Custom Set'
        lang_set_slug = 'custom-set'
        lang_set_color = 'Peru'
        locale_ids = ['fr_FR', 'ja_JP']

    class lang_set_f27:
        lang_set_name = 'F27 Set'
        lang_set_slug = 'f27-set'
        lang_set_color = 'Green'
        locale_ids = ['ja_JP', 'fr_FR', 'ru_RU']


class TransPlatformData(DataSet):
    class Meta:
        django_model = 'dashboard.TransPlatform'

    class platform_zanata_public:
        engine_name = 'zanata'
        subject = 'public'
        api_url = 'https://translate.zanata.org'
        platform_slug = 'ZNTAPUB'
        server_status = True

    class platform_zanata_fedora:
        engine_name = 'zanata'
        subject = 'fedora'
        api_url = 'https://fedora.zanata.org'
        platform_slug = 'ZNTAFED'
        server_status = True


class ReleaseStreamData(DataSet):
    class Meta:
        django_model = 'dashboard.ReleaseStream'

    class relstream_fedora:
        relstream_name = 'Fedora'
        relstream_slug = RELSTREAM_SLUGS[1]
        relstream_server = 'http://koji.fedoraproject.org/kojihub'
        top_url = 'https://kojipkgs.fedoraproject.org'
        relstream_status = True

    class relstream_rhel:
        relstream_name = 'RHEL'
        relstream_slug = RELSTREAM_SLUGS[0]
        relstream_server = 'http://companyserver.net/tool'
        top_url = 'http://companyserver.net/topdir'
        relstream_status = False


class StreamBranchesData(DataSet):
    class Meta:
        django_model = 'dashboard.StreamBranches'

    class streambranch_f27:
        relbranch_name = 'Fedora 27'
        relbranch_slug = 'fedora-27'
        relstream_slug = RELSTREAM_SLUGS[1]
        lang_set = 'f27-set'
        created_on = '2017-10-30 00:00+05:30'
        sync_calendar = False


class PackagesData(DataSet):
    class Meta:
        django_model = 'dashboard.Packages'

    class package_candlepin:
        package_name = 'candlepin'
        upstream_name = 'candlepin'
        upstream_url = 'https://github.com/candlepin/candlepin'
        transplatform_slug = TransPlatformData.platform_zanata_public
        transplatform_name = 'candlepin'
        transplatform_url = 'https://translate.zanata.org/project/view/candlepin'
        release_streams = ['fedora']

    class package_subscription_manager:
        package_name = 'subscription-manager'
        upstream_name = 'subscription-manager'
        upstream_url = 'https://github.com/candlepin/subscription-manager'
        transplatform_slug = TransPlatformData.platform_zanata_public
        transplatform_name = 'subscription-manager'
        transplatform_url = 'https://translate.zanata.org/project/view/subscription-manager'
        release_streams = ['fedora']

    class package_anaconda:
        package_name = 'anaconda'
        upstream_name = 'anaconda'
        upstream_url = 'https://github.com/rhinstaller/anaconda'
        transplatform_slug = TransPlatformData.platform_zanata_fedora
        transplatform_name = 'anaconda'
        transplatform_url = 'https://fedora.zanata.org/project/view/anaconda'
        release_streams = ['fedora']

    class package_ibus:
        package_name = 'ibus'
        upstream_name = 'ibus'
        upstream_url = 'https://github.com/ibus/ibus'
        transplatform_slug = TransPlatformData.platform_zanata_fedora
        transplatform_name = 'ibus'
        transplatform_url = 'https://fedora.zanata.org/project/view/ibus'
        release_streams = ['fedora']
