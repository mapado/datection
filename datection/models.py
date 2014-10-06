# -*- coding: utf-8 -*-

"""
Utility models for datection.
"""

from datetime import timedelta
from datetime import datetime
from datetime import time
from datetime import date
from dateutil.rrule import rrulestr
from dateutil.rrule import rruleset

from datection.utils import cached_property
from datection.timepoint import DAY_START
from datection.timepoint import DAY_END
from datection.timepoint import MISSING_YEAR
from datection.timepoint import ALL_DAY


class DurationRRule(object):

    """Wrapper around a rrule + duration object, providing handy properties
    to ease the manipulation of rrules.

    """

    def __init__(self, duration_rrule, apply_exclusion=True):
        self.duration_rrule = duration_rrule
        self.apply_exclusion = apply_exclusion

    def __hash__(self):
        data = {
            'duration': self.duration_rrule['duration'],
            'rrule': self.duration_rrule['rrule'],
        }
        return hash(frozenset(data.items()))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self == other

    def __iter__(self):
        """Iterate over the dates generated by the DurationRRule rrule.

        If the rrule is not bounded, only the dates in the upcoming year
        (from the current date) will be iterated over.

        """
        if self.bounded:
            for dtime in self.date_producer:
                yield dtime
        else:
            self.rrule._dtstart = datetime.combine(date.today(), DAY_START)
            end_bound_date = date.today() + timedelta(days=365)
            end_bound = datetime.combine(end_bound_date, DAY_END)
            for dtime in self.date_producer:
                if dtime < end_bound:
                    yield dtime
                else:
                    raise StopIteration

    @cached_property
    def exclusion_rrules(self):
        """Return the list of exclusion rrules."""
        return [
            rrulestr(exc_rrule)
            for exc_rrule in self.duration_rrule.get('excluded', [])
        ]

    @cached_property
    def rrule(self):
        """Instanciate an rrule from the rrule string

        As this is a lazy property, the rrulestr -> rrule operation
        is only performed the first time.

        """
        return rrulestr(self.duration_rrule['rrule'])

    @property
    def date_producer(self):
        """Return an iterator yielding every dates defined by both the
        rrule and exclusion rrules.

        """
        if not self.exclusion_rrules or not self.apply_exclusion:
            return self.rrule

        rset = rruleset()
        rset.rrule(self.rrule)
        for ex_rrule in self.exclusion_rrules:
            rset.exrule(ex_rrule)
        return rset

    @property
    def duration(self):
        """The DurationRRule duration, in minutes (as an integer)."""
        return int(self.duration_rrule['duration'])

    @property
    def unlimited(self):
        """Whether the DurationRRule is bounded or not."""
        if self.duration_rrule.get('unlimited'):
            return True
        return self.rrule._until is None and self.rrule._count is None

    @property
    def is_continuous(self):
        """Whether the rrule is to be taken by intervals, or continuously."""
        return self.duration_rrule.get('continuous', False)

    @property
    def start_datetime(self):
        """The DurationRRule start is a combination of the rrule.dstart
        and the start time.

        """
        start_time = self.time_interval[0]
        return datetime.combine(self.rrule.dtstart, start_time)

    @property
    def end_datetime(self):
        """The end datetime of the DurationRRule, where the end date
        is either the until date, of if no until datetime is specified,
        the dtstart date, added with the rrule duration (in minutes).

        """
        if self.rrule.until or self.rrule.count:
            if self.rrule.until:
                end_date = self.rrule.until
            else:
                for dtime in self:
                    pass  # ugly hack
                end_date = dtime

            if self.is_continuous:
                return datetime.combine(
                    end_date, self.time_interval[1])
            else:
                return datetime.combine(
                    end_date, self.time_interval[0]
                ) + timedelta(minutes=self.duration)
        else:
            return datetime.combine(
                self.rrule.dtstart.date(), self.time_interval[0]
            ) + timedelta(days=365, minutes=self.duration)

    @property
    def date_interval(self):
        """The DurationRRule date interval.

        If the rrule specifies an until datetime, returns a tuple of
        2 elements: the dtstart date and the until date. Otherwise,
        return a tuple of 2 elements: the the dtstart date and None.

        """
        if self.rrule.until:
            return (self.rrule.dtstart.date(), self.rrule.until.date())
        return (self.rrule.dtstart.date(), None)

    @property
    def time_interval(self):
        """The DurationRRule time interval.

        If the rrule specifies a start time, returns a tuple of 2
        elements: the start time, and start time + duration.
        Otherwise, return the default value: (time(0, 0, 0), time(23, 59))

        """
        if (self.rrule.byminute is not None
                and self.rrule.byhour is not None):
            start_time = time(self.rrule.byhour[0], self.rrule.byminute[0])
            end_dt = datetime.combine(datetime.today(), start_time)
            end_time = (end_dt + timedelta(minutes=self.duration)).time()
            return (start_time, end_time)
        else:
            return (DAY_START, DAY_END)

    @property
    def weekday_indexes(self):
        """The list of index of recurrent weekdays."""
        if self.rrule.byweekday:
            return [wk.weekday for wk in self.rrule.byweekday]

    @property
    def weekday_interval(self):
        """The index interval bewteen the first and last recurrent weekdays

        """
        if self.rrule.byweekday:
            start_idx = self.weekday_indexes[0]
            end_idx = self.weekday_indexes[-1]
            return range(start_idx, end_idx + 1)

    @property
    def is_recurring(self):
        if not 'BYDAY' in self.duration_rrule['rrule']:
            return False
        if len(self.rrule.byweekday) == 7 and not self.is_all_year_recurrence:
            # if a rrule says "every day from DT_START to DT_END", it is
            # similar to "from DT_START to DT_END", hence it is not a
            # recurrence!
            return False
        return True

    @property
    def is_all_year_recurrence(self):
        if not 'BYDAY' in self.duration_rrule['rrule']:
            return False
        return self.rrule.dtstart + timedelta(days=365) == self.rrule.until

    @property
    def missing_year(self):
        """Return True if the recurrence rule year is 1."""
        return self.rrule.dtstart.year == MISSING_YEAR

    @property
    def bounded(self):
        """Return True if the RRule has a specified UNTIL datetime, else
        return False.

        """
        return not self.unlimited
