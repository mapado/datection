# -*- coding: utf-8 -*-
""" Test suite of the timepoint serialize suite. """

import unittest
import sys
sys.path.insert(0, '..')

import datetime

from datection.parse import parse
from datection.export import to_db
from ..serialize import *


# We pretend to be in the future
today = datetime.date(day=5, month=10, year=2008)


class TestSerializeFrDates(unittest.TestCase):
    """ Test class of the Date serializer with french data"""

    def test_valid_litteral_date(self):
        """ Test the serialization of valid years of litteral format. """
        date = parse(u'le lundi 5 mars 2013', 'fr')[0]
        assert date.valid
        date_norm = date.to_python()
        assert date_norm == datetime.date(year=2013, month=3, day=5)

    def test_missing_weekday(self):
        """Check that missing weekday has no influence on validity."""
        assert parse(u'5 mars 2013', 'fr')[0].valid

    def test_valid_numeric_date(self):
        """ Test the normalisation of valid years of litteral formats. """
        date = parse(u'5/03/2013', 'fr')[0]
        assert date.valid
        date_norm = date.to_python()
        assert date_norm == datetime.date(year=2013, month=3, day=5)

    def test_invalid_dates(self):
        """ Check that missing date leads to invalid structure. """
        assert parse(u'5/03', 'fr', valid=False)[0].valid is False
        assert parse(u' lundi 5 mars', 'fr', valid=False)[0].valid is False

    def test_to_db(self):
        """ Test the return format for sql insert """
        dates = to_db(u'le lundi 5 mars 2013', 'fr')
        assert len(dates) == 1
        date = dates[0]
        assert date[0] == datetime.datetime(year=2013, month=3, day=5, hour=0, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=3, day=5, hour=23, minute=59, second=59)

    def test_future_date(self):
        """ Test that the date is in the future. """
        date = parse(u'le mercredi 16 décembre 2013', 'fr')[0]
        assert date.future(reference=today)

    def test_past_date(self):
        """ Test that the date is in the past. """
        date = parse(u'le mercredi 16 décembre 2003', 'fr')[0]
        assert not date.future(reference=today)

    def test_numeric_2digit_format(self):
        """Test that numeric dates with a 2 digit year are
        properly serialized.

        """
        # past date
        date = parse(u'06/01/78', 'fr')[0]
        assert date.year == 1978

        date = parse(u'06/01/15', 'fr')[0]
        assert date.year == 2015

    def test_redundant_dates(self):
        """Test that redundant serialized dates are only returned once
        from the parse function.

        """
        dates = parse(u'le 15 février 2013, plop, 15/02/2013', 'fr')
        assert len(dates) == 1


class TestSerializeFrTimeInterval(unittest.TestCase):
    """ Test class of the Time serializer on french data. """

    def test_valid_time(self):
        """ Test the serializer on a valid time."""
        time = parse(u'15h30', 'fr')[0]
        assert time.valid
        time_norm = time.to_python()
        assert time_norm == datetime.time(hour=15, minute=30)

    def test_missing_minute(self):
        """ Test the serializer on a time witout minute. """
        time = parse(u'15h', 'fr')[0]
        assert time.valid
        time_norm = time.to_python()
        assert time_norm == datetime.time(hour=15, minute=0)

    def test_valid_time_interval(self):
        """ Test the serializer on a valid time *interval*"""
        time = parse(u'de 15h30 à 16h', 'fr')[0]
        assert time.valid
        time_norm = time.to_python()
        st_time = datetime.time(hour=15, minute=30)
        end_time = datetime.time(hour=16, minute=0)
        assert time_norm == (st_time, end_time)

    def test_all_interval_formats(self):
        """ Test that all supported formats lead to equivalent serialized forms."""
        assert parse(u'15h30', 'fr')[0] == parse(u'15:30', 'fr')[0]
        assert parse(u'de 15h à 18h', 'fr')[0] == parse(u'15h-18h', 'fr')[0]
        assert parse(u'entre 15h et 18h', 'fr')[0] == parse(u'15h-18h', 'fr')[0]


class TestSerializeFrDateList(unittest.TestCase):
    """ Test class of the DateList serializer with french data. """

    def test_valid_format(self):
        """ Test the serializer on a valid date list."""
        datelist = parse(u'le 5, 6 et 7 octobre 2013', 'fr')[0]
        assert datelist.valid
        assert all([date.valid for date in datelist.dates])
        datelist_norm = datelist.to_python()
        assert datelist_norm[0] == datetime.date(year=2013, month=10, day=5)
        assert datelist_norm[1] == datetime.date(year=2013, month=10, day=6)
        assert datelist_norm[2] == datetime.date(year=2013, month=10, day=7)

    def test_missing_year(self):
        """ Test the serializer on a date with no year."""
        datelist = parse(u'le 5, 6 et 7 octobre', 'fr', valid=False)[0]
        assert not datelist.valid
        assert not datelist.dates[0].valid
        assert not datelist.dates[1].valid
        assert not datelist.dates[2].valid

    def test_to_db(self):
        """ Test the serializer on a valid date list."""
        datelist = to_db(u'le 5, 6 et 8 octobre 2013', 'fr')[0]
        assert len(datelist) == 3
        date = datelist[0]
        assert date[0] == datetime.datetime(year=2013, month=10, day=5, hour=0, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=10, day=5, hour=23, minute=59, second=59)
        date = datelist[1]
        assert date[0] == datetime.datetime(year=2013, month=10, day=6, hour=0, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=10, day=6, hour=23, minute=59, second=59)
        date = datelist[2]
        assert date[0] == datetime.datetime(year=2013, month=10, day=8, hour=0, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=10, day=8, hour=23, minute=59, second=59)

    def test_future_date_list(self):
        """ Test that the datetlist is in the future. """
        datelist = parse(u'le 5, 6 et 8 octobre 2013', 'fr')[0]
        assert datelist.future(reference=today)

    def test_past_date_list(self):
        """ Test that the datetlist is in the past. """
        datelist = parse(u'le 5, 6 et 8 octobre 2003', 'fr')[0]
        assert not datelist.future(reference=today)


class TestSerializeFrDateTime(unittest.TestCase):
    """ Test class of the DateTime serializer with french data. """

    def test_valid_format(self):
        """ Test the serializer on a valid format. """
        dt = parse(u'le lundi 15 mars 2013 à 20h', 'fr')[0]
        assert dt.valid
        assert dt.date.valid
        assert dt.time.valid
        assert dt.to_python() == datetime.datetime(
            year=2013, month=3, day=15, hour=20, minute=0)

    def test_all_formats(self):
        dt1 = parse(u'le lundi 15 mars 2013 de 15h à 20h', 'fr')[0]
        dt2 = parse(u'le lundi 15 mars 2013, 15h-20h', 'fr')[0]
        assert dt1 == dt2

    def test_to_db(self):
        """ Test the serializer on a valid date time. """
        dt = to_db(u'le lundi 15 mars 2013 à 20h', 'fr')
        assert len(dt) == 1
        date = dt[0]
        assert date[0] == datetime.datetime(year=2013, month=3, day=15, hour=20, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=3, day=15, hour=20, minute=0, second=0)

        dt = to_db(u'le lundi 15 mars 2013 de 19h à 20h', 'fr')
        assert len(dt) == 1
        date = dt[0]
        assert date[0] == datetime.datetime(year=2013, month=3, day=15, hour=19, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=3, day=15, hour=20, minute=0, second=0)

    def test_future_datetime(self):
        """ Test that the datetime is in the future. """
        dt = parse(u'le 8 octobre 2013 à 20h30', 'fr')[0]
        assert dt.future(reference=today)

    def test_past_date_list(self):
        """ Test that the datetlist is in the past. """
        dt = parse(u'le 8 octobre 2003 à 20h30', 'fr')[0]
        assert not dt.future(reference=today)


class TestSerializeFrDateTimeList(unittest.TestCase):
    """ Test class of the DateTimeList serializer with french data."""

    def test_valid_format(self):
        """ Test the serializer on a valid format."""
        datetimelist = parse(u'les 6 et 9 octobre 2013 de 15h à 20h', 'fr')[0]
        assert datetimelist.valid
        for date in datetimelist:
            assert date.valid
        datetimelist_norm = datetimelist.to_python()
        assert datetimelist_norm[0][0] == datetime.datetime(
            year=2013, month=10, day=6, hour=15, minute=0)
        assert datetimelist_norm[0][1] == datetime.datetime(
            year=2013, month=10, day=6, hour=20, minute=0)
        assert datetimelist_norm[1][0] == datetime.datetime(
            year=2013, month=10, day=9, hour=15, minute=0)
        assert datetimelist_norm[1][1] == datetime.datetime(
            year=2013, month=10, day=9, hour=20, minute=0)

    def test_all_formats(self):
        dtl1 = parse(u'les 6 et 9 octobre 2013, 15h - 20h', 'fr')[0]
        dtl2 = parse(u'6, 9 octobre 2013 entre 15h et 20h', 'fr')[0]
        dtl3 = parse(u'6, 9 octobre 2013 de 15h à 20h', 'fr')[0]
        assert dtl1 == dtl2 == dtl3

    def test_to_db(self):
        """ Test the serializer on a valid date time list. """
        datetimelist = to_db(u'les 6 et 9 octobre 2013 de 15h à 20h', 'fr')[0]

        # le 6
        date = datetimelist[0]
        assert date[0] == datetime.datetime(year=2013, month=10, day=6, hour=15, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=10, day=6, hour=20, minute=0, second=0)

        # le 7
        date = datetimelist[1]
        assert date[0] == datetime.datetime(year=2013, month=10, day=9, hour=15, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=10, day=9, hour=20, minute=0, second=0)

    def test_future_datetime_list(self):
        """ Test that the datetime is in the future. """
        dt = parse(u'le 6, 7, 8 octobre 2013 à 20h30', 'fr')[0]
        assert dt.future(reference=today)

    def test_past_datetime_list(self):
        """ Test that the datetlist is in the past. """
        dt = parse(u'le 6, 7, 8 octobre 2003 à 20h30', 'fr')[0]
        assert not dt.future(reference=today)


class TestSerializeFrDateInterval(unittest.TestCase):
    """ Test class of the DateInterval serializer with french data """

    def test_valid_format(self):
        """ Test the serialize """
        di = parse(u'du 15 au 18 février 2013', 'fr')[0]
        assert di.valid
        dateinterval = di.to_python()
        assert dateinterval[0] == datetime.date(year=2013, month=2, day=15)
        assert dateinterval[1] == datetime.date(year=2013, month=2, day=18)

    def test_all_formats(self):
        di1 = parse(u'du 15 au 18 février 2013', 'fr')[0]
        di2 = parse(u'15 au 18 février 2013', 'fr')[0]
        di3 = parse(u'15-18 février 2013', 'fr')[0]
        assert di1 == di2 == di3

    def test_to_db(self):
        """ Test the serializer on a valid dateinterval. """
        dateinterval = to_db(u'du 6 au 9 octobre 2013', 'fr')[0]

        assert len(dateinterval) == 2
        assert dateinterval[0] == datetime.datetime(year=2013, month=10, day=6, hour=0, minute=0, second=0)
        assert dateinterval[1] == datetime.datetime(year=2013, month=10, day=9, hour=23, minute=59, second=59)

    def test_future_datetime_interval(self):
        """ Test that the datetime is in the future. """
        dti = parse(u'du 7 au 8 octobre 2013 à 20h30', 'fr')[0]
        assert dti.future(reference=today)

    def test_past_datetime_list(self):
        """ Test that the datetlist is in the past. """
        dti = parse(u'du 7 au 8 octobre 2003 à 20h30', 'fr')[0]
        assert not dti.future(reference=today)


class TestSerializeFrDateTimeInterval(unittest.TestCase):
    """ Test class of the DateTimeInterval serialize with french data """

    def test_valid_format(self):
        """ Test the serialize """
        dti = parse(u'du 15 au 17 février 2013 de 14h à 18h30', 'fr')[0]
        assert dti.valid
        datetime_interval = dti.to_python()

        assert datetime_interval[0][0] == datetime.datetime(
            year=2013, month=2, day=15, hour=14, minute=0)
        assert datetime_interval[0][1] == datetime.datetime(
            year=2013, month=2, day=15, hour=18, minute=30)
        assert datetime_interval[1][0] == datetime.datetime(
            year=2013, month=2, day=16, hour=14, minute=0)
        assert datetime_interval[1][1] == datetime.datetime(
            year=2013, month=2, day=16, hour=18, minute=30)
        assert datetime_interval[2][0] == datetime.datetime(
            year=2013, month=2, day=17, hour=14, minute=0)
        assert datetime_interval[2][1] == datetime.datetime(
            year=2013, month=2, day=17, hour=18, minute=30)

    def test_to_db(self):
        """ Test the serializer on a valid dateinterval. """
        datetime_interval_list = to_db(u'du 15 au 18 février 2013 de 14h à 18h30', 'fr')[0]

        assert len(datetime_interval_list) == 4

        # 2013-02-15
        datetime_interval = datetime_interval_list[0]
        assert datetime_interval[0] == datetime.datetime(year=2013, month=2, day=15, hour=14, minute=0, second=0)
        assert datetime_interval[1] == datetime.datetime(year=2013, month=2, day=15, hour=18, minute=30, second=0)

        # 2013-02-16
        datetime_interval = datetime_interval_list[1]
        assert datetime_interval[0] == datetime.datetime(year=2013, month=2, day=16, hour=14, minute=0, second=0)
        assert datetime_interval[1] == datetime.datetime(year=2013, month=2, day=16, hour=18, minute=30, second=0)

        # 2013-02-17
        datetime_interval = datetime_interval_list[2]
        assert datetime_interval[0] == datetime.datetime(year=2013, month=2, day=17, hour=14, minute=0, second=0)
        assert datetime_interval[1] == datetime.datetime(year=2013, month=2, day=17, hour=18, minute=30, second=0)

        # 2013-02-18
        datetime_interval = datetime_interval_list[3]
        assert datetime_interval[0] == datetime.datetime(year=2013, month=2, day=18, hour=14, minute=0, second=0)
        assert datetime_interval[1] == datetime.datetime(year=2013, month=2, day=18, hour=18, minute=30, second=0)
