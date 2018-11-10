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
from dashboard.constants import RELSTREAM_SLUGS, TS_JOB_TYPES


class LanguageData(DataSet):
    class Meta:
        django_model = 'dashboard.Language'

    class lang_ja:
        locale_id = 'ja_JP'
        lang_name = 'Japanese'
        locale_alias = 'ja'
        locale_script = 'Hani'
        lang_status = True

    class lang_fr:
        locale_id = 'fr_FR'
        lang_name = 'French'
        locale_alias = 'fr'
        locale_script = 'Latn'
        lang_status = False

    class lang_ru:
        locale_id = 'ru_RU'
        lang_name = 'Russian'
        locale_alias = 'ru'
        locale_script = 'Cyrl'
        lang_status = True

    class lang_ko:
        locale_id = 'ko_KR'
        lang_name = 'Korean'
        locale_alias = 'ko'
        locale_script = 'Hang'
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


class PlatformData(DataSet):
    class Meta:
        django_model = 'dashboard.Platform'

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


class ProductData(DataSet):
    class Meta:
        django_model = 'dashboard.Product'

    class product_fedora:
        product_name = 'Fedora'
        product_slug = RELSTREAM_SLUGS[1]
        product_server = 'https://koji.fedoraproject.org/kojihub'
        top_url = 'https://kojipkgs.fedoraproject.org'
        product_build_tags = ['f28', 'f29', 'rawhide']
        product_status = True

    class product_rhel(product_fedora):
        product_name = 'RHEL'
        product_slug = RELSTREAM_SLUGS[0]
        product_server = 'https://companyserver.net/tool'
        top_url = 'http://companyserver.net/topdir'
        product_build_tags = ['tag1', 'tag2']
        product_status = False


class ReleaseData(DataSet):
    class Meta:
        django_model = 'dashboard.Release'

    class release_f27:
        release_name = 'Fedora 27'
        release_slug = 'fedora-27'
        product_slug = ProductData.product_fedora
        language_set_slug = LanguageSetData.lang_set_f27
        created_on = '2017-10-30 00:00+05:30'
        sync_calendar = False


class PackageData(DataSet):
    class Meta:
        django_model = 'dashboard.Package'

    class package_candlepin:
        package_name = 'candlepin'
        upstream_name = 'candlepin'
        upstream_url = 'https://github.com/candlepin/candlepin'
        platform_slug = PlatformData.platform_zanata_public
        platform_name = 'candlepin'
        platform_url = 'https://translate.zanata.org/project/view/candlepin'
        products = ['fedora']

    class package_subscription_manager:
        package_name = 'subscription-manager'
        upstream_name = 'subscription-manager'
        upstream_url = 'https://github.com/candlepin/subscription-manager'
        platform_slug = PlatformData.platform_zanata_public
        platform_name = 'subscription-manager'
        platform_url = 'https://translate.zanata.org/project/view/subscription-manager'
        products = ['fedora']

    class package_anaconda:
        package_name = 'anaconda'
        upstream_name = 'anaconda'
        upstream_url = 'https://github.com/rhinstaller/anaconda'
        platform_slug = PlatformData.platform_zanata_fedora
        platform_name = 'anaconda'
        platform_url = 'https://fedora.zanata.org/project/view/anaconda'
        products = ['fedora']

    class package_ibus:
        package_name = 'ibus'
        upstream_name = 'ibus'
        upstream_url = 'https://github.com/ibus/ibus'
        platform_slug = PlatformData.platform_zanata_fedora
        platform_name = 'ibus'
        platform_url = 'https://fedora.zanata.org/project/view/ibus'
        products = ['fedora']


class JobTemplateData(DataSet):
    class Meta:
        django_model = 'dashboard.JobTemplate'

    class template_syncupstream:
        job_template_type = TS_JOB_TYPES[2]
        job_template_name = 'Clone Upstream Repo'
        job_template_desc = 'Clone Package Upstream GIT Repository'
        job_template_json_str = '{"job":{"name":"upstream stats","type":"syncupstream", ' \
                                '"buildsys": "%BUILD_SYSTEM%", "exception": "raise", "execution": "sequential", ' \
                                '"package": "%PACKAGE_NAME%", "return_type": "json", "tags": ["%BUILD_TAG%"], ' \
                                '"tasks": [{"clone": "latest git branch"}]}}'

    class template_syncdownstream:
        job_template_type = TS_JOB_TYPES[3]
        job_template_name = 'Latest Build Info'
        job_template_desc = 'Get latest build info from build system'
        job_template_json_str = '{"job":{"name":"downstream stats","type":"syncdownstream", ' \
                                '"buildsys": "%BUILD_SYSTEM%", "exception": "raise", "execution": "sequential", ' \
                                '"package": "%PACKAGE_NAME%", "return_type": "json", "tags": ["%BUILD_TAG%"], ' \
                                '"tasks": [{"get": "latest build info"}]}}'
