# -*- coding: utf-8 -*-

"""Test suite of the french grammar."""

from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from datection.grammar.fr import DATE
from datection.grammar.fr import NUMERIC_DATE
from datection.grammar.fr import TIME
from datection.grammar.fr import TIME_INTERVAL
from datection.grammar.fr import TIME_PATTERN
from datection.grammar.fr import DATETIME
from datection.grammar.fr import PARTIAL_NUMERIC_DATE
from datection.grammar.fr import PARTIAL_LITTERAL_DATE
from datection.grammar.fr import PARTIAL_DATE
from datection.grammar.fr import DATE_LIST
from datection.grammar.fr import DATE_INTERVAL
from datection.grammar.fr import DATETIME_LIST
from datection.grammar.fr import DATETIME_PATTERN
from datection.grammar.fr import DATETIME_INTERVAL
from datection.grammar.fr import CONTINUOUS_DATETIME_INTERVAL
from datection.grammar.fr import WEEKDAY
from datection.grammar.fr import WEEKDAY_LIST
from datection.grammar.fr import WEEKDAY_INTERVAL
from datection.grammar.fr import WEEKDAY_PATTERN
from datection.grammar.fr import WEEKLY_RECURRENCE
from datection.grammar.fr import MULTIPLE_WEEKLY_RECURRENCE
from datection.timepoint import Date
from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import Datetime
from datection.timepoint import DatetimeList
from datection.timepoint import DateList
from datection.timepoint import DateInterval
from datection.timepoint import DatetimeInterval
from datection.timepoint import ContinuousDatetimeInterval
from datection.timepoint import Weekdays
from datection.timepoint import WeeklyRecurrence
from datection.test.test_grammar import TestGrammar
from datection.test.test_grammar import set_pattern


class TestDate(TestGrammar):

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


class TestNumericDate(TestGrammar):

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


class TestTime(TestGrammar):

    pattern = TIME

    def test_parse_time(self):
        self.assert_parse_equal(u'15h30', Time(15, 30))
        self.assert_parse_equal(u'15:30', Time(15, 30))

    def test_parse_time_no_minute(self):
        self.assert_parse_equal('15h', Time(15, 0))


class TestTimeInterval(TestGrammar):

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


class TestTimePattern(TestGrammar):

    pattern = TIME_PATTERN

    def test_parse_time_list_formats(self):
        self.assert_parse(u'à 18h, 19h30, et de 22h à 23h30')

    def test_parse_time_list(self):
        res = self.pattern.parseString(u'à 18h, 19h30, et de 22h à 23h30')
        self.assertEqual(
            list(res),
            [
                TimeInterval(Time(18, 0), Time(18, 0)),
                TimeInterval(Time(19, 30), Time(19, 30)),
                TimeInterval(Time(22, 0), Time(23, 30))
            ])


class TestPartialDate(TestGrammar):

    pattern = PARTIAL_DATE

    @set_pattern(PARTIAL_LITTERAL_DATE)
    def test_parse_partial_litteral_date_formats(self):
        self.assert_parse(u'mars 2012')
        self.assert_parse(u'avril')

    @set_pattern(PARTIAL_LITTERAL_DATE)
    def test_parse_partial_litteral_date_full(self):
        self.assert_parse_equal(u'mars 2015', Date(2015, 3, None))

    @set_pattern(PARTIAL_LITTERAL_DATE)
    def test_parse_partial_litteral_date_missing_year(self):
        self.assert_parse_equal(u'mars', Date(None, 3, None))

    @set_pattern(PARTIAL_NUMERIC_DATE)
    def test_parse_partial_numeric_date_formats(self):
        self.assert_parse(u'02/2014')
        self.assert_parse(u'02/04')
        self.assert_parse(u'02/04/2014')

    @set_pattern(PARTIAL_NUMERIC_DATE)
    def test_parse_partial_numeric_date(self):
        self.assert_parse_equal(u'2/12', Date(2012, 2, None))
        self.assert_parse_equal(u'12/2012', Date(2012, 12, None))

    def test_parse_partial_date_formats(self):
        self.assert_parse(u'1er')
        self.assert_parse(u'2')
        self.assert_parse(u'2, ')
        self.assert_parse(u'2 avril')
        self.assert_parse(u'2 avril, ')
        self.assert_parse(u'2 avril, et')
        self.assert_parse(u'2 avril 2015')
        self.assert_parse(u'2/12, ')
        self.assert_parse(u'2/12, et')
        self.assert_parse(u'2/12/12, et')
        self.assert_parse(u'2/12/2012, et')

    def test_parse_partial_date(self):
        self.assert_parse_equal(u'5', Date(None, None, 5))
        self.assert_parse_equal(u'1er', Date(None, None, 1))
        self.assert_parse_equal(u'1er avril', Date(None, 4, 1))
        self.assert_parse_equal(u'01/02', Date(None, 2, 1))
        self.assert_parse_equal(u'1er mars 2015', Date(2015, 3, 1))
        self.assert_parse_equal(u'02/04/2014', Date(2014, 4, 2))


class TestDateList(TestGrammar):

    pattern = DATE_LIST

    def test_parse_date_list_formats(self):
        self.assert_parse(u"les 5, 6, 8 mars 2013")
        self.assert_parse(u"5, 6 et 8 mars 2013")
        self.assert_parse(u"Le 5, 6 et 8 mars")

    def test_parse_date_list(self):
        self.assert_parse_equal(
            u"5, 8, 10 mars 2015",
            DateList([Date(2015, 3, 5), Date(2015, 3, 8), Date(2015, 3, 10)]))


class TestDateInterval(TestGrammar):

    pattern = DATE_INTERVAL

    def test_parse_date_interval_formats(self):
        self.assert_parse(u"Du 5 au 7 octobre 2015")
        self.assert_parse(u"Du 5 septembre au 7 octobre 2015")
        self.assert_parse(u"du 5 septembre 2014 au 7 octobre 2015")
        self.assert_parse(u"5 septembre 2014 - 7 octobre 2015")
        self.assert_parse(u"Du 03/05/2014 au 03/05/2015")
        self.assert_parse(u"Du 3 au 05/05/2015")
        self.assert_parse(u"du 03/05/2014 au 03/05/2015")
        self.assert_parse(u"03/05/2014 - 03/05/2015")
        self.assert_parse(u"du 03/05 au 03/05/2015")
        self.assert_parse(u"du 03/05 au 5 mai 2015")

    def test_parse_date_interval_full(self):
        self.assert_parse_equal(
            u"Du 5 septembre 2014 au 7 octobre 2015",
            DateInterval(Date(2014, 9, 5), Date(2015, 10, 7)))
        self.assert_parse_equal(
            u"du 03/05/2014 au 03/05/2015",
            DateInterval(Date(2014, 5, 3), Date(2015, 5, 3)))
        self.assert_parse_equal(
            u"du 03/05 au 5 mai 2015",
            DateInterval(Date(2015, 5, 3), Date(2015, 5, 5)))

    def test_parse_date_interval_missing_start_year(self):
        self.assert_parse_equal(
            u"Du 5 septembre au 7 octobre 2015",
            DateInterval(Date(2015, 9, 5), Date(2015, 10, 7)))
        self.assert_parse_equal(
            u"du 03/05 au 03/05/2015",
            DateInterval(Date(2015, 5, 3), Date(2015, 5, 3)))
        self.assert_parse_equal(
            u"du 03/05 au 05 mai 2015",
            DateInterval(Date(2015, 5, 3), Date(2015, 5, 5)))

    def test_parse_date_interval_missing_start_year_month(self):
        self.assert_parse_equal(
            u"Du 5 au 7 octobre 2015",
            DateInterval(Date(2015, 10, 5), Date(2015, 10, 7)))
        self.assert_parse_equal(
            u"Du 3 au 05/05/2015",
            DateInterval(Date(2015, 5, 3), Date(2015, 5, 5)))


class TestDatetime(TestGrammar):

    pattern = DATETIME

    def test_parse_datetime_formats(self):
        self.assert_parse(u'Le 5 mars 2015 à 15h30')
        self.assert_parse(u'le 5 mars 2015 de 14h à 15h30')
        self.assert_parse(u'Le 5 mars 2015, à 15h30')
        self.assert_parse(u'Le 5 mars 2015, à partir de 15h30')
        self.assert_parse(u'Le 5 mars 2015 : 15h30')

    def test_parse_datetime(self):
        self.assert_parse_equal(
            u'5 mars 2015 à 15h30',
            Datetime(Date(2015, 3, 5), Time(15, 30)))
        self.assert_parse_equal(
            u'Le 5 mars 2015, à partir de 15h30',
            Datetime(Date(2015, 3, 5), Time(15, 30)))
        self.assert_parse_equal(
            u'Le 5 mars 2015 : 15h30',
            Datetime(Date(2015, 3, 5), Time(15, 30)))


class TestDatetimePattern(TestGrammar):

    pattern = DATETIME_PATTERN

    def test_parse_datetime_pattern_formats(self):
        self.assert_parse(
            u'Le 25 novembre 2012 à 20h, 22h30, et de 23h à 23h30')

    def test_parse_datetime_pattern(self):
        res = self.pattern.parseString(
            u'Le 25 novembre 2012 à 20h, 22h30, et de 23h à 23h30')
        self.assertEqual(
            list(res),
            [
                Datetime(Date(2012, 11, 25), Time(20, 0), Time(20, 0)),
                Datetime(Date(2012, 11, 25), Time(22, 30), Time(22, 30)),
                Datetime(Date(2012, 11, 25), Time(23, 0), Time(23, 30)),
            ])


class TestDatetimeList(TestGrammar):

    pattern = DATETIME_LIST

    def test_parse_datetime_list_formats(self):
        self.assert_parse(u"les 5, 6, 7 septembre 2014, à 15h20")
        self.assert_parse(u"les 5, 6, 7 septembre 2014, de 15h à 15h20")
        self.assert_parse(u"Les 5, 6, 7 septembre 2014, de 15h à 15h20")
        self.assert_parse(u"les 05/04/2014, et 06/05/2014, à 15h20")
        self.assert_parse(u"Les 05/04/2014, 06/05/2014, de 16h à 15h20")
        self.assert_parse(u"Les 05/04, 6 avril 2015, de 16h à 15h20")

    def test_parse_datetime_list_single_time(self):
        self.assert_parse_equal(
            u"les 5, 8, 10 mars 2015 à 18h",
            DatetimeList([
                Datetime(Date(2015, 3, 5), Time(18, 0)),
                Datetime(Date(2015, 3, 8), Time(18, 0)),
                Datetime(Date(2015, 3, 10), Time(18, 0)),
            ]
            ))
        self.assert_parse_equal(
            u"Les 05/04/2014, 06/04/2014, à 16h",
            DatetimeList([
                Datetime(Date(2014, 4, 5), Time(16, 0)),
                Datetime(Date(2014, 4, 6), Time(16, 0)),
            ]))
        self.assert_parse_equal(
            u"Les 05/04, 6 avril 2015, à 16h",
            DatetimeList([
                Datetime(Date(2015, 4, 5), Time(16, 0)),
                Datetime(Date(2015, 4, 6), Time(16, 0)),
            ]))

    def test_parse_datetime_list_time_interval(self):
        self.assert_parse_equal(
            u"les 5, 8, 10 mars 2015 de 16h à 18h",
            DatetimeList([
                Datetime(Date(2015, 3, 5), Time(16, 0), Time(18, 0)),
                Datetime(Date(2015, 3, 8), Time(16, 0), Time(18, 0)),
                Datetime(Date(2015, 3, 10), Time(16, 0), Time(18, 0)),
            ]
            ))
        self.assert_parse_equal(
            u"Les 05/04/2014, 06/04/2014, de 14h à 16h",
            DatetimeList([
                Datetime(Date(2014, 4, 5), Time(14, 0), Time(16, 0)),
                Datetime(Date(2014, 4, 6), Time(14, 0), Time(16, 0)),
            ]))
        self.assert_parse_equal(
            u"Les 05/04, 6 avril 2015, de 14h à 16h",
            DatetimeList([
                Datetime(Date(2015, 4, 5), Time(14, 0), Time(16, 0)),
                Datetime(Date(2015, 4, 6), Time(14, 0), Time(16, 0)),
            ]))


class TestDatetimeInterval(TestGrammar):

    pattern = DATETIME_INTERVAL

    def test_parse_datetime_interval_formats(self):
        self.assert_parse(u"Du 5 au 28 avril 2015 à 18h")
        self.assert_parse(u"Du 5 mars au 28 avril 2015 à 18h")
        self.assert_parse(u"Du 5 mars 2014  au 28 avril 2015 à 18h")
        self.assert_parse(u"Du 5 au 28 avril 2015 de 16h à 18h")
        self.assert_parse(u"Du 5 mars au 28 avril 2015 de 16h à 18h")
        self.assert_parse(u"Du 5 mars 2014  au 28 avril 2015 de 16h à 18h")
        self.assert_parse(u"Du 05/04/2015 au 28/04/2015 à 18h")
        self.assert_parse(u"Du 05/04/2015 au 28/04/2015 de 14h à 18h")
        self.assert_parse(u"Du 05/04 au 20 avril 2015 de 14h à 18h")

    def test_missing_end_date_year_raises_exception(self):
        with self.assertRaises(ValueError):
            self.pattern.parseString(u"Du 26 août au 29 septembre à 15h")

    def test_parse_datetime_interval(self):
        date_interval = DateInterval(Date(2015, 4, 5), Date(2015, 4, 28))
        time_interval = TimeInterval(Time(18, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 5 avril 2015 au 28 avril 2015 à 18h",
            DatetimeInterval(date_interval, time_interval))
        self.assert_parse_equal(
            u"Du 05/04/2015 au 28/04/2015 à 18h",
            DatetimeInterval(date_interval, time_interval))
        self.assert_parse_equal(
            u"Du 05/04/2015 au 28 avril 2015 à 18h",
            DatetimeInterval(date_interval, time_interval))

    def test_parse_datetime_interval_partial_dates(self):
        date_interval = DateInterval(Date(2015, 4, 5), Date(2015, 4, 28))
        time_interval = TimeInterval(Time(18, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 5 au 28 avril 2015 à 18h",
            DatetimeInterval(date_interval, time_interval))
        self.assert_parse_equal(
            u"Du 05/04 au 28/04/2015 à 18h",
            DatetimeInterval(date_interval, time_interval))
        self.assert_parse_equal(
            u"Du 05/04 au 28 avril 2015 à 18h",
            DatetimeInterval(date_interval, time_interval))

        date_interval = DateInterval(Date(2015, 3, 5), Date(2015, 4, 28))
        time_interval = TimeInterval(Time(14, 0), Time(18, 0))
        self.assert_parse_equal(
            u"Du 5 mars au 28 avril 2015 de 14h à 18h",
            DatetimeInterval(date_interval, time_interval))


class TestContinuousDatetimeInterval(TestGrammar):

    pattern = CONTINUOUS_DATETIME_INTERVAL

    def test_parse_continuous_datetime_interval_formats(self):
        self.assert_parse(u"Du 5 mars 2015 à 18h au 6 mars 2015 à 5h")
        self.assert_parse(u"5 mars 2015 à 18h - 6 mars 2015 à 5h")
        self.assert_parse(u"5 mars 2015 - 18h - 6 mars 2015 - 5h")
        self.assert_parse(u"5 mars - 18h - 6 mars 2015 - 5h")
        self.assert_parse(u"Du 05/03/2015 à 18h au 06/03/2015 à 5h")
        self.assert_parse(u"05/03/2015 à 18h - 06/03/2015 à 5h")
        self.assert_parse(u"5 mars 2015 - 18h - 06/03/2015 - 5h")

    def test_parse_continuous_datetime_interval(self):
        start_date = Date(2015, 3, 5)
        start_time = Time(18, 0)
        end_date = Date(2015, 3, 6)
        end_time = Time(5, 0)
        self.assert_parse_equal(
            u"Du 5 mars 2015 à 18h au 6 mars 2015 à 5h",
            ContinuousDatetimeInterval(
                start_date, start_time, end_date, end_time))
        self.assert_parse_equal(
            u"Du 5/3/2015 à 18h au 6 mars 2015 à 5h",
            ContinuousDatetimeInterval(
                start_date, start_time, end_date, end_time))
        self.assert_parse_equal(
            u"Du 5/3/2015 à 18h au 6/3/2015 à 5h",
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
        self.assert_parse_equal(
            u"Du 5/3 à 18h au 6 mars 2015 à 5h",
            ContinuousDatetimeInterval(
                start_date, start_time, end_date, end_time))
        self.assert_parse_equal(
            u"Du 5/3 à 18h au 6/3/2015 à 5h",
            ContinuousDatetimeInterval(
                start_date, start_time, end_date, end_time))


class TestWeekdayRecurrence(TestGrammar):

    pattern = WEEKLY_RECURRENCE

    @set_pattern(WEEKDAY)
    def test_parse_weekday_formats(self):
        self.assert_parse(u"lundi")
        self.assert_parse(u"lundis")

    def test_parse_weekday_span(self):
        self.assertEqual(WEEKDAY.parseString(u"lundi")[0], MO)
        self.assertEqual(WEEKDAY.parseString(u"mardi")[0], TU)
        self.assertEqual(WEEKDAY.parseString(u"mercredi")[0], WE)
        self.assertEqual(WEEKDAY.parseString(u"jeudi")[0], TH)
        self.assertEqual(WEEKDAY.parseString(u"vendredi")[0], FR)
        self.assertEqual(WEEKDAY.parseString(u"samedi")[0], SA)
        self.assertEqual(WEEKDAY.parseString(u"dimanche")[0], SU)

    @set_pattern(WEEKDAY_LIST)
    def test_parse_weekday_list_formats(self):
        self.assert_parse(u"le lundi")
        self.assert_parse(u"les lundis")
        self.assert_parse(u"les lundis, mardi, et mercredis")

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
    def test_parse_weekday_interval(self):
        self.assert_parse_equal(
            u"du lundi au mercredi", Weekdays([MO, TU, WE]))

    @set_pattern(WEEKDAY_PATTERN)
    def test_parse_weekday_pattern_formats(self):
        self.assert_parse(u"le lundi")
        self.assert_parse(u"les lundis")
        self.assert_parse(u"les lundis, mardi, et mercredis")
        self.assert_parse(u"du lundi au mercredi")

    @set_pattern(WEEKDAY_PATTERN)
    def test_parse_weekday_pattern(self):
        self.assert_parse_equal(u"le lundi", Weekdays([MO]))
        self.assert_parse_equal(u"les lundis", Weekdays([MO]))
        self.assert_parse_equal(
            u"les lundis, mardi, et mercredis", Weekdays([MO, TU, WE]))
        self.assert_parse_equal(
            u"du lundi au mercredi", Weekdays([MO, TU, WE]))

    def test_parse_weekly_recurrence1_formats(self):
        self.assert_parse(
            u"du lundi au vendredi, du 2 au 29 mars 2015, de 8h à 10h")
        self.assert_parse(u"le vendredi, du 2 au 29 mars 2015, à 10h")

    def test_parse_weekly_recurrence1(self):
        self.assert_parse_equal(
            u"du lundi au vendredi, du 2 au 29 mars 2015, de 8h à 10h",
            WeeklyRecurrence(
                DateInterval(Date(2015, 3, 2), Date(2015, 3, 29)),
                TimeInterval(Time(8, 0), Time(10, 0)),
                [MO, TU, WE, TH, FR]))
        self.assert_parse_equal(
            u"le vendredi, du 2 au 29 mars 2015, à 10h",
            WeeklyRecurrence(
                DateInterval(Date(2015, 3, 2), Date(2015, 3, 29)),
                TimeInterval(Time(10, 0), Time(10, 0)),
                [FR]))

    def test_parse_weekly_recurrence2_formats(self):
        self.assert_parse(
            u"du lundi au vendredi, de 8h à 10h, du 2 au 29 mars 2015, ")
        self.assert_parse(u"le vendredi à 10h, du 2 au 29 mars 2015")

    def test_parse_weekly_recurrence2(self):
        self.assert_parse_equal(
            u"du lundi au vendredi, de 8h à 10h, du 2 au 29 mars 2015, ",
            WeeklyRecurrence(
                DateInterval(Date(2015, 3, 2), Date(2015, 3, 29)),
                TimeInterval(Time(8, 0), Time(10, 0)),
                [MO, TU, WE, TH, FR]))
        self.assert_parse_equal(
            u"le vendredi à 10h, du 2 au 29 mars 2015",
            WeeklyRecurrence(
                DateInterval(Date(2015, 3, 2), Date(2015, 3, 29)),
                TimeInterval(Time(10, 0), Time(10, 0)),
                [FR]))

    def test_parse_weekly_recurrence3_formats(self):
        self.assert_parse(
            u"Du 2 au 29 mars 2015 de 8h à 10h, du lundi au vendredi")
        self.assert_parse(u"du 2 au 29 mars 2015 à 10h, le vendredi")

    def test_parse_weekly_recurrence3(self):
        self.assert_parse_equal(
            u"Du 2 au 29 mars 2015 de 8h à 10h, du lundi au vendredi",
            WeeklyRecurrence(
                DateInterval(Date(2015, 3, 2), Date(2015, 3, 29)),
                TimeInterval(Time(8, 0), Time(10, 0)),
                [MO, TU, WE, TH, FR]))
        self.assert_parse_equal(
            u"du 2 au 29 mars 2015 à 10h, le vendredi",
            WeeklyRecurrence(
                DateInterval(Date(2015, 3, 2), Date(2015, 3, 29)),
                TimeInterval(Time(10, 0), Time(10, 0)),
                [FR]))

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

    @set_pattern(MULTIPLE_WEEKLY_RECURRENCE)
    def test_parse_multiple_weekly_recurrence_formats(self):
        self.assert_parse(
            u"""Du 29/03/15 au 02/04/15 - Mardi, mercredi samedi 16h-19h,
            lundi à 18h""")
        self.assert_parse(
            u"""Du 29/03/15 au 02/04/15 - Mardi, mercredi samedi 16h-19h,
            lundi à 18h, dimanche à 20h30""")

    @set_pattern(MULTIPLE_WEEKLY_RECURRENCE)
    def test_parse_multiple_weekly_recurrence(self):
        wk1 = WeeklyRecurrence(
            date_interval=DateInterval(Date(2015, 3, 29), Date(2015, 4, 2)),
            time_interval=TimeInterval(Time(16, 0), Time(19, 0)),
            weekdays=Weekdays([TU, WE, SA]))
        wk2 = WeeklyRecurrence(
            date_interval=DateInterval(Date(2015, 3, 29), Date(2015, 4, 2)),
            time_interval=TimeInterval(Time(18, 0), Time(18, 0)),
            weekdays=Weekdays([MO]))
        wk3 = WeeklyRecurrence(
            date_interval=DateInterval(Date(2015, 3, 29), Date(2015, 4, 2)),
            time_interval=TimeInterval(Time(20, 30), Time(20, 30)),
            weekdays=Weekdays([SU]))
        self.assertListEqual(
            list(self.pattern.parseString(
                u"""Du 29/03/15 au 02/04/15 - Mardi, mercredi samedi 16h-19h,
                lundi à 18h""")),
            [wk1, wk2])
        self.assertListEqual(
            list(self.pattern.parseString(
                u"""Du 29/03/15 au 02/04/15 - Mardi, mercredi samedi 16h-19h,
                lundi à 18h, dimanche à 20h30""")),
            [wk1, wk2, wk3])
