# -*- coding: utf-8 -*-

"""
Test suite of the datection.cohesive
"""

import unittest

import datection
from datection.models import DurationRRule
from datection.cohesive import cohesive_rrules


class TestMoreCohesive(unittest.TestCase):

    """Test suite of the functions responsible of a more cohesive and human
    readable list of date.
    """

    def setUp(self):
        self.lang = 'fr'

    def test_days_recurrence_in_lapse_time(self):
        rrs = datection.to_db('du 21 au 30 mars 2014',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('le lundi et mardi à 14h',
                                   self.lang, only_future=False))

        expected_rr_res = 'DTSTART:20140321T000000\nRRULE:FREQ=WEEKLY;' \
            'BYDAY=MO,TU;BYHOUR=14;BYMINUTE=0;UNTIL=20140330T000000'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertEqual(expected_rr_res, res[0]['rrule'])
        self.assertEqual(0, res[0]['duration'])

    def test_precise_time_in_a_date(self):
        rrs = datection.to_db('le 21 mars 2014',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('le 21 mars 2014 à 14h',
                                   self.lang, only_future=False))

        rr_res = 'DTSTART:20140321T000000\nRRULE:FREQ=DAILY;' \
            'COUNT=1;BYHOUR=14;BYMINUTE=0'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertEqual(rr_res, res[0]['rrule'])

    def test_precise_time_in_a_lapse_time(self):
        rrs = datection.to_db('du 18 au 25 mars 2014',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('le 21 mars 2014 à 14h',
                                   self.lang, only_future=False))

        rr_res = 'DTSTART:20140318T000000\nRRULE:FREQ=DAILY;' \
            'COUNT=1;BYHOUR=14;BYMINUTE=0;UNTIL=20140325T140000'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertEqual(rr_res, res[0]['rrule'])

    def test_group_successive_dates(self):
        rrs = datection.to_db('1, 2 et 3 janvier 2016',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('4 et 5 janvier 2016',
                                   self.lang, only_future=False))

        rr_res = 'DTSTART:20160101T000000\nRRULE:FREQ=DAILY;' \
            'BYHOUR=0;BYMINUTE=0;UNTIL=20160105T000000'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertEqual(rr_res, res[0]['rrule'])

    def test_avoid_doubles_date(self):
        rrs = datection.to_db('1, 2 et 3 janvier 2016',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('3 et 4 janvier 2016',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('1 au 5 janvier 2016',
                                   self.lang, only_future=False))

        rr_res = 'DTSTART:20160101T000000\nRRULE:FREQ=DAILY;' \
            'BYHOUR=0;BYMINUTE=0;UNTIL=20160105T235900'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertEqual(rr_res, res[0]['rrule'])

    def test_avoid_group_when_time_exist_and_differ(self):
        rrs = datection.to_db('1, 2 et 3 janvier 2016 à 17h30',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('3 et 4 janvier 2016 à 18h',
                                   self.lang, only_future=False))

        rr_res_1 = 'DTSTART:20160103T000000\nRRULE:FREQ=DAILY;' \
            'BYHOUR=18;BYMINUTE=0;UNTIL=20160104T180000'
        rr_res_2 = 'DTSTART:20160101T000000\nRRULE:FREQ=DAILY;' \
            'BYHOUR=17;BYMINUTE=30;UNTIL=20160103T173000'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 2)
        self.assertEqual(rr_res_1, res[0]['rrule'])
        self.assertEqual(rr_res_2, res[1]['rrule'])

    def test_weekdays_concat(self):
        rrs = datection.to_db('le mercredi à 14h',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('le lundi et mardi à 14h',
                                   self.lang, only_future=False))

        rr_res = 'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE;BYHOUR=14;BYMINUTE=0;'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertIn(rr_res, res[0]['rrule'])

    def test_weekdays_not_concat_if_time_different(self):
        rrs = datection.to_db('le mercredi à 14h',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('le lundi et mardi à 15h',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le lundi et mardi à 16h',
                                   self.lang, only_future=False))

        rr_res_1 = 'FREQ=WEEKLY;BYDAY=WE;BYHOUR=14;BYMINUTE=0;'
        rr_res_2 = 'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=16;BYMINUTE=0;'
        rr_res_3 = 'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 3)
        self.assertIn(rr_res_1, res[0]['rrule'])
        self.assertIn(rr_res_2, res[1]['rrule'])
        self.assertIn(rr_res_3, res[2]['rrule'])

    def test_multiple_unification_possible(self):
        rrs = datection.to_db('du 14 avril au 16 juin 2020 ',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('du 10 au 24 janvier  2015 ',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le mercredi à 14h',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le lundi et mardi à 15h',
                                   self.lang, only_future=False))
        res = cohesive_rrules(rrs)
        rrr = datection.display(res, "fr")
