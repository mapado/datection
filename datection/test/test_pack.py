# -*- coding: utf-8 -*-

""" Functional tests on datection.pack """

from builtins import zip
from builtins import range
import unittest

import six

from datection.timepoint import ALL_DAY
from datection.models import DurationRRule
from datection import pack


class TestPack(unittest.TestCase):

    def assertRruleStrEqual(self, rrule_str1, rrule_str2):
        new_rrule_lines = rrule_str1.splitlines()
        result_lines = rrule_str2.splitlines()
        self.assertEqual(new_rrule_lines[0], result_lines[0])
        new_details = new_rrule_lines[1].split(":")[1].split(";")
        res_details = result_lines[1].split(":")[1].split(";")
        six.assertCountEqual(self, new_details, res_details)

    def assertRrulesEqual(self, rrule1, rrule2):
        six.assertCountEqual(self, list(rrule1.keys()), list(rrule2.keys()))
        for k in list(rrule2.keys()):
            if k == 'rrule':
                self.assertRruleStrEqual(rrule1[k], rrule2[k])
            elif k == 'excluded':
                self.assertEqual(len(rrule1[k]), len(rrule2[k]))
                if len(rrule1[k]) > 0:
                    rrule1_exs = sorted(rrule1[k])
                    rrule2_exs = sorted(rrule2[k])
                    for rrule1_ex, rrule2_ex in zip(rrule1_exs, rrule2_exs):
                        self.assertRruleStrEqual(rrule1_ex, rrule2_ex)
            else:
                self.assertEqual(rrule1[k], rrule2[k])

    def assertPackEqual(self, rrules, result, pack_no_timings=False):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        packer = pack.RrulePacker(drrs, pack_no_timings=pack_no_timings)
        packed = packer.pack_rrules()
        self.assertEqual(len(packed), 1)
        new_rrule = packed[0].duration_rrule
        self.assertRrulesEqual(new_rrule, result)

    def assertPackEqualMulti(self, rrules, result):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        packer = pack.RrulePacker(drrs)
        packed = packer.pack_rrules()
        self.assertEqual(len(packed), len(result))
        sorted_packed = sorted(packed, key=lambda drr: drr.start_datetime)
        result = [DurationRRule(rrule) for rrule in result]
        sorted_result = sorted(result, key=lambda drr: drr.start_datetime)
        for i in range(len(result)):
            self.assertRrulesEqual(sorted_result[i].duration_rrule,
                                   sorted_packed[i].duration_rrule)

    def assertPackWithGapsEqual(self, rrules, result):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        packer = pack.RrulePackerWithGaps(drrs)
        packed = packer.pack_with_gaps()
        self.assertEqual(len(packed), 1)
        new_rrule = packed[0].duration_rrule
        self.assertRrulesEqual(new_rrule, result)

    def assertNotPack(self, rrules, pack_no_timings=False):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        packer = pack.RrulePacker(drrs, pack_no_timings=pack_no_timings)
        packed = packer.pack_rrules()
        six.assertCountEqual(self, drrs, packed)

    def assertNotPackWithGaps(self, rrules):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        packer = pack.RrulePackerWithGaps(drrs)
        packed = packer.pack_rrules()
        six.assertCountEqual(self, drrs, packed)

    def test_include_sing_in_cont(self):
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        self.assertPackEqual([single, cont], cont)

    def test_not_include_sing_in_cont(self):
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        single_date = {'duration': 30,
                       'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_date])

        single_hour = {'duration': 30,
                       'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=5')}
        self.assertNotPack([cont, single_hour])

        single_minu = {'duration': 30,
                       'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=8;BYHOUR=3')}
        self.assertNotPack([cont, single_minu])

        single_dura = {'duration': 5,
                       'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_dura])

    def test_include_sing_in_wrec(self):
        single = {'duration': 60,
                  'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        self.assertPackEqual([single, weekly], weekly)

        weekly_2 = {'duration': 60,
                    'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        self.assertPackEqual([single, weekly_2], weekly_2)

    def test_not_include_sing_in_wrec(self):

        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}

        single_hour = {'duration': 60,
                       'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=9')}
        self.assertNotPack([weekly, single_hour])

        single_minu = {'duration': 60,
                       'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=1;BYHOUR=8')}
        self.assertNotPack([weekly, single_minu])

        single_day = {'duration': 60,
                      'rrule': ('DTSTART:20150318\nRRULE:FREQ=DAILY;'
                                'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        self.assertNotPack([weekly, single_day])

        single_dura = {'duration': 90,
                       'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        self.assertNotPack([weekly, single_dura])

    def test_extend_cont_with_sing(self):
        single_before = {'duration': 30,
                         'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        single_after = {'duration': 30,
                        'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                                  'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        result = {'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161024T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}
        self.assertPackEqual([single_before, cont, single_after], result)

    def test_not_extend_cont(self):
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        single_too_soon = {'duration': 30,
                           'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                     'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_too_soon])

        single_too_late = {'duration': 30,
                           'rrule': ('DTSTART:20161025\nRRULE:FREQ=DAILY;'
                                     'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_too_late])

        single_hour = {'duration': 30,
                       'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=4')}
        self.assertNotPack([cont, single_hour])

        single_minute = {'duration': 30,
                         'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=10;BYHOUR=3')}
        self.assertNotPack([cont, single_minute])

        single_duration = {'duration': 90,
                           'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                     'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_duration])

    def test_extend_wrec_with_sing(self):
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        sing_before = {'duration': 60,
                       'rrule': ('DTSTART:20150303\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_after = {'duration': 60,
                      'rrule': ('DTSTART:20150331\nRRULE:FREQ=DAILY;'
                                'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20150303\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150331T235959')}

        self.assertPackEqual([weekly, sing_before, sing_after], result)

    def test_not_extend_wrec(self):
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}

        sing_too_soon = {'duration': 60,
                         'rrule': ('DTSTART:20150217\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        self.assertNotPack([weekly, sing_too_soon])

        sing_too_late = {'duration': 60,
                         'rrule': ('DTSTART:20150407\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        self.assertNotPack([weekly, sing_too_late])

        sing_wrong_day = {'duration': 60,
                          'rrule': ('DTSTART:20150225\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        self.assertNotPack([weekly, sing_wrong_day])

        sing_wrong_dur = {'duration': 61,
                          'rrule': ('DTSTART:20150224\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        self.assertNotPack([weekly, sing_wrong_dur])

        sing_wrong_min = {'duration': 60,
                          'rrule': ('DTSTART:20150224\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=5;BYHOUR=8')}
        self.assertNotPack([weekly, sing_wrong_min])

        sing_wrong_hou = {'duration': 60,
                          'rrule': ('DTSTART:20150224\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=0;BYHOUR=9')}
        self.assertNotPack([weekly, sing_wrong_hou])

    def test_fusion_cont_overlap(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        result = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}
        self.assertPackEqual([cont1, cont2], result)

    def test_fusion_cont_extend(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        result = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}
        self.assertPackEqual([cont1, cont2], result)

    def test_no_fusion_cont_gap(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161025\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        self.assertNotPack([cont1, cont2])

    def test_no_fusion_cont_diff(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=2'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        self.assertNotPack([cont1, cont2])

        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=10;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        self.assertNotPack([cont1, cont2])

        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 40}
        self.assertNotPack([cont1, cont2])

    def test_fusion_wrec_overlap(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150414T235959')}
        self.assertPackEqual([weekly1, weekly2], result)

    def test_fusion_wrec_extend(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150329\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150414T235959')}
        self.assertPackEqual([weekly1, weekly2], result)

    def test_fusion_wrec_days(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20161011\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161019T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20161004\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161018T235959')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20161010\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20161018T235959')}
        self.assertPackEqual([weekly1, weekly2], result)

    def test_no_fusion_wrec_gap(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150405\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

    def test_no_fusion_wrec_diff(self):
        weekly1 = {'duration': 30,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=9;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=10;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150302\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

    def test_no_fusion_wrec_days(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20161011\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161019T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20161003\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161018T235959')}
        self.assertNotPack([weekly1, weekly2])

    def test_merge_sing_into_cont(self):
        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20161028\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20161027\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        cont = {'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161028T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}
        self.assertPackEqual([sing_3, sing_1, sing_2], cont)

    def test_merge_continuous_sing_into_cont(self):
        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20161028\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20161027\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        cont = {'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161028T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}
        self.assertPackEqual([sing_3, sing_1, sing_2], cont)

    def test_remove_duplicate_single_dates(self):
        sing_1 = {
            "duration": 0,
            "rrule": "DTSTART:20190125\nRRULE:FREQ=DAILY;COUNT=1;BYHOUR=19;BYMINUTE=5"
        }

        sing_2 = {
            "duration": 0,
            "rrule": "DTSTART:20190125\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=05;BYHOUR=19;BYDAY=MO,TU,WE,TH,FR,SA,SU"
        }
        self.assertPackEqual([sing_1, sing_2], sing_1)

    def test_remove_englobing_single_dates(self):
        sing_1 = {
            "duration": 0,
            "rrule": "DTSTART:20190125\nRRULE:FREQ=DAILY;COUNT=1;BYHOUR=19;BYMINUTE=5"
        }

        sing_2 = {
            "duration": 240,
            "rrule": "DTSTART:20190125\nRRULE:FREQ=DAILY;COUNT=1;BYHOUR=19;BYMINUTE=5"
        }
        self.assertPackEqual([sing_1, sing_2], sing_2)

    def test_merge_sing_into_cont_2(self):
        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20161028\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_3_bis = {'duration': 60,
                      'rrule': ('DTSTART:20161028\nRRULE:FREQ=DAILY;'
                                'COUNT=1;BYMINUTE=0;BYHOUR=9')}
        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_1_bis = {'duration': 60,
                      'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                                'COUNT=1;BYMINUTE=0;BYHOUR=9')}
        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20161027\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_2_bis = {'duration': 60,
                      'rrule': ('DTSTART:20161027\nRRULE:FREQ=DAILY;'
                                'COUNT=1;BYMINUTE=0;BYHOUR=9')}
        cont = {'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161028T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}
        cont_bis = {'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                              'UNTIL=20161028T235959;INTERVAL=1;'
                              'BYMINUTE=0;BYHOUR=9'),
                    'duration': 60}
        self.assertPackEqualMulti([sing_3, sing_1, sing_2, sing_1_bis,
                                   sing_2_bis, sing_3_bis],
                                  [cont_bis, cont])

    def test_merge_sing_into_wrec(self):
        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20161012\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20161012\nRRULE:FREQ=WEEKLY;BYDAY=WE;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20161026T235959')}
        self.assertPackEqual([sing_3, sing_1, sing_2], weekly)

    def test_many_sing_merge_week(self):
        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20161012\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_4 = {'duration': 60,
                  'rrule': ('DTSTART:20161020\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_5 = {'duration': 60,
                  'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_6 = {'duration': 60,
                  'rrule': ('DTSTART:20161102\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        sing_list = [sing_1, sing_2, sing_3, sing_4, sing_5, sing_6]
        drrs = [DurationRRule(s) for s in sing_list]
        packer = pack.RrulePacker(drrs)
        packed = packer.pack_rrules()
        self.assertEqual(len(packed), 3)
        self.assertEqual(len(packer._single_dates), 2)
        self.assertEqual(len(packer._weekly_rec), 1)

        new_week = packer._weekly_rec[0].duration_rrule
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20161012\nRRULE:FREQ=WEEKLY;BYDAY=WE;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20161102T235959')}
        self.assertRrulesEqual(new_week, weekly)

    def test_many_sing_merge_cont(self):
        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20161012\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_4 = {'duration': 60,
                  'rrule': ('DTSTART:20161020\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_5 = {'duration': 60,
                  'rrule': ('DTSTART:20161021\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_6 = {'duration': 60,
                  'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}

        sing_list = [sing_1, sing_2, sing_3, sing_4, sing_5, sing_6]
        drrs = [DurationRRule(s) for s in sing_list]
        packer = pack.RrulePacker(drrs)
        packed = packer.pack_rrules()
        self.assertEqual(len(packed), 3)
        self.assertEqual(len(packer._single_dates), 2)
        self.assertEqual(len(packer._continuous), 1)

        new_cont = packer._continuous[0].duration_rrule
        cont = {'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161021T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=8'),
                'duration': 60}
        self.assertRrulesEqual(new_cont, cont)

    def test_merge_two_weekly(self):
        sing_1 = {'duration': 60,
                  'rrule': ('DTSTART:20161012\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_2 = {'duration': 60,
                  'rrule': ('DTSTART:20161013\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_3 = {'duration': 60,
                  'rrule': ('DTSTART:20161019\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_4 = {'duration': 60,
                  'rrule': ('DTSTART:20161020\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_5 = {'duration': 60,
                  'rrule': ('DTSTART:20161026\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        sing_6 = {'duration': 60,
                  'rrule': ('DTSTART:20161027\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20161012\nRRULE:FREQ=WEEKLY;BYDAY=WE,TH;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20161027T235959')}
        self.assertPackEqual([sing_1, sing_2, sing_3, sing_4, sing_5, sing_6], weekly)

    def test_no_timing_matching_cont_include(self):
        single = {'duration': ALL_DAY,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=0')}

        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        self.assertNotPack([single, cont], pack_no_timings=False)
        self.assertPackEqual([single, cont], cont, pack_no_timings=True)

    def test_no_timing_matching_cont_extend(self):
        single_before = {'duration': ALL_DAY,
                         'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=0;BYHOUR=0')}

        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}

        result = {'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161023T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30}
        self.assertNotPack([single_before, cont], pack_no_timings=False)
        self.assertPackEqual([single_before, cont], result, pack_no_timings=True)

    def test_no_timing_matching_week_include(self):
        single = {'duration': ALL_DAY,
                  'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=0')}

        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        self.assertNotPack([single, weekly], pack_no_timings=False)
        self.assertPackEqual([single, weekly], weekly, pack_no_timings=True)

    def test_no_timing_matching_week_extend(self):
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        sing_before = {'duration': ALL_DAY,
                       'rrule': ('DTSTART:20150303\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=0')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20150303\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}

        self.assertNotPack([weekly, sing_before], pack_no_timings=False)
        self.assertPackEqual([weekly, sing_before], result, pack_no_timings=True)

    def test_pack_conts_with_gaps(self):
        # exception is a continuous single date
        cont1 = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161022T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        result = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'excluded': [
                      ('DTSTART:20161023\nRRULE:FREQ=DAILY;BYHOUR=3;'
                       'BYMINUTE=0;COUNT=1')],
                  'duration': 30}
        self.assertPackWithGapsEqual([cont1, cont2], result)

        # exception is a continuous rrule
        cont1 = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161021T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        result = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'excluded': [
                      ('DTSTART:20161022\nRRULE:FREQ=DAILY;BYHOUR=3;'
                       'BYMINUTE=0;INTERVAL=1;UNTIL=20161023T235959')],
                  'duration': 30}
        self.assertPackWithGapsEqual([cont1, cont2], result)

    def test_no_pack_conts_with_gaps(self):
        cont1 = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161009T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        self.assertNotPackWithGaps([cont1, cont2])

    def test_pack_wrecs_with_gaps(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20170307\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20170401T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20170411\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20170516T235959')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20170307\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20170516T235959'),
                  'excluded': [
                      ('DTSTART:20170402\nRRULE:FREQ=DAILY;BYHOUR=8;'
                       'BYMINUTE=0;INTERVAL=1;UNTIL=20170410T235959')]}
        self.assertPackWithGapsEqual([weekly1, weekly2], result)

    def test_no_pack_wrecs_with_gaps(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20170321\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20170401T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20170420\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20170503T235959')}
        self.assertNotPackWithGaps([weekly1, weekly2])
