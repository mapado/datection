# -*- coding: utf-8 -*-

"""Test suite of the timepoint coherency filter."""

import unittest

from datection.timepoint import Date
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import WeeklyRecurrence
from dateutil.rrule import SA

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

    def test_deduplicate_date_and_weekly(self):
        timepoints = [
            Date(2017, 9, 16),
            WeeklyRecurrence(
                DateInterval.make_undefined(),
                TimeInterval.make_all_day(),
                [SA]
            )
        ]
        cf = TimepointCoherencyFilter(timepoints)
        cf.deduplicates_weekly_recurrences_and_dates()

        self.assertEqual(cf.timepoints, [Date(2017, 9, 16)])

    def test_deduplicate_datetime_and_weekly(self):
        timepoints = [
            Datetime(Date(2017, 9, 16), Time(10, 30)),
            WeeklyRecurrence(
                DateInterval.make_undefined(),
                TimeInterval(Time(10, 30), Time(12, 30)),
                [SA]
            )
        ]
        cf = TimepointCoherencyFilter(timepoints)
        cf.deduplicates_weekly_recurrences_and_dates()

        self.assertEqual(cf.timepoints, [Datetime(Date(2017, 9, 16), Time(10, 30))])

    def test_remove_weekly_when_matching_date(self):
        timepoints = [
            Date(2017, 9, 16),
            WeeklyRecurrence(
                DateInterval.make_undefined(),
                TimeInterval(Time(10, 30), Time(12, 30)),
                [SA]
            )
        ]
        cf = TimepointCoherencyFilter(timepoints)
        cf.deduplicates_weekly_recurrences_and_dates()

        self.assertEqual(cf.timepoints, [Date(2017, 9, 16)])


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
                'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                          'BYHOUR=18;BYMINUTE=0'),
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
                'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;'
                          'BYDAY=MO;BYHOUR=18;BYMINUTE=0'),
                'unlimited': True
            },
            {   # les mardi à 20h
                'duration': 0,
                'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;'
                          'BYDAY=TU;BYHOUR=20;BYMINUTE=0'),
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


class TestRRuleNumberCoherencyHeuristics(unittest.TestCase):

    """Test the heuristics based on the RRule number."""

    @classmethod
    def setUpClass(cls):
        """Change the heuristics limits, to enable smaller datasets."""
        cls.MAX_SINGLE_DATE_RRULES = RRuleCoherencyFilter.MAX_SINGLE_DATE_RRULES
        cls.MAX_SMALL_DATE_INTERVAL_RRULES = RRuleCoherencyFilter.\
            MAX_SMALL_DATE_INTERVAL_RRULES

        RRuleCoherencyFilter.MAX_SINGLE_DATE_RRULES = 2
        RRuleCoherencyFilter.MAX_SMALL_DATE_INTERVAL_RRULES = 2

    @classmethod
    def tearDownClass(cls):
        RRuleCoherencyFilter.MAX_SINGLE_DATE_RRULES = cls.MAX_SINGLE_DATE_RRULES
        RRuleCoherencyFilter.MAX_SMALL_DATE_INTERVAL_RRULES = cls.\
            MAX_SMALL_DATE_INTERVAL_RRULES

    def test_apply_single_date_number_coherency_heuristics(self):
        schedule = [
            # Le 5, 6, 7 novembre 2015
            {
                'duration': 1439,
                'rrule': ('DTSTART:20151105\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=0'),
            },
            {
                'duration': 1439,
                'rrule': ('DTSTART:20151106\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=0'),
            },
            {
                'duration': 1439,
                'rrule': ('DTSTART:20151107\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=0'),
            }
        ]
        drrs = [DurationRRule(item) for item in schedule]
        rcf = RRuleCoherencyFilter(drrs)
        rcf.apply_single_date_number_coherency_heuristics()
        self.assertEqual(rcf.drrs, drrs[:2])

    def test_apply_small_date_interval_number_coherency_heuristics(self):
        schedule = [
            {   # Du 5 au 9 mars 2015,
                'duration': 1439,
                'rrule': ('DTSTART:20150315\nRRULE:FREQ=DAILY;BYHOUR=0;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150318'),
            },
            {  # Du 15 au 18 mars 2015
                'duration': 1439,
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=0;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150309'),
            },
            {   # Du 21 au 24 mars 2015
                'duration': 1439,
                'rrule': ('DTSTART:20150321\nRRULE:FREQ=DAILY;BYHOUR=0;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150324'),
            }
        ]
        drrs = [DurationRRule(item) for item in schedule]
        rcf = RRuleCoherencyFilter(drrs)
        rcf.apply_small_date_interval_number_coherency_heuristics()
        self.assertEqual(rcf.drrs, drrs[:2])

    def test_apply_long_date_interval_number_coherency_heuristics(self):
        schedule = [
            {   # Le lundi et mardi, Du 1er janvier au 2 mai 2015, de 8h à 15h
                'duration': 420,
                'rrule': ('DTSTART:20150101\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20150502T235959'),
            },
            {   # le lundi du 3 mai 2015 au 1er octobre 2015 de 8h à 12h
                'duration': 240,
                'rrule': ('DTSTART:20150503\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20151001T235959'),
            },
            {   # le mardi du 3 mai 2015 au 1er octobre 2015 de 8h à 12h
                'duration': 240,
                'rrule': ('DTSTART:20150503\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20151001T235959'),
            },
            {   # le lundi du 2 octobre 2015 au 4 mars 2016 de 8h à 12h
                'duration': 240,
                'rrule': ('DTSTART:20151002\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20160304T235959')
            }
        ]
        drrs = [DurationRRule(item) for item in schedule]
        rcf = RRuleCoherencyFilter(drrs)
        rcf.apply_long_date_interval_number_coherency_heuristics()
        out_schedule = [drr.duration_rrule for drr in rcf.drrs]
        self.assertListEqual(out_schedule, schedule[:3])

    def test_apply_unlimited_date_interval_number_coherency_heuristics(self):
        schedule = [
            {   # Le lundi et mardi, Du 1er janvier au 2 octobre 2015,
                # de 8h à 15h
                'duration': 420,
                'rrule': ('DTSTART:20150101\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20151002T235959'),
            },
            {   # le lundi du 3 octobre 2015 au 7 juillet 2016 de 8h à 12h
                'duration': 240,
                'rrule': ('DTSTART:20151003\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20160707T235959'),
            },
            {   # le mardi du 3 octobre 2015 au 7 juillet 2016 de 8h à 12h
                'duration': 240,
                'rrule': ('DTSTART:20151003\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20160707T235959'),
            },
        ]
        drrs = [DurationRRule(item) for item in schedule]
        rcf = RRuleCoherencyFilter(drrs)
        rcf.apply_unlimited_date_interval_number_coherency_heuristics()
        out_schedule = [drr.duration_rrule for drr in rcf.drrs]
        self.assertListEqual(out_schedule, schedule[:1])
