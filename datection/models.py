# -*- coding: utf-8 -*-

"""
Utility models for datection.
"""

import re

from datetime import timedelta
from datetime import datetime
from datetime import time
from datetime import date
from dateutil.rrule import rrulestr
from dateutil.rrule import rruleset
from dateutil.rrule import rrule
from dateutil.rrule import FREQNAMES

from datection.utils import cached_property
from datection.utils import cleanup_rrule_string
from datection.utils import UNLIMITED_DATETIME_START
from datection.utils import UNLIMITED_DATETIME_END
from datection.timepoint import DAY_START
from datection.timepoint import DAY_END
from datection.timepoint import ALL_DAY


class DurationRRule(object):

    """Wrapper around a rrule + duration object, providing handy properties
    to ease the manipulation of rrules.

    """

    def __init__(
            self,
            duration_rrule,
            apply_exclusion=True,
            forced_lower_bound=None,
            forced_upper_bound=None):
        self.duration_rrule = duration_rrule
        self.apply_exclusion = apply_exclusion
        self.forced_lower_bound = forced_lower_bound
        self.forced_upper_bound = forced_upper_bound

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
            if self.forced_lower_bound:
                start_bound_date = self.forced_lower_bound
            else:
                start_bound_date = date.today()
            if type(start_bound_date) == datetime:
                self.rrule._dtstart = start_bound_date
            else:
                self.rrule._dtstart = datetime.combine(start_bound_date, DAY_START)
            if self.forced_upper_bound:
                end_bound_date = self.forced_upper_bound
            else:
                end_bound_date = date.today() + timedelta(days=365)
            end_bound = datetime.combine(end_bound_date, DAY_END)
            for dtime in self.date_producer:
                if dtime < end_bound:
                    yield dtime
                else:
                    raise StopIteration

    def set_weekdays(self, weekdays):
        """Update the rrule byweekday property and the underlying
        duration_rrule rrule string.

        """
        self.duration_rrule['rrule'] = re.sub(
            r'(?<=BYDAY=)[^;]+',
            ','.join(str(w) for w in weekdays),
            self.duration_rrule['rrule'])
        self.rrule._byweekday = [w.weekday for w in weekdays]

    def add_weekdays(self, weekdays):
        """
        Adds the days of the week to the rrule
        """
        weekdays_str = ";BYDAY=" + ','.join(str(w) for w in weekdays)
        self.duration_rrule['rrule'] += weekdays_str
        self.rrule._byweekday = [w.weekday for w in weekdays]

    def set_frequency(self, freq):
        """
        Sets the frequency type of the rrule (DAILY/WEAKLY/...)
        """
        self.duration_rrule['rrule'] = re.sub(
            r'(?<=FREQ=)[^;]+',
            freq,
            self.duration_rrule['rrule'])
        self.rrule._freq = FREQNAMES.index(freq)

    def add_interval_ind(self):
        """
        Adds the interval indicator to the rrule
        """
        self.duration_rrule['rrule'] += ';INTERVAL=1'
        self.rrule._interval = 1

    def remove_count(self):
        """
        Removes the COUNT attribute of the rrule
        """
        self.duration_rrule['rrule'] = re.sub(
            r';?COUNT=[^;]+',
            '',
            self.duration_rrule['rrule'])
        self.rrule._count = 0

    def set_startdate(self, start_date):
        """
        Update the rrule start date property and the underlying dstart.
        """
        self.duration_rrule['rrule'] = re.sub(
            r'(?<=DTSTART:)[^\n]+',
            start_date.strftime('%Y%m%d'),
            self.duration_rrule['rrule'])
        self.rrule._dstart = start_date

    def set_enddate(self, end_date):
        """
        Update the rrule end date property and the underlying _until.
        """
        if end_date is not None:
            self.duration_rrule['rrule'] = re.sub(
                r'(?<=UNTIL=)[^T]+',
                end_date.strftime('%Y%m%d'),
                self.duration_rrule['rrule'])
        else:
            self.duration_rrule['rrule'] = re.sub(
                r'(?<=UNTIL=)[^T]+',
                '',
                self.duration_rrule['rrule'])

        self.rrule._until = end_date

    def add_enddate(self, end_date):
        """
        Adds an end date (UNTIL) to the rrule
        """
        end_datetime = datetime.combine(end_date, DAY_END)
        end_str = ";UNTIL=" + end_datetime.strftime('%Y%m%dT%H%M%S')
        self.duration_rrule['rrule'] += end_str
        self.rrule._until = end_datetime

    @cached_property
    def exclusion_rrules(self):
        """Return the list of exclusion rrules."""

        # input exclusions strings might be incomplete regarding
        # the start and the end of the exclusions
        ex_rrules = self.duration_rrule.get('excluded', [])
        for idx in xrange(len(ex_rrules)):
            if ex_rrules[idx].find("DTSTART") == -1:
                rrule_start = self.rrule._dtstart
                start = "DTSTART:%s\n" % rrule_start.strftime('%Y%m%dT%H%M%S')
                ex_rrules[idx] = start + ex_rrules[idx]
            if ex_rrules[idx].find("UNTIL") == -1:
                rrule_until = self.rrule._until
                rrule_end = ";UNTIL=" + rrule_until.strftime('%Y%m%dT%H%M%S')
                ex_rrules[idx] = ex_rrules[idx] + rrule_end

        return [
            rrulestr(cleanup_rrule_string(exc_rrule))
            for exc_rrule in self.duration_rrule.get('excluded', [])
        ]

    @cached_property
    def exclusion_duration(self):
        """
        Return the list of exclusion duration (may be filled with
        Nones in case the container was missing in the serialized string)
        """
        exclusion_nb = len(self.duration_rrule.get('excluded', []))
        return self.duration_rrule.get('excluded_duration', [None] * exclusion_nb)

    @cached_property
    def rrule(self):
        """Instanciate an rrule from the rrule string

        As this is a lazy property, the rrulestr -> rrule operation
        is only performed the first time.

        """
        rrule_str = cleanup_rrule_string(self.duration_rrule['rrule'])
        rrule = rrulestr(rrule_str)

        # when we are in unlimited mode, datection need to
        # have DTSTART=01-01-0001 & UNTIL=31-12-9999
        if self.duration_rrule.get('unlimited'):
            rrule._dtstart   = UNLIMITED_DATETIME_START
            rrule._until     = UNLIMITED_DATETIME_END

        return rrule

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
            if (self.rrule._byhour != ex_rrule._byhour or
               self.rrule._byminute != ex_rrule._byminute):
                rset.rrule(ex_rrule)
                mask_kwargs = {"interval": ex_rrule._interval,
                               "count": ex_rrule._count,
                               "dtstart": ex_rrule._dtstart,
                               "freq": ex_rrule._freq,
                               "until": ex_rrule._until,
                               "wkst": ex_rrule._wkst,
                               "cache": False if ex_rrule._cache is None else True,
                               "byweekday": ex_rrule._byweekday}
                mask_kwargs.update({"byhour": self.rrule._byhour,
                                    "byminute": self.rrule._byminute})
                mask_rrule = rrule(**mask_kwargs)
                rset.exrule(mask_rrule)
            else:
                rset.exrule(ex_rrule)
        return rset

    @property
    def duration(self):
        """The DurationRRule duration, in minutes (as an integer)."""
        return int(self.duration_rrule['duration'])

    @property
    def start_datetime(self):
        """The DurationRRule start is a combination of the rrule.dstart
        and the start time.

        """
        start_time = self.time_interval[0]
        return datetime.combine(self.rrule._dtstart, start_time)

    @property
    def end_datetime(self):
        """The end datetime of the DurationRRule, where the end date
        is either the until date, of if no until datetime is specified,
        the dtstart date, added with the rrule duration (in minutes).

        """
        if self.rrule._until or self.rrule._count:
            if self.rrule._until:
                end_date = self.rrule._until
            else:
                for dtime in self:
                    pass  # ugly hack
                end_date = dtime

            if self.is_continuous:
                return datetime.combine(
                    end_date, self.time_interval[1])
            else:
                date = datetime.combine(end_date, self.time_interval[0])
                try:
                    return date + timedelta(minutes=self.duration)
                except OverflowError:
                    return date
        else:
            date = datetime.combine(
                self.rrule._dtstart.date(),
                self.time_interval[0]
            )
            try:
                return date + timedelta(days=365, minutes=self.duration)
            except OverflowError:
                return date

    @property
    def date_interval(self):
        """The DurationRRule date interval.

        If the rrule specifies an until datetime, returns a tuple of
        2 elements: the dtstart date and the until date. Otherwise,
        return a tuple of 2 elements: the the dtstart date and None.

        """
        if self.rrule._until:
            return (self.rrule._dtstart.date(), self.rrule._until.date())
        return (self.rrule._dtstart.date(), None)

    @property
    def time_interval(self):
        """The DurationRRule time interval.

        If the rrule specifies a start time, returns a tuple of 2
        elements: the start time, and start time + duration.
        Otherwise, return the default value: (time(0, 0, 0), time(23, 59))

        """
        if (self.rrule._byminute and self.rrule._byhour and not self.duration == ALL_DAY):
            first_hour = sorted(list(self.rrule._byhour))[0]
            first_minute = sorted(list(self.rrule._byminute))[0]
            start_time = time(first_hour, first_minute)
            end_dt = datetime.combine(datetime.today(), start_time)
            end_time = (end_dt + timedelta(minutes=self.duration)).time()
            return (start_time, end_time)
        else:
            return (DAY_START, DAY_END)

    @property
    def weekday_indexes(self):
        """The list of index of recurrent weekdays."""
        if self.rrule._byweekday:
            return sorted(list(self.rrule._byweekday))

    @property
    def weekday_interval(self):
        """The index interval bewteen the first and last recurrent weekdays

        """
        if self.rrule._byweekday:
            start_idx = self.weekday_indexes[0]
            end_idx = self.weekday_indexes[-1]
            return range(start_idx, end_idx + 1)

    @property
    def is_recurring(self):
        if not 'BYDAY' in self.duration_rrule['rrule']:
            return False
        if ((self.rrule._byweekday is not None) and len(self.rrule._byweekday) == 7 and
            not self.is_all_year_recurrence):
            # if a rrule says "every day from DT_START to DT_END", it is
            # similar to "from DT_START to DT_END", hence it is not a
            # recurrence!
            return False
        if 'COUNT=1' in self.duration_rrule['rrule']:
            return False
        return True

    @property
    def is_all_year_recurrence(self):
        if not 'BYDAY' in self.duration_rrule['rrule']:
            return False
        return self.rrule._dtstart + timedelta(days=365) == self.rrule._until

    # Properties describing the RRule typology

    @property
    def bounded(self):
        """Return True if the RRule has a specified UNTIL datetime, else
        return False.

        """
        return not self.unlimited

    @property
    def unlimited(self):
        """Whether the DurationRRule is bounded or not."""
        if self.duration_rrule.get('unlimited'):
            return True
        # if more than 12 month event
        if self.rrule._until and (self.end_datetime - self.start_datetime).days > 364:
            return True

        return self.rrule._until is None and self.rrule._count is None

    @property
    def is_continuous(self):
        """Whether the rrule is to be taken by intervals, or continuously."""
        return self.duration_rrule.get('continuous', False)

    @property
    def single_date(self):
        """Return True if the RRule describes a single date(time)."""
        return (
            self.rrule._count == 1 and
            self.duration <= ALL_DAY
        )

    @property
    def small_date_interval(self):
        """Return True if the RRule describes a date interval of less
        than 4 months and more than a day.

        """
        start_date, end_date = self.date_interval
        if not end_date:
            return False
        return 1 <= (end_date - start_date).days <= 4 * 30

    @property
    def long_date_interval(self):
        """Return True if the RRule describes a date interval of less
        than 8 months and than 4 months.

        """
        start_date, end_date = self.date_interval
        if not end_date:
            return False
        return 4 * 30 < (end_date - start_date).days <= 8 * 30

    @property
    def unlimited_date_interval(self):
        """Return True if the RRule describes a date interval of more
        than 8 months.

        """
        start_date, end_date = self.date_interval
        if not end_date:
            return False
        return (end_date - start_date).days > 8 * 30

    @property
    def has_timings(self):
        return (
            self.duration < ALL_DAY
        )
