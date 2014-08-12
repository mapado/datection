# -*- coding: utf-8 -*-

import unittest

from datetime import datetime
from datection.models import DurationRRule
from datection.export import export_continuous_schedule
from datection.export import export_non_continuous_schedule
from datection.export import schedule_to_start_end_list
from datection.export import schedule_to_discretised_days
from datection.export import schedule_first_date
from datection.export import schedule_last_date
from datection.export import discretised_days_to_scheduletags


class ExportScheduleToSQLTest(unittest.TestCase):

    """Test the rrule --> SQL schedule conversion utilities."""

    def test_export_non_continuous_schedule(self):
        """Check the result of a future non continuous schedule export."""
        start = datetime(2014, 1, 1, 0, 0)
        end = datetime(2015, 1, 1, 0, 0)
        schedule = [
            {
                'duration': 570,
                # future with respect to start/end
                'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20140308T235959'),
                'texts': [u'Du 5 au 8 mars 2014, de 8h \xe0 17h30']
            }
        ]
        schedule = DurationRRule(schedule[0])
        export = export_non_continuous_schedule(schedule, start, end)
        expected = [
            (datetime(2014, 3, 5, 8, 0), datetime(2014, 3, 5, 17, 30)),
            (datetime(2014, 3, 6, 8, 0), datetime(2014, 3, 6, 17, 30)),
            (datetime(2014, 3, 7, 8, 0), datetime(2014, 3, 7, 17, 30)),
            (datetime(2014, 3, 8, 8, 0), datetime(2014, 3, 8, 17, 30)),
        ]
        self.assertEqual(export, expected)

    def test_export_past_non_continuous_schedule(self):
        """Check the result of a past non continuous schedule export."""
        start = datetime(2014, 1, 1, 0, 0)
        end = datetime(2015, 1, 1, 0, 0)
        schedule = [
            {
                'duration': 570,
                # past with respect to start/end
                'rrule': ('DTSTART:20120305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20120308T235959'),
                'texts': [u'Du 5 au 8 mars 2014, de 8h \xe0 17h30']
            }
        ]
        schedule = DurationRRule(schedule[0])
        export = export_non_continuous_schedule(schedule, start, end)
        self.assertEqual(export, [])

    def test_export_continuous_schedule(self):
        """Check the result of a future continuous schedule export."""
        start = datetime(2014, 1, 1, 0, 0)
        end = datetime(2015, 1, 1, 0, 0)
        schedule = [
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20140308T235959'),
                'texts': [u' 5 mars \xe0 8h au 8 mars \xe0 17h30']
            }
        ]
        schedule = DurationRRule(schedule[0])
        export = export_continuous_schedule(schedule, start, end)
        expected = [
            (datetime(2014, 3, 5, 8, 0), datetime(2014, 3, 5, 23, 59)),
            (datetime(2014, 3, 6, 0, 0), datetime(2014, 3, 6, 23, 59)),
            (datetime(2014, 3, 7, 0, 0), datetime(2014, 3, 7, 23, 59)),
            (datetime(2014, 3, 8, 0, 0), datetime(2014, 3, 8, 17, 30)),
        ]
        self.assertEqual(export, expected)

    def test_export_past_continuous_schedule(self):
        """Check the result of a past continuous schedule export."""
        start = datetime(2014, 1, 1, 0, 0)
        end = datetime(2015, 1, 1, 0, 0)
        schedule = [
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20130305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20130308T235959'),
                'texts': [u' 5 mars \xe0 8h au 8 mars \xe0 17h30']
            }
        ]
        schedule = DurationRRule(schedule[0])
        export = export_continuous_schedule(schedule, start, end)
        self.assertEqual(export, [])

    def test_export_schedule_to_start_end_list(self):
        schedule = [
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            }
        ]
        start = datetime(2014, 12, 3, 0, 0)
        end = datetime(2014, 12, 15, 0, 0)
        sch = schedule_to_start_end_list(schedule, start, end)
        self.assertEqual(sch[0]['start'], datetime(2014, 12, 4, 8, 0))
        self.assertEqual(sch[0]['end'],   datetime(2014, 12, 4, 23, 59))
        self.assertEqual(sch[1]['start'], datetime(2014, 12, 5, 0, 0))
        self.assertEqual(sch[1]['end'],   datetime(2014, 12, 5, 23, 59))
        self.assertEqual(sch[2]['start'], datetime(2014, 12, 6, 0, 0))
        self.assertEqual(sch[2]['end'],   datetime(2014, 12, 6, 23, 59))
        self.assertEqual(sch[3]['start'], datetime(2014, 12, 7, 0, 0))
        self.assertEqual(sch[3]['end'],   datetime(2014, 12, 7, 23, 59))
        self.assertEqual(sch[4]['start'], datetime(2014, 12, 8, 0, 0))
        self.assertEqual(sch[4]['end'],   datetime(2014, 12, 8, 23, 59))
        self.assertEqual(sch[5]['start'], datetime(2014, 12, 9, 0, 0))
        self.assertEqual(sch[5]['end'],   datetime(2014, 12, 9, 17, 30))

    def test_export_schedule_to_start_end_list_future(self):
        schedule = [
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            }
        ]
        start = datetime(2014, 11, 3, 0, 0)
        end = datetime(2014, 11, 15, 0, 0)
        sch = schedule_to_start_end_list(schedule, start, end)
        self.assertEqual(sch, [])

    def test_export_schedule_to_start_end_list_past(self):
        schedule = [
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            }
        ]
        start = datetime(2014, 12, 10, 0, 0)
        end = datetime(2014, 12, 15, 0, 0)
        sch = schedule_to_start_end_list(schedule, start, end)
        self.assertEqual(sch, [])

    def test_schedule_to_discretised_days(self):
        schedule = [
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141104\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141105T235959'),
            },
            {
                'continuous': True,
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
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            },
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141104\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141105T235959'),
            }
        ]

        first_date = schedule_first_date(schedule)

        self.assertEqual(first_date, datetime(2014, 11, 4, 8, 0, 0))

    def test_schedule_last_date(self):
        self.assertEqual(schedule_last_date(None), None)
        self.assertEqual(schedule_last_date([]), None)

        schedule = [
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141204\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141209T235959'),
            },
            {
                'continuous': True,
                'duration': 4890,
                'rrule': ('DTSTART:20141104\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141105T235959'),
            }
        ]

        last_date = schedule_last_date(schedule)

        self.assertEqual(last_date, datetime(2014, 12, 9, 17, 30, 0))

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
                '2014-32_weekend_full',
                '2014-32_weekend_night',
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
                '2014-32_weekend_full',
                '2014-32_weekend_night',
                '2014-32_weekend_day',
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
                '2014-48_weekend_full',
                '2014-48_weekend_day',
                '2014_year_full',
                '2014_year_day',
                '2014_year_night',
            ])
        )
