# -*- coding: utf-8 -*-

"""
Unit test of the human readable display of normalized dates
"""

import unittest

import datection
import datetime

from ..display import to_start_end_datetimes, \
    consecutives, groupby_consecutive_dates, groupby_time, groupby_date
from ..utils import DurationRRule


class LongDisplayTest(unittest.TestCase):

    """Test the output of the LongScheduleFormatter formatter"""

    def setUp(self):
        self.lang = 'fr'

    def test_date(self):
        text = u'15 mars 2013'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Le 15 mars 2013')

    def test_date_interval(self):
        text = u'du 15 au 22 mars 2013'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Du 15 au 22 mars 2013')

    def test_date_list(self):
        text = u'les 5, 8, 18 et 25 avril 2014'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Les 5, 8, 18, 25 avril 2014')

    def test_datetime(self):
        text = u'15 novembre 2013, 15h30'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Le 15 novembre 2013 à 15 h 30')

    def test_datetime_with_time_interval(self):
        text = u'15 novembre 2013, 15h30 - 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Le 15 novembre 2013 de 15 h 30 à 18 h')

    def test_datetime_interval(self):
        text = u'du 15 au 25 novembre 2013, 15h30 - 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Du 15 au 25 novembre 2013 de 15 h 30 à 18 h')

    def test_datetime_interval_several_months(self):
        text = u'du 15 avril au 25 novembre 2013, 15h30 - 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Du 15 avril au 25 novembre 2013 de 15 h 30 à 18 h')

    def test_datetime_list(self):
        text = u'le 5 avril à 15h30 et le 18 mai 2013 à 16h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Le 5 avril 2013 à 15 h 30\nLe 18 mai 2013 à 16 h')

    def test_weekday_recurrence_all_year(self):
        text = u'tous les lundis'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Le lundi')

    def test_weekday_recurrence_time_interval(self):
        text = u'le lundi à 19h30'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Le lundi, à 19 h 30')

    def test_weekday_recurrence_time_interval2(self):
        text = u'le lundi de 19h30 à 22h30'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Le lundi, de 19 h 30 à 22 h 30')

    def test_weekday_recurrence_date_interval(self):
        text = u'le lundi, du 15 au 30 janvier 2013'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(output, u'Le lundi, du 15 au 30 janvier 2013')

    def test_weekday_recurrence_datetime_interval(self):
        text = u'le lundi, du 15 au 30 janvier 2013 de 15h à 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Le lundi, du 15 au 30 janvier 2013, de 15 h à 18 h')

    def test_weekday_recurrence_all_days(self):
        text = u'du lundi au dimanche, du 15 au 30 janvier 2013 de 15h à 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Du 15 au 30 janvier 2013 de 15 h à 18 h')

    def test_weekday_recurrence_all_days2(self):
        text = u'tous les jours, du 15 au 30 janvier 2013 de 15h à 18h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Du 15 au 30 janvier 2013 de 15 h à 18 h')

    def test_display_disjoint_weekdays(self):
        text = u'Le lundi, mercredi, vendredi de 5h à 8h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Le lundi, mercredi, vendredi, de 5 h à 8 h')

    def test_display_joined_weekdays(self):
        text = u'Du lundi au vendredi de 5h à 8h'
        schedule = datection.to_db(text, self.lang, only_future=False)
        output = datection.display(schedule, self.lang)
        self.assertEqual(
            output, u'Du lundi au vendredi, de 5 h à 8 h')


class ShortDisplayTest(unittest.TestCase):

    """Test the output of the ShortScheduleFormatter formatter"""

    def setUp(self):
        self.lang = 'fr'

    def test_display_today(self):
        schedule = [
            {
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,SU;'
                'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
            }
        ]
        d = datetime.date(2013, 8, 11)  # the 'today' of the test
        bounds = (
            datetime.datetime(2013, 8, 11, 0, 0),
            datetime.datetime(2013, 8, 11, 23, 59))
        expected = u"Aujourd'hui de 22 h 30 à 23 h 30"
        self.assertEqual(
            datection.display(
                schedule, self.lang, short=True, bounds=bounds, reference=d),
            expected)

    def test_display_tomorrow(self):
        schedule = [
            {
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,SU;'
                'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
            }
        ]
        d = datetime.date(2013, 8, 10)  # the 'today' of the test
        bounds = (
            datetime.datetime(2013, 8, 11, 0, 0),
            datetime.datetime(2013, 8, 11, 23, 59))
        expected = u"Demain de 22 h 30 à 23 h 30"
        self.assertEqual(
            datection.display(
                schedule, self.lang, short=True, bounds=bounds, reference=d),
            expected)

    def test_display_weekday(self):
        schedule = [
            {
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,SU;'
                'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
            }
        ]
        d = datetime.date(2013, 8, 14)  # the 'today' of the test
        bounds = (
            datetime.datetime(2013, 8, 14, 0, 0),
            datetime.datetime(2013, 8, 19, 23, 59))
        expected = u"Dimanche de 22 h 30 à 23 h 30 + 1 date"
        self.assertEqual(
            datection.display(
                schedule, self.lang, short=True, bounds=bounds, reference=d),
            expected)

    def test_display_full_date(self):
        schedule = [
            {
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,SU;'
                'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
            }
        ]
        d = datetime.date(2013, 8, 2)  # the 'today' of the test
        bounds = (
            datetime.datetime(2013, 8, 10, 0, 0),
            datetime.datetime(2013, 8, 19, 23, 59))
        expected = u"Le 11 août de 22 h 30 à 23 h 30 + 4 dates"
        self.assertEqual(
            datection.display(
                schedule, self.lang, short=True, bounds=bounds, reference=d),
            expected)

    def test_display_full_date_short_month(self):
        schedule = [
            {
                'duration': 60,
                'rrule': ('DTSTART:20131107\nRRULE:FREQ=DAILY;'
                'BYHOUR=22;BYMINUTE=30;UNTIL=20131130T235959')
            }
        ]
        d = datetime.date(2013, 11, 8)  # the 'today' of the test
        bounds = (
            datetime.datetime(2013, 11, 19, 0, 0),
            datetime.datetime(2013, 11, 25, 23, 59))
        expected = u"Le 19 nov. de 22 h 30 à 23 h 30 + 6 dates"
        self.assertEqual(
            datection.display(
                schedule, self.lang, short=True, bounds=bounds, reference=d),
            expected)

    def test_short_display_unbounded_rrule(self):
        schedule = [
            {
                'duration': 0,
                # no dtstart, no until!
                'rrule': ('DTSTART:\nRRULE:FREQ=DAILY;BYHOUR=22;BYMINUTE=30')
            }
        ]
        d = datetime.date(2013, 11, 19)  # the 'today' of the test
        bounds = (
            datetime.datetime(2013, 11, 19, 8, 0),
            datetime.datetime(2013, 11, 19, 23, 59))
        expected = u"Aujourd'hui à 22 h 30"
        self.assertEqual(
            datection.display(
                schedule, self.lang, short=True, bounds=bounds, reference=d),
            expected)


class TestUtilities(unittest.TestCase):

    """Tests of all the datection.display utility functions"""

    def test_to_start_end_datetimes(self):
        schedule = [
            DurationRRule({
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=WE,TH,FR;'
                'BYHOUR=22;BYMINUTE=30;UNTIL=20130809T235959')
            })
        ]
        expected = [
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 9, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 9, 23, 30, 0)
            }]
        self.assertEqual(
            to_start_end_datetimes(schedule), expected)

    def test_to_start_end_datetimes_start_bound(self):
        schedule = [
            DurationRRule({
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=WE,TH,FR;'
                          'BYHOUR=22;BYMINUTE=30;UNTIL=20130809T235959')
            })
        ]
        expected = [
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 9, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 9, 23, 30, 0)
            }]
        start_bound = datetime.date(2013, 8, 8)
        self.assertEqual(
            to_start_end_datetimes(schedule, start_bound=start_bound),
            expected)

    def test_consecutives(self):
        d1 = {
            'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
            'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
        }
        d2 = {
            'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
            'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
        }
        self.assertTrue(consecutives(d1, d2))

        d3 = {
            'start': datetime.datetime(2013, 8, 6, 22, 30, 0),
            'end': datetime.datetime(2013, 8, 6, 23, 30, 0)
        }
        self.assertTrue(consecutives(d3, d1))
        self.assertTrue(consecutives(d1, d3))
        self.assertFalse(consecutives(d2, d3))

    def test_groupby_consecutive_dates(self):
        datetimes = [
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 10, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 10, 23, 30, 0)
            }]

        expected = [[datetimes[0], datetimes[1]], [datetimes[2]]]
        self.assertEqual(groupby_consecutive_dates(datetimes), expected)

    def test_groupby_time(self):
        datetimes = [
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 10, 21, 0, 0),
                'end': datetime.datetime(2013, 8, 10, 21, 0, 0)
            }]

        expected = [[datetimes[0], datetimes[1]], [datetimes[2]]]
        self.assertEqual(groupby_time(datetimes), expected)

    def test_groupby_date(self):
        datetimes = [
            {
                'start': datetime.datetime(2013, 8, 7, 20, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 21, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 10, 21, 0, 0),
                'end': datetime.datetime(2013, 8, 10, 21, 0, 0)
            }]

        expected = [[datetimes[0], datetimes[1]], [datetimes[2]]]
        self.assertEqual(groupby_date(datetimes), expected)
