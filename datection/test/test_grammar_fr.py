# -*- coding: utf-8 -*-

"""Test suite of the french grammar."""

from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from datection.grammar.fr import DATE
from datection.grammar.fr import NUMERIC_DATE
from datection.grammar.fr import TIME
from datection.grammar.fr import TIME_INTERVAL
from datection.grammar.fr import TIME_PATTERN
from datection.grammar.fr import DATETIME
from datection.grammar.fr import PARTIAL_DATE
from datection.grammar.fr import DATE_LIST
from datection.grammar.fr import DATE_INTERVAL
from datection.grammar.fr import NUMERIC_DATE_INTERVAL
from datection.grammar.fr import DATETIME_LIST
from datection.grammar.fr import DATETIME_PATTERN
from datection.grammar.fr import NUMERIC_DATETIME_LIST
from datection.grammar.fr import DATETIME_INTERVAL
from datection.grammar.fr import NUMERIC_DATETIME_INTERVAL
from datection.grammar.fr import CONTINUOUS_DATETIME_INTERVAL
from datection.grammar.fr import NUMERIC_CONTINUOUS_DATETIME_INTERVAL
from datection.grammar.fr import WEEKDAY
from datection.grammar.fr import WEEKDAY_LIST
from datection.grammar.fr import WEEKDAY_INTERVAL
from datection.grammar.fr import WEEKDAY_PATTERN
from datection.grammar.fr import WEEKLY_RECURRENCE
from datection.grammar.fr import WEEKLY_RECURRENCE_1
from datection.grammar.fr import WEEKLY_RECURRENCE_2
from datection.grammar.fr import WEEKLY_RECURRENCE_3
from datection.models import Date
from datection.models import Time
from datection.models import TimeInterval
from datection.models import Datetime
from datection.models import DateInterval
from datection.models import DatetimeInterval
from datection.models import ContinuousDatetimeInterval
from datection.models import Weekdays
from datection.test.test_grammar import TestGrammar
from datection.test.test_grammar import set_pattern


class TestDateRegex(TestGrammar):

    pattern = DATE

    def test_parse_date(self):
        self.assert_parse_equal(u'le 1er janvier 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'Le 1er janvier 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'1er janvier 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'1er Janvier 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'1ER Janvier 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'2 mars 2015', Date(2015, 3, 2))

    def test_parse_date_with_abbreviated_names(self):
        self.assert_parse_equal(u'1er jan 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'1er Jan 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'Le 1er jan. 2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'2 mar 2015', Date(2015, 3, 2))
        self.assert_parse_equal(u'le 2 mar. 2015', Date(2015, 3, 2))

    def test_parse_date_missing_year(self):
        self.assert_parse_equal(u'1er janvier', Date(None, 1, 1))

    def test_parse_result_span(self):
        self.assert_span_equal(u'le 2 mar. 2015', (3, 14))


class TestNumericDateRegex(TestGrammar):

    pattern = NUMERIC_DATE

    def test_parse_numeric_date(self):
        self.assert_parse_equal(u'01/01/2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'01/01/15', Date(2015, 1, 1))
        self.assert_parse_equal(u'1/01/15', Date(2015, 1, 1))
        self.assert_parse_equal(u'1/1/15', Date(2015, 1, 1))
        self.assert_parse_equal(u'26/2', Date(None, 2, 26))

    def test_numeric_date_separators(self):
        self.assert_parse_equal(u'01/01/2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'01-01-2015', Date(2015, 1, 1))
        self.assert_parse_equal(u'01.01.2015', Date(2015, 1, 1))

    def test_parse_result_span(self):
        self.assert_span_equal(u'01/01/2015', (0, 10))


class TestTimeRegex(TestGrammar):

    pattern = TIME

    def test_parse_time(self):
        self.assert_parse_equal(u'15h30', Time(15, 30))
        self.assert_parse_equal(u'15:30', Time(15, 30))

    def test_parse_time_no_minute(self):
        self.assert_parse_equal('15h', Time(15, 0))

    def test_parse_result_span(self):
        self.assert_span_equal(u'15h30', (0, 5))
        self.assert_span_equal(u'15h', (0, 2))


class TestTimeIntervalRegex(TestGrammar):

    pattern = TIME_INTERVAL

    def test_parse_time_interval_formats(self):
        self.assert_parse(u'De 15h30 à 18h')
        self.assert_parse(u'de 15h30 à 18h')
        self.assert_parse(u'15h30 - 18h')
        self.assert_parse(u'Entre 15h30 et 18h')
        self.assert_parse(u'entre 15h30 et 18h')
        self.assert_parse(u'15h30')
        self.assert_parse(u'à 15h30')

    def test_parse_time(self):
        self.assert_parse_equal(
            u'de 15h30 à 18h', TimeInterval(Time(15, 30), Time(18, 0)))
        self.assert_parse_equal(
            u'15h30', TimeInterval(Time(15, 30), Time(15, 30)))

    def test_parse_result_span(self):
        self.assert_span_equal(u'de 15h à 15h30', (3, 14))
        self.assert_span_equal(u'de 15h30 à 16h', (3, 13))
        self.assert_span_equal(u'15h30', (0, 5))
        self.assert_span_equal(u'15h', (0, 2))


class TestTimePatternRegex(TestGrammar):

    pattern = TIME_PATTERN

    def test_parse_time_list_formats(self):
        self.assert_parse(u'à 18h, 19h30, et de 22h à 23h30')

    def test_parse_time_list(self):
        self.assert_parse_list_equal(
            u'à 18h, 19h30, et de 22h à 23h30',
            [
                TimeInterval(Time(18, 0), Time(18, 0)),
                TimeInterval(Time(19, 30), Time(19, 30)),
                TimeInterval(Time(22, 0), Time(23, 30))
            ])


class TestPartialDate(TestGrammar):

    pattern = PARTIAL_DATE

    def test_parse_date_in_list_formats(self):
        self.assert_parse(u'1er mars 2012')
        self.assert_parse(u'2 avril')
        self.assert_parse(u'5')
        self.assert_parse(u'1,')
        self.assert_parse(u'2 et')
        self.assert_parse(u'2 avril et')
        self.assert_parse(u'2 avril,')
        self.assert_parse(u'2 Avril,')
        self.assert_parse(u'2 avril 2015,')
        self.assert_parse(u'2 avril 2015 et')

    def test_parse_date_in_list_full(self):
        self.assert_parse_equal(u'1er mars 2015', Date(2015, 3, 1))

    def test_parse_date_in_list_missing_year(self):
        self.assert_parse_equal(u'1er mars', Date(None, 3, 1))

    def test_parse_date_in_list_missing_year_and_month(self):
        self.assert_parse_equal(u'1er', Date(None, None, 1))

    def test_parse_result_span(self):
        self.assert_span_equal(u'2 avril 2015 et', (0, 12))
        self.assert_span_equal(u'1er mars 2012', (0, 13))
        self.assert_span_equal(u'1er mars', (0, 7))
        self.assert_span_equal(u'1er', (0, 1))


class TestDateList(TestGrammar):

    pattern = DATE_LIST

    def test_parse_date_list_formats(self):
        self.assert_parse(u"les 5, 6, 8 mars 2013")
        self.assert_parse(u"5, 6 et 8 mars 2013")
        self.assert_parse(u"Le 5, 6 et 8 mars")
        self.assert_parse(u"Les 5, 6 et 8")

    def test_parse_date_list(self):
        self.assert_parse_equal(
            u"5, 8, 10 mars 2015",
            [Date(2015, 3, 5), Date(2015, 3, 8), Date(2015, 3, 10)])

    def test_parse_result_span(self):
        self.assert_span_equal(u"les 5, 6, 8 mars 2013", (4, 21))
        self.assert_span_equal(u"5, 6 et 8 mars 2013", (0, 19))
        self.assert_span_equal(u"Le 5, 6 et 8 mars", (3, 17))
        self.assert_span_equal(u"Les 5, 6 et 8", (4, 13))


class TestDateInterval(TestGrammar):

    pattern = DATE_INTERVAL

    def test_parse_date_interval_formats(self):
        self.assert_parse(u"Du 5 au 7 octobre 2015")
        self.assert_parse(u"Du 5 septembre au 7 octobre 2015")
        self.assert_parse(u"du 5 septembre 2014 au 7 octobre 2015")
        self.assert_parse(u"5 septembre 2014 - 7 octobre 2015")

    def test_parse_date_interval_full(self):
        self.assert_parse_equal(
            u"Du 5 septembre 2014 au 7 octobre 2015",
            DateInterval(Date(2014, 9, 5), Date(2015, 10, 7)))

    def test_parse_date_interval_missing_start_year(self):
        self.assert_parse_equal(
            u"Du 5 septembre au 7 octobre 2015",
            DateInterval(Date(2015, 9, 5), Date(2015, 10, 7)))

    def test_parse_date_interval_missing_start_year_month(self):
        self.assert_parse_equal(
            u"Du 5 au 7 octobre 2015",
            DateInterval(Date(2015, 10, 5), Date(2015, 10, 7)))

    def test_parse_result_span(self):
        self.assert_span_equal(u"Du 5 au 7 octobre 2015", (3, 22))
        self.assert_span_equal(u"Du 5 septembre au 7 octobre 2015", (3, 32))
        self.assert_span_equal(
            u"du 5 septembre 2014 au 7 octobre 2015", (3, 37))
        self.assert_span_equal(u"5 septembre 2014 - 7 octobre 2015", (0, 33))


class TestNumericDateInterval(TestGrammar):

    pattern = NUMERIC_DATE_INTERVAL

    def test_parse_numeric_date_interval_formats(self):
        self.assert_parse(u"Du 03/05/2014 au 03/05/2015")
        self.assert_parse(u"du 03/05/2014 au 03/05/2015")
        self.assert_parse(u"03/05/2014 - 03/05/2015")

    def test_parse_numeric_date_interval(self):
        self.assert_parse_equal(
            u"Du 03/05/2014 au 03/05/2015",
            DateInterval(Date(2014, 5, 3), Date(2015, 5, 3)))

    def test_parse_result_span(self):
        self.assert_span_equal(u"Du 03/05/2014 au 03/05/2015", (3, 27))
        self.assert_span_equal(u"du 03/05/2014 au 03/05/2015", (3, 27))
        self.assert_span_equal(u"03/05/2014 - 03/05/2015", (0, 23))


class TestDatetimeRegex(TestGrammar):

    pattern = DATETIME

    def test_parse_datetime_formats(self):
        self.assert_parse(u'Le 5 mars 2015 à 15h30')
        self.assert_parse(u'le 5 mars 2015 de 14h à 15h30')
        self.assert_parse(u'Le 5 mars 2015, à 15h30')

    def test_parse_datetime(self):
        self.assert_parse_equal(
            u'5 mars 2015 à 15h30',
            Datetime(Date(2015, 3, 5), Time(15, 30)))

    def test_parse_result_span(self):
        self.assert_span_equal(u'Le 5 mars 2015 à 15h30', (3, 22))
        self.assert_span_equal(u'le 5 mars 2015 de 14h à 15h30', (3, 29))
        self.assert_span_equal(u'Le 5 mars 2015, à 15h30', (3, 23))


class TestDatetimePatternRegex(TestGrammar):

    pattern = DATETIME_PATTERN

    def test_parse_datetime_pattern_formats(self):
        self.assert_parse(
            u'Le 25 novembre 2012 à 20h, 22h30, et de 23h à 23h30')

    def test_parse_datetime_pattern(self):
        self.assert_parse_list_equal(
            u'Le 25 novembre 2012 à 20h, 22h30, et de 23h à 23h30',
            [
                Datetime(Date(2012, 11, 25), Time(20, 0), Time(20, 0)),
                Datetime(Date(2012, 11, 25), Time(22, 30), Time(22, 30)),
                Datetime(Date(2012, 11, 25), Time(23, 0), Time(23, 30)),
            ])


class TestDatetimeListRegex(TestGrammar):

    pattern = DATETIME_LIST

    def test_parse_datetime_list_formats(self):
        self.assert_parse(u"les 5, 6, 7 septembre 2014, à 15h20")
        self.assert_parse(u"les 5, 6, 7 septembre 2014, de 15h à 15h20")
        self.assert_parse(u"Les 5, 6, 7 septembre 2014, de 15h à 15h20")

    def test_parse_datetime_list_single_time(self):
        self.assert_parse_equal(
            u"les 5, 8, 10 mars 2015 à 18h",
            [
                Datetime(Date(2015, 3, 5), Time(18, 0)),
                Datetime(Date(2015, 3, 8), Time(18, 0)),
                Datetime(Date(2015, 3, 10), Time(18, 0)),
            ]
        )

    def test_parse_datetime_list_time_interval(self):
        self.assert_parse_equal(
            u"les 5, 8, 10 mars 2015 de 16h à 18h",
            [
                Datetime(Date(2015, 3, 5), Time(16, 0), Time(18, 0)),
                Datetime(Date(2015, 3, 8), Time(16, 0), Time(18, 0)),
                Datetime(Date(2015, 3, 10), Time(16, 0), Time(18, 0)),
            ]
        )


class TestNumericDatetimeListRegex(TestGrammar):

    pattern = NUMERIC_DATETIME_LIST

    def test_parse_datetime_list_formats(self):
        self.assert_parse(u"les 05/04/2014, 06/05/2014, à 15h20")
        self.assert_parse(u"Les 05/04/2014, 06/05/2014, de 16h à 15h20")

    def test_parse_datetime_list_single_time(self):
        self.assert_parse_equal(
            u"les 05/04/2014, 06/04/2014, à 15h20",
            [
                Datetime(Date(2014, 4, 5), Time(15, 20)),
                Datetime(Date(2014, 4, 6), Time(15, 20)),
            ]
        )

    def test_parse_datetime_list_time_interval(self):
        self.assert_parse_equal(
            u"Les 05/04/2014, 06/04/2014, de 16h à 17h20",
            [
                Datetime(Date(2014, 4, 5), Time(16, 0), Time(17, 20)),
                Datetime(Date(2014, 4, 6), Time(16, 0), Time(17, 20)),
            ]
        )

    def test_parse_result_span(self):
        self.assert_span_equal(u"les 05/04/2014, 06/05/2014, à 15h20", (4, 35))
        self.assert_span_equal(
            u"Les 05/04/2014, 06/05/2014, de 16h à 15h20", (4, 42))


class TestDatetimeIntervalRegex(TestGrammar):

    pattern = DATETIME_INTERVAL

    def test_parse_datetime_interval_formats(self):
        self.assert_parse(u"Du 5 au 28 avril 2015 à 18h")
        self.assert_parse(u"Du 5 mars au 28 avril 2015 à 18h")
        self.assert_parse(u"Du 5 mars 2014  au 28 avril 2015 à 18h")
        self.assert_parse(u"Du 5 au 28 avril 2015 de 16h à 18h")
        self.assert_parse(u"Du 5 mars au 28 avril 2015 de 16h à 18h")
        self.assert_parse(u"Du 5 mars 2014  au 28 avril 2015 de 16h à 18h")

    def test_missing_end_date_year_raises_exception(self):
        with self.assertRaises(ValueError):
            self.pattern.parseString(u"Du 26 août au 29 septembre à 15h")

    def test_parse_datetime_interval(self):
        date_interval = DateInterval(Date(2015, 4, 5), Date(2015, 4, 28))
        time_interval = TimeInterval(Time(18, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 5 avril 2015 au 28 avril 2015 à 18h",
            DatetimeInterval(date_interval, time_interval))

    def test_parse_datetime_interval_partial_dates(self):
        date_interval = DateInterval(Date(2015, 4, 5), Date(2015, 4, 28))
        time_interval = TimeInterval(Time(18, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 5 au 28 avril 2015 à 18h",
            DatetimeInterval(date_interval, time_interval))

        date_interval = DateInterval(Date(2015, 3, 5), Date(2015, 4, 28))
        time_interval = TimeInterval(Time(14, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 5 mars au 28 avril 2015 de 14h à 18h",
            DatetimeInterval(date_interval, time_interval))

    def test_parse_result_span(self):
        self.assert_span_equal(u"Du 5 au 28 avril 2015 à 18h", (3, 26))
        self.assert_span_equal(u"Du 5 mars au 28 avril 2015 à 18h", (3, 31))
        self.assert_span_equal(
            u"Du 5 mars 2014  au 28 avril 2015 à 18h", (3, 37))
        self.assert_span_equal(u"Du 5 au 28 avril 2015 de 16h à 18h", (3, 33))
        self.assert_span_equal(
            u"Du 5 mars au 28 avril 2015 de 16h à 18h", (3, 38))
        self.assert_span_equal(
            u"Du 5 mars 2014  au 28 avril 2015 de 16h à 18h", (3, 44))


class TestNumericDatetimeIntervalRegex(TestGrammar):

    pattern = NUMERIC_DATETIME_INTERVAL

    def test_parse_datetime_interval_formats(self):
        self.assert_parse(u"Du 05/04/2015 au 28/04/2015 à 18h")
        self.assert_parse(u"Du 05/04/2015 au 28/04/2015 de 14h à 18h")

    def test_missing_end_date_year_raises_exception(self):
        with self.assertRaises(ValueError):
            self.pattern.parseString(u"26/05 au 29/06 à 15h")

    def test_parse_datetime_interval(self):
        date_interval = DateInterval(Date(2015, 4, 5), Date(2015, 4, 28))
        time_interval = TimeInterval(Time(18, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 05/04/2015  au 28/04/2015 à 18h",
            DatetimeInterval(date_interval, time_interval))

        time_interval = TimeInterval(Time(14, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 05/04/2015 au 28/04/2015 de 14h à 18h",
            DatetimeInterval(date_interval, time_interval))

    def test_parse_result_span(self):
        self.assert_span_equal(u"Du 05/04/2015 au 28/04/2015 à 18h", (3, 32))
        self.assert_span_equal(
            u"Du 05/04/2015 au 28/04/2015 de 14h à 18h", (3, 39))


class TestContinuousDatetimeInterval(TestGrammar):

    pattern = CONTINUOUS_DATETIME_INTERVAL

    def test_parse_continuous_datetime_interval_formats(self):
        self.assert_parse(u"Du 5 mars 2015 à 18h au 6 mars 2015 à 5h")
        self.assert_parse(u"5 mars 2015 à 18h - 6 mars 2015 à 5h")
        self.assert_parse(u"5 mars 2015 - 18h - 6 mars 2015 - 5h")
        self.assert_parse(u"5 mars - 18h - 6 mars 2015 - 5h")

    def test_parse_continuous_datetime_interval(self):
        start_date = Date(2015, 3, 5)
        start_time = Time(18, 0)
        end_date = Date(2015, 3, 6)
        end_time = Time(5, 0)
        self.assert_parse_equal(
            u"Du 5 mars 2015 à 18h au 6 mars 2015 à 5h",
            ContinuousDatetimeInterval(
                start_date, start_time, end_date, end_time))

    def test_parse_continuous_datetime_interval_partial_dates(self):
        start_date = Date(2015, 3, 5)
        start_time = Time(18, 0)
        end_date = Date(2015, 3, 6)
        end_time = Time(5, 0)
        self.assert_parse_equal(
            u"Du 5 mars à 18h au 6 mars 2015 à 5h",
            ContinuousDatetimeInterval(
                start_date, start_time, end_date, end_time))

    def test_parse_result_span(self):
        self.assert_span_equal(
            u"Du 5 mars 2015 à 18h au 6 mars 2015 à 5h", (3, 39))
        self.assert_span_equal(u"5 mars 2015 à 18h - 6 mars 2015 à 5h", (0, 35))
        self.assert_span_equal(u"5 mars 2015 - 18h - 6 mars 2015 - 5h", (0, 35))
        self.assert_span_equal(u"5 mars - 18h - 6 mars 2015 - 5h", (0, 30))


class TestNumericContinuousDatetimeInterval(TestGrammar):

    pattern = NUMERIC_CONTINUOUS_DATETIME_INTERVAL

    def test_parse_continuous_datetime_interval_formats(self):
        self.assert_parse(u"Du 05/03/2015 à 18h au 06/03/2015 à 5h")
        self.assert_parse(u"05/03/2015 à 18h - 06/03/2015 à 5h")
        self.assert_parse(u"05/03/2015 - 18h - 06/03/2015 - 5h")

    def test_parse_continuous_datetime_interval(self):
        start_date = Date(2015, 3, 5)
        start_time = Time(18, 0)
        end_date = Date(2015, 3, 6)
        end_time = Time(5, 0)
        self.assert_parse_equal(
            u"Du 05/03/2015 à 18h au 06/03/2015 à 5h",
            ContinuousDatetimeInterval(
                start_date, start_time, end_date, end_time))

    def test_parse_result_span(self):
        self.assert_span_equal(
            u"Du 05/03/2015 à 18h au 06/03/2015 à 5h", (3, 37))
        self.assert_span_equal(u"05/03/2015 à 18h - 06/03/2015 à 5h", (0, 33))
        self.assert_span_equal(u"05/03/2015 - 18h - 06/03/2015 - 5h", (0, 33))


class TestWeekdayRecurrence(TestGrammar):

    pattern = WEEKLY_RECURRENCE

    @set_pattern(WEEKDAY)
    def test_parse_weekday_formats(self):
        self.assert_parse(u"lundi")
        self.assert_parse(u"lundis")

    def test_parse_weekday_span(self):
        self.assertEqual(WEEKDAY.parseString(u"lundi")[0].value, MO)
        self.assertEqual(WEEKDAY.parseString(u"mardi")[0].value, TU)
        self.assertEqual(WEEKDAY.parseString(u"mercredi")[0].value, WE)
        self.assertEqual(WEEKDAY.parseString(u"jeudi")[0].value, TH)
        self.assertEqual(WEEKDAY.parseString(u"vendredi")[0].value, FR)
        self.assertEqual(WEEKDAY.parseString(u"samedi")[0].value, SA)
        self.assertEqual(WEEKDAY.parseString(u"dimanche")[0].value, SU)

    @set_pattern(WEEKDAY_LIST)
    def test_parse_weekday_list_formats(self):
        self.assert_parse(u"le lundi")
        self.assert_parse(u"les lundis")
        self.assert_parse(u"les lundis, mardi, et mercredis")

    @set_pattern(WEEKDAY_LIST)
    def test_parse_weekday_list_span(self):
        self.assert_span_equal(u"le lundi", (3, 8))
        self.assert_span_equal(u"les lundis", (4, 9))
        self.assert_span_equal(u"les lundis, mardi, et mercredis", (4, 30))

    @set_pattern(WEEKDAY_LIST)
    def test_parse_weekday_list(self):
        self.assert_parse_equal(u"le lundi", Weekdays([MO]))
        self.assert_parse_equal(u"les lundis", Weekdays([MO]))
        self.assert_parse_equal(
            u"les lundis, mardi, et mercredis", Weekdays([MO, TU, WE]))

    @set_pattern(WEEKDAY_INTERVAL)
    def test_parse_weekday_interval_formats(self):
        self.assert_parse(u"du lundi au mercredi")

    @set_pattern(WEEKDAY_INTERVAL)
    def test_parse_weekday_interval_span(self):
        self.assert_span_equal(u"du lundi au mercredi", (3, 20))

    @set_pattern(WEEKDAY_INTERVAL)
    def test_parse_weekday_interval(self):
        self.assert_parse_equal(
            u"du lundi au mercredi", Weekdays([MO, TU, WE]))

    @set_pattern(WEEKDAY_PATTERN)
    def test_parse_weekday_pattern(self):
        self.assert_parse(u"le lundi")
        self.assert_parse(u"les lundis")
        self.assert_parse(u"les lundis, mardi, et mercredis")
        self.assert_parse(u"du lundi au mercredi")

    @set_pattern(WEEKDAY_PATTERN)
    def test_parse_weekday_pattern_span(self):
        self.assert_span_equal(u"le lundi", (3, 8))
        self.assert_span_equal(u"les lundis", (4, 9))
        self.assert_span_equal(u"les lundis, mardi, et mercredis", (4, 30))
        self.assert_span_equal(u"du lundi au mercredi", (3, 20))

    @set_pattern(WEEKLY_RECURRENCE_1)
    def test_parse_weekly_recurrence1_formats(self):
        self.assert_parse(
            u"du lundi au vendredi, du 2 au 29 mars 2015, de 8h à 10h")
        self.assert_parse(u"le vendredi, du 2 au 29 mars 2015, à 10h")

    @set_pattern(WEEKLY_RECURRENCE_2)
    def test_parse_weekly_recurrence2_formats(self):
        self.assert_parse(
            u"du lundi au vendredi, de 8h à 10h, du 2 au 29 mars 2015, ")
        self.assert_parse(u"le vendredi à 10h, du 2 au 29 mars 2015")

    @set_pattern(WEEKLY_RECURRENCE_3)
    def test_parse_weekly_recurrence3_formats(self):
        self.assert_parse(
            u"Du 2 au 29 mars 2015 de 8h à 10h, du lundi au vendredi")
        self.assert_parse(u"du 2 au 29 mars 2015 à 10h, le vendredi")

    def test_parse_weekly_recurrence_formats(self):
        self.assert_parse(
            u"du lundi au vendredi, du 2 au 29 mars 2015, de 8h à 10h")
        self.assert_parse(u"le vendredi, du 2 au 29 mars 2015, à 10h")
        self.assert_parse(
            u"du lundi au vendredi, de 8h à 10h, du 2 au 29 mars 2015, ")
        self.assert_parse(u"le vendredi à 10h, du 2 au 29 mars 2015")
        self.assert_parse(
            u"Du 2 au 29 mars 2015 de 8h à 10h, du lundi au vendredi")
        self.assert_parse(u"du 2 au 29 mars 2015 à 10h, le vendredi")
