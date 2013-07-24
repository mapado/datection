# -*- coding: utf-8 -*-

"""
Unit test of the human readable display of normalized dates
"""

import unittest

import datection


class DisplayTest(unittest.TestCase):

    def setUp(self):
        self.lang = 'fr'

    def test_date(self):
        text = u'15 mars 2013'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le 15 mars 2013.')

    def test_date_interval(self):
        text = u'du 15 au 22 mars 2013'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Du 15 au 22 mars 2013.')

    def test_date_list(self):
        text = u'les 5, 8, 18 et 25 avril 2014'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Les 5, 8, 18, 25 avril 2014.')

    def test_datetime(self):
        text = u'15 novembre 2013, 15h30'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le 15 novembre 2013 à 15h30.')

    def test_datetime_with_time_interval(self):
        text = u'15 novembre 2013, 15h30 - 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le 15 novembre 2013 de 15h30 à 18h.')

    def test_datetime_interval(self):
        text = u'du 15 au 25 novembre 2013, 15h30 - 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Du 15 au 25 novembre 2013 de 15h30 à 18h.')

    def test_datetime_interval_several_months(self):
        text = u'du 15 avril au 25 novembre 2013, 15h30 - 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Du 15 avril au 25 novembre 2013 de 15h30 à 18h.')

    def test_datetime_list(self):
        text = u'le 5 avril à 15h30 et le 18 mai 2013 à 16h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le 5 avril 2013 à 15h30.\nLe 18 mai 2013 à 16h.')

    def test_weekday_recurrence_all_year(self):
        text = u'tous les lundis'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le lundi.')

    def test_weekday_recurrence_time_interval(self):
        text = u'le lundi à 19h30'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le lundi, à 19h30.')

    def test_weekday_recurrence_time_interval2(self):
        text = u'le lundi de 19h30 à 22h30'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le lundi, de 19h30 à 22h30.')

    def test_weekday_recurrence_date_interval(self):
        text = u'le lundi, du 15 au 30 janvier 2013'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le lundi, du 15 au 30 janvier 2013.')

    def test_weekday_recurrence_datetime_interval(self):
        text = u'le lundi, du 15 au 30 janvier 2013 de 15h à 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, 'fr')
        self.assertEqual(output, u'Le lundi, du 15 au 30 janvier 2013, de 15h à 18h.')

    def test_weekday_recurrence_all_days(self):
        text = u'du lundi au dimanche, du 15 au 30 janvier 2013 de 15h à 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Tous les jours, du 15 au 30 janvier 2013, de 15h à 18h.')
