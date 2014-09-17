# -*- coding: utf-8 -*-

"""Definition of Timepoint classes."""

from datetime import timedelta
from datetime import datetime
from datetime import time
from datetime import date
from dateutil.rrule import rrulestr
from dateutil.rrule import rrule
from dateutil.rrule import WEEKLY

from datection.utils import get_current_date
from datection.utils import makerrulestr
from datection.utils import duration


ALL_DAY = 1439  # number of minutes from midnight to 23:59
MISSING_YEAR = 1000
DAY_START = time(0, 0)
DAY_END = time(23, 59, 59)


class Timepoint(object):

    """Base class of all timepoint classes."""

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        # weird hack that seems to prevent unexpected pyparsing error
        if not other:
            return False
        # end of hack
        if not isinstance(other, Timepoint):
            return False
        if type(self) is not type(other):
            return False
        return True


class Date(Timepoint):

    """An object representing a date, more flexible than the
    datetime.date object, as it tolerates missing information.

    """

    def __init__(self, year, month, day):
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
    def from_match(self, match):
        year = match['year'] if match['year'] else None
        month = match['month'] if match['month'] else None
        return Date(year, month, match['day'])

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a single Date """
        return makerrulestr(self.to_python(), count=1, byhour=0, byminute=0)

    @property
    def valid(self):
        return self.to_python() is not None

    def to_python(self):
        """Convert a Date object to a datetime.object"""
        try:
            return date(year=self.year, month=self.month, day=self.day)
        except TypeError:
            # Eg: if one of the attributes is None
            return None

    def export(self):
        """Return a dict containing the rrule and the duration (in min).

        """
        return {
            'rrule': self.rrulestr,
            'duration': ALL_DAY,
        }

    def future(self, reference=None):
        """Returns whether the Date is located in the future.

        If no reference is given, datetime.date.today() will be
        taken as reference.

        """
        reference = reference if reference is not None else get_current_date()
        return self.to_python() >= reference


class Time(Timepoint):

    """An object representing a time, more flexible than the
    datetime.time object, as it tolerates missing information.

    """

    def __init__(self, hour, minute):
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

    @property
    def valid(self):
        try:
            self.to_python()
        except ValueError:
            return False
        else:
            return True

    def to_python(self):
        return time(self.hour, self.minute)


class TimeInterval(Timepoint):

    def __init__(self, start_time, end_time):
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

    @property
    def valid(self):
        return self.start_time.valid and self.end_time.valid

    def is_single_time(self):
        return self.start_time == self.end_time


class DateList(Timepoint):

    def __init__(self, dates):
        self.dates = dates

    def __iter__(self):
        for _date in self.dates:
            yield _date

    def __eq__(self, other):
        if not super(DateList, self).__eq__(other):
            return False
        return self.dates == other.dates

    @classmethod
    def from_match(cls, dates):
        """Return a DateList instance constructed from a regex match result."""
        dates = cls.set_months(dates)
        dates = cls.set_years(dates)
        return DateList(dates)

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

    @property
    def valid(self):
        """ Check that all dates in self.dates are valid. """
        return all([_date.valid for _date in self.dates])

    def export(self):
        return [_date.export() for _date in self.dates]

    def to_python(self):
        """Convert self.dates to a list of datetime.date objects."""
        return [_date.to_python() for _date in self.dates]

    def future(self, reference=None):
        """Returns whether the DateList is located in the future.

        A DateList is considered future even if a part of its dates
        are future.

        If no reference is given, datetime.date.today() will be
        taken as reference.

        """
        reference = reference if reference is not None else get_current_date()
        return any([d.future(reference) for d in self.dates])


class DateInterval(Timepoint):

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.excluded = []

    def __eq__(self, other):
        if not super(DateInterval, self).__eq__(other):
            return False
        return (
            self.start_date == other.start_date
            and self.end_date == other.end_date)

    def __iter__(self):
        current = self.start_date.to_python()
        while current <= self.end_date.to_python():
            yield current
            current += timedelta(days=1)

    @classmethod
    def make_undefined(cls):
        return DateInterval(Date(1, 1, 1), Date(9999, 12, 31))

    @classmethod
    def from_match(cls, start_date, end_date):
        """Return a DateInterval instance constructed from a regex match
        result.

        """
        start_date = cls.set_start_date_year(start_date, end_date)
        start_date = cls.set_start_date_month(start_date, end_date)
        return DateInterval(start_date, end_date)

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

    @property
    def undefined(self):
        return self == DateInterval.make_undefined()

    @property
    def valid(self):
        """ Check that start and end date are valid. """
        if self.undefined:
            return False
        return all([self.start_date.valid, self.end_date.valid])

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a date interval """
        start = self.start_date.to_python()
        end = self.end_date.to_python()
        return makerrulestr(start, end, interval=1, byhour=0, byminute=0)

    def to_python(self):
        return [_date for _date in self]

    def export(self):
        """ Return a dict containing the recurrence rule and the duration
            (in min)

        """
        export = {
            'rrule': self.rrulestr,
            'duration': ALL_DAY,
        }
        if self.excluded:
            export['excluded'] = self.excluded
        return export

    def future(self, reference=None):
        """Returns whether the DateInterval is located in the future.

        A DateInterval is considered future if its end date is located
        in the future.

        If no reference is given, datetime.date.today() will be
        taken as reference.

        """
        reference = reference if reference is not None else get_current_date()
        return self.end_date.future(reference)


class Datetime(Timepoint):

    """An object representing a datetime, more flexible than the
    datetime.datetime object, as it tolerates missing information.

    """

    def __init__(self, date, start_time, end_time=None):
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
    def combine(cls, date, start_time, end_time=None):  # pragma: no cover
        return Datetime(date, start_time, end_time)

    @property
    def valid(self):
        """ Checks that both self.time and self.date are valid. """
        return self.date.valid and self.start_time.valid and self.end_time.valid

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a DateTime """
        start_date = self.date.to_python()
        return makerrulestr(
            start=start_date,
            count=1,
            byhour=self.start_time.hour,
            byminute=self.start_time.minute)

    def to_python(self):
        start_datetime = datetime.combine(
            self.date.to_python(), self.start_time.to_python())
        end_datetime = datetime.combine(
            self.date.to_python(), self.end_time.to_python())
        return (start_datetime, end_datetime)

    def export(self):
        """ Return a dict containing the recurrence rule and the duration
            (in min)

        """
        return {
            'rrule': self.rrulestr,
            'duration': duration(
                start=self.start_time,
                end=self.end_time),
        }

    def future(self, reference=None):
        """Return whether the datetime is located in the future.

        If no reference is given, datetime.date.today() will be
        taken as reference.

        """
        reference = reference if reference is not None else get_current_date()
        return self.date.future(reference)


class DatetimeList(Timepoint):

    def __init__(self, datetimes, *args, **kwargs):
        self.datetimes = datetimes

    def __eq__(self, other):
        if not super(DatetimeList, self).__eq__(other):
            return False
        return self.datetimes == other.datetimes

    def __getitem__(self, index):
        return self.datetimes[index]

    def __iter__(self):
        return iter(self.datetimes)

    @property
    def time_interval(self):
        return TimeInterval(self[0].start_time, self[0].end_time)

    @property
    def dates(self):
        return [dt.date for dt in self]

    @classmethod
    # pragma: no cover
    def from_match(cls, dates, time_interval, *args, **kwargs):
        st, et = time_interval
        datetimes = [Datetime.combine(date, st, et) for date in dates]
        return DatetimeList(datetimes, *args, **kwargs)

    def future(self, reference=None):
        """Returns whether the DateTimeList is located in the future.

        A DateTimeList is considered future even if a part of its
        datetimes are future.

        The default time reference is the day of the method execution.

        """
        reference = reference if reference is not None else get_current_date()
        return any([dt.date.future(reference) for dt in self.datetimes])

    @property
    def valid(self):
        """ Check the validity of each datetime in self.datetimes. """
        return all([dt.valid for dt in self.datetimes])

    def export(self):
        return [dt.export() for dt in self.datetimes]

    # def to_python(self):
    #     return [dt.to_python() for dt in self.datetimes]


class DatetimeInterval(Timepoint):

    def __init__(self, date_interval, time_interval):
        self.date_interval = date_interval
        self.time_interval = time_interval
        self.excluded = []

    def __eq__(self, other):
        if not super(DatetimeInterval, self).__eq__(other):
            return False
        return (
            self.date_interval == other.date_interval
            and self.time_interval == other.time_interval)

    @property
    def valid(self):
        return all([self.date_interval.valid, self.time_interval.valid])

    @property
    def rrulestr(self):
        start_time = self.time_interval.start_time.to_python()
        start_date = self.date_interval.start_date.to_python()
        end_date = self.date_interval.end_date.to_python()
        end = datetime.combine(end_date, DAY_END)
        return makerrulestr(
            start=start_date,
            end=end,
            interval=1,
            byhour=start_time.hour,
            byminute=start_time.minute)

    # def to_python(self):
    #     out = []
    #     start_date = self.date_interval.start_date.to_python()
    #     end_date = self.date_interval.end_date.to_python()
    #     delta = end_date - start_date
    #     start_time = self.time_interval.start_time.to_python()
    #     end_time = self.time_interval.end_time.to_python()

    #     for i in xrange(0, delta.days + 1):
    #         i_date = start_date + timedelta(days=i)
    #         i_start_datetime = datetime.combine(i_date, start_time)
    #         i_end_datetime = datetime.combine(i_date, end_time)
    #         out.append((i_start_datetime, i_end_datetime))
    #     return out

    def export(self):
        export = {
            'rrule': self.rrulestr,
            'duration': duration(
                start=self.time_interval.start_time,
                end=self.time_interval.end_time),
        }
        if self.excluded:
            export['excluded'] = self.excluded
        return export

    def future(self, reference=None):
        """Returns whether the DateTimeInterval is located in the future.

        A DateTimeInterval is considered future if its end date is located
        in the future.

        If no reference is given, datetime.date.today() will be
        taken as reference.

        """
        reference = reference if reference is not None else get_current_date()
        return self.date_interval.end_date.future(reference)


class ContinuousDatetimeInterval(Timepoint):

    def __init__(self, start_date, start_time, end_date, end_time):
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
    def from_match(
            cls, start_date, start_time, end_date, end_time):
        start_date = cls.set_month(start_date, end_date)
        start_date = cls.set_year(start_date, end_date)
        return ContinuousDatetimeInterval(
            start_date, start_time, end_date, end_time)

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

    @property
    def valid(self):
        return all([
            self.start_date.valid,
            self.end_date.valid,
            self.start_time.valid,
            self.end_time.valid
        ])

    def future(self, reference=None):
        reference = reference if reference is not None else get_current_date()
        end_datetime = Datetime.combine(self.end_date, self.end_time)
        return end_datetime.future(reference)

    @property
    def rrulestr(self):
        """Return the ContinuousDatetimeInterval RRule string."""
        end_dt = datetime.combine(self.end_date.to_python(),  DAY_END)
        return makerrulestr(
            start=self.start_date.to_python(),
            end=end_dt,
            interval=1,
            byhour=self.start_time.hour,
            byminute=self.start_time.minute)

    def export(self):
        """Export the ContinuousDatetimeInterval to a database-ready format."""
        start_datetime = datetime.combine(
            self.start_date.to_python(), self.start_time.to_python())
        end_datetime = datetime.combine(
            self.end_date.to_python(), self.end_time.to_python())
        return {
            'rrule': self.rrulestr,
            'duration': duration(start=start_datetime, end=end_datetime),
            'continuous': True,
        }

    # def to_python(self):
    # return (self.start_datetime.to_python(), self.end_datetime.to_python())


class Weekdays(Timepoint):

    def __init__(self, days, *args, **kwargs):
        self.days = days

    def __eq__(self, other):
        if not super(Weekdays, self).__eq__(other):
            return False
        return self.days == other.days


class WeeklyRecurrence(Timepoint):

    def __init__(self, date_interval, time_interval, weekdays):
        self.date_interval = date_interval
        self.time_interval = time_interval
        self.weekdays = weekdays
        self.excluded = []

    def __eq__(self, other):
        if not super(WeeklyRecurrence, self).__eq__(other):
            return False
        return (
            self.date_interval == other.date_interval and
            self.time_interval == other.time_interval and
            self.weekdays == other.weekdays)

    @property
    def rrulestr(self):
        """ Generate a full description of the recurrence rule"""
        end = datetime.combine(self.date_interval.end_date.to_python(), DAY_END)
        return makerrulestr(
            self.date_interval.start_date.to_python(),
            end=end,
            rule=self.to_python())

    @property
    def valid(self):
        return (
            len(self.weekdays) > 0 and
            self.date_interval.valid and
            self.time_interval.valid
        )

    def future(self, reference=None):
        return self.date_interval.future(reference)

    def to_python(self):
        return rrule(
            WEEKLY,
            byweekday=self.weekdays,
            byhour=self.time_interval.start_time.hour,
            byminute=self.time_interval.start_time.minute)

    def export(self):
        export = {
            'rrule': self.rrulestr,
            'duration': duration(
                start=self.time_interval.start_time,
                end=self.time_interval.end_time),
        }
        if self.date_interval.undefined:
            export['unlimited'] = True
        if self.excluded:
            export['excluded'] = self.excluded
        return export
