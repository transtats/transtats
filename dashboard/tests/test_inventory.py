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

from mock import patch
from fixture import DjangoFixture
from fixture.style import NamedDataStyle
from fixture.django_testcase import FixtureTestCase
from dashboard.managers.inventory import InventoryManager, PackagesManager
from dashboard.models import ReleaseStream
from dashboard.tests.testdata.db_fixtures import (
    LanguagesData, LanguageSetData, TransPlatformData, ReleaseStreamData,
    StreamBranchesData, PackagesData
)
from dashboard.tests.testdata.mock_values import (mock_requests_get_add_package,
                                                  mock_requests_get_validate_package)

db_fixture = DjangoFixture(style=NamedDataStyle())


class InventoryManagerTest(FixtureTestCase):

    inventory_manager = InventoryManager()
    fixture = db_fixture
    datasets = [LanguagesData, LanguageSetData, TransPlatformData, ReleaseStreamData, StreamBranchesData]

    def test_get_locales(self):
        """
        Test get_locales
        """
        japanese_locale = self.inventory_manager.get_locales(pick_locales=['ja_JP'])
        self.assertEqual(len(japanese_locale), 1)
        self.assertEqual(japanese_locale[0].lang_name, 'Japanese')
        self.assertEqual(japanese_locale[0].locale_alias, 'ja')

    def test_get_locale_alias(self):
        """
        Test get_locale_alias
        """
        locale_alias = self.inventory_manager.get_locale_alias('fr_FR')
        self.assertEqual(locale_alias, 'fr')

        locale_alias = self.inventory_manager.get_locale_alias('de_DE')
        self.assertEqual(locale_alias, 'de_DE')

    def test_get_locales_set(self):
        """
        Test get_locales_set
        """
        active_locales, inactive_locales, aliases = \
            self.inventory_manager.get_locales_set()
        self.assertEqual(len(active_locales), 3)
        self.assertEqual(len(inactive_locales), 1)
        self.assertEqual(len(aliases), 4)

    def test_get_langset(self):
        """
        Test get_get_langset
        """
        lang_set = self.inventory_manager.get_langset(langset_slug='custom-set')
        self.assertEqual(lang_set.lang_set_name, 'Custom Set')
        self.assertEqual(lang_set.lang_set_color, 'Peru')

    def test_get_langsets(self):
        """
        Test get_langsets
        """
        lang_sets = self.inventory_manager.get_langsets(
            fields=['lang_set_name', 'locale_ids']
        )
        self.assertEqual(len(lang_sets), 2)
        self.assertNotIn('lang_set_color', vars(lang_sets[0]))
        self.assertListEqual(lang_sets[0].locale_ids, ['fr_FR', 'ja_JP'])

    def test_get_locale_groups(self):
        """
        Test get_locale_groups
        """
        locale_groups = self.inventory_manager.get_locale_groups('ja_JP')
        self.assertDictEqual(locale_groups, {'ja_JP': ['custom-set', 'f27-set']})

    def test_get_all_locales_groups(self):
        """
        Test get_all_locales_groups
        """
        groups_of_all_locales = self.inventory_manager.get_all_locales_groups()
        self.assertDictEqual(groups_of_all_locales,
                             {'ja_JP': ['custom-set', 'f27-set'], 'fr_FR': ['custom-set', 'f27-set'],
                              'ru_RU': ['f27-set'], 'ko_KR': []})

    def test_get_translation_platforms(self):
        """
        Test get_translation_platforms
        """
        transplatforms = self.inventory_manager.get_translation_platforms(engine='zanata')
        self.assertEqual(transplatforms[1].api_url, 'https://translate.zanata.org')
        self.assertEqual(transplatforms[1].platform_slug, 'ZNTAPUB')

    def test_get_transplatforms_set(self):
        """
        Test get_transplatforms_set
        """
        active_platforms, inactive_platforms = self.inventory_manager.get_transplatforms_set()
        self.assertEqual(len(active_platforms), 2)
        self.assertEqual(len(inactive_platforms), 0)

    def test_get_transplatform_slug_url(self):
        """
        test get_transplatform_slug_url
        """
        slug_url_tuple = self.inventory_manager.get_transplatform_slug_url()
        self.assertTupleEqual(slug_url_tuple, (('ZNTAFED', 'https://fedora.zanata.org'),
                                               ('ZNTAPUB', 'https://translate.zanata.org')))

    def test_get_relbranch_locales(self):
        """
        Test get_relbranch_locales
        """
        relbranch_locales = self.inventory_manager.get_relbranch_locales("nonexisting-relbranch")
        self.assertFalse(relbranch_locales)
        relbranch_locales = self.inventory_manager.get_relbranch_locales('fedora-27')
        self.assertListEqual(relbranch_locales, ['ja_JP', 'fr_FR', 'ru_RU'])

    def test_get_release_streams(self):
        """
        Test get_release_streams
        """
        relstream_fedora = ReleaseStream.objects.get(relstream_name='Fedora')
        relstream_rhel = ReleaseStream.objects.get(relstream_name='RHEL')

        release_streams = self.inventory_manager.get_release_streams()
        self.assertEqual(len(release_streams), 2)
        self.assertIn(relstream_fedora, release_streams)
        self.assertIn(relstream_rhel, release_streams)

        release_streams = self.inventory_manager.get_release_streams(stream_slug='RHEL')
        self.assertEqual(len(release_streams), 1)
        self.assertIn(relstream_rhel, release_streams)

        release_streams = self.inventory_manager.get_release_streams(only_active=True)
        self.assertEqual(len(release_streams), 1)
        self.assertIn(relstream_fedora, release_streams)

    def test_get_locale_lang_tuple(self):
        """
        Test get_locale_lang_tuple
        """
        ru_tuple = ('ru_RU', 'Russian')
        fr_tuple = ('fr_FR', 'French')
        locale_lang_tuple = self.inventory_manager.get_locale_lang_tuple()
        self.assertEqual(len(locale_lang_tuple), 3)

        locale_lang_tuple = self.inventory_manager.get_locale_lang_tuple(locales=['fr_FR', 'ru_RU'])
        self.assertEqual(len(locale_lang_tuple), 2)
        self.assertTupleEqual(locale_lang_tuple[0], ru_tuple)
        self.assertTupleEqual(locale_lang_tuple[1], fr_tuple)

    def test_get_relstream_slug_name(self):
        """
        Test get_relstream_slug_name
        """
        relstream_slug_name_tuple = self.inventory_manager.get_relstream_slug_name()
        self.assertEqual(len(relstream_slug_name_tuple), 1)
        self.assertTupleEqual(relstream_slug_name_tuple[0], ('fedora', 'Fedora'))


class PackagesManagerTest(FixtureTestCase):

    packages_manager = PackagesManager()
    fixture = db_fixture
    datasets = [PackagesData]

    def test_get_packages(self):
        """
        Test get_packages
        """
        packages = self.packages_manager.get_packages()
        self.assertEqual(len(packages), 4)
        package_names = [PackagesData.package_anaconda.package_name,
                         PackagesData.package_ibus.package_name]
        packages = self.packages_manager.get_packages(pkgs=package_names).values()
        self.assertEqual(len(packages), 2)
        self.assertEqual(packages[0]['package_name'], PackagesData.package_anaconda.package_name)
        self.assertEqual(packages[1]['package_name'], PackagesData.package_ibus.package_name)
        # todo: test the filtering according to params
        # params = ['package_name', 'upstream_url']
        # packages = self.packages_manager.get_packages(pkgs=['ibus'], pkg_params=params)
        # self.assertTrue(set(params).issubset(vars(packages.get()).keys()))

    def test_is_package_exist(self):
        """
        Test is_package_exist
        """
        self.assertTrue(self.packages_manager.is_package_exist(PackagesData.package_anaconda.package_name))
        self.assertFalse(self.packages_manager.is_package_exist('otherpackage'))

    @patch('requests.get', new=mock_requests_get_add_package)
    def test_add_package(self):
        """
        Test add_package
        """
        kwargs = {'package_name': 'authconfig', 'upstream_url': 'https://github.com/jcam/authconfig',
                  'transplatform_slug': 'ZNTAFED', 'release_streams': ['fedora']}
        package_added = self.packages_manager.add_package(**kwargs)
        self.assertTrue(package_added)
        self.assertTrue(self.packages_manager.is_package_exist('authconfig'))
        package_added = self.packages_manager.add_package(**kwargs)
        self.assertFalse(package_added)

    @patch('requests.get', new=mock_requests_get_validate_package)
    def test_validate_package(self):
        """
        Test validate_package
        """
        transplatform = TransPlatformData.platform_zanata_public.platform_slug
        package_candlepin_name = PackagesData.package_candlepin.package_name
        package_validated = self.packages_manager.validate_package(package_name=package_candlepin_name,
                                                                   transplatform_slug=transplatform)
        self.assertEqual(package_validated, package_candlepin_name)
        package_validated = self.packages_manager.validate_package(package_name='otherpackage',
                                                                   transplatform_slug=transplatform)
        self.assertFalse(package_validated)
