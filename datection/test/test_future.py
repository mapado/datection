# -*- coding: utf-8 -*-

import unittest
import datetime

from datection.dtfuture import is_future


class TestFuture(unittest.TestCase):

    def setUp(self):
        self.schedule = [
            {
                'duration': 1439,
                'rrule': ('DTSTART:20130305\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=0'),
            }
        ]

    def test_future(self):
        # reference date is one day before the schedule date
        today = datetime.datetime(2013, 3, 4, 0, 0, 0)
        self.assertTrue(is_future(self.schedule, reference=today))

    def test_not_future(self):
        # reference date is one day after the schedule date
        today = datetime.datetime(2013, 3, 6, 0, 0, 0)
        self.assertFalse(is_future(self.schedule, reference=today))

    def test_mixted_future_and_past_dates(self):
        # reference date is one day before the schedule date
        today = datetime.datetime(2013, 3, 6, 0, 0, 0)
        future_date = {
            # future date compared to date reference
            'duration': 1439,
            'rrule': ('DTSTART:20130308\nRRULE:FREQ=DAILY;COUNT=1;'
                      'BYMINUTE=0;BYHOUR=0'),
        }
        self.schedule.append(future_date)
        self.assertTrue(is_future(self.schedule, reference=today))
