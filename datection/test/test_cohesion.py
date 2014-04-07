# -*- coding: utf-8 -*-
"""
Test suite of the datection.cohesive
"""

import unittest
import datection

from datection.cohesion import cohesive_rrules


def gen_cohesive(mystr):
    return cohesive_rrules(datection.to_db(mystr, 'fr', only_future=False))


class TestMoreCohesive(unittest.TestCase):

    """Test suite of functions responsible of a duration rrrule minifier

    That build more cohesive and human readable date sentences.

    """

    def list_has_item_containing(self, items, contains):
        self.assertEqual(len(items), len(contains))
        is_validated_contains = [False for it in contains]
        for drr in items:
            for idx, cont in enumerate(contains):
                if cont in drr['rrule']:
                    is_validated_contains[idx] = True
        for cont in is_validated_contains:
            self.assertTrue(cont)

    def test_days_recurrence_in_lapse_time(self):
        res = gen_cohesive("""
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
        res = gen_cohesive("""
            le 21 mars 2014,
            le 21 mars 2014 à 14h
        """)
        # wanted result
        # Le 21 mars 2014 à 14 h

        self.list_has_item_containing(res, [
            'DTSTART:20140321T140000\nRRULE:FREQ=DAILY;'
            'COUNT=1;BYHOUR=14;BYMINUTE=0',
        ])

    def test_precise_time_in_a_lapse_time(self):
        res = gen_cohesive("""
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
        res = gen_cohesive("""
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
        res = gen_cohesive("""
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
        res = gen_cohesive("""
            1, 2 et 3 janvier 2016 à 17h30,
            3 et 4 janvier 2016 à 18h
        """)
        # wanted result
        # Du 1er au 3 janvier 2016 à 17 h 30
        # Du 3 au 4 janvier 2016 à 18 h

        self.list_has_item_containing(res, [
            'DTSTART:20160103T180000\nRRULE:FREQ=DAILY;'
            'BYHOUR=18;BYMINUTE=0;UNTIL=20160104T180000',

            'DTSTART:20160101T173000\nRRULE:FREQ=DAILY;'
            'BYHOUR=17;BYMINUTE=30;UNTIL=20160103T173000',
        ])

    def test_weekdays_concat(self):
        res = gen_cohesive("""
            le mercredi à 14h,
            le lundi et mardi à 14h
        """)
        # wanted result
        # Du lundi au mercredi, à 14 h

        self.list_has_item_containing(res, [
            'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE;BYHOUR=14;BYMINUTE=0;',
        ])

    def test_weekdays_not_concat_if_time_different(self):
        res = gen_cohesive("""
            le mercredi à 14h,
            le lundi et mardi à 15h,
            le lundi et mardi à 16h
        """)
        # wanted result
        # Le mercredi, à 14 h
        # Le lundi et mardi, à 16 h
        # Le lundi et mardi, à 15 h

        self.list_has_item_containing(res, [
            'FREQ=WEEKLY;BYDAY=WE;BYHOUR=14;BYMINUTE=0;',

            'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=16;BYMINUTE=0;',

            'FREQ=WEEKLY;BYDAY=MO,TU;BYHOUR=15;BYMINUTE=0;',
        ])

    def test_weekdays_not_concat_if_day_different_with_composition(self):
        res = gen_cohesive("""
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
        res = gen_cohesive("""
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
        res = gen_cohesive("""
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
        res = gen_cohesive("""
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

    def test_real_case_1(self):
        res = gen_cohesive("""
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
        res = gen_cohesive("""
            Du jeudi au samedi, à 19 h 30
            Du jeudi au samedi, à 21 h 30
            Du jeudi au samedi
            Du 2 janvier au 1er mars 2014
        """)

        # wanted result
        # Du jeudi au samedi, du 2 janvier au 1er mars 2014, à 21 h 30
        # Du jeudi au samedi, du 2 janvier au 1er mars 2014, à 19 h 30

        self.list_has_item_containing(res, [
            'DTSTART:20140102T213000\nRRULE:FREQ=WEEKLY;BYDAY=TH,FR,SA;'
            'BYHOUR=21;BYMINUTE=30;UNTIL=20140301T213000',

            'DTSTART:20140102T193000\nRRULE:FREQ=WEEKLY;BYDAY=TH,FR,SA;'
            'BYHOUR=19;BYMINUTE=30;UNTIL=20140301T193000',
        ])

    def test_real_case_3(self):
        res = gen_cohesive("""
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
            '20151205T000000\nRRULE:FREQ=DAILY;COUNT=1;',

            '20130703T130000\nRRULE:FREQ=DAILY;'
            'BYHOUR=13;BYMINUTE=0;UNTIL=20130728',

            '20140113T200000\nRRULE:FREQ=WEEKLY;BYDAY=TH;'
            'BYHOUR=20;BYMINUTE=0;UNTIL=20140327',

            'FREQ=WEEKLY;BYDAY=TH;BYHOUR=20;BYMINUTE=30;',

            '20130912T000000\nRRULE:FREQ=DAILY;'
            'BYHOUR=0;BYMINUTE=0;UNTIL=20131219',

            '20151107T000000\nRRULE:FREQ=DAILY;COUNT=1;',
        ])

    def test_real_case_4(self):
        res = gen_cohesive("""
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
        res = gen_cohesive("""
            Le dimanche
            Le vendredi, à 20 h
            Le vendredi, dimanche, du 3 au 5 octobre 2014, à 20 h
            Du 4 au 6 octobre 2013
            Le 6 octobre 2013 à 13 h
        """)

        # result wanted
        # du 3 au 5 octobre 2014, à 20 h
        # Du 4 au 6 octobre 2013 à 13h
        # TODO

    def test_real_case_6(self):
        res = gen_cohesive("""
            Le samedi, à 14 h
            Le dimanche, à 10 h 30
            Les 8, 9, 10, 10, 11, 11, 12 et 12 janvier 2014
            Le 8 janvier 2014 à 14 h
        """)

        # result wanted
        # TODO
        # Du 8 au 11 janvier 2014 à 14 h
        # Le dimanche 12 janvier à 10h30

    def test_real_case_7(self):
        res = gen_cohesive("""
            Le dimanche, de 10 h à 18 h
            Du 17 au 19 janvier 2014 de 9 h à 18 h
        """)

        # result wanted
        # Du 17 au 19 janvier 2014 de 9 h à 18 h

        # TODO because there is only 1 day that match perfectly patern so extend to
        # what seem to be a resonable timelapse.


    # TODO set close time has mergeable (get avg by half hours)
    # TODO set lonely hour del if a more complete rrule has same
    # TODO set composition has an option
