    # -*- coding: utf-8 -*-

"""Functional tests on the output of the datection.parse high level function."""

import unittest

from datetime import datetime, date
from dateutil.rrule import TU, WE, TH, FR

from datection import parse
from datection.models import DurationRRule
from datection.timepoint import Date
from datection.timepoint import Datetime
from datection.timepoint import Time
from datection.timepoint import WeeklyRecurrence


class TestParse(unittest.TestCase):

    """Test suite of the datection.parse function."""

    lang = 'fr'

    def assert_generates(self, text, datetimes):
        schedules = [tp.export() for tp in parse(text, self.lang)]
        generated_datetimes = []
        for schedule in schedules:
            if isinstance(schedule, list):
                for item in schedule:
                    generated_datetimes.extend(list(DurationRRule(item)))
            else:
                generated_datetimes.extend(list(DurationRRule(schedule)))
        self.assertItemsEqual(generated_datetimes, datetimes)

    def test_date(self):
        self.assert_generates(u"Le 5 mars 2015", [datetime(2015, 3, 5, 0, 0)])

    def test_datetime(self):
        self.assert_generates(
            u"Le 5 mars 2015 à 18h30", [datetime(2015, 3, 5, 18, 30)])

        self.assert_generates(
            u"Le 5 mars 2015.\nA 18h30", [datetime(2015, 3, 5, 18, 30)])

    def test_numeric_datetime(self):
        self.assert_generates(
            u"03/12/2013 18:30", [datetime(2013, 12, 3, 18, 30)])
        self.assert_generates(
            u"06.03.2016 15h00", [datetime(2016, 3, 6, 15, 0)])

    def test_datetime_with_time_interval(self):
        self.assert_generates(
            u"Le 5 mars 2015 de 16h à 18h30", [
                datetime(2015, 3, 5, 16, 0),
            ])
        self.assert_generates(
            u"Le 5 mars 2015. De 16h à 18h30", [datetime(2015, 3, 5, 16, 0)])

    def test_datetime_with_several_time_intervals(self):
        self.assert_generates(
            u"Le 5 mars 2015, 16h-18h30 et 19h-20h30", [
                datetime(2015, 3, 5, 16, 0),
                datetime(2015, 3, 5, 19, 0),
            ])

    def test_date_list(self):
        self.assert_generates(
            u"Les 5, 6, 7 et 11 août 2014",
            [
                datetime(2014, 8, 5, 0, 0),
                datetime(2014, 8, 6, 0, 0),
                datetime(2014, 8, 7, 0, 0),
                datetime(2014, 8, 11, 0, 0),
            ])

    def test_multi_datetime(self):
        self.assert_generates(
            u"Le 25 septembre 2015 à 20 h et 11 novembre 2015 à 21 h",
            [
                datetime(2015, 9, 25, 20, 0),
                datetime(2015, 11, 11, 21, 0),
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
                datetime(2013, 12, 6, 0, 0),
                datetime(2013, 12, 7, 0, 0),
                datetime(2013, 12, 8, 0, 0),
                datetime(2013, 12, 9, 0, 0),
            ])

        self.assert_generates(
            u"du 16 janvier jusqu'au 19 janvier 2015",
            [
                datetime(2015, 1, 16, 0, 0),
                datetime(2015, 1, 17, 0, 0),
                datetime(2015, 1, 18, 0, 0),
                datetime(2015, 1, 19, 0, 0),
            ])

        self.assert_generates(
            u"de mercredi 16 jusqu'à samedi 19 mars 2015",
            [
                datetime(2015, 3, 16, 0, 0),
                datetime(2015, 3, 17, 0, 0),
                datetime(2015, 3, 18, 0, 0),
                datetime(2015, 3, 19, 0, 0),
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

    def test_datetime_interval_with_multiple_weekday_exception(self):
        self.assert_generates(
            u"Du 6 au 15 décembre 2014 à 23h, sauf le mardi et le jeudi",
            [
                datetime(2014, 12, 6,   23, 0),
                datetime(2014, 12, 7,   23, 0),
                datetime(2014, 12, 8,   23, 0),
                datetime(2014, 12, 10,  23, 0),
                datetime(2014, 12, 12,  23, 0),
                datetime(2014, 12, 13,  23, 0),
                datetime(2014, 12, 14,  23, 0),
                datetime(2014, 12, 15,  23, 0),
            ])

    def test_datetime_interval_with_weekday_exception_time(self):
        self.assert_generates(
            u"Du 6 au 15 décembre 2014 à 23h, sauf le mardi à 22h",
            [
                datetime(2014, 12, 6,   23, 0),
                datetime(2014, 12, 7,   23, 0),
                datetime(2014, 12, 8,   23, 0),
                datetime(2014, 12, 9,   22, 0),
                datetime(2014, 12, 10,  23, 0),
                datetime(2014, 12, 11,  23, 0),
                datetime(2014, 12, 12,  23, 0),
                datetime(2014, 12, 13,  23, 0),
                datetime(2014, 12, 14,  23, 0),
                datetime(2014, 12, 15,  23, 0),
            ])

    def test_datetime_interval_with_weekday_multiple_exception_time(self):
        self.assert_generates(
            u"Du 6 au 12 décembre 2014 à 23h, sauf le mardi à 22h et le jeudi à 21h",
            [
                datetime(2014, 12, 6,   23, 0),
                datetime(2014, 12, 7,   23, 0),
                datetime(2014, 12, 8,   23, 0),
                datetime(2014, 12, 9,   22, 0),
                datetime(2014, 12, 10,  23, 0),
                datetime(2014, 12, 11,  21, 0),
                datetime(2014, 12, 12,  23, 0),
            ])

    def test_datetime_interval_with_weekday_exception_time_transfer(self):
        self.assert_generates(
            u"Du lundi au vendredi, du 6 au 15 décembre 2014 sauf le mardi à 23h",
            [
                datetime(2014, 12, 8,   23, 0),
                datetime(2014, 12, 10,  23, 0),
                datetime(2014, 12, 11,  23, 0),
                datetime(2014, 12, 12,  23, 0),
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

        self.assert_generates(
            u'séance les jeudis et vendredi, du 6 au 15 décembre 2014,à 11h et 12h',
            [
                datetime(2014, 12, 11, 11, 0),
                datetime(2014, 12, 12, 11, 0),
                datetime(2014, 12, 11, 12, 0),
                datetime(2014, 12, 12, 12, 0),
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

    def test_weekday_list(self):
        wks = parse(
            u"Le mardi et mercredi, de 10 h à 19 h 30",
            "fr",
            valid=False)
        self.assertEqual(len(wks), 1)
        wk = wks[0]
        self.assertEqual(wk.weekdays, [TU, WE])

    def test_date_interval_multi_weekdays(self):
        wks = parse(
            "Du 05-02-2015 au 06-02-2015 - jeu. à 19h | ven. à 20h30",
            "fr")
        self.assertEqual(len(wks), 2)
        self.assertEqual(wks[1].weekdays, [FR])
        self.assertEqual(wks[0].weekdays, [TH])

    def test_datetime_pattern(self):
        self.assert_generates(
            u"15-12-2015 - 11h & 16h",
            [
                datetime(2015, 12, 15, 11, 0),
                datetime(2015, 12, 15, 16, 0)
            ])
        self.assert_generates(
            u'Samedi 1 Juin 2014 de 11h à 13h et de 14h à 17h',
            [datetime(2014, 6, 1, 11, 0), datetime(2014, 6, 1, 14, 0)])

    def test_expression_morning(self):
        dt = [tp for tp in parse(u"Le 5 mars 2015, le matin", "fr")
              if isinstance(tp, Datetime)][0]
        self.assertEqual(dt.start_time, Time(8, 0))
        self.assertEqual(dt.end_time, Time(12, 0))

    def test_expression_day(self):
        dt = [tp for tp in parse(u"Le 5 mars 2015, en soirée", "fr")
              if isinstance(tp, Datetime)][0]
        self.assertEqual(dt.start_time, Time(18, 0))
        self.assertEqual(dt.end_time, Time(22, 0))

    def test_expression_evening(self):
        dt = [tp for tp in parse(u"Le 5 mars 2015, en journée", "fr")
              if isinstance(tp, Datetime)][0]
        self.assertEqual(dt.start_time, Time(8, 0))
        self.assertEqual(dt.end_time, Time(18, 0))

    def test_expression_midday(self):
        dt = [tp for tp in parse(u"Le 5 mars 2015, à midi", "fr")
              if isinstance(tp, Datetime)][0]
        self.assertEqual(dt.start_time, Time(12, 0))
        self.assertEqual(dt.end_time, Time(12, 0))

    def test_expression_midnight(self):
        dt = [tp for tp in parse(u"Le 5 mars 2015, à minuit", "fr")
              if isinstance(tp, Datetime)][0]
        self.assertEqual(dt.start_time, Time(23, 59))
        self.assertEqual(dt.end_time, Time(23, 59))

    def test_expression_every_day(self):
        wk = [tp for tp in parse(u"Du 5 au 18 mars 2015, tous les jours", "fr")
              if isinstance(tp, WeeklyRecurrence)][0]
        self.assertEqual(len(wk.weekdays), 7)

    def test_accented_uppercase_date(self):
        self.assert_generates(u"sam 21 FÉVRIER 2015 20H00", [datetime(2015, 2, 21, 20, 0)])

    def test_yesgolive_tricky_date(self):
        text = u'Mar 28, 2014 8:00 PM \u2013 9:55 PM'
        self.assert_generates(
            text,
            [datetime(2014, 3, 28, 20, 0)]
        )

    def test_long_text(self):
        text = u'Short text 12.03.2016'
        self.assertEqual(parse(text, 'fr')[0].span, (11, 21))

        text = u'Long text is looooooooooooooooooooooooooooooooooooooooooong 12.04.2016'
        self.assertEqual(parse(text, 'fr')[0].span, (60, 70))

    def test_slash_separator(self):
        text = u'01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2015 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016 / 01/11/2016'
        res = parse(text, 'fr')
        self.assertEqual(len(res), 2)
        self.assertIsInstance(res[0], Date)


class TestYearLessExpressions(unittest.TestCase):

    """Test the behaviour of the parser when the year of the timempoints
    is the specified in the text.

    """
    lang = 'fr'

    def test_parse_yearless_date(self):
        text = u"Le 5 mars"
        self.assertEqual(parse(text, self.lang), [])
        timepoints = parse(text, self.lang, reference=date(2015, 5, 1))
        d = timepoints[0]
        self.assertEqual(d.year, 2015)

    def test_parse_yearless_date_interval(self):
        text = u"Du 5 mars au 9 avril"
        timepoints = parse(text, self.lang, reference=date(2015, 5, 1))
        dt = timepoints[0]
        self.assertEqual(dt.start_date.year, 2015)
        self.assertEqual(dt.end_date.year, 2015)

    def test_parse_yearless_date_interval_separate_years(self):
        text = u"Du 5 mars au 9 février"
        timepoints = parse(text, self.lang, reference=date(2015, 5, 1))
        dt = timepoints[0]
        self.assertEqual(dt.start_date.year, 2014)
        self.assertEqual(dt.end_date.year, 2015)

    def test_parse_yearless_date_list(self):
        text = u"Le 5 et 12 février"
        timepoints = parse(text, self.lang, reference=date(2015, 5, 1))
        dt = timepoints[0]
        self.assertEqual(dt.dates[0].year, 2015)
        self.assertEqual(dt.dates[1].year, 2015)
