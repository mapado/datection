# -*- coding: utf-8 -*-

"""
Definition of language agnostic temporal expressions related regexes .

"""
import re

from pyparsing import Regex
from pyparsing import Optional
from pyparsing import oneOf

from datection.utils import normalize_2digit_year
from datection.models import Date
from datection.models import Time
from datection.models import TimeInterval
from datection.models import Datetime
from datection.models import DateList
from datection.models import DateInterval
from datection.models import DatetimeList
from datection.models import DatetimeInterval
from datection.models import ContinuousDatetimeInterval


def optional_ci(s):
    return Optional(Regex(s, flags=re.I))


def oneof_ci(choices):
    return oneOf(choices, caseless=True)


def optional_oneof_ci(choices):
    return Optional(oneof_ci(choices))


def as_int(text, start_index, match):
    """Return the integer value of the matched text."""
    return int(match[0])


def as_4digit_year(text, start_index, match):
    """Return a 4 digit, integer year from a YEAR regex match."""
    if len(match[0]) == 4:
        return int(match[0])
    elif len(match[0]) == 2:
        return int(normalize_2digit_year(match[0]))


def as_date(text, start_index, match):
    """Return a Date object from a DATE regex match."""
    year = match.year if match.year else None
    month = match.month if match.month else None
    return Date(year, month, match.day)


def as_time(text, start_index, match):
    """Return a Time object from a TIME regex match."""
    minute = match.minute if match.minute else 0
    return Time(match.hour, minute)


def as_time_interval(text, start_index, match):
    """Return a TimeInterval object from the TIME_INTERVAL regex match."""
    if not match.get('end_time'):
        match['end_time'] = match['start_time']
    return TimeInterval(match['start_time'], match['end_time'])


def as_datetime(text, start_index, match):
    """Return a Datetime object from the DATETIME regex match."""
    d = match['date']
    ti = match['time_interval']
    return Datetime(d, ti.start_time, ti.end_time)


def as_datelist(text, start_index, match):
    """Return a DateList object from the DATE_LIST regex match."""
    return DateList.from_match(list(match['dates']))


def as_date_interval(text, start_index, match):
    """Return a DateInterval object from the DATE_INTERVAL regex match."""
    return DateInterval.from_match(match['start_date'], match['end_date'])


def as_datetime_list(text, start_index, match):
    dates = DateList.from_match(list(match['dates']))
    return DatetimeList.from_match(dates, match['time_interval'])


def as_datetime_interval(text, start_index, match):
    return DatetimeInterval(match['date_interval'], match['time_interval'])


def as_continuous_datetime_interval(text, start_index, match):
    return ContinuousDatetimeInterval(
        match['start_date'],
        match['start_time'],
        match['end_date'],
        match['end_time'])

# The day number. Ex: lundi *18* juin 2013.
DAY_NUMBER = Regex(
    ur'(?<![\d])'  # not preceeded by a digit
    # OK: (0)1..(0)9...10...29, 30, 31
    ur'([0-2][0-9]|(0)?[1-9]|3[0-1]|1(?=er))'
    # no number, prices or time tags after
    # to avoid matching (20)13 in a year, (20)€ or (15)h
    # Note that is its possible for a single digit  to be matched
    # that's ok because the DAY_NUMBER regex will be used in combination
    # with others like DAYS, MONTHS, etc
    ur'( )?(?![\d|€)|h])').\
    setParseAction(as_int).\
    setResultsName('day')

# The year number. A valid year must either start with 1 or 2.
YEAR = Regex(ur'[12]\d{3}').\
    setParseAction(as_int).\
    setResultsName('year')

# hour: between 00 and 24. Can be 2 digit or 1-digit long.
# The hour it must not be preceded by another digit
# The minute must not be followed by another digit
HOUR = Regex(ur'(?<!\d)(0[0-9]|1[0-9]|2[0-4]|[0-9])(?!\d)').\
    setParseAction(as_int).\
    setResultsName('hour')

# Minute: bewteen 00 and 59
MINUTE = Regex(ur'[0-5][0-9]').\
    setParseAction(as_int).\
    setResultsName('minute')

# The numeric version of the month: 2 digits bewteen 01 and 12
NUMERIC_MONTH = Regex(ur'0[1-9]|1[0-2]').\
    setParseAction(as_int).\
    setResultsName('month')

# The numeric version of the year number, either 2 digits or 4 digits
# (ex: dd/mm/2012 or dd/mm/12)
NUMERIC_YEAR = Regex(ur'%s|\d{2}(?!\d{1,2})' % (YEAR.pattern)).\
    setParseAction(as_4digit_year).\
    setResultsName('year')
