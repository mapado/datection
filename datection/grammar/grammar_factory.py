# -*- coding: utf-8 -*-
from builtins import object
from pyparsing import Optional
from pyparsing import Regex
from pyparsing import OneOrMore
from pyparsing import oneOf
from pyparsing import Each
from pyparsing import Group

from datection.timepoint import Time
from datection.grammar import DAY_NUMBER
from datection.grammar import YEAR
from datection.grammar import HOUR
from datection.grammar import MINUTE
from datection.grammar import SECOND
from datection.grammar import NUMERIC_MONTH
from datection.grammar import NUMERIC_YEAR
from datection.grammar import optional_ci
from datection.grammar import optional_oneof_ci
from datection.grammar import oneof_ci
from datection.grammar import as_time_interval
from datection.grammar import as_date_interval
from datection.grammar import as_date
from datection.grammar import as_time
from datection.grammar import as_datetime
from datection.grammar import as_datelist
from datection.grammar import as_datetime_list
from datection.grammar import as_datetime_list_multitime
from datection.grammar import as_weekday_interval
from datection.grammar import as_weekday_list
from datection.grammar import as_continuous_datetime_interval
from datection.grammar import as_weekly_recurrence
from datection.grammar import develop_datetime_patterns
from datection.grammar import develop_datetime_interval_patterns
from datection.grammar import develop_weekly_recurrence_patterns
from datection.grammar import extract_time_patterns
from datection.grammar import complete_partial_date

from dateutil.rrule import weekdays
import importlib


class GrammarFactory(object):

    def __init__(self, lang_module):
        """"""
        module = importlib.import_module(lang_module)
        self._weekdays = module.WEEKDAYS
        self._short_weekdays = module.SHORT_WEEKDAYS
        self._months = module.MONTHS
        self._short_months = module.SHORT_MONTHS
        self._ordinal_appendix = module.ORDINAL_APPENDIX
        self._time_prepositions = module.TIME_PREPOSITIONS
        self._time_conjunctions = module.TIME_CONJUNCTIONS
        self._time_interval_start = module.TIME_INTERVAL_START
        self._time_interval_middle = module.TIME_INTERVAL_MIDDLE
        self._date_preposition = module.DATE_PREPOSITION
        self._date_conjunctions = module.DATE_CONJUNCTIONS
        self._date_interval_start = module.DATE_INTERVAL_START
        self._date_interval_middle = module.DATE_INTERVAL_MIDDLE
        self._date_time_links = module.DATE_TIME_LINKS
        self._weekly_list_start = module.WEEKLY_LIST_START
        self._weekly_list_middle = module.WEEKLY_LIST_MIDDLE
        self._open = module.OPEN

    def set_weekday(self, text, start_index, match):
        """ Return the month number from the month name. """
        idx = self._weekdays.get(match[0].lower())
        if idx is None:
            idx = self._short_weekdays.get(match[0].lower())
        return weekdays[idx]

    def weekday_grm(self):
        """
        A weekday name can be in its full form or abbreviated form
        """
        return (
            (
                # weekday with optional s at the end
                oneof_ci(list(self._weekdays.keys())) + Optional(Regex(r'(?<!\s)s?'))
            ) |
            # short weekday not followed by another alphanum char
            oneof_ci(list(self._short_weekdays.keys())) + Regex(r'\.?(?!\w)').leaveWhitespace()
        ).setParseAction(self.set_weekday)('weekday')

    def set_month_number(self, text, start_index, match):
        """ Return the month number from the month name. """
        return (
            self._months.get(match[0].lower()) or
            self._short_months.get(match[0].lower())
        )

    def month_grm(self):
        """
        A month name can be in its full form or an abbreviated form.
        When matched, a month name will be transformed to the corresponding
        month index.
        """
        return oneof_ci(
            list(self._months.keys()) +
            list(self._short_months.keys()),
        ).setParseAction(self.set_month_number)('month')

    def daynumber_grm(self):
        """
        Adds the potential appendix: 1 -> 1st or 2 -> 2nd
        """
        return DAY_NUMBER + optional_oneof_ci(self._ordinal_appendix)

    def as_time_12(self, text, start_index, matches):
        """ Return a Time instance from a TIME pattern match. """
        hour = matches['hour']
        minute = matches.get('minute') if matches.get('minute') else 0
        if matches['period'].lower() == 'pm':
            hour += 12
        return Time(hour, minute)

    def time_12_grm(self):
        """
        (at) 10(:30) am/pm
        """
        return (
            optional_oneof_ci(self._time_prepositions) +
            HOUR +
            Optional(u':') +
            Optional(MINUTE) +
            oneof_ci([u'am', 'pm'])('period')
        ).setParseAction(self.as_time_12)

    def time_24_grm(self):
        """
        (à) 18h(30)
        """
        return (
            optional_oneof_ci(self._time_prepositions) +
            HOUR +
            oneof_ci([u'h', u':']) +
            Optional(MINUTE) +
            Optional(u':') +
            Optional(SECOND)
        ).setParseAction(as_time)

    def time_interval_grm(self, time_grm):
        """
        A time interval is composed of a start time, an optional separator and
        an optional end time.
        15h30 is a time interval bewteen 15h30 and 15h30
        15h30 - 17h speaks for itself
        """
        return (
            optional_oneof_ci(self._time_interval_start) +
            time_grm('start_time') +
            optional_oneof_ci(self._time_interval_middle) +
            Optional(time_grm('end_time'))
        ).setParseAction(as_time_interval)

    def time_pattern_grm(self, time_interval_grm):
        """
        Meta pattern catching a list of time patterns (time or time interval)
        """
        return (
            OneOrMore(
                time_interval_grm +
                Optional(OneOrMore(oneOf(self._time_conjunctions)))
            )('patterns')
        ).setParseAction(extract_time_patterns)

    def date_pattern_grm(self, weekday_grm, date_grm, numeric_date_grm):
        """
        Le vendredi 12 décembre
        """
        return (
            optional_oneof_ci(self._date_preposition) +
            Optional(weekday_grm) +
            (date_grm | numeric_date_grm)
        ).setParseAction(as_date)

    def date_list_grm(self, date_grm):
        """
        Les samedi 12 janvier et dimanche 14 mars
        """
        return (
            optional_oneof_ci(self._date_preposition) +
            Group(
                date_grm +
                OneOrMore(date_grm)
            )('dates')
        ).setParseAction(as_datelist)

    def date_interval_grm(self, weekday_grm, partial_date_grm, date_pattern_grm):
        """
        A date interval is composed of a start (possibly partial) date and an
        end date
        """
        return (
            optional_oneof_ci([',', '-']) +
            optional_oneof_ci(self._date_interval_start) +
            partial_date_grm('start_date') +
            oneof_ci(self._date_interval_middle) +
            Optional(weekday_grm) +
            date_pattern_grm('end_date') +
            optional_oneof_ci([',', '-'])
        ).setParseAction(as_date_interval)

    def datetime_pattern_grm(self, date_pattern_grm, time_pattern_grm):
        """
        A datetime is a date, a separator and a time interval (either a single)
        time, or a start time and an end time
        """
        return (
            date_pattern_grm('date') +
            optional_oneof_ci(self._date_time_links) +
            optional_oneof_ci(list(self._weekdays.keys()) + list(self._short_weekdays.keys())) +
            Optional('.') +
            time_pattern_grm('time_pattern')
        ).setParseAction(develop_datetime_patterns)

    def datetime_list_grm(self, datetime_grm):
        """
        Le vendredi 12 à 14h et le samedi 13 à 15h
        """
        return (
            Group(
                datetime_grm +
                OneOrMore(
                    Optional(oneOf(self._date_conjunctions)) +
                    datetime_grm
                )
            )('datetime')
        ).setParseAction(as_datetime_list_multitime)

    def date_timeinterval_grm(self, date_pattern_grm, time_interval_grm):
        """
        A datetime is a date, a separator and a time interval (either a single)
        time, or a start time and an end time
        """
        return (
            date_pattern_grm('date') +
            optional_oneof_ci(self._date_time_links) +
            Optional('.') +
            time_interval_grm('time_interval')
        ).setParseAction(as_datetime)

    def dateinterval_time_grm(self, date_interval_grm, time_pattern_grm):
        """
        From April 1st to May 2nd, between 10am and 2pm
        """
        return (
            optional_oneof_ci([',', '-']) +
            date_interval_grm('date_interval') +
            Optional(u',') +
            time_pattern_grm('time_patterns') +
            optional_oneof_ci([',', '-'])
        ).setParseAction(develop_datetime_interval_patterns)

    def datelist_timeinterval_grm(self, date_grm, time_interval_grm):
        """
        A datetime list is a list of dates, along with a time interval
        """
        return (
            optional_oneof_ci(self._date_preposition) +
            OneOrMore(date_grm)('dates') +
            Optional(u',') +
            optional_oneof_ci(self._date_time_links) +
            time_interval_grm('time_interval')
        ).setParseAction(as_datetime_list)


    def continuous_datetime_interval_grm(self, date_pattern_grm, time_grm):
        """
        Example: du 5 mars 2015 à 13h au 7 mars 2015 à 7h
        """
        return (
            optional_oneof_ci(self._date_interval_start) +
            date_pattern_grm("start_date") +
            optional_oneof_ci(self._date_time_links) +
            time_grm("start_time") +
            oneof_ci(self._date_interval_middle) +
            date_pattern_grm("end_date") +
            optional_oneof_ci(self._date_time_links) +
            time_grm("end_time")
        ).setParseAction(as_continuous_datetime_interval)

    def weekday_interval_grm(self, weekday_grm):
        """
        An interval of weekdays
        """
        return (
            optional_ci(self._open) +
            optional_oneof_ci(self._date_interval_start) +
            weekday_grm +
            optional_oneof_ci(self._date_interval_middle) +
            weekday_grm
        ).setParseAction(as_weekday_interval)('weekdays')

    def weekday_pattern_grm(self, weekday_interval_grm, weekday_list_grm):
        """
        """
        return (
            optional_oneof_ci([',', '-']) +
            (weekday_interval_grm | weekday_list_grm) +
            optional_oneof_ci([',', '-'])
        )

    def weekday_list_grm(self, weekday_grm):
        """
        Open every Monday and Tuesday
        """
        return (
            optional_oneof_ci(self._weekly_list_start) +
            OneOrMore(
                weekday_grm +
                Optional(OneOrMore(oneOf(self._weekly_list_middle)))
            )
        ).setParseAction(as_weekday_list)('weekdays')

    def weekly_recurrence(self, weekday_pattern_grm, time_pattern_grm, date_interval_grm):
        """
        """
        return Each(
            [
                weekday_pattern_grm('weekdays'),
                Optional(time_pattern_grm('time_interval')),
                Optional(date_interval_grm('date_interval')),
            ]
        ).setParseAction(as_weekly_recurrence)

    def multiple_weekly_recurrence_grm(self, weekday_pattern_grm, time_pattern_grm, date_interval_grm):
        """
        Ex: Du 29/03/11 au 02/04/11 - Mardi, mercredi samedi à 19h, jeudi à
        20h30 et vendredi à 15h"
        """
        return (
            Optional(date_interval_grm('date_interval')) +
            (
                Group(
                    weekday_pattern_grm +
                    time_pattern_grm
                ) +
                OneOrMore(
                    optional_oneof_ci(self._date_conjunctions) +
                    Group(
                        weekday_pattern_grm +
                        time_pattern_grm
                    )
                )
            )('groups')
        ).setParseAction(develop_weekly_recurrence_patterns)

    def british_date_grm(self, month_grm, daynumber_grm):
        """
        5(th) (of) October(,) 2004
        """
        return (
            daynumber_grm +
            optional_ci(u'of') +
            month_grm +
            Optional(u'.') +  # for abbreviated months
            Optional(u',') +
            YEAR
        )

    def american_date_grm(self, month_grm, daynumber_grm):
        """
        October (the) 5(th), 2004
        """
        return (
            month_grm +
            Optional(u'.') +
            optional_ci(u'the') +
            daynumber_grm +
            Optional(u',') +
            YEAR
        )

    def french_date_grm(self, daynumber_grm, month_grm):
        """
        5 avril (2016)
        """
        return (
            daynumber_grm +
            month_grm +
            Optional(u'.') +  # for abbreviated months
            Optional(YEAR)
        )

    def british_numeric_date_grm(self):
        """
        (0)5/(0)2/(20)04 or (0)5-(0)2-(20)04
        """
        return (
            DAY_NUMBER +
            optional_oneof_ci(['/', '-', u'.']) +
            NUMERIC_MONTH +
            optional_oneof_ci(['/', '-', u'.']) +
            NUMERIC_YEAR
        )

    def american_numeric_date_grm(self):
        """
        (20)14/(0)5/(0)1 or (20)14-(0)5-(0)1
        Note that american numeric date are not allowed to have
        2 digit years, as it would create a confusion in certain cases
        Example: 04/05/08 --> Date(2004, 5, 8) or Date(2008, 5, 4)?
        """
        return (
            YEAR +
            optional_oneof_ci(['/', '-', u'.']) +
            NUMERIC_MONTH +
            optional_oneof_ci(['/', '-', u'.']) +
            DAY_NUMBER
        )

    def french_numeric_date_grm(self):
        """
        Example: 05/10/2012, 05/03
        """
        return (
            DAY_NUMBER +
            oneOf([u'/', u'-', u'.']) +
            NUMERIC_MONTH +
            Optional(
                oneOf([u'/', u'-', u'.']) +
                NUMERIC_YEAR
            )
        )

    def end_litteral_date_grm(self, month_grm):
        """
        End of a litteral date, meaning a month and an optional
        year.
        """
        return (
            month_grm +
            Optional(YEAR)
        ).setParseAction(as_date)

    def end_numeric_date_grm(self):
        """
        End of a litteral date, meaning a month and an optional
        year.
        """
        return (
            NUMERIC_MONTH +
            Optional(
                oneOf([u'/', u'-', u'.']) +
                NUMERIC_YEAR
            )
        ).setParseAction(as_date)

    def repeatable_date_grm(self, weekday_grm, day_grm, month_grm):
        """
        A partial date is a mandatory day number, and optional litteral/numeric
        month and year, and optional separator
        """
        end_litteral_date_grm = self.end_litteral_date_grm(month_grm)
        end_numeric_date_grm = self.end_numeric_date_grm()
        return (
            Optional(weekday_grm) +
            day_grm('day') +
            Optional(oneOf([u'/', u'-', u'.'])) +
            Optional(
                end_litteral_date_grm('partial_date') |
                end_numeric_date_grm('partial_date')
            ) +
            Optional(OneOrMore(oneOf(self._date_conjunctions)))
        ).setParseAction(complete_partial_date)
