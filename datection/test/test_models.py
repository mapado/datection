# -*- coding: utf-8 -*-

"""Test suite of the datection.model module."""

import unittest

from datection.models import DurationRRule
from dateutil.rrule import rrule
from datetime import datetime
from datetime import date
from datetime import time


class ContinuousDurationRRuleTest(unittest.TestCase):

    def setUp(self):
        self.schedule = {
            'continuous': True,
            'duration': 4890,
            'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                      'BYMINUTE=0;INTERVAL=1;UNTIL=20140308T235959'),
            'texts': [u' 5 mars \xe0 8h au 8 mars 2014 \xe0 17h30']
        }
        self.drr = DurationRRule(self.schedule)

    def test_start_datetime(self):
        self.assertEqual(self.drr.start_datetime, datetime(2014, 3, 5, 8, 0))

    def test_end_datetime(self):
        self.assertEqual(self.drr.end_datetime, datetime(2014, 3, 8, 17, 30))

    def test_is_continuous(self):
        self.assertTrue(self.drr.is_continuous)

    def test_date_interval(self):
        expected = (date(2014, 3, 5), date(2014, 3, 8))
        self.assertEqual(self.drr.date_interval, expected)

    def test_time_interval(self):
        expected = (time(8, 0), time(17, 30))
        self.assertEqual(self.drr.time_interval, expected)


class DurationRRuleTest(unittest.TestCase):

    def setUp(self):
        self.bounded_recurrence = {
            'duration': 1439,
            'rrule': ('DTSTART:20130305\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                      'UNTIL=20140428T235959'),
            'texts': [u'le lundi du 5 mars 2013 au 28 avril 2014']
        }
        self.bounded_recurrence_weekday_range = {
            'duration': 1439,
            'rrule': ('DTSTART:20130305\nRRULE:FREQ=WEEKLY;BYDAY=MO,WE;'
                      'UNTIL=20140428T235959'),
            'texts': [u'le lundi et mercredi, du 5 mars 2013 au 28 avril 2014']
        }
        self.one_time = {
            'duration': 0,
            'rrule': ('DTSTART:20130305\nRRULE:FREQ=DAILY;COUNT=1;'
                      'BYMINUTE=30;BYHOUR=15'),
            'texts': [u'5 mars 2013 à 15h30']
        }
        self.one_time_time_interval = {
            'duration': 90,
            'rrule': ('DTSTART:20130305\nRRULE:FREQ=DAILY;COUNT=1;'
                      'BYMINUTE=0;BYHOUR=14'),
            'texts': [u'5 mars 2013 de 14h à 15h30']
        }
        self.unbounded_recurrence = {
            'duration': 1439,
            'rrule': 'DTSTART:20130305\nRRULE:FREQ=WEEKLY;BYDAY=MO'
        }

    def test_rrule_property(self):
        drr = DurationRRule(self.bounded_recurrence)
        self.assertIsInstance(drr.rrule, rrule)

    def test_duration_property(self):
        drr = DurationRRule(self.bounded_recurrence)
        self.assertEqual(drr.duration, 1439)

    def test_start_datetime_property(self):
        drr = DurationRRule(self.one_time)
        self.assertEqual(drr.start_datetime, datetime(2013, 3, 5, 15, 30, 0))

    def test_start_datetime_property_no_time(self):
        drr = DurationRRule(self.bounded_recurrence)
        self.assertEqual(drr.start_datetime, datetime(2013, 3, 5, 0, 0, 0))

    def test_end_datetime_property_no_until(self):
        drr = DurationRRule(self.one_time)
        self.assertEqual(drr.end_datetime, datetime(2013, 3, 5, 15, 30, 0))

    def test_end_datetime_property_unbounded_recurrence(self):
        drr = DurationRRule(self.unbounded_recurrence)
        self.assertEqual(drr.end_datetime, datetime(2014, 3, 5, 23, 59))

    def test_end_datetime_property(self):
        drr = DurationRRule(self.bounded_recurrence)
        self.assertEqual(drr.end_datetime, datetime(2014, 4, 28, 23, 59))

    def test_date_interval_property(self):
        drr = DurationRRule(self.bounded_recurrence)
        expected = (date(2013, 3, 5), date(2014, 4, 28))
        self.assertEqual(drr.date_interval, expected)

    def test_date_interval_property_no_until(self):
        drr = DurationRRule(self.one_time)
        expected = (date(2013, 3, 5), None)
        self.assertEqual(drr.date_interval, expected)

    def test_time_interval(self):
        drr = DurationRRule(self.one_time_time_interval)
        expected = (time(14, 0), time(15, 30))
        self.assertEqual(drr.time_interval, expected)

    def test_time_interval_duration_zero(self):
        drr = DurationRRule(self.one_time)
        expected = (time(15, 30), time(15, 30))
        self.assertEqual(drr.time_interval, expected)

    def test_time_interval_all_day(self):
        drr = DurationRRule(self.bounded_recurrence)
        expected = (time(0, 0), time(23, 59))
        self.assertEqual(drr.time_interval, expected)

    def test_weekday_indexes(self):
        drr = DurationRRule(self.bounded_recurrence)
        self.assertEqual(drr.weekday_indexes, [0])

    def test_weekday_indexes_weekday_range(self):
        drr = DurationRRule(self.bounded_recurrence_weekday_range)
        self.assertEqual(drr.weekday_indexes, [0, 2])

    def test_weekday_indexes_no_weekday_recurrence(self):
        drr = DurationRRule(self.one_time)
        self.assertIsNone(drr.weekday_interval)

    def test_weekday_interval(self):
        drr = DurationRRule(self.bounded_recurrence)
        self.assertEqual(drr.weekday_interval, [0])

    def test_weekday_interval_weekday_range(self):
        drr = DurationRRule(self.bounded_recurrence_weekday_range)
        self.assertEqual(drr.weekday_interval, [0, 1, 2])

    def test_weekday_interval_no_weekday_recurrence(self):
        drr = DurationRRule(self.one_time)
        self.assertIsNone(drr.weekday_interval)
