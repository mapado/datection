# -*- coding: utf-8 -*-

import unittest

from datetime import datetime
from datection.models import DurationRRule
from datection.export import export_continuous_schedule
from datection.export import export_non_continuous_schedule
from datection.export import schedule_to_start_end_list


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
