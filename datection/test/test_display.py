# -*- coding: utf-8 -*-

"""Test suite of the datection.display module."""

import unittest
import locale
import datetime
import datection

from datection.display import DateFormatter
from datection.display import DateIntervalFormatter
from datection.display import DateListFormatter
from datection.display import DatetimeFormatter
from datection.display import DatetimeIntervalFormatter
from datection.display import ContinuousDatetimeIntervalFormatter
from datection.display import TimeFormatter
from datection.display import TimeIntervalFormatter
from datection.display import WeekdayReccurenceFormatter
from datection.display import NextOccurenceFormatter
from datection.display import OpeningHoursFormatter
from datection.display import LongFormatter
from datection.display import NoFutureOccurence
from datection.display import groupby_consecutive_dates
from datection.display import groupby_date
from datection.display import groupby_time
from datection.display import consecutives
from datection.display import to_start_end_datetimes
from datection.display import display
from datection.models import DurationRRule


class TestDateFormatterfr_FR(unittest.TestCase):

    """Test suite of the DateFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        date = datetime.date(2013, 1, 1)
        self.dfmt = DateFormatter(date)

    def test_format_day_first(self):
        self.assertEqual(self.dfmt.format_day(), u'1er')

    def test_format_day(self):
        self.dfmt.date = datetime.date(2013, 1, 2)
        self.assertEqual(self.dfmt.format_day(), u'2')

    def test_format_dayname(self):
        self.assertEqual(self.dfmt.format_dayname(), u'mardi')

    def test_format_abbreviated_dayname(self):
        fmt = self.dfmt.format_dayname(abbrev=True)
        self.assertEqual(fmt, u'mar.')

    def test_format_month(self):
        self.assertEqual(self.dfmt.format_month(), u'janvier')

    def test_format_abbreviated_month(self):
        fmt = self.dfmt.format_month(abbrev=True)
        self.assertEqual(fmt, u'janv.')

    def test_format_year(self):
        self.assertEqual(self.dfmt.format_year(), u'2013')

    def test_format_abbreviated_year(self):
        fmt = self.dfmt.format_year(abbrev=True)
        self.assertEqual(fmt, u'13')

    def test_format_all_parts(self):
        fmt = self.dfmt.format_all_parts(
            include_dayname=True,
            abbrev_dayname=False,
            abbrev_monthname=False,
            abbrev_year=False,
            prefix='')
        self.assertEqual(fmt.strip(), u'mardi 1er janvier 2013')

        fmt = self.dfmt.format_all_parts(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=False,
            abbrev_year=False,
            prefix='le')
        self.assertEqual(fmt.strip(), u'le mar. 1er janvier 2013')

        fmt = self.dfmt.format_all_parts(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=True,
            abbrev_year=False,
            prefix='')
        self.assertEqual(fmt.strip(), u'mar. 1er janv. 2013')

        fmt = self.dfmt.format_all_parts(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=True,
            abbrev_year=True,
            prefix='le')
        self.assertEqual(fmt.strip(), u'le mar. 1er janv. 13')

    def test_format_no_year(self):
        fmt = self.dfmt.format_no_year(
            include_dayname=True,
            abbrev_dayname=False,
            abbrev_monthname=False,
            prefix='')
        self.assertEqual(fmt.strip(), u'mardi 1er janvier')

        fmt = self.dfmt.format_no_year(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=False,
            prefix='')
        self.assertEqual(fmt.strip(), u'mar. 1er janvier')

        fmt = self.dfmt.format_no_year(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=True,
            prefix='le')
        self.assertEqual(fmt.strip(), u'le mar. 1er janv.')

    def test_format_no_month_no_year(self):
        fmt = self.dfmt.format_no_month_no_year(
            include_dayname=True,
            abbrev_dayname=False,
            prefix='le')
        self.assertEqual(fmt.strip(), u'le mardi 1er')

        fmt = self.dfmt.format_no_month_no_year(
            include_dayname=True,
            abbrev_dayname=True,
            prefix='')
        self.assertEqual(fmt.strip(), u'mar. 1er')

    def test_display_with_reference(self):
        ref = datetime.date(2013, 1, 1)
        self.assertEqual(self.dfmt.display(reference=ref), u"aujourd'hui")

        ref = datetime.date(2012, 12, 31)
        self.assertEqual(self.dfmt.display(reference=ref), u"demain")

        ref = datetime.date(2012, 12, 28)
        self.assertEqual(self.dfmt.display(reference=ref), u"ce mardi")

    def test_display_full(self):
        self.assertEqual(self.dfmt.display(), u'1er janvier 2013')

    def test_display_abbreviated(self):
        self.assertEqual(
            self.dfmt.display(abbrev_dayname=True), u'mar. 1er janvier 2013')
        self.assertEqual(
            self.dfmt.display(abbrev_monthname=True), u'1er janv. 2013')
        self.assertEqual(
            self.dfmt.display(abbrev_year=True), u'1er janvier 13')

    def test_exclude_year(self):
        self.assertEqual(self.dfmt.display(include_year=False), u'1er janvier')

    def test_exclude_year_and_month(self):
        self.assertEqual(
            self.dfmt.display(include_year=False, include_month=False), u'1er')


class TestDateIntervalFormatterfr_FR(unittest.TestCase):

    """Test suite of the DateIntervalFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        start = datetime.date(2013, 11, 15)
        end = datetime.date(2013, 12, 15)
        self.difmt = DateIntervalFormatter(start, end)

    def test_display_same_day(self):
        self.difmt.end_date = datetime.date(2013, 11, 15)
        self.assertTrue(self.difmt.same_day_interval())
        self.assertEqual(self.difmt.display(), u'le 15 novembre 2013')

    def test_display_same_month(self):
        self.difmt.end_date = datetime.date(2013, 11, 17)
        self.assertTrue(self.difmt.same_month_interval())
        self.assertEqual(self.difmt.display(), u'du 15 au 17 novembre 2013')

    def test_display_same_year(self):
        self.difmt.end_date = datetime.date(2013, 12, 17)
        self.assertTrue(self.difmt.same_year_interval())
        self.assertEqual(
            self.difmt.display(), u'du 15 novembre au 17 décembre 2013')

    def test_display(self):
        self.difmt.end_date = datetime.date(2014, 12, 17)
        self.assertEqual(
            self.difmt.display(), u'du 15 novembre 2013 au 17 décembre 2014')


class TestDateListFormatterfr_FR(unittest.TestCase):

    """Test suite of the DateListFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        date_list = [
            datetime.date(2013, 3, 4),
            datetime.date(2013, 3, 5),
            datetime.date(2013, 3, 6),
            datetime.date(2013, 3, 9),
        ]
        self.dlfmt = DateListFormatter(date_list)

    def test_display(self):
        self.assertEqual(self.dlfmt.display(), u'les 4, 5, 6 et 9 mars 2013')

    def test_display_one_date(self):
        self.dlfmt.date_list = [datetime.date(2013, 3, 4)]
        self.assertEqual(self.dlfmt.display(), u'le 4 mars 2013')


class TestTimeFormatterfr_FR(unittest.TestCase):

    """Test suite of the TimeFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        time = datetime.time(12, 15)
        self.tfmt = TimeFormatter(time)

    def test_format_hour(self):
        self.assertEqual(self.tfmt.format_hour(), u'12')

    def test_format_minute(self):
        self.assertEqual(self.tfmt.format_minute(), u'15')

    def test_format_minute_zero(self):
        self.tfmt.time = datetime.time(12, 0)
        self.assertEqual(self.tfmt.format_minute(), u'')

    def test_display(self):
        self.assertEqual(self.tfmt.display(), u'12 h 15')

    def test_display_midnight(self):
        self.tfmt.time = datetime.time(0, 0)
        self.assertEqual(self.tfmt.display(), u'minuit')


class TestTimeIntervalfr_FR(unittest.TestCase):

    """Test suite of the TimeIntervalFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        start = datetime.time(12, 15)
        end = datetime.time(13, 0)
        self.tifmt = TimeIntervalFormatter(start, end)

    def test_display(self):
        self.assertEqual(self.tifmt.display(), u'de 12 h 15 à 13 h')

    def test_display_end_time_midnight(self):
        self.tifmt.end_time = datetime.time(0, 0)
        self.assertEqual(self.tifmt.display(), u'de 12 h 15 à minuit')

    def test_display_equal_bounds(self):
        self.tifmt.end_time = self.tifmt.start_time
        self.assertEqual(self.tifmt.display(), u'12 h 15')

    def test_display_all_day(self):
        start = datetime.time(0, 0)
        end = datetime.time(23, 59)
        tifmt = TimeIntervalFormatter(start, end)
        self.assertEqual(tifmt.display(), u'')


class TestDatetimeFormatterfr_FR(unittest.TestCase):

    """Test suite of the DatetimeFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        dt = datetime.datetime(2013, 3, 4, 12, 15)
        self.dtfmt = DatetimeFormatter(dt)

    def test_display(self):
        self.assertEqual(self.dtfmt.display(), u"le 4 mars 2013 à 12 h 15")

    def test_display_arg_passing(self):
        self.assertEqual(
            self.dtfmt.display(include_year=False), u"le 4 mars à 12 h 15")


class TestDatetimeIntervalFormatterfr_FR(unittest.TestCase):

    """Test suite of the DatetimeIntervalFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        start = datetime.datetime(2013, 3, 4, 12, 15)
        end = datetime.datetime(2013, 8, 5, 12, 15)
        self.dtifmt = DatetimeIntervalFormatter(start, end)

    def test_display_same_day(self):
        self.dtifmt.start_datetime = datetime.datetime(2013, 8, 5, 10, 15)
        self.assertEqual(
            self.dtifmt.display(), u'le 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_same_month(self):
        self.dtifmt.start_datetime = datetime.datetime(2013, 8, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_same_year(self):
        self.dtifmt.start_datetime = datetime.datetime(2013, 7, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er juillet au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display(self):
        self.dtifmt.start_datetime = datetime.datetime(2012, 7, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er juillet 2012 au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_single_time(self):
        self.dtifmt.start_datetime = datetime.datetime(2012, 7, 1, 12, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er juillet 2012 au 5 août 2013 à 12 h 15')

    def test_display_all_day(self):
        self.dtifmt.start_datetime = datetime.datetime(2013, 3, 4, 0, 0)
        self.dtifmt.end_datetime = datetime.datetime(2013, 8, 5, 23, 59)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 4 mars au 5 août 2013')


class TestContinuousDatetimeIntervalFormatterfr_FR(unittest.TestCase):

    """Test suite of the DatetimeIntervalFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        start = datetime.datetime(2013, 3, 4, 12, 15)
        end = datetime.datetime(2013, 8, 5, 12, 15)
        self.cdtifmt = ContinuousDatetimeIntervalFormatter(start, end)

    def test_display_same_year(self):
        self.assertEqual(
            self.cdtifmt.display(),
            u'du 4 mars à 12 h 15 au 5 août 2013 à 12 h 15')

    def test_display(self):
        self.cdtifmt.start = datetime.datetime(2012, 3, 4, 12, 15)
        self.assertEqual(
            self.cdtifmt.display(),
            u'du 4 mars 2012 à 12 h 15 au 5 août 2013 à 12 h 15')


class TestWeekdayReccurenceFormatter_fr_FR(unittest.TestCase):

    """Test suite of the WeekdayReccurenceFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        drr = {
            'duration': 60,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,SU;'
                      'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
        }
        self.wkfmt = WeekdayReccurenceFormatter(drr)

        drr = {
            'duration': 60,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
                      'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                      'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
        }
        self.wkfmt_alldays = WeekdayReccurenceFormatter(drr)

        drr = {
            'duration': 60,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
                      'BYDAY=MO,TU,WE;'
                      'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
        }
        self.wkfmt_continuous = WeekdayReccurenceFormatter(drr)

    def test_day_name(self):
        self.assertEqual(self.wkfmt.day_name(1), u'mardi')

    def test_all_weekdays(self):
        self.assertFalse(self.wkfmt.all_weekdays())

        self.assertTrue(self.wkfmt_alldays.all_weekdays())

    def test_format_discontinuous_weekday_interval(self):
        self.assertEqual(
            self.wkfmt.format_weekday_interval(),
            u'le lundi, mardi et dimanche')

    def test_format_continuous_weekday_interval(self):
        self.assertEqual(
            self.wkfmt_continuous.format_weekday_interval(),
            u'du lundi au mercredi')

    def test_format_date_interval(self):
        self.assertEqual(self.wkfmt.format_date_interval(),
                         u'du 7 au 31 août 2013')

    def test_format_time_interval(self):
        self.assertEqual(self.wkfmt.format_time_interval(),
                         u'de 22 h 30 à 23 h 30')

    def test_display(self):
        self.assertEqual(
            self.wkfmt.display(),
            (u'le lundi, mardi et dimanche, du 7 au 31 août 2013, '
                u'de 22 h 30 à 23 h 30'))
        self.assertEqual(
            self.wkfmt_alldays.display(),
            (u'du 7 au 31 août 2013, de 22 h 30 à 23 h 30'))

        self.assertEqual(
            self.wkfmt_continuous.display(),
            u'du lundi au mercredi, du 7 au 31 août 2013, de 22 h 30 à 23 h 30')


class TestNextOccurrencefr_FRFormatter(unittest.TestCase):

    """Test suite of the WeekdayReccurenceFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        schedule = [
            {
                'duration': 0,
                'rrule': ('DTSTART:20141112\nRRULE:FREQ=DAILY;BYHOUR=9;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141128T235959'),
                'span': (0, 30)
            }
        ]
        start = datetime.datetime(2014, 11, 10)
        end = datetime.datetime(2014, 11, 20)
        self.nofmt = NextOccurenceFormatter(schedule, start, end)

    def test_format_next_occurence(self):
        ref = datetime.datetime(2014, 10, 10)
        self.assertEqual(self.nofmt.display(ref), u'Le 12 novembre 2014 à 9 h')

    def test_format_next_occurence_soon(self):
        ref = datetime.datetime(2014, 11, 10)
        self.assertEqual(self.nofmt.display(ref), u'Ce mercredi à 9 h')

    def test_format_next_occurence_today(self):
        ref = datetime.datetime(2014, 11, 14)
        self.nofmt.start = datetime.datetime(2014, 11, 14)
        self.assertEqual(self.nofmt.display(ref), u"Aujourd'hui à 9 h")

    def test_format_next_occurence_past(self):
        self.nofmt.start = datetime.datetime(2015, 11, 10)
        self.nofmt.end = datetime.datetime(2015, 11, 20)
        ref = datetime.datetime(2014, 11, 15)
        with self.assertRaises(NoFutureOccurence):
            self.nofmt.display(ref)

    def test_format_next_occurence_and_summary(self):
        ref = datetime.datetime(2014, 10, 10)
        self.assertEqual(
            self.nofmt.display(ref, summarize=True),
            u'Le 12 novembre 2014 à 9 h + autres dates')

    def test_format_next_occurence_and_summary_all_day(self):
        schedule = [
            {
                'duration': 1439,
                'rrule': ('DTSTART:20141112\nRRULE:FREQ=DAILY;BYHOUR=0;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141128T235959'),
                'span': (0, 30)
            }
        ]
        start = datetime.datetime(2014, 11, 10)
        end = datetime.datetime(2014, 11, 20)
        nofmt = NextOccurenceFormatter(schedule, start, end)
        ref = datetime.datetime(2014, 10, 10)
        self.assertEqual(
            nofmt.display(ref, summarize=True),
            u'12 novembre 2014 + autres dates')


class TestOpeningHoursFormatterfr_FR(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        schedule = [
            {
                'duration': 480,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                'BYHOUR=10;BYMINUTE=0;UNTIL=20150117T235959'),
            },
            {
                'duration': 240,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                          'BYHOUR=14;BYMINUTE=0;UNTIL=20150117T235959'),
            },
            {
                'duration': 480,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=WE;'
                          'BYHOUR=10;BYMINUTE=0;UNTIL=20150117T235959'),
            },
            {
                'duration': 480,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=TH;'
                          'BYHOUR=10;BYMINUTE=0;UNTIL=20150117T235959'),
            },
            {
                'duration': 450,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=FR;'
                          'BYHOUR=10;BYMINUTE=30;UNTIL=20150117T235959'),
            },
            {
                'duration': 480,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=SA;'
                          'BYHOUR=10;BYMINUTE=0;UNTIL=20150117T235959'),
            },
            {
                'duration': 480,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=SU;'
                          'BYHOUR=10;BYMINUTE=0;UNTIL=20150117T235959'),
            }]
        self.ohfmt = OpeningHoursFormatter(schedule)

    def test_display_openings(self):
        fmt = self.ohfmt.format_openings(self.ohfmt.opening_hours[:2])
        expected = u"""Lundi de 10 h à 18 h et de 14 h à 18 h"""
        self.assertEqual(fmt, expected)

    def test_display(self):
        fmt = self.ohfmt.display()
        expected = u"""Lundi de 10 h à 18 h et de 14 h à 18 h
Mercredi de 10 h à 18 h
Jeudi de 10 h à 18 h
Vendredi de 10 h 30 à 18 h
Samedi de 10 h à 18 h
Dimanche de 10 h à 18 h"""
        self.assertEqual(fmt, expected)


class TestLongFormatter_fr_FR(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        schedule = [
            {'duration': 0,
             'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;BYHOUR=9;'
                       'BYMINUTE=0;INTERVAL=1;UNTIL=20140309T235959'),
             'span': (0, 24)},
            {'duration': 0,
             'rrule': ('DTSTART:20140226\nRRULE:FREQ=DAILY;COUNT=1;'
                       'BYMINUTE=0;BYHOUR=9'),
             'span': (49, 69)
             }
        ]
        self.fmt = LongFormatter(schedule)

    def test_display(self):
        self.assertEqual(
            self.fmt.display(),
            u'Le 26 février 2014, du 5 au 9 mars 2014, à 9 h')

    def test_display_weekday_reccurence(self):
        schedule = [
            {
                'duration': 480,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=SU;'
                          'BYHOUR=10;BYMINUTE=0;UNTIL=20150117T235959'),
            }
        ]
        fmt = LongFormatter(schedule)
        self.assertEqual(fmt.display(), u'Le dimanche, de 10 h à 18 h')


class TestDisplay_fr_FR(unittest.TestCase):

    def setUp(self):
        self.locale = 'fr_FR.UTF8'
        locale.setlocale(locale.LC_TIME, self.locale)

    def test_display_shortest(self):
        schedule = [
            {'duration': 1439,
             'rrule': ('DTSTART:20131215\nRRULE:FREQ=DAILY;COUNT=1;'
                       'BYMINUTE=0;BYHOUR=0'),
             'span': (3, 25)},
            {'duration': 1439,
             'rrule': ('DTSTART:20131216\nRRULE:FREQ=DAILY;COUNT=1;'
                       'BYMINUTE=0;BYHOUR=0'),
             'span': (3, 25)}
        ]
        start = datetime.datetime(2013, 12, 10)
        end = datetime.datetime(2013, 12, 17)
        reference = start
        short = NextOccurenceFormatter(schedule, start, end).display(
            reference, summarize=True)
        default = LongFormatter(schedule).display(abbrev_monthname=True)
        shortest_fmt = display(
            schedule,
            self.locale,
            short=True,
            shortest=False,
            bounds=(start, end),
            reference=reference)
        self.assertGreater(len(short), len(default))
        self.assertEqual(shortest_fmt, default)
        self.assertEqual(short,   u'Ce dimanche + autres dates')
        self.assertEqual(default, u'Du 15 au 16 déc. 2013')

    def test_display_recurrence(self):
        schedule = [
            {'duration': 60,
             'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                       'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959'),
             'span': (0, 48)}]
        start = datetime.datetime(2015, 3, 1)
        end = datetime.datetime(2015, 3, 17)
        reference = datetime.datetime(2015, 3, 1)
        short = NextOccurenceFormatter(schedule, start, end).display(
            reference, summarize=True)
        default = LongFormatter(schedule).display(abbrev_monthname=True)
        shortest_fmt = display(
            schedule,
            self.locale,
            short=True,
            shortest=False,
            bounds=(start, end),
            reference=reference)
        self.assertGreater(len(default), len(short))
        self.assertEqual(shortest_fmt, short)
        self.assertEqual(
            default,      u'Le mardi, du 5 au 26 mars 2015, de 8 h à 9 h')
        self.assertEqual(
            shortest_fmt, u'Le 10 mars 2015 de 8 h à 9 h + autres dates')

    def test_display_recurrence_no_summarize(self):
        schedule = [
            {'duration': 60,
             'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                       'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959'),
             'span': (0, 48)}]
        start = datetime.datetime(2015, 3, 1)
        end = datetime.datetime(2015, 3, 17)
        reference = datetime.datetime(2015, 3, 1)
        short = NextOccurenceFormatter(schedule, start, end).display(
            reference, summarize=False)
        default = LongFormatter(schedule).display(abbrev_monthname=True)
        shortest_fmt = display(
            schedule,
            self.locale,
            short=False,
            shortest=True,
            bounds=(start, end),
            reference=reference)
        self.assertGreater(len(default), len(short))
        self.assertEqual(shortest_fmt, short)
        self.assertEqual(
            default,      u'Le mardi, du 5 au 26 mars 2015, de 8 h à 9 h')
        self.assertEqual(
            shortest_fmt, u'Le 10 mars 2015 de 8 h à 9 h')

    def test_display_weekday_recurrence(self):
        sch = datection.to_db(u"Le samedi", "fr")
        self.assertEqual(display(sch, 'fr_FR.UTF8'), u'Le samedi')

    def test_display_weekday_recurrence_time(self):
        sch = datection.to_db(u"Le samedi à 15h30", "fr")
        self.assertEqual(display(sch, 'fr_FR.UTF8'), u'Le samedi, à 15 h 30')

    def test_display_weekday_recurrence_time_interval(self):
        sch = datection.to_db(u"Le samedi de 12 h 00 à 15h30", "fr")
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'), u'Le samedi, de 12 h à 15 h 30')

    def test_display_weekday_recurrence_list(self):
        sch = datection.to_db(u"Le lundi et samedi", "fr")
        self.assertEqual(display(sch, 'fr_FR.UTF8'), u'Le lundi et samedi')

    def test_display_weekday_recurrence_list_time(self):
        sch = datection.to_db(u"Le lundi et samedi à 15h30", "fr")
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'), u'Le lundi et samedi, à 15 h 30')

    def test_display_weekday_recurrence_list_time_interval(self):
        sch = datection.to_db(u"Le lundi et mardi de 14 h à 16 h 30", "fr")
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'), u'Le lundi et mardi, de 14 h à 16 h 30')

    def test_display_weekday_recurrence_interval(self):
        sch = datection.to_db(u"Du samedi au dimanche", "fr")
        self.assertEqual(display(sch, 'fr_FR.UTF8'), u'Le samedi et dimanche')

    def test_display_date(self):
        sch = datection.to_db(u"Le 15 mars 2013", "fr", only_future=False)
        self.assertEqual(display(sch, 'fr_FR.UTF8'), u'Le 15 mars 2013')

    def test_display_date_interval(self):
        sch = datection.to_db(
            u"Le 15 mars 2013 PLOP PLOP 16 mars 2013", "fr", only_future=False)
        self.assertEqual(display(sch, 'fr_FR.UTF8'), u'Du 15 au 16 mars 2013')

    def test_display_date_list(self):
        sch = datection.to_db(
            u"Le 15 mars 2013 PLOP PLOP 18 mars 2013", "fr", only_future=False)
        self.assertEqual(display(sch, 'fr_FR.UTF8'), u'Les 15 et 18 mars 2013')

        sch = datection.to_db(
            u"15/03/2015 hhhh 16/03/2015 hhh 18/03/2015",
            "fr", only_future=False)
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'), u'Les 15, 16 et 18 mars 2015')

    def test_display_datetime(self):
        sch = datection.to_db(
            u"Le 15 mars 2013 à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'), u'Le 15 mars 2013 à 18 h 30')

    def test_display_datetime_interval(self):
        sch = datection.to_db(
            u"Le 15 mars 2013 de 16 h à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'), u'Le 15 mars 2013 de 16 h à 18 h 30')

    def test_display_datetime_list(self):
        sch = datection.to_db(
            u"Le 15 et 18 mars 2013 à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'), u'Les 15 et 18 mars 2013 à 18 h 30')

    def test_display_datetime_list_time_interval(self):
        sch = datection.to_db(
            u"Le 15 & 18 mars 2013 de 16 h à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, 'fr_FR.UTF8'),
            u'Les 15 et 18 mars 2013 de 16 h à 18 h 30')


class TestUtilities(unittest.TestCase):

    """Tests of all the datection.display utility functions"""

    def test_to_start_end_datetimes(self):
        schedule = [
            DurationRRule({
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=WE,TH,FR;'
                'BYHOUR=22;BYMINUTE=30;UNTIL=20130809T235959')
            })
        ]
        expected = [
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 9, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 9, 23, 30, 0)
            }]
        self.assertEqual(
            to_start_end_datetimes(schedule), expected)

    def test_to_start_end_datetimes_start_bound(self):
        schedule = [
            DurationRRule({
                'duration': 60,
                'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=WE,TH,FR;'
                          'BYHOUR=22;BYMINUTE=30;UNTIL=20130809T235959')
            })
        ]
        expected = [
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 9, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 9, 23, 30, 0)
            }]
        start_bound = datetime.date(2013, 8, 8)
        self.assertEqual(
            to_start_end_datetimes(schedule, start_bound=start_bound),
            expected)

    def test_consecutives(self):
        d1 = {
            'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
            'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
        }
        d2 = {
            'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
            'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
        }
        self.assertTrue(consecutives(d1, d2))

        d3 = {
            'start': datetime.datetime(2013, 8, 6, 22, 30, 0),
            'end': datetime.datetime(2013, 8, 6, 23, 30, 0)
        }
        self.assertTrue(consecutives(d3, d1))
        self.assertTrue(consecutives(d1, d3))
        self.assertFalse(consecutives(d2, d3))

    def test_groupby_consecutive_dates(self):
        datetimes = [
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 10, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 10, 23, 30, 0)
            }]

        expected = [[datetimes[0], datetimes[1]], [datetimes[2]]]
        self.assertEqual(groupby_consecutive_dates(datetimes), expected)

    def test_groupby_time(self):
        datetimes = [
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 8, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 8, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 10, 21, 0, 0),
                'end': datetime.datetime(2013, 8, 10, 21, 0, 0)
            }]

        expected = [[datetimes[0], datetimes[1]], [datetimes[2]]]
        self.assertEqual(groupby_time(datetimes), expected)

    def test_groupby_date(self):
        datetimes = [
            {
                'start': datetime.datetime(2013, 8, 7, 20, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 21, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 7, 22, 30, 0),
                'end': datetime.datetime(2013, 8, 7, 23, 30, 0)
            },
            {
                'start': datetime.datetime(2013, 8, 10, 21, 0, 0),
                'end': datetime.datetime(2013, 8, 10, 21, 0, 0)
            }]

        expected = [[datetimes[0], datetimes[1]], [datetimes[2]]]
        self.assertEqual(groupby_date(datetimes), expected)
