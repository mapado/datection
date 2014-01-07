# -*- coding: utf-8 -*-

""" Test suite of the timepoint serialize suite. """

import unittest
import datetime

from datection.parse import parse


# We pretend to be in the past
today = datetime.date(day=5, month=10, year=2008)


class TestNormalizeFrDates(unittest.TestCase):

    """ Test class of the Date serializer with french data"""

    def test_valid_litteral_date(self):
        """ Test the serialization of valid years of litteral format. """
        date = parse(u'le lundi 5 mars 2013', 'fr')[0]
        self.assertTrue(date.valid)
        date_norm = date.to_python()
        self.assertEqual(date_norm, datetime.date(year=2013, month=3, day=5))

    def test_missing_weekday(self):
        """Check that missing weekday has no influence on validity."""
        self.assertTrue(parse(u'5 mars 2013', 'fr')[0].valid)

    def test_valid_numeric_date(self):
        """ Test the normalisation of valid years of litteral formats. """
        date = parse(u'5/03/2013', 'fr')[0]
        self.assertTrue(date.valid)
        date_norm = date.to_python()
        self.assertEqual(date_norm, datetime.date(year=2013, month=3, day=5))

    def test_missing_year(self):
        """ Check that missing year does not lead to invalid structure.

        A missing year will be set to the current year

        """
        self.assertTrue(parse(u'5/03', 'fr')[0].valid)
        self.assertTrue(parse(u' lundi 5 mars', 'fr')[0].valid)

        d_no_year = parse(u'le 15 février de 15h à 20h, plop', 'fr')[0]
        self.assertEqual(d_no_year.date.year, datetime.date.today().year + 1)
        self.assertTrue(d_no_year.valid)
        self.assertTrue(d_no_year.date.valid)

    def test_future_date(self):
        """ Test that the date is in the future. """
        date = parse(u'le mercredi 16 décembre 2013', 'fr')[0]
        self.assertTrue(date.future(reference=today))

    def test_past_date(self):
        """ Test that the date is in the past. """
        date = parse(u'le mercredi 16 décembre 2003', 'fr')[0]
        self.assertFalse(date.future(reference=today))

    def test_numeric_2digit_format(self):
        """Test that numeric dates with a 2 digit year are
        properly serialized.

        """
        # past date
        date = parse(u'06/01/78', 'fr')[0]
        self.assertEqual(date.year, 1978)

        date = parse(u'06/01/15', 'fr')[0]
        self.assertEqual(date.year, 2015)

    def test_redundant_dates(self):
        """Test that redundant serialized dates are only returned once
        from the parse function.

        """
        dates = parse(u'le 15 février 2013, plop, 15/02/2013', 'fr')
        self.assertEqual(len(dates), 1)

    def test_serialize_abbreviated_month(self):
        """ Test that an abbreviated month is correctlyt serialized, with or
            without trailing dot.

        """
        date = parse(u'le lundi 5 mar 2013', 'fr')[0]  # no trailing dot
        self.assertEqual(date.month, 3)

        date = parse(u'le lundi 5 mar. 2013', 'fr')[0]  # no trailing dot
        self.assertEqual(date.month, 3)


class TestNormalizeFrTimeInterval(unittest.TestCase):

    """ Test class of the Time serializer on french data. """

    def test_valid_time(self):
        """ Test the serializer on a valid time."""
        time = parse(u'15h30', 'fr')[0]
        self.assertTrue(time.valid)
        time_norm = time.to_python()
        self.assertEqual(time_norm, datetime.time(hour=15, minute=30))

    def test_missing_minute(self):
        """ Test the serializer on a time witout minute. """
        time = parse(u'15h', 'fr')[0]
        self.assertTrue(time.valid)
        time_norm = time.to_python()
        self.assertEqual(time_norm, datetime.time(hour=15, minute=0))

    def test_valid_time_interval(self):
        """ Test the serializer on a valid time *interval*"""
        time = parse(u'de 15h30 à 16h', 'fr')[0]
        self.assertTrue(time.valid)
        time_norm = time.to_python()
        st_time = datetime.time(hour=15, minute=30)
        end_time = datetime.time(hour=16, minute=0)
        self.assertEqual(time_norm, (st_time, end_time))

    def test_all_interval_formats(self):
        """ Test that all supported formats lead to equivalent serialized forms."""
        self.assertIsNotNone(
            parse(u'15h30', 'fr')[0], parse(u'15:30', 'fr')[0])
        self.assertIsNotNone(
            parse(u'de 15h à 18h', 'fr')[0], parse(u'15h-18h', 'fr')[0])
        self.assertIsNotNone(parse(u'entre 15h et 18h', 'fr')[
            0], parse(u'15h-18h', 'fr')[0])

    def test_to_python_no_end_time(self):
        """Test the format of the to_python method when no end_time is found
        """
        time = parse(u'15h', 'fr')[0]
        time_norm = time.to_python()
        self.assertEqual(time_norm, datetime.time(hour=15, minute=0))

    def test_to_python(self):
        """Test the format of the to_python method """
        time = parse(u'de 15h à 16h', 'fr')[0]
        time_norm = time.to_python()
        self.assertEqual(
            time_norm,
            (datetime.time(hour=15, minute=0),
             datetime.time(hour=16, minute=0)))


class TestNormalizeFrDateList(unittest.TestCase):

    """ Test class of the DateList serializer with french data. """

    def test_valid_format(self):
        """ Test the serializer on a valid date list."""
        datelist = parse(u'le 5, 6 et 7 octobre 2013', 'fr')[0]
        self.assertTrue(datelist.valid)
        self.assertTrue(all([date.valid for date in datelist.dates]))
        datelist_norm = datelist.to_python()
        self.assertEqual(
            datelist_norm[0], datetime.date(year=2013, month=10, day=5))
        self.assertEqual(
            datelist_norm[1], datetime.date(year=2013, month=10, day=6))
        self.assertEqual(
            datelist_norm[2], datetime.date(year=2013, month=10, day=7))

    def test_missing_year(self):
        """ Test the serializer on a date with no year.

        If the year is missing, the current year is assigned

        """
        datelist = parse(u'le 5, 6 et 7 octobre', 'fr')[0]
        next_year = datetime.date.today().year + 1
        self.assertTrue(datelist.valid)
        self.assertTrue(datelist.dates[0].valid)
        self.assertEqual(datelist.dates[0].year, next_year)
        self.assertTrue(datelist.dates[1].valid)
        self.assertEqual(datelist.dates[1].year, next_year)
        self.assertTrue(datelist.dates[2].valid)
        self.assertEqual(datelist.dates[2].year, next_year)

    def test_to_python(self):
        """ Test the return value of the to_python mehod """
        datelist = parse(u'le 5 et 6 octobre 2013', 'fr')[0].to_python()
        self.assertEqual(
            datelist[0], datetime.date(year=2013, month=10, day=5))
        self.assertEqual(
            datelist[1], datetime.date(year=2013, month=10, day=6))

    def test_future_date_list(self):
        """ Test that the datetlist is in the future. """
        datelist = parse(u'le 5, 6 et 8 octobre 2013', 'fr')[0]
        self.assertTrue(datelist.future(reference=today))

    def test_past_date_list(self):
        """ Test that the datetlist is in the past. """
        datelist = parse(u'le 5, 6 et 8 octobre 2003', 'fr')[0]
        self.assertFalse(datelist.future(reference=today))


class TestNormalizeFrDateTime(unittest.TestCase):

    """ Test class of the DateTime serializer with french data. """

    def test_valid_format(self):
        """ Test the serializer on a valid format. """
        dt = parse(u'le lundi 15 mars 2013 à 20h', 'fr')[0]
        self.assertTrue(dt.valid)
        self.assertTrue(dt.date.valid)
        self.assertTrue(dt.time.valid)
        self.assertEqual(dt.to_python(), datetime.datetime(
            year=2013, month=3, day=15, hour=20, minute=0))

    def test_all_formats(self):
        dt1 = parse(u'le lundi 15 mars 2013 de 15h à 20h', 'fr')[0]
        dt2 = parse(u'le lundi 15 mars 2013, 15h-20h', 'fr')[0]
        self.assertEqual(dt1, dt2)

    def test_future_datetime(self):
        """ Test that the datetime is in the future. """
        dt = parse(u'le 8 octobre 2013 à 20h30', 'fr')[0]
        self.assertTrue(dt.future(reference=today))

    def test_past_date_list(self):
        """ Test that the datetlist is in the past. """
        dt = parse(u'le 8 octobre 2003 à 20h30', 'fr')[0]
        self.assertFalse(dt.future(reference=today))

    def test_missing_year(self):
        """ test the normalisation of a datetime with a missing year """
        dt = parse(u'le 8 octobre à 20h30', 'fr')[0]
        self.assertEqual(dt.date.year, datetime.date.today().year + 1)
        self.assertTrue(dt.valid)
        self.assertTrue(dt.date.valid)
        self.assertTrue(dt.time.valid)

    def test_numerical_format(self):
        dt = parse(u'01/04/2014 20h30', 'fr')[0]
        self.assertEqual(dt.date.day, 1)
        self.assertEqual(dt.date.month, 4)
        self.assertEqual(dt.date.year, 2014)
        self.assertEqual(dt.time.start_time.hour, 20)
        self.assertEqual(dt.time.start_time.minute, 30)


class TestNormalizeFrDateTimeList(unittest.TestCase):

    """ Test class of the DateTimeList serializer with french data."""

    def test_valid_format(self):
        """ Test the serializer on a valid format."""
        datetimelist = parse(u'les 6 et 9 octobre 2013 de 15h à 20h', 'fr')[0]
        self.assertTrue(datetimelist.valid)
        for date in datetimelist:
            self.assertTrue(date.valid)
        datetimelist_norm = datetimelist.to_python()
        self.assertEqual(datetimelist_norm[0][0], datetime.datetime(
            year=2013, month=10, day=6, hour=15, minute=0))
        self.assertEqual(datetimelist_norm[0][1], datetime.datetime(
            year=2013, month=10, day=6, hour=20, minute=0))
        self.assertEqual(datetimelist_norm[1][0], datetime.datetime(
            year=2013, month=10, day=9, hour=15, minute=0))
        self.assertEqual(datetimelist_norm[1][1], datetime.datetime(
            year=2013, month=10, day=9, hour=20, minute=0))

    def test_all_formats(self):
        dtl1 = parse(u'les 6 et 9 octobre 2013, 15h - 20h', 'fr')[0]
        dtl2 = parse(u'6, 9 octobre 2013 entre 15h et 20h', 'fr')[0]
        dtl3 = parse(u'6, 9 octobre 2013 de 15h à 20h', 'fr')[0]
        self.assertIsNotNone(dtl1)
        self.assertIsNotNone(dtl2)
        self.assertIsNotNone(dtl3)

    def test_to_python(self):
        datetimelist = parse(
            u'les 6 et 9 octobre 2013 de 15h à 20h', 'fr')[0].to_python()

        # le 6
        date = datetimelist[0]
        self.assertEqual(date[0], datetime.datetime(
            year=2013, month=10, day=6, hour=15, minute=0, second=0))
        self.assertEqual(date[1], datetime.datetime(
            year=2013, month=10, day=6, hour=20, minute=0, second=0))

        # le 7
        date = datetimelist[1]
        self.assertEqual(date[0], datetime.datetime(
            year=2013, month=10, day=9, hour=15, minute=0, second=0))
        self.assertEqual(date[1], datetime.datetime(
            year=2013, month=10, day=9, hour=20, minute=0, second=0))

    def test_future_datetime_list(self):
        """ Test that the datetime is in the future. """
        dt = parse(u'le 6, 7, 8 octobre 2013 à 20h30', 'fr')[0]
        self.assertTrue(dt.future(reference=today))

    def test_past_datetime_list(self):
        """ Test that the datetlist is in the past. """
        dt = parse(u'le 6, 7, 8 octobre 2003 à 20h30', 'fr')[0]
        self.assertFalse(dt.future(reference=today))

    def test_missing_year(self):
        """ Test the normalisation of a datetimelist in the case
            where the date is missing

        """
        dtl = parse(u'le 6, 7, 8 octobre à 20h30', 'fr')[0]
        self.assertTrue(dtl.valid)
        self.assertEqual(
            dtl.datetimes[0].date.year, datetime.date.today().year + 1)
        self.assertEqual(
            dtl.datetimes[1].date.year, datetime.date.today().year + 1)
        self.assertEqual(
            dtl.datetimes[2].date.year, datetime.date.today().year + 1)


class TestNormalizeFrDateInterval(unittest.TestCase):

    """ Test class of the DateInterval serializer with french data """

    def test_litteral_format(self):
        """ Test the serializer """
        di = parse(u'du 15 au 18 février 2013', 'fr')[0]
        self.assertTrue(di.valid)
        dateinterval = di.to_python()
        self.assertEqual(
            dateinterval[0], datetime.date(year=2013, month=2, day=15))
        self.assertEqual(
            dateinterval[1], datetime.date(year=2013, month=2, day=18))

    def test_numeric_format(self):
        di = parse(u'du 03/04/2011 au 05/06/2012', 'fr')[0]
        self.assertTrue(di.valid)
        dateinterval = di.to_python()
        self.assertEqual(
            dateinterval[0], datetime.date(year=2011, month=4, day=3))
        self.assertEqual(
            dateinterval[1], datetime.date(year=2012, month=6, day=5))

    def test_numeric_format_2digit_year(self):
        di = parse(u'du 03/04/11 au 05/06/12', 'fr')[0]
        self.assertTrue(di.valid)
        dateinterval = di.to_python()
        self.assertEqual(
            dateinterval[0], datetime.date(year=2011, month=4, day=3))
        self.assertEqual(
            dateinterval[1], datetime.date(year=2012, month=6, day=5))

        # Test the special case where the 2 digit year starts with 0
        di = parse(u'du 03/04/07 au 05/06/07', 'fr')[0]
        self.assertTrue(di.valid)
        dateinterval = di.to_python()
        self.assertEqual(
            dateinterval[0], datetime.date(year=2007, month=4, day=3))
        self.assertEqual(
            dateinterval[1], datetime.date(year=2007, month=6, day=5))

    def test_all_formats(self):
        di1 = parse(u'du 15 au 18 février 2013', 'fr')[0]
        di2 = parse(u'15 au 18 février 2013', 'fr')[0]
        di3 = parse(u'15-18 février 2013', 'fr')[0]
        self.assertIsNotNone(di1)
        self.assertIsNotNone(di2)
        self.assertIsNotNone(di3)

    def test_to_python(self):
        dateinterval = parse(u'du 6 au 9 octobre 2013', 'fr')[0].to_python()

        self.assertEqual(len(dateinterval), 2)
        self.assertEqual(
            dateinterval[0], datetime.date(year=2013, month=10, day=6))
        self.assertEqual(
            dateinterval[1], datetime.date(year=2013, month=10, day=9))

    def test_missing_year(self):
        """ Test then normalisation of a datetimeinterval
            in the case of a missing year

        """
        di = parse(u'du 6 au 9 octobre', 'fr')[0]
        self.assertTrue(di.start_date.valid)
        self.assertTrue(di.end_date.valid)
        self.assertEqual(di.start_date.year, datetime.date.today().year + 1)
        self.assertEqual(di.end_date.year, datetime.date.today().year + 1)
        self.assertTrue(di.valid)

    def test_numeric_dates_missing_first_year(self):
        """ Test then normalisation of a datetimeinterval in the case of
            numeric dates with the first year missing

        """
        di = parse(u'du 01/03 au 05/04/07 il pleuvra', 'fr')[0]
        self.assertTrue(di.start_date.valid)
        self.assertTrue(di.end_date.valid)
        self.assertEqual(di.start_date.year, di.end_date.year)
        self.assertEqual(di.end_date.year, 2007)
        self.assertTrue(di.valid)

    def test_numeric_dates_end_date_next_year(self):
        """ Test then normalisation of a datetimeinterval in the case of
            end month in the year after the start date

        """
        di = parse(u'du 01/12 au 05/04/07 il pleuvra', 'fr')[0]
        self.assertEqual(di.start_date.year, 2006)
        self.assertEqual(di.end_date.year, 2007)

    def test_numeric_dates_end_date_next_year_implicit(self):
        """ Test then normalisation of a datetimeinterval in the case of
            end month in the year after the start date with implicit years

        """
        di = parse(u'du 01/12 au 05/04 il pleuvra', 'fr')[0]
        self.assertEqual(di.start_date.year, datetime.date.today().year)
        self.assertEqual(di.end_date.year, datetime.date.today().year + 1)


class TestNormalizeFrDateTimeInterval(unittest.TestCase):

    """ Test class of the DateTimeInterval serialize with french data """

    def test_litteral_format(self):
        """ Test the serialize """
        dti = parse(u'du 15 au 17 février 2013 de 14h à 18h30', 'fr')[0]
        self.assertTrue(dti.valid)
        datetime_interval = dti.to_python()

        self.assertEqual(datetime_interval[0][0], datetime.datetime(
            year=2013, month=2, day=15, hour=14, minute=0))
        self.assertEqual(datetime_interval[0][1], datetime.datetime(
            year=2013, month=2, day=15, hour=18, minute=30))
        self.assertEqual(datetime_interval[1][0], datetime.datetime(
            year=2013, month=2, day=16, hour=14, minute=0))
        self.assertEqual(datetime_interval[1][1], datetime.datetime(
            year=2013, month=2, day=16, hour=18, minute=30))
        self.assertEqual(datetime_interval[2][0], datetime.datetime(
            year=2013, month=2, day=17, hour=14, minute=0))
        self.assertEqual(datetime_interval[2][1], datetime.datetime(
            year=2013, month=2, day=17, hour=18, minute=30))

    def test_numeric_format(self):
        dti = parse(u'du 16/02 au 17/02/13 : de 14h à 18h30', 'fr')[0]
        self.assertTrue(dti.valid)
        datetime_interval = dti.to_python()

        self.assertEqual(datetime_interval[0][0], datetime.datetime(
            year=2013, month=2, day=16, hour=14, minute=0))
        self.assertEqual(datetime_interval[0][1], datetime.datetime(
            year=2013, month=2, day=16, hour=18, minute=30))
        self.assertEqual(datetime_interval[1][0], datetime.datetime(
            year=2013, month=2, day=17, hour=14, minute=0))
        self.assertEqual(datetime_interval[1][1], datetime.datetime(
            year=2013, month=2, day=17, hour=18, minute=30))

    def test_to_python(self):
        datetime_interval_list = parse(
            u'du 15 au 16 février 2013 à 18h30', 'fr')[0].to_python()

        self.assertEqual(len(datetime_interval_list), 2)

        # 2013-02-15
        datetime_interval = datetime_interval_list[0]
        self.assertEqual(datetime_interval, datetime.datetime(
            year=2013, month=2, day=15, hour=18, minute=30, second=0))

        # 2013-02-16
        datetime_interval = datetime_interval_list[1]
        self.assertEqual(datetime_interval, datetime.datetime(
            year=2013, month=2, day=16, hour=18, minute=30, second=0))

    def test_future_datetime_interval(self):
        """ Test that the datetime is in the future. """
        dti = parse(u'du 7 au 8 octobre 2013 à 20h30', 'fr')[0]
        self.assertTrue(dti.future(reference=today))

    def test_past_datetime_list(self):
        """ Test that the datetlist is in the past. """
        dti = parse(u'du 7 au 8 octobre 2003 à 20h30', 'fr')[0]
        self.assertFalse(dti.future(reference=today))


class TestNormalizeContinuousDatetimeInterval(unittest.TestCase):

    def test_litteral_format(self):
        text = u"Du 8 mars 2013 à 20h00 au 9 mars 2013 à 5h"
        cdti = parse(text, 'fr')[0]
        self.assertEqual(cdti.start_datetime.to_python(),
                         datetime.datetime(2013, 3, 8, 20, 0))
        self.assertEqual(cdti.end_datetime.to_python(),
                         datetime.datetime(2013, 3, 9, 5, 0))

    def test_litteral_format_no_first_year(self):
        text = u"Du 8 mars à 20h00 au 9 mars 2013 à 5h"
        cdti = parse(text, 'fr')[0]
        self.assertEqual(cdti.start_datetime.to_python(),
                         datetime.datetime(2013, 3, 8, 20, 0))
        self.assertEqual(cdti.end_datetime.to_python(),
                         datetime.datetime(2013, 3, 9, 5, 0))

    def test_numeric_format(self):
        text = u"Du 8/07/2013 à 23h00 au 9/07/2013 à 2h"
        cdti = parse(text, 'fr')[0]
        self.assertEqual(cdti.start_datetime.to_python(),
                         datetime.datetime(2013, 7, 8, 23, 0))
        self.assertEqual(cdti.end_datetime.to_python(),
                         datetime.datetime(2013, 7, 9, 2, 0))

    def test_numeric_format_no_first_year(self):
        text = u"Du 8/07 à 23:00 au 9/07/2013 à 2:00"
        cdti = parse(text, 'fr')[0]
        self.assertEqual(cdti.start_datetime.to_python(),
                         datetime.datetime(2013, 7, 8, 23, 0))
        self.assertEqual(cdti.end_datetime.to_python(),
                         datetime.datetime(2013, 7, 9, 2, 0))

    def test_future(self):
        reference = datetime.date(2012, 8, 17)
        text = u"Du 8 mars 2013 - 20h00 au 9 mars 2013 - 5h"
        cdti = parse(text, 'fr')[0]
        self.assertTrue(cdti.future(reference))

    def test_past(self):
        reference = datetime.date(2014, 8, 17)
        text = u"8 mars 2013 à 20h00 à 9 mars 2013 à 5h"
        cdti = parse(text, 'fr')[0]
        self.assertFalse(cdti.future(reference))

    def test_rrulestr(self):
        text = u"Du 8 mars 2013 à 20h00 au 9 mars 2013 à 5h"
        cdti = parse(text, 'fr')[0]
        expected = ("DTSTART:20130308\nRRULE:FREQ=DAILY;BYHOUR=20;BYMINUTE=0;"
                    "INTERVAL=1;UNTIL=20130309T235959")
        self.assertEqual(cdti.rrulestr, expected)

    def test_to_db(self):
        text = u"Du 8 mars 2013 à 20h00 à 9 mars 2013 à 5h"
        cdti = parse(text, 'fr')[0]
        to_db = cdti.to_db()
        self.assertEqual(to_db['duration'], 540)
        self.assertTrue(to_db['continuous'])
