# -*- coding: utf-8 -*-

import re

from datenames import *

# words located before a date, giving hints about how it relates
# to other dates
DAYS_PREFIX = r'le'
FR_WEEKDAY = r'(%s)' % ('|'.join(WEEKDAY['fr'].keys()))


# first the whole month number, then the abbreviated
# otherwhise, 'oct' might be matched in 'october', thus breaking
# the whole date structure
FR_SHORT_MONTH = [k + r'\.?' for k in SHORT_MONTH['fr'].keys()]
FR_MONTH = r'(?<!\w)(%s)(?!\w)' % ('|'.join(MONTH['fr'].keys() + FR_SHORT_MONTH))

# The day number. Ex: lundi *18* juin 2013.
DAY_NUMBER = (
    r'(?<!\d)'  # not preceeded by a digit
    r'([0-2][0-9]|(0)?[1-9]|3[0-1]|1(?=er))'  # OK: (0)1..(0)9...10...29, 30, 31
    r'( )?(?![\d|€)|h])')  # no number, prices or time tags after
    # to avoid matching (20)13 in a year, (20)€ or (15)h
    # Note that is its possible for a single digit  to be matched
    # that's ok because the DAY_NUMBER regex will be used in combination
    # with others like DAYS, MONTHS, etc

# The year number. A  valid year must begin with 2, to avoid detection
# of past dates
YEAR = r'2\d{3}'

# hour: between 00 and 24. Can be 2 digit or 1-digit long.
# The hour it must not be preceded by another digit
# The minute must not be followed by another digit
HOUR = r'(?<!\d)(0[1-9]|1[0-9]|2[0-4]|[0-9])(?!\d)'

# Minute: bewteen 00 and 59
MINUTE = r'[0-5][0-9]'

# A date of the form 'le mercredi 18 juin 2013'
# Note: only the month is a mandatory marker
# Note2: this pattern is not compiled. This way,
# it can be re-used in other patters, to avoid
# redudancy and un-maintainability
_FR_DATE = r"""
    ((?P<day>{day})(er)?)\s* # day number (optional)
    (?P<month_name>{month_name})\s*  # month
    (?P<year>{year})?  # year (optional)
    """.format(day=DAY_NUMBER, month_name=FR_MONTH, year=YEAR)

FR_DATE = re.compile(
    _FR_DATE, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# The numeric version of the month: 2 digits bewteen 01 and 12
NUMERIC_MONTH = r'0[1-9]|1[0-2]'

# The numeric version of the year number, either 2 digits or 4 digits
# (ex: dd/mm/2012 or dd/mm/12)
NUMERIC_YEAR = r'%s|\d{2}' % (YEAR)

NUMERIC_DATE_SEPARATOR = r'[/\.]'
# Dates of format dd/mm(/(yy)yy)
_FR_NUMERIC_DATE = r"""
    (?P<day>{day})
    {sep}  # separator
    (?P<month_name>{month})
    ({sep})? # optional separator (if year not present)
    (?P<year>{year})?  # year (optional)
    """.format(
    day=DAY_NUMBER,
    sep=NUMERIC_DATE_SEPARATOR,
    month=NUMERIC_MONTH,
    year=NUMERIC_YEAR)

FR_NUMERIC_DATE = re.compile(_FR_NUMERIC_DATE, flags=re.VERBOSE)

# separator bewteen hour and minutes
# example: 10h50, 10:50, 10h
TIME_SEPARATOR = r'(h|:)'

# Time, of form hhhmm, or hh:mm
FR_TIME = r'(?P<hour>{hour})(\s)?{sep}(?P<minute>{minute})?'.format(
    hour=HOUR, sep=TIME_SEPARATOR, minute=MINUTE)

# Same that FR_TIME, but with no group. Use it when several
# times are matched (ex: time intervals)
_FR_TIME = r'({hour})(\s)?({sep})({minute})?'.format(
    hour=HOUR, sep=TIME_SEPARATOR, minute=MINUTE)

# Time interval: one time or two times linked by a prefix and a suffix
# Examples:
# * 15h30
# * de 15h30 à 20h
# * mercredi 13 mars, 15h30 - 16h
FR_TIME_INTERVAL_PREFIX = r'(-|à|,|de|entre)'
FR_TIME_INTERVAL_SUFFIX = r'(à|et|-)'
_FR_TIME_INTERVAL = r"""
    ({prefix}\s*)?
    (?P<start_time>{time})
    (\s*{suffix})?
    (\s*(?P<end_time>{time}))?
    """.format(
    prefix=FR_TIME_INTERVAL_PREFIX, time=_FR_TIME,
    suffix=FR_TIME_INTERVAL_SUFFIX)
FR_TIME_INTERVAL = re.compile(
    r'%s' % (_FR_TIME_INTERVAL),
    flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)


# Intervals are spans of date, linked by a prefix and a suffix.
# Examples:
# * du 15 au 18 Mars. (prefix: 'au', suffix: 'du')
# * du samedi 19 au mercredi 23 octobre 2013
INTERVAL_PREFIX = r'du'
INTERVAL_SUFFIX = r'(au|-)'
_FR_DATE_INTERVAL = r"""
    ({prefix}\s)?
    ((?P<start_day>{day})(er)?)\s* # day number
    (?P<start_month_name>{month_name})?\s*  # month (optional)
    (?P<start_year>{year})?\s* # year (optional)
    (?P<suffix>{suffix})\s*  # prefix
    ({weekday_name})?\s*  # day (optional)
    ((?P<end_day>{day})(er)?)\s* # day number # day number (optional)
    (?P<end_month_name>{month_name})?\s*  # month (optional)
    (?P<end_year>{year})?  # year (optional)
    """.format(
    prefix=INTERVAL_PREFIX, weekday_name=FR_WEEKDAY, day=DAY_NUMBER,
    month_name=FR_MONTH, year=YEAR, suffix=INTERVAL_SUFFIX)
FR_DATE_INTERVAL = re.compile(
    _FR_DATE_INTERVAL, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)


_FR_NUMERIC_DATE_INTERVAL = r"""
    ({prefix}\s)?
    (?P<start_day>{day}) # day number
    {sep}
    (?P<start_month_name>{month_name})\s* # month
    (
        {sep}
        (?P<start_year>{year})\s  # year
    )?
    {suffix}\s  # prefix
    (?P<end_day>{day})  # day number # day number
    {sep}
    (?P<end_month_name>{month_name})  # month
    {sep}
    (?P<end_year>{year})  # year
    """.format(
    prefix=INTERVAL_PREFIX, day=DAY_NUMBER, sep=NUMERIC_DATE_SEPARATOR,
    month_name=NUMERIC_MONTH, year=NUMERIC_YEAR, suffix=INTERVAL_SUFFIX)
FR_NUMERIC_DATE_INTERVAL = re.compile(
    _FR_NUMERIC_DATE_INTERVAL, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# Datetime: a date and a time
# Examples:
# le mercredi 18 juin 2013 à 20h30
# le 15 août 2013 de 15h30 à 16h45
FR_DATETIME = re.compile(r"""
    {date}\s*
    [^\d]{{,4}}
    {time}
    """.format(date=_FR_DATE, time=_FR_TIME_INTERVAL),
    flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# an interval of dates with a time information
# Examples
# * du samedi 19 au mercredi 23 octobre 2013, à 15h30
# * du 15 au 18 Mars de 20h30 à 23h
FR_DATETIME_INTERVAL = re.compile(r"""
    {date_interval}
    [^\d]{{,4}}
    {time}
    """.format(date_interval=_FR_DATE_INTERVAL, time=_FR_TIME_INTERVAL),
    flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

FR_NUMERIC_DATETIME_INTERVAL = re.compile(r"""
    {date_interval}
    [^\d]{{,4}}
    {time}
    """.format(date_interval=_FR_NUMERIC_DATE_INTERVAL, time=_FR_TIME_INTERVAL),
    flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# A date list is a list of independant dates, linkes by a prefix and a suffix
# Examples:
# * Mercredi 15, jeudi 16, vendredi 17 et lundi 20 mars
# * Les 25, 26, 27 et 28 octobre
# * les 25, 26, 27 mars 2013
FR_DATE_LIST_PREFIX = r'le(s)?'  # le/les
FR_DATE_LIST_SUFFIX = r'et'
_FR_DATE_IN_LIST = r"""
        (?P<weekday_name>{weekday_name})?\s*  # day (optional)
        (?P<day>{day})\s* # day number
        (?P<month_name>{month_name})?\s*
        (?P<year>{year})?\s*
    """.format(
    prefix=FR_DATE_LIST_PREFIX, weekday_name=FR_WEEKDAY, day=DAY_NUMBER,
    month_name=FR_MONTH, year=YEAR)
FR_DATE_IN_LIST = re.compile(
    _FR_DATE_IN_LIST, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# Example: lundi 25, mardi, 26 et mercredi 27 mars 2013
_FR_DATE_LIST_WEEKDAY = r"""
    (?P<date_list>
        (
            {weekday_name}\s* # weekday (optional)
            {day}\s* # day number
            (,\s)?
        )+
        ({suffix}\s*)?  # separator
        ({weekday_name})?\s*  # day (optional)
        {day}\s* # day number
        {month_name}\s*
        ({year})?\s*
    )
    """.format(
    suffix=FR_DATE_LIST_SUFFIX, weekday_name=FR_WEEKDAY,
    day=DAY_NUMBER, month_name=FR_MONTH, year=YEAR)

FR_DATE_LIST_WEEKDAY = re.compile(
    _FR_DATE_LIST_WEEKDAY, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# Example: 25, 26, 27 mars 2013
# strong hypothesis: no weekday
_FR_DATE_LIST = r"""
    (?P<date_list>
        (
            {day}\s* # day number
            (,\s)?
        )+
        ({suffix}\s*)?  # separator
        {day}\s* # day number
        {month_name}\s*
        ({year})?\s*
    )
    """.format(
    suffix=FR_DATE_LIST_SUFFIX, weekday_name=FR_WEEKDAY,
    day=DAY_NUMBER, month_name=FR_MONTH, year=YEAR)

FR_DATE_LIST = re.compile(
    _FR_DATE_LIST, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)


# A given time for a list of dates
# Examples:
# * le mercredi 6, jeudi 7 et vendredi 8 juin 2013 à 20h30
# * le mercredi 6, jeudi 7 et vendredi 8 juin 2013 de 20h à 20h30
FR_DATETIME_LIST_WEEKDAY = re.compile(r"""
    {datelist}
    [^\d]{{,4}}
    {time}
    """.format(datelist=_FR_DATE_LIST_WEEKDAY, time=_FR_TIME_INTERVAL),
    flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# datetime list with *no* weekday
FR_DATETIME_LIST = re.compile(r"""
    {datelist}
    [^\d]{{,4}}
    {time}
    """.format(datelist=_FR_DATE_LIST, time=_FR_TIME_INTERVAL),
    flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)


# Reccurent weekdays bewteen a (possibly implicit) date interval
# Examples:
# * les lundis, mardis et mercredis
# * le lundi du 5 au 13 mars 2013
FR_WEEKDAY_LIST_PREFIX = r'le(s)?'
FR_WEEKDAY_LIST_SUFFIX = r'\set\s|,\s'

_FR_WEEKDAY_RECURRENCE = r"""
    {prefix}\s
    (?P<weekdays>
        (
            {weekday}(?!\s\d)  # recurrent weekday not followed by a date num
            ({suffix})?
        )+
    )
    \s?(?P<date_interval>{date_interval})?
    (([,\s]+)?(?P<time_interval>{time_interval}))?
    """.format(
    prefix=FR_WEEKDAY_LIST_PREFIX, weekday=FR_WEEKDAY,
    suffix=FR_WEEKDAY_LIST_SUFFIX, date_interval=_FR_DATE_INTERVAL,
    time_interval=_FR_TIME_INTERVAL)

FR_WEEKDAY_RECURRENCE = re.compile(
    _FR_WEEKDAY_RECURRENCE, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

# Reccurent weekdays interval bewteen a (possibly implicit) date interval
# Examples:
# * du lundi au mercredi
# * du  lundi au vendredi du 5 au 13 mars 2013
FR_WEEKDAY_INTERVAL_PREFIX = r'du'
FR_WEEKDAY_INTERVAL_SUFFIX = r'\sau\s'

_FR_WEEKDAY_INTERVAL_RECURRENCE = r"""
    {prefix}\s
    (?P<start_weekday>{weekday}(?!\s\d))  # weekday with no date
    {suffix}
    (?P<end_weekday>{weekday}(?!\s\d))
    ([,\s]+(?P<date_interval>{date_interval}))?
    (\s(?P<time_interval>{time_interval}))?
    """.format(
    prefix=FR_WEEKDAY_INTERVAL_PREFIX, weekday=FR_WEEKDAY,
    suffix=FR_WEEKDAY_INTERVAL_SUFFIX, date_interval=_FR_DATE_INTERVAL,
    time_interval=_FR_TIME_INTERVAL)

FR_WEEKDAY_INTERVAL_RECURRENCE = re.compile(
    _FR_WEEKDAY_INTERVAL_RECURRENCE, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)


# Recurrent 'all days' expression
FR_ALL_WEEKDAYS = r'tous\sles\sjours(,)?'

_FR_ALL_WEEKDAY_RECURRENCE = r"""
    {prefix}
    \s
    (?P<date_interval>{date_interval})?
    (,?\s(?P<time_interval>{time_interval}))?
    """.format(
    prefix=FR_ALL_WEEKDAYS, date_interval=_FR_DATE_INTERVAL,
    time_interval=_FR_TIME_INTERVAL)

FR_ALL_WEEKDAY_RECURRENCE = re.compile(
    _FR_ALL_WEEKDAY_RECURRENCE, flags=re.VERBOSE | re.IGNORECASE | re.UNICODE)

TIMEPOINT_REGEX = {
    'fr': {
        'date': [FR_DATE, FR_NUMERIC_DATE],
        'date_list': [FR_DATE_LIST_WEEKDAY, FR_DATE_LIST],
        '_date_in_list': [FR_DATE_IN_LIST],  # "private" sub-regex
        'date_interval': [FR_DATE_INTERVAL, FR_NUMERIC_DATE_INTERVAL],
        '_time': [FR_TIME],  # "private" sub-regex
        'time_interval': [FR_TIME_INTERVAL],
        'datetime': [FR_DATETIME],
        'datetime_list': [FR_DATETIME_LIST_WEEKDAY, FR_DATETIME_LIST],
        'datetime_interval': [FR_DATETIME_INTERVAL, FR_NUMERIC_DATETIME_INTERVAL],
        'weekday_recurrence': [FR_WEEKDAY_RECURRENCE],
        'weekday_interval_recurrence': [FR_WEEKDAY_INTERVAL_RECURRENCE],
        'allweekday_recurrence': [FR_ALL_WEEKDAY_RECURRENCE]
    }
}

TIMEPOINT_PROBE = {
    'fr': [FR_MONTH, FR_NUMERIC_DATE, FR_TIME_INTERVAL, YEAR, FR_WEEKDAY]
}
