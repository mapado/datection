    # -*- coding: utf-8 -*-

"""Functional tests on the output of the datection.parse high level function."""

import unittest

import six

from datetime import datetime, date
from dateutil.rrule import TU, WE, SA

from datection import parse
from datection.models import DurationRRule
from datection.timepoint import Date
from datection.timepoint import Datetime
from datection.timepoint import Time
from datection.timepoint import WeeklyRecurrence
from datection.timepoint import ContinuousDatetimeInterval
from datection.timepoint import DateInterval
from datection.timepoint import TimeInterval


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
        six.assertCountEqual(self, generated_datetimes, datetimes)

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
        self.assert_generates(
            u"Les 7, 8, 10, 11 juillet 2019 de 11 h 30 à 12 h 55",
            [
                datetime(2019, 7, 7, 11, 30),
                datetime(2019, 7, 8, 11, 30),
                datetime(2019, 7, 10, 11, 30),
                datetime(2019, 7, 11, 11, 30),
            ])

    def test_parse_double_list_date(self):
        self.assert_generates(
            u"Les 16-17 et 19-20 avril 2018",
            [
                datetime(2018, 4, 16, 0, 0),
                datetime(2018, 4, 17, 0, 0),
                datetime(2018, 4, 19, 0, 0),
                datetime(2018, 4, 20, 0, 0),
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
                datetime(2013, 12, 6, 0, 0),
                datetime(2013, 12, 7, 0, 0),
                datetime(2013, 12, 9, 0, 0),
            ])

    def test_date_interval_with_datelist_exception(self):
        self.assert_generates(
            u"Du 6 au 14 décembre 2013, sauf les 8,10,12 décembre",
            [
                datetime(2013, 12, 6, 0, 0),
                datetime(2013, 12, 7, 0, 0),
                datetime(2013, 12, 9, 0, 0),
                datetime(2013, 12, 11, 0, 0),
                datetime(2013, 12, 13, 0, 0),
                datetime(2013, 12, 14, 0, 0),
            ])
        self.assert_generates(
            u"Du 6 au 14 décembre 2013, sauf les 8,9,11 décembre",
            [
                datetime(2013, 12, 6, 0, 0),
                datetime(2013, 12, 7, 0, 0),
                datetime(2013, 12, 10, 0, 0),
                datetime(2013, 12, 12, 0, 0),
                datetime(2013, 12, 13, 0, 0),
                datetime(2013, 12, 14, 0, 0),
            ])

    def test_date_interval_with_recurrence_exception(self):
        self.assert_generates(
            u"du 6 au 14 juillet 2017 relache le lundi",
            [
                datetime(2017, 7, 6, 0, 0),
                datetime(2017, 7, 7, 0, 0),
                datetime(2017, 7, 8, 0, 0),
                datetime(2017, 7, 9, 0, 0),
                datetime(2017, 7, 11, 0, 0),
                datetime(2017, 7, 12, 0, 0),
                datetime(2017, 7, 13, 0, 0),
                datetime(2017, 7, 14, 0, 0),
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

    # TEMPORARY COMMENTED DUE TO REGRESSION
    # def test_date_interval_multi_weekdays(self):
    #     wks = parse(
    #         "Du 05-02-2015 au 06-02-2015 - jeu. à 19h | ven. à 20h30",
    #         "fr")
    #     self.assertEqual(len(wks), 2)
    #     self.assertNotEqual(wks[0].weekdays, wks[1].weekdays)
    #     self.assertIn(wks[1].weekdays[0], [TH, FR])
    #     self.assertIn(wks[0].weekdays[0], [TH, FR])

    def test_list_with_vertical_bars(self):
        self.assert_generates(
            u"17/06/2016 20:30|18/06/2016 20:30|19/06/2016 18:00",
            [
                datetime(2016, 6, 17, 20, 30),
                datetime(2016, 6, 18, 20, 30),
                datetime(2016, 6, 19, 18, 0),
            ])

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

    def test_numeric_datetime_pattern(self):
        self.assert_generates(
            u"Le 08/11/2017 : Mercredi de 20:30 à 23:00",
            [datetime(2017, 11, 8, 20, 30)])
        self.assert_generates(
            u"Le 08/11/2017 : Merc. de 20:30 à 23:00",
            [datetime(2017, 11, 8, 20, 30)])

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

    def test_timing_alone(self):
        text = u"ouvert de 10h à 18h."
        res = parse(text, "fr")
        self.assertEqual(len(res), 0)

    def test_timing_with_exclusion(self):
        text = u"ouvert de 10h à 18h. Fermé le dimanche"
        res = parse(text, "fr")
        self.assertEqual(len(res), 1)
        self.assertTrue(isinstance(res[0], WeeklyRecurrence))
        self.assertEqual(res[0].time_interval.start_time, Time(10,00))
        self.assertEqual(len(res[0].excluded), 1)

    def test_timing_away_from_date(self):
        text = u"Tous les jours.Blablablablablabla. De 9h45 à 13h."
        res = parse(text, "fr")[0]
        self.assertTrue(isinstance(res, WeeklyRecurrence))
        self.assertEqual(len(res.weekdays), 7)
        self.assertEqual(res.time_interval.start_time, Time(9,45))
        self.assertEqual(res.time_interval.end_time, Time(13,00))

    def test_standardized_pattern(self):
        text = u"du 2019-01-31 18:00:00 au 2019-01-31 20:00:00"
        results = parse(text, "fr")
        self.assertEqual(len(results), 1)
        self.assertTrue(isinstance(results[0], ContinuousDatetimeInterval))
        self.assertEqual(results[0].start_time, Time(18,00))
        self.assertEqual(results[0].end_time, Time(20,00))

    def test_long_text_complex_pattern(self):
        text = """Du 13/04/2017 à 23:30 au 14/04/2017 à 05:00\nDu 20/04/2017 à 23:30 au 21/04/2017 à 05:00\nDu 27/04/2017 à 23:30 au 28/04/2017 à 05:00\nDu 04/05/2017 à 23:30 au 05/05/2017 à 05:00\nDu 11/05/2017 à 23:30 au 12/05/2017 à 05:00\nDu 18/05/2017 à 23:30 au 19/05/2017 à 05:00\nDu 25/05/2017 à 23:30 au 26/05/2017 à 05:00\nDu 27/04/2017 à 23:30 au 28/04/2017 à 05:00"""
        result = parse(text, 'fr')
        self.assertEqual(len(result), 7)
        for res in result:
            self.assertTrue(isinstance(res, ContinuousDatetimeInterval))
            self.assertEqual(res.start_time, Time(23, 30))
            self.assertEqual(res.end_time, Time(5, 0))


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


class TestParseWeekly(unittest.TestCase):

    def test_pipe_pattern(self):
        date_interval = DateInterval(Date(2018, 3, 24), Date(2018, 11, 1))
        wk1 = WeeklyRecurrence(date_interval, TimeInterval(Time(14, 0), Time(18, 0)), [TU])
        wk2 = WeeklyRecurrence(date_interval, TimeInterval(Time(10, 0), Time(12, 0)), [TU])
        wk3 = WeeklyRecurrence(date_interval, TimeInterval(Time(10, 0), Time(12, 0)), [SA])
        schedule_description = "les mardis du 24/03/2018 au 01/11/2018 de 14:00 à 18:00 | les mardis du 24/03/2018 au 01/11/2018 de 10:00 à 12:00 | les samedis du 24/03/2018 au 01/11/2018 de 10:00 à 12:00"
        timepoints = parse(schedule_description, 'fr')
        self.assertListEqual(sorted(timepoints), sorted([wk1, wk2, wk3]))

    def test_multiline_pattern(self):
        date_interval = DateInterval(Date(2018, 3, 24), Date(2018, 11, 1))
        wk1 = WeeklyRecurrence(date_interval, TimeInterval(Time(14, 0), Time(18, 0)), [TU])
        wk2 = WeeklyRecurrence(date_interval, TimeInterval(Time(10, 0), Time(12, 0)), [TU])
        wk3 = WeeklyRecurrence(date_interval, TimeInterval(Time(10, 0), Time(12, 0)), [SA])
        schedule_description = """
            les mardis du 24/03/2018 au 01/11/2018 de 14:00 à 18:00
            les mardis du 24/03/2018 au 01/11/2018 de 10:00 à 12:00
            les samedis du 24/03/2018 au 01/11/2018 de 10:00 à 12:00
        """
        timepoints = parse(schedule_description, 'fr')
        self.assertListEqual(sorted(timepoints), sorted([wk1, wk2, wk3]))
