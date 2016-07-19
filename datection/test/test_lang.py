# -*- coding: utf-8 -*-

"""Test suite of the lang detection."""

import unittest
from datection.lang import detect_language


class TestLang(unittest.TestCase):

    """Test suite of the lang detection."""

    def test_non_integrated_lang_with_another_detected(self):
        schedule_desc = u'|Lundi de 11:00 \xe0 20:00|Mardi de 11:00'
        u'\xe0 20:00|Mercredi de 11:00 \xe0 20:00|Jeudi de 11:00 '
        u'\xe0 20:00|Vendredi de 11:00 \xe0 20:00|Samedi de 11:00 '
        u'\xe0 20:00|Dimanche de 11:00 \xe0 20:00'
        proposed_lang = u'zh'

        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'fr')

    def test_integrated_lang_with_another_detected(self):
        schedule_desc = u'|Lundi de 11:00 \xe0 20:00|Mardi de 11:00'
        u'\xe0 20:00|Mercredi de 11:00 \xe0 20:00'
        proposed_lang = u'en'

        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'fr')

    def test_non_integrated_lang_with_nothing_detected(self):
        schedule_desc = u'daladlas sjkdajk djkqsdj kjksdsqkj'
        proposed_lang = u'zh'

        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'zh')

    def test_integrated_locale(self):
        schedule_desc = u'10-12-2016'
        proposed_lang = u'en'

        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'en')

    def test_date_pattern_detection(self):
        schedule_desc = u'2016/12/20'
        proposed_lang = u'su'

        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'en')

    def test_ambiguous_words(self):
        schedule_desc = u"12 jan 2015"  # 'jan' can be fr or en

        proposed_lang = u'en'
        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'en')

        proposed_lang = u'fr'
        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'fr')

        schedule_desc = u'jeu 12 jan 2022'
        proposed_lang = u'en'
        lang = detect_language(schedule_desc, proposed_lang)
        self.assertEqual(lang, 'fr')
