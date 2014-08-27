# -*- coding: utf-8 -*-

"""
Normalization tools converting date-related regex matches into pure
python objects (date, time, datetime, rrule, etc), supporting a
conversion into a NoSQL database ready format.

"""

import re
from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta

from dateutil.rrule import rrule, WEEKLY
from datection.regex import WEEKDAY
from datection.regex import TIMEPOINT_REGEX
from datection.regex import MONTH
from datection.regex import SHORT_MONTH
from datection.utils import makerrulestr
from datection.utils import normalize_2digit_year
from datection.utils import digit_to_int
from datection.utils import duration


ALL_DAY = 1439  # number of minutes from midnight to 23:59
MISSING_YEAR = 1000
DAY_START = time(0, 0)
DAY_END = time(23, 59, 59)


def timepoint_factory(detector, lang, data, **kwargs):
    """ Return an instance of the appropriate Timepoint child class
        given the detector value.

    """
    factory = {
        'date': Date,
        'date_interval': DateInterval,
        'time_interval': TimeInterval,
        'datetime': DateTime,
        'date_list': DateList,
        'datetime_list': DateTimeList,
        'datetime_interval': DateTimeInterval,
        'continuous_datetime_interval': ContinuousDatetimeInterval,
        'weekday_recurrence': WeekdayRecurrence,
        'weekday_interval_recurrence': WeekdayIntervalRecurrence,
        'allweekday_recurrence': AllWeekdayRecurrence,
    }
    if detector not in factory:
        raise NotImplementedError(
            detector + " normalisation is not yet handled.")
    return factory[detector]._from_groupdict(data, lang, ** kwargs)


class Timepoint(object):

    """ The mother class for all timepoint classes. """

    def __init__(self, lang=None, span=None):
        self.lang = lang
        self.span = span

    def __eq__(self, other):
        return self.to_python() == other.to_python()

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(str(self.to_python()))

    def to_python(self):
        """Converts the Timepoint instance to a pure python value."""
        return None

    def future(self, reference=None):
        """Return whether the timepoint is located in the future."""
        return False


class Date(Timepoint):

    """Date normalizer, in charge of normalizing date regex matches."""

    def __init__(self, year, month, day, **kwargs):
        super(Date, self).__init__(**kwargs)
        self.year = year
        self.month = month
        self.day = day

    def __repr__(self):
        return '<{cls}: {d}/{m}/{y}>'.format(cls=self.__class__.__name__,
                                             d=self.day, m=self.month,
                                             y=self.year)

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        """Create a Date instance from a regex match groupdict."""
        year = cls._set_year(groupdict.get('year'))
        month = cls._set_month(groupdict['month'], lang)
        day = cls._set_day(groupdict.get('day'))
        return Date(year=year, month=month, day=day, lang=lang, **kwargs)

    @classmethod
    def _set_year(cls, year):
        """ Set and normalise the date year

        If year is None (missing year), return 1.
        Else, if the year is numeric but only 2 digit long, we guess in
        which century it is (ex: dd/mm/13 -> 1913, 2013, etc ?)
        Else, make sure the year is an int

        """
        if not year:
        # if year is not given, set year as 1, as a marker of missing year
            return MISSING_YEAR

        # Case of a numeric date with short year format
        if len(str(year)) == 2:
            return normalize_2digit_year(year)
        else:
            return int(year)

    @classmethod
    def _set_month(cls, month, lang):
        """Return the month number from the month name

        If the month is an integer, or a digit string, return its int
        version.
        The month name can be abbreviated or whole.

        """
        if not month:
            return
        if isinstance(month, int):
            return month
        elif month.isdigit():
            return int(month)

        # if month name is abbreviated
        month = month.rstrip('.').lower()
        if month in SHORT_MONTH[lang]:
            return SHORT_MONTH[lang][month]
        return MONTH[lang][month]

    @classmethod
    def _set_day(cls, day):
        """Return the integer value of day, except if day is None."""
        if not day:
            return None
        return int(day)

    @property
    def valid(self):
        """If the generated datetime.date is valid, return True, else False.

        """
        if all([self.year, self.month, self.day]):
            try:  # check if date is valid
                date(year=self.year, month=self.month, day=self.day)
            except ValueError:
                return False
            else:
                return True
        else:
            return False

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a single Date """
        start = self.to_python()
        return makerrulestr(start, count=1, byhour=0, byminute=0)

    def to_python(self):
        """Convert a Date object to a datetime.object"""
        try:
            return date(year=self.year, month=self.month, day=self.day)
        except TypeError:
            # Eg: if one of the attributes is None
            return None

    def to_db(self):
        """ Return a dict containing the recurrence rule, the duration
            (in min), and the matching text.

        """
        return {
            'rrule': self.rrulestr,
            'duration': ALL_DAY,  # 23 hours 59 minutes
            'span': self.span
        }

    def future(self, reference=date.today()):
        """Returns whether the Date is located in the future.

        The default time reference is the day of the method execution.

        """
        return self.to_python() >= reference


class DateList(Timepoint):

    """Date list normalizer in charge of normalizing date list regex matches"""

    def __init__(self, dates, **kwargs):
        """ Initialize the DateList object. """
        super(DateList, self).__init__(**kwargs)
        self.dates = dates

    def __iter__(self):
        """Iterate over the list of dates"""
        for _date in self.dates:
            yield _date

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        """Instanciate a DateList from a regex match groupdict."""
        groupdict = digit_to_int(groupdict)
        span = kwargs['span']
        dates = cls._set_dates(groupdict, lang, span)

        # make the dates without a year inherit from the one which does
        # if needed
        dates = cls._set_year(dates)

        # make the dates without a month inherit from the one which does
        # if needed
        dates = cls._set_month(dates)
        return DateList(dates, **kwargs)

    @classmethod
    def _set_dates(cls, groupdict, lang, span):
        """Normalize the dates and return a list of Date objects."""
        dates = []
        for match in re.finditer(TIMEPOINT_REGEX[lang]['_date_in_list'][0],
                                 groupdict['date_list']):
            groupdict = match.groupdict()
            if not groupdict['year']:
                groupdict['year'] = MISSING_YEAR
            _date = Date._from_groupdict(groupdict, lang=lang, span=span)
            dates.append(_date)
        return dates

    @staticmethod
    def _set_year(dates):
        """ All dates without a year will inherit from the end date year """
        # Assign MISSING_YEAR to year, if year is None
        # It will be a marker allowing the year to be replaced
        # by the same value as the last year of the list
        # Ex: 2, 3 & 5 juin 2013 → 2/06/13, 3/06/13 & 5/06/13
        end_date = dates[-1]
        if end_date.year:
            for _date in dates[:-1]:
                if _date.year == MISSING_YEAR:
                    _date.year = end_date.year
        return dates

    @staticmethod
    def _set_month(dates):
        """ All dates without a month will inherit from the end date month """
        end_date = dates[-1]
        if end_date.month:
            for _date in dates[:-1]:
                if not _date.month:
                    _date.month = end_date.month
        return dates

    @property
    def valid(self):
        """ Check that all dates in self.dates are valid. """
        return all([_date.valid for _date in self.dates])

    def to_python(self):
        """Convert self.dates to a list of datetime.date objects."""
        return [_date.to_python() for _date in self.dates]

    def to_db(self):
        """Convert self.dates to a list of duration rrules."""
        return [_date.to_db() for _date in self.dates]

    def future(self, reference=date.today()):
        """Returns whether the DateList is located in the future.

        A DateList is considered future even if a part of its dates
        are future.

        The default time reference is the day of the method execution.

        """
        return any([d.future(reference) for d in self.dates])


class DateInterval(Timepoint):

    """Date normalizer, in charge of normalizing date interval regex matches.

    """

    def __init__(self, start_date, end_date, **kwargs):
        super(DateInterval, self).__init__(**kwargs)
        self.start_date = start_date
        self.end_date = end_date

    def __iter__(self):
        """ Iteration through the self.dates list. """
        for _date in [self.start_date, self.end_date]:
            yield _date

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        start_date, end_date = cls._set_dates(groupdict, lang)
        return DateInterval(start_date, end_date, **kwargs)

    @classmethod
    def _set_dates(cls, groupdict, lang):
        """ Restore all missing groupdict and serialize the start and end date """
        # start date inherits from end month name if necessary
        if (not groupdict.get('start_month')
            and groupdict.get('end_month')):
            groupdict['start_month'] = groupdict['end_month']

        if not groupdict.get('start_year') and groupdict.get('end_year'):
            groupdict['start_year'] = groupdict['end_year']
        elif not (groupdict.get('start_year') or groupdict.get('end_year')):
            groupdict['start_year'] = MISSING_YEAR
            groupdict['end_year'] = groupdict['start_year']

        # Create normalised start date of Date type
        start_date_groupdict = {
            'day': groupdict['start_day'],
            'month': groupdict['start_month'],
            'year': groupdict['start_year']
        }
        start_date = Date._from_groupdict(start_date_groupdict, lang=lang)

        # create normalized end date of Date type
        end_date_groupdict = {
            'day': groupdict['end_day'],
            'month': groupdict['end_month'],
            'year': groupdict['end_year']
        }
        end_date = Date._from_groupdict(end_date_groupdict, lang=lang)

        # warning, if end month occurs before start month, then end month
        # is next year
        if end_date.month < start_date.month:

            # standard case: the end year is well known
            if end_date.year != MISSING_YEAR:
                if start_date.year == end_date.year:
                    start_date.year -= 1
                elif not groupdict['end_year']:
                    end_date.year += 1

            # weird case: the end year is unknown and after greater than
            # the (still unknown start year). In this case, the end year
            # will be 2 and the start year will be 1.
            else:
                start_date.year = MISSING_YEAR
                end_date.year = MISSING_YEAR + 1

        return start_date, end_date

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

    def to_python(self):
        return [_date.to_python() for _date in self]

    def to_db(self):
        """ Return a dict containing the recurrence rule and the duration
            (in min)

        """
        return {
            'rrule': self.rrulestr,
            'duration': ALL_DAY,
            'span': self.span
        }

    def future(self, reference=date.today()):
        """Returns whether the DateInterval is located in the future.

        A DateInterval is considered future if its end date is located
        in the future.

        The default time reference is the day of the method execution.

        """
        return self.end_date.future(reference)


class Time(Timepoint):

    """Time normalizer, in charge of normalizing the time regex matches."""

    def __init__(self, hour, minute, **kwargs):
        super(Time, self).__init__(**kwargs)
        self.hour = hour
        self.minute = minute

    @classmethod
    def _from_groupdict(cls, groupdict, **kwargs):
        groupdict = digit_to_int(groupdict)
        minute = groupdict['minute'] if groupdict.get('minute') else 0
        hour = groupdict['hour']
        return Time(hour, minute, **kwargs)

    @property
    def valid(self):
        """ Return whether the time is valid or not.

        The validity of the date is checked by trying to instanciate
        a datetime.date object.

        """
        if self.hour is not None and self.minute is not None:
            try:  # check if time is valid
                time(self.hour, self.minute)
            except ValueError:
                return False
            else:
                return True
        else:
            return False

    def to_python(self):
        """Convert a Time object to a datetime.time object."""
        if not self.valid:
            return None
        return time(hour=int(self.hour), minute=int(self.minute))

    def to_db(self):
        return None


class TimeInterval(Timepoint):

    """Time interval normalizer, in charge of normalizing time interval regex
    matches.

    """

    def __init__(self, start_time, end_time=None, **kwargs):
        super(TimeInterval, self).__init__(**kwargs)
        self.start_time = start_time
        self.end_time = end_time

    def __iter__(self):
        """ Iteration over the start and end time. """
        for _time in [self.start_time, self.end_time]:
            yield _time

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        start_time = cls._set_start_time(groupdict.get('start_time'), lang)
        end_time = cls._set_end_time(groupdict.get('end_time'), lang)
        return TimeInterval(start_time, end_time, **kwargs)

    @classmethod
    def _set_start_time(cls, start_time_text, lang):
        """ Normalize the start time into a Time object """
        if not start_time_text:
            return None
        match = re.search(TIMEPOINT_REGEX[lang]['_time'][0], start_time_text)
        return Time._from_groupdict(match.groupdict(), lang=lang)

    @classmethod
    def _set_end_time(cls, end_time_text,  lang):
        """ Normalize the end time into a Time object """
        # normalization of self.end_time into a Time object
        if not end_time_text:
            return None
        match = re.search(TIMEPOINT_REGEX[lang]['_time'][0], end_time_text)
        return Time._from_groupdict(match.groupdict(), lang=lang)

    @property
    def valid(self):
        """ Check that both self.start_time and self.end_time (if any)
        are valid.

        """
        if self.end_time:
            return all([self.start_time.valid, self.end_time.valid])
        else:
            return self.start_time.valid

    def to_python(self):
        """Return either a tuple (start_time, end_time), or simply start_time
        if self.end_time is null, as datetime.time objects.

        """
        if self.end_time:
            return (self.start_time.to_python(), self.end_time.to_python())
        else:
            return self.start_time.to_python()

    def to_db(self):
        return None


class DateTime(Timepoint):

    """Datetime normalizer, in charge of normalizing datetime regex matches."""

    def __init__(self, date, time, **kwargs):
        super(DateTime, self).__init__(**kwargs)
        self.date = date
        self.time = time

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        date = cls._set_date(groupdict, lang)
        time = cls._set_time(groupdict, lang)
        return DateTime(date, time, **kwargs)

    @classmethod
    def _set_date(cls, groupdict, lang):
        """Set the datetime date, as a Date object."""
        year = groupdict.get('year') or MISSING_YEAR
        month = groupdict.get('month')
        day = groupdict.get('day')
        date_groupdict = {'day': day, 'month': month, 'year': year}
        return Date._from_groupdict(date_groupdict, lang=lang)

    @classmethod
    def _set_time(cls, groupdict, lang):
        """Set the datetime time, as a TimeInterval object."""
        start_time = groupdict.get('start_time')
        end_time = groupdict.get('end_time')
        st_match = re.search(
            TIMEPOINT_REGEX[lang]['_time'][0], start_time)
        st = Time._from_groupdict(st_match.groupdict())
        if not end_time:
            return TimeInterval(start_time=st, end_time=None)
        else:
            et_match = re.search(
                TIMEPOINT_REGEX[lang]['_time'][0], end_time)
            et = Time._from_groupdict(et_match.groupdict())
            return TimeInterval(start_time=st, end_time=et)

    @property
    def valid(self):
        """ Checks that both self.time and self.date are valid. """
        return all([self.time.valid and self.date.valid])

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a DateTime """
        start_date = self.date.to_python()
        start_time = self.time.start_time
        return makerrulestr(start_date, count=1, byhour=start_time.hour,
                            byminute=start_time.minute)

    def to_python(self):
        start_datetime = datetime(
            year=self.date.year,
            month=self.date.month,
            day=self.date.day,
            hour=self.time.start_time.hour,
            minute=self.time.start_time.minute)

        if self.time.end_time:
            end_datetime = datetime(
                year=self.date.year,
                month=self.date.month,
                day=self.date.day,
                hour=self.time.end_time.hour,
                minute=self.time.end_time.minute)
            return (start_datetime, end_datetime)
        else:
            return start_datetime

    def to_db(self):
        """ Return a dict containing the recurrence rule and the duration
            (in min)

        """
        return {
            'rrule': self.rrulestr,
            'duration': duration(
                start=self.time.start_time, end=self.time.end_time),
            'span': self.span
        }

    def future(self, reference=date.today()):
        """Return whether the datetime is located in the future.

        The default time reference is the day of the method execution.

        """
        return self.date.future(reference)


class DateTimeList(Timepoint):

    """Datetime list normalizer, in charge of normalizing datetime list
    regex matches.

    """

    def __init__(self, datetimes, **kwargs):
        super(DateTimeList, self).__init__(**kwargs)
        self.datetimes = datetimes

    def __iter__(self):
        """ Iteration over self.datetimes list """
        for dt in self.datetimes:
            yield dt

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        start_time = groupdict.get('start_time')
        end_time = groupdict.get('end_time')
        date_list = groupdict.get('date_list')
        span = kwargs['span']
        datetimes = cls._set_datetimes(date_list, start_time, end_time,
                                       lang, span)
        return DateTimeList(datetimes, **kwargs)

    @classmethod
    def _set_datetimes(cls, dates, start_time, end_time, lang, span):
        """ Associate the time interval to each date in the date list.

        The normalization process will instanciate DateTime objects,
        and store them in self.datetimes.

        """
        datetimes = []
        # Extract the date list and create a DateList object
        for date_list_pattern in TIMEPOINT_REGEX[lang]['date_list']:
            dl_match = re.search(date_list_pattern, dates)
            if dl_match:
                date_list = DateList._from_groupdict(
                    dl_match.groupdict(), span=span, lang=lang)
                break
        # extract the time interval and create a TimeInterval object
        start_time_match = re.search(
            TIMEPOINT_REGEX[lang]['_time'][0], start_time)
        start_time = Time._from_groupdict(start_time_match.groupdict())
        # if not end_time:
        #     time_interval = TimeInterval(
        #         start_time=start_time, end_time=None, lang=lang)
        if end_time:
            end_time_match = re.search(
                TIMEPOINT_REGEX[lang]['_time'][0], end_time)
            end_time = Time._from_groupdict(end_time_match.groupdict())
        time_interval = TimeInterval(
            start_time=start_time, end_time=end_time, lang=lang)

        # Populate self.datetimes with Datetimes objects
        for _date in date_list:
            datetimes.append(
                DateTime(date=_date, time=time_interval, lang=lang, span=span))
        return datetimes

    def future(self, reference=date.today()):
        """Returns whether the DateTimeList is located in the future.

        A DateTimeList is considered future even if a part of its
        datetimes are future.

        The default time reference is the day of the method execution.

        """
        return any([dt.date.future(reference) for dt in self.datetimes])

    @property
    def valid(self):
        """ Check the validity of each datetime in self.datetimes. """
        return all([dt.valid for dt in self.datetimes])

    def to_db(self):
        return [dt.to_db() for dt in self.datetimes]

    def to_python(self):
        return [dt.to_python() for dt in self.datetimes]


class DateTimeInterval(Timepoint):

    """ A datetime interval refers to a interval of date, with specified time.

    """

    def __init__(self, date_interval, time_interval, **kwargs):

        super(DateTimeInterval, self).__init__(**kwargs)
        self.date_interval = date_interval
        self.time_interval = time_interval

    def __iter__(self):
        """ Iteration over the start and end datetime. """
        for _date in self.date_interval:
            yield _date

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        time_interval = cls._set_time_interval(groupdict, lang)
        date_interval = cls._set_date_interval(groupdict, lang)
        return DateTimeInterval(date_interval, time_interval, **kwargs)

    @classmethod
    def _set_time_interval(cls, groupdict, lang):
        return TimeInterval._from_groupdict(groupdict, lang)

    @classmethod
    def _set_date_interval(cls, groupdict, lang):
        return DateInterval._from_groupdict(groupdict, lang)

    @property
    def valid(self):
        """ Checks that start and end datetimes are valid. """
        return all([self.date_interval.valid, self.time_interval.valid])

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a DateTimeInterval """
        start_time = self.time_interval.start_time
        start_date = self.date_interval.start_date.to_python()
        end = datetime.combine(self.date_interval.end_date.to_python(),
                               DAY_END)
        return makerrulestr(start_date, end, interval=1,
                            byhour=start_time.hour, byminute=start_time.minute)

    def to_python(self):
        out = []

        # getting date interval
        start_date = self.date_interval.start_date
        end_date = self.date_interval.end_date

        start_date = date(year=start_date.year, month=start_date.month,
                          day=start_date.day)
        end_date = date(year=end_date.year, month=end_date.month,
                        day=end_date.day)
        delta = end_date - start_date

        # getting time interval
        start_time = self.time_interval.start_time
        end_time = self.time_interval.end_time

        nb_days = range(0, delta.days + 1)
        for i in nb_days:
            i_date = start_date + timedelta(days=i)
            i_start_datetime = datetime(
                year=i_date.year,
                month=i_date.month,
                day=i_date.day,
                hour=start_time.hour,
                minute=start_time.minute,
                second=0
            )
            if end_time:
                i_end_datetime = datetime(
                    year=i_date.year,
                    month=i_date.month,
                    day=i_date.day,
                    hour=end_time.hour,
                    minute=end_time.minute,
                    second=0
                )
                out.append((i_start_datetime, i_end_datetime))
            else:
                out.append((i_start_datetime, i_start_datetime))

        return out

    def to_db(self):
        return {
            'rrule': self.rrulestr,
            'duration': duration(
                start=self.time_interval.start_time,
                end=self.time_interval.end_time),
            'span': self.span
        }

    def future(self, reference=date.today()):
        """Returns whether the DateTimeInterval is located in the future.

        A DateTimeInterval is considered future if its end date is located
        in the future.

        The default time reference is the day of the method execution.

        """
        return self.date_interval.end_date.future(reference)


class ContinuousDatetimeInterval(Timepoint):

    def __init__(self, start_datetime, end_datetime, **kwargs):
        super(ContinuousDatetimeInterval, self).__init__(**kwargs)
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):

        # normalize the date and time regex matches
        date_interval = DateInterval._from_groupdict(groupdict, lang, **kwargs)
        time_interval = TimeInterval._from_groupdict(groupdict, lang, **kwargs)

        # now, combine them into start/end DateTimes
        start_datetime = DateTime(date_interval.start_date,
                                  TimeInterval(time_interval.start_time))
        end_datetime = DateTime(date_interval.end_date,
                                TimeInterval(time_interval.end_time))
        return ContinuousDatetimeInterval(
            start_datetime, end_datetime, **kwargs)

    @property
    def valid(self):
        return all([self.start_datetime.valid, self.end_datetime.valid])

    def future(self, reference=date.today()):
        return self.end_datetime.future(reference)

    @property
    def rrulestr(self):
        """Return the ContinuousDatetimeInterval RRule string."""
        start_dt = self.start_datetime.to_python()
        start_time = start_dt.time()
        start_date = start_dt.date()
        end_dt = datetime.combine(self.end_datetime.to_python().date(),
                                  DAY_END)
        return makerrulestr(
            start_date, end_dt,
            interval=1, byhour=start_time.hour, byminute=start_time.minute)

    def to_db(self):
        """Export the ContinuousDatetimeInterval to a database-ready format."""
        return {
            'rrule': self.rrulestr,
            'duration': duration(start=self.start_datetime.to_python(),
                                 end=self.end_datetime.to_python()),
            'continuous': True,
            'span': self.span
        }

    def to_python(self):
        return (self.start_datetime.to_python(), self.end_datetime.to_python())


class WeekdayRecurrence(Timepoint):

    """ Object in charge of normalizing a weekday recurrence extraction result

    The normalized result is a dateutil.rrule.rrule object, generating datetimes
    using the recurrence rule.

    This rrule can be formatted to the RFC standard format using the __str__
    method.

    """

    def __init__(
        self, weekdays, start_date, end_date, start_time, end_time,
        **kwargs
    ):
        super(WeekdayRecurrence, self).__init__(**kwargs)
        self.weekdays = weekdays
        self.start_date = start_date
        self.end_date = end_date
        self.start_time = start_time
        self.end_time = end_time

    def __eq__(self, other):
        """ Equality is based on the RFC syntax """
        return str(self) == str(other)

    def __str__(self):
        return self.rrulestr

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        weekdays = cls._set_weekdays(groupdict, lang)
        start_date, end_date = cls._set_date_interval(groupdict, lang)
        start_time, end_time = cls._set_time_interval(groupdict, lang)
        return WeekdayRecurrence(
            weekdays, start_date, end_date, start_time, end_time, **kwargs)

    @classmethod
    def _set_weekdays(cls, groupdict, lang):
        """ Return the list of reccurent days index

        For example, if groupdict['weekdays'] == 'le lundi, mardi et mercredi',
        it returns [0, 1, 2]

        """
        return sorted(
            WEEKDAY[lang][day.group(0)] for day in
            re.finditer(
                r'|'.join(WEEKDAY[lang].keys()),
                groupdict['weekdays'].lower()))

    @classmethod
    def _set_date_interval(cls, groupdict, lang):
        """Return a tuple of the bounds of the detected date interval.

        If not date interval was found, return (today, None).

        """
        if groupdict.get('date_interval'):
            date_interval = DateInterval._from_groupdict(
                groupdict, lang=lang).to_python()
            return date_interval
        else:
            return date.today(), None

    @classmethod
    def _set_time_interval(cls, groupdict, lang):
        """Return a tuple of the bounds of the detected time interval.

        If no time interval was detected, return (DAY_START, DAY_END).
        If a single time was detected, return it, along with None,
        except if this time is DAY_START, in this case, return
        (DAY_START, DAY_END).

        """
        if groupdict.get('time_interval'):
            time_interval = TimeInterval._from_groupdict(
                groupdict, lang=lang).to_python()
            # TimeInterval.to_python() can either return a time instance
            # or a list of 2 time instances, because we made the choice
            # of always dealing with TimeInterval, to avoid having too
            # much normalizer classes
            if isinstance(time_interval, time):
                if time_interval == DAY_START:  # all day
                    return DAY_START, DAY_END
                else:
                    return time_interval, None
            else:
                return time_interval[0], time_interval[-1]
        else:
            return DAY_START, DAY_END

    @property
    def rrulestr(self):
        """ Generate a full description of the recurrence rule"""
        if self.end_date is not None:
            end = datetime.combine(self.end_date, DAY_END)
        elif self.end_date is None:
            end = None
        return makerrulestr(self.start_date, end=end, rule=self.to_python())

    @property
    def valid(self):
        """ A recurrence is valid if it applies on at least one weekday.

        Otherwhise it would be a nonsense

        """
        return len(self.weekdays) >= 0

    def future(self, reference=date.today()):
        if self.end_date is None:
            return True
        return self.end_date > reference

    def to_python(self):
        if self.start_time.hour or self.start_time.minute:
            return rrule(
                WEEKLY,
                byweekday=self.weekdays,
                byhour=self.start_time.hour,
                byminute=self.start_time.minute)
        else:
            return rrule(WEEKLY, byweekday=self.weekdays)

    def to_db(self):
        return {
            'rrule': self.rrulestr,
            'duration': duration(start=self.start_time, end=self.end_time),
            'span': self.span
        }


class WeekdayIntervalRecurrence(WeekdayRecurrence):

    """ Object in charge of normalizing recurrent weekdays *intervals*

    The only logic differing from the WeekdayRecurrence class is the
    way the weekdays are set.

    """

    @classmethod
    def _set_weekdays(cls, groupdict, lang):
        """ Return the list of reccurent days index

        Example: if 'start_day' == 'lundi' and 'end_day' == 'vendredi',
        the output is [0, 1, 2, 3, 4]

        """
        start_weekday = groupdict['start_weekday'].rstrip('s').lower()
        start_weekday_nb = WEEKDAY[lang][start_weekday]
        end_weekday = groupdict['end_weekday'].rstrip('s').lower()
        end_weekday_nb = WEEKDAY[lang][end_weekday]

        if start_weekday_nb < end_weekday_nb:
            return range(start_weekday_nb, end_weekday_nb + 1)
        else:
            return range(start_weekday_nb, 7) + range(end_weekday_nb + 1)


class AllWeekdayRecurrence(WeekdayRecurrence):

    """ Object in charge of the normalisation of a recurrence rule ocurring
        all days of the week

    """

    @classmethod
    def _set_weekdays(cls, groupdict, lang):
        return range(0, 7)
