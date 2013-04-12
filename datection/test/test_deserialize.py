# -*- coding: utf-8 -*-

""" Test suite of the timepoint deserializing suite. """

import unittest
import sys
sys.path.insert(0, '..')

import datection.serialize

from datection.parse import parse
from datection.deserialize import deserialize


class TestDeserialize(unittest.TestCase):
    """ Test the deserialization of all the Timepoint subclasses.

    For each Timepoint subclass, we test that:
    *   the original instance is equal to the serialized and then
        deserialized original instance
        Eg: original == deserialize(original).serialized()
    *   Bothe original and deserialized instance have equal serialized
        reprsentations.
        Eg: original.serialize() == deserialized.serialize()

    """

    def test_deserialize_date(self):
        """ Test case for a Date instance. """
        date = parse(u'le 15 janvier 2013', 'fr')[0]
        assert isinstance(date, datection.serialize.Date)
        ser = date.serialize()
        newdate = deserialize(ser)
        assert date == newdate
        assert date.serialize() == newdate.serialize()

    def test_deserialize_time(self):
        """ Test case for a Time instance. """
        time = parse(u'15h30', 'fr')[0]
        assert isinstance(time, datection.serialize.TimeInterval)
        ser = time.serialize()
        newtime = deserialize(ser)
        assert time == newtime
        assert time.serialize() == newtime.serialize()

    def test_deserialize_time_interval(self):
        """ Test case for TimeInterval instance. """
        time = parse(u'de 15h30 à 16h30', 'fr')[0]
        assert isinstance(time, datection.serialize.TimeInterval)
        ser = time.serialize()
        newtime = deserialize(ser)
        assert time == newtime
        assert time.serialize() == newtime.serialize()

    def test_deserialize_date_list(self):
        """ Test case for a DateList instance. """
        datelist = parse(u'le 5 et 6 janvier 2013', 'fr')[0]
        assert isinstance(datelist, datection.serialize.DateList)
        ser = datelist.serialize()
        newdatelist = deserialize(ser)
        assert datelist == newdatelist
        assert datelist.serialize() == newdatelist.serialize()

    def test_deserialize_date_interval(self):
        """ Test case for a DateInterval instance. """
        dateinterval = parse(u'du 5 au 8 janvier 2013', 'fr')[0]
        assert isinstance(dateinterval, datection.serialize.DateInterval)
        ser = dateinterval.serialize()
        newdateinterval = deserialize(ser)
        assert dateinterval == newdateinterval
        assert dateinterval.serialize() == newdateinterval.serialize()

    def test_deserialize_datetime(self):
        """ Test case for a DateTime instance. """
        datetime = parse(u'le 5 janvier 2013 à 15h39', 'fr')[0]
        assert isinstance(datetime, datection.serialize.DateTime)
        ser = datetime.serialize()
        newdatetime = deserialize(ser)
        assert datetime == newdatetime
        assert datetime.serialize() == newdatetime.serialize()

    def test_deserialize_datetime_list(self):
        """ Test case for a DateTimeList instance. """
        datetimelist = parse(u'les 5, 6, 7 janvier 2013, de 15h39 à 16h', 'fr')[0]
        assert isinstance(datetimelist, datection.serialize.DateTimeList)
        ser = datetimelist.serialize()
        newdatetimelist = deserialize(ser)
        assert datetimelist == newdatetimelist
        assert datetimelist.serialize() == newdatetimelist.serialize()

    def test_deserialize_datetime_interval(self):
        """ Test case for a DateTimeInterval instance. """
        datetimeinterval = parse(u'du 7 au 9 janvier 2013, de 15h39 à 16h', 'fr')[0]
        assert isinstance(datetimeinterval, datection.serialize.DateTimeInterval)
        ser = datetimeinterval.serialize()
        newdatetimeinterval = deserialize(ser)
        assert datetimeinterval == newdatetimeinterval
        assert datetimeinterval.serialize() == newdatetimeinterval.serialize()


if __name__ == '__main__':
    unittest.main()
