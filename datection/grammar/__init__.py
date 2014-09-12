# -*- coding: utf-8 -*-

"""
Definition of language agnostic temporal expressions related regexes .

"""
import re

from operator import attrgetter
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


class Match(object):

    """Wraps the text matched by a pyparsing pattern, storing the
    matched value, along with the start and end indices of the Match
    in the text.

    """

    def __init__(self, value, start_index, end_index):
        self.value = value
        self.start_index = start_index
        self.end_index = end_index

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.value)

    def __nonzero__(self):
        return self.value is not None


def span(matches):
    matches = sorted(matches, key=attrgetter('start_index'))
    return (matches[0].start_index, matches[-1].end_index)


def make_match(match, matched_text, start_index):
    return Match(match, start_index, start_index + len(matched_text))


def optional_ci(s):
    return Optional(Regex(s, flags=re.I))


def oneof_ci(choices):
    return oneOf(choices, caseless=True)


def optional_oneof_ci(choices):
    return Optional(oneof_ci(choices))


def as_int(text, start_index, match):
    """Return the integer value of the matched text."""
    return Match(int(match[0]), start_index, start_index + len(match[0]))


def as_4digit_year(text, start_index, match):
    """Return a 4 digit, integer year from a YEAR regex match."""
    if len(match[0]) == 4:
        year = int(match[0])
    elif len(match[0]) == 2:
        year = int(normalize_2digit_year(match[0]))
    return make_match(year, match[0], start_index)


def as_date(text, start_index, matches):
    """Return a Date object from a DATE regex match."""
    year = matches.get('year', Match(None, None, None))
    month = matches.get('month', Match(None, None, None))
    day = matches.get('day', Match(None, None, None))
    # do not take the non matches into account in the span calculation
    span_matches = filter(bool, [year, month, day])
    return Date(year.value, month.value, day.value,
                span=span(span_matches))


def as_time(text, start_index, matches):
    """Return a Time object from a TIME regex match."""
    hour = matches['hour']
    minute = matches.get('minute', Match(0, None, None))
    if matches.get('minute'):
        span_matches = [matches['hour'], matches['minute']]

    else:
        span_matches = [matches['hour']]
    return Time(hour.value, minute.value, span=span(span_matches))


def as_time_interval(text, start_index, matches):
    """Return a TimeInterval object from the TIME_INTERVAL regex match."""
    if not matches.get('end_time'):
        matches['end_time'] = matches['start_time']
    return TimeInterval(
        matches['start_time'],
        matches['end_time'],
        span=span([matches['start_time'], matches['end_time']]))


def as_datetime(text, start_index, matches):
    """Return a Datetime object from the DATETIME regex match."""
    d = matches['date']
    ti = matches['time_interval']
    return Datetime(d, ti.start_time, ti.end_time, span=span([d, ti]))


def as_datelist(text, start_index, matches):
    """Return a DateList object from the DATE_LIST regex match."""
    dates = list(matches['dates'])
    return DateList.from_match(dates, span=span(dates))


def as_date_interval(text, start_index, matches):
    """Return a DateInterval object from the DATE_INTERVAL regex match."""
    sd = matches['start_date']
    ed = matches['end_date']
    return DateInterval.from_match(sd, ed, span=span([sd, ed]))


def as_datetime_list(text, start_index, match):
    match_dates = list(match['dates'])
    dates = DateList.from_match(match_dates, span=span(match_dates))
    span_matches = [dates, match['time_interval']]
    return DatetimeList.from_match(
        dates, match['time_interval'],
        span=span(span_matches))


def as_datetime_interval(text, start_index, match):
    di = match['date_interval']
    ti = match['time_interval']
    return DatetimeInterval(di, ti, span=span([di, ti]))


def as_continuous_datetime_interval(text, start_index, match):
    sd, st = match['start_date'], match['start_time']
    ed, et = match['end_date'], match['end_time']
    return ContinuousDatetimeInterval.from_match(
        sd, st, ed, et, span=span([sd, st, ed, et]))


def extract_time_patterns(text, start_index, match):
    return match


def develop_datetime_patterns(text, start_index, match):
    out = []
    date = match['date']
    times = list(match['time_pattern'])
    for start_time, end_time in times:
        out.append(Datetime(date,  start_time, end_time))
    return out


def complete_partial_date(text, start_index, matches):
    if matches.get('partial_date'):
        date = matches['partial_date']
        date.day = matches['day'][0].value
        date.span = (matches['day'][0].start_index, date.end_index)
        return date
    else:
        return Date(
            year=None,
            month=None,
            day=matches['day'][0].value,
            span=span([matches['day'][0]]))

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
