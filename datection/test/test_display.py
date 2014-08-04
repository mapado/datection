# -*- coding: utf-8 -*-

"""Test the datection.display function"""

import datection
import unittest


class TestDisplay(unittest.TestCase):

    """Test the datection.display function."""

    def assertDisplayEqual(self, text, result, lang='fr'):
        """Converts the argument text to a list of duration/rrule dicts,
        render them in the argument language, and check that the result
        is the same than the argument result.

        """
        sch = datection.to_db(text, lang, only_future=False)
        fmt = datection.display(sch, lang)
        self.assertEqual(fmt, result)

    def test_past_date(self):
        self.assertDisplayEqual(
            u'12/06/2013 Période Ouverture 2013', u'Le 12 juin 2013')

    def test_past_date_interval(self):
        self.assertDisplayEqual(
            u"Du 01/01/2013 au 31/12/2013 Périodes d'ouvertures 2013",
            u'Du 1er janvier au 31 décembre 2013')
