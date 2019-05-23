# -*- coding: utf-8 -*-

""" Functional tests on datection.combine.split """
import unittest
import six
from datection.combine.split import split_schedules
from datection.combine.split import split_short_continuous_schedules
from datetime import date


class TestSplit(unittest.TestCase):

    def assertRruleStrEqual(self, rrule_str1, rrule_str2):
        new_rrule_lines = rrule_str1.splitlines()
        result_lines = rrule_str2.splitlines()
        self.assertEqual(new_rrule_lines[0], result_lines[0])
        new_details = new_rrule_lines[1].split(":")[1].split(";")
        res_details = result_lines[1].split(":")[1].split(";")
        six.assertCountEqual(self, new_details, res_details)

    def test_only_past(self):
        reference = date(2016, 10, 24)
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        pasts, futures = split_schedules([cont], reference)
        self.assertEqual(len(pasts), 1)
        self.assertEqual(len(futures), 0)

    def test_only_future(self):
        reference = date(2016, 10, 10)
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        pasts, futures = split_schedules([cont], reference)
        self.assertEqual(len(pasts), 0)
        self.assertEqual(len(futures), 1)

    def test_split(self):
        reference = date(2016, 10, 15)
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        pasts, futures = split_schedules([cont], reference)
        self.assertEqual(len(pasts), 1)
        self.assertRruleStrEqual(pasts[0]['rrule'],
                                 ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                                  'UNTIL=20161014T235959;INTERVAL=1;'
                                  'BYMINUTE=0;BYHOUR=3'))

        self.assertEqual(len(futures), 1)
        self.assertRruleStrEqual(futures[0]['rrule'],
                                 ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                                  'UNTIL=20161023T235959;INTERVAL=1;'
                                  'BYMINUTE=0;BYHOUR=3'))

    def test_split_short_continuous_schedules(self):
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161011T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        result = split_short_continuous_schedules([cont])
        self.assertEqual(len(result), 2)


    def test_no_split_short_continuous_schedules(self):
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161012T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30}
        result = split_short_continuous_schedules([cont])
        self.assertEqual(len(result), 1)

