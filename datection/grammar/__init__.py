# -*- coding: utf-8 -*-

"""
Definition of language agnostic temporal expressions related regexes .

"""
import re

from dateutil.rrule import weekdays
from dateutil.rrule import weekday
from pyparsing import Regex
from pyparsing import Optional
from pyparsing import oneOf

from datection.utils import normalize_2digit_year
from datection.timepoint import Date
from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import Datetime
from datection.timepoint import DateList
from datection.timepoint import DateInterval
from datection.timepoint import DatetimeList
from datection.timepoint import DatetimeInterval
from datection.timepoint import ContinuousDatetimeInterval
from datection.timepoint import WeeklyRecurrence
from datection.timepoint import Weekdays


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
        year = int(match[0])
    elif len(match[0]) == 2:
        year = int(normalize_2digit_year(match[0]))
    return year


def as_date(text, start_index, matches):
    """Return a Date object from a DATE regex match."""
    year = matches.get('year') if matches.get('year') else None
    month = matches.get('month') if matches.get('month') else None
    day = matches.get('day') if matches.get('day') else None
    return Date(year, month, day)


def as_time(text, start_index, matches):
    """Return a Time object from a TIME regex match."""
    hour = matches['hour']
    minute = matches.get('minute') if matches.get('minute') else 0
    return Time(hour, minute)


def as_time_interval(text, start_index, matches):
    """Return a TimeInterval object from the TIME_INTERVAL regex match."""
    if not matches.get('end_time'):
        matches['end_time'] = matches['start_time']
    return TimeInterval(matches['start_time'], matches['end_time'])


def as_datetime(text, start_index, matches):
    """Return a Datetime object from the DATETIME regex match."""
    d = matches['date']
    ti = matches['time_interval']
    return Datetime(d, ti.start_time, ti.end_time)


def as_datelist(text, start_index, matches):
    """Return a DateList object from the DATE_LIST regex match."""
    dates = list(matches['dates'])
    return DateList.from_match(dates)


def as_date_interval(text, start_index, matches):
    """Return a DateInterval object from the DATE_INTERVAL regex match."""
    sd = matches['start_date']
    ed = matches['end_date']
    return DateInterval.from_match(sd, ed)


def as_datetime_list(text, start_index, matches):
    match_dates = list(matches['dates'])
    dates = DateList.from_match(match_dates)
    return DatetimeList.from_match(dates, matches['time_interval'])


def as_datetime_interval(text, start_index, matches):
    di = matches['date_interval']
    ti = matches['time_interval']
    return DatetimeInterval(di, ti)


def as_continuous_datetime_interval(text, start_index, matches):
    sd, st = matches['start_date'], matches['start_time']
    ed, et = matches['end_date'], matches['end_time']
    return ContinuousDatetimeInterval.from_match(sd, st, ed, et)


def as_weekday_list(text, start_index, matches):
    day_matches = [m for m in matches if isinstance(m, weekday)]
    return Weekdays(day_matches)


def as_weekday_interval(text, start_index, matches):
    day_matches = [m for m in matches if isinstance(m, weekday)]
    interval = slice(
        day_matches[0].weekday,
        day_matches[-1].weekday + 1)
    days = list(weekdays[interval])
    return Weekdays(days)


def as_weekly_recurrence(text, start_index, matches):
    wkdays = [m for m in matches if isinstance(m, Weekdays)]
    days = []
    for wkday in wkdays:
        days.extend(wkday.days)
    if matches.get('date_interval'):
        date_interval = matches['date_interval']
    else:
        date_interval = DateInterval.make_undefined()
    if matches.get('time_interval'):
        time_interval = matches['time_interval']
    else:
        time_interval = TimeInterval.make_all_day()
    return WeeklyRecurrence(
        date_interval,
        time_interval,
        days)


def weekdays_as_weekly_recurrence(text, start_index, matches):
    if matches.get('time_interval'):
        time_interval = matches['time_interval'][0]
    else:
        time_interval = TimeInterval.make_all_day()
    return WeeklyRecurrence(
        date_interval=DateInterval.make_undefined(),
        time_interval=time_interval,
        weekdays=matches['weekdays'])


def extract_time_patterns(text, start_index, matches):
    return [m for m in matches if isinstance(m, TimeInterval)]


def develop_datetime_patterns(text, start_index, matches):
    out = []
    date = matches['date']
    times = [m for m in matches if isinstance(m, TimeInterval)]
    for start_time, end_time in times:
        out.append(Datetime(date, start_time, end_time))
    return out


def complete_partial_date(text, start_index, matches):
    if matches.get('partial_date'):
        date = matches['partial_date']
        date.day = matches['day'][0]
        return date
    else:
        return Date(year=None, month=None, day=matches['day'][0])


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
NUMERIC_MONTH = Regex(ur'1[0-2]|0[1-9]|[1-9](?!\d)').\
    setParseAction(as_int).\
    setResultsName('month')

# The numeric version of the year number, either 2 digits or 4 digits
# (ex: dd/mm/2012 or dd/mm/12)
NUMERIC_YEAR = Regex(ur'%s|\d{2}(?!\d{1,2})' % (YEAR.pattern)).\
    setParseAction(as_4digit_year).\
    setResultsName('year')
