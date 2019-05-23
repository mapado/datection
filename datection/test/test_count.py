# -*- coding: utf-8 -*-
import unittest
from datection.models import DurationRRule
from datection.combine.count import add_count_estimation


class TestCount(unittest.TestCase):

    def test_count_single_date(self):
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        single = DurationRRule(single)
        add_count_estimation(single)
        self.assertEqual(single.duration_rrule['estimated_count'], 1)

    def test_count_continuous(self):
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        cont = DurationRRule(cont)
        add_count_estimation(cont)
        self.assertEqual(cont.duration_rrule['estimated_count'], 13)

    def test_count_weekly_rec(self):
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly = DurationRRule(weekly)
        add_count_estimation(weekly)
        self.assertEqual(weekly.duration_rrule['estimated_count'], 8)
