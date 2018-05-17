# -*- coding: utf-8 -*-
"""
Module in charge of transforming a rrule + duraction object into the shortest
human-readable string possible.
"""
from builtins import object
import datetime
from collections import namedtuple

import datection.rendering.utils as utils
from datection.rendering.wrappers import cached_property
from datection.rendering.exceptions import NoFutureOccurence
from datection.rendering.next_occurence import NextOccurenceFormatter
from datection.rendering.seo import SeoFormatter
from datection.rendering.full import FullFormatter
from datection.rendering.place_summary import PlaceSummaryFormatter
from datection.lang import getlocale


FormatterTuple = namedtuple("FormatterTuple", ["formatter", "display_args"])


class DisplaySchedule(object):
    """
    Render a schedule using different formatters, and return the best
    possible rendering.
    """
    def __init__(self):
        self.formatter_tuples = []
        self.best_formatter = None

    def _compare_formatters(self, fmt_tuple_1, fmt_tuple_2):
        """
        Return the formatter tuple generating the smallest rendering
        """
        if not fmt_tuple_1:
            return fmt_tuple_2
        elif not fmt_tuple_2:
            return fmt_tuple_1

        fmt_1 = fmt_tuple_1.formatter.display(**fmt_tuple_1.display_args)
        fmt_2 = fmt_tuple_2.formatter.display(**fmt_tuple_2.display_args)

        return fmt_tuple_1 if len(fmt_1) < len(fmt_2) else fmt_tuple_2

    @cached_property
    def _best_formatter(self):
        """ Return the best formatter tuple among self.formatter_tuples """
        best_formatter = None
        for fmt_tuple in self.formatter_tuples:
            best_formatter = self._compare_formatters(
                best_formatter, fmt_tuple)
        return best_formatter

    def display(self):
        """
        Return the smallest rendering among all the formatter options
        """
        try:
            return self._best_formatter.formatter.display(
                **self._best_formatter.display_args)
        except NoFutureOccurence:
            return u''

    def next_changes(self):
        """ return the formatter next changes datetime """
        return self._best_formatter.formatter.next_changes()


def get_display_schedule(
    schedule, loc, short=False, seo=False, bounds=(None, None),
        reference=utils.get_current_date()):
    """
    get a DisplaySchedule object according to the better ouput
    """
    # make fr_FR.UTF8 the default locale
    locale = getlocale(loc) if getlocale(loc) else 'fr_FR.UTF8'

    display_schedule = DisplaySchedule()
    if seo:
        fmt_tuple = FormatterTuple(SeoFormatter(schedule, locale), {})
        display_schedule.formatter_tuples.append(fmt_tuple)
        return display_schedule
    elif not short:
        fmt_tuple = FormatterTuple(FullFormatter(schedule, locale), {})
        display_schedule.formatter_tuples.append(fmt_tuple)
        return display_schedule
    else:
        if not reference and not bounds:
            start, end = (datetime.datetime.min, datetime.datetime.max)
        else:
            start, end = bounds

        if not isinstance(reference, datetime.datetime):
            reference = datetime.datetime.min

        short_fmt = NextOccurenceFormatter(schedule, start, end, locale)
        default_fmt = FullFormatter(schedule, locale)
        short_fmt_tuple = FormatterTuple(
            short_fmt,
            {
                "reference": reference,
                "summarize": True,
                "prefix": False,
                "abbrev_monthname": True,
                "abbrev_dayname": True
            })
        display_schedule.formatter_tuples.append(short_fmt_tuple)

        default_fmt_tuple = FormatterTuple(
            default_fmt, {
                "prefix": False,
                "abbrev_monthname": True,
                "summarize": True
            })
        display_schedule.formatter_tuples.append(default_fmt_tuple)

        return display_schedule


def get_short_display_place_schedule(schedule, loc):
    """
    Gives a short formatting for place schedule
    """
    locale = getlocale(loc) if getlocale(loc) else 'fr_FR.UTF8'

    fmt = PlaceSummaryFormatter(schedule, locale)

    return fmt.display()


def get_full_display_place_schedule(schedule, loc):
    """
    Gives a long formatting for place schedule trying to avoid
    to display dates bounds (full year interval for instance)
    """
    locale = getlocale(loc) if getlocale(loc) else 'fr_FR.UTF8'

    fmt = FullFormatter(schedule, locale)

    return fmt.display(avoid_bounds_display=True)


def display(schedule, loc, short=False, seo=False, bounds=(None, None),
            reference=utils.get_current_date()):
    """
    Format a schedule into the shortest human readable sentence possible

    args:
        schedule:
            (list) a list of rrule dicts, containing a duration
            and a RFC rrule
        loc:
            (str) the target locale
        short:
            (bool) if True, a shorter sentence will be generated
        bounds:
            limit start / end datetimes beyond which the dates will
            not even be considered
        seo(bool):
            if True, an SeoFormatter will be used
    """
    return get_display_schedule(
        schedule,
        loc,
        short=short,
        seo=seo,
        bounds=bounds,
        reference=reference).display()
