# -*- coding: utf-8 -*-

import unittest

from freezegun import freeze_time

from datetime import datetime
from datection.export import schedule_to_discretised_days
from datection.export import schedule_first_date
from datection.export import schedule_last_date
from datection.export import schedule_next_date
from datection.export import discretised_days_to_scheduletags
from datection.export import split_past_and_future
from datection.export import terminate_infinite_schedule


class ExportScheduleToSQLTest(unittest.TestCase):

    """Test the rrule --> SQL schedule conversion utilities."""

    def test_schedule_to_discretised_days(self):
        schedule = [
            {
                'duration': 4890,
                'rrule': ('DTSTART:20141104\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141105T235959'),
            },
            {
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            },
        ]
        dates = schedule_to_discretised_days(schedule)

        expected = [
            datetime(2014, 11, 4, 8, 0, 0),
            datetime(2014, 11, 5, 8, 0, 0),
            datetime(2014, 12, 4, 8, 0, 0),
            datetime(2014, 12, 5, 8, 0, 0),
            datetime(2014, 12, 6, 8, 0, 0),
            datetime(2014, 12, 7, 8, 0, 0),
            datetime(2014, 12, 8, 8, 0, 0),
            datetime(2014, 12, 9, 8, 0, 0),
        ]
        self.assertEqual(dates, expected)

    def test_schedule_first_date(self):
        self.assertEqual(schedule_first_date(None), None)
        self.assertEqual(schedule_first_date([]), None)

        schedule = [
            {
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            },
            {
                'duration': 4890,
                'rrule': ('DTSTART:20141104\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141105T235959'),
            }
        ]

        self.assertEqual(schedule_first_date(schedule), datetime(2014, 11, 4, 8, 0, 0))
        self.assertEqual(schedule_first_date(schedule, ""), datetime(2014, 11, 4, 8, 0, 0))
        self.assertEqual(schedule_first_date(schedule, "Europe/Paris"), datetime(2014, 11, 4, 7, 0, 0))
        self.assertEqual(schedule_first_date(schedule, None), datetime(2014, 11, 4, 8, 0, 0))

    def test_schedule_last_date(self):
        self.assertEqual(schedule_last_date(None), None)
        self.assertEqual(schedule_last_date([]), None)

        schedule = [
            {
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            },
            {
                'duration': 4890,
                'rrule': ('DTSTART:20141104\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141105T235959'),
            }
        ]

        self.assertEqual(schedule_last_date(schedule), datetime(2014, 12, 9, 17, 30, 0))
        self.assertEqual(schedule_last_date(schedule, ""), datetime(2014, 12, 9, 17, 30, 0))
        self.assertEqual(schedule_last_date(schedule, "Europe/Paris"), datetime(2014, 12, 9, 16, 30, 0))
        self.assertEqual(schedule_last_date(schedule, None), datetime(2014, 12, 9, 17, 30, 0))

    def test_schedule_next_date(self):
        self.assertEqual(schedule_next_date(None), None)
        self.assertEqual(schedule_next_date([]), None)

        schedule = [
            {
                'duration': 180,
                'rrule': ('DTSTART:20420801\nRRULE:FREQ=WEEKLY;BYDAY=SU;'
                    'BYHOUR=10;BYMINUTE=30;UNTIL=20420930'),
            }
        ]

        self.assertEqual(schedule_next_date(schedule), datetime(2042, 8, 3, 10, 30, 0))
        self.assertEqual(schedule_next_date(schedule, ""), datetime(2042, 8, 3, 10, 30, 0))
        self.assertEqual(schedule_next_date(schedule, "Europe/Paris"), datetime(2042, 8, 3, 9, 30, 0))
        self.assertEqual(schedule_next_date(schedule, None), datetime(2042, 8, 3, 10, 30, 0))


    def test_discretised_days_to_scheduletags(self):
        self.assertEqual(discretised_days_to_scheduletags([]), ['no_schedule'])

        dtlist = [datetime(2014, 11, 4, 8, 0, 0)];
        self.assertEqual(
            sorted(discretised_days_to_scheduletags(dtlist)),
            sorted(['2014-11-04_day_full', '2014-11-04_day', '2014_year_full', '2014_year_day'])
        )

        dtlist = [ datetime(2015, 1, 2, 21, 30, 0), ];
        self.assertEqual(
            sorted(discretised_days_to_scheduletags(dtlist)),
            sorted(['2015-01-02_day_full', '2015-01-02_night', '2015_year_full', '2015_year_night'])
        )

        dtlist = [ datetime(2014, 8, 17, 21, 30, 0), ];
        self.assertEqual(
            sorted(discretised_days_to_scheduletags(dtlist)),
            sorted([
                '2014-08-17_day_full',
                '2014-08-17_night',
                '2014-33_sunday_full',
                '2014-33_weekend_full',
                '2014-33_weekend_night',
                '2014_year_full',
                '2014_year_night',
            ])
        )

        dtlist = [ datetime(2014, 8, 17, 21, 30, 0), datetime(2014, 8, 16, 12, 30, 0), ];
        self.assertEqual(
            sorted(discretised_days_to_scheduletags(dtlist)),
            sorted([
                '2014-08-16_day_full',
                '2014-08-16_day',
                '2014-08-17_day_full',
                '2014-08-17_night',
                '2014-33_sunday_full',
                '2014-33_weekend_full',
                '2014-33_weekend_night',
                '2014-33_weekend_day',
                '2014_year_full',
                '2014_year_day',
                '2014_year_night',
            ])
        )

        dtlist = [
            datetime(2014, 11, 4, 20, 0, 0),
            datetime(2014, 11, 5, 20, 0, 0),
            datetime(2014, 12, 4, 8, 0, 0),
            datetime(2014, 12, 5, 8, 0, 0),
            datetime(2014, 12, 6, 8, 0, 0),
            datetime(2014, 12, 7, 8, 0, 0),
            datetime(2014, 12, 8, 8, 0, 0),
            datetime(2014, 12, 9, 8, 0, 0),
        ]

        self.assertEqual(
            sorted(discretised_days_to_scheduletags(dtlist)),
            sorted([
                '2014-11-04_day_full',
                '2014-11-05_day_full',
                '2014-12-04_day_full',
                '2014-12-05_day_full',
                '2014-12-06_day_full',
                '2014-12-07_day_full',
                '2014-12-08_day_full',
                '2014-12-09_day_full',
                '2014-11-04_night',
                '2014-11-05_night',
                '2014-12-04_day',
                '2014-12-05_day',
                '2014-12-06_day',
                '2014-12-07_day',
                '2014-12-08_day',
                '2014-12-09_day',
                '2014-49_sunday_full',
                '2014-49_weekend_full',
                '2014-49_weekend_day',
                '2014_year_full',
                '2014_year_day',
                '2014_year_night',
            ])
        )


@freeze_time("2018-01-14 20:00:01")
class SplitPastFutureTest(unittest.TestCase):

    def setUp(self):
        self._20180103_8h = {
            'duration': 0,
            'rrule': ('DTSTART:20180103\nRRULE:FREQ=DAILY;BYHOUR=8;'
                      'BYMINUTE=0;COUNT=1'),
        }

        self._20180114_15h = {
            'duration': 0,
            'rrule': ('DTSTART:20180114\nRRULE:FREQ=DAILY;BYHOUR=15;'
                      'BYMINUTE=0;COUNT=1'),
        }

        self._20180115_15h = {
            'duration': 0,
            'rrule': ('DTSTART:20180115\nRRULE:FREQ=DAILY;BYHOUR=15;'
                      'BYMINUTE=0;COUNT=1'),
        }

    def test_basic_split(self):
        schedule = [self._20180103_8h, self._20180114_15h, self._20180115_15h]

        past, future = split_past_and_future(schedule)

        self.assertListEqual([self._20180103_8h, self._20180114_15h], past)
        self.assertListEqual([self._20180115_15h], future)

    def test_keep_all_day(self):
        schedule = [self._20180103_8h, self._20180114_15h, self._20180115_15h]

        past, future = split_past_and_future(schedule, keep_all_day=True)

        self.assertListEqual([self._20180103_8h], past)
        self.assertListEqual([self._20180114_15h, self._20180115_15h], future)

    def test_reference_day(self):
        schedule = [self._20180103_8h, self._20180114_15h, self._20180115_15h]

        past, future = split_past_and_future(
            schedule, keep_all_day=True, reference_date=datetime(2018, 1, 16, 18, 0))

        self.assertListEqual([self._20180103_8h, self._20180114_15h, self._20180115_15h], past)
        self.assertListEqual([], future)


@freeze_time("2018-01-16 20:00:01")
class TerminateScheduleTest(unittest.TestCase):

    def test_terminate_schedule(self):
        schedule = [{
            'duration': 0,
            'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;BYDAY=SU;'
                      'BYHOUR=10;BYMINUTE=30'),
        }]

        expected_output = [{
            'duration': 0,
            'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;BYDAY=SU;'
                      'BYHOUR=10;BYMINUTE=30;UNTIL=20180116T235959'),
        }]

        flag, result = terminate_infinite_schedule(schedule, new_end=datetime.now())
        self.assertTrue(flag)
        self.assertListEqual(result, expected_output)

    def test_not_terminate_schedule_single_date(self):
        schedule = [{
            'duration': 0,
            'rrule': ('DTSTART:20180103\nRRULE:FREQ=DAILY;BYHOUR=8;'
                      'BYMINUTE=0;COUNT=1'),
        }]

        flag, result = terminate_infinite_schedule(schedule, new_end=datetime.now())
        self.assertFalse(flag)
        self.assertListEqual(result, schedule)

    def test_not_terminate_schedule_continuous(self):
        schedule = [{
            'duration': 0,
            'rrule': ('DTSTART:20180103\nRRULE:FREQ=DAILY;BYHOUR=8;'
                      'BYMINUTE=0;INTERVAL=1;UNTIL=20180116T235959'),
        }]

        flag, result = terminate_infinite_schedule(schedule, new_end=datetime.now())
        self.assertFalse(flag)
        self.assertListEqual(result, schedule)

    def test_not_terminate_schedule_bounded_recurring(self):
        schedule = [{
            'duration': 0,
            'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;BYDAY=SU;'
                      'BYHOUR=10;BYMINUTE=30;UNTIL=20180116T235959'),
        }]

        flag, result = terminate_infinite_schedule(schedule, new_end=datetime.now())
        self.assertFalse(flag)
        self.assertListEqual(result, schedule)
