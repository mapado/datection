# -*- coding: utf-8 -*-

"""
Test suite of the timepoint regexes.
"""

import unittest
import sys
import re

sys.path.insert(0, '..')
from ..regex import *


class TestDateRegex(unittest.TestCase):
    """ Test class for the extraction of dates from strings.

    Examples: 13 février 2013, mardi 13 février, mardi 13 février 2013

    """
    def test_extract_perfect_date(self):
        """Test the extraction of a perfectly formatted french date."""
        text = """ Adulte : 19 € Tarif réduit : 13 €
                Mardi 19 février 2013 : de 20h à 21h20."""
        date = re.search(FR_DATE, text)
        assert date.group(0).strip() == '19 février 2013'
        # assert date.groupdict()['weekday_name'] == 'Mardi'
        assert date.groupdict()['day'] == '19'
        assert date.groupdict()['month_name'] == 'février'
        assert date.groupdict()['year'] == '2013'

    def test_ignorecase(self):
        """Test the extraction of a date with both upper and lower case."""
        text = """ Adulte : 19 € Tarif réduit : 13 €
                lundi 28 Février 2001 : de 20h à 21h20."""
        date = re.search(FR_DATE, text)
        assert date.group(0).strip() == '28 Février 2001'
        # assert date.groupdict()['weekday_name'] == 'lundi'
        assert date.groupdict()['month_name'] == 'Février'

    def test_missing_day(self):
        """Test the extraction of a date without day name."""
        text = 'Adulte : 19 € Tarif réduit : 13 € 28 Février 2001 : de 20h à 21h20.'
        date = re.search(FR_DATE, text)

        assert date.group(0).strip() == '28 Février 2001'
        # assert date.groupdict()['weekday_name'] is None
        assert date.groupdict()['day'] == '28'
        assert date.groupdict()['month_name'] == 'Février'

    def test_missing_date(self):
        """ Test that the date is mandatory for the match to happen. """
        text = 'Adulte : 19 € Tarif réduit : 13 € Février 2001 : de 20h à 21h20.'
        date = re.search(FR_DATE, text)
        assert date is None

    def test_missing_year(self):
        """Test the extraction of a date with no year."""
        text = 'Adulte : 19 € Tarif réduit : 13 € Mardi 4 Février : de 20h à 21h20.'
        date = re.search(FR_DATE, text)
        assert date.group(0).strip() == '4 Février'
        assert date.groupdict()['year'] is None

    def test_all_date_formats(self):
        """Test the extraction of the date in all possible formats.

        Accepted formats are:
        * one digit, from 1 to 9
        * two digits:
          * if the first digit is 0, 1 or 2, the second digit must be between 0 and 9
          * if the first digit is 3, the second digit must be either 0 or 1
        That way, we can extract dates bewteen 1 and 31.

        Note that the regex does not check the validity of the date/month couple.
        For example, 31 Février would be extracted, even though Février stops at 28 or 29.

        """
        # One digit dates
        text = '4 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == '4'
        text = '0 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text) is None

        # Two digits dates
        text = '09 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == '09'
        text = '14 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == '14'
        text = '24 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == '24'
        text = '31 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text).groupdict()['day'] == '31'
        text = ' 32 Février : de 20h à 21h20.'
        assert re.search(FR_DATE, text) is None

    def test_premier(self):
        """ Test the extraction of a date with a '1er' in the string. """
        date = re.search(FR_DATE, "plop le 1er juin 2012 lala")
        assert date.groupdict()['day'] == '1'
        assert date.groupdict()['month_name'] == 'juin'
        assert date.groupdict()['year'] == '2012'


class TestNumericDateRegex(unittest.TestCase):
    """ Test class for the extraction of numeric dates of format dd/mm/yyyy """

    def test_standard_format(self):
        """ Test the extraction of a numeric french date (dd/mm/yyyy)."""
        text = """ Adulte : 19 € Tarif réduit : 13 €
                19/03/2012 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == '19/03/2012'
        assert date.groupdict()['day'] == '19'
        assert date.groupdict()['month_name'] == '03'
        assert date.groupdict()['year'] == '2012'

    def test_two_digit_year_format(self):
        """ Test the extraction of a date of format dd/mm/yy """
        text = """ Adulte : 19 € Tarif réduit : 13 €
                19/03/12 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == '19/03/12'
        assert date.groupdict()['day'] == '19'
        assert date.groupdict()['month_name'] == '03'
        assert date.groupdict()['year'] == '12'

    def test_missing_year(self):
        """ Test the extraction of a date of format dd/mm """
        text = """ Adulte : 19 € Tarif réduit : 13 € 19/03 : de 20h à 21h20."""
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.group(0).strip() == '19/03'
        assert date.groupdict()['day'] == '19'
        assert date.groupdict()['month_name'] == '03'
        assert date.groupdict()['year'] is None

    def test_all_month_formats(self):
        """ Test the extraction of months with all possible formats."""
        # Regognized formats
        text = "Plop 12/12/2012 plop"
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.groupdict()['month_name'] == '12'
        text = "Plop 12/01/2012 plop"
        date = re.search(FR_NUMERIC_DATE, text)
        assert date.groupdict()['month_name'] == '01'

        # Unrecognized formats
        text = "Plop 12/1/2012 plop"
        assert re.search(FR_NUMERIC_DATE, text) is None


class TestDateIntervalRegex(unittest.TestCase):
    """ Test class for the extraction of date intervals.

    Examples: du lundi 17 au mercredi 23 octobre, du 5 au 8 octobre 2013.

    """
    def test_day_number_and_month(self):
        """ Extract date intervals of the form 'du X au Y MM YYYY' """
        text = "du lundi 17 au mercredi 23 octobre 2012: de 20h à 21h20."
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == '17'
        assert interval.groupdict()['start_month_name'] is None
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == '23'
        assert interval.groupdict()['end_month_name'] == 'octobre'
        assert interval.groupdict()['end_year'] == '2012'

    def test_only_number_and_month(self):
        """ Extract date intervals of the form 'du X au Y MM' """
        text = "du 5 au 8 octobre: de 20h à 21h20."
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == '5'
        assert interval.groupdict()['start_month_name'] is None
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == '8'
        assert interval.groupdict()['end_month_name'] == 'octobre'
        assert interval.groupdict()['end_year'] is None

    def test_premier(self):
        text = 'Du 19 janvier au 1er mai 2013'
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == '19'
        assert interval.groupdict()['start_month_name'] == 'janvier'
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == '1'
        assert interval.groupdict()['end_month_name'] == 'mai'
        assert interval.groupdict()['end_year'] == '2013'

    def test_dash_separator(self):
        text = "5-7 avril 2013"
        interval = re.search(FR_DATE_INTERVAL, text)
        assert interval.groupdict()['start_day'] == '5'
        assert interval.groupdict()['start_month_name'] is None
        assert interval.groupdict()['start_year'] is None
        assert interval.groupdict()['end_day'] == '7'
        assert interval.groupdict()['end_month_name'] == 'avril'
        assert interval.groupdict()['end_year'] == '2013'


class TestTimeRegex(unittest.TestCase):
    """ Test class for the extraction of times.

    Examples: 20h30, 20h, 20 h, 7h, 7h00, 21:20

    """
    def test_minute_and_hour(self):
        """ Extract an time composed of both minute and hour stamps."""
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 à 21h20."""
        times = re.search(FR_TIME, text)
        assert times.groupdict()['hour'] == '21'
        assert times.groupdict()['minute'] == '20'

    def test_only_hour(self):
        """ Extract a time without the minute stamp. """
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 à 21h."""
        times = re.search(FR_TIME, text)
        assert times.groupdict()['hour'] == '21'
        assert times.groupdict()['minute'] is None

    def test_colon_separator(self):
        """ Extract a time with the ':' hour/minute separator."""
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 à 7:20."""
        times = re.search(FR_TIME, text)
        assert times.groupdict()['hour'] == '7'
        assert times.groupdict()['minute'] == '20'

    def test_space_separator(self):
        """ Extract a time with a ' ' as hour/minute separator. """
        datetime = re.search(FR_TIME, "Dimanche 30 mai 2013 10 h")
        assert datetime.groupdict()['hour'] == '10'

        datetime = re.search(FR_TIME, "Dimanche 30 mai 2013 7 h20")
        assert datetime.groupdict()['hour'] == '7'
        assert datetime.groupdict()['minute'] == '20'

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
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 de 20h à 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == '20h'
        assert interval.groupdict()['end_time'] == '21h20'

        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 entre 20h et 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == '20h'
        assert interval.groupdict()['end_time'] == '21h20'

    def test_dash_separator(self):
        """ Extract a time interval from a string with '-' as separator."""
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 20h - 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == '20h'
        assert interval.groupdict()['end_time'] == '21h20'

        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 20h-21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == '20h'
        assert interval.groupdict()['end_time'] == '21h20'

    def test_single_time(self):
        """ Extract a single time from a string. """
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == '21h20'
        assert interval.groupdict()['end_time'] is None

        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013, 21 h."""
        interval = re.search(FR_TIME_INTERVAL, text)
        assert interval.groupdict()['start_time'] == '21 h'
        assert interval.groupdict()['end_time'] is None

    def test_parse_time_interval(self):
        """ Parse a matched time interval to re-create time structure. """
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 de 20h à 21h20."""
        interval = re.search(FR_TIME_INTERVAL, text)
        start_time = re.search(FR_TIME, interval.groupdict()['start_time'])
        assert start_time.groupdict()['hour'] == '20'
        assert start_time.groupdict()['minute'] is None

        end_time = re.search(FR_TIME, interval.groupdict()['end_time'])
        assert end_time.groupdict()['hour'] == '21'
        assert end_time.groupdict()['minute'] == '20'


class TestDateTimeRegex(unittest.TestCase):
    """ Test class for the extraction of datetimes.

    Example: le mardi 13 février 2013 à 15h30, 8 février 2013, 15h
        le mardi 15 mars, de 15h à 16h

    """
    def test_perfect_format(self):
        """ Extract a datetime from a perfectly formatted string. """
        text = """ Adulte : 19 € Tarif réduit :
            13 € le jeudi 13 août 2013 à 20h30."""
        datetime = re.search(FR_DATETIME, text)
        assert datetime.groupdict()['start_time'] == '20h30'
        assert datetime.groupdict()['end_time'] is None
        assert datetime.groupdict()['day'] == '13'

    def test_dash_separator(self):
        """ Extract a datetime from a string with '-' as date/time separator."""
        text = """ Adulte : 19 € Tarif réduit :
            13 € le jeudi 13 août 2013 - 20h30."""
        datetime = re.search(FR_DATETIME, text)
        assert datetime.groupdict()['start_time'] == '20h30'
        assert datetime.groupdict()['end_time'] is None
        assert datetime.groupdict()['day'] == '13'

    def test_comma_separator(self):
        """ Extract a datetime from a string with ',' as date/time separator."""
        text = """ Adulte : 19 € Tarif réduit :
            13 € 8 février, 20h30."""
        datetime = re.search(FR_DATETIME, text)
        assert datetime.groupdict()['start_time'] == '20h30'
        assert datetime.groupdict()['end_time'] is None
        assert datetime.groupdict()['day'] == '8'

    def test_interval_perfect_format(self):
        """ Test the extracton of a datetime time interval on a perfect string."""
        text = """ Adulte : 19 € Tarif réduit : 13 €
                le mardi 13 septembre de 20h à 21h20."""
        tstamp_time_int = re.search(FR_DATETIME, text)
        assert tstamp_time_int.groupdict()['day'] == '13'
        assert tstamp_time_int.groupdict()['month_name'] == 'septembre'
        assert tstamp_time_int.groupdict()['year'] is None
        assert tstamp_time_int.groupdict()['start_time'] == '20h'
        assert tstamp_time_int.groupdict()['end_time'] == '21h20'

    def test_interval_with_comma(self):
        text = 'le mardi 13 septembre, de 20h à 21h20'
        tstamp_time_int = re.search(FR_DATETIME, text)
        assert tstamp_time_int.groupdict()['day'] == '13'
        assert tstamp_time_int.groupdict()['month_name'] == 'septembre'
        assert tstamp_time_int.groupdict()['year'] is None
        assert tstamp_time_int.groupdict()['start_time'] == '20h'
        assert tstamp_time_int.groupdict()['end_time'] == '21h20'

    def test_interval_all_prefixes_suffixes(self):
        """ Test the extraction of a datetime time interval will all prefixes/suffixes."""
        # entre / et
        tstamp_time_int = re.search(FR_DATETIME,
            'le mardi 13 septembre entre 20h et 21h20.')
        assert tstamp_time_int.groupdict()['day'] == '13'
        assert tstamp_time_int.groupdict()['month_name'] == 'septembre'
        assert tstamp_time_int.groupdict()['year'] is None
        assert tstamp_time_int.groupdict()['start_time'] == '20h'
        assert tstamp_time_int.groupdict()['end_time'] == '21h20'

        # , / -
        tstamp_time_int = re.search(FR_DATETIME,
            'le mardi 13 septembre, 20h - 21h20.')
        assert tstamp_time_int.groupdict()['start_time'] == '20h'
        assert tstamp_time_int.groupdict()['end_time'] == '21h20'
        tstamp_time_int = re.search(FR_DATETIME,
            'le mardi 13 septembre, 20h-21h20.')
        assert tstamp_time_int.groupdict()['start_time'] == '20h'
        assert tstamp_time_int.groupdict()['end_time'] == '21h20'


class TestDateListRegex(unittest.TestCase):
    """ Test class for extractio of date list.

    Example: les 25, 26 et 27 février 2013.

    """
    def test_extract(self):
        """Test the extraction of a list of the form Day X, Day Y, et Day X Month."""
        text = """ Adulte : 19 € Tarif réduit :
            13 € le Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février."""
        datelist = re.search(FR_DATE_LIST_WEEKDAY, text)
        expected = "Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février"
        assert datelist.groupdict()['date_list'].strip() == expected

        text = """ Adulte : 19 € Tarif réduit :
            13 € le lundi 13 et mardi 14 février."""
        datelist = re.search(FR_DATE_LIST_WEEKDAY, text)
        expected = "lundi 13 et mardi 14 février"
        assert datelist.groupdict()['date_list'].strip() == expected


class TestDateTimeListRegex(unittest.TestCase):
    """Test class for the extraction of date time lists.

    Examples: les 25, 26 et 27 février 2013, mercredi 14 et jeudi 15 mars,
        les 25, 26 et 27 février 2013 à 15h, les 25, 26 et 27 février 2013, 15h-16h

    """
    def test_date_and_or_comma(self):
        """Checks that the date list prefix can be either 'et' or ','. """
        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26 et 27 février 2013 de 20h à 21h20."""
        datelist = re.search(FR_DATETIME_LIST, text)
        assert datelist.groupdict()['date_list'].strip() == '25, 26 et 27 février 2013'

        text = """ Adulte : 19 € Tarif réduit :
            13 € les 25, 26, 27 février 2013 de 20h à 21h20."""
        datelist = re.search(FR_DATETIME_LIST, text)
        assert datelist.groupdict()['date_list'].strip() == '25, 26, 27 février 2013'

    def test_date_time_list(self):
        text = """ Adulte : 19 € Tarif réduit :
            13 € le Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février de 20h à 21h20."""
        datelist = re.search(FR_DATETIME_LIST_WEEKDAY, text)
        expected = "Mercredi 13, jeudi 14, Vendredi 15 et mercredi 20 février"
        assert datelist.groupdict()['date_list'].strip() == expected
        assert datelist.groupdict()['start_time'] == '20h'
        assert datelist.groupdict()['end_time'] == '21h20'


class TestDateTimeIntervalRegex(unittest.TestCase):

    def test_date_time_interval(self):
        text = """Adulte : 19 € Tarif réduit :
            13 € le du 15 au 23 mai 2013 de 20h à 21h20."""
        dti = re.search(FR_DATETIME_INTERVAL, text)
        assert dti.groupdict()['start_day'] == '15'
        assert dti.groupdict()['start_month_name'] is None
        assert dti.groupdict()['start_year'] is None
        assert dti.groupdict()['end_day'] == '23'
        assert dti.groupdict()['end_month_name'] == 'mai'
        assert dti.groupdict()['end_year'] == '2013'
        assert dti.groupdict()['start_time'] == '20h'
        assert dti.groupdict()['end_time'] == '21h20'



class TestRecurrenceRegex(unittest.TestCase):
    """ Test class for the extraction of recurrent dates.

    Examples: les lundis, le lundi et mardi, les lundis et mardis

    """
    def test_recurrent_days(self):
        """ Test the extraction of reccurent days, of form 'le(s) lundi(s)' """
        text = """ Adulte : 19 € Tarif réduit : 13 € les lundis de 20h à 21h20."""
        recurrence = re.search(FR_DATE_RECURRENCE, text)
        assert recurrence.groupdict()['prefix'] == 'les'
        assert recurrence.groupdict()['start_weekday_name'] == 'lundi'

        text = """ Adulte : 19 € Tarif réduit : 13 € le lundi de 20h à 21h20."""
        recurrence = re.search(FR_DATE_RECURRENCE, text)
        assert recurrence.groupdict()['prefix'] == 'le'
        assert recurrence.groupdict()['start_weekday_name'] == 'lundi'

        text = """ Adulte : 19 € Tarif réduit : 13 € les lundi et vendredis de 20h à 21h20."""
        recurrence = re.search(FR_DATE_RECURRENCE, text)
        assert recurrence.groupdict()['prefix'] == 'les'
        assert recurrence.groupdict()['start_weekday_name'] == 'lundi'
        assert recurrence.groupdict()['suffix'] == 'et'
        assert recurrence.groupdict()['end_weekday_name'] == 'vendredi'

    def test_reccurent_intervals(self):
        """ Test the extraction of reccurent intervals; of form 'du lundi au vendredi'. """
        text = """ Adulte : 19 € Tarif réduit : 13 € du lundi au vendredi de 20h à 21h20."""
        recurrence = re.search(FR_DATE_RECURRENCE, text)
        assert recurrence.groupdict()['prefix'] == 'du'
        assert recurrence.groupdict()['start_weekday_name'] == 'lundi'
        assert recurrence.groupdict()['suffix'] == 'au'
        assert recurrence.groupdict()['end_weekday_name'] == 'vendredi'


    def test_bad_formats(self):
        text = "fermé le lundi 8"
        dates = re.findall(DAY_NUMBER, text)
        assert dates
        recurrence = re.search(FR_DATE_RECURRENCE, text)
        assert not recurrence

        text = 'plop Le lundi 18 mars plop'
        dates = re.findall(DAY_NUMBER, text)
        assert dates
        recurrence = re.search(FR_DATE_RECURRENCE, text)
        assert not recurrence


class TestDateTimeRecurrenceRegex(unittest.TestCase):
    """ Test class for the extraction of recurrent time intervals.

    Examples: 'les lundis, de 10h à 15h', 'le lundi et mardi, entre 20h et 22h'.

    """
    def test_all_formats(self):
        text = 'tous les lundis, de 15h à 16h30'
        rec_ttinverval = re.search(FR_DATETIME_RECURRENCE, text)
        assert rec_ttinverval.groupdict()['start_weekday_name'] == 'lundi'
        assert rec_ttinverval.groupdict()['start_time'] == '15h'
        assert rec_ttinverval.groupdict()['end_time'] == '16h30'

        text = 'tous les lundis, entre 15h et 16h30'
        rec_ttinverval = re.search(FR_DATETIME_RECURRENCE, text)
        assert rec_ttinverval.groupdict()['start_weekday_name'] == 'lundi'
        assert rec_ttinverval.groupdict()['start_time'] == '15h'
        assert rec_ttinverval.groupdict()['end_time'] == '16h30'

        text = 'tous les lundis entre 15h et 16h30'
        rec_ttinverval = re.search(FR_DATETIME_RECURRENCE, text)
        assert rec_ttinverval.groupdict()['start_weekday_name'] == 'lundi'
        assert rec_ttinverval.groupdict()['start_time'] == '15h'
        assert rec_ttinverval.groupdict()['end_time'] == '16h30'

        text = 'tous les mardis, dimanches de 6h à 13h'
        rec_ttinverval = re.search(FR_DATETIME_RECURRENCE, text)
        assert rec_ttinverval.groupdict()['start_weekday_name'] == 'mardi'
        assert rec_ttinverval.groupdict()['end_weekday_name'] == 'dimanche'
        assert rec_ttinverval.groupdict()['start_time'] == '6h'
        assert rec_ttinverval.groupdict()['end_time'] == '13h'

        text = 'tous les mardis et dimanches de 6h à 13h'
        rec_ttinverval = re.search(FR_DATETIME_RECURRENCE, text)
        assert rec_ttinverval.groupdict()['start_weekday_name'] == 'mardi'
        assert rec_ttinverval.groupdict()['end_weekday_name'] == 'dimanche'
        assert rec_ttinverval.groupdict()['start_time'] == '6h'
        assert rec_ttinverval.groupdict()['end_time'] == '13h'
