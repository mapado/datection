# -*- coding: utf-8 -*-

"""
Utility models for datection.
"""

from datetime import timedelta
from datetime import datetime
from datetime import time
from dateutil.rrule import rrulestr

from datection.utils import lazy_property


class DurationRRule(object):

    """Wrapper around a rrule + duration object, providing handy properties
    to ease the manipulation of rrules.

    """

    def __init__(self, duration_rrule):
        self.duration_rrule = duration_rrule

    @lazy_property
    def rrule(self):
        """Instanciate an rrule from the rrule string

        As this is a lazy property, the rrulestr -> rrule operation
        is only performed the first time.

        If the rrule defined weekly recurrence and has no 'until' date,
        one will be set automatically, to avoid infinite loops when
        iterating over the rrule dates.

        """
        rrule = rrulestr(self.duration_rrule['rrule'])

        # Set the until date to one year in the future if non existent
        if rrule.byweekday and not rrule.until:
            rrule._until = datetime.combine(
                rrule.dtstart.date() + timedelta(days=365),
                time(23, 59))
        return rrule

    @property
    def duration(self):
        """The DurationRRule duration, in minutes (as an integer)."""
        return int(self.duration_rrule['duration'])

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
        if self.rrule.until:
            if self.is_continuous:
                return datetime.combine(
                    self.rrule.until.date(), self.time_interval[1])
            else:
                return datetime.combine(
                    self.rrule.until.date(), self.time_interval[0]
                ) + timedelta(minutes=self.duration)
        else:
            return datetime.combine(
                self.rrule.dtstart.date(), self.time_interval[0]
            ) + timedelta(minutes=self.duration)

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
            return (time(0, 0), time(23, 59))

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
