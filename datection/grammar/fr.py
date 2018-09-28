# -*- coding: utf-8 -*-
"""
Definition of French specific grammar, related to temoral expressions.
"""
from __future__ import absolute_import
from pyparsing import Optional

from datection.grammar import YEAR
from datection.grammar import oneof_ci

from .grammar_factory import GrammarFactory

grm_gen = GrammarFactory('datection.data.fr')

# base patterns
WEEKDAY = grm_gen.weekday_grm()
MONTH = grm_gen.month_grm()
DAY_NUMBER = grm_gen.daynumber_grm()

# date basic patterns
DATE = grm_gen.french_date_grm(DAY_NUMBER, MONTH)
END_LITTERAL_DATE = grm_gen.end_litteral_date_grm(MONTH)
END_NUMERIC_DATE = grm_gen.end_numeric_date_grm()
FR_NUMERIC_DATE = grm_gen.french_numeric_date_grm()
US_NUMERIC_DATE = grm_gen.american_numeric_date_grm()
NUMERIC_DATE = ((FR_NUMERIC_DATE | US_NUMERIC_DATE) + Optional(u','))

# date more complex patterns
DATE_PATTERN = grm_gen.date_pattern_grm(WEEKDAY, DATE, NUMERIC_DATE)
REPEATABLE_DATE = grm_gen.repeatable_date_grm(WEEKDAY, DAY_NUMBER, MONTH)
DATE_LIST = grm_gen.date_list_grm(REPEATABLE_DATE)
DATE_INTERVAL = grm_gen.date_interval_grm(WEEKDAY, REPEATABLE_DATE, DATE_PATTERN)

# time basic patterns
TIME = grm_gen.time_24_grm()
TIME_INTERVAL = grm_gen.time_interval_grm(TIME)
TIME_PATTERN = grm_gen.time_pattern_grm(TIME_INTERVAL)

# date-time patterns
DATETIME = grm_gen.date_timeinterval_grm(DATE_PATTERN, TIME_INTERVAL)
DATETIME_PATTERN = grm_gen.datetime_pattern_grm(DATE_PATTERN, TIME_PATTERN)
DATELIST_TIMEINTERVAL = grm_gen.datelist_timeinterval_grm(REPEATABLE_DATE, TIME_INTERVAL)
DATETIME_LIST_MULTITIME = grm_gen.datetime_list_grm(DATETIME)
DATETINTERVAL_TIME = grm_gen.dateinterval_time_grm(DATE_INTERVAL, TIME_PATTERN)
CONTINUOUS_DATETIME_INTERVAL = grm_gen.continuous_datetime_interval_grm(DATE_PATTERN, TIME)

# weekdays patterns
WEEKDAY_LIST = grm_gen.weekday_list_grm(WEEKDAY)
WEEKDAY_INTERVAL = grm_gen.weekday_interval_grm(WEEKDAY)
WEEKDAY_PATTERN = grm_gen.weekday_pattern_grm(WEEKDAY_INTERVAL, WEEKDAY_LIST)
WEEKLY_RECURRENCE = grm_gen.weekly_recurrence(WEEKDAY_PATTERN, TIME_PATTERN, DATE_INTERVAL)
MULTIPLE_WEEKLY_RECURRENCE = grm_gen.multiple_weekly_recurrence_grm(WEEKDAY_PATTERN, TIME_PATTERN, DATE_INTERVAL)

EXCLUSION = oneof_ci([u'sauf', u'relâche', u'relache', u'fermé', u'repos', u'excepté'])

TIMEPOINTS = [
    ('weekly_rec', WEEKLY_RECURRENCE, [('weekly_rec_multi', MULTIPLE_WEEKLY_RECURRENCE)]),

    ('datetime', DATETIME_PATTERN, [
        ('datetime_list', DATELIST_TIMEINTERVAL),
        ('datetime_interval', DATETINTERVAL_TIME),
        ('continuous_datetime_interval', CONTINUOUS_DATETIME_INTERVAL),
        ('datetime_list_multitime', DATETIME_LIST_MULTITIME),
    ]),

    ('date', DATE_PATTERN, [
        ('date_list', DATE_LIST),
        ('date_interval', DATE_INTERVAL),
    ]),

    ('time_pattern', TIME_PATTERN),

    ('exclusion', EXCLUSION),
]

PROBES = [MONTH, NUMERIC_DATE, TIME_INTERVAL, YEAR, WEEKDAY, DAY_NUMBER]

# List of expressions associated with their replacement
# This replacement allows to reduce the complexity of the patterns
EXPRESSIONS = {
    u'midi': u'12h',
    u'minuit': u'23h59',
    u'(uniquement )?le matin': u'de 8h à 12h',
    u'(uniquement )?en journée': u'de 8h à 18h',
    u'(uniquement )?en soirée': u'de 18h à 22h',
    u"l'après-midi": u'de 14h à 18h',
    u'tous les jours': u'du lundi au dimanche',
    u"toute l'année": u'Du 1er janvier au 31 décembre',
    u"jusqu'à": u"à",
    u"jusqu'au": u"au",
    u'(à|a) partir de': u'de',
}
