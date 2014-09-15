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
from datection.normalize import MISSING_YEAR
from datection.normalize import DAY_START
from datection.normalize import DAY_END


class Timepoint(object):

    def __init__(self, span=(0, 0)):
        self.span = span

    @property
    def start_index(self):
        return self.span[0]

    @property
    def end_index(self):
        return self.span[1]

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        # weird hack that seems to prevent unexpected pyparsing error
        if not other:
            return False
        # end of hack
        if isinstance(other, Timepoint) and type(self) is not type(other):
            return False
        return True


class Date(Timepoint):

    """An object representing a date, more flexible than the
    datetime.date object, as it tolerates missing information.

    """

    def __init__(self, year, month, day, *args, **kwargs):
        super(Date, self).__init__(*args, **kwargs)
        self.year = year
        self.month = month
        self.day = day

    def __eq__(self, other):
        if not super(Date, self).__eq__(other):
            return False
        return (
            self.year == other.year
            and self.month == other.month
            and self.day == other.day)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (
            self.__class__.__name__,
            str(self.year) if self.year is not None else '?',
            str(self.month) if self.month is not None else '?',
            str(self.day)
        )

    @classmethod
    def from_match(self, match, *args, **kwargs):
        year = match['year'] if match['year'] else None
        month = match['month'] if match['month'] else None
        return Date(year, month, match['day'], *args, **kwargs)


class Time(Timepoint):

    """An object representing a time, more flexible than the
    datetime.time object, as it tolerates missing information.

    """

    def __init__(self, hour, minute, *args, **kwargs):
        super(Time, self).__init__(*args, **kwargs)
        self.hour = hour
        self.minute = minute

    def __repr__(self):
        return u'<%s %d:%s>' % (
            self.__class__.__name__,
            self.hour,
            str(self.minute).zfill(2))

    def __eq__(self, other):
        if not super(Time, self).__eq__(other):
            return False
        return (self.hour == other.hour and self.minute == other.minute)


class TimeInterval(Timepoint):

    def __init__(self, start_time, end_time, *args, **kwargs):
        super(TimeInterval, self).__init__(*args, **kwargs)
        self.start_time = start_time
        self.end_time = end_time

    def __iter__(self):
        yield self.start_time
        yield self.end_time

    def __repr__(self):
        return u'<%s %d:%s - %d:%s>' % (
            self.__class__.__name__,
            self.start_time.hour,
            str(self.start_time.minute).zfill(2),
            self.end_time.hour,
            str(self.end_time.minute).zfill(2))

    def __eq__(self, other):
        if not super(TimeInterval, self).__eq__(other):
            return False
        return (
            self.start_time == other.start_time and
            self.end_time == other.end_time)

    def is_single_time(self):
        return self.start_time == self.end_time


class DateList(Timepoint):

    def __init__(self, dates, *args, **kwargs):
        super(DateList, self).__init__(*args, **kwargs)
        self.dates = dates

    def __iter__(self):
        for _date in self.dates:
            yield _date

    @classmethod
    def from_match(cls, dates, *args, **kwargs):
        """Return a DateList instance constructed from a regex match result."""
        dates = cls.set_months(dates)
        dates = cls.set_years(dates)
        return DateList(dates, *args, **kwargs)

    @classmethod
    def set_years(cls, dates):
        """Make all dates without year inherit from the last date year."""
        last_date = dates[-1]
        if not last_date:
            raise ValueError('Last date must have a non nil year.')
        for _date in dates[:-1]:
            if not _date.year:
                _date.year = last_date.year
        return dates

    @classmethod
    def set_months(cls, dates):
        """Make all dates without month inherit from the last date month."""
        last_date = dates[-1]
        if not last_date:
            raise ValueError('Last date must have a non nil month.')
        for _date in dates[:-1]:
            if not _date.month:
                _date.month = last_date.month
        return dates

    def __eq__(self, other):
        if not super(DateList, self).__eq__(other):
            return False
        if isinstance(other, list):
            return self.dates == other
        return self.dates == other.dates


class DateInterval(Timepoint):

    def __init__(self, start_date, end_date, *args, **kwargs):
        super(DateInterval, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date

    def __eq__(self, other):
        if not super(DateInterval, self).__eq__(other):
            return False
        return (
            self.start_date == other.start_date
            and self.end_date == other.end_date)

    def __iter__(self):
        yield self.start_date
        yield self.end_date

    @classmethod
    def from_match(cls, start_date, end_date, *args, **kwargs):
        """Return a DateInterval instance constructed from a regex match
        result.

        """
        start_date = cls.set_start_date_year(start_date, end_date)
        start_date = cls.set_start_date_month(start_date, end_date)
        return DateInterval(start_date, end_date, *args, **kwargs)

    @classmethod
    def set_start_date_year(cls, start_date, end_date):
        """Make the start_date inherit from the end_date year, if needed."""
        if not end_date.year:
            raise ValueError("End date must have a year")
        if not start_date.year:
            start_date.year = end_date.year
        return start_date

    @classmethod
    def set_start_date_month(cls, start_date, end_date):
        """Make the start_date inherit from the end_date month, if needed."""
        if not end_date.month:
            raise ValueError("End date must have a month")
        if not start_date.month:
            start_date.month = end_date.month
        return start_date


class Datetime(Timepoint):

    """An object representing a datetime, more flexible than the
    datetime.datetime object, as it tolerates missing information.

    """

    def __init__(self, date, start_time, end_time=None, *args, **kwargs):
        super(Datetime, self).__init__(*args, **kwargs)
        self.date = date
        self.start_time = start_time
        if not end_time:
            self.end_time = start_time
        else:
            self.end_time = end_time

    def __eq__(self, other):
        if not super(Datetime, self).__eq__(other):
            return False
        return (
            self.date == other.date
            and self.start_time == other.start_time
            and self.end_time == other.end_time)

    def __repr__(self):
        return '<%s %d/%d/%d - %d:%s%s>' % (
            self.__class__.__name__,
            self.date.year,
            self.date.month,
            self.date.day,
            self.start_time.hour,
            str(self.start_time.minute).zfill(2),
            '-%s:%s' % (
                self.end_time.hour,
                str(self.end_time.minute).zfill(2)
            ) if self.start_time != self.end_time else '')

    @classmethod
    def combine(cls, date, start_time, end_time=None, *args, **kwargs):
        return Datetime(date, start_time, end_time, *args, **kwargs)


class DatetimeList(Timepoint):

    def __init__(self, datetimes, *args, **kwargs):
        super(DatetimeList, self).__init__(*args, **kwargs)
        self.datetimes = datetimes

    def __eq__(self, other):
        if isinstance(other, list):
            return self.datetimes == other
        return self.datetimes == other.datetimes

    @classmethod
    def from_match(cls, dates, time_interval, *args, **kwargs):
        st, et = time_interval
        datetimes = [Datetime.combine(date, st, et) for date in dates]
        return DatetimeList(datetimes, *args, **kwargs)


class DatetimeInterval(Timepoint):

    def __init__(self, date_interval, time_interval, *args, **kwargs):
        super(DatetimeInterval, self).__init__(*args, **kwargs)
        self.date_interval = date_interval
        self.time_interval = time_interval

    def __eq__(self, other):
        if not super(DatetimeInterval, self).__eq__(other):
            return False
        return (
            self.date_interval == other.date_interval
            and self.time_interval == other.time_interval)


class ContinuousDatetimeInterval(Timepoint):

    def __init__(
            self, start_date, start_time, end_date, end_time, *args, **kwargs):
        super(ContinuousDatetimeInterval, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.start_time = start_time
        self.end_date = end_date
        self.end_time = end_time

    def __eq__(self, other):
        if not super(ContinuousDatetimeInterval, self).__eq__(other):
            return False
        return (
            self.start_date == other.start_date
            and self.start_time == other.start_time
            and self.end_date == other.end_date
            and self.end_time == other.end_time)

    @classmethod
    def from_match(cls, start_date, start_time, end_date, end_time, *args, **kwargs):
        start_date = cls.set_month(start_date, end_date)
        start_date = cls.set_year(start_date, end_date)
        return ContinuousDatetimeInterval(
            start_date, start_time, end_date, end_time, *args, **kwargs)

    @classmethod
    def set_year(cls, start_date, end_date):
        if not end_date.year:
            raise ValueError("end date must have a year")
        if not start_date.year:
            start_date.year = end_date.year
        return start_date

    @classmethod
    def set_month(cls, start_date, end_date):
        if not end_date.month:
            raise ValueError("end date must have a month")
        if not start_date.month:
            start_date.month = end_date.month
        return start_date


class Weekdays(Timepoint):

    def __init__(self, days, *args, **kwargs):
        super(Weekdays, self).__init__(*args, **kwargs)
        self.days = days

    def __eq__(self, other):
        if not super(Weekdays, self).__eq__(other):
            return False
        if isinstance(other, list):
            return self.days == other
        return self.days == other.days


class WeeklyRecurrence(Timepoint):

    def __init__(self, date_interval, time_interval, weekdays, *args, **kwargs):
        super(WeeklyRecurrence, self).__init__(*args, **kwargs)
        self.date_interval = date_interval
        self.time_interval = time_interval
        self.weekdays = weekdays


class DurationRRule(object):

    """Wrapper around a rrule + duration object, providing handy properties
    to ease the manipulation of rrules.

    """

    def __init__(self, duration_rrule):
        self.duration_rrule = duration_rrule

    def __hash__(self):
        return hash(frozenset(self.duration_rrule.items()))

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
            for dtime in self.rrule:
                yield dtime
        else:
            end_bound_date = date.today() + timedelta(days=365)
            end_bound = datetime.combine(end_bound_date, DAY_END)
            for dtime in self.rrule:
                if dtime < end_bound:
                    yield dtime
                else:
                    raise StopIteration

    @cached_property
    def rrule(self):
        """Instanciate an rrule from the rrule string

        As this is a lazy property, the rrulestr -> rrule operation
        is only performed the first time.

        If the rrule defined weekly recurrence and has no 'until' date,
        one will be set automatically, to avoid infinite loops when
        iterating over the rrule dates.

        If an exclusion RRule is present, then it will be excluded from
        the 'rrule' one, using an rruleset.

        """
        if self.duration_rrule.get('exclusion'):
            rset = rruleset()
            rset.rrule(rrulestr(self.duration_rrule['rrule']))
            rset.exrule(rrulestr(self.duration_rrule['exclusion']))
            return rset
        return rrulestr(self.duration_rrule['rrule'])

    @property
    def duration(self):
        """The DurationRRule duration, in minutes (as an integer)."""
        return int(self.duration_rrule['duration'])

    @property
    def unlimited(self):
        """Whether the DurationRRule is bounded or not."""
        return self.duration_rrule.get('unlimited', False)

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
                    pass
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
