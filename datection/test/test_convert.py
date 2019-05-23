# -*- encoding: utf-8 -*-
"""
Test suite for the datection.convert module
"""
from builtins import zip
from builtins import range
import unittest

import six

from datection.convert import convert_to_concise_form
from datection.convert import convert_to_plain_form
from datection.models import DurationRRule


class TestConvert(unittest.TestCase):

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

    def assertConvertEqual(self, rrules, expected, func):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        expected = [DurationRRule(rrule) for rrule in expected]
        results = func(drrs)
        sorted_result = sorted(results, key=lambda drr: drr.start_datetime)
        sorted_expected = sorted(expected, key=lambda drr: drr.start_datetime)

        for i in range(len(results)):
            self.assertRrulesEqual(sorted_result[i].duration_rrule,
                                   sorted_expected[i].duration_rrule)

    def assertToPlainEqual(self, rrules, results):
        self.assertConvertEqual(rrules, results, convert_to_plain_form)

    def assertToConciseEqual(self, rrules, results):
        self.assertConvertEqual(rrules, results, convert_to_concise_form)

    def test_plain_to_concise(self):
        """
        Simple merge with gaps.
        """
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
        self.assertToConciseEqual([cont1, cont2], [result])

    def test_concise_to_plain(self):
        """
        Simple split due to exclusion rrule.
        """
        concise = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                             'UNTIL=20161030T235959;INTERVAL=1;'
                             'BYMINUTE=0;BYHOUR=3'),
                   'excluded': [
                       ('DTSTART:20161022\nRRULE:FREQ=DAILY;BYHOUR=3;'
                        'BYMINUTE=0;INTERVAL=1;UNTIL=20161023T235959')],
                   'duration': 30}
        cont1 = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161021T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        self.assertToPlainEqual([concise], [cont1, cont2])

    def test_mixed_concise_to_plain(self):
        """
        Split due to exclusion + pack additional single date.
        """
        concise = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                             'UNTIL=20161030T235959;INTERVAL=1;'
                             'BYMINUTE=0;BYHOUR=3'),
                   'excluded': [
                       ('DTSTART:20161022\nRRULE:FREQ=DAILY;BYHOUR=3;'
                        'BYMINUTE=0;INTERVAL=1;UNTIL=20161023T235959')],
                   'duration': 30}
        # sing_1 fits at the beginning of concise's exclusion
        sing_1 = {'duration': 30,
                  'rrule': ('DTSTART:20161022\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}

        cont1 = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161022T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        self.assertToPlainEqual([concise, sing_1], [cont1, cont2])

    def test_mixed_plain_to_concise(self):
        """
        Pack with gaps two continuous rules, one of the continuous
        rule already has an exclusion.
        """
        cont1 = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161021T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'excluded': [
                     ('DTSTART:20161018\nRRULE:FREQ=DAILY;BYHOUR=3;'
                      'BYMINUTE=0;COUNT=1')],
                 'duration': 30}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        result = {'rrule': ('DTSTART:20161001\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'excluded': [
                      ('DTSTART:20161018\nRRULE:FREQ=DAILY;BYHOUR=3;'
                       'BYMINUTE=0;COUNT=1'),
                      ('DTSTART:20161022\nRRULE:FREQ=DAILY;BYHOUR=3;'
                       'BYMINUTE=0;INTERVAL=1;UNTIL=20161023T235959')],
                  'duration': 30}
        self.assertToConciseEqual([cont1, cont2], [result])
