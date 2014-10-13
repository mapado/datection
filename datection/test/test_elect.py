# -*- coding: utf-8 -*-

"""
Test suite of the datection.elect module
"""

import unittest

from datetime import datetime
from datection.elect import best_schedule
from datection.elect import common_elements
from datection.similarity import discretise_schedule


class TestScheduleElection(unittest.TestCase):

    """Test suite of the functions responsible of the 'election' of the
    best schedule among a list of inter-similar schedules.

    """

    def setUp(self):
        schedule1 = [
            {
                'duration': 1439,
                'rrule': ('DTSTART:20140305\nRRULE:FREQ=WEEKLY;'
                          'BYDAY=MO,TU,WE,TH,FR,SA,SU;UNTIL=20140320T235959'),
            }]

        schedule2 = [
            {
                'duration': 120,
                'rrule': ('DTSTART:20140305\nRRULE:FREQ=WEEKLY;BYHOUR=8;'
                          'BYMINUTE=0;BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                          'UNTIL=20140320T235959'),
            }]
        schedule3 = [
            {
                'duration': 120,
                'rrule': ('DTSTART:20140305\nRRULE:FREQ=WEEKLY;BYHOUR=8;'
                          'BYMINUTE=0;BYDAY=MO;UNTIL=20140320T235959'),
            }]
        self.schedules = [schedule1, schedule2, schedule3]

    def test_common_elements(self):
        """Check the calculation of the common datetimes bewteen all
        discrete schedules.

        """
        # discretise the schedules in 30 minute intervals
        discrete = [discretise_schedule(schedule, grain_level="min", grain_quantity=30)
                    for schedule in self.schedules]
        expected = set([
            datetime(2014, 3, 10, 8, 0),
            datetime(2014, 3, 10, 8, 30),
            datetime(2014, 3, 10, 9, 0),
            datetime(2014, 3, 10, 9, 30),
            datetime(2014, 3, 10, 10, 0),
            datetime(2014, 3, 17, 8, 0),
            datetime(2014, 3, 17, 8, 30),
            datetime(2014, 3, 17, 9, 0),
            datetime(2014, 3, 17, 9, 30),
            datetime(2014, 3, 17, 10, 0),
        ])
        self.assertEqual(common_elements(discrete), expected)

    def test_best_schedule(self):
        """Check that the chosen schedule is the most precise one."""
        self.assertEqual(best_schedule(self.schedules), self.schedules[2])

    def test_best_schedule_with_outlier(self):
        """Check what happens when a full outlier is found among the schedules.

        """
        schedules = self.schedules[:]
        schedules.append([
            {
                'duration': 1439,
                'rrule': ('DTSTART:20140408\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=0'),
            }
        ])
        self.assertIsNone(best_schedule(schedules))
