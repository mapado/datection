# -*- coding: utf-8 -*-

import unittest
import datetime

from datection.models import DurationRRule
from datection.utils import isoformat_concat, normalize_2digit_year


class UtilsTest(unittest.TestCase):

    def test_isoformat_concat(self):
        dt = datetime.datetime(2013, 8, 4, 8, 30, 0)
        fmt = isoformat_concat(dt)
        self.assertEqual(fmt, '20130804T083000')

    def test_rrule_duration_wrapper_recurrence(self):
        duration_rrule = {
            # le lundi, du 5 au 30 avril 2014, de 8h à 9h
            'duration': 60,
            'rrule': ('DTSTART:20140405\nRRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;'
                      'BYMINUTE=0;UNTIL=20140430')
        }
        wrapper = DurationRRule(duration_rrule)
        self.assertEqual(wrapper.duration, 60)
        self.assertEqual(
            str(wrapper.rrule), 'FREQ=WEEKLY;BYWEEKDAY=MO;BYHOUR=8;BYMINUTE=0')
        self.assertTrue(wrapper.is_recurring)
        self.assertFalse(wrapper.is_all_year_recurrence)

    def test_rrule_duration_wrapper_allyear_recurrence(self):
        duration_rrule = {
            # le lundi de 8h à 9h
            'duration': 60,
            'rrule': ('DTSTART:20140405\nRRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;'
                      'BYMINUTE=0;UNTIL=20150405')
        }
        wrapper = DurationRRule(duration_rrule)
        self.assertTrue(wrapper.is_recurring)
        self.assertTrue(wrapper.is_all_year_recurrence)

    def test_rrule_duration_wrapper_no_recurrence(self):
        duration_rrule = {
            # du 5 au 30 avril 2014, de 8h à 9h
            'duration': 60,
            'rrule': ('DTSTART:20140405\nRRULE:FREQ=DAILY;BYHOUR=8;BYMINUTE=0;'
                      'INTERVAL=1;UNTIL=20140430T235959')
        }
        wrapper = DurationRRule(duration_rrule)
        self.assertFalse(wrapper.is_recurring)
        self.assertFalse(wrapper.is_all_year_recurrence)

    def test_serialize_2digit_year(self):
        self.assertEqual(normalize_2digit_year(12), 2012)
        self.assertEqual(normalize_2digit_year(20), 2020)
        self.assertEqual(normalize_2digit_year(30), 1930)
        self.assertEqual(normalize_2digit_year(80), 1980)
