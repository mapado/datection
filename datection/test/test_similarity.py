# -*- coding: utf-8 -*-

"""
Test suite of the similarity module
"""

from __future__ import division

import unittest

from datection.similarity import *
from dateutil.rrule import rrulestr


class UtilsTest(unittest.TestCase):
    def test_jaccard_distance(self):
        s1 = set([0, 1, 2, 3])
        s2 = set([0, 1, 2, 4])

        self.assertEqual(jaccard_distance(s1, s2), 3/5)
        self.assertEqual(jaccard_distance(s1, s1), 1)


class WeekdayRRuleSimilarityTest(unittest.TestCase):
    """Test similarity score calculation bewteen weekday recurrences"""
    def setUp(self):
        self.rrule_struct1 = {
            'duration': 180,
            'rrule': ('DTSTART:20130806\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE;'
                'BYHOUR=5;BYMINUTE=0;UNTIL=20130826')
            }
        self.rrule1 = rrulestr(self.rrule_struct1['rrule'])
        self.rrule_struct2 = {
            'duration': 600,
            'rrule': ('DTSTART:20130806\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,FR;'
                'BYHOUR=4;BYMINUTE=0;UNTIL=20130816')
            }
        self.rrule2 = rrulestr(self.rrule_struct2['rrule'])

    def test_weekday_similarity(self):
        self.assertEqual(weekday_similarity(self.rrule1, self.rrule2), 2/4)
        self.assertEqual(weekday_similarity(self.rrule1, self.rrule1), 1)

    def test_duration_similarity(self):
        self.assertEqual(duration_similarity(self.rrule1, self.rrule2), 11/21)
        self.assertEqual(duration_similarity(self.rrule1, self.rrule1), 1)

    def test_schedule_similarity(self):
        self.assertEqual(
            schedule_similarity(self.rrule_struct1, self.rrule_struct2), 6/18)
        self.assertEqual(
            schedule_similarity(self.rrule_struct1, self.rrule_struct1), 1)

    def test_rrule_similarity(self):
        avg = (2/4 + 11/21 + 6/18) / 3
        self.assertEqual(
            round(rrule_similarity(self.rrule_struct1, self.rrule_struct2), 9),
            round(avg, 9))
        self.assertEqual(
            similarity(self.rrule_struct1, self.rrule_struct1), 1)

    def test_similarity_with_recurrences(self):
        avg = (2/4 + 11/21 + 6/18) / 3
        self.assertEqual(
            round(similarity(self.rrule_struct1, self.rrule_struct2), 9),
            round(avg, 9))
        self.assertEqual(
            similarity(self.rrule_struct1, self.rrule_struct1), 1)


class TimepointRRuleSimilarityTest(unittest.TestCase):
    """Test similarity score calculation bewteen timepoints"""
    def setUp(self):
        self.rrule_struct1 = {
            'duration': 0,
            'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;COUNT=1;'
                'BYMINUTE=30;BYHOUR=20')
        }
        self.rrule1 = rrulestr(self.rrule_struct1['rrule'])
        self.rrule_struct2 = {
            'duration': 0,
            'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;COUNT=1;'
                'BYMINUTE=30;BYHOUR=21')
        }
        self.rrule2 = rrulestr(self.rrule_struct2['rrule'])

    def test_duration_similarity(self):
        self.assertEqual(duration_similarity(self.rrule1, self.rrule2), 1)
        self.assertEqual(duration_similarity(self.rrule1, self.rrule1), 1)

    def test_schedule_similarity(self):
        self.assertEqual(
            schedule_similarity(self.rrule_struct1, self.rrule_struct2), 0)
        self.assertEqual(
            schedule_similarity(self.rrule_struct1, self.rrule_struct1), 1)

    def test_similarity_with_recurrences(self):
        avg = (1 + 0) / 2
        self.assertEqual(
            round(similarity(self.rrule_struct1, self.rrule_struct2), 9),
            round(avg, 9))
        self.assertEqual(
            similarity(self.rrule_struct1, self.rrule_struct1), 1)


class VariousRRuleSimilarityTest(unittest.TestCase):

    def setUp(self):
        self.rrule_struct1 = {
                'duration': 0,
                'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;COUNT=1;'
                    'BYMINUTE=30;BYHOUR=20')
            }
        self.rrule_struct2 = {
                'duration': 600,
                'rrule': ('DTSTART:20130806\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,FR;'
                    'BYHOUR=4;BYMINUTE=0;UNTIL=20130816')
            }

    def tets_similarity(self):
        with self.assertRaises(ValueError):
            similarity(self.rrule_struct1, self.rrule_struct2)