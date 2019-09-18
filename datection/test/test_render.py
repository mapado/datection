# -*- coding: utf-8 -*-

"""Test suite of the datection.render module."""

import unittest
import locale
import datetime
import mock
import datection

from datection.test import GetCurrentDayMocker
from datection.rendering.date_time import ContinuousDatetimeIntervalFormatter
from datection.rendering.date import DateFormatter
from datection.rendering.date import DateIntervalFormatter
from datection.rendering.date import DateListFormatter
from datection.rendering.date_time import DatetimeFormatter
from datection.rendering.date_time import DatetimeIntervalFormatter
from datection.render import DisplaySchedule
from datection.render import FormatterTuple
from datection.rendering.time import TimeFormatter
from datection.rendering.time import TimePatternFormatter
from datection.rendering.weekday_reccurence import WeekdayReccurenceFormatter
from datection.rendering.next_occurence import NextOccurenceFormatter
from datection.rendering.full import FullFormatter
from datection.rendering.seo import SeoFormatter
from datection.rendering.base import NextChangesMixin
from datection.rendering.exceptions import NoFutureOccurence
from datection.rendering.utils import groupby_consecutive_dates
from datection.rendering.utils import groupby_date
from datection.rendering.utils import groupby_time
from datection.rendering.utils import consecutives
from datection.rendering.utils import to_start_end_datetimes
from datection.rendering.place_summary import PlaceSummaryFormatter
from datection.models import DurationRRule


class TestDateFormatterfr_FR(GetCurrentDayMocker):

    """Test suite of the DateFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestDateFormatterfr_FR, cls).setUpClass()

    def setUp(self):
        self.dfmt = DateFormatter(datetime.date(2013, 1, 1))
        super(TestDateFormatterfr_FR, self).setUp()

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

    def test_format_year_when_past(self):
        self.set_current_date(datetime.date(2014, 11, 1))
        self.assertEqual(self.dfmt.format_year(), u'2013')

    def test_format_year_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2012, 11, 1))
        self.assertEqual(self.dfmt.format_year(), u'')

    def test_force_format_year_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2012, 11, 1))
        self.assertEqual(self.dfmt.format_year(force=True), u'2013')

    def test_format_abbreviated_year(self):
        fmt = self.dfmt.format_year(abbrev=True)
        self.assertEqual(fmt, u'13')

    def test_format_all_parts(self):
        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=False,
            abbrev_monthname=False,
            abbrev_year=False,
            prefix=False)
        self.assertEqual(fmt.strip(), u'mardi 1er janvier 2013')

        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=False,
            abbrev_year=False,
            prefix=True)
        self.assertEqual(fmt.strip(), u'le mar. 1er janvier 2013')

        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=True,
            abbrev_year=False,
            prefix=False)
        self.assertEqual(fmt.strip(), u'mar. 1er janv. 2013')

        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=True,
            abbrev_year=True,
            prefix=True)
        self.assertEqual(fmt.strip(), u'le mar. 1er janv. 13')

    def test_format_all_parts_force_year_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2012, 11, 1))
        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=False,
            abbrev_monthname=False,
            abbrev_year=False,
            prefix=False,
            force_year=True)
        self.assertEqual(fmt.strip(), u'mardi 1er janvier 2013')

    def test_format_all_parts_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2012, 11, 1))
        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=False,
            abbrev_monthname=False,
            abbrev_year=False,
            prefix=False,
            force_year=False)
        self.assertEqual(fmt.strip(), u'mardi 1er janvier')

    def test_format_no_year(self):
        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=False,
            abbrev_monthname=False,
            prefix=False,
            include_year=False)
        self.assertEqual(fmt.strip(), u'mardi 1er janvier')

        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=False,
            prefix=False,
            include_year=False)
        self.assertEqual(fmt.strip(), u'mar. 1er janvier')

        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=True,
            abbrev_monthname=True,
            prefix=True,
            include_year=False)
        self.assertEqual(fmt.strip(), u'le mar. 1er janv.')

    def test_format_no_month_no_year(self):
        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=False,
            prefix=True,
            include_year=False,
            include_month=False)
        self.assertEqual(fmt.strip(), u'le mardi 1er')

        fmt = self.dfmt.display(
            include_dayname=True,
            abbrev_dayname=True,
            prefix=False,
            include_year=False,
            include_month=False)
        self.assertEqual(fmt.strip(), u'mar. 1er')

    def test_display_with_reference(self):
        ref = datetime.date(2013, 1, 1)
        self.assertEqual(self.dfmt.display(reference=ref), u"aujourd'hui")

        ref = datetime.date(2012, 12, 31)
        self.assertEqual(self.dfmt.display(reference=ref), u"demain")

        ref = datetime.date(2012, 12, 30)
        self.assertEqual(self.dfmt.display(reference=ref), u"ce mardi")

        ref = datetime.date(2012, 12, 29)
        self.assertEqual(self.dfmt.display(reference=ref), u"ce mardi")

        ref = datetime.date(2012, 12, 28)
        self.assertEqual(self.dfmt.display(reference=ref), u"ce mardi")

        ref = datetime.date(2012, 12, 27)
        self.assertEqual(self.dfmt.display(reference=ref), u"ce mardi")

        ref = datetime.date(2012, 12, 26)
        self.assertEqual(self.dfmt.display(reference=ref), u"ce mardi")

        ref = datetime.date(2012, 12, 25)
        self.assertEqual(
            self.dfmt.display(reference=ref), u"1er janvier 2013")

    def test_display_full(self):
        self.assertEqual(self.dfmt.display(), u'1er janvier 2013')

    def test_display_full_date_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2012, 12, 1))
        self.assertEqual(self.dfmt.display(include_year=True), u'1er janvier')

    def test_display_full_force_year_date_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2012, 12, 1))
        self.assertEqual(
            self.dfmt.display(include_year=True, force_year=True),
            u'1er janvier 2013')

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

    def test_contradictory_arguments(self):
        with self.assertRaises(ValueError):
            self.dfmt.display(include_year=False, force_year=True)


class TestDateIntervalFormatterfr_FR(GetCurrentDayMocker):

    """Test suite of the DateIntervalFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestDateIntervalFormatterfr_FR, cls).setUpClass()

    def setUp(self):
        start = datetime.date(2013, 11, 15)
        end = datetime.date(2013, 12, 15)
        self.difmt = DateIntervalFormatter(start, end)
        super(TestDateIntervalFormatterfr_FR, self).setUp()

    def test_display_same_day(self):
        self.difmt.end_date = datetime.date(2013, 11, 15)
        self.assertTrue(self.difmt.same_day_interval())
        self.assertEqual(self.difmt.display(), u'le 15 novembre 2013')

    def test_display_same_day_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 8, 1))
        self.difmt.end_date = datetime.date(2013, 11, 15)
        self.assertTrue(self.difmt.same_day_interval())
        self.assertEqual(self.difmt.display(), u'le 15 novembre')

    def test_display_same_day_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 8, 1))
        self.difmt.end_date = datetime.date(2013, 11, 15)
        self.assertTrue(self.difmt.same_day_interval())
        self.assertEqual(
            self.difmt.display(force_year=True),
            u'le 15 novembre 2013')

    def test_display_same_month(self):
        self.difmt.end_date = datetime.date(2013, 11, 17)
        self.assertTrue(self.difmt.same_month_interval())
        self.assertEqual(self.difmt.display(), u'du 15 au 17 novembre 2013')

    def test_display_same_month_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 8, 1))
        self.difmt.end_date = datetime.date(2013, 11, 17)
        self.assertTrue(self.difmt.same_month_interval())
        self.assertEqual(self.difmt.display(), u'du 15 au 17 novembre')

    def test_display_two_consecutive_days(self):
        self.difmt.end_date = datetime.date(2013, 11, 16)
        self.assertTrue(self.difmt.has_two_consecutive_days())
        self.assertEqual(
            self.difmt.display(force_year=True),
            u'les 15 et 16 novembre 2013')

    def test_display_same_month_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 8, 1))
        self.difmt.end_date = datetime.date(2013, 11, 17)
        self.assertTrue(self.difmt.same_month_interval())
        self.assertEqual(
            self.difmt.display(force_year=True),
            u'du 15 au 17 novembre 2013')

    def test_display_same_year(self):
        self.difmt.end_date = datetime.date(2013, 12, 17)
        self.assertTrue(self.difmt.same_year_interval())
        self.assertEqual(
            self.difmt.display(), u'du 15 novembre au 17 décembre 2013')

    def test_display_same_year_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 8, 1))
        self.difmt.end_date = datetime.date(2013, 12, 17)
        self.assertTrue(self.difmt.same_year_interval())
        self.assertEqual(
            self.difmt.display(), u'du 15 novembre au 17 décembre')

    def test_display_same_year_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 8, 1))
        self.difmt.end_date = datetime.date(2013, 12, 17)
        self.assertTrue(self.difmt.same_year_interval())
        self.assertEqual(
            self.difmt.display(force_year=True),
            u'du 15 novembre au 17 décembre 2013')

    def test_display(self):
        self.difmt.end_date = datetime.date(2014, 12, 17)
        self.assertEqual(
            self.difmt.display(), u'du 15 novembre 2013 au 17 décembre 2014')

    def test_display_start_date_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 8, 1))
        self.difmt.end_date = datetime.date(2014, 12, 17)
        self.assertEqual(
            self.difmt.display(), u'du 15 novembre 2013 au 17 décembre 2014')

    def test_display_date_interval_same_month_different_year(self):
        self.difmt.start_date = datetime.date(2014, 12, 17)
        self.difmt.end_date = datetime.date(2015, 12, 17)
        self.assertEqual(
            self.difmt.display(), u'du 17 décembre 2014 au 17 décembre 2015')


class TestDateListFormatterfr_FR(GetCurrentDayMocker):

    """Test suite of the DateListFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestDateListFormatterfr_FR, cls).setUpClass()

    def setUp(self):
        date_list = [
            datetime.date(2013, 3, 4),
            datetime.date(2013, 3, 5),
            datetime.date(2013, 3, 6),
            datetime.date(2013, 3, 9),
        ]
        self.dlfmt = DateListFormatter(date_list)
        super(TestDateListFormatterfr_FR, self).setUp()

    def test_display(self):
        self.assertEqual(self.dlfmt.display(), u'les 4, 5, 6 et 9 mars 2013')

    def test_display_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 1, 1))
        self.assertEqual(self.dlfmt.display(), u'les 4, 5, 6 et 9 mars')

    def test_display_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 1, 1))
        self.assertEqual(
            self.dlfmt.display(force_year=True),
            u'les 4, 5, 6 et 9 mars 2013')

    def test_display_one_date(self):
        self.dlfmt.date_list = [datetime.date(2013, 3, 4)]
        self.assertEqual(self.dlfmt.display(), u'le 4 mars 2013')

    def test_display_one_date_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 1, 1))
        self.dlfmt.date_list = [datetime.date(2013, 3, 4)]
        self.assertEqual(self.dlfmt.display(), u'le 4 mars')

    def test_display_one_date_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 1, 1))
        self.dlfmt.date_list = [datetime.date(2013, 3, 4)]
        self.assertEqual(
            self.dlfmt.display(force_year=True), u'le 4 mars 2013')


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

    """Test suite of the TimePatternFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')

    def setUp(self):
        start = datetime.time(12, 15)
        end = datetime.time(13, 0)
        self.tifmt = TimePatternFormatter(start, end)

    def test_display(self):
        self.assertEqual(self.tifmt.display(), u'de 12 h 15 à 13 h')

    def test_display_end_time_midnight(self):
        self.tifmt.end_time = datetime.time(0, 0)
        self.assertEqual(self.tifmt.display(), u'de 12 h 15 à minuit')

    def test_display_end_time_after_midnight(self):
        self.tifmt.start_time = datetime.time(22, 30)
        self.tifmt.end_time = datetime.time(2, 0)
        self.assertEqual(self.tifmt.display(), u'de 22 h 30 à 2 h')

    def test_display_equal_bounds(self):
        self.tifmt.end_time = self.tifmt.start_time
        self.assertEqual(self.tifmt.display(), u'12 h 15')

    def test_display_all_day(self):
        start = datetime.time(0, 0)
        end = datetime.time(23, 59)
        tifmt = TimePatternFormatter(start, end)
        self.assertEqual(tifmt.display(), u'')


class TestDatetimeFormatterfr_FR(GetCurrentDayMocker):

    """Test suite of the DatetimeFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestDatetimeFormatterfr_FR, cls).setUpClass()

    def setUp(self):
        dt = datetime.datetime(2013, 3, 4, 12, 15)
        self.dtfmt = DatetimeFormatter(dt)
        super(TestDatetimeFormatterfr_FR, self).setUp()

    def test_display(self):
        self.assertEqual(self.dtfmt.display(), u"le 4 mars 2013 à 12 h 15")

    def test_display_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 1, 1))
        self.assertEqual(self.dtfmt.display(), u"le 4 mars à 12 h 15")

    def test_display_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 1, 1))
        self.assertEqual(
            self.dtfmt.display(force_year=True),
            u"le 4 mars 2013 à 12 h 15")

    def test_display_arg_passing(self):
        self.assertEqual(
            self.dtfmt.display(include_year=False), u"le 4 mars à 12 h 15")

    def test_display_arg_passing_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2011, 1, 1))
        self.assertEqual(
            self.dtfmt.display(include_year=False), u"le 4 mars à 12 h 15")


class TestDatetimeIntervalFormatterfr_FR(GetCurrentDayMocker):

    """Test suite of the DatetimeIntervalFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestDatetimeIntervalFormatterfr_FR, cls).setUpClass()

    def setUp(self):
        start = datetime.datetime(2013, 3, 4, 12, 15)
        end = datetime.datetime(2013, 8, 5, 12, 15)
        self.dtifmt = DatetimeIntervalFormatter(start, end)
        super(TestDatetimeIntervalFormatterfr_FR, self).setUp()

    def test_display_same_day(self):
        self.dtifmt.start_datetime = datetime.datetime(2013, 8, 5, 10, 15)
        self.assertEqual(
            self.dtifmt.display(), u'le 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_same_day_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.dtifmt.start_datetime = datetime.datetime(2013, 8, 5, 10, 15)
        self.assertEqual(
            self.dtifmt.display(), u'le 5 août de 10 h 15 à 12 h 15')

    def test_display_same_month(self):
        self.dtifmt.start_datetime = datetime.datetime(2013, 8, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_same_month_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.dtifmt.start_datetime = datetime.datetime(2013, 8, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er au 5 août de 10 h 15 à 12 h 15')

    def test_display_same_month_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.dtifmt.start_datetime = datetime.datetime(2013, 8, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(force_year=True),
            u'du 1er au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_same_year(self):
        self.dtifmt.start_datetime = datetime.datetime(2013, 7, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er juillet au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_same_year_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.dtifmt.start_datetime = datetime.datetime(2013, 7, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er juillet au 5 août de 10 h 15 à 12 h 15')

    def test_display_same_year_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.dtifmt.start_datetime = datetime.datetime(2013, 7, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(force_year=True),
            u'du 1er juillet au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display(self):
        self.dtifmt.start_datetime = datetime.datetime(2012, 7, 1, 10, 15)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 1er juillet 2012 au 5 août 2013 de 10 h 15 à 12 h 15')

    def test_display_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
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

    def test_display_all_day_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.dtifmt.start_datetime = datetime.datetime(2013, 3, 4, 0, 0)
        self.dtifmt.end_datetime = datetime.datetime(2013, 8, 5, 23, 59)
        self.assertEqual(
            self.dtifmt.display(),
            u'du 4 mars au 5 août')

    def test_display_all_day_in_less_than_6_months_force_year(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.dtifmt.start_datetime = datetime.datetime(2013, 3, 4, 0, 0)
        self.dtifmt.end_datetime = datetime.datetime(2013, 8, 5, 23, 59)
        self.assertEqual(
            self.dtifmt.display(force_year=True),
            u'du 4 mars au 5 août 2013')


class TestContinuousDatetimeIntervalFormatterfr_FR(GetCurrentDayMocker):

    """Test suite of the DatetimeIntervalFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestContinuousDatetimeIntervalFormatterfr_FR, cls).setUpClass()

    def setUp(self):
        start = datetime.datetime(2013, 3, 4, 12, 15)
        end = datetime.datetime(2013, 8, 5, 12, 15)
        self.cdtifmt = ContinuousDatetimeIntervalFormatter(start, end)
        super(TestContinuousDatetimeIntervalFormatterfr_FR, self).setUp()

    def test_display_same_year(self):
        self.assertEqual(
            self.cdtifmt.display(),
            u'du 4 mars à 12 h 15 au 5 août 2013 à 12 h 15')

    def test_display_same_year_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.assertEqual(
            self.cdtifmt.display(),
            u'du 4 mars à 12 h 15 au 5 août à 12 h 15')

    def test_display_same_day(self):
        start = datetime.datetime(2019, 1, 11, 12, 15)
        end = datetime.datetime(2019, 1, 11, 18, 15)
        cdtifmt = ContinuousDatetimeIntervalFormatter(start, end)
        self.assertEqual(
            cdtifmt.display(),
            'vendredi 11 janvier, de 12 h 15 à 18 h 15'
        )


    def test_display(self):
        self.cdtifmt.start = datetime.datetime(2012, 3, 4, 12, 15)
        self.assertEqual(
            self.cdtifmt.display(),
            u'du 4 mars à 12 h 15 au 5 août 2013 à 12 h 15')


class TestWeekdayReccurenceFormatter_fr_FR(GetCurrentDayMocker):

    """Test suite of the WeekdayReccurenceFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestWeekdayReccurenceFormatter_fr_FR, cls).setUpClass()

    def setUp(self):
        drr = {
            'duration': 60,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,SU;'
                      'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
        }
        self.wkfmt = WeekdayReccurenceFormatter([drr])

        drr = {
            'duration': 60,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
                      'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                      'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
        }
        self.wkfmt_alldays = WeekdayReccurenceFormatter([drr])

        drr = {
            'duration': 60,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
                      'BYDAY=MO,TU,WE;'
                      'BYHOUR=22;BYMINUTE=30;UNTIL=20130831T235959')
        }
        self.wkfmt_continuous = WeekdayReccurenceFormatter([drr])

        drr1 = {
            'duration': 60,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
                      'BYDAY=MO,TU,WE;'
                      'BYHOUR=19;BYMINUTE=30;UNTIL=20130831T235959')
        }

        drr2 = {
            'duration': 90,
            'rrule': ('DTSTART:20130807\nRRULE:FREQ=WEEKLY;'
                      'BYDAY=MO,TU,WE;'
                      'BYHOUR=21;BYMINUTE=30;UNTIL=20130831T235959')
        }
        self.wkfmt_multitime = WeekdayReccurenceFormatter([drr1, drr2])
        super(TestWeekdayReccurenceFormatter_fr_FR, self).setUp()

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

    def test_format_date_interval_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.assertEqual(self.wkfmt.format_date_interval(),
                         u'du 7 au 31 août')

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

        self.assertEqual(
            self.wkfmt_multitime.display(),
            u'du lundi au mercredi, du 7 au 31 août 2013, de 19 h 30 à 20 h 30 et de 21 h 30 à 23 h')

    def test_display_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 4, 1))
        self.assertEqual(
            self.wkfmt.display(),
            (u'le lundi, mardi et dimanche, du 7 au 31 août, '
                u'de 22 h 30 à 23 h 30'))
        self.assertEqual(
            self.wkfmt_alldays.display(),
            (u'du 7 au 31 août, de 22 h 30 à 23 h 30'))

        self.assertEqual(
            self.wkfmt_continuous.display(),
            u'du lundi au mercredi, du 7 au 31 août, de 22 h 30 à 23 h 30')


class TestNextOccurrenceFormatterfr_FR(GetCurrentDayMocker):

    """Test suite of the WeekdayReccurenceFormatter using the fr_FR locale."""

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestNextOccurrenceFormatterfr_FR, cls).setUpClass()

    def setUp(self):
        schedule = [
            {
                'duration': 0,
                'rrule': ('DTSTART:20141112\nRRULE:FREQ=DAILY;BYHOUR=9;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141128T235959'),
            }
        ]
        start = datetime.datetime(2014, 11, 10)
        end = datetime.datetime(2014, 11, 20)
        self.nofmt = NextOccurenceFormatter(schedule, start, end)
        super(TestNextOccurrenceFormatterfr_FR, self).setUp()

    def test_format_next_occurence(self):
        ref = datetime.datetime(2014, 10, 10)
        self.assertEqual(self.nofmt.display(ref), u'Le 12 novembre 2014 à 9 h')

    def test_format_next_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2014, 7, 1))
        ref = datetime.datetime(2014, 10, 10)
        self.assertEqual(self.nofmt.display(ref), u'Le 12 novembre à 9 h')

    def test_format_next_occurence_soon(self):
        ref = datetime.datetime(2014, 11, 10)
        self.assertEqual(self.nofmt.display(ref), u'Ce mercredi à 9 h')

    def test_format_next_occurence_today(self):
        ref = datetime.datetime(2014, 11, 14)
        self.nofmt.start = datetime.datetime(2014, 11, 14)
        self.assertEqual(
            self.nofmt.display(ref, summarize=False), u"Aujourd'hui à 9 h")

    def test_format_next_occurence_today_all_day(self):
        ref = datetime.datetime(2014, 11, 14)
        schedule = [
            {
                'duration': 1439,
                'rrule': ('DTSTART:20141112\nRRULE:FREQ=DAILY;BYHOUR=0;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141128T235959'),
            }
        ]
        start = datetime.datetime(2014, 11, 14)
        end = datetime.datetime(2014, 11, 20)
        self.nofmt = NextOccurenceFormatter(schedule, start, end)
        self.assertEqual(
            self.nofmt.display(ref, summarize=False), u"Aujourd'hui")
        self.assertEqual(
            self.nofmt.display(ref, summarize=True), u"Auj. + autres dates")

    def test_format_next_occurence_today_plus_other_occurences(self):
        ref = datetime.datetime(2014, 11, 12)
        schedule = [
            {
                'duration': 0,
                'rrule': ('DTSTART:20141112\nRRULE:FREQ=DAILY;BYHOUR=9;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141113T235959'),
            }
        ]
        start = datetime.datetime(2014, 11, 10)
        end = datetime.datetime(2014, 11, 20)
        self.nofmt = NextOccurenceFormatter(schedule, start, end)
        self.assertEqual(
            self.nofmt.display(ref, summarize=True),
            u"Auj. à 9 h + autres dates")

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
        self.set_current_date(datetime.date(2014, 7, 1))
        self.assertEqual(
            self.nofmt.display(ref, summarize=True),
            u'Le 12 novembre à 9 h + autres dates')

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
        self.set_current_date(datetime.date(2014, 7, 1))
        self.assertEqual(
            nofmt.display(ref, summarize=True),
            u'12 novembre + autres dates')


class TestFullFormatter_fr_FR(GetCurrentDayMocker):

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestFullFormatter_fr_FR, cls).setUpClass()

    def setUp(self):
        schedule = [
            {'duration': 0,
             'rrule': ('DTSTART:20140305\nRRULE:FREQ=DAILY;BYHOUR=9;'
                       'BYMINUTE=0;INTERVAL=1;UNTIL=20140309T235959'),
             },
            {'duration': 0,
             'rrule': ('DTSTART:20140226\nRRULE:FREQ=DAILY;COUNT=1;'
                       'BYMINUTE=0;BYHOUR=9')
             },
            {'duration': 0,
             'rrule': ('DTSTART:20150226\nRRULE:FREQ=DAILY;COUNT=1;'
                       'BYMINUTE=0;BYHOUR=9'),
             }
        ]
        self.fmt = FullFormatter(schedule)
        super(TestFullFormatter_fr_FR, self).setUp()

    def test_display(self):
        self.assertEqual(
            self.fmt.display(),
            """Du mercredi 5 au dimanche 9 mars 2014 à 9 h\nLe mercredi 26 février 2014, le jeudi 26 février 2015, à 9 h""")

    def test_display_in_less_than_6_months(self):
        self.set_current_date(datetime.date(2013, 11, 1))
        self.assertEqual(
            self.fmt.display(),
            'Du mercredi 5 au dimanche 9 mars 2014 à 9 h\nLe mercredi 26 février 2014, le jeudi 26 février 2015, à 9 h')

    def test_display_day_with_one_date(self):
        # Le vendredi 25 septembre 2015 à 20 h

        schedule = [
            {
                'duration': 0,
                'rrule': 'DTSTART:20150925\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=20'
            }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Le vendredi 25 septembre 2015 à 20 h")

    def test_display_day_with_one_date_full_day(self):
        # Le vendredi 25 septembre 2015 à 20 h

        schedule = [
            {
                'duration': 0,
                'rrule': 'DTSTART:20150925\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'
            }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Le vendredi 25 septembre 2015")

    def test_display_day_with_two_date(self):
        # Le vendredi 25 septembre 2015 à 20, le samedi 10 octobre 2015 à 18 h
        schedule = [
            {
                'duration': 0,
                'rrule': 'DTSTART:20150925\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=20'
            },
            {
                'duration': 0,
                'rrule': 'DTSTART:20151010\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=18'
            }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Le vendredi 25 septembre 2015 à 20 h\nLe samedi 10 octobre 2015 à 18 h")

    def test_display_day_with_three_date(self):
        # Le 25 septembre 2015, le 10 octobre 2015 et le 11 novembre 2015 à 21 h
        schedule = [
            {
                'duration': 0,
                'rrule': 'DTSTART:20150925\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=21'
            },
            {
                'duration': 0,
                'rrule': 'DTSTART:20151010\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=21'
            },
            {
                'duration': 0,
                'rrule': 'DTSTART:20151111\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=21'
            }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Le 25 septembre 2015, le 10 octobre 2015, le 11 novembre 2015, à 21 h")

    def test_display_weekday_reccurence(self):
        schedule = [
            {
                'duration': 480,
                'rrule': ('DTSTART:20140117\nRRULE:FREQ=WEEKLY;BYDAY=SU;'
                          'BYHOUR=10;BYMINUTE=0'),
                'unlimited': True,
            }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(fmt.display(), u'Le dimanche, de 10 h à 18 h')

    def test_display_end_after_midnight_day_enumeration(self):
        schedule = [
            {
                "duration" : 360,
                "rrule" : ('DTSTART:20150709\nRRULE:FREQ=DAILY;UNTIL=20150710T235959;'
                           'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO,TU,WE,TH,FR,SA,SU')
            }
        ]
        fmt = FullFormatter(schedule)
        display = fmt.display()
        self.assertEqual(display, u'Les jeudi 9 et vendredi 10 juillet 2015 de 22 h à 4 h')

    def test_display_end_after_midnight_day_interval(self):
        schedule = [
            {
                "duration" : 360,
                "rrule" : ('DTSTART:20150705\nRRULE:FREQ=DAILY;UNTIL=20150710T235959;'
                           'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO,TU,WE,TH,FR,SA,SU')
            }
        ]
        fmt = FullFormatter(schedule)
        display = fmt.display()
        self.assertEqual(display, u'Du dimanche 5 au vendredi 10 juillet 2015 de 22 h à 4 h')

    def test_display_end_after_midnight_same_day(self):
        schedule = [
            {
                "duration" : 120,
                "rrule" : ('DTSTART:20150710\nRRULE:FREQ=DAILY;UNTIL=20150710T235959;'
                           'INTERVAL=1;BYMINUTE=00;BYHOUR=2;BYDAY=MO,TU,WE,TH,FR,SA,SU')
            }
        ]
        fmt = FullFormatter(schedule)
        display = fmt.display()
        self.assertEqual(display, u'Le vendredi 10 juillet 2015 de 2 h à 4 h')

    def test_display_multidays_single_date(self):
        schedule = [
            {
                "rrule": "DTSTART:20190927\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=00;BYHOUR=08;BYDAY=MO,TU,WE,TH,FR,SA,SU",
                "duration": 56880,
            }
        ]
        fmt = FullFormatter(schedule)
        display = fmt.display()
        self.assertEqual(display, u'Du 27 septembre à 8 h au 5 novembre 2019 à 20 h')

    def test_display_excluded_weekday(self):
        # Du 5 au 28 mars 2015 de 8h à 9h, sauf le lundi
        schedule = [
            {'duration': 60,
             'excluded': [
                 ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYDAY=MO;BYHOUR=8;'
                  'BYMINUTE=0;UNTIL=20150328T235959')
             ],
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150328T235959')
             }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Du jeudi 5 au samedi 28 mars 2015 de 8 h à 9 h, sauf le lundi")

    def test_display_excluded_weekday_interval(self):
        # Du 5 au 28 mars 2015 de 8h à 9h, sauf le lundi, mardi et mercredi
        schedule = [
            {'duration': 60,
             'excluded': [
                 ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYDAY=MO,TU,WE;BYHOUR=8;'
                  'BYMINUTE=0;UNTIL=20150328T235959')
             ],
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150328T235959')
             }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Du jeudi 5 au samedi 28 mars 2015 de 8 h à 9 h, sauf du lundi au mercredi")

    def test_display_excluded_weekday_list(self):
        # Du 5 au 28 mars 2015 de 8h à 9h, sauf le lundi, mardi et jeudi
        schedule = [
            {'duration': 60,
             'excluded': [
                 ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYDAY=MO,TU,TH;BYHOUR=8;'
                  'BYMINUTE=0;UNTIL=20150328T235959')
             ],
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150328T235959')
             }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Du jeudi 5 au samedi 28 mars 2015 de 8 h à 9 h, sauf le lundi, mardi et jeudi")

    def test_display_excluded_weekday_list_many_excluded(self):
        # Du 5 au 28 mars 2015 de 8h à 9h, sauf le lundi, mardi et jeudi
        schedule = [
            {'duration': 60,
             'excluded': [
                 ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYDAY=TU;BYHOUR=8;'
                  'BYMINUTE=0;UNTIL=20150328T235959'),
                 ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYDAY=TH;BYHOUR=8;'
                  'BYMINUTE=0;UNTIL=20150328T235959')
             ],
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150328T235959')
             }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Du jeudi 5 au samedi 28 mars 2015 de 8 h à 9 h, sauf le mardi et jeudi")

    def test_display_excluded_datetime(self):
        # "Du 5 au 28 mars 2015 de 8h à 9h, sauf le 17 mars"
        schedule = [
            {'duration': 60,
             'excluded': [
                 ('DTSTART:20150317\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;'
                  'BYHOUR=8')
             ],
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20150328T235959')
             }
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u"Du jeudi 5 au samedi 28 mars 2015 de 8 h à 9 h, sauf le 17 mars 2015")

    def test_regrouping_weekdays_by_interval(self):
        # Du 30 septembre au 11 octobre 2015:
        # - du mercredi au samedi, de 20 h à 21 h
        # - le dimanche, de 17 h à 18 h
        #
        # Du 20 au 22 octobre 2015:
        # - du mardi au samedi, de 20 h à 21 h
        # - le dimanche, de 17 h à 18 h
        schedule = [
            {
                "duration": 60,
                "rrule": ("DTSTART:20151020\nRRULE:FREQ=DAILY;"
                          "UNTIL=20151022T235959;INTERVAL=1;BYMINUTE=00;"
                          "BYHOUR=20;BYDAY=TU,WE,TH,FR,SA")
            },
            {
                "duration": 60,
                "rrule": ("DTSTART:20151020\nRRULE:FREQ=DAILY;"
                          "UNTIL=20151022T235959;INTERVAL=1;BYMINUTE=00;"
                          "BYHOUR=17;BYDAY=SU")
            },
            {
                "duration": 60,
                "rrule": ("DTSTART:20150930\nRRULE:FREQ=DAILY;"
                          "UNTIL=20151011T235959;INTERVAL=1;BYMINUTE=00;"
                          "BYHOUR=20;BYDAY=WE,TH,FR,SA")
            },
            {
                "duration": 60,
                "rrule": ("DTSTART:20150930\nRRULE:FREQ=DAILY;"
                          "UNTIL=20151011T235959;INTERVAL=1;BYMINUTE=00;"
                          "BYHOUR=17;BYDAY=SU")
            },
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u'Du 30 septembre au 11 octobre 2015:\n'
            u'- du mercredi au samedi, de 20 h \xe0 21 h\n'
            u'- le dimanche, de 17 h \xe0 18 h\n'
            u'\n'
            u'Du 20 au 22 octobre 2015:\n'
            u'- du mardi au samedi, de 20 h \xe0 21 h\n'
            u'- le dimanche, de 17 h \xe0 18 h\n')

    def test_filter_non_informative(self):
        # test the filtering of the rrule without time information
        # in case there is a more precise rule
        schedule = [
            {
                "duration": 0,
                "rrule": ("DTSTART:20151223\nRRULE:FREQ=DAILY;COUNT=1;"
                          "INTERVAL=1;BYMINUTE=00;BYHOUR=20;"
                          "BYDAY=MO,TU,WE,TH,FR,SA,SU")
            },
            {
                "duration": 1439,
                "rrule": ("DTSTART:20151215\nRRULE:FREQ=DAILY;"
                          "UNTIL=20151231T235959;INTERVAL=1;BYMINUTE=0;"
                          "BYHOUR=0;BYDAY=MO,TU,WE,TH,FR,SA,SU")
            },
        ]
        fmt = FullFormatter(schedule)
        self.assertEqual(
            fmt.display(),
            u'Le mercredi 23 décembre 2015 à 20 h')


class TestSeoFormatter_fr_FR(GetCurrentDayMocker):

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestSeoFormatter_fr_FR, cls).setUpClass()

    def test_format_single_day(self):
        sch = datection.export(
            u"Le 18 mars 2013 à 18h30", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars 2013')

    def test_format_date_list_same_month(self):
        sch = datection.export(
            u"Le 18 et 19 mars 2013 à 18h30", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars 2013')

    def test_format_date_interval_same_month(self):
        sch = datection.export(
            u"Du 1er au 19 mars 2013 à 18h30", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars 2013')

    def test_format_date_two_months(self):
        sch = datection.export(
            u"Le 5 mars 2013, le 7 avril 2013", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars et avril 2013')

    def test_format_date_interval_two_months(self):
        sch = datection.export(
            u"Du 5 au 27 mars 2013, du 7 au 8 avril 2013", "fr",
            only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars et avril 2013')

    def test_format_date_interval_two_months2(self):
        sch = datection.export(
            u"Du 5 mars au 8 avril 2013", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars et avril 2013')

    def test_format_date_interval_three_months(self):
        sch = datection.export(
            u"Du 5 mars au 8 mai 2013", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'')

    def test_format_date_interval_two_months_two_years(self):
        sch = datection.export(
            u"Le 5 décembre 2013, le 7 janvier 2014", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'')

    def test_sort_month_names(self):
        sch = datection.export(
            u"Le 5 décembre 2013, le 7 novembre 2013", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'novembre et décembre 2013')

    def test_format_weekday_recurrence(self):
        sch = datection.export(
            u"Le lundi du 5 au 25 mars 2015", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars 2015')

    def test_format_weekday_recurrence_two_months(self):
        sch = datection.export(
            u"Le lundi du 5 mars au 25 avril 2015", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'mars et avril 2015')

    def test_format_weekday_recurrence_three_months(self):
        sch = datection.export(
            u"Le lundi du 5 mars au 25 mai 2015", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'')

    def test_format_unbounded_weekday_recurrence(self):
        sch = datection.export(u"Le lundi", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(formatter.display(), u'')

    def test_next_date(self):
        self.set_current_date(datetime.date(2013, 8, 8))
        sch = datection.export(
            u"Du lundi 1er aout 2013 au lundi 31 aout 2013", "fr", only_future=False)
        formatter = SeoFormatter(sch)
        self.assertEqual(
            formatter.next_occurence()['start'], datetime.datetime(2013, 8, 8))


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


class TestDisplaySchedule(GetCurrentDayMocker):

    @classmethod
    def setUpClass(cls):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF8')
        super(TestDisplaySchedule, cls).setUpClass()

    def test_display_schedule(self):
        self.set_current_date(datetime.date(2012, 11, 1))
        ref = datetime.datetime(2014, 11, 14)
        sch = datection.export(
            u"Du 1er au 19 mars 2013 à 18h30", "fr", only_future=False)
        formatter1 = SeoFormatter(sch)

        schedule = [
            {
                'duration': 0,
                'rrule': ('DTSTART:20141112\nRRULE:FREQ=DAILY;BYHOUR=9;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141113T235959'),
            }
        ]
        start = datetime.datetime(2014, 11, 10)
        end = datetime.datetime(2014, 11, 20)
        formatter2 = NextOccurenceFormatter(schedule, start, end)

        ds = DisplaySchedule()
        ds.formatter_tuples.append(FormatterTuple(formatter1, {}))
        ds.formatter_tuples.append(FormatterTuple(
            formatter2, {'reference': ref, 'summarize': True}))

        self.assertEqual(ds.display(), 'mars 2013')
        self.assertEqual(
            ds.next_changes(), datetime.datetime(2013, 2, 23, 0, 0, 0))

    def test_display_schedule_past(self):
        self.get_current_date_mock.return_value = datetime.date(2040, 11, 1)
        ref = datetime.datetime(2040, 11, 14)
        schedule = [
            {
                'duration': 0,
                'rrule': ('DTSTART:20141112\nRRULE:FREQ=DAILY;BYHOUR=9;'
                          'BYMINUTE=0;INTERVAL=1;UNTIL=20141113T235959'),
            }
        ]
        start = datetime.datetime(2040, 11, 10)
        end = datetime.datetime(2040, 11, 20)
        formatter2 = NextOccurenceFormatter(schedule, start, end)

        ds = DisplaySchedule()
        ds.formatter_tuples.append(FormatterTuple(
            formatter2, {'reference': ref, 'summarize': True}))

        self.assertEqual(ds.display(), u'')


class TestNextDateMixin(GetCurrentDayMocker):

    def test_next_date_mixin_empty(self):
        next_change = NextChangesMixin()
        self.assertEqual(next_change.next_changes(), None)

        next_change.next_occurence = mock.MagicMock(return_value=None)
        self.assertEqual(next_change.next_changes(), None)

        next_change.next_occurence = mock.MagicMock(return_value={})
        self.assertEqual(next_change.next_changes(), None)

    def test_next_date_gt_7_days(self):
        self.set_current_date(datetime.date(2012, 11, 1))
        next_change = NextChangesMixin()
        next_occur = {
            'start': datetime.datetime(2013, 8, 8, 20, 30, 0),
            'end': datetime.datetime(2013, 8, 8, 22, 0, 0)
        }
        next_change.next_occurence = mock.MagicMock(return_value=next_occur)

        self.assertEqual(
            next_change.next_changes(), datetime.datetime(2013, 8, 2, 0, 0, 0))

        next_occur = {'start': datetime.datetime(2013, 8, 20, 21, 0, 0)}
        next_change.next_occurence = mock.MagicMock(return_value=next_occur)

        self.assertEqual(
            next_change.next_changes(), datetime.datetime(2013, 8, 14, 0, 0, 0))

    def test_long_formatter_gt_7_days(self):
        self.set_current_date(datetime.date(2014, 8, 27))
        sch = datection.export(
            u"Le 14 septembre 2014 à 18h", "fr", only_future=False)
        formatter = FullFormatter(sch)

        self.assertIsNone(formatter.next_changes())

    def test_next_date_today(self):
        self.set_current_date(datetime.date(2013, 8, 8))
        next_change = NextChangesMixin()
        next_occur = {'start': datetime.datetime(2013, 8, 8, 20, 30, 0)}
        next_change.next_occurence = mock.MagicMock(return_value=next_occur)

        self.assertEqual(next_change.next_changes(), datetime.datetime(2013, 8, 9, 0, 0, 0))

    def test_next_date_tomorrow(self):
        self.set_current_date(datetime.date(2013, 8, 7))
        next_change = NextChangesMixin()
        next_occur = {'start': datetime.datetime(2013, 8, 8, 20, 30, 0)}
        next_change.next_occurence = mock.MagicMock(return_value=next_occur)

        self.assertEqual(
            next_change.next_changes(), datetime.datetime(2013, 8, 8, 0, 0, 0))

    def test_next_date_lt_7_days_gt_1d(self):
        self.set_current_date(datetime.date(2013, 8, 2))
        next_change = NextChangesMixin()
        next_occur = {'start': datetime.datetime(2013, 8, 8, 20, 30, 0)}
        next_change.next_occurence = mock.MagicMock(return_value=next_occur)

        self.assertEqual(
            next_change.next_changes(), datetime.datetime(2013, 8, 7, 0, 0, 0))

        self.set_current_date(datetime.date(2013, 8, 6))
        next_change = NextChangesMixin()
        next_occur = {'start': datetime.datetime(2013, 8, 8, 20, 30, 0)}
        next_change.next_occurence = mock.MagicMock(return_value=next_occur)

        self.assertEqual(
            next_change.next_changes(), datetime.datetime(2013, 8, 7, 0, 0, 0))


    def test_short_sched_kwargs_include_days(self):
        schedule = [{
            u'duration': 1439,
            u'rrule': u'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;BYHOUR=0;BYMINUTE=0',
            u'span': [48, 68],
            u'unlimited': True
        }]
        datection.get_display_schedule(
            schedule,
            'fr',
            short=True,
            bounds=(datetime.datetime(2015, 9, 7, 2, 0), None),
            reference=datetime.datetime.now()
        ).display()


class TestPlaceSummaryRender(unittest.TestCase):

    def test_every_day(self):
        """"""
        schedule = [
            {'duration': 60,
             'excluded': [
                 ('DTSTART:20150317\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;'
                  'BYHOUR=8')
             ],
                'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=8;'
                          'BYMINUTE=0;INTERVAL=1')
             }
        ]

        fmt = PlaceSummaryFormatter(schedule)
        self.assertEqual(fmt.display(), "Tous les jours")

    def test_except(self):
        """"""
        schedule = [
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO,TU,TH')
            },
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=FR,SA,SU')
            }
        ]

        fmt = PlaceSummaryFormatter(schedule)
        self.assertEqual(fmt.display(), "Tous les jours sauf mer.")

        schedule = [
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO,TU,TH')
            },
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=SA,SU')
            }
        ]

        fmt = PlaceSummaryFormatter(schedule)
        self.assertEqual(fmt.display(), "Tous les jours sauf mer. et ven.")

    def test_list(self):
        """"""
        schedule = [
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO')
            }
        ]

        fmt = PlaceSummaryFormatter(schedule)
        self.assertEqual(fmt.display(), "Lun.")

        schedule = [
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO,TU')
            }
        ]

        fmt = PlaceSummaryFormatter(schedule)
        self.assertEqual(fmt.display(), "Lun. et mar.")

        schedule = [
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO,TU,TH')
            }
        ]

        fmt = PlaceSummaryFormatter(schedule)
        self.assertEqual(fmt.display(), "Lun., mar. et jeu.")

        schedule = [
            {
                "duration": 360,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=22;BYDAY=MO,TU')
            },
            {
                "duration": 60,
                "rrule": ('DTSTART:20150709\nRRULE:FREQ=DAILY;'
                          'INTERVAL=1;BYMINUTE=00;BYHOUR=23;BYDAY=TH')
            }
        ]

        fmt = PlaceSummaryFormatter(schedule)
        self.assertEqual(fmt.display(), "Lun., mar. et jeu.")
