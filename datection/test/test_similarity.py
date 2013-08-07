# -*- coding: utf-8 -*-

"""
Test suite of the similarity module
"""

from __future__ import division

import unittest

from datection.similarity import *
from dateutil.rrule import rrulestr
from datetime import time, date

class UtilsTest(unittest.TestCase):
    """Test utility functions of the similarity module"""
    def test_jaccard_distance(self):
        s1 = set([0, 1, 2, 3])
        s2 = set([0, 1, 2, 4])

        self.assertEqual(jaccard_distance(s1, s2), 3/5)
        self.assertEqual(jaccard_distance(s1, s1), 1)

    def test_discretise_day_interval(self):
        rrule = rrulestr(('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
            'BYHOUR=15;BYMINUTE=30;UNTIL=20130810'))
        self.assertEqual(len(discretise_day_interval(rrule)), 4)
        self.assertEqual(discretise_day_interval(rrule)[1], date(2013, 8, 8))

    def test_discretise_time_slot(self):
        struct  = {
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
            'BYHOUR=15;BYMINUTE=30;UNTIL=20130810'),
            'duration': 180
        }
        self.assertEqual(len(discretise_time_slot(struct)), 7)
        self.assertEqual(discretise_time_slot(struct)[1], time(16, 0))


class AttributeCombiationTest(unittest.TestCase):
    """Test the combination of several rrules"""
    def setUp(self):
        self.schedule = [{
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,'
                    'WE,TH,FR;BYHOUR=15;BYMINUTE=30;UNTIL=20130827')
            },
            {
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=SA;'
                    'BYHOUR=15;BYMINUTE=30;UNTIL=20130913')
            }
        ]

    def test_combine_weekdays(self):
        self.assertEqual(combine_weekdays(self.schedule), set(range(6)))

    def test_combine_duration(self):
        self.assertEqual(len(combine_duration(self.schedule)), 38)

    def test_combine_duration_no_overlap(self):
        no_overlap  = [
            {
                'duration': 0,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,'
                    'WE,TH,FR;BYHOUR=15;BYMINUTE=30;UNTIL=20130810')
            },
            {
                'duration': 0,
                'rrule': ('DTSTART:20130907\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,'
                    'WE,TH,FR;BYHOUR=15;BYMINUTE=30;UNTIL=20130910')
            }
        ]
        self.assertEqual(
            len(combine_duration(no_overlap)), 8)

    def test_combine_time_interval(self):
        self.assertEqual(len(combine_schedule(self.schedule)), 3)

    def test_combine_time_interval_no_overlap(self):
        no_overlap  = [
            {
                'duration': 0,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,'
                    'WE,TH,FR;BYHOUR=15;BYMINUTE=30;UNTIL=20130810')
            },
            {
                'duration': 0,
                'rrule': ('DTSTART:20130907\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,'
                    'WE,TH,FR;BYHOUR=15;BYMINUTE=30;UNTIL=20130910')
            }
        ]
        self.assertEqual(
            len(combine_schedule(no_overlap)), 1)



class WeekdayRRuleSimilarityTest(unittest.TestCase):
    """Test similarity score calculation bewteen weekday recurrences"""
    def setUp(self):
        self.schedule1 = [{
            'duration': 180,
            'rrule': ('DTSTART:20130806\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE;'
                'BYHOUR=5;BYMINUTE=0;UNTIL=20130826')
            }]
        self.schedule2 = [{
            'duration': 600,
            'rrule': ('DTSTART:20130806\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,FR;'
                'BYHOUR=4;BYMINUTE=0;UNTIL=20130816')
            }]

    def test_weekday_similarity(self):
        weekday_set1 = combine_weekdays(self.schedule1)
        weekday_set2 = combine_weekdays(self.schedule2)
        self.assertEqual(weekday_similarity(weekday_set1, weekday_set2), 2/4)
        self.assertEqual(weekday_similarity(weekday_set1, weekday_set1), 1)

    def test_duration_similarity(self):
        day_set1 = combine_duration(self.schedule1)
        day_set2 = combine_duration(self.schedule2)
        self.assertEqual(duration_similarity(day_set1, day_set2), 11/21)
        self.assertEqual(duration_similarity(day_set1, day_set1), 1)

    def test_schedule_similarity(self):
        time_slots_set1 = combine_schedule(self.schedule1)
        time_slots_set2 = combine_schedule(self.schedule2)
        self.assertEqual(
            schedule_similarity(time_slots_set1, time_slots_set2), 6/18)
        self.assertEqual(
            schedule_similarity(time_slots_set1, time_slots_set1), 1)

    def test_rrule_similarity(self):
        avg = (2/4 + 11/21 + 6/18) / 3
        self.assertEqual(
            round(similarity(self.schedule1, self.schedule2), 9),
            round(avg, 9))
        self.assertEqual(
            similarity(self.schedule1, self.schedule1), 1)
