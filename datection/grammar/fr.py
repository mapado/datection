# -*- coding: utf-8 -*-

"""
Definition of French specific grammar, related to temoral expressions.

"""

from pyparsing import Optional
from pyparsing import oneOf
from pyparsing import OneOrMore
from pyparsing import FollowedBy
from pyparsing import Group
from dateutil.rrule import weekdays

from datection.grammar import DAY_NUMBER
from datection.grammar import YEAR
from datection.grammar import HOUR
from datection.grammar import MINUTE
from datection.grammar import NUMERIC_MONTH
from datection.grammar import NUMERIC_YEAR
from datection.grammar import as_date
from datection.grammar import as_time
from datection.grammar import as_datetime
from datection.grammar import as_datelist
from datection.grammar import as_date_interval
from datection.grammar import as_time_interval
from datection.grammar import as_datetime_list
from datection.grammar import as_datetime_interval
from datection.grammar import as_continuous_datetime_interval
from datection.grammar import as_weekday_list
from datection.grammar import as_weekday_interval
from datection.grammar import as_weekly_recurrence
from datection.grammar import complete_partial_date
from datection.grammar import extract_time_patterns
from datection.grammar import develop_datetime_patterns
from datection.grammar import optional_ci
from datection.grammar import optional_oneof_ci
from datection.grammar import oneof_ci
from datection.data.fr import WEEKDAYS
from datection.data.fr import SHORT_WEEKDAYS
from datection.data.fr import MONTHS
from datection.data.fr import SHORT_MONTHS


def set_month_number(text, start_index, match):
    """Return the month number from the month name."""
    return MONTHS.get(match[0]) or SHORT_MONTHS.get(match[0])


def set_weekday(text, start_index, match):
    """Return the month number from the month name."""
    idx = WEEKDAYS.get(match[0].lower())
    if idx is None:
        idx = SHORT_WEEKDAYS.get(match[0].lower())
    return weekdays[idx]


# A weekday name can be in its full form or abbreviated form
WEEKDAY = (
    (
        oneof_ci(WEEKDAYS.keys()) + Optional('s')
    ) | oneof_ci(SHORT_WEEKDAYS.keys()) + ~FollowedBy('s')
).setParseAction(set_weekday)

# A month name can be in its full form or an abbreviated form.
# When matched, a month name will be transformed to the corresponding
# month index.
MONTH = oneof_ci(
    MONTHS.keys()
    + SHORT_MONTHS.keys(),
).setParseAction(set_month_number)('month')

DAY_NUMBER = DAY_NUMBER + optional_ci(u'er')

# A date is composed of a day number, an optional 'er' (for '1er') that
# we do not care about, a month and an optional year.
# Abbreviated months can also have a dot at their end, that will be ignored.
DATE = (
    optional_ci(u"le")
    + DAY_NUMBER
    + MONTH
    + Optional(u'.')  # for abbreviated months
    + Optional(YEAR)
).setParseAction(as_date)


# A numeric date is a day, month and a year separated by a one-char
# token. Example: 05/10/2012
date_sep = oneOf([u'/', u'-', u'.'])
NUMERIC_DATE = (
    DAY_NUMBER +
    date_sep +
    NUMERIC_MONTH +
    Optional(
        date_sep +
        NUMERIC_YEAR
    ) +
    Optional(u',')
).setParseAction(as_date)


DATE_PATTERN = (DATE | NUMERIC_DATE)

# A time is an hour, a separator and a time
TIME = (
    Optional(u'à') +
    HOUR +
    oneof_ci([u'h', u':']) +
    Optional(MINUTE)
).setParseAction(as_time)

# A time interval is composed of a start time, an optional separator and
# an optional end time.
# 15h30 is a time interval bewteen 15h30 and 15h30
# 15h30 - 17h speaks for itself
TIME_INTERVAL = (
    optional_oneof_ci([u'de', u'entre', u'à']) +
    TIME('start_time') +
    optional_oneof_ci([u'-', u'à', u'et']) +
    Optional(TIME('end_time'))
).setParseAction(as_time_interval)


# Meta pattern catching a list of time patterns (time or time interval)
TIME_PATTERN = (
    OneOrMore(
        TIME_INTERVAL +
        Optional(OneOrMore(oneOf([u',', u'et'])))
    )('patterns')
).setParseAction(extract_time_patterns)

# A partial litteral date is both optional month and year.
PARTIAL_LITTERAL_DATE = (
    MONTH +
    Optional(YEAR)
).setParseAction(as_date)

# A partial litteral date is both optional numeric month and year.
PARTIAL_NUMERIC_DATE = (
    NUMERIC_MONTH +
    Optional(
        date_sep +
        NUMERIC_YEAR
    )
).setParseAction(as_date)

# A partial date is a mandatory day number, and optional litteral/numeric
# month and year, and optional separator
PARTIAL_DATE = (
    DAY_NUMBER('day') +
    Optional(date_sep) +
    Optional(
        PARTIAL_LITTERAL_DATE('partial_date') |
        PARTIAL_NUMERIC_DATE('partial_date')
    )
    + Optional(OneOrMore(oneOf([u',', u'et'])))
).setParseAction(complete_partial_date)

# A date list is a list of partial dates
DATE_LIST = (
    optional_oneof_ci([u"le", u"les"]) +
    Group(
        PARTIAL_DATE +
        OneOrMore(PARTIAL_DATE)
    )('dates')
).setParseAction(as_datelist)

# A date interval is composed of a start (possibly partial) date and an
# end date
DATE_INTERVAL = (
    optional_ci(u"du") +
    PARTIAL_DATE('start_date') +
    oneof_ci([u'au', '-']) +
    (DATE | NUMERIC_DATE)('end_date')
).setParseAction(as_date_interval)

# A datetime is a date, a separator and a time interval (either a single)
# time, or a start time and an end time
DATETIME = (
    DATE('date') +
    optional_ci(u',') +
    TIME_INTERVAL('time_interval')
).setParseAction(as_datetime)

DATETIME_PATTERN = (
    DATE('date') +
    TIME_PATTERN('time_pattern')
).setParseAction(develop_datetime_patterns)

# A datetime list is a list of dates, along with a time interval
DATETIME_LIST = (
    optional_oneof_ci([u"les", u"le"]) +
    OneOrMore(PARTIAL_DATE)('dates') +
    Optional(u',') +
    optional_oneof_ci([u'à', u'-']) +
    TIME_INTERVAL('time_interval')
).setParseAction(as_datetime_list)


# a datetime interval is an interval of dates, and a time interval
DATETIME_INTERVAL = (
    DATE_INTERVAL('date_interval') +
    Optional(u',') +
    TIME_INTERVAL('time_interval')
).setParseAction(as_datetime_interval)


# Example: du 5 mars 2015 à 13h au 7 mars 2015 à 7h
CONTINUOUS_DATETIME_INTERVAL = (
    optional_ci(u'du') +
    (DATE | NUMERIC_DATE)("start_date") +
    optional_oneof_ci([u"à", u"-"]) +
    TIME("start_time") +
    optional_oneof_ci([u"au", '-']) +
    (DATE | NUMERIC_DATE)("end_date") +
    optional_oneof_ci([u"à", u"-"]) +
    TIME("end_time")
).setParseAction(as_continuous_datetime_interval)


# A list of several weekdays
WEEKDAY_LIST = (
    optional_oneof_ci([u"le", u"les"]) +
    OneOrMore(WEEKDAY + Optional(OneOrMore(oneOf([u',', u'et']))))
).setParseAction(as_weekday_list)('weekdays')

# An interval of weekdays
WEEKDAY_INTERVAL = (
    optional_ci(u"du") +
    WEEKDAY
    + u"au"
    + WEEKDAY
).setParseAction(as_weekday_interval)('weekdays')

# Any weekday related pattern
WEEKDAY_PATTERN = (
    WEEKDAY_INTERVAL | WEEKDAY_LIST
)


WEEKLY_RECURRENCE_1 = (
    WEEKDAY_PATTERN('weekdays') +
    Optional(',') +
    DATE_INTERVAL('date_interval') +
    Optional(',') +
    TIME_INTERVAL('time_interval')
).setParseAction(as_weekly_recurrence)

WEEKLY_RECURRENCE_2 = (
    WEEKDAY_PATTERN('weekdays') +
    Optional(',') +
    TIME_INTERVAL('time_interval') +
    Optional(',') +
    DATE_INTERVAL('date_interval')
).setParseAction(as_weekly_recurrence)

WEEKLY_RECURRENCE_3 = (
    DATETIME_INTERVAL('datetime_interval') +
    Optional(',') +
    WEEKDAY_PATTERN
).setParseAction(as_weekly_recurrence)

WEEKLY_RECURRENCE = (
    WEEKLY_RECURRENCE_1 |
    WEEKLY_RECURRENCE_2 |
    WEEKLY_RECURRENCE_3
)
