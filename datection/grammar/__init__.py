# -*- coding: utf-8 -*-

"""
Definition of language agnostic temporal expressions related regexes .

"""

import re

from dateutil.rrule import weekdays
from dateutil.rrule import weekday
from pyparsing import Regex
from pyparsing import Optional

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
    """Return a Regex object matching the argument string case-insensitively."""
    return Optional(Regex(s, flags=re.I))


def oneof_ci(choices):
    """Return a Regex object matching any of the argument choice,
    case-insensitively.

    """
    choices = sorted(choices, key=len, reverse=True)
    return Regex(r'|'.join(choices), flags=re.I)


def optional_oneof_ci(choices):
    """Return a Regex Regex object matching none or any of the argument choice,
    case-insensitively.

    """
    return Optional(oneof_ci(choices))


def as_int(text, start_index, match):
    """Return the integer value of the matched text."""
    return int(match[0])


def as_4digit_year(text, start_index, match):
    """Return a 4 digit, integer year from a match of the YEAR pattern."""
    if len(match[0]) == 4:
        year = int(match[0])
    elif len(match[0]) == 2:
        year = int(normalize_2digit_year(match[0]))
    return year


def as_date(text, start_index, matches):
    """Return a Date object from a match of the DATE pattern."""
    year = matches.get('year')
    month = matches.get('month')
    day = matches.get('day')
    return Date(year, month, day)


def as_time(text, start_index, matches):
    """Return a Time object from a match of the TIME pattern."""
    hour = matches['hour']
    minute = matches.get('minute', 0)
    return Time(hour, minute)


def as_time_interval(text, start_index, matches):
    """Return a TimeInterval object from a match of the TIME_INTERVAL pattern.

    """
    if not matches.get('end_time'):
        matches['end_time'] = matches['start_time']
    return TimeInterval(matches['start_time'], matches['end_time'])


def as_datetime(text, start_index, matches):
    """Return a Datetime object from a match of the DATETIME pattern."""
    d = matches['date']
    ti = matches['time_interval']
    return Datetime(d, ti.start_time, ti.end_time)


def regroup_dates_by_continuty(date_list):
    """Return a DateInterval instance per date continuity group in the
    DateList dates, and a DateList object containing all the non
    continuous dates.

    """
    out = []
    groups = date_list.contiguous_groups()
    interval_groups = [group for group in groups if len(group) > 1]
    single_dates = [group[0] for group in groups if len(group) == 1]
    for interval_group in interval_groups:
        out.append(DateInterval(
            start_date=interval_group[0],
            end_date=interval_group[-1]))

    if single_dates:
        out.append(DateList(dates=single_dates))

    return out


def as_datelist(text, start_index, matches):
    """Return a DateList object from a match of the DATE_LIST pattern."""
    date_list = DateList.from_match(list(matches['dates']))
    if date_list.contiguous_dates():
        return DateInterval(
            start_date=date_list.dates[0],
            end_date=date_list.dates[-1])
    else:
        return regroup_dates_by_continuty(date_list)


def as_date_interval(text, start_index, matches):
    """Return a DateInterval object from a match of the DATE_INTERVAL pattern"""
    sd = matches['start_date']
    ed = matches['end_date']
    return DateInterval.from_match(sd, ed)


def as_datetime_list(text, start_index, matches):
    """Return a DatetimeList object from a match of the DATETIME_LIST pattern"""
    timepoints = as_datelist(text, start_index, matches)
    if isinstance(timepoints, DateInterval):
        return DatetimeInterval(timepoints, matches['time_interval'])
    else:
        out = []
        start_time = matches['time_interval'].start_time
        end_time = matches['time_interval'].end_time
        date_intervals = [
            timepoint for timepoint in timepoints
            if isinstance(timepoint, DateInterval)]
        for date_interval in date_intervals:
            out.append(DatetimeInterval(
                date_interval, matches['time_interval']))
        date_lists = [
            timepoint for timepoint in timepoints
            if isinstance(timepoint, DateList)]
        if date_lists:
            datetimes = [
                Datetime.combine(date, start_time, end_time)
                for date_list in date_lists
                for date in date_list]
            out.append(DatetimeList(datetimes))
        return out


def as_continuous_datetime_interval(text, start_index, matches):
    """Return a ContinuousDatetimeInterval object from a match of the
    CONTTUNUOUS_DATETIME_INTERVAL pattern.

    """
    sd, st = matches['start_date'], matches['start_time']
    ed, et = matches['end_date'], matches['end_time']
    return ContinuousDatetimeInterval.from_match(sd, st, ed, et)


def as_datetime_list_multitime(text, start_index, matches):
    """
    Return a DatetimeList containing all the matching Datetimes
    """
    items = matches['datetime']
    datetimes = [d for d in items if isinstance(d, Datetime)]
    return DatetimeList(datetimes)


def as_weekday_list(text, start_index, matches):
    """Return a Weekdays object from a match of the WEEKDAY_LIST pattern."""
    day_matches = [m for m in matches if isinstance(m, weekday)]
    return Weekdays(day_matches)


def as_weekday_interval(text, start_index, matches):
    """Return a Weekdays object from a match of the WEEKDAY_INTERVAL pattern."""
    day_matches = [m for m in matches if isinstance(m, weekday)]
    interval = slice(
        day_matches[0].weekday,
        day_matches[-1].weekday + 1)
    days = list(weekdays[interval])
    return Weekdays(days)


def as_weekly_recurrence(text, start_index, matches):
    """Return a WeeklyRecurrence object from a match of the WEEKLY_RECURRENCE
    pattern.

    """
    wkdays = [m for m in matches if isinstance(m, Weekdays)]
    time_intervals = [m for m in matches if isinstance(m, TimeInterval)]
    days = []
    for wkday in wkdays:
        days.extend(wkday.days)

    date_interval = matches.get('date_interval', DateInterval.make_undefined())
    if not time_intervals:
        time_intervals = [TimeInterval.make_all_day()]
    return [WeeklyRecurrence(date_interval, ti, days) for ti in time_intervals]


def weekdays_as_weekly_recurrence(text, start_index, matches):
    """Convert a weekday match (single, interval or list) to a WeeklyRecurrence
    object.

    The WeeklyRecurrence date interval will be unlimited, and its time interval
    will cover all day.

    """
    if matches.get('time_interval'):
        time_interval = matches['time_interval'][0]
    else:
        time_interval = TimeInterval.make_all_day()
    return WeeklyRecurrence(
        date_interval=DateInterval.make_undefined(),
        time_interval=time_interval,
        weekdays=matches['weekdays'])


def extract_time_patterns(text, start_index, matches):
    """Return a list of TimeInterval from the pattern match."""
    return [m for m in matches if isinstance(m, TimeInterval)]


def develop_datetime_patterns(text, start_index, matches):
    """Assign each time interval match to the date interval match, and
    return a list of Datetime objects.

    """
    out = []
    date = matches['date']
    times = [m for m in matches if isinstance(m, TimeInterval)]
    for start_time, end_time in times:
        out.append(Datetime(date, start_time, end_time))
    return out


def complete_partial_date(text, start_index, matches):
    """Return a full date, combined from the matched day and partial date.

    If no partial date was matched, return a Date object with missing
    year and month.

    """
    if matches.get('partial_date'):
        date = matches['partial_date']
        date.day = matches['day'][0]
        return date
    else:
        return Date(year=None, month=None, day=matches['day'][0])


def develop_datetime_interval_patterns(text, start_index, matches):
    """Combine each matched time interval with the matched date interval.

    Each time interval is combined to the date interval, thus returning
    a list of DatetimeInterval objects.

    """
    out = []
    date_interval = matches['date_interval']
    time_intervals = [m for m in matches if isinstance(m, TimeInterval)]
    for time_interval in time_intervals:
        dti = DatetimeInterval(
            date_interval=date_interval,
            time_interval=time_interval)
        out.append(dti)
    return out


def develop_weekly_recurrence_patterns(text, start_index, matches):
    """Return a list of WeeklyRecurrence objects from a match of the
    MULTIPLE_WEEKLY_RECURRENCE pattern.

    Each weekday/time_interval couple is combined with the date interval
    match, to form a WeeklyRecurrence object.

    """
    out = []
    if matches.get('date_interval'):
        date_interval = matches['date_interval']
    else:
        date_interval = DateInterval.make_undefined()
    for group in matches['groups']:
        wk = WeeklyRecurrence(
            date_interval=date_interval,
            weekdays=group['weekdays'],
            time_interval=group['patterns'][0])
        out.append(wk)
    return out


# The day number. Ex: lundi *18* juin 2013.
DAY_NUMBER = Regex(
    r'(?<![\dh:])'  # not preceeded by a digit, a 'h' or a ':'
    # OK: (0)1..(0)9...10...29, 30, 31
    r'([1-2][0-9]|(0)?[1-9]|3[0-1]|1(?=er))'
    # no number, prices or time tags after
    # to avoid matching (20)13 in a year, (20)€ or (15)h
    # Note that is its possible for a single digit  to be matched
    # that's ok because the DAY_NUMBER regex will be used in combination
    # with others like DAYS, MONTHS, etc
    r'( )?(?![\d|€)|h])').\
    setParseAction(as_int).\
    setResultsName('day')

# The year number. A valid year must either start with 1 or 2.
YEAR = Regex(r'[12]\d{3}').\
    setParseAction(as_int).\
    setResultsName('year')

# hour: between 00 and 24. Can be 2 digit or 1-digit long.
# The hour it must not be preceded by another digit
# The minute must not be followed by another digit
HOUR = Regex(r'(?<!\d)(0[0-9]|1[0-9]|2[0-4]|[0-9])(?!\d)').\
    setParseAction(as_int).\
    setResultsName('hour')

# Minute: bewteen 00 and 59
MINUTE = Regex(r'[0-5][0-9]').\
    setParseAction(as_int).\
    setResultsName('minute')

# Minute: bewteen 00 and 59
SECOND = Regex(r'[0-5][0-9]').\
    setParseAction(as_int).\
    setResultsName('second')

# The numeric version of the month: 2 digits bewteen 01 and 12
NUMERIC_MONTH = Regex(r'1[0-2]|0[1-9]|[1-9](?!\d)').\
    setParseAction(as_int).\
    setResultsName('month')

# The numeric version of the year number, either 2 digits or 4 digits
# (ex: dd/mm/2012 or dd/mm/12)
NUMERIC_YEAR = Regex(r'%s|\d{2}(?!\d{1,2})' % (YEAR.pattern)).\
    setParseAction(as_4digit_year).\
    setResultsName('year')
