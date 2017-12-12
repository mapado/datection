# -*- coding: utf-8 -*-
"""
Definition of English specific grammar, related to temoral expressions.
"""
from __future__ import absolute_import
from datection.grammar import YEAR
from datection.grammar import oneof_ci

from .grammar_factory import GrammarFactory

grm_gen = GrammarFactory('datection.data.en')

# Base grammars
WEEKDAY = grm_gen.weekday_grm()
MONTH = grm_gen.month_grm()
DAY_NUMBER_EXT = grm_gen.daynumber_grm()

# Time grammars
TIME = grm_gen.time_12_grm()
TIME_INTERVAL = grm_gen.time_interval_grm(TIME)
TIME_PATTERN = grm_gen.time_pattern_grm(TIME_INTERVAL)

# Date grammars
BRITISH_DATE = grm_gen.british_date_grm(MONTH, DAY_NUMBER_EXT)
AMERICAN_DATE = grm_gen.american_date_grm(MONTH, DAY_NUMBER_EXT)
DATE = (BRITISH_DATE | AMERICAN_DATE)

# Numeric date grammars
BRITISH_NUMERIC_DATE = grm_gen.british_numeric_date_grm()
AMERICAN_NUMERIC_DATE = grm_gen.american_numeric_date_grm()
NUMERIC_DATE = (BRITISH_NUMERIC_DATE | AMERICAN_NUMERIC_DATE)

# Complex patterns
DATE_PATTERN = grm_gen.date_pattern_grm(WEEKDAY, DATE, NUMERIC_DATE)
DATETIME_PATTERN = grm_gen.datetime_pattern_grm(DATE_PATTERN, TIME_PATTERN)

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
