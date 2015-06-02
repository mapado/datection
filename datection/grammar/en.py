# -*- coding: utf-8 -*-

"""
Definition of English specific grammar, related to temoral expressions.

"""

from pyparsing import Optional
from pyparsing import Regex
from pyparsing import OneOrMore
from pyparsing import oneOf
from dateutil.rrule import weekdays

from datection.timepoint import Time
from datection.grammar import DAY_NUMBER
from datection.grammar import YEAR
from datection.grammar import HOUR
from datection.grammar import MINUTE
from datection.grammar import NUMERIC_MONTH
from datection.grammar import NUMERIC_YEAR
from datection.grammar import optional_ci
from datection.grammar import optional_oneof_ci
from datection.grammar import oneof_ci
from datection.grammar import as_time_interval
from datection.grammar import as_date
from datection.grammar import develop_datetime_patterns
from datection.grammar import extract_time_patterns
from datection.data.en import WEEKDAYS
from datection.data.en import SHORT_WEEKDAYS
from datection.data.en import MONTHS
from datection.data.en import SHORT_MONTHS


def set_month_number(text, start_index, match):
    """Return the month number from the month name."""
    return MONTHS.get(match[0].lower()) or SHORT_MONTHS.get(match[0].lower())


def set_weekday(text, start_index, match):
    """Return the month number from the month name."""
    idx = WEEKDAYS.get(match[0].lower())
    if idx is None:
        idx = SHORT_WEEKDAYS.get(match[0].lower())
    return weekdays[idx]


def as_time(text, start_index, matches):
    """Return a Time instance from a TIME pattern match."""
    hour = matches['hour']
    minute = matches.get('minute') if matches.get('minute') else 0
    if matches['period'].lower() == 'pm':
        hour += 12
    return Time(hour, minute)

# A weekday name can be in its full form or abbreviated form
WEEKDAY = (
    (
        # weekday with optional s at the end
        oneof_ci(WEEKDAYS.keys()) + Optional(Regex(r'(?<!\s)s?'))
    ) |
    # short weekday not followed by another alphanum char
    oneof_ci(SHORT_WEEKDAYS.keys()) + Regex(r'\.?(?!\w)').leaveWhitespace()
).setParseAction(set_weekday)

# A month name can be in its full form or an abbreviated form.
# When matched, a month name will be transformed to the corresponding
# month index.
MONTH = oneof_ci(
    MONTHS.keys()
    + SHORT_MONTHS.keys(),
).setParseAction(set_month_number)('month')

DAY_NUMBER = DAY_NUMBER + optional_oneof_ci([u'st', u'nd', u'rd', u'th'])

# (at) 10(:30) am/pm
TIME = (
    optional_ci(u'at') +
    HOUR +
    Optional(u':') +
    Optional(MINUTE) +
    oneof_ci([u'am', 'pm'])('period')
).setParseAction(as_time)

# A time interval is composed of a start time, an optional separator and
# an optional end time.
# 15h30 is a time interval bewteen 15h30 and 15h30
# 15h30 - 17h speaks for itself
TIME_INTERVAL = (
    optional_oneof_ci([u'from', u'bewteen']) +
    TIME('start_time') +
    optional_oneof_ci([u'-', u'to', u'and']) +
    Optional(TIME('end_time'))
).setParseAction(as_time_interval)

# Meta pattern catching a list of time patterns (time or time interval)
TIME_PATTERN = (
    OneOrMore(
        TIME_INTERVAL +
        Optional(OneOrMore(oneOf([u',', u'and', u'&', u'or', u';', u'/'])))
    )('patterns')
).setParseAction(extract_time_patterns)

# 5(th) (of) October(,) 2004
BRITISH_DATE = (
    DAY_NUMBER +
    optional_ci(u'of') +
    MONTH +
    Optional(u'.') +  # for abbreviated months
    Optional(u',') +
    YEAR
)

# October (the) 5(th), 2004
AMERICAN_DATE = (
    MONTH +
    Optional(u'.') +
    optional_ci(u'the') +
    DAY_NUMBER +
    Optional(u',') +
    YEAR
)

# (0)5/(0)2/(20)04 or (0)5-(0)2-(20)04
date_sep = optional_oneof_ci(['/', '-'])
BRITISH_NUMERIC_DATE = (
    DAY_NUMBER +
    date_sep +
    NUMERIC_MONTH +
    date_sep +
    NUMERIC_YEAR
)

# (20)14/(0)5/(0)1 or (20)14-(0)5-(0)1
# Note that american numeric date are not allowed to have
# 2 digit years, as it would create a confusion in certain cases
# Example: 04/05/08 --> Date(2004, 5, 8) or Date(2008, 5, 4)?
AMERICAN_NUMERIC_DATE = (
    YEAR +
    date_sep +
    NUMERIC_MONTH +
    date_sep +
    DAY_NUMBER
)

# Generalize date patterns
NUMERIC_DATE = (BRITISH_NUMERIC_DATE | AMERICAN_NUMERIC_DATE)
DATE = (BRITISH_DATE | AMERICAN_DATE)
DATE_PATTERN = (
    optional_ci(u"on") +
    Optional(WEEKDAY) +
    (DATE | NUMERIC_DATE)
).setParseAction(as_date)


# A datetime is a date, a separator and a time interval (either a single)
# time, or a start time and an end time
DATETIME_PATTERN = (
    DATE_PATTERN('date') +
    optional_oneof_ci([u',', u'-', u':']) +
    Optional('.') +
    TIME_PATTERN('time_pattern')
).setParseAction(develop_datetime_patterns)

EXCLUSION = oneof_ci([u'except', u'closed'])

TIMEPOINTS = [
    ('date', DATE_PATTERN),
    ('datetime', DATETIME_PATTERN),
    ('exclusion', EXCLUSION),
]

PROBES = [MONTH, NUMERIC_DATE, TIME_INTERVAL, YEAR, WEEKDAY]

# List of expressions associated with their replacement
# This replacement allows to reduce the complexity of the patterns
EXPRESSIONS = {
}
