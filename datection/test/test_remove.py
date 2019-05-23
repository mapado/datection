# -*- coding: utf-8 -*-

""" Functional tests on datection.combine.remove """

from builtins import range
import six
import unittest

from datection.combine.remove import RruleRemover
from datection.models import DurationRRule


class TestRemove(unittest.TestCase):

    def assertRrulesEqual(self, rrule1, rrule2):
        six.assertCountEqual(self, list(rrule1.keys()), list(rrule2.keys()))
        for k in list(rrule2.keys()):
            if k == 'rrule':
                new_rrule_lines = rrule1[k].splitlines()
                result_lines = rrule2[k].splitlines()
                self.assertEqual(new_rrule_lines[0], result_lines[0])
                new_details = new_rrule_lines[1].split(":")[1].split(";")
                res_details = result_lines[1].split(":")[1].split(";")
                six.assertCountEqual(self, new_details, res_details)
            else:
                self.assertEqual(rrule1[k], rrule2[k])

    def assertNothingLeft(self, rrules, to_remove):
        remover = RruleRemover([DurationRRule(rrule) for rrule in rrules])
        remover.remove_rrules([DurationRRule(rrule) for rrule in to_remove])
        self.assertEqual(len(remover.get_remaining_rrules()), 0)

    def assertNotImpacted(self, rrules, to_remove):
        remover = RruleRemover([DurationRRule(rrule) for rrule in rrules])
        remover.remove_rrules([DurationRRule(rrule) for rrule in to_remove])
        result = remover.get_remaining_rrules()
        self.assertRrulesEqual(result[0].duration_rrule,
                               DurationRRule(rrules[0]).duration_rrule)

    def assertRemoveEquals(self, rrules, to_remove, expected):
        remover = RruleRemover([DurationRRule(rrule) for rrule in rrules])
        remover.remove_rrules([DurationRRule(rrule) for rrule in to_remove])
        result = remover.get_remaining_rrules()
        self.assertEqual(len(result), len(expected))
        sorted_result = sorted(result, key=lambda drr: drr.start_datetime)
        expected = [DurationRRule(rrule) for rrule in expected]
        sorted_expected = sorted(expected, key=lambda drr: drr.start_datetime)
        for i in range(len(result)):
            self.assertRrulesEqual(sorted_result[i].duration_rrule,
                                   sorted_expected[i].duration_rrule)

    def test_remove_sing_from_sing(self):
        sing_1 = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        sing_2 = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNothingLeft([sing_1], [sing_2])

    def test_not_remove_sing_from_sing(self):
        sing_1 = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        sing_2 = {'duration': 30,
                  'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        sing_3 = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=10;BYHOUR=3')}

        sing_4 = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=4')}

        sing_5 = {'duration': 35,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        self.assertNotImpacted([sing_1], [sing_2])
        self.assertNotImpacted([sing_1], [sing_3])
        self.assertNotImpacted([sing_1], [sing_4])
        self.assertNotImpacted([sing_1], [sing_5])

    def test_remove_sing_from_cont_begin(self):
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        result = {'rrule': ('DTSTART:20161017\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161023T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        self.assertRemoveEquals([cont], [single], [result])

    def test_remove_sing_from_cont_end(self):
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161023\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        result = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161022T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        self.assertRemoveEquals([cont], [single], [result])

    def test_remove_sing_from_cont_middle(self):
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        result_1 = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                              'UNTIL=20161017T235959;INTERVAL=1;'
                              'BYMINUTE=0;BYHOUR=3'),
                    'duration': 30}

        result_2 = {'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                              'UNTIL=20161023T235959;INTERVAL=1;'
                              'BYMINUTE=0;BYHOUR=3'),
                    'duration': 30}

        self.assertRemoveEquals([cont], [single], [result_1, result_2])

    def test_not_remove_sing_from_cont(self):
        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        sing_1 = {'duration': 30,
                  'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        sing_2 = {'duration': 30,
                  'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        sing_3 = {'duration': 30,
                  'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=5')}

        sing_4 = {'duration': 30,
                  'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=10;BYHOUR=3')}

        sing_5 = {'duration': 40,
                  'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=10;BYHOUR=3')}

        self.assertNotImpacted([cont], [sing_1])
        self.assertNotImpacted([cont], [sing_2])
        self.assertNotImpacted([cont], [sing_3])
        self.assertNotImpacted([cont], [sing_4])
        self.assertNotImpacted([cont], [sing_5])

    def test_remove_sing_from_wrec_begin(self):
        single = {'duration': 60,
                  'rrule': ('DTSTART:20170207\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        result = {'duration': 60,
                  'rrule': ('DTSTART:20170208\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        self.assertRemoveEquals([wrec], [single], [result])

    def test_remove_sing_from_wrec_end(self):
        single = {'duration': 60,
                  'rrule': ('DTSTART:20170221\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170227T235959')}

        result = {'duration': 60,
                  'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170220T235959')}

        self.assertRemoveEquals([wrec], [single], [result])

    def test_remove_sing_from_wrec_middle(self):
        single = {'duration': 60,
                  'rrule': ('DTSTART:20170214\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170227T235959')}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170213T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170215\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170227T235959')}

        self.assertRemoveEquals([wrec], [single], [result_1, result_2])

    def test_not_remove_sing_from_wrec(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170131\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170307\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170207\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=9')}

        sing_4 = {'duration': 60,
                  'rrule': ('DTSTART:20170208\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        self.assertNotImpacted([wrec], [sing_1])
        self.assertNotImpacted([wrec], [sing_2])
        self.assertNotImpacted([wrec], [sing_3])
        self.assertNotImpacted([wrec], [sing_4])

    def test_remove_cont_from_sing(self):
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont_1 = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161023T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        cont_2 = {'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161023T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        cont_3 = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161018T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        self.assertNothingLeft([single], [cont_1])
        self.assertNothingLeft([single], [cont_2])
        self.assertNothingLeft([single], [cont_3])

    def test_not_remove_cont_from_sing(self):
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont_1 = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161023T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 35}

        cont_2 = {'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161023T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        cont_3 = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161017T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        self.assertNotImpacted([single], [cont_1])
        self.assertNotImpacted([single], [cont_2])
        self.assertNotImpacted([single], [cont_3])

    def test_remove_cont_from_cont_full(self):
        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        bigger_cont = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                                 'UNTIL=20161023T235959;INTERVAL=1;'
                                 'BYMINUTE=0;BYHOUR=3'),
                       'duration': 30}

        self.assertNothingLeft([cont], [bigger_cont])

    def test_remove_cont_from_cont_begin(self):
        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        cont_1 = {'rrule': ('DTSTART:20161014\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161018T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        result = {'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161023T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        self.assertRemoveEquals([cont], [cont_1], [result])

    def test_remove_cont_from_cont_end(self):
        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        cont_1 = {'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        result = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161017T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        self.assertRemoveEquals([cont], [cont_1], [result])

    def test_remove_cont_from_cont_middle(self):
        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        cont_1 = {'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161021T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        result_1 = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                              'UNTIL=20161017T235959;INTERVAL=1;'
                              'BYMINUTE=0;BYHOUR=3'),
                    'duration': 30}

        result_2 = {'rrule': ('DTSTART:20161022\nRRULE:FREQ=DAILY;'
                              'UNTIL=20161023T235959;INTERVAL=1;'
                              'BYMINUTE=0;BYHOUR=3'),
                    'duration': 30}

        self.assertRemoveEquals([cont], [cont_1], [result_1, result_2])

    def test_not_remove_cont_from_cont(self):
        cont = {'rrule': ('DTSTART:20161016\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        cont_1 = {'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161021T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 35}

        cont_2 = {'rrule': ('DTSTART:20161014\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161015T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        cont_3 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161026T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}

        cont_4 = {'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161021T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=6'),
                  'duration': 30}

        self.assertNotImpacted([cont], [cont_1])
        self.assertNotImpacted([cont], [cont_2])
        self.assertNotImpacted([cont], [cont_3])
        self.assertNotImpacted([cont], [cont_4])

    def test_remove_cont_from_wrec_begin(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        cont = {'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170208T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        result = {'duration': 60,
                  'rrule': ('DTSTART:20170209\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        self.assertRemoveEquals([wrec], [cont], [result])

    def test_remove_cont_from_wrec_middle(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        cont = {'rrule': ('DTSTART:20170208\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170215T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170207T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170216\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        self.assertRemoveEquals([wrec], [cont], [result_1, result_2])

    def test_remove_cont_from_wrec_end(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        cont = {'rrule': ('DTSTART:20170220\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170304T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        result = {'duration': 60,
                  'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170219T235959')}

        self.assertRemoveEquals([wrec], [cont], [result])

    def test_remove_cont_from_wrec_full(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        cont = {'rrule': ('DTSTART:20170205\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170304T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        self.assertNothingLeft([wrec], [cont])

    def test_not_remove_cont_from_wrec(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        cont_1 = {'rrule': ('DTSTART:20170301\nRRULE:FREQ=DAILY;'
                            'UNTIL=20170304T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=8'),
                  'duration': 60}

        cont_2 = {'rrule': ('DTSTART:20170120\nRRULE:FREQ=DAILY;'
                            'UNTIL=20170205T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=8'),
                  'duration': 60}

        cont_3 = {'rrule': ('DTSTART:20170220\nRRULE:FREQ=DAILY;'
                            'UNTIL=20170304T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=7'),
                  'duration': 60}

        self.assertNotImpacted([wrec], [cont_1])
        self.assertNotImpacted([wrec], [cont_2])
        self.assertNotImpacted([wrec], [cont_3])

    def test_remove_wrec_from_sing(self):
        single = {'duration': 60,
                  'rrule': ('DTSTART:20170214\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170213\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170215T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170214\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170219T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170207\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170214T235959')}

        self.assertNothingLeft([single], [wrec_1])
        self.assertNothingLeft([single], [wrec_2])
        self.assertNothingLeft([single], [wrec_3])

    def test_not_remove_wrec_from_sing(self):
        single = {'duration': 60,
                  'rrule': ('DTSTART:20170214\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        wrec_1 = {'duration': 64,
                  'rrule': ('DTSTART:20170213\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170215T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170215\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170219T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170207\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170213T235959')}

        wrec_4 = {'duration': 60,
                  'rrule': ('DTSTART:20170213\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170215T235959')}

        self.assertNotImpacted([single], [wrec_1])
        self.assertNotImpacted([single], [wrec_2])
        self.assertNotImpacted([single], [wrec_3])
        self.assertNotImpacted([single], [wrec_4])

    def test_remove_wrec_from_cont_begin(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170128\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170212T235959')}

        cont = {'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170221T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,WE,TH,FR,SA,SU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170207T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170208\nRRULE:FREQ=DAILY;INTERVAL=1;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170221T235959')}

        self.assertRemoveEquals([cont], [wrec], [result_1, result_2])

    def test_remove_wrec_from_cont_middle(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170206\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170216T235959')}

        cont = {'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170225T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;INTERVAL=1;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170206T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170207\nRRULE:FREQ=WEEKLY;BYDAY=MO,WE,TH,FR,SA,SU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170214T235959')}

        result_3 = {'duration': 60,
                    'rrule': ('DTSTART:20170215\nRRULE:FREQ=DAILY;INTERVAL=1;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170225T235959')}

        self.assertRemoveEquals([cont], [wrec], [result_1, result_2, result_3])

    def test_remove_wrec_from_cont_end(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170215\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        cont = {'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170225T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170221\nRRULE:FREQ=WEEKLY;BYDAY=MO,WE,TH,FR,SA,SU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170225T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;INTERVAL=1;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170220T235959')}

        self.assertRemoveEquals([cont], [wrec], [result_1, result_2])

    def test_remove_wrec_from_cont_full(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170128\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        cont = {'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170225T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,WE,TH,FR,SA,SU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170225T235959')}

        self.assertRemoveEquals([cont], [wrec], [result_1])

    def test_not_remove_wrec_from_cont(self):
        cont = {'rrule': ('DTSTART:20170201\nRRULE:FREQ=DAILY;'
                          'UNTIL=20170224T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}

        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170128\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170205T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170222\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170128\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=10;UNTIL=20170212T235959')}

        self.assertNotImpacted([cont], [wrec_1])
        self.assertNotImpacted([cont], [wrec_2])
        self.assertNotImpacted([cont], [wrec_3])

    def test_remove_wrec_from_wrec_begin(self):
        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170120\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170213T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170120\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170207T235959')}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170207T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170208\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        self.assertRemoveEquals([wrec_1], [wrec_2], [result_1, result_2])
        self.assertRemoveEquals([wrec_1], [wrec_3], [result_2])

    def test_remove_wrec_from_wrec_middle(self):
        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170208\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170215T235959')}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;'
                              'BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170213T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170214\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170214T235959')}

        result_3 = {'duration': 60,
                    'rrule': ('DTSTART:20170215\nRRULE:FREQ=WEEKLY;'
                              'BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        self.assertRemoveEquals([wrec_1], [wrec_2],
                                [result_1, result_2, result_3])

    def test_remove_wrec_from_wrec_middle_full(self):
        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170208\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170215T235959')}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;'
                              'BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170212T235959')}

        result_3 = {'duration': 60,
                    'rrule': ('DTSTART:20170215\nRRULE:FREQ=WEEKLY;'
                              'BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        self.assertRemoveEquals([wrec_1], [wrec_3], [result_1, result_3])

    def test_remove_wrec_from_wrec_end(self):
        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170214\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170214\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        result_1 = {'duration': 60,
                    'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170213T235959')}

        result_2 = {'duration': 60,
                    'rrule': ('DTSTART:20170214\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        self.assertRemoveEquals([wrec_1], [wrec_2], [result_1, result_2])
        self.assertRemoveEquals([wrec_1], [wrec_3], [result_1])

    def test_remove_wrec_from_wrec_full(self):
        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170130\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170130\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170228T235959')}

        result = {'duration': 60,
                  'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        self.assertRemoveEquals([wrec_1], [wrec_2], [result])
        self.assertNothingLeft([wrec_1], [wrec_3])

    def test_not_remove_wrec_from_wrec(self):
        wrec = {'duration': 60,
                'rrule': ('DTSTART:20170201\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                          'BYHOUR=8;BYMINUTE=0;UNTIL=20170222T235959')}

        wrec_1 = {'duration': 60,
                  'rrule': ('DTSTART:20170208\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=10;UNTIL=20170215T235959')}

        wrec_2 = {'duration': 60,
                  'rrule': ('DTSTART:20170208\nRRULE:FREQ=WEEKLY;BYDAY=WE;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170215T235959')}

        wrec_3 = {'duration': 60,
                  'rrule': ('DTSTART:20170120\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170131T235959')}

        wrec_4 = {'duration': 60,
                  'rrule': ('DTSTART:20170223\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170315T235959')}

        self.assertNotImpacted([wrec], [wrec_1])
        self.assertNotImpacted([wrec], [wrec_2])
        self.assertNotImpacted([wrec], [wrec_3])
        self.assertNotImpacted([wrec], [wrec_4])
