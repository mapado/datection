# -*- coding: utf-8 -*-

"""
Test suite of the timepoint regexes.
"""

import unittest
import re

from datection.regex import FR_DATE
from datection.regex import FR_NUMERIC_DATE
from datection.regex import BACKWARDS_NUMERIC_DATE
from datection.regex import FR_DATE_INTERVAL
from datection.regex import FR_NUMERIC_DATE_INTERVAL
from datection.regex import FR_TIME
from datection.regex import FR_TIME_INTERVAL
from datection.regex import FR_DATETIME
from datection.regex import FR_NUMERIC_DATETIME
from datection.regex import FR_DATE_LIST_WEEKDAY
from datection.regex import FR_DATE_LIST
from datection.regex import FR_DATETIME_LIST
from datection.regex import FR_DATETIME_LIST_WEEKDAY
from datection.regex import FR_DATETIME_INTERVAL
from datection.regex import FR_WEEKDAY_RECURRENCE
from datection.regex import DAY_NUMBER
from datection.regex import FR_WEEKDAY_INTERVAL_RECURRENCE
from datection.regex import FR_CONTINUOUS_DATETIME_INTERVAL
from datection.regex import FR_CONTINUOUS_NUMERIC_DATETIME_INTERVAL


class TestDateRegex(unittest.TestCase):

    """ Test class for the extraction of dates from strings.

    Examples: 13 février 2013, mardi 13 février, mardi 13 février 2013

    """

    def test_extract_perfect_date(self):
        """Test the extraction of a perfectly formatted french date."""
        text = u""" Adulte : 19 € Tarif réduit : 13 €
                Mardi 19 février 2013 : de 20h à 21h20."""
        date = re.search(FR_DATE, text)
        assert date.group(0).strip() == u'19 février 2013'
        # assert date.groupdict()['weekday_name'] == u'Mardi'
        assert date.groupdict()['day'] == u'19'
        assert date.groupdict()['month'] == u'février'
        assert date.groupdict()['year'] == u'2013'

    def test_ignorecase(self):
        """Test the extraction of a date with both upper and lower case."""
        text = u""" Adulte : 19 € Tarif réduit : 13 €
                lundi 28 Février 2001 : de 20h à 21h20."""
        date = re.search(FR_DATE, text)
        assert date.group(0).strip() == u'28 Février 2001'
        assert date.groupdict()['month'] == u'Février'

    def test_missing_day(self):
        """Test the extraction of a date without day name."""
        text = u'Tarif réduit : 13 € 28 Février 2001 : de 20h à 21h20.'
        date = re.search(FR_DATE, text)

        assert date.group(0).strip() == u'28 Février 2001'
        assert date.groupdict()['day'] == u'28'
        assert date.groupdict()['month'] == u'Février'
        assert date.groupdict()['year'] == u'2001'

    def test_missing_date(self):
        """ Test that the date is mandatory for the match to happen. """
        text = u' Tarif réduit : 13 € Février 2001 : de 20h à 21h20.'
        date = re.search(FR_DATE, text)
        assert date is None

    def test_missing_year(self):
        """Test the extraction of a date with no year."""
        text = u'réduit : 13 € Mardi 4 Février : de 20h à 21h20.'
        date = re.search(FR_DATE, text)
        assert date.group(0).strip() == u'4 Février'
        assert date.groupdict()['year'] is None

    def test_all_date_formats(self):
        """Test the extraction of the date in all possible formats.

        Accepted formats are:
        * one digit, from 1 to 9
        * two digits:
          * if the first digit is 0, 1 or 2, the second digit must be between
            0 and 9
          * if the first digit is 3, the second digit must be either 0 or 1
        That way, we can extract dates bewteen 1 and 31.

        Note that the regex does not check the validity of the date/month
        couple. For example, '31 Février' would be extracted, even though
        February stops at 28 or 29.

        """
        # One digit dates
        text = u'4 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == u'4'
        text = u'0 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text) is None

        # Two digits dates
        text = u'09 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == u'09'
        text = u'14 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == u'14'
        text = u'24 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == u'24'
        text = u'31 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == u'31'
        text = u' 32 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text) is None

    def test_premier(self):
        """ Test the extraction of a date with a '1er' in the string. """
        date = re.search(FR_DATE, u"plop le 1er juin 2012 lala")
        assert date.groupdict()['day'] == u'1'
        assert date.groupdict()['month'] == u'juin'
        assert date.groupdict()['year'] == u'2012'

    def test_abbreviated_month(self):
        # without trailing dot
        date = re.search(FR_DATE, u"plop le 5 fev 2012 lala")
        assert date.groupdict()['day'] == u'5'
        assert date.groupdict()['month'] == u'fev'
        assert date.groupdict()['year'] == u'2012'

        # with trailing dot
        date = re.search(FR_DATE, u"plop le 5 fev. 2012 lala")
        assert date.groupdict()['day'] == u'5'
        assert date.groupdict()['month'] == u'fev.'
        assert date.groupdict()['year'] == u'2012'


class TestNumericDateRegex(unittest.TestCase):

    """ Test class for the extraction of numeric dates of format dd/mm/yyyy """

    def test_standard_format(self):
        """ Test the extraction of a numeric french date (dd/mm/yyyy)."""
        text = u""" Adulte : 19 € Tarif réduit : 13 €
                19/03/2012 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == u'19/03/2012'
        assert date.groupdict()['day'] == u'19'
        assert date.groupdict()['month'] == u'03'
        assert date.groupdict()['year'] == u'2012'

    def test_two_digit_year_format(self):
        """ Test the extraction of a date of format dd/mm/yy """
        text = u""" Adulte : 19 € Tarif réduit : 13 €
                19/03/12 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == u'19/03/12'
        assert date.groupdict()['day'] == u'19'
        assert date.groupdict()['month'] == u'03'
        assert date.groupdict()['year'] == u'12'

    def test_missing_year(self):
        """ Test the extraction of a date of format dd/mm """
        text = u""" Adulte : 19 € Tarif réduit : 13 € 19/03 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == u'19/03'
        assert date.groupdict()['day'] == u'19'
        assert date.groupdict()['month'] == u'03'
        assert date.groupdict()['year'] is None

    def test_all_month_formats(self):
        """ Test the extraction of months with all possible formats."""
        # Regognized formats
        text = u"Plop 12/12/2012 plop"
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.groupdict()['month'] == u'12'
        text = u"Plop 12/01/2012 plop"
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.groupdict()['month'] == u'01'

        # Unrecognized formats
        text = u"Plop 12/1/2012 plop"
        assert re.search(FR_NUMERIC_DATE, text) is None

    def test_dot_separator(self):
        """ Test the extraction of a numeric french date using a dot for
            separation : dd.mm.yyyy

        """
        text = u""" Adulte : 19 € Tarif réduit : 13 €
                19.03.2012 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == u'19.03.2012'
        assert date.groupdict()['day'] == u'19'
        assert date.groupdict()['month'] == u'03'
        assert date.groupdict()['year'] == u'2012'

    def test_dash_separator(self):
        """ Test the extraction of a numeric french date using a dot for
            separation : dd-mm-yyyy

        """
        text = u""" Adulte : 19 € Tarif réduit : 13 €
                19-03-2012 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == u'19-03-2012'
        assert date.groupdict()['day'] == u'19'
        assert date.groupdict()['month'] == u'03'
        assert date.groupdict()['year'] == u'2012'

    def test_backwards_numeric_date(self):
        """Test the extraction of a date of format yyyy/mm/dd"""
        match = re.search(BACKWARDS_NUMERIC_DATE, u'2014-01-19')
        self.assertEqual(match.groupdict()['year'], u'2014')
        self.assertEqual(match.groupdict()['month'], u'01')
        self.assertEqual(match.groupdict()['day'], u'19')


class TestDateIntervalRegex(unittest.TestCase):

    """ Test class for the extraction of date intervals.

    Examples: du lundi 17 au mercredi 23 octobre, du 5 au 8 octobre 2013.

    """

    def test_day_number_and_month(self):
        """ Extract date intervals of the form 'du X au Y MM YYYY' """
        text = u"du lundi 17 au mercredi 23 octobre 2012: de 20h à 21h20."
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'17'
        assert interval.groupdict()['start_month'] is None
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == u'23'
        assert interval.groupdict()['end_month'] == u'octobre'
        assert interval.groupdict()['end_year'] == u'2012'

    def test_only_number_and_month(self):
        """ Extract date intervals of the form 'du X au Y MM' """
        text = u"du 5 au 8 octobre: de 20h à 21h20."
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'5'
        assert interval.groupdict()['start_month'] is None
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == u'8'
        assert interval.groupdict()['end_month'] == u'octobre'
        assert interval.groupdict()['end_year'] is None

    def test_premier(self):
        text = u'Du 19 janvier au 1er mai 2013'
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'19'
        assert interval.groupdict()['start_month'] == u'janvier'
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == u'1'
        assert interval.groupdict()['end_month'] == u'mai'
        assert interval.groupdict()['end_year'] == u'2013'

    def test_dash_separator(self):
        text = u"5-7 avril 2013"
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'5'
        assert interval.groupdict()['start_month'] is None
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == u'7'
        assert interval.groupdict()['end_month'] == u'avril'
        assert interval.groupdict()['end_year'] == u'2013'

    def test_date_interal_separator_superior_sign(self):
        text = u"03 > 07 décembre 2013"
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'03'
        assert interval.groupdict()['start_month'] is None
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == u'07'
        assert interval.groupdict()['end_month'] == u'décembre'
        assert interval.groupdict()['end_year'] == u'2013'

    def test_numeric_date_interval(self):
        text = u"ohai du 01/12/2005 au 05/04/2007 lala"
        interval = re.search(FR_NUMERIC_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'01'
        assert interval.groupdict()['start_month'] == u'12'
        assert interval.groupdict()['start_year'] == u'2005'
        assert interval.groupdict()['end_day'] == u'05'
        assert interval.groupdict()['end_month'] == u'04'
        assert interval.groupdict()['end_year'] == u'2007'

    def test_numeric_date_interval_20th_century(self):
        text = u'plop du 30/03/1999 au 31/03/1999 plop'
        interval = re.search(FR_NUMERIC_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'30'
        assert interval.groupdict()['start_month'] == u'03'
        assert interval.groupdict()['start_year'] == u'1999'
        assert interval.groupdict()['end_day'] == u'31'
        assert interval.groupdict()['end_month'] == u'03'
        assert interval.groupdict()['end_year'] == u'1999'

    def test_numeric_date_interval_fot_separator(self):
        text = u"ohai du 01.12.2005 - 05.04.2007 lala"
        interval = re.search(FR_NUMERIC_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'01'
        assert interval.groupdict()['start_month'] == u'12'
        assert interval.groupdict()['start_year'] == u'2005'
        assert interval.groupdict()['end_day'] == u'05'
        assert interval.groupdict()['end_month'] == u'04'
        assert interval.groupdict()['end_year'] == u'2007'

    def test_numeric_date_interval_2digit_year(self):
        text = u"ohai du 01/12/05 au 05/04/07 lala"
        interval = re.search(FR_NUMERIC_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'01'
        assert interval.groupdict()['start_month'] == u'12'
        assert interval.groupdict()['start_year'] == u'05'
        assert interval.groupdict()['end_day'] == u'05'
        assert interval.groupdict()['end_month'] == u'04'
        assert interval.groupdict()['end_year'] == u'07'

    def test_numeric_date_interval_no_first_year(self):
        text = u"ohai du 01/12 au 05/04/07 lala"
        interval = re.search(FR_NUMERIC_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == u'01'
        assert interval.groupdict()['start_month'] == u'12'
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == u'05'
        assert interval.groupdict()['end_month'] == u'04'
        assert interval.groupdict()['end_year'] == u'07'


class TestTimeRegex(unittest.TestCase):

    """ Test class for the extraction of times.

    Examples: 20h30, 20h, 20 h, 7h, 7h00, 21:20

    """

    def test_minute_and_hour(self):
        """ Extract an time composed of both minute and hour stamps."""
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 à 21h20."""
        times = re.search(FR_TIME, text)
        assert times.groupdict()['hour'] == u'21'
        assert times.groupdict()['minute'] == u'20'

    def test_minute_and_hour_space_sep(self):
        """ Extract an time composed of both minute and hour stamps."""
        text = u"21 h 20"""
        times = re.search(FR_TIME, text)
        assert times.groupdict()['hour'] == u'21'
        assert times.groupdict()['minute'] == u'20'

    def test_only_hour(self):
        """ Extract a time without the minute stamp. """
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 à 21h."""
        times = re.search(FR_TIME, text)
        assert times.groupdict()['hour'] == u'21'
        assert times.groupdict()['minute'] is None

    def test_colon_separator(self):
        """ Extract a time with the ':' hour/minute separator."""
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 à 7:20."""
        times = re.search(FR_TIME, text)
        assert times.groupdict()['hour'] == u'7'
        assert times.groupdict()['minute'] == u'20'

    def test_space_separator(self):
        """ Extract a time with a ' ' as hour/minute separator. """
        datetime = re.search(FR_TIME, "Dimanche 30 mai 2013 10 h")
        assert datetime.groupdict()['hour'] == u'10'

        datetime = re.search(FR_TIME, "Dimanche 30 mai 2013 7 h20")
        assert datetime.groupdict()['hour'] == u'7'
        assert datetime.groupdict()['minute'] == u'20'

    def test_midnight(self):
        """ Extract a time when hour is midnight"""
        datetime = re.search(FR_TIME, "00h30")
        assert datetime.groupdict()['hour'] == u'00'
        assert datetime.groupdict()['minute'] == u'30'

        datetime = re.search(FR_TIME, "0h30")
        assert datetime.groupdict()['hour'] == u'0'
        assert datetime.groupdict()['minute'] == u'30'

    def test_bad_formats(self):
        """ Checks that badly formatted strings are not extracted. """
        assert re.search(FR_TIME, "Dimanche 30 mai 2013 h30") is None
        assert re.search(FR_TIME, "Dimanche 30 mai 2013 30h30") is None


class TestTimeIntervalRegex(unittest.TestCase):

    """ Test class for the extraction of time intervals.

    Examples: de 20h à 23h, entre 8h et 10h, 15h-16h30

    """

    def test_perfect_format(self):
        """ Extract a time interval from a perfectly formatted string. """
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 de 20h à 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == u'20h '
        assert interval.groupdict()['end_time'] == u'21h20'

        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 entre 20h et 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == u'20h '
        assert interval.groupdict()['end_time'] == u'21h20'

    def test_dash_separator(self):
        """ Extract a time interval from a string with '-' as separator."""
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 20h - 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == u'20h '
        assert interval.groupdict()['end_time'] == u'21h20'

        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 20h-21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == u'20h'
        assert interval.groupdict()['end_time'] == u'21h20'

    def test_single_time(self):
        """ Extract a single time from a string. """
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == u'21h20'
        assert interval.groupdict()['end_time'] is None

        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 21 h."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == u'21 h'
        assert interval.groupdict()['end_time'] is None

    def test_parse_time_interval(self):
        """ Parse a matched time interval to re-create time structure. """
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 de 20h à 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        start_time = re.search(FR_TIME, interval.groupdict()['start_time'])
        assert start_time.groupdict()['hour'] == u'20'
        assert start_time.groupdict()['minute'] is None

        end_time = re.search(FR_TIME, interval.groupdict()['end_time'])
        assert end_time.groupdict()['hour'] == u'21'
        assert end_time.groupdict()['minute'] == u'20'


class TestDateTimeRegex(unittest.TestCase):

    """ Test class for the extraction of datetimes.

    Example: le mardi 13 février 2013 à 15h30, 8 février 2013, 15h
        le mardi 15 mars, de 15h à 16h

    """

    def test_perfect_format(self):
        """ Extract a datetime from a perfectly formatted string. """
        text = u""" Adulte : 19 € Tarif réduit :
            13 € le jeudi 13 août 2013 à 20h30."""
        datetime = re.search(FR_DATETIME, text)
        assert datetime.groupdict()['start_time'] == u'20h30'
        assert datetime.groupdict()['end_time'] is None
        assert datetime.groupdict()['day'] == u'13'

    def test_dash_separator(self):
        """ Extract a datetime from a string with '-' as date/time separator."""
        text = u""" Adulte : 19 € Tarif réduit :
            13 € le jeudi 13 août 2013 - 20h30."""
        datetime = re.search(FR_DATETIME, text)
        assert datetime.groupdict()['start_time'] == u'20h30'
        assert datetime.groupdict()['end_time'] is None
        assert datetime.groupdict()['day'] == u'13'

    def test_comma_separator(self):
        """ Extract a datetime from a string with ',' as date/time separator."""
        text = u""" Adulte : 19 € Tarif réduit :
            13 € 8 février, 20h30."""
        datetime = re.search(FR_DATETIME, text)
        assert datetime.groupdict()['start_time'] == u'20h30'
        assert datetime.groupdict()['end_time'] is None
        assert datetime.groupdict()['day'] == u'8'

    def test_interval_perfect_format(self):
        """ Test the extracton of a datetime time interval on a perfect string."""
        text = u""" Adulte : 19 € Tarif réduit : 13 €
                le mardi 13 septembre de 20h à 21h20."""
        tstamp_time_int = re.search(FR_DATETIME, text)
        assert tstamp_time_int.groupdict()['day'] == u'13'
        assert tstamp_time_int.groupdict()['month'] == u'septembre'
        assert tstamp_time_int.groupdict()['year'] is None
        assert tstamp_time_int.groupdict()['start_time'] == u'20h '
        assert tstamp_time_int.groupdict()['end_time'] == u'21h20'

    def test_interval_with_comma(self):
        text = u'le mardi 13 septembre, de 20h à 21h20'
        tstamp_time_int = re.search(FR_DATETIME, text)
        assert tstamp_time_int.groupdict()['day'] == u'13'
        assert tstamp_time_int.groupdict()['month'] == u'septembre'
        assert tstamp_time_int.groupdict()['year'] is None
        assert tstamp_time_int.groupdict()['start_time'] == u'20h '
        assert tstamp_time_int.groupdict()['end_time'] == u'21h20'

    def test_interval_all_prefixes_suffixes(self):
        """ Test the extraction of a datetime time interval will all prefixes/suffixes."""
        # entre / et
        tstamp_time_int = re.search(FR_DATETIME,
                                    'le mardi 13 septembre entre 20h et 21h20.')
        assert tstamp_time_int.groupdict()['day'] == u'13'
        assert tstamp_time_int.groupdict()['month'] == u'septembre'
        assert tstamp_time_int.groupdict()['year'] is None
        assert tstamp_time_int.groupdict()['start_time'] == u'20h '
        assert tstamp_time_int.groupdict()['end_time'] == u'21h20'

        # , / -
        tstamp_time_int = re.search(FR_DATETIME,
                                    'le mardi 13 septembre, 20h - 21h20.')
        assert tstamp_time_int.groupdict()['start_time'] == u'20h '
        assert tstamp_time_int.groupdict()['end_time'] == u'21h20'
        tstamp_time_int = re.search(FR_DATETIME,
                                    'le mardi 13 septembre, 20h-21h20.')
        assert tstamp_time_int.groupdict()['start_time'] == u'20h'
        assert tstamp_time_int.groupdict()['end_time'] == u'21h20'

    def test_numerical_format(self):
        text = u'01/08/2013 21:30'
        tstamp_time_int = re.search(FR_NUMERIC_DATETIME, text)
        assert tstamp_time_int.groupdict()['day'] == u'01'
        assert tstamp_time_int.groupdict()['month'] == u'08'
        assert tstamp_time_int.groupdict()['year'] == u'2013'
        assert tstamp_time_int.groupdict()['start_time'] == u'21:30'
        assert tstamp_time_int.groupdict()['end_time'] is None


class TestDateListRegex(unittest.TestCase):

    """ Test class for extractio of date list.

    Example: les 25, 26 et 27 février 2013.

    """

    def test_extract_weekday(self):
        text = u"""Tarif réduit :
        13 € le Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février."""
        datelist = re.search(FR_DATE_LIST_WEEKDAY, text)
        expected = u"Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février"
        assert datelist.groupdict()['date_list'].strip() == expected

    def test_extract_weekday_ampersand_separator(self):
        text = u""" Adulte : 19 € Tarif réduit :
            13 € le lundi 13 & mardi 14 février."""
        datelist = re.search(FR_DATE_LIST_WEEKDAY, text)
        expected = u"lundi 13 & mardi 14 février"
        assert datelist.groupdict()['date_list'].strip() == expected

    def test_extract_no_weekday(self):
        text = u"""Plop les 13 et 14 février 2014 NOISE."""
        datelist = re.search(FR_DATE_LIST, text)
        expected = u"13 et 14 février 2014"
        assert datelist.groupdict()['date_list'].strip() == expected

    def test_extract_no_weekday_ampersand_separator(self):
        text = u"""Plop les 13 & 14 février 2014 NOISE."""
        datelist = re.search(FR_DATE_LIST, text)
        expected = u"13 & 14 février 2014"
        assert datelist.groupdict()['date_list'].strip() == expected

    def test_extract_no_weekday_comma_separator(self):
        text = u"""Plop les 13, 14 février 2014 NOISE."""
        datelist = re.search(FR_DATE_LIST, text)
        expected = u"13, 14 février 2014"
        assert datelist.groupdict()['date_list'].strip() == expected


class TestDateTimeListRegex(unittest.TestCase):

    """Test class for the extraction of date time lists.

    Examples:
        * les 25, 26 et 27 février 2013, mercredi 14 et jeudi 15 mars,
        * les 25, 26 et 27 février 2013 à 15h,
        * les 25, 26 et 27 février 2013, 15h-16h

    """

    def test_date_and_or_comma(self):
        """Checks that the date list prefix can be either 'et' or ','. """
        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 de 20h à 21h20."""
        datelist = re.search(FR_DATETIME_LIST, text)
        assert datelist.groupdict()[
            'date_list'].strip() == u'25, 26 et 27 février 2013'

        text = u""" Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 de 20h à 21h20."""
        datelist = re.search(FR_DATETIME_LIST, text)
        assert datelist.groupdict()[
            'date_list'].strip() == u'25, 26, 27 février 2013'

    def test_date_time_list(self):
        text = u""" Adulte : 19 € Tarif réduit :
            13 € le Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février de 20h à 21h20."""
        datelist = re.search(FR_DATETIME_LIST_WEEKDAY, text)
        expected = u"Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février"
        assert datelist.groupdict()['date_list'].strip() == expected
        assert datelist.groupdict()['start_time'] == u'20h '
        assert datelist.groupdict()['end_time'] == u'21h20'


class TestDateTimeIntervalRegex(unittest.TestCase):

    def test_date_time_interval(self):
        text = u"""Adulte : 19 € Tarif réduit :
            13 € le du 15 au 23 mai 2013 de 20h à 21h20."""
        dti = re.search(FR_DATETIME_INTERVAL, text)
        assert dti.groupdict()['start_day'] == u'15'
        assert dti.groupdict()['start_month'] is None
        assert dti.groupdict()['start_year'] is None
        assert dti.groupdict()['end_day'] == u'23'
        assert dti.groupdict()['end_month'] == u'mai'
        assert dti.groupdict()['end_year'] == u'2013'
        assert dti.groupdict()['start_time'] == u'20h '
        assert dti.groupdict()['end_time'] == u'21h20'


class TestWeekdayListRecurrenceRegex(unittest.TestCase):

    """ Test class for the extraction of recurrent weekdays in (possibly implicit)
    datetime intervals.

    Examples:
    * les lundis
    * le lundi et mardi
    * les lundis, mardis et dimanches
    * les lundi et mardi, du 5 au 15 mars 2013
    * les lundi et mardi, de 15 au 30 avril 2013, de 15h à 18h30
    * les lundi et mardi, de 15h à 18h30

    """

    def test_recurrent_days(self):
        """ Test the extraction of reccurent days, of form 'le(s) lundi(s)' """
        text = u""" Adulte : 19 € Tarif réduit : 13 € les lundis de 20h à 21h20."""
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()['weekdays'] == u'lundis'

        text = u""" Adulte : 19 € Tarif réduit : 13 € le lundi de 20h à 21h20."""
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()['weekdays'] == u'lundi'

        text = u""" Adulte : 19 € Tarif réduit : 13 € les lundis et vendredis de 20h à 21h20."""
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()['weekdays'] == u'lundis et vendredis'

    def test_weekdays_list(self):
        text = u""" le loto aura lieu le lundi, mardi et mercredi """
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()[
            'weekdays'] == u'lundi, mardi et mercredi'

    def test_recurrent_weedays_in_date_interval(self):
        text = u""" le loto aura lieu lundi, mardi et mercredi du 15 au 30 juin 2013 """
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()[
            'weekdays'] == u'lundi, mardi et mercredi'
        assert recurrence.groupdict()[
            'date_interval'] == u'du 15 au 30 juin 2013'
        assert recurrence.groupdict()['start_day'] == u'15'
        assert recurrence.groupdict()['start_month'] is None
        assert recurrence.groupdict()['start_year'] is None
        assert recurrence.groupdict()['end_day'] == u'30'
        assert recurrence.groupdict()['end_month'] == u'juin'
        assert recurrence.groupdict()['end_year'] == u'2013'

        text = u""" le loto aura lieu le lundi, mardi et mercredi, du 15 au 30 juin 2013 """
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()[
            'weekdays'] == u'lundi, mardi et mercredi, '
        assert recurrence.groupdict()[
            'date_interval'] == u'du 15 au 30 juin 2013'

    def test_recurrent_weedays_in_datetime_interval(self):
        text = u""" le loto aura lieu lundi, mardi, vendredi du 15 au 30 juin 2013 de 15h à 16h30 """
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()['weekdays'] == u'lundi, mardi, vendredi'
        assert recurrence.groupdict()[
            'date_interval'] == u'du 15 au 30 juin 2013'
        assert recurrence.groupdict()['start_day'] == u'15'
        assert recurrence.groupdict()['start_month'] is None
        assert recurrence.groupdict()['start_year'] is None
        assert recurrence.groupdict()['end_day'] == u'30'
        assert recurrence.groupdict()['end_month'] == u'juin'
        assert recurrence.groupdict()['end_year'] == u'2013'
        assert recurrence.groupdict()['time_interval'] == u'de 15h à 16h30'
        assert recurrence.groupdict()['start_time'] == u'15h '
        assert recurrence.groupdict()['end_time'] == u'16h30'

        text = u""" le loto aura lieu le lundi, mardi et dimanche, du 15 au 30 juin 2013, de 15h à 16h30 """
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()[
            'weekdays'] == u'lundi, mardi et dimanche, '
        assert recurrence.groupdict()[
            'date_interval'] == u'du 15 au 30 juin 2013'
        assert recurrence.groupdict()['time_interval'] == u'de 15h à 16h30'

    def test_recurrent_weedays_in_time_interval(self):
        text = u""" le loto aura lieu le lundi, mardi, vendredi de 15h à 16h30 """
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert recurrence.groupdict()['weekdays'] == u'lundi, mardi, vendredi'
        assert recurrence.groupdict()['date_interval'] is None
        assert recurrence.groupdict()['time_interval'] == u'de 15h à 16h30'
        assert recurrence.groupdict()['start_time'] == u'15h '
        assert recurrence.groupdict()['end_time'] == u'16h30'

    def test_bad_formats(self):
        text = u"fermé le lundi 8"
        dates = re.findall(DAY_NUMBER, text)
        assert dates
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert not recurrence

        text = u'plop Le lundi 18 mars plop'
        dates = re.findall(DAY_NUMBER, text)
        assert dates
        recurrence = re.search(FR_WEEKDAY_RECURRENCE, text)
        assert not recurrence


class TestWeekdayIntervalRecurrenceRegex(unittest.TestCase):

    def test_detection(self):
        text = u"du lundi au vendredi"
        match = re.search(FR_WEEKDAY_INTERVAL_RECURRENCE, text)
        self.assertEqual(match.group(), text)

    def test_detection_time(self):
        text = u"du lundi au vendredi, de 5h à 8h"
        match = re.search(FR_WEEKDAY_INTERVAL_RECURRENCE, text)
        self.assertEqual(match.group(), text)


class TestContinuousDatetimeIntervalRegex(unittest.TestCase):

    def test_detection(self):
        text = u"du 16 mai 2014 à 20h00 à 17 mai 2014 à 6h"
        match = re.search(FR_CONTINUOUS_DATETIME_INTERVAL, text)
        self.assertIsNotNone(match)
        gdict = match.groupdict()
        self.assertEqual(gdict['start_day'], u'16')
        self.assertEqual(gdict['start_month'], u'mai')
        self.assertEqual(gdict['start_year'], u'2014')
        self.assertEqual(gdict['start_time'], u'20h00')
        self.assertEqual(gdict['end_day'], u'17')
        self.assertEqual(gdict['end_month'], u'mai')
        self.assertEqual(gdict['end_year'], u'2014')
        self.assertEqual(gdict['end_time'], u'6h')

    def test_detection_no_year(self):
        text = u"du 16 mai à 20h00 au 17 mai 2014 à 6h"
        match = re.search(FR_CONTINUOUS_DATETIME_INTERVAL, text)
        self.assertIsNotNone(match)
        gdict = match.groupdict()
        self.assertEqual(gdict['start_day'], u'16')
        self.assertEqual(gdict['start_month'], u'mai')
        self.assertIsNone(gdict['start_year'])
        self.assertEqual(gdict['start_time'], u'20h00')
        self.assertEqual(gdict['end_day'], u'17')
        self.assertEqual(gdict['end_month'], u'mai')
        self.assertEqual(gdict['end_year'], u'2014')
        self.assertEqual(gdict['end_time'], u'6h')

    def test_detection_numeric_date(self):
        text = u"du 16/05/2014 à 20h00 au 17/05/2014 à 6h"
        match = re.search(FR_CONTINUOUS_NUMERIC_DATETIME_INTERVAL, text)
        self.assertIsNotNone(match)
        gdict = match.groupdict()
        self.assertEqual(gdict['start_day'], u'16')
        self.assertEqual(gdict['start_month'], u'05')
        self.assertEqual(gdict['start_year'], u'2014')
        self.assertEqual(gdict['start_time'], u'20h00')
        self.assertEqual(gdict['end_day'], u'17')
        self.assertEqual(gdict['end_month'], u'05')
        self.assertEqual(gdict['end_year'], u'2014')
        self.assertEqual(gdict['end_time'], u'6h')

    def test_detection_numeric_date_no_year(self):
        text = u"du 16/05 à 20h00 à 17/05/2014 à 06h"
        match = re.search(FR_CONTINUOUS_NUMERIC_DATETIME_INTERVAL, text)
        self.assertIsNotNone(match)
        gdict = match.groupdict()
        self.assertEqual(gdict['start_day'], u'16')
        self.assertEqual(gdict['start_month'], u'05')
        self.assertIsNone(gdict['start_year'])
        self.assertEqual(gdict['start_time'], u'20h00')
        self.assertEqual(gdict['end_day'], u'17')
        self.assertEqual(gdict['end_month'], u'05')
        self.assertEqual(gdict['end_year'], u'2014')
        self.assertEqual(gdict['end_time'], u'06h')
