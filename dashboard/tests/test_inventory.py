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

from django.test import TestCase
from dashboard.managers.inventory import InventoryManager
from dashboard.models import Languages, LanguageSet, TransPlatform, ReleaseStream, StreamBranches
from dashboard.constants import RELSTREAM_SLUGS


class InventoryTest(TestCase):

    inventory_manager = InventoryManager()

    def setUp(self):
        """
        Lets dump some test data in db
        """
        Languages.objects.update_or_create(
            locale_id='ja_JP', lang_name='Japanese', locale_alias='ja', lang_status=True
        )

        Languages.objects.update_or_create(
            locale_id='fr_FR', lang_name='French', locale_alias='fr', lang_status=False
        )

        Languages.objects.update_or_create(
            locale_id='ru_RU', lang_name='Russian', locale_alias='ru', lang_status=True
        )

        Languages.objects.update_or_create(
            locale_id='ko_KR', lang_name='Korean', locale_alias='ko', lang_status=True
        )

        LanguageSet.objects.update_or_create(
            lang_set_name='Custom Set', lang_set_slug='custom-set', lang_set_color='Peru',
            locale_ids=['fr_FR', 'ja_JP']
        )

        LanguageSet.objects.update_or_create(
            lang_set_name='F27 Set', lang_set_slug='f27-set', lang_set_color='Green',
            locale_ids=['ja_JP', 'fr_FR', 'ru_RU']
        )

        TransPlatform.objects.update_or_create(
            engine_name='zanata', subject='public', api_url='https://translate.zanata.org',
            platform_slug='ZNTAPUB', server_status=True
        )

        # todo: specify top_url (if top_url is missing, it should raise error but it doesn't)
        ReleaseStream.objects.update_or_create(
            relstream_name='Fedora', relstream_slug=RELSTREAM_SLUGS[1],
            relstream_server='http://koji.fedoraproject.org/kojihub', relstream_status=True
        )

        ReleaseStream.objects.update_or_create(
            relstream_name='RHEL', relstream_slug=RELSTREAM_SLUGS[0],
            relstream_server='http://companyserver.net/tool', top_url='http://companyserver.net/topdir',
            relstream_status=False
        )

        StreamBranches.objects.update_or_create(
            relbranch_name='Fedora 27', relbranch_slug='fedora-27', relstream_slug=RELSTREAM_SLUGS[1],
            lang_set='f27-set', created_on='2017-10-30 00:00+05:30', sync_calendar=False
        )

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
        self.assertEqual(transplatforms[0].api_url, 'https://translate.zanata.org')
        self.assertEqual(transplatforms[0].platform_slug, 'ZNTAPUB')

    def test_get_transplatforms_set(self):
        """
        Test get_transplatforms_set
        """
        active_platforms, inactive_platforms = self.inventory_manager.get_transplatforms_set()
        self.assertEqual(len(active_platforms), 1)
        self.assertEqual(len(inactive_platforms), 0)

    def test_get_transplatform_slug_url(self):
        """
        test get_transplatform_slug_url
        """
        slug_url_tuple = self.inventory_manager.get_transplatform_slug_url()
        self.assertTupleEqual(slug_url_tuple, (('ZNTAPUB', 'https://translate.zanata.org'),))

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
