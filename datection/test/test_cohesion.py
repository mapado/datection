# -*- coding: utf-8 -*-
"""
Test suite of the datection.cohesive
"""
import unittest
import datection
from datetime import datetime
from datetime import timedelta
from datection.cohesion import cohesive_rrules


def gen_cohesive(mystr):
    return cohesive_rrules(datection.export(mystr, 'fr', only_future=False))


class TestMoreCohesive(unittest.TestCase):

    """Test suite of functions responsible of a duration rrrule minifier

    That build more cohesive and human readable date sentences.

    """

    def list_has_item_containing(self, items, contains):
        """ Check each rrule fragments string in :contains: is in :items: """
        self.assertEqual(len(items), len(contains))
        is_validated_contains = [False for it in contains]
        for drr in items:
            for idx, cont in enumerate(contains):
                if cont in drr['rrule']:
                    is_validated_contains[idx] = True
        for cont in is_validated_contains:
            self.assertTrue(cont)

    def test_days_recurrence_in_lapse_time(self):
        res = gen_cohesive(u"""
            du 21 au 30 mars 2014,
            le lundi et mardi à 14h
        """)
        # wanted result
        # Le lundi et mardi, du 21 au 30 mars 2014, à 14 h
        self.list_has_item_containing(res, [
            'DTSTART:20140321T140000\nRRULE:FREQ=WEEKLY;BYDAY=MO,'
            'TU;BYHOUR=14;BYMINUTE=0;UNTIL=20140330T140000',
        ])
        self.assertEqual(0, res[0]['duration'])

    def test_precise_time_in_a_date(self):
        res = gen_cohesive(u"""
            le 21 mars 2014,
            le 21 mars 2014 à 14h
        """)
        # wanted result
        # Le 21 mars 2014 à 14 h
        self.list_has_item_containing(res, [
            ('DTSTART:20140321T140000\nRRULE:FREQ=DAILY;COUNT=1;'
                'BYHOUR=14;BYMINUTE=0')
        ])

    def test_precise_time_in_a_lapse_time(self):
        res = gen_cohesive(u"""
            du 18 au 25 mars 2014,
            le 21 mars 2014 à 14h
        """)
        # wanted result
        # Du 18 au 25 mars 2014 à 14 h

        self.list_has_item_containing(res, [
            'DTSTART:20140318T140000\nRRULE:FREQ=DAILY;'
            'BYHOUR=14;BYMINUTE=0;UNTIL=20140325T140000',
        ])

    def test_group_successive_dates(self):
        res = gen_cohesive(u"""
            1, 2 et 3 janvier 2016,
            4 et 5 janvier 2016
        """)
        # wanted result
        # Du 1er au 5 janvier 2016

        self.list_has_item_containing(res, [
            'DTSTART:20160101T000000\nRRULE:FREQ=DAILY;'
            'BYHOUR=0;BYMINUTE=0;UNTIL=20160105T235900',
        ])

    def test_avoid_doubles_date(self):
        res = gen_cohesive(u"""
            1, 2 et 3 janvier 2016,
            3 et 4 janvier 2016,
            1 au 5 janvier 2016
        """)
        # wanted result
        # Du 1er au 5 janvier 2016

        self.list_has_item_containing(res, [
            'DTSTART:20160101T000000\nRRULE:FREQ=DAILY;'
            'BYHOUR=0;BYMINUTE=0;UNTIL=20160105T235900',
        ])

    def test_avoid_group_when_time_exist_and_differ(self):
        res = gen_cohesive(u"""
            1, 2 et 3 janvier 2016 à 21h30,
            3 et 4 janvier 2016 à 18h
        """)
        # wanted result
        # Du 1er au 3 janvier 2016 à 17 h 30
        # Du 3 au 4 janvier 2016 à 18 h

        self.list_has_item_containing(res, [
            'DTSTART:20160103T180000\nRRULE:FREQ=DAILY;'
            'BYHOUR=18;BYMINUTE=0;UNTIL=20160104T180000',

            'DTSTART:20160101T213000\nRRULE:FREQ=DAILY;'
            'BYHOUR=21;BYMINUTE=30;UNTIL=20160103T213000',
        ])

    def test_weekdays_concat(self):
        res = gen_cohesive(u"""
            le mercredi à 14h,
            le lundi et mardi à 14h
        """)
        # wanted result
        # Du lundi au mercredi, à 14 h

        self.list_has_item_containing(res, [
            'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE;BYHOUR=14;BYMINUTE=0;',
        ])

    def test_weekdays_not_concat_if_time_different(self):
        res = gen_cohesive(u"""
            le mercredi à 14h,
            le lundi et mardi à 15h,
            le lundi et mardi à 17h
        """)
        # wanted result
        # Le mercredi, à 14 h
        # Le lundi et mardi, à 15 h
        # Le lundi et mardi, à 17 h

        self.list_has_item_containing(res, [
            'FREQ=WEEKLY;BYDAY=WE;BYHOUR=14;BYMINUTE=0;',

            'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=17;BYMINUTE=0;',

            'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;',
        ])

    def test_weekdays_not_concat_if_day_different_with_composition(self):
        res = gen_cohesive(u"""
            du 2 avril au 15 août,
            le lundi et mardi à 15h',
            le mercredi à 16h
        """)
        # wanted result
        # Le mercredi, à 16 h
        # Le lundi et mardi, à 15 h

        self.list_has_item_containing(res, [
            'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;',

            'FREQ=WEEKLY;BYDAY=WE;BYHOUR=16;BYMINUTE=0;',
        ])

    def test_multiple_unification_possible(self):
        res = gen_cohesive(u"""
            du 14 avril au 16 juin 2020,
            le mercredi à 14h,
            le lundi et mardi à 15h
        """)
        # wanted result
        # Le lundi et mardi, du 14 avril au 16 juin 2020, à 15 h
        # Le mercredi, du 14 avril au 16 juin 2020, à 14 h

        self.list_has_item_containing(res, [
            'DTSTART:20200414T150000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
            'BYHOUR=15;BYMINUTE=0;UNTIL=20200616T150000',

            'DTSTART:20200414T140000\nRRULE:FREQ=WEEKLY;BYDAY=WE;'
            'BYHOUR=14;BYMINUTE=0;UNTIL=20200616T140000',
        ])

    def test_union_followed_by_composition(self):
        res = gen_cohesive(u"""
            du 14 avril au 16 juin 2020,
            du 5 juin au 9 juin 2020,
            le mercredi à 14h,
            le lundi et mardi à 15h
        """)
        # wanted result
        # Le lundi et mardi, du 14 avril au 16 juin 2020, à 15 h
        # Le mercredi, du 14 avril au 16 juin 2020, à 14 h

        self.list_has_item_containing(res, [
            '20200414T140000\nRRULE:FREQ=WEEKLY;BYDAY=WE;'
            'BYHOUR=14;BYMINUTE=0;UNTIL=20200616',

            '20200414T150000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
            'BYHOUR=15;BYMINUTE=0;UNTIL=20200616',
        ])

    def test_avoid_ambiguous_composition(self):
        res = gen_cohesive(u"""
            du 14 avril au 16 juin 2020,
            du 14 juillet au 9 août 2020,
            le mercredi à 14h,
            le lundi et mardi à 15h
        """)

        # wanted result
        # Le mercredi, à 14 h
        # Le lundi et mardi, à 15 h
        # Du 14 avril au 16 juin 2020, du 14 juillet au 9 août 2020

        self.list_has_item_containing(res, [
            'DTSTART:20200414T000000\nRRULE:FREQ=DAILY;'
            'BYHOUR=0;BYMINUTE=0;UNTIL=20200616T235900',

            'DTSTART:20200714T000000\nRRULE:FREQ=DAILY;'
            'BYHOUR=0;BYMINUTE=0;UNTIL=20200809T235900',

            'RRULE:FREQ=WEEKLY;BYDAY=WE;BYHOUR=14;BYMINUTE=0;',

            'RRULE:FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;',
        ])

    def test_fuzzy_time(self):
        res = gen_cohesive(u"""
            du 14 avril au 16 juin 2020 à 16h,
            du 14 avril au 16 juin 2020 à 15h,
        """)

        # wanted result
        # du 14 avril au 16 juin 2020 à 15h,

        self.list_has_item_containing(res, [
            '20200414T150000\nRRULE:FREQ=DAILY;BYHOUR=15;'
            'BYMINUTE=0;UNTIL=20200616'
        ])

    def test_temporal_distance(self):
        res = cohesive_rrules(datection.export(u"""
            du 16 avril au 16 juin 2020 à 16h,
            du 16 avril au 16 juin 2015 à 16h,
        """, 'fr', only_future=False),
                              created_at=datetime(year=2014, month=1, day=1))

        self.list_has_item_containing(res, [
            '20150416T160000\nRRULE:FREQ=DAILY;BYHOUR=16;BYMINUTE=0;UNTIL=20150616T160000'
        ])

    def test_real_case_1(self):
        res = gen_cohesive(u"""
            Le dimanche
            Le lundi
            Du 5 février 2014 au 5 février 2015 à 20 h
            Du 16 au 26 avril 2014
        """)

        # wanted result
        # Le lundi et dimanche, du 16 au 26 avril 2014, à 20 h

        self.list_has_item_containing(res, [
            'DTSTART:20140416T200000\nRRULE:FREQ=WEEKLY;BYDAY=MO,SU;BYHOUR=20;'
            'BYMINUTE=0;UNTIL=20140426T200000'
        ])

    def test_real_case_2(self):
        res = gen_cohesive(u"""
            Du jeudi au samedi, à 19 h 30
            Du jeudi au samedi, à 21 h 30
            Du jeudi au samedi
            Du 2 janvier au 1er mars 2014
        """)

        # wanted result
        # Du jeudi au samedi, du 2 janvier au 1er mars 2014, à 21 h 30
        # Du jeudi au samedi, du 2 janvier au 1er mars 2014, à 19 h 30

        self.list_has_item_containing(res, [
            'DTSTART:20140102T000000\nRRULE:FREQ=WEEKLY;BYDAY=TH,FR,SA;'
            'BYHOUR=19;BYMINUTE=30;UNTIL=20140301T000000',

            'DTSTART:20140102T000000\nRRULE:FREQ=WEEKLY;BYDAY=TH,FR,SA;'
            'BYHOUR=21;BYMINUTE=30;UNTIL=20140301T000000'
        ])

    def test_real_case_3(self):
        res = gen_cohesive(u"""
            Le jeudi, à 20 h 30
            Le jeudi, du 13 janvier au 28 février 2014, de 20 h à 21 h 15
            Du 12 septembre au 19 décembre 2013,
            13 février 2014, 20 février 2014,
            27 février 2014, 6 mars 2014,
            13 mars 2014, 20 mars 2014, 27 mars 2014 à 20 h
            Du 3 au 28 juillet 2013, du 12 septembre au 19 décembre 2013,
            7 novembre 2015, 5 décembre 2015
            Le 28 juillet 2013 à 13 h
        """)

        # wanted result
        # Le jeudi, du 13 janvier au 27 mars 2014, de 20 h à 21 h 15
        # Le jeudi, à 20 h 30
        # Du 12 septembre au 19 décembre 2013, le 7 novembre 2015, le 5 décembre 2015,
        # Du 3 au 28 juillet 2013 à 13 h

        self.list_has_item_containing(res, [
            'T203000\nRRULE:FREQ=WEEKLY;'
            'BYDAY=TH;BYHOUR=20;BYMINUTE=30;',

            'DTSTART:20151205T000000\nRRULE:FREQ=DAILY;'
            'COUNT=1;BYHOUR=0;BYMINUTE=0',

            'T200000\nRRULE:FREQ=WEEKLY;BYDAY=TH;'
            'BYHOUR=20;BYMINUTE=0;',

            'DTSTART:20130703T130000\nRRULE:FREQ=DAILY;'
            'BYHOUR=13;BYMINUTE=0;UNTIL=20130728T130000',

            'DTSTART:20130912T000000\nRRULE:FREQ=DAILY;'
            'BYHOUR=0;BYMINUTE=0;UNTIL=20131219T235900',

            'DTSTART:20151107T000000\nRRULE:FREQ=DAILY;'
            'COUNT=1;BYHOUR=0;BYMINUTE=0'
        ])

    def test_real_case_4(self):
        res = gen_cohesive(u"""
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
        """)

        # result wanted
        # Du 8 septembre au 29 décembre 2013 à 17 h
        # Du 1er mars au 17 mai 2014 à 18 h

        self.list_has_item_containing(res, [
            '20140301T180000\nRRULE:FREQ=DAILY;BYHOUR=18;'
            'BYMINUTE=0;UNTIL=20140517',

            '20130908T170000\nRRULE:FREQ=DAILY;BYHOUR=17;'
            'BYMINUTE=0;UNTIL=20131229',
        ])

    def test_real_case_5(self):
        res = gen_cohesive(u"""
            Le dimanche
            Le vendredi, à 20 h
            Le vendredi, dimanche, du 3 au 5 octobre 2014, à 20 h
            Du 4 au 6 octobre 2013
            Le 6 octobre 2013 à 13 h
        """)

        # result wanted
        # Le vendredi, dimanche, du 3 au 5 octobre 2014, à 20 h
        # Du 4 au 6 octobre 2013 à 13h

        self.list_has_item_containing(res, [
            'DTSTART:20131004T130000\nRRULE:FREQ=DAILY;'
            'BYHOUR=13;BYMINUTE=0;UNTIL=20131006T130000',

            'DTSTART:20141003T200000\nRRULE:FREQ=WEEKLY;'
            'BYDAY=FR,SU;BYHOUR=20;BYMINUTE=0;UNTIL=20141005T200000',
        ])

    def test_real_case_6(self):
        res = cohesive_rrules([{
            'duration': 1439,
            'rrule': 'DTSTART:20150705\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'
        }, {
            'duration': 1439,
            'rrule': 'DTSTART:20150704\nRRULE:FREQ=DAILY;BYHOUR=0;BYMINUTE=0;INTERVAL=1;UNTIL=20150705'
        }])

        # wanted result
        # Du 4 au 5 juillet 2015

        self.list_has_item_containing(res, [
            'DTSTART:20150704T000000\nRRULE:FREQ=DAILY;'
            'BYHOUR=0;BYMINUTE=0;UNTIL=20150705T235900'
        ])

    def test_real_case_7(self):
        res = cohesive_rrules([{
            'duration': 1439,
            'rrule': 'DTSTART:20130322\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=23'
        }, {
            'duration': 1439,
            'rrule': 'DTSTART:20130323\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=23'
        }])

        # wanted result
        # Du 22 au 23 mars 2013 à 23 h

        self.list_has_item_containing(res, [
            'DTSTART:20130322T230000\nRRULE:FREQ=DAILY;'
            'BYHOUR=23;BYMINUTE=0;UNTIL=20130323T230000'
        ])

    def test_real_case_8(self):
        res = cohesive_rrules([{
            'duration': 1439, 'rrule':
            'DTSTART:20131210\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'},
            {'duration': 1439, 'rrule':
             'DTSTART:20130603\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'},
            {'duration': 1439, 'rrule':
             'DTSTART:20130603\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'},
            {'duration': 1439, 'rrule':
             'DTSTART:20130606\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'},
            {'duration': 1439, 'rrule':
             'DTSTART:20130627\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'
             }])

        # wanted result
        # Les 3, 6 et 27 juin 2013, le 10 décembre 2013
        self.list_has_item_containing(res, [
            'DTSTART:20130627T000000\nRRULE:'
            'FREQ=DAILY;COUNT=1;BYHOUR=0;BYMINUTE=0',

            'DTSTART:20131210T000000\nRRULE:'
            'FREQ=DAILY;COUNT=1;BYHOUR=0;BYMINUTE=0',

            'DTSTART:20130603T000000\nRRULE:'
            'FREQ=DAILY;COUNT=1;BYHOUR=0;BYMINUTE=0',

            'DTSTART:20130606T000000\nRRULE:'
            'FREQ=DAILY;COUNT=1;BYHOUR=0;BYMINUTE=0'

        ])

    def test_real_case_9(self):
        res = cohesive_rrules([{
            'duration': 450,
            'rrule': 'DTSTART:\nRRULE:FREQ=DAILY;INTERVAL=1;BYMINUTE=00;BYHOUR=11;BYDAY=WE;WKST=MO'
        }, {
            'duration': 450,
            'rrule': 'DTSTART:\nRRULE:FREQ=DAILY;INTERVAL=1;BYMINUTE=00;BYHOUR=11;BYDAY=TH;WKST=MO'
        }, {
            'duration': 450,
            'rrule': 'DTSTART:\nRRULE:FREQ=DAILY;INTERVAL=1;BYMINUTE=00;BYHOUR=11;BYDAY=FR;WKST=MO'
        }, {
            'duration': 450,
            'rrule': 'DTSTART:\nRRULE:FREQ=DAILY;INTERVAL=1;BYMINUTE=00;BYHOUR=11;BYDAY=SA;WKST=MO'
        }, {
            'duration': 450,
            'rrule': 'DTSTART:\nRRULE:FREQ=DAILY;INTERVAL=1;BYMINUTE=00;BYHOUR=11;BYDAY=SU;WKST=MO'
        }])

        # wanted result
        # Du mercredi au dimanche, de 11 h à 18 h 30

        self.list_has_item_containing(res, [
            'FREQ=WEEKLY;BYDAY=WE,TH,FR,SA,SU;BYHOUR=11;BYMINUTE=0;'
        ])

    def test_real_case_10(self):
        res = cohesive_rrules([{
            u'duration': 90,
            u'rrule': u'DTSTART:20130726\nRRULE:FREQ=WEEKLY;BYDAY=TU,TH;BYHOUR=16;BYMINUTE=0;UNTIL=20140726'
        }, {
            u'duration': 90,
            u'rrule': u'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=TU,TH;BYHOUR=16;BYMINUTE=0;UNTIL=20140717'
        }])

        # wanted result
        # Le mardi et jeudi, de 16 h à 17 h 30

        self.list_has_item_containing(res, [
            'RRULE:FREQ=WEEKLY;BYDAY=TU,TH;BYHOUR=16;BYMINUTE=0;'
        ])

    def test_real_case_11(self):
        res = cohesive_rrules([{
            'duration': 0,
            'rrule': u'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=SA;UNTIL=20140717'
        }, {
            'duration': 240,
            'rrule': u'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;BYHOUR=9;BYMINUTE=0;UNTIL=20140717'
        }])

        # wanted result
        # le samedi de 9 h à 13 h

        self.list_has_item_containing(res, [
            'FREQ=WEEKLY;BYDAY=SA;BYHOUR=9;BYMINUTE=0;'
        ])

    def test_real_case_12(self):
        res = cohesive_rrules([{
            'duration': 1439,
            'rrule': 'DTSTART:20130726\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;UNTIL=20140726'
        }, {
            'duration': 0,
            'rrule': 'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=SU;UNTIL=20140717'
        }, {
            'duration': 0,
            'rrule': 'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;UNTIL=20140717'
        }, {
            'duration': 0,
            'rrule': 'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20140717'
        }])

        # wanted result
        # le lundi et le dimanche

        self.list_has_item_containing(res, [
            'FREQ=WEEKLY;BYDAY=MO;BYHOUR=0;BYMINUTE=0;',
            'FREQ=WEEKLY;BYDAY=SU;BYHOUR=0;BYMINUTE=0;'
        ])

    def test_real_case_13(self):
        res = cohesive_rrules([{
            'duration': 180,
            'rrule': 'DTSTART:20130401\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;BYHOUR=15;BYMINUTE=0;UNTIL=20131031'
        }, {
            'duration': 1439,
            'rrule': 'DTSTART:20130401\nRRULE:FREQ=DAILY;BYHOUR=0;BYMINUTE=0;INTERVAL=1;UNTIL=20131031'
        }, {
            'duration': 0,
            'rrule': 'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;UNTIL=20140717'
        }, {
            'duration': 0,
            'rrule': 'DTSTART:20131031\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=13'
        }, {
            'duration': 180,
            'rrule': 'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=SA,SU;BYHOUR=15;BYMINUTE=0;UNTIL=20140717'
        }, {
            'duration': 0,
            'rrule': 'DTSTART:20130717\nRRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20140717'
        }])

        # wanted result
        # Le samedi et dimanche, de 15 h à 18 h
        # Le lundi,
        # Le 31 octobre 2013 à 13 h
        # Du 1er avril au 31 octobre 2013 de 15 h à 18 h

        self.list_has_item_containing(res, [
            'DTSTART:20130401T150000\nRRULE:FREQ=DAILY;'
            'BYHOUR=15;BYMINUTE=0;UNTIL=20131031T180000',

            '\nRRULE:FREQ=WEEKLY;BYDAY=SA,SU;BYHOUR=15;BYMINUTE=0;',

            '\nRRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=0;BYMINUTE=0;',

            'DTSTART:20130401T130000\nRRULE:FREQ=DAILY;BYHOUR=13;BYMINUTE=0'
        ])

    def test_real_case_14(self):
        res = cohesive_rrules([{
            'duration': 1439,
            'rrule': 'DTSTART:20101220\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'
        }])
        self.assertEqual(
            res[0],
            {
                'duration': 1439,
                'rrule': 'DTSTART:20101220T000000\nRRULE:'
                'FREQ=DAILY;COUNT=1;BYHOUR=0;BYMINUTE=0',
            })

    def test_year_1000(self):
        res = cohesive_rrules([{
            'duration': 1439,
            'rrule': 'DTSTART:10001220\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'
        }])

        now = datetime.utcnow()
        next_year = datetime.utcnow() + timedelta(days=365)
        self.assertEqual(
            res[0],
            {
                'duration': 1439,
                'rrule': (
                    'DTSTART:%sT000000\nRRULE:FREQ=WEEKLY;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                    'BYHOUR=0;BYMINUTE=0;UNTIL=%sT000000'
                ) % (now.strftime('%Y%m%d'), next_year.strftime('%Y%m%d')),
            })
