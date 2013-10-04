# -*- coding: utf-8 -*-

"""
Test suite of the similarity module
"""

from __future__ import division

import unittest

from ..similarity import jaccard_distance, discretise_day_interval, \
    discretise_schedule, similarity
from datetime import datetime


class ScheduleSimilarityTest(unittest.TestCase):

    def test_jaccard_distance_no_intersection(self):
        set1 = set((1, 2, 3))
        set2 = set((4, 5, 6))
        self.assertEqual(jaccard_distance(set1, set2), 0)

    def test_jaccard_distance_some_intersection(self):
        set1 = set((1, 2, 3))
        set2 = set((3, 4, 5))
        # |⋃| / |⋂|  = 1 / 5 = 0.2
        self.assertEqual(jaccard_distance(set1, set2), 0.2)

    def test_jaccard_distance_total_intersection(self):
        set1 = set((1, 2, 3))
        set2 = set((1, 2, 3))
        # |⋃| / |⋂|  = 3 / 3 = 1
        self.assertEqual(jaccard_distance(set1, set2), 1)

    def test_discretise_single_schedule(self):
        schedule = [
            {
                'rrule': ('DTSTART:20140205\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60,
            }
        ]
        expected = [
            datetime(2014, 2, 5, 8, 0, 0),
            datetime(2014, 2, 5, 8, 30, 0),
            datetime(2014, 2, 5, 9, 0, 0),
        ]
        self.assertItemsEqual(discretise_schedule(schedule), expected)

    def test_discretise_several_schedules(self):
        schedule = [
            {
                'rrule': ('DTSTART:20140205\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60,
            },
            {
                'rrule': ('DTSTART:20140206\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60,
            }
        ]
        expected = [
            datetime(2014, 2, 5, 8, 0, 0),
            datetime(2014, 2, 5, 8, 30, 0),
            datetime(2014, 2, 5, 9, 0, 0),
            datetime(2014, 2, 6, 8, 0, 0),
            datetime(2014, 2, 6, 8, 30, 0),
            datetime(2014, 2, 6, 9, 0, 0),
        ]
        self.assertItemsEqual(discretise_schedule(schedule), expected)

    def test_discretise_day_interval(self):
        start = datetime(2014, 2, 5, 8, 0, 0)
        end = datetime(2014, 2, 5, 9, 0, 0)
        expected = [
            datetime(2014, 2, 5, 8, 0, 0),
            datetime(2014, 2, 5, 8, 30, 0),
            datetime(2014, 2, 5, 9, 0, 0),
        ]
        self.assertItemsEqual(discretise_day_interval(start, end), expected)

    def test_similarity_no_overlap(self):
        schedule1 = [
            {
                'rrule': ('DTSTART:20140205\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60,
            }
        ]
        schedule2 = [
            {
                'rrule': ('DTSTART:20140206\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60,
            }
        ]
        self.assertEqual(similarity(schedule1, schedule2), 0)

    def test_similarity_some_overlap(self):
        schedule1 = [
            {
                'rrule': ('DTSTART:20140205\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60,
            }
        ]
        schedule2 = [
            {
                'rrule': ('DTSTART:20140205\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 120,
            }
        ]
        self.assertEqual(similarity(schedule1, schedule2), 0.6)

    def test_similarity_total_overlap(self):
        schedule1 = [
            {
                'rrule': ('DTSTART:20140205\nRRULE:FREQ=DAILY;COUNT=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60,
            }
        ]
        self.assertEqual(similarity(schedule1, schedule1), 1.0)
