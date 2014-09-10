# -*- coding: utf-8 -*-

"""
Definition of French specific grammar, related to temoral expressions.

"""

from pyparsing import Optional
from pyparsing import oneOf
from pyparsing import OneOrMore

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


def set_weekday_number(text, start_index, match):
    """Return the month number from the month name."""
    return WEEKDAYS.get(match[0]) or SHORT_WEEKDAYS.get(match[0])


# A weekday name can be in its full form or abbreviated form
WEEKDAY = oneof_ci(
    WEEKDAYS.keys()
    + SHORT_WEEKDAYS.keys(),
).setParseAction(set_weekday_number).setResultsName('weekday')

# A month name can be in its full form or an abbreviated form.
# When matched, a month name will be transformed to the corresponding
# month index.
MONTH = oneof_ci(
    MONTHS.keys()
    + SHORT_MONTHS.keys(),
).setParseAction(set_month_number).setResultsName('month')

DAY_NUMBER = DAY_NUMBER + optional_ci(u'er').suppress()

# A date is composed of a day number, an optional 'er' (for '1er') that
# we do not care about, a month and a year. Abbreviated months can also
# have a dot at their end, that will be ignored.
DATE = (
    optional_ci(u"le").suppress()
    + DAY_NUMBER
    + MONTH
    + Optional(u'.').suppress()  # for abbreviated months
    + YEAR
).setParseAction(as_date)


# A numeric date is a day, month and a year separated by a one-char
# token. Example: 05/10/2012
date_sep = oneOf([u'/', u'-', u'.']).suppress()
NUMERIC_DATE = (
    DAY_NUMBER +
    date_sep +
    NUMERIC_MONTH +
    date_sep +
    NUMERIC_YEAR +
    Optional(u',')
).setParseAction(as_date)

# A backwards numeric date is a yaer, month and a day separated by a
# one-char token. Example: 2013/10/04
BACKWARDS_NUMERIC_DATE = (
    NUMERIC_YEAR +
    date_sep +
    NUMERIC_MONTH +
    date_sep +
    DAY_NUMBER
).setParseAction(as_date)


# A time is an hour, a separator and a time
TIME = (
    HOUR +
    oneof_ci([u'h', u':']).suppress() +
    Optional(MINUTE)
).setParseAction(as_time)

# A time interval is composed of a start time, an optional separator and
# an optional end time.
# 15h30 is a time interval bewteen 15h30 and 15h30
# 15h30 - 17h speaks for itself
TIME_INTERVAL = (
    optional_oneof_ci([u'de', u'entre', u'à']) +
    TIME.setResultsName('start_time') +
    optional_oneof_ci([u'-', u'à', u'et']) +
    Optional(TIME.setResultsName('end_time'))
).setParseAction(as_time_interval)

# A partial date must at least have a day number, and then can
# have a month and a year.
PARTIAL_DATE = (
    DAY_NUMBER +
    Optional(MONTH) +
    Optional(YEAR) +
    optional_oneof_ci([u',', u'et'])
).setParseAction(as_date)

# A date list is a list of partial dates
DATE_LIST = (
    optional_oneof_ci([u"le", u"les"]) +
    OneOrMore(PARTIAL_DATE).setResultsName('dates')
).setParseAction(as_datelist)

# A date interval is composed of a start (possibly partial) date and an
# end date
DATE_INTERVAL = (
    optional_ci(u"du") +
    PARTIAL_DATE.setResultsName('start_date') +
    oneof_ci([u'au', '-']) +
    DATE.setResultsName('end_date')
).setParseAction(as_date_interval)

# A date interval is composed of a numeric start date and a numeric end
# date
NUMERIC_DATE_INTERVAL = (
    optional_ci(u"du") +
    NUMERIC_DATE.setResultsName('start_date') +
    oneof_ci([u'au', '-']) +
    NUMERIC_DATE.setResultsName('end_date')
).setParseAction(as_date_interval)

# A datetime is a date, a separator and a time interval (either a single)
# time, or a start time and an end time
DATETIME = (
    DATE.setResultsName('date') +
    optional_ci(u',') +
    TIME_INTERVAL.setResultsName('time_interval')
).setParseAction(as_datetime)


# A datetime list is a list of dates, along with a time interval
DATETIME_LIST = (
    optional_oneof_ci([u"les", u"le"]) +
    OneOrMore(PARTIAL_DATE).setResultsName('dates') +
    Optional(u',') +
    optional_oneof_ci([u'à', u'-']) +
    TIME_INTERVAL.setResultsName('time_interval')
).setParseAction(as_datetime_list)

# same than DATETIME_LIST with numerical dates
NUMERICAL_DATETIME_LIST = (
    optional_oneof_ci([u"les", u"le"]) +
    OneOrMore(NUMERIC_DATE).setResultsName('dates') +
    Optional(u',') +
    optional_oneof_ci([u'à', u'-']) +
    TIME_INTERVAL.setResultsName('time_interval')
).setParseAction(as_datetime_list)


# a datetime interval is an interval of dates, and a time interval
DATETIME_INTERVAL = (
    DATE_INTERVAL.setResultsName('date_interval') +
    Optional(u',') +
    TIME_INTERVAL.setResultsName('time_interval')
).setParseAction(as_datetime_interval)

# a datetime interval is an interval of numeric dates, and a time interval
NUMERIC_DATETIME_INTERVAL = (
    NUMERIC_DATE_INTERVAL.setResultsName('date_interval') +
    Optional(u',') +
    TIME_INTERVAL.setResultsName('time_interval')
).setParseAction(as_datetime_interval)

# Example: du 5 mars 2015 à 13h au 7 mars 2015 à 7h
CONTINUOUS_DATETIME_INTERVAL = (
    optional_ci(u'du') +
    DATE.setResultsName("start_date") +
    optional_oneof_ci([u"à", u"-"]) +
    TIME.setResultsName("start_time") +
    optional_oneof_ci([u"au", '-']) +
    DATE.setResultsName("end_date") +
    optional_oneof_ci([u"à", u"-"]) +
    TIME.setResultsName("end_time")
).setParseAction(as_continuous_datetime_interval)

# Example: du 05/11/2015 à 13h au 07/11/2015 à 7h
NUMERIC_CONTINUOUS_DATETIME_INTERVAL = (
    optional_ci(u'du') +
    NUMERIC_DATE.setResultsName("start_date") +
    optional_oneof_ci([u"à", u"-"]) +
    TIME.setResultsName("start_time") +
    optional_oneof_ci([u"au", '-']) +
    NUMERIC_DATE.setResultsName("end_date") +
    optional_oneof_ci([u"à", u"-"]) +
    TIME.setResultsName("end_time")
).setParseAction(as_continuous_datetime_interval)
