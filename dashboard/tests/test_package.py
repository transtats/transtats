# Copyright 2018 Red Hat, Inc.
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
from collections import OrderedDict
from fixture.style import NamedDataStyle
from fixture.django_testcase import FixtureTestCase

from dashboard.managers.packages import PackagesManager
from dashboard.tests.testdata.db_fixtures import (
    LanguageData, LanguageSetData, PlatformData, ProductData, ReleaseData, PackageData
)
from dashboard.tests.testdata.mock_values import (
    mock_requests_get_add_package, mock_requests_get_validate_package,
    mock_requests_get_git_branches
)

db_fixture = DjangoFixture(style=NamedDataStyle())


class PackagesManagerTest(FixtureTestCase):

    packages_manager = PackagesManager()
    fixture = db_fixture
    datasets = [LanguageData, LanguageSetData, ProductData, ReleaseData, PackageData]

    def test_get_packages(self):
        """
        Test get_packages
        """
        packages = self.packages_manager.get_packages()
        self.assertEqual(len(packages), 4)
        package_names = [PackageData.package_anaconda.package_name,
                         PackageData.package_ibus.package_name]
        packages = self.packages_manager.get_packages(pkgs=package_names).values()
        self.assertEqual(len(packages), 2)
        self.assertEqual(packages[0]['package_name'], PackageData.package_anaconda.package_name)
        self.assertEqual(packages[1]['package_name'], PackageData.package_ibus.package_name)
        # todo: test the filtering according to params
        # params = ['package_name', 'upstream_url']
        # packages = self.packages_manager.get_packages(pkgs=['ibus'], pkg_params=params)
        # self.assertTrue(set(params).issubset(vars(packages.get()).keys()))

    def test_is_package_exist(self):
        """
        Test is_package_exist
        """
        self.assertTrue(self.packages_manager.is_package_exist(PackageData.package_anaconda.package_name))
        self.assertFalse(self.packages_manager.is_package_exist('otherpackage'))

    @patch('requests.get', new=mock_requests_get_add_package)
    def test_add_package(self):
        """
        Test add_package
        """
        transplatform = PlatformData.platform_zanata_fedora.platform_slug
        kwargs = {'package_name': 'authconfig', 'upstream_url': 'https://github.com/jcam/authconfig',
                  'transplatform_slug': transplatform, 'release_streams': ['fedora']}
        package_added = self.packages_manager.add_package(**kwargs)
        self.assertTrue(package_added)
        self.assertTrue(self.packages_manager.is_package_exist('authconfig'))
        package_added = self.packages_manager.add_package(**kwargs)
        self.assertFalse(package_added)

    def test_count_packages(self):
        """
        Test count_packages
        """
        count = self.packages_manager.count_packages()
        self.assertEqual(count, 4)

    def test_get_package_name_tuple(self):
        """
        Test get_package_name_tuple
        """
        tuples = self.packages_manager.get_package_name_tuple()
        self.assertEqual(len(tuples), 4)
        self.assertEquals(tuples[0], ('anaconda', 'anaconda'))

    @patch('requests.get', new=mock_requests_get_validate_package)
    def test_validate_package(self):
        """
        Test validate_package
        """
        transplatform = PlatformData.platform_zanata_public.platform_slug
        package_candlepin_name = PackageData.package_candlepin.package_name
        package_validated = self.packages_manager.validate_package(package_name=package_candlepin_name,
                                                                   transplatform_slug=transplatform)
        self.assertEqual(package_validated, package_candlepin_name)
        package_validated = self.packages_manager.validate_package(package_name='otherpackage',
                                                                   transplatform_slug=transplatform)
        self.assertFalse(package_validated)

    def test_get_lang_id_name_dict(self):
        """
        Test get_lang_id_name_dict
        """
        lang_dict = self.packages_manager.get_lang_id_name_dict(
            release_branch=ReleaseData.release_f27.release_slug
        )
        self.assertDictEqual(lang_dict, OrderedDict(
            [(('fr_FR', 'fr'), 'French'), (('ja_JP', 'ja'), 'Japanese'), (('ru_RU', 'ru'), 'Russian')]))

    def test_get_package_releases(self):
        """
        Test get_package_releases
        """
        package_releases = self.packages_manager.get_package_releases(
            PackageData.package_anaconda.package_name
        )
        self.assertEqual(len(package_releases), 1)
        self.assertEquals(package_releases[0].release_name, 'Fedora 27')
        self.assertEquals(package_releases[0].product_slug.product_name, 'Fedora')
        self.assertEquals(package_releases[0].language_set_slug.lang_set_name, 'F27 Set')

    @patch('requests.get', new=mock_requests_get_git_branches)
    def test_git_branches(self):
        """
        Test git_branches
        """
        scm_branch = self.packages_manager.git_branches(
            package_name=PackageData.package_anaconda.package_name
        )
        self.assertEqual(len(scm_branch), 2)
        self.assertListEqual(scm_branch, ['autoupdate-potfiles', 'master'])
