# -*- coding: utf8 -*-

""" Test suite of the timepoint serialize suite. """

import unittest
import sys
sys.path.insert(0, '..')

from datetime import datetime

from datection import parse, parse_to_serialized, parse_to_sql
from ..serialize import *


class TestSerializeFrDates(unittest.TestCase):
    """ Test class of the Date serializer with french data"""

    def test_valid_litteral_date(self):
        """ Test the serialization of valid years of litteral format. """
        date = parse(u'le lundi 5 mars 2013', 'fr')[0]
        assert date.valid
        assert date.timepoint == 'date'
        date_norm = date.serialize()
        assert date_norm['day'] == 5
        assert date_norm['month'] == 3
        assert date_norm['year'] == 2013

    def test_missing_weekday(self):
        """Check that missing weekday has no influence on validity."""
        assert parse(u'5 mars 2013', 'fr')[0].valid

    def test_valid_numeric_date(self):
        """ Test the normalisation of valid years of litteral formats. """
        date = parse(u'5/03/2013', 'fr')[0]
        assert date.valid
        assert date.timepoint == 'date'
        date_norm = date.serialize()
        assert date_norm['day'] == 5
        assert date_norm['month'] == 3
        assert date_norm['year'] == 2013

    def test_to_json(self):
        """ Test the serialisation of a Date object. """
        date = parse_to_serialized(u'le lundi 5 mars 2013', 'fr')[0]
        assert date['day'] == 5
        assert date['month'] == 3
        assert date['year'] == 2013
        assert date['valid'] is True
        assert date['timepoint'] == 'date'

    def test_invalid_dates(self):
        """ Check that missing date leads to invalid structure. """
        assert parse(u'5/03', 'fr', valid=False)[0].valid is False
        assert parse(u' lundi 5 mars', 'fr', valid=False)[0].valid is False

    def test_to_sql(self):
        """ Test the return format for sql insert """
        datelist = parse_to_sql(u'le lundi 5 mars 2013', 'fr')
        assert len(datelist) == 1
        date = datelist[0]
        assert date[0] == datetime.datetime(year=2013, month=3, day=5, hour=0, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=3, day=5, hour=23, minute=59, second=59)


class TestSerializeFrTimeInterval(unittest.TestCase):
    """ Test class of the Time serializer on french data. """

    def test_valid_time(self):
        """ Test the serializer on a valid time."""
        time = parse(u'15h30', 'fr')[0]
        assert time.valid
        assert time.timepoint == 'time_interval'
        time_norm = time.serialize()
        assert time_norm['start_time']['hour'] == 15
        assert time_norm['start_time']['minute'] == 30

    def test_missing_minute(self):
        """ Test the serializer on a time witout minute. """
        time = parse(u'15h', 'fr')[0]
        assert time.valid
        assert time.timepoint == 'time_interval'
        time_norm = time.serialize()
        assert time_norm['start_time']['hour'] == 15
        assert time_norm['start_time']['minute'] == 0

    def test_valid_time_interval(self):
        """ Test the serializer on a valid time *interval*"""
        time = parse(u'de 15h30 à 16h', 'fr')[0]
        assert time.valid
        assert time.timepoint == 'time_interval'
        time_norm = time.serialize()
        assert time_norm['start_time']['hour'] == 15
        assert time_norm['start_time']['minute'] == 30
        assert time_norm['end_time']['hour'] == 16
        assert time_norm['end_time']['minute'] == 0

    def test_all_interval_formats(self):
        """ Test that all supported formats lead to equivalent serialized forms."""
        assert parse(u'15h30', 'fr')[0] == parse(u'15:30', 'fr')[0]
        assert parse(u'de 15h à 18h', 'fr')[0] == parse(u'15h-18h', 'fr')[0]
        assert parse(u'entre 15h et 18h', 'fr')[0] == parse(u'15h-18h', 'fr')[0]

    def test_to_sql(self):
        """ Test the return format for sql insert """
        date_list = parse_to_sql(u'de 15h30 à 16h', 'fr')
        assert len(date_list) == 0


class TestSerializeFrDateList(unittest.TestCase):
    """ Test class of the DateList serializer with french data. """

    def test_valid_format(self):
        """ Test the serializer on a valid date list."""
        datelist = parse(u'le 5, 6 et 7 octobre 2013', 'fr')[0]
        assert datelist.timepoint == 'date_list'
        assert datelist.valid
        assert all([date.valid for date in datelist.dates])
        datelist_norm = datelist.serialize()
        assert datelist_norm['dates'][0]['day'] == 5
        assert datelist_norm['dates'][0]['month'] == 10
        assert datelist_norm['dates'][0]['year'] == 2013
        assert datelist_norm['dates'][1]['day'] == 6
        assert datelist_norm['dates'][1]['month'] == 10
        assert datelist_norm['dates'][1]['year'] == 2013
        assert datelist_norm['dates'][2]['day'] == 7
        assert datelist_norm['dates'][2]['month'] == 10
        assert datelist_norm['dates'][2]['year'] == 2013

    def test_missing_year(self):
        """ Test the serializer on a date with no year."""
        datelist = parse(u'le 5, 6 et 7 octobre', 'fr', valid=False)[0]
        assert datelist.timepoint == 'date_list'
        assert not datelist.valid
        assert not datelist.dates[0].valid
        assert not datelist.dates[1].valid
        assert not datelist.dates[2].valid

    def test_to_sql(self):
        """ Test the serializer on a valid date list."""
        datelist = parse_to_sql(u'le 5, 6 et 8 octobre 2013', 'fr')[0]
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


class TestSerializeFrDateTime(unittest.TestCase):
    """ Test class of the DateTime serializer with french data. """

    def test_valid_format(self):
        """ Test the serializer on a valid format. """
        datetime = parse(u'le lundi 15 mars 2013 à 20h', 'fr')[0]
        assert datetime.valid
        assert datetime.date.valid
        assert datetime.time.valid
        datetime_norm = datetime.serialize()
        assert datetime_norm['date']['day'] == 15
        assert datetime_norm['date']['month'] == 3
        assert datetime_norm['date']['year'] == 2013
        assert datetime_norm['time']['start_time']['hour'] == 20
        assert datetime_norm['time']['start_time']['minute'] == 0
        assert datetime_norm['time']['end_time'] is None

    def test_all_formats(self):
        dt1 = parse(u'le lundi 15 mars 2013 de 15h à 20h', 'fr')[0]
        dt2 = parse(u'le lundi 15 mars 2013, 15h-20h', 'fr')[0]
        assert dt1 == dt2

    def test_to_sql(self):
        """ Test the serializer on a valid date time. """
        dt = parse_to_sql(u'le lundi 15 mars 2013 à 20h', 'fr')
        assert len(dt) == 1
        date = dt[0]
        assert date[0] == datetime.datetime(year=2013, month=3, day=15, hour=20, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=3, day=15, hour=20, minute=0, second=0)

        dt = parse_to_sql(u'le lundi 15 mars 2013 de 19h à 20h', 'fr')
        assert len(dt) == 1
        date = dt[0]
        assert date[0] == datetime.datetime(year=2013, month=3, day=15, hour=19, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=3, day=15, hour=20, minute=0, second=0)


class TestSerializeFrDateTimeList(unittest.TestCase):
    """ Test class of the DateTimeList serializer with french data."""

    def test_valid_format(self):
        """ Test the serializer on a valid format."""
        datetimelist = parse(u'les 6 et 9 octobre 2013 de 15h à 20h', 'fr')[0]
        assert datetimelist.valid
        for date in datetimelist:
            assert date.valid
        datetimelist_norm = datetimelist.serialize()
        assert datetimelist_norm['datetimes'][0]['date']['year'] == 2013
        assert datetimelist_norm['datetimes'][0]['date']['month'] == 10
        assert datetimelist_norm['datetimes'][0]['date']['day'] == 6
        assert datetimelist_norm['datetimes'][0]['time']['start_time']['hour'] == 15
        assert datetimelist_norm['datetimes'][0]['time']['start_time']['minute'] == 0
        assert datetimelist_norm['datetimes'][0]['time']['end_time']['hour'] == 20
        assert datetimelist_norm['datetimes'][0]['time']['end_time']['minute'] == 0
        assert datetimelist_norm['datetimes'][0]['date']['day'] == 6

    def test_all_formats(self):
        dtl1 = parse(u'les 6 et 9 octobre 2013, 15h - 20h', 'fr')[0]
        dtl2 = parse(u'6, 9 octobre 2013 entre 15h et 20h', 'fr')[0]
        dtl3 = parse(u'6, 9 octobre 2013 de 15h à 20h', 'fr')[0]
        assert dtl1 == dtl2 == dtl3

    def test_to_sql(self):
        """ Test the serializer on a valid date time list. """
        datetimelist = parse_to_sql(u'les 6 et 9 octobre 2013 de 15h à 20h', 'fr')[0]

        # le 6
        date = datetimelist[0]
        assert date[0] == datetime.datetime(year=2013, month=10, day=6, hour=15, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=10, day=6, hour=20, minute=0, second=0)

        # le 7
        date = datetimelist[1]
        assert date[0] == datetime.datetime(year=2013, month=10, day=9, hour=15, minute=0, second=0)
        assert date[1] == datetime.datetime(year=2013, month=10, day=9, hour=20, minute=0, second=0)


class TestSerializeFrDateInterval(unittest.TestCase):
    """ Test class of the DateInterval serializer with french data """

    def test_valid_format(self):
        """ Test the serialize """
        di = parse(u'du 15 au 18 février 2013', 'fr')[0]
        assert di.valid
        dateinterval = di.serialize()
        assert dateinterval['start_date']['year'] == 2013
        assert dateinterval['start_date']['month'] == 02
        assert dateinterval['start_date']['day'] == 15
        assert dateinterval['end_date']['year'] == 2013
        assert dateinterval['end_date']['month'] == 02
        assert dateinterval['end_date']['day'] == 18

    def test_all_formats(self):
        di1 = parse(u'du 15 au 18 février 2013', 'fr')[0]
        di2 = parse(u'15 au 18 février 2013', 'fr')[0]
        di3 = parse(u'15-18 février 2013', 'fr')[0]
        assert di1 == di2 == di3

    def test_to_sql(self):
        """ Test the serializer on a valid dateinterval. """
        dateinterval = parse_to_sql(u'du 6 au 9 octobre 2013', 'fr')[0]

        assert len(dateinterval) == 2
        assert dateinterval[0] == datetime.datetime(year=2013, month=10, day=6, hour=0, minute=0, second=0)
        assert dateinterval[1] == datetime.datetime(year=2013, month=10, day=9, hour=23, minute=59, second=59)


class TestSerializeFrDateTimeInterval(unittest.TestCase):
    """ Test class of the DateTimeInterval serialize with french data """

    def test_valid_format(self):
        """ Test the serialize """
        dti = parse(u'du 15 au 18 février 2013 de 14h à 18h30', 'fr')[0]
        assert dti.valid
        datetime_interval = dti.serialize()
        assert datetime_interval['date_interval']['start_date']['year'] == 2013
        assert datetime_interval['date_interval']['start_date']['month'] == 02
        assert datetime_interval['date_interval']['start_date']['day'] == 15

        assert datetime_interval['date_interval']['end_date']['year'] == 2013
        assert datetime_interval['date_interval']['end_date']['month'] == 02
        assert datetime_interval['date_interval']['end_date']['day'] == 18

        assert datetime_interval['time_interval']['start_time']['hour'] == 14
        assert datetime_interval['time_interval']['start_time']['minute'] == 00
        assert datetime_interval['time_interval']['end_time']['hour'] == 18
        assert datetime_interval['time_interval']['end_time']['minute'] == 30

    def test_to_sql(self):
        """ Test the serializer on a valid dateinterval. """
        datetime_interval_list = parse_to_sql(u'du 15 au 18 février 2013 de 14h à 18h30', 'fr')[0]

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
