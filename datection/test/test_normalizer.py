# -*- coding: utf8 -*-

""" Test suite of the timepoint normalizer suite. """

import unittest
import sys
import json
sys.path.insert(0, '..')

from datection import parse, parse_to_json
from ..normalizer import *


class TestFrDateNormalizer(unittest.TestCase):
    """ Test class of the Date normalizer with french data"""

    def test_valid_litteral_date(self):
        """ Test the normalisation of valid years of litteral format. """
        date = parse(u'le lundi 5 mars 2013', 'fr')[0]
        assert date.valid
        assert date.timepoint == 'date'
        date_norm = date.to_dict()
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
        date_norm = date.to_dict()
        assert date_norm['day'] == 5
        assert date_norm['month'] == 3
        assert date_norm['year'] == 2013

    def test_to_json(self):
        """ Test the serialisation of a Date object. """
        datejson = parse_to_json('le lundi 5 mars 2013', 'fr')[0]
        date = json.loads(datejson)
        assert date['day'] == 5
        assert date['month'] == 3
        assert date['year'] == 2013
        assert date['valid'] == True
        assert date['timepoint'] == 'date'

    def test_invalid_dates(self):
        """ Check that missing date leads to invalid structure. """
        assert parse(u'5/03', 'fr')[0].valid is False
        assert parse(u'lundi 5 mars', 'fr')[0].valid is False


class TestFrTimeIntervalNormalizer(unittest.TestCase):
    """ Test class of the Time normalizer on french data. """

    def test_valid_time(self):
        """ Test the normaliser on a valid time."""
        time = parse(u'15h30', 'fr')[0]
        assert time.valid
        assert time.timepoint == 'time_interval'
        time_norm = time.to_dict()
        assert time_norm['start_time']['hour'] == 15
        assert time_norm['start_time']['minute'] == 30

    def test_missing_minute(self):
        """ Test the normaliser on a time witout minute. """
        time = parse(u'15h', 'fr')[0]
        assert time.valid
        assert time.timepoint == 'time_interval'
        time_norm = time.to_dict()
        assert time_norm['start_time']['hour'] == 15
        assert time_norm['start_time']['minute'] == 0

    def test_valid_time_interval(self):
        """ Test the normaliser on a valid time *interval*"""
        time = parse(u'de 15h30 à 16h', 'fr')[0]
        assert time.valid
        assert time.timepoint == 'time_interval'
        time_norm = time.to_dict()
        assert time_norm['start_time']['hour'] == 15
        assert time_norm['start_time']['minute'] == 30
        assert time_norm['end_time']['hour'] == 16
        assert time_norm['end_time']['minute'] == 0

    def test_all_interval_formats(self):
        """ Test that all supported formats lead to equivalent normalized forms."""
        assert parse(u'15h30', 'fr')[0] == parse(u'15:30', 'fr')[0]
        assert parse(u'de 15h à 18h', 'fr')[0] == parse(u'15h-18h', 'fr')[0]
        assert parse(u'entre 15h et 18h', 'fr')[0] == parse(u'15h-18h', 'fr')[0]


class TestFrDateListNormalizer(unittest.TestCase):
    """ Test class of the DateList normaliser with french data. """

    def test_valid_format(self):
        """ Test the normaliser on a valid date list."""
        datelist = parse(u'le 5, 6 et 7 octobre 2013', 'fr')[0]
        assert datelist.timepoint == 'date_list'
        assert datelist.valid
        assert all([date.valid for date in datelist.dates])
        datelist_norm = datelist.to_dict()
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
        """ Test the normaliser on a date with no year."""
        datelist = parse(u'le 5, 6 et 7 octobre', 'fr')[0]
        assert datelist.timepoint == 'date_list'
        assert not datelist.valid
        assert not datelist.dates[0].valid
        assert not datelist.dates[1].valid
        assert not datelist.dates[2].valid


class TestFrDateTime(unittest.TestCase):
    """ Test class of the DateTime normalizer with french data. """

    def test_valid_format(self):
        """ Test the normaliser on a valid format. """
        datetime = parse(u'le lundi 15 mars 2013 à 20h', 'fr')[0]
        assert datetime.valid
        assert datetime.date.valid
        assert datetime.time.valid
        datetime_norm = datetime.to_dict()
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


class TestFrDateTimeList(unittest.TestCase):
    """ Test class of the DateTimeList normalizer with french data."""

    def test_valid_format(self):
        """ Test the normaliser on a valid format."""
        datetimelist = parse(u'les 6 et 9 octobre 2013 de 15h à 20h', 'fr')[0]
        assert datetimelist.valid
        for date in datetimelist:
            assert date.valid
        datetimelist_norm = datetimelist.to_dict()
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