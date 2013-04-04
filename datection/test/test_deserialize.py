# -*- coding: utf8 -*-

""" Test suite of the timepoint deserializing suite. """

import unittest
import sys
sys.path.insert(0, '..')

import datection

from datection.deserialize import deserialize


class TestDeserialize(unittest.TestCase):
    """ Test the deserialization of all the Timepoint subclasses. """

    def test_deserialize_date(self):
        date = datection.parse(u'le 15 janvier 2013', 'fr')[0]
        assert isinstance(date, datection.serialize.Date)
        ser = date.serialize()
        newdate = deserialize(ser)
        assert date == newdate

    def test_deserialize_time(self):
        time = datection.parse(u'15h30', 'fr')[0]
        assert isinstance(time, datection.serialize.TimeInterval)
        ser = time.serialize()
        newtime = deserialize(ser)
        assert time == newtime

    def test_deserialize_time_interval(self):
        time = datection.parse(u'de 15h30 à 16h30', 'fr')[0]
        assert isinstance(time, datection.serialize.TimeInterval)
        ser = time.serialize()
        newtime = deserialize(ser)
        assert time == newtime

    def test_deserialize_date_list(self):
        datelist = datection.parse(u'le 5 et 6 janvier 2013', 'fr')[0]
        assert isinstance(datelist, datection.serialize.DateList)
        ser = datelist.serialize()
        newdatelist = deserialize(ser)
        assert datelist == newdatelist

    def test_deserialize_date_interval(self):
        dateinterval = datection.parse(u'du 5 au 8 janvier 2013', 'fr')[0]
        assert isinstance(dateinterval, datection.serialize.DateInterval)
        ser = dateinterval.serialize()
        newdateinterval = deserialize(ser)
        assert dateinterval == newdateinterval

    def test_deserialize_datetime(self):
        datetime = datection.parse(u'le 5 janvier 2013 à 15h39', 'fr')[0]
        assert isinstance(datetime, datection.serialize.DateTime)
        ser = datetime.serialize()
        newdatetime = deserialize(ser)
        assert datetime == newdatetime

    def test_deserialize_datetime_list(self):
        datetimelist = datection.parse(u'les 5, 6, 7 janvier 2013, de 15h39 à 16h', 'fr')[0]
        assert isinstance(datetimelist, datection.serialize.DateTimeList)
        ser = datetimelist.serialize()
        newdatetimelist = deserialize(ser)
        assert datetimelist == newdatetimelist

    def test_deserialize_datetime_interval(self):
        datetimeinterval = datection.parse(u'du 7 au 9 janvier 2013, de 15h39 à 16h', 'fr')[0]
        assert isinstance(datetimeinterval, datection.serialize.DateTimeInterval)
        ser = datetimeinterval.serialize()
        newdatetimeinterval = deserialize(ser)
        assert datetimeinterval == newdatetimeinterval


if __name__ == '__main__':
    unittest.main()
