# -*- coding: utf-8 -*-
"""
Test suite of the datection.cohesive
"""

import unittest
import datection

from datection.cohesion import cohesive_rrules


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
            'BYHOUR=14;BYMINUTE=0;UNTIL=20140325T000000'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertEqual(rr_res, res[0]['rrule'])

    def test_group_successive_dates(self):
        rrs = datection.to_db('1, 2 et 3 janvier 2016',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('4 et 5 janvier 2016',
                                   self.lang, only_future=False))

        rr_res = 'DTSTART:20160101T000000\nRRULE:FREQ=DAILY;' \
            'BYHOUR=0;BYMINUTE=0;UNTIL=20160105T235900'

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
            'BYHOUR=0;BYMINUTE=0;UNTIL=20160105T000000'

        res = cohesive_rrules(rrs)
        self.assertEqual(len(res), 1)
        self.assertEqual(rr_res, res[0]['rrule'])

    def test_avoid_group_when_time_exist_and_differ(self):
        rrs = datection.to_db('1, 2 et 3 janvier 2016 à 17h30',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('3 et 4 janvier 2016 à 18h',
                                   self.lang, only_future=False))

        res = cohesive_rrules(rrs)
        rr_res_1 = False
        rr_res_2 = False
        for dr in res:
            r = dr['rrule']
            if 'DTSTART:20160103T000000\nRRULE:FREQ=DAILY;' \
                    'BYHOUR=18;BYMINUTE=0;UNTIL=20160104T180000' == r:
                rr_res_1 = True
            if 'DTSTART:20160101T000000\nRRULE:FREQ=DAILY;' \
                    'BYHOUR=17;BYMINUTE=30;UNTIL=20160103T173000' == r:
                rr_res_2 = True

        self.assertEqual(len(res), 2)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)

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

        res = cohesive_rrules(rrs)

        rr_res_1 = False
        rr_res_2 = False
        rr_res_3 = False
        for dr in res:
            r = dr['rrule']
            if 'FREQ=WEEKLY;BYDAY=WE;BYHOUR=14;BYMINUTE=0;' in r:
                rr_res_1 = True
            if 'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=16;BYMINUTE=0;' in r:
                rr_res_2 = True
            if 'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;' in r:
                rr_res_3 = True

        self.assertEqual(len(res), 3)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)
        self.assertTrue(rr_res_3)

    def test_weekdays_not_concat_if_day_different_with_composition(self):
        rrs = datection.to_db('du 2 avril au 15 août',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('le lundi et mardi à 15h',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le mercredi à 16h',
                                   self.lang, only_future=False))

        res = cohesive_rrules(rrs)

        rr_res_1 = False
        rr_res_2 = False
        for dr in res:
            r = dr['rrule']
            if 'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;' in r:
                rr_res_1 = True
            if 'FREQ=WEEKLY;BYDAY=WE;BYHOUR=16;BYMINUTE=0;' in r:
                rr_res_2 = True
        self.assertEqual(len(res), 2)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)

    def test_multiple_unification_possible(self):
        rrs = datection.to_db('du 14 avril au 16 juin 2020 ',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('le mercredi à 14h',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le lundi et mardi à 15h',
                                   self.lang, only_future=False))
        res = cohesive_rrules(rrs)
        rr_res_1 = False
        rr_res_2 = False
        for dr in res:
            r = dr['rrule']
            if ('DTSTART:20200414T000000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                    'BYHOUR=15;BYMINUTE=0;UNTIL=20200616T000000' in r):
                rr_res_1 = True
            if ('DTSTART:20200414T000000\nRRULE:FREQ=WEEKLY;BYDAY=WE;'
                    'BYHOUR=14;BYMINUTE=0;UNTIL=20200616T000000' in r):
                rr_res_2 = True
        self.assertEqual(len(res), 2)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)

    def test_union_followed_by_composition(self):
        rrs = datection.to_db('du 14 avril au 16 juin 2020 ',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('du 5 juin au 9 juin 2020 ',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le mercredi à 14h',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le lundi et mardi à 15h',
                                   self.lang, only_future=False))
        res = cohesive_rrules(rrs)
        rr_res_1 = False
        rr_res_2 = False
        for dr in res:
            r = dr['rrule']
            if '20200414T000000\nRRULE:FREQ=WEEKLY;BYDAY=WE;' \
                    'BYHOUR=14;BYMINUTE=0;UNTIL=20200616' in r:
                rr_res_1 = True
            if '20200414T000000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;' \
                    'BYHOUR=15;BYMINUTE=0;UNTIL=20200616' in r:
                rr_res_2 = True

        self.assertEqual(len(res), 2)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)

    def test_avoid_ambiguous_composition(self):
        rrs = datection.to_db('du 14 avril au 16 juin 2020 ',
                              self.lang, only_future=False)
        rrs.extend(datection.to_db('du 14 juillet au 9 août 2020 ',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le mercredi à 14h',
                                   self.lang, only_future=False))
        rrs.extend(datection.to_db('le lundi et mardi à 15h',
                                   self.lang, only_future=False))
        res = cohesive_rrules(rrs)
        rr_res_1 = False
        rr_res_2 = False
        rr_res_3 = False
        rr_res_4 = False
        for dr in res:
            r = dr['rrule']
            if 'RRULE:FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;' in r:
                rr_res_1 = True
            elif 'RRULE:FREQ=WEEKLY;BYDAY=WE;BYHOUR=14;BYMINUTE=0;' in r:
                rr_res_2 = True
            elif 'DTSTART:20200714T000000\nRRULE:FREQ=DAILY;' \
                    'BYHOUR=0;BYMINUTE=0;UNTIL=20200809T000000' in r:
                rr_res_3 = True
            elif 'DTSTART:20200414T000000\nRRULE:FREQ=DAILY;' \
                    'BYHOUR=0;BYMINUTE=0;UNTIL=20200616T000000' in r:
                rr_res_4 = True
        self.assertEqual(len(res), 4)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)
        self.assertTrue(rr_res_3)
        self.assertTrue(rr_res_4)

    def test_real_case_1(self):
        rrs = datection.to_db("""
            Le dimanche
            Le lundi
            Du 5 février 2014 au 5 février 2015 à 20 h
            Du 16 au 26 avril 2014
        """, self.lang, only_future=False)
        res = cohesive_rrules(rrs)
        import ipdb
        ipdb.set_trace()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['rrule'], 'DTSTART:20140416T000000\n'
                         'RRULE:FREQ=WEEKLY;BYDAY=MO,SU;BYHOUR=20;'
                         'BYMINUTE=0;UNTIL=20140426T000000')

    def test_real_case_2(self):
        rrs = datection.to_db("""
            Du jeudi au samedi, à 19 h 30
            Du jeudi au samedi, à 21 h 30
            Du jeudi au samedi
            Du 2 janvier au 1er mars 2014
        """, self.lang, only_future=False)
        res = cohesive_rrules(rrs)

        rr_res_1 = False
        rr_res_2 = False

        for dr in res:
            r = dr['rrule']
            if ('DTSTART:20140102T000000\nRRULE:FREQ=WEEKLY;BYDAY=TH,FR,SA;'
                    'BYHOUR=21;BYMINUTE=30;UNTIL=20140301T235959' in r):
                rr_res_1 = True
            elif ('DTSTART:20140102T000000\nRRULE:FREQ=WEEKLY;BYDAY=TH,FR,SA;'
                    'BYHOUR=19;BYMINUTE=30;UNTIL=20140301T235959' in r):
                rr_res_2 = True

        self.assertEqual(len(res), 2)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)

    def test_real_case_3(self):

        rrs = datection.to_db("""
            Le jeudi, à 20 h 30
            Le jeudi, du 13 janvier au 28 février 2014, de 20 h à 21 h 15
            Du 12 septembre au 19 décembre 2013,
            13 février 2014, 20 février 2014,
            27 février 2014, 6 mars 2014,
            13 mars 2014, 20 mars 2014, 27 mars 2014 à 20 h
            Du 3 au 28 juillet 2013, du 12 septembre au 19 décembre 2013,
            7 novembre 2015, 5 décembre 2015
            Le 28 juillet 2013 à 13 h
        """, self.lang, only_future=False)
        res = cohesive_rrules(rrs)

        rr_res_1 = False
        rr_res_2 = False
        rr_res_3 = False
        rr_res_4 = False
        rr_res_5 = False
        rr_res_6 = False

        for dr in res:
            r = dr['rrule']
            if '20151205T000000\nRRULE:FREQ=DAILY;COUNT=1;' in r:
                rr_res_1 = True
            elif '20130703T000000\nRRULE:FREQ=DAILY;' \
                    'BYHOUR=13;BYMINUTE=0;UNTIL=20130728' in r:
                rr_res_2 = True
            elif '20140113T000000\nRRULE:FREQ=WEEKLY;BYDAY=TH;' \
                    'BYHOUR=20;BYMINUTE=0;UNTIL=20140327' in r:
                rr_res_3 = True
            elif 'FREQ=WEEKLY;BYDAY=TH;BYHOUR=20;BYMINUTE=30;' in r:
                rr_res_4 = True
            elif '20130912T000000\nRRULE:FREQ=DAILY;' \
                    'BYHOUR=0;BYMINUTE=0;UNTIL=20131219' in r:
                rr_res_5 = True
            elif '20151107T000000\nRRULE:FREQ=DAILY;COUNT=1;' in r:
                rr_res_6 = True

        self.assertEqual(len(res), 6)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)
        self.assertTrue(rr_res_3)
        self.assertTrue(rr_res_4)
        self.assertTrue(rr_res_5)
        self.assertTrue(rr_res_6)

    def test_real_case_4(self):
        rrs = datection.to_db("""
            Du 8 septembre au 3 novembre 2013,
            du 3 novembre au 8 décembre 2013,
            du 8 au 22 décembre 2013,
            du 22 au 29 décembre 2013,
            29 décembre 2013 à 17 h
            Le 1er mars 2014,
            du 1er au 8 mars 2014,
            du 8 au 15 mars 2014,
            du 15 au 22 mars 2014,
            du 22 au 29 mars 2014,
            du 29 mars au 5 avril 2014,
            du 5 au 12 avril 2014,
            du 12 au 19 avril 2014,
            du 19 au 26 avril 2014,
            du 26 avril au 3 mai 2014,
            du 3 au 10 mai 2014,
            du 10 au 17 mai 2014,
            17 mai 2014 à 18 h
        """, self.lang, only_future=False)
        res = cohesive_rrules(rrs)
        rr_res_1 = False
        rr_res_2 = False
        for dr in res:
            r = dr['rrule']
            if '20140301T000000\nRRULE:FREQ=DAILY;BYHOUR=18;' \
               'BYMINUTE=0;UNTIL=20140517' in r:
                rr_res_1 = True
            elif '20130908T000000\nRRULE:FREQ=DAILY;BYHOUR=17;' \
                    'BYMINUTE=0;UNTIL=20131229' in r:
                rr_res_2 = True
        self.assertEqual(len(res), 2)
        self.assertTrue(rr_res_1)
        self.assertTrue(rr_res_2)
