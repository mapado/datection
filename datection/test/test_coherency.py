# -*- coding: utf-8 -*-

"""Test suite of the timepoint coherency filter."""

import unittest

from datection.timepoint import Date
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import Time

from datection.models import DurationRRule
from datection.coherency import TimepointCoherencyFilter
from datection.coherency import RRuleCoherencyFilter


class TestTimepointCoherencyFilter(unittest.TestCase):

    """Test suite of the timepoint coherency filter."""

    def test_deduplicate_date_interval_and_dates(self):
        timepoints = [
            DateInterval(Date(2014, 11, 12), Date(2014, 11, 14)),
            Date(2014, 11, 12),
            Date(2014, 11, 13),
            Date(2014, 11, 14)
        ]
        cf = TimepointCoherencyFilter(timepoints)
        cf.deduplicate_date_interval_and_dates()

        self.assertEqual(
            cf.timepoints,
            [
                Date(2014, 11, 12),
                Date(2014, 11, 13),
                Date(2014, 11, 14)
            ]
        )

    def test_deduplicate_date_interval_and_datetimes(self):
        timepoints = [
            DateInterval(Date(2014, 11, 12), Date(2014, 11, 14)),
            Datetime(Date(2014, 11, 12), Time(18, 0), Time(20, 0)),
            Datetime(Date(2014, 11, 13), Time(18, 0), Time(20, 0)),
            Datetime(Date(2014, 11, 14), Time(18, 0), Time(20, 0))
        ]
        cf = TimepointCoherencyFilter(timepoints)
        cf.deduplicate_date_interval_and_dates()

        self.assertEqual(
            cf.timepoints,
            [
                Datetime(Date(2014, 11, 12), Time(18, 0), Time(20, 0)),
                Datetime(Date(2014, 11, 13), Time(18, 0), Time(20, 0)),
                Datetime(Date(2014, 11, 14), Time(18, 0), Time(20, 0))
            ]
        )


class TestRRuleTypeCoherencyHeuristics(unittest.TestCase):

    """Test the coherency heuristics based on the rrules type."""

    def test_apply_single_date_coherency_heuristics(self):
        schedule = [
            {   # Du 5 au 6 novembre 2015 à 8h
                'duration': 0,
                'rrule': ('DTSTART:20151105\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20151106T235959'),
            },
            {   # Le 7 novembre à 18h
                'duration': 0,
                'rrule': ('DTSTART:20151107\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=18'),
            },
            {   # les lundis à 18h
                'duration': 0,
                'rrule': ('DTSTART:00010101\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                          'BYHOUR=18;BYMINUTE=0;UNTIL=99991231T235959'),
                'unlimited': True
            },
        ]
        drrs = [DurationRRule(item) for item in schedule]
        rcf = RRuleCoherencyFilter(drrs)
        rcf.apply_single_date_coherency_heuristics()
        self.assertEqual(rcf.drrs, drrs[:2])  # 'les lundis à 18h' was removed

    def test_apply_long_date_interval_coherency_heuristics(self):
        schedule = [
            {
                # Du 1er janvier au 5 juin 2015
                'duration': 1439,
                'rrule': ('DTSTART:20150101\nRRULE:FREQ=DAILY;BYHOUR=0;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150605'),
            },
            {
                # Du 7 juin au 15 novembre 2015
                'duration': 1439,
                'rrule': ('DTSTART:20150607\nRRULE:FREQ=DAILY;BYHOUR=0;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20151115'),
            },
            {
                # Le 7 mars 2015
                'duration': 1439,
                'rrule': ('DTSTART:20150307\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=0'),
            }
        ]
        drrs = [DurationRRule(item) for item in schedule]
        rcf = RRuleCoherencyFilter(drrs)
        rcf.apply_long_date_interval_coherency_heuristics()
        self.assertEqual(rcf.drrs, drrs[:2])  # 'Le 7 mars 2015' was removed

    def test_apply_unlimited_date_interval_coherency_heuristics(self):
        schedule = [
            {   # les lundis à 18h
                'duration': 0,
                'rrule': ('DTSTART:00010101\nRRULE:FREQ=WEEKLY;'
                          'BYDAY=MO;BYHOUR=18;BYMINUTE=0;'
                          'UNTIL=99991231T235959'),
                'unlimited': True
            },
            {   # les mardi à 20h
                'duration': 0,
                'rrule': ('DTSTART:00010101\nRRULE:FREQ=WEEKLY;'
                          'BYDAY=TU;BYHOUR=20;BYMINUTE=0;'
                          'UNTIL=99991231T235959'),
                'unlimited': True
            },
            {   # le 5 mars 2015
                'duration': 1439,
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;'
                          'COUNT=1;BYMINUTE=0;BYHOUR=0'),
            },
        ]
        drrs = [DurationRRule(item) for item in schedule]
        rcf = RRuleCoherencyFilter(drrs)
        rcf.apply_unlimited_date_interval_coherency_heuristics()
        self.assertEqual(rcf.drrs, drrs[:2])  # 'Le 5 mars 2015' was removed
