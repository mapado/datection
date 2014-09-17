# -*- coding: utf-8 -*-

"""Functional tests on the output of the datection.parse high level function."""

import unittest

from datetime import datetime

from datection import parse
from datection.models import DurationRRule


class TestParse(unittest.TestCase):

    """Test suite of the datection.parse function."""

    lang = 'fr'

    def assert_generates(self, text, datetimes):
        schedule = parse(text, self.lang)[0].export()
        generated_datetimes = []
        if isinstance(schedule, list):
            for item in schedule:
                generated_datetimes.extend(list(DurationRRule(item)))
        else:
            generated_datetimes = list(DurationRRule(schedule))
        self.assertListEqual(generated_datetimes, datetimes)

    def test_date(self):
        self.assert_generates(u"Le 5 mars 2015", [datetime(2015, 3, 5, 0, 0)])

    def test_datetime(self):
        self.assert_generates(
            u"Le 5 mars 2015 à 18h30", [datetime(2015, 3, 5, 18, 30)])

    def test_datetime_with_time_interval(self):
        self.assert_generates(
            u"Le 5 mars 2015 de 16h à 18h30", [datetime(2015, 3, 5, 16, 0)])

    def test_date_list(self):
        self.assert_generates(
            u"Les 5, 6, 7 et 11 août 2014",
            [
                datetime(2014, 8, 5, 0, 0),
                datetime(2014, 8, 6, 0, 0),
                datetime(2014, 8, 7, 0, 0),
                datetime(2014, 8, 11, 0, 0),
            ])

    def test_datetime_list(self):
        self.assert_generates(
            u"Les 5, 6, 7 et 11 août 2014 à 15h30",
            [
                datetime(2014, 8, 5, 15, 30),
                datetime(2014, 8, 6, 15, 30),
                datetime(2014, 8, 7, 15, 30),
                datetime(2014, 8, 11, 15, 30),
            ])

    def test_datetime_list_with_time_interval(self):
        self.assert_generates(
            u"Les 5, 6, 7 et 11 août 2014 de 15h30 à 18h",
            [
                datetime(2014, 8, 5, 15, 30),
                datetime(2014, 8, 6, 15, 30),
                datetime(2014, 8, 7, 15, 30),
                datetime(2014, 8, 11, 15, 30),
            ])

    def test_date_interval(self):
        self.assert_generates(
            u"Du 6 au 9 décembre 2013",
            [
                datetime(2013, 12, 6,  0, 0),
                datetime(2013, 12, 7,  0, 0),
                datetime(2013, 12, 8,  0, 0),
                datetime(2013, 12, 9, 0, 0),
            ])

    def test_date_interval_with_date_exception(self):
        self.assert_generates(
            u"Du 6 au 9 décembre 2013, sauf le 8 décembre",
            [
                datetime(2013, 12, 6,  0, 0),
                datetime(2013, 12, 7,  0, 0),
                datetime(2013, 12, 9, 0, 0),
            ])

    def test_date_interval_with_weekday_exception(self):
        self.assert_generates(
            u"Du 6 au 16 décembre 2014, sauf le lundi",
            [
                datetime(2014, 12, 6,  0, 0),
                datetime(2014, 12, 7,  0, 0),
                datetime(2014, 12, 9,  0, 0),
                datetime(2014, 12, 10,  0, 0),
                datetime(2014, 12, 11,  0, 0),
                datetime(2014, 12, 12,  0, 0),
                datetime(2014, 12, 13,  0, 0),
                datetime(2014, 12, 14,  0, 0),
                datetime(2014, 12, 16,  0, 0),
            ])

    def test_datetime_interval(self):
        self.assert_generates(
            u"Du 6 au 9 décembre 2013 à 20h30",
            [
                datetime(2013, 12, 6,  20, 30),
                datetime(2013, 12, 7,  20, 30),
                datetime(2013, 12, 8,  20, 30),
                datetime(2013, 12, 9,  20, 30),
            ])

    def test_datetime_interval_with_time_interval(self):
        self.assert_generates(
            u"Du 6 au 9 décembre 2013 de 20h30 à 23h",
            [
                datetime(2013, 12, 6,  20, 30),
                datetime(2013, 12, 7,  20, 30),
                datetime(2013, 12, 8,  20, 30),
                datetime(2013, 12, 9,  20, 30),
            ])

    def test_datetime_interval_with_date_exception(self):
        self.assert_generates(
            u"Du 6 au 9 décembre 2013 à 23h, sauf le 7 décembre",
            [
                datetime(2013, 12, 6,  23, 0),
                datetime(2013, 12, 8,  23, 0),
                datetime(2013, 12, 9,  23, 0),
            ])

    def test_datetime_interval_with_weekday_exception(self):
        self.assert_generates(
            u"Du 6 au 15 décembre 2014 à 23h, sauf le mardi",
            [
                datetime(2014, 12, 6,   23, 0),
                datetime(2014, 12, 7,   23, 0),
                datetime(2014, 12, 8,   23, 0),
                datetime(2014, 12, 10,  23, 0),
                datetime(2014, 12, 11,  23, 0),
                datetime(2014, 12, 12,  23, 0),
                datetime(2014, 12, 13,  23, 0),
                datetime(2014, 12, 14,  23, 0),
                datetime(2014, 12, 15,  23, 0),
            ])

    def test_weekly_recurrence(self):
        self.assert_generates(
            u"Du lundi au vendredi, du 5 au 15 décembre 2014, de 8h à 9h",
            [
                datetime(2014, 12, 5,  8, 0),
                datetime(2014, 12, 8,  8, 0),
                datetime(2014, 12, 9,  8, 0),
                datetime(2014, 12, 10,  8, 0),
                datetime(2014, 12, 11,  8, 0),
                datetime(2014, 12, 12,  8, 0),
                datetime(2014, 12, 15,  8, 0),
            ])

    def test_weekly_recurrence_with_date_exception(self):
        self.assert_generates(
            u"Du lundi au vendredi, du 5 au 15 décembre 2014, de 8h à 9h sauf le 12 décembre",
            [
                datetime(2014, 12, 5,  8, 0),
                datetime(2014, 12, 8,  8, 0),
                datetime(2014, 12, 9,  8, 0),
                datetime(2014, 12, 10,  8, 0),
                datetime(2014, 12, 11,  8, 0),
                datetime(2014, 12, 15,  8, 0),
            ])

    def test_weekly_recurrence_with_undefined_date_interval(self):
        wk = parse(u"le lundi", "fr", valid=False)[0]
        self.assertTrue(wk.date_interval.undefined)
        export = wk.export()
        self.assertTrue(export['unlimited'])
