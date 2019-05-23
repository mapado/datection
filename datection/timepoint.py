# -*- coding: utf-8 -*-

"""Definition of Timepoint classes."""

from builtins import str
from builtins import range
from builtins import object
from datetime import timedelta
from datetime import datetime
from datetime import time
from datetime import date
from dateutil.rrule import rrule
from dateutil.rrule import rruleset
from dateutil.rrule import WEEKLY
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU
from operator import attrgetter
from copy import deepcopy

from datection.utils import get_current_date
from datection.utils import makerrulestr
from datection.utils import duration
from datection.utils import UNLIMITED_DATE_START
from datection.utils import UNLIMITED_DATE_END

ALL_DAY = 1439  # number of minutes from midnight to 23:59
MISSING_YEAR = 1000
DAY_START = time(0, 0)
DAY_END = time(23, 59, 59)
MIN_YEAR = 1970
ORDERED_DAYS = [MO, TU, WE, TH, FR, SA, SU]


class NormalizationError(Exception):
    pass


def add_span(f):
    """Add the instance span attribute to the export if the instance
    as a 'span' attribute.

    """
    def wrapper(*args, **kwargs):
        instance = args[0]
        export = f(*args, **kwargs)
        if hasattr(instance, 'span'):
            export['span'] = instance.span
        return export
    return wrapper


def transmit_span(f):
    """Transmit the instance 'span' attribute to every member of the instance
    export, it it possesses a 'span' attribute.

    """
    def wrapper(*args, **kwargs):
        instance = args[0]
        export = f(*args, **kwargs)
        if hasattr(instance, 'span'):
            for item in export:
                item['span'] = instance.span
        return export
    return wrapper


def has_no_timings(tp):
    """
    Function that checks if the given timepoint has some timings
    defined

    @param tp(Timepoint)

    @return: True if the timepoints no timings
    """
    if isinstance(tp, (Date, DateList, DateInterval)):
        return True

    if isinstance(tp, Datetime):
        return tp.duration == ALL_DAY

    if isinstance(tp, (DatetimeList, DatetimeInterval, WeeklyRecurrence)):
        return tp.time_interval.undefined

    return False


def has_timings(tp):
    """
    Function that checks if the given timepoint has some timings
    defined

    @param tp(Timepoint)

    @return: True if the timepoints has timings
    """
    return not has_no_timings(tp)


def enrich_with_timings(tp, timing):
    """
    Returns a new timepoint based on the given one and
    adds the given timing.

    @param tp(Timepoint)
    @param timing(TimeInterval)

    @return: new Timepoint with timings
    """
    if isinstance(tp, Date):
        return Datetime.from_match(tp, timing)

    elif isinstance(tp, DateList):
        return DatetimeList.from_match(tp, timing)

    elif isinstance(tp, DateInterval):
        return DatetimeInterval.from_match(tp, timing)

    elif isinstance(tp, (Datetime, DatetimeList,
                         DatetimeInterval, WeeklyRecurrence)):
        new_tp = deepcopy(tp)
        new_tp.set_time_interval(timing)
        return new_tp

    return tp


class YearDescriptor(object):

    """A descriptor of the year of a timepoint, whatever its class."""

    def __get__(self, instance, owner):
        """Get the year value on the correct object, depending on the instance
        instance class.

        """
        if isinstance(instance, (DateList, DatetimeList)):
            return instance.dates[-1].year
        elif isinstance(instance, (DateInterval, ContinuousDatetimeInterval)):
            return instance.end_date.year
        elif isinstance(instance, Datetime):
            return instance.date.year
        elif isinstance(instance, (DatetimeInterval, WeeklyRecurrence)):
            return instance.date_interval.end_date.year

    def set_date_interval_year(self, date_interval, year):
        """Set the year of the start_date and end_date of the date_interval."""
        date_interval.end_date.year = year
        if date_interval.start_date.month > date_interval.end_date.month:
            date_interval.start_date.year = year - 1
        else:
            date_interval.start_date.year = year

    def set_datelist_year(self, date_list, year):
        """Set the year of all the dates of the date_list."""
        for _date in date_list:
            _date.year = year

    def __set__(self, instance, value):
        """Set the year value on the correct object, depending on the instance
        instance class.

        """
        if isinstance(instance, (DateInterval, ContinuousDatetimeInterval)):
            self.set_date_interval_year(instance, value)
        elif isinstance(instance, (DateList, DatetimeList)):
            self.set_datelist_year(instance, value)
        elif isinstance(instance, Datetime):
            instance.date.year = value
        elif isinstance(instance, (DatetimeInterval, WeeklyRecurrence)):
            self.set_date_interval_year(instance.date_interval, value)


class AllowMissingYearDescriptor(object):

    """A descriptor handling the acceptance of timepoints with missing years."""

    def __init__(self, default):
        self.default = default

    def set_date_interval_allow_missing_year(self, date_interval, value):
        """Set the 'allow_missing_year' atribute of the date interval."""
        date_interval.start_date.allow_missing_year = value
        date_interval.end_date.allow_missing_year = value

    def __get__(self, instance, owner):
        """Set the allow_missing_year value on the correct object,
        depending on the instance instance class.

        """
        if isinstance(instance, (DateList, DatetimeList)):
            return all(d.allow_missing_year for d in instance)
        elif isinstance(instance, (DateInterval, ContinuousDatetimeInterval)):
            return all(
                d.allow_missing_year
                for d in (instance.start_date, instance.end_date))
        elif isinstance(instance, Datetime):
            return instance.date.allow_missing_year
        elif isinstance(instance, (DatetimeInterval, WeeklyRecurrence)):
            return instance.date_interval.allow_missing_year

    def __set__(self, instance, value):
        """Set the allow_missing_year value on the correct object,
        depending on the instance instance class.

        """
        if isinstance(instance, (DateInterval, ContinuousDatetimeInterval)):
            self.set_date_interval_allow_missing_year(instance, value)
        elif isinstance(instance, (DateList, DatetimeList)):
            for _date in instance:
                _date.allow_missing_year = value
        elif isinstance(instance, Datetime):
            instance.date.allow_missing_year = value
        elif isinstance(instance, (DatetimeInterval, WeeklyRecurrence)):
            self.set_date_interval_allow_missing_year(
                instance.date_interval, value)


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

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return u'<%s %s>' % (self.__class__.__name__, str(self))

    @property
    def duration(self):
        return 0


class AbstractDateInterval(Timepoint):

    """Abstract base class of all Timepoint classes describing a date
    interval.

    """
    pass


class AbstractDate(Timepoint):

    """Abstract base class of all Timepoint describing a single date."""
    pass


class Date(AbstractDate):

    """An object representing a date, more flexible than the
    datetime.date object, as it tolerates missing information.

    """

    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
        self.allow_missing_year = True

    def __eq__(self, other):
        if not super(Date, self).__eq__(other):
            return False
        return (
            self.year == other.year
            and self.month == other.month
            and self.day == other.day)

    def __hash__(self):
        return hash((self.year, self.month, self.day))

    def __repr__(self):  # pragma: no cover
        return u'%s/%s/%s' % (
            str(self.year).zfill(4) if self.year is not None else '?',
            str(self.month).zfill(2) if self.month is not None else '?',
            str(self.day).zfill(2)
        ) 

    def __lt__(self, other):
        return self.to_python() < other.to_python()

    @classmethod
    def from_match(self, match):  # pragma: no cover
        year = match['year'] if match['year'] else None
        month = match['month'] if match['month'] else None
        return Date(year, month, match['day'])

    @classmethod
    def from_date(self, date):
        return Date(date.year, date.month, date.day)

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a single Date """
        return makerrulestr(self.to_python(), count=1, byhour=0, byminute=0)

    @property
    def valid(self):
        return self.to_python() is not None

    @property
    def duration(self):
        return ALL_DAY

    def to_python(self):
        """Convert a Date object to a datetime.object"""
        try:
            return date(year=self.year, month=self.month, day=self.day)
        except (TypeError, ValueError):
            if self.allow_missing_year:
                # Try again with the minimum year possible
                try:
                    return date(year=MIN_YEAR, month=self.month, day=self.day)
                except (TypeError, ValueError):
                    # Eg: either the month or the day is None or out of bounds
                    return None

    def day_of_week(self):
        """
        Returns the day of week
        """
        return self.to_python().weekday()

    @add_span
    def export(self):
        """Return a dict containing the rrule and the duration (in min).

        """
        return {
            'rrule': self.rrulestr,
            'duration': self.duration,
        }

    def future(self, reference=None):
        """Returns whether the Date is located in the future.

        If no reference is given, datetime.date.today() will be
        taken as reference.

        """
        reference = reference if reference is not None else get_current_date()
        return (self.to_python() >= reference)


class Time(Timepoint):

    """An object representing a time, more flexible than the
    datetime.time object, as it tolerates missing information.

    """

    def __init__(self, hour, minute):
        self.hour = hour
        self.minute = minute

    def __repr__(self):  # pragma: no cover
        return u'<%s %d:%s>' % (
            self.__class__.__name__,
            self.hour,
            str(self.minute).zfill(2))

    def __eq__(self, other):
        if not super(Time, self).__eq__(other):
            return False
        return (self.hour == other.hour and self.minute == other.minute)

    def __lt__(self, other):
        return self.to_python < other.to_python()

    def __hash__(self):
        return hash((self.hour, self.minute))

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
        return u'%d:%s - %d:%s' % (
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

    def __lt__(self, other):
        return self.start_time < other.start_time

    def __hash__(self):
        return hash((self.start_time, self.end_time))

    @classmethod
    def make_all_day(self):
        return TimeInterval(Time(0, 0), Time(23, 59))

    @property
    def valid(self):
        return self.start_time.valid and self.end_time.valid

    @property
    def undefined(self):
        return self == TimeInterval.make_all_day()

    def is_single_time(self):
        return self.start_time == self.end_time


class DateList(Timepoint):

    year = YearDescriptor()
    allow_missing_year = AllowMissingYearDescriptor(True)

    def __init__(self, dates):
        self.dates = dates

    def __iter__(self):
        for _date in self.dates:
            yield _date

    def __eq__(self, other):
        if not super(DateList, self).__eq__(other):
            return False
        return self.dates == other.dates

    def __lt__(self, other):
        return min(self.dates) < min(other.dates)

    def __hash__(self):
        return hash(tuple(self.dates))

    def __repr__(self):
        return object.__repr__(self)

    @classmethod
    def from_match(cls, dates):
        """Return a DateList instance constructed from a regex match result."""
        dates = cls.set_months(dates)
        dates = cls.set_years(dates)
        return DateList(dates)

    @staticmethod
    def set_years(dates):
        """Make all dates without year inherit from the last date year."""
        last_date = dates[-1]
        for _date in dates[:-1]:
            if not _date.year:
                if _date.month > last_date.month:
                    _date.year = last_date.year - 1
                else:
                    _date.year = last_date.year
        return dates

    @staticmethod
    def set_months(dates):
        """Make all dates without month inherit from the last date month."""
        last_date = dates[-1]
        if not last_date.month:
            raise NormalizationError('Last date must have a non nil month.')
        for _date in dates[:-1]:
            if not _date.month:
                _date.month = last_date.month
        return dates

    @property
    def valid(self):
        """ Check that all dates in self.dates are valid. """
        return all([_date.valid for _date in self.dates])

    @transmit_span
    def export(self):
        return [_date.export() for _date in self.dates]

    def contiguous_groups(self):
        """Group contiguous dates together."""
        def consecutive(date1, date2):
            return date1.to_python() + timedelta(days=1) == date2.to_python()

        contiguous_groups = [[self.dates[0]], ]
        group_index = 0
        previous_date = self.dates[0]
        for current_date in self.dates[1:]:
            if not consecutive(previous_date, current_date):
                group_index += 1
                contiguous_groups.append([])
            contiguous_groups[group_index].append(current_date)
            previous_date = current_date
        return contiguous_groups

    def contiguous_dates(self):
        """Return True if all the dates in ther interval are continuous.

        """
        return len(self.contiguous_groups()) == 1

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


class DateInterval(AbstractDateInterval):

    year = YearDescriptor()
    allow_missing_year = AllowMissingYearDescriptor(True)

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

    def __lt__(self, other):
        return self.start_date < other.start_date

    def __hash__(self):
        return hash((self.start_date, self.end_date))

    def __iter__(self):
        current = self.start_date.to_python()
        while current <= self.end_date.to_python():
            yield current
            current += timedelta(days=1)

    def __repr__(self):
        return u'%s - %s%s' % (
            str(self.start_date),
            str(self.end_date),
            str("" if not self.excluded
                    else " { EXCLUDED: " + str(self.excluded) + "}")
        )

    @classmethod
    def make_undefined(cls):
        start = Date.from_date(UNLIMITED_DATE_START)
        end = Date.from_date(UNLIMITED_DATE_END)

        return DateInterval(start, end)

    @classmethod
    def from_match(cls, start_date, end_date):
        """Return a DateInterval instance constructed from a regex match
        result.

        """
        start_date = cls.set_start_date_year(start_date, end_date)
        start_date = cls.set_start_date_month(start_date, end_date)
        return DateInterval(start_date, end_date)

    @staticmethod
    def set_start_date_year(start_date, end_date):
        """Make the start_date inherit from the end_date year, if needed."""
        if not end_date.year:
            return start_date
        if not start_date.year:
            if not end_date.month:
                start_date.year = end_date.year - 1
            elif not start_date.month:
                start_date.year = end_date.year
            elif start_date.month > end_date.month:
                start_date.year = end_date.year - 1
            else:
                start_date.year = end_date.year
        return start_date

    @staticmethod
    def set_start_date_month(start_date, end_date):
        """Make the start_date inherit from the end_date month, if needed."""
        if not end_date.month:
            raise NormalizationError("End date must have a month")
        if not start_date.month:
            start_date.month = end_date.month
        return start_date

    @property
    def undefined(self):
        return self == DateInterval.make_undefined()

    @property
    def valid(self):
        """ Check that start and end date are valid. """
        return all([self.start_date.valid, self.end_date.valid])

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a date interval """
        start = self.start_date.to_python()
        end = self.end_date.to_python()
        return makerrulestr(start, end, interval=1, byhour=0, byminute=0)

    @property
    def duration(self):
        return ALL_DAY

    def length(self):
        """ Date range length """
        return (self.end_date.to_python() - self.start_date.to_python())

    def to_python(self):
        return [_date for _date in self]

    @add_span
    def export(self):
        """ Return a dict containing the recurrence rule and the duration
            (in min)

        """
        export = {
            'rrule': self.rrulestr,
            'duration': self.duration,
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


class Datetime(AbstractDate):

    """An object representing a datetime, more flexible than the
    datetime.datetime object, as it tolerates missing information.

    """

    year = YearDescriptor()
    allow_missing_year = AllowMissingYearDescriptor(True)

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

    def __lt__(self, other):
        return self.to_python() < other.to_python()

    def __hash__(self):
        return hash((self.date, self.start_time, self.end_time))

    def __repr__(self):
        return u'%s - %d:%s%s' % (
            str(self.date),
            self.start_time.hour,
            str(self.start_time.minute).zfill(2),
            '-%s:%s' % (
                self.end_time.hour,
                str(self.end_time.minute).zfill(2)
            ) if self.start_time != self.end_time else '')

    def set_time_interval(self, time_interval):
        """ Sets the time interval """
        self.start_time = time_interval.start_time
        if not time_interval.end_time:
            self.end_time = self.start_time
        else:
            self.end_time = time_interval.end_time

    @classmethod
    def from_match(cls, date, timing):
        """
        Creates a Datetime from a Date and a TimeInterval
        """
        return cls(date, timing.start_time, timing.end_time)

    @classmethod
    def combine(cls, date, start_time, end_time=None):
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

    @property
    def duration(self):
        return duration(start=self.start_time,
                        end=self.end_time)

    @add_span
    def export(self):
        """ Return a dict containing the recurrence rule and the duration
            (in min)

        """
        return {
            'rrule': self.rrulestr,
            'duration': self.duration,
        }

    def future(self, reference=None):
        """Return whether the datetime is located in the future.

        If no reference is given, datetime.date.today() will be
        taken as reference.

        """
        reference = reference if reference is not None else get_current_date()
        return self.date.future(reference)

    def to_python(self):
        try:
            return datetime(
                self.date.year,
                self.date.month,
                self.date.day,
                self.start_time.hour,
                self.start_time.minute)
        except (TypeError, ValueError):
            try:
                return datetime(
                    MIN_YEAR,
                    self.date.month,
                    self.date.day,
                    self.start_time.hour,
                    self.start_time.minute)
            except (TypeError, ValueError):
                return None

    def day_of_week(self):
        """
        Returns the day of week
        """
        return self.to_python().weekday()


class DatetimeList(Timepoint):

    year = YearDescriptor()
    allow_missing_year = AllowMissingYearDescriptor(True)

    def __init__(self, datetimes, *args, **kwargs):
        self.datetimes = datetimes

    def __eq__(self, other):
        if not super(DatetimeList, self).__eq__(other):
            return False
        return self.datetimes == other.datetimes

    def __lt__(self, other):
        return min(self.datetimes) < min(other.datetimes)

    def __hash__(self):
        return hash(tuple(self.datetimes))

    def __getitem__(self, index):
        return self.datetimes[index]

    def __iter__(self):
        return iter(self.datetimes)

    def __repr__(self):
        return object.__repr__(self)

    def set_time_interval(self, time_interval):
        """ Sets the time interval """
        for datetime in self.datetimes:
            datetime.set_time_interval(time_interval)

    @classmethod
    # pragma: no cover
    def from_match(cls, dates, time_interval, *args, **kwargs):
        st, et = time_interval
        datetimes = [Datetime.combine(date, st, et) for date in dates]
        return DatetimeList(datetimes, *args, **kwargs)

    @property
    def time_interval(self):
        return TimeInterval(self[0].start_time, self[0].end_time)

    @property
    def dates(self):
        return [dt.date for dt in self]

    def future(self, reference=None):
        """Returns whether the DateTimeList is located in the future.

        A DateTimeList is considered future even if a part of its
        datetimes are future.

        """
        reference = reference if reference is not None else get_current_date()
        return any([dt.date.future(reference) for dt in self.datetimes])

    @property
    def valid(self):
        """ Check the validity of each datetime in self.datetimes. """
        return all([dt.valid for dt in self.datetimes])

    @transmit_span
    def export(self):
        return [dt.export() for dt in self.datetimes]


class DatetimeInterval(AbstractDateInterval):

    year = YearDescriptor()
    allow_missing_year = AllowMissingYearDescriptor(True)

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

    def __lt__(self, other):
        if self.date_interval < other.date_interval:
            return True
        elif self.date_interval == other.date_interval:
            if self.time_interval < other.time_interval:
                return True
        return False


    def __hash__(self):
        return hash((self.date_interval, self.time_interval))

    def __repr__(self):
        return u'<%s (%s) (%s)%s>' % (
            str(self.__class__.__name__),
            str(self.date_interval),
            str(self.time_interval),
            str("" if not self.excluded
                    else " { EXCLUDED: " + str(self.excluded) + "}"),
        )

    def __iter__(self):
        current = self.date_interval.start_date.to_python()
        while current <= self.date_interval.end_date.to_python():
            yield current
            current += timedelta(days=1)

    def set_time_interval(self, time_interval):
        """ Sets the time interval """
        self.time_interval = time_interval

    @classmethod
    def from_match(cls, date_interval, time_interval):
        """
        Creates a DatetimeInterval from a DateInterval and a TimeInterval
        """
        datetime_interval = cls(date_interval, time_interval)
        datetime_interval.excluded = date_interval.excluded
        return datetime_interval

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

    @property
    def duration(self):
        return duration(start=self.time_interval.start_time,
                        end=self.time_interval.end_time)

    @add_span
    def export(self):
        export = {
            'rrule': self.rrulestr,
            'duration': self.duration,
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

    def to_python(self):
        return [_date for _date in self]


class ContinuousDatetimeInterval(Timepoint):

    year = YearDescriptor()
    allow_missing_year = AllowMissingYearDescriptor(True)

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

    def __lt__(self, other):
        if self.start_date < other.start_date:
            return True
        elif self.start_date == other.start_date:
            if self.start_time < other.start_time:
                return True
        return False

    def __hash__(self):
        return hash((self.start_date, self.start_time, self.end_date, self.end_time))

    def __repr__(self):
        return object.__repr__(self)

    @classmethod
    def from_match(
            cls, start_date, start_time, end_date, end_time):
        start_date = cls.set_month(start_date, end_date)
        start_date = cls.set_year(start_date, end_date)
        return ContinuousDatetimeInterval(
            start_date, start_time, end_date, end_time)

    @staticmethod
    def set_year(start_date, end_date):
        if not end_date.year:
            raise NormalizationError("end date must have a year")
        if not start_date.year:
            start_date.year = end_date.year
        return start_date

    @staticmethod
    def set_month(start_date, end_date):
        if not end_date.month:
            raise NormalizationError("end date must have a month")
        if not start_date.month:
            start_date.month = end_date.month
        return start_date

    @property
    def valid(self):
        sdt = Datetime.combine(self.start_date, self.start_time).to_python()
        edt = Datetime.combine(self.end_date, self.end_time).to_python()
        if (sdt > edt):
            return False
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
            count=1,
            byhour=self.start_time.hour,
            byminute=self.start_time.minute)

    @property
    def duration(self):
        start_datetime = datetime.combine(
            self.start_date.to_python(), self.start_time.to_python())
        end_datetime = datetime.combine(
            self.end_date.to_python(), self.end_time.to_python())
        return duration(start=start_datetime,
                        end=end_datetime)

    @add_span
    def export(self):
        """Export the ContinuousDatetimeInterval to a database-ready format."""
        return {
            'rrule': self.rrulestr,
            'duration': self.duration
        }


class Weekdays(Timepoint):

    def __init__(self, days, *args, **kwargs):
        self.days = [d for d in ORDERED_DAYS if d in days]

    def __eq__(self, other):
        if not super(Weekdays, self).__eq__(other):
            return False
        return sorted(str(d) for d in self.days) == sorted(str(d) for d in other.days)

    def __lt__(self, other):
        return min(self.days) < min(other.days)

    def __hash__(self):
        return hash(sorted(self.days))

    def __len__(self):
        return len(self.days)

    def __iter__(self):
        return iter(self.days)

    def __repr__(self):
        if self.all_week:
            return 'ALL_WEEK'
        else:
            return u', '.join(str(w) for w in self.days)

    @property
    def all_week(self):
        return [w.weekday for w in self.days] == list(range(0, 7))


class WeeklyRecurrence(Timepoint):

    year = YearDescriptor()
    allow_missing_year = AllowMissingYearDescriptor(True)

    def __init__(self, date_interval, time_interval, weekdays):
        self.date_interval = date_interval
        self.time_interval = time_interval
        self.weekdays = [d for d in ORDERED_DAYS if d in weekdays]
        self.excluded = []

    def __eq__(self, other):
        if not super(WeeklyRecurrence, self).__eq__(other):
            return False
        return (
            self.date_interval == other.date_interval and
            self.time_interval == other.time_interval and
            self.weekdays == other.weekdays)

    def __lt__(self, other):
        first_self = next(iter(self.to_python()))
        first_other = next(iter(other.to_python()))
        if first_self and first_other:
            return first_self < first_other
        return False

    def __hash__(self):
        return hash((self.date_interval, self.time_interval, (str(d) for d in self.weekdays)))

    def __repr__(self):
        return u'<%s - (%s) (%s) (%s)%s>' % (
            self.__class__.__name__,
            str(self.date_interval),
            str(self.weekdays),
            str(self.time_interval),
            str("" if not self.excluded
                    else " { EXCLUDED: " + str(self.excluded) + "}"),
        )

    @classmethod
    def make_undefined(cls, time_interval):
        """
        Creates a unbounded, every day, WeeklyRecurrence based
        on the given TimeInterval
        """
        date_interval = DateInterval.make_undefined()
        weekdays = ORDERED_DAYS
        return cls(date_interval, time_interval, weekdays)

    def set_time_interval(self, time_interval):
        """ Sets the time interval """
        self.time_interval = time_interval

    @property
    def rrulestr(self):
        """ Generate a full description of the recurrence rule"""
        end = datetime.combine(
            self.date_interval.end_date.to_python(), DAY_END)
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

    @property
    def duration(self):
        return duration(start=self.time_interval.start_time,
                        end=self.time_interval.end_time)

    @add_span
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

        self.weekdays = sorted(self.weekdays, key=attrgetter('weekday'))

        return export
