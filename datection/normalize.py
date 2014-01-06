# -*- coding: utf-8 -*-

import re
import datetime

from dateutil.rrule import rrule, WEEKLY

from .regex import WEEKDAY, MONTH, TIMEPOINT_REGEX, SHORT_MONTH
from .utils import makerrulestr, duration


ALL_DAY = 1439  # number of minutes from midnight to 23:59


def timepoint_factory(detector, data, **kwargs):
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
        'weekday_recurrence': WeekdayRecurrence,
        'weekday_interval_recurrence': WeekdayIntervalRecurrence,
        'allweekday_recurrence': AllWeekdayRecurrence,
    }
    if detector not in factory:
        raise NotImplementedError(
            detector + " normalisation is not yet handled.")
    return factory[detector](data, **kwargs)


class Timepoint(object):

    """ The mother class for all timepoint classes. """

    def __init__(self, data, **kwargs):
        """ Set all key/values in data and kwargs as instance arguments.

        All pure numeric strings are converted to int.
        All non-pure numeric strings are stripped.
        All non-string values are inserted as-is.

        """
        for k, v in data.items():
            if v and isinstance(v, basestring):
                if v.isdigit():
                    data[k] = int(v)
        self.data = data
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def __eq__(self, other):
        return self.to_python() == other.to_python()

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(str(self.to_python()))

    def future(self, reference=None):
        """Return whether the timepoint is located in the future."""
        return False

    def text_to_db(self):
        """Make sure self.text is unicode/made of unicode texts."""
        if not hasattr(self, 'text'):
            return u''
        if isinstance(self.text, basestring):
            return [self.text.decode('utf-8')]
        elif isinstance(self.text, list):
            return [text.decode('utf-8') for text in self.text]


class Date(Timepoint):

    """Date normalizer, in charge of normalizing date regex matches."""

    def __init__(self, data=dict(), day=None, month=None, month_name=None,
                 year=None, **kwargs):
        super(Date, self).__init__(data, **kwargs)
        if data:
            self.year = self._set_year(self.data.get('year'))
            self.month = self._set_month(self.data.get('month_name'))
            self.day = self._set_day(self.data.get('day'))
        else:
            # if the year is None, set its value to datetime.MINYEAR (= 1)
            # in this case, the date will be considered as invalid
            if year:
                if len(str(year)) == 4:
                    self.year = int(year)
                else:
                    # if a 2 digit year has been passed as argument, it needs
                    # to be normalized
                    self.year = self._normalize_2digit_year(year)
            else:
                self.year = datetime.MINYEAR

            # if month is not given but month name is, deduce month from it
            if month:
                self.month = int(month)
            elif month_name:
                # deduce month number from month name
                self.month = self._set_month(month_name)
            else:
                self.month = None

            self.day = int(day)

    @staticmethod
    def _normalize_2digit_year(year):
        """ Normalize a 2 digit year into a 4 digit one

        Example: xx/xx/12 --> xx/xx/2012

        WARNING: if a past date is written in this format (ex: 01/06/78)
        it is impossible to know if it references the year 1978 or 2078.
        If the 2-digit date is less than 15 years in the future,
        we consider that it takes place in our century, otherwise,
        it is considered as a past date

        """
        current_year = datetime.date.today().year
        century = int(str(current_year)[:2])

        # handle special case where the 2 digit year started with a 0
        # int("07") = 7
        if len(str(year)) == 1:
            year = '0' + str(year)
        else:
            year = str(year)
        if int(str(century) + year) - current_year < 15:
            # if year is less than 15 years in the future, it is considered
            # a future date
            return int(str(century) + year)
        else:
            # else, it is treated as a past date
            return int(str(century - 1) + year)

    def _set_year(self, year):
        """ Set and normalise the date year

        If year is None (missing year) we replace it by the next year
        Elif the year is numeric but only 2 digit long, we guess in which
        century it is (ex: dd/mm/13 -> 1913, 2013, etc ?)
        Else, make sure the year is an int

        """
        if not year:
            return datetime.date.today().year + 1

        # Case of a numeric date with short year format
        if len(str(year)) == 2:
            return self._normalize_2digit_year(year)
        else:
            return int(self.data['year'])

    def _set_month(self, month_name):
        """Set the date month from the date month name

        If the month name is an integer, return it as is.
        If the month name is a string, return is numeric value,
        whether the month name is abbreviated or not.

        """
        if isinstance(month_name, basestring):  # string date
            # if month name is whole
            if month_name.lower() in MONTH[self.lang]:
                return MONTH[self.lang][month_name.lower()]
            # if month name is abbreviated
            else:
                # remove trailing dot, if any
                month_name = month_name.rstrip('.')
                if month_name.lower() in SHORT_MONTH[self.lang]:
                    return SHORT_MONTH[self.lang][month_name.lower()]
        elif isinstance(month_name, int):  # numeric date
            return month_name
        else:
            return None

    def _set_day(self, day):
        """Return the integer value of day, except if day is None."""
        if not day:
            return None
        return int(day)

    @property
    def valid(self):
        """If the generated datetime.date is valid, return True, else False.

        """
        if all([self.year, self.month, self.day]):
            if self.year == datetime.MINYEAR:
                return False
            try:  # check if date is valid
                datetime.date(year=self.year, month=self.month, day=self.day)
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
            return datetime.date(
                year=self.year, month=self.month, day=self.day)
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
            'texts': self.text_to_db()
        }

    def future(self, reference=datetime.date.today()):
        """Returns whether the Date is located in the future.

        The default time reference is the day of the method execution.

        """
        return self.to_python() > reference


class DateList(Timepoint):

    """Date list normalizer in charge of normalizing date list regex matches"""

    def __init__(self, data=dict(), dates=None, **kwargs):
        """ Initialize the DateList object. """
        super(DateList, self).__init__(data, **kwargs)
        if dates:
            self.dates = dates
        else:
            self.dates = self._set_dates(data)
            self._set_year()
            self._set_month()

    def __iter__(self):
        """Iterate over the list of dates"""
        for date in self.dates:
            yield date

    def _set_dates(self, data):
        """Normalize the dates and return a list of Date objects."""
        dates = []
        for date in re.finditer(
                TIMEPOINT_REGEX[self.lang]['_date_in_list'][0],
                self.data['date_list']):
            # Assign datetime.MINYEAR to year, if year is None
            # It will be a marker allowing the year to be replaced
            # by the same value as the last year of the list
            # Ex: 2, 3 & 5 juin 2013 → 2/06/13, 3/06/13 & 5/06/13
            if not date.groupdict()['year']:
                groupdict = dict(date.groupdict())
                groupdict['year'] = datetime.MINYEAR
                dates.append(Date(groupdict, lang=self.lang, text=self.text))
            else:
                dates.append(
                    Date(date.groupdict(), lang=self.lang, text=self.text))
        return dates

    def _set_year(self):
        """ All dates without a year will inherit from the end date year """
        end_date = self.dates[-1]
        if end_date.year:
            if end_date.year == datetime.MINYEAR:
                end_date.year = datetime.date.today().year
            for date in self.dates[:-1]:
                if date.year == datetime.MINYEAR:
                    date.year = end_date.year

    def _set_month(self):
        """ All dates without a month will inherit from the end date month """
        end_date = self.dates[-1]
        if end_date.month:
            for date in self.dates[:-1]:
                if not date.month:
                    date.month = end_date.month

    @property
    def valid(self):
        """ Check that all dates in self.dates are valid. """
        return all([date.valid for date in self.dates])

    def to_python(self):
        """Convert self.dates to a list of datetime.date objects."""
        return [date.to_python() for date in self.dates]

    def to_db(self):
        """Convert self.dates to a list of duration rrules."""
        return [date.to_db() for date in self.dates]

    def future(self, reference=datetime.date.today()):
        """Returns whether the DateList is located in the future.

        A DateList is considered future even if a part of its dates
        are future.

        The default time reference is the day of the method execution.

        """
        return any([d.future(reference) for d in self.dates])


class DateInterval(Timepoint):

    """Date normalizer, in charge of normalizing date interval regex matches.

    """

    def __init__(self, data={}, start_date=None, end_date=None, **kwargs):
        super(DateInterval, self).__init__(data, **kwargs)
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        if not (start_date and end_date):
            self._set_dates()

    def __iter__(self):
        """ Iteration through the self.dates list. """
        for date in [self.start_date, self.end_date]:
            yield date

    def _set_dates(self):
        """ Restore all missing data and serialize the start and end date """
        # start date inherits from end month name if necessary
        if not self.data['start_month_name'] and self.data['end_month_name']:
            self.data['start_month_name'] = self.data['end_month_name']

        if not self.data['start_year'] and self.data['end_year']:
            start_year = self.data['end_year']
            end_year = self.data['end_year']
        elif not (self.data['start_year'] or self.data['end_year']):
            start_year = datetime.date.today().year
            end_year = datetime.date.today().year
        else:
            start_year = self.data['start_year']
            end_year = self.data['end_year']

        # Create normalised start date of Date type
        if not hasattr(self, 'start_date'):
            self.start_date = Date(
                year=start_year,
                month_name=self.data['start_month_name'],
                day=self.data['start_day'],
                lang=self.lang,
                text=self.text)
        # create serialized end date of Date type
        if not hasattr(self, 'end_date'):
            self.end_date = Date(
                year=end_year,
                month_name=self.data['end_month_name'],
                day=self.data['end_day'],
                lang=self.lang,
                text=self.text)

        # warning, if end month occurs before start month, then end month
        # is next year
        if self.end_date.month < self.start_date.month:
            if self.data['end_year'] and not self.data['start_year']:
                self.start_date.year -= 1
            elif not self.data['end_year']:
                self.end_date.year += 1

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
        return [date.to_python() for date in self]

    def to_db(self):
        """ Return a dict containing the recurrence rule and the duration
            (in min)

        """
        return {
            'rrule': self.rrulestr,
            'duration': ALL_DAY,
            'texts': self.text_to_db()
        }

    def future(self, reference=datetime.date.today()):
        """Returns whether the DateInterval is located in the future.

        A DateInterval is considered future if its end date is located
        in the future.

        The default time reference is the day of the method execution.

        """
        return self.end_date.future(reference)


class Time(Timepoint):

    """Time normalizer, in charge of normalizing the time regex matches."""

    def __init__(self, data=dict(), hour=None, minute=None, **kwargs):
        super(Time, self).__init__(data, **kwargs)
        if hour is not None:
            self.hour = hour
        if minute is not None:
            self.minute = minute
        if hour is None and minute is None:
            self.minute = self._set_minute(self.data.get('minute'))
            self.hour = int(self.data['hour']) if self.data['hour'] else None

    def _set_minute(self, minute):
        """ Set self.minute to (0 if missing or null) """
        return int(minute) if minute else 0

    @property
    def valid(self):
        """ Return whether the time is valid or not.

        The validity of the date is checked by trying to instanciate
        a datetime.date object.

        """
        if self.hour is not None and self.minute is not None:
            try:  # check if time is valid
                datetime.time(self.hour, self.minute)
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
        return datetime.time(hour=int(self.hour), minute=int(self.minute))

    def to_db(self):
        return None


class TimeInterval(Timepoint):

    """Time interval normalizer, in charge of normalizing time interval regex
    matches.

    """

    def __init__(self, data=dict(), start_time=None, end_time=None, **kwargs):
        super(TimeInterval, self).__init__(data, **kwargs)
        # store TimeInterval specific arguments
        if start_time:
            self.start_time = start_time
        self.end_time = end_time
        if not(start_time):
            self.start_time = self._set_start_time(self.data.get('start_time'))
            self.end_time = self._set_end_time(self.data.get('end_time'))

    def __iter__(self):
        """ Iteration over the start and end time. """
        for time in [self.start_time, self.end_time]:
            yield time

    def _set_start_time(self, st):
        """ Normalize the start time into a Time object """
        if not st:
            return None
        st = re.search(TIMEPOINT_REGEX[self.lang]['_time'][0], st,
                       flags=re.IGNORECASE | re.UNICODE)
        return Time(st.groupdict(), lang=self.lang)

    def _set_end_time(self, et):
        """ Normalize the end time into a Time object """
        # normalization of self.end_time into a Time object
        if not et:
            return None
        et = re.search(TIMEPOINT_REGEX[self.lang]['_time'][0], et,
                       flags=re.IGNORECASE | re.UNICODE)
        return Time(et.groupdict(), lang=self.lang)

    @property
    def valid(self):
        """ Check that both self.start_time and self.end_time (if any) are valid. """
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

    def __init__(self, data={}, date=None, time=None, **kwargs):
        super(DateTime, self).__init__(data, **kwargs)
        if date:
            self.date = date
        if time:
            self.time = time
        if not (date and time):
            year = self.data.get('year') or datetime.date.today().year + 1
            month_name = self.data.get('month_name')
            day = self.data.get('day')
            start_time = self.data.get('start_time')
            end_time = self.data.get('end_time')
            self.date = self._set_date(year, month_name, day)
            self.time = self._set_time(start_time, end_time)

    def _set_date(self, year, month_name, day):
        """Set the datetime date, as a Date object."""
        return Date(
            year=year, month_name=month_name, day=day,
            lang=self.lang, text=self.text)

    def _set_time(self, start_time, end_time):
        """Set the datetime time, as a TimeInterval object."""
        st_match = re.search(
            TIMEPOINT_REGEX[self.lang]['_time'][0], start_time)
        st = Time(st_match.groupdict())
        if not end_time:
            return TimeInterval(start_time=st, end_time=None)
        else:
            et_match = re.search(
                TIMEPOINT_REGEX[self.lang]['_time'][0], end_time)
            et = Time(et_match.groupdict())
            return TimeInterval(start_time=st, end_time=et)

    @property
    def valid(self):
        """ Checks that both self.time and self.date are valid. """
        return all([self.time.valid and self.date.valid])

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a DateTime """
        start = self.date.to_python()
        st = self.time.start_time
        return makerrulestr(
            start,
            count=1, byhour=st.hour, byminute=st.minute)

    def to_python(self):
        start_datetime = datetime.datetime(
            year=self.date.year,
            month=self.date.month,
            day=self.date.day,
            hour=self.time.start_time.hour,
            minute=self.time.start_time.minute,
            second=0
        )

        if self.time.end_time:
            end_datetime = datetime.datetime(
                year=self.date.year,
                month=self.date.month,
                day=self.date.day,
                hour=self.time.end_time.hour,
                minute=self.time.end_time.minute,
                second=0
            )
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
            'texts': self.text_to_db()
        }

    def future(self, reference=datetime.date.today()):
        """Return whether the datetime is located in the future.

        The default time reference is the day of the method execution.

        """
        return self.date.future(reference)


class DateTimeList(Timepoint):

    """Datetime list normalizer, in charge of normalizing datetime list
    regex matches.

    """

    def __init__(self, data=dict(), datetimes=None, **kwargs):
        super(DateTimeList, self).__init__(data, **kwargs)
        if datetimes:
            self.datetimes = datetimes
        else:
            start_time = self.data.get('start_time')
            end_time = self.data.get('end_time')
            date_list = self.data.get('date_list')
            self.datetimes = self._set_datetimes(
                date_list, start_time, end_time)

    def __iter__(self):
        """ Iteration over self.datetimes list """
        for dt in self.datetimes:
            yield dt

    def _set_datetimes(self, dates, start_time, end_time):
        """ Associate the time interval to each date in the date list.

        The normalization process will instanciate DateTime objects,
        and store them in self.datetimes.

        """
        datetimes = []

        # Extract the date list and create a DateList object
        for date_list_pattern in TIMEPOINT_REGEX[self.lang]['date_list']:
            dl = re.search(date_list_pattern, dates)
            if dl:
                date_list = DateList(
                    dl.groupdict(), text=dl.group(0), lang=self.lang)
                break
        # extract the time interval and create a TimeInterval object
        st = re.search(TIMEPOINT_REGEX[self.lang]['_time'][0], start_time)
        st = Time(st.groupdict())
        if not end_time:
            ti = TimeInterval(start_time=st, end_time=None, lang=self.lang)
        else:
            et = re.search(TIMEPOINT_REGEX[self.lang]['_time'][0], end_time)
            et = Time(et.groupdict())
            ti = TimeInterval(start_time=st, end_time=et, lang=self.lang)

        # Populate self.datetimes with Datetimes objects
        for date in date_list:
            datetimes.append(
                DateTime(date=date, time=ti, lang=self.lang, text=self.text))
        return datetimes

    def future(self, reference=datetime.date.today()):
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

    """ A datetime interval refers to a interval of date, with specified time. """

    def __init__(self, data={}, date_interval=None, time_interval=None, **kwargs):

        super(DateTimeInterval, self).__init__(data, **kwargs)
        if date_interval:
            self.date_interval = date_interval
        if time_interval:
            self.time_interval = time_interval
        if not(date_interval and time_interval):
            st = self.data.get('start_time')
            et = self.data.get('end_time')
            self.time_interval = self._set_time_interval(st, et)
            self.date_interval = self._set_date_interval()

    def __iter__(self):
        """ Iteration over the start and end datetime. """
        for date in self.date_interval:
            yield date

    def _set_time_interval(self, start_time, end_time):
        return TimeInterval(
            {
                'start_time': start_time,
                'end_time': end_time
            },
            lang=self.lang)

    def _set_date_interval(self):
        # if the end month name (always prewent) is a number,
        # it means that the date is written numerically
        # so a numeric date interval regex must be used
        # otherwise, the date is written "normally", so a litteral date
        # interval regex is used
        if isinstance(self.data['end_month_name'], basestring):
            re_date_interval = TIMEPOINT_REGEX[self.lang]['date_interval'][0]
        else:
            re_date_interval = TIMEPOINT_REGEX[self.lang]['date_interval'][1]
        return DateInterval(
            re.search(
                re_date_interval,
                self.text
            ).groupdict(),
            lang=self.lang, text=self.text)

    @property
    def valid(self):
        """ Checks that start and end datetimes are valid. """
        return all([self.date_interval.valid, self.time_interval.valid])

    @property
    def rrulestr(self):
        """ Return a reccurence rule string tailored for a DateTimeInterval """
        st = self.time_interval.start_time
        start = self.date_interval.start_date.to_python()
        end = datetime.datetime.combine(
            self.date_interval.end_date.to_python(),
            datetime.time(23, 59, 59))
        return makerrulestr(
            start, end,
            interval=1, byhour=st.hour, byminute=st.minute)

    def to_python(self):
        out = []

        # getting date interval
        sd = self.date_interval.start_date
        ed = self.date_interval.end_date

        start_date = datetime.date(year=sd.year, month=sd.month, day=sd.day)
        end_date = datetime.date(year=ed.year, month=ed.month, day=ed.day)
        delta = end_date - start_date

        # getting time interval
        start_time = self.time_interval.start_time
        end_time = self.time_interval.end_time

        nb_days = range(0, delta.days + 1)
        for i in nb_days:
            i_date = start_date + datetime.timedelta(days=i)
            i_start_datetime = datetime.datetime(
                year=i_date.year,
                month=i_date.month,
                day=i_date.day,
                hour=start_time.hour,
                minute=start_time.minute,
                second=0
            )
            if end_time:
                i_end_datetime = datetime.datetime(
                    year=i_date.year,
                    month=i_date.month,
                    day=i_date.day,
                    hour=end_time.hour,
                    minute=end_time.minute,
                    second=0
                )
                out.append((i_start_datetime, i_end_datetime))
            else:
                out.append(i_start_datetime)

        return out

    def to_db(self):
        return {
            'rrule': self.rrulestr,
            'duration': duration(
                start=self.time_interval.start_time,
                end=self.time_interval.end_time),
            'texts': self.text_to_db()
        }

    def future(self, reference=datetime.date.today()):
        """Returns whether the DateTimeInterval is located in the future.

        A DateTimeInterval is considered future if its end date is located
        in the future.

        The default time reference is the day of the method execution.

        """
        return self.date_interval.end_date.future(reference)


class WeekdayRecurrence(Timepoint):

    """ Object in charge of normalizing a weekday recurrence extraction result

    The normalized result is a dateutil.rrule.rrule object, generating datetimes
    using the recurrence rule.

    This rrule can be formatted to the RFC standard format using the __str__
    method.

    """

    def __init__(self, data={}, weekdays=None, start=None, end=None, **kwargs):
        super(WeekdayRecurrence, self).__init__(data, **kwargs)
        self.weekdays = self._set_weekdays() if not weekdays else weekdays
        if not start and not end:
            self.start_datetime, self.end_datetime = self._set_datetime_interval(
            )
        else:
            self.start_datetime, self.end_datetime = start, end

    def __eq__(self, other):
        """ Equality is based on the RFC syntax """
        return str(self) == str(other)

    def __str__(self):
        return self.rrulestr

    def _set_weekdays(self):
        """ Return the list of reccurent days index

        For example, if self.data['weekdays'] == 'le lundi, mardi et mercredi',
        it returns [0, 1, 2]

        """
        return sorted([
            WEEKDAY[self.lang][day.group(0)] for day in
            re.finditer(
                r'|'.join(WEEKDAY[self.lang].keys()),
                self.data['weekdays'].lower())])

    def _set_datetime_interval(self):
        """ Return the start and end date of the recurrence.

        If not specified, the default start date value is datetime.now().
        If not specified, the default end date value is one year after
        datetime.now().

        """
        if self.data.get('date_interval') and self.data.get('time_interval'):
            datetime_interval = DateTimeInterval(
                data=self.data,
                lang=self.lang,
                text=self.data['date_interval'] + ' ' + self.data['time_interval']).\
                to_python()
            start_datetime = datetime_interval[0][0]
            end_datetime = datetime_interval[-1][-1]

        elif self.data.get('date_interval') and not self.data.get('time_interval'):
            # normalize darte interval from regex matches
            date_interval = DateInterval(
                data=self.data,
                lang=self.lang,
                text=self.data['date_interval'])
            # extract the start and end dates from date interval
            start_date = date_interval.start_date.to_python()
            end_date = date_interval.end_date.to_python()

            # Create datetimes from the start and end dates by associatng
            # each of them with a default time
            start_time = datetime.time(hour=0, minute=0, second=0)
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_time = datetime.time(hour=23, minute=59, second=59)
            end_datetime = datetime.datetime.combine(end_date, end_time)

        elif self.data.get('time_interval') and not self.data.get('date_interval'):
            # normalize darte interval from regex matches
            time_interval = TimeInterval(
                data=self.data,
                lang=self.lang,
                text=self.data['time_interval'])
            # extract the start and end times from date interval
            start_time = time_interval.start_time.to_python()
            if time_interval.end_time:
                end_time = time_interval.end_time.to_python()
            else:
                end_time = time_interval.start_time.to_python()

            # Create datetimes from the start and end times by associatng
            # each of them with a default date
            start_date = datetime.date.today()
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_date = start_datetime.date() + datetime.timedelta(days=365)
            end_datetime = datetime.datetime.combine(
                end_date, end_time)
        else:
            start_datetime = datetime.datetime.combine(
                datetime.date.today(),
                datetime.time(0, 0, 0))
            # if not specified, the end date is one year after the start date
            end_datetime = start_datetime + datetime.timedelta(days=365)
        return start_datetime, end_datetime

    @property
    def rrulestr(self):
        """ Generate a full description of the recurrence rule"""
        return makerrulestr(
            self.start_datetime.date(),
            end=datetime.datetime.combine(
                self.end_datetime.date(), datetime.time(23, 59, 59)),
            rule=self.to_python())

    @property
    def valid(self):
        """ A recurrence is valid if it applies on at least one weekday.

        Otherwhise it would be a nonsense

        """
        return len(self.weekdays) >= 0

    def future(self, reference=datetime.date.today()):
        return self.end_datetime.date() > reference

    def to_python(self):
        st = self.start_datetime.time()
        start_h, start_min = st.hour, st.minute
        if start_h or start_min:
            return rrule(
                WEEKLY,
                byweekday=self.weekdays,
                byhour=start_h,
                byminute=start_min)
        else:
            return rrule(
                WEEKLY,
                byweekday=self.weekdays)

    def to_db(self):
        # measure the duration
        end_datetime = datetime.datetime.combine(
            self.start_datetime, self.end_datetime.time())
        return {
            'rrule': self.rrulestr,
            'duration': duration(start=self.start_datetime, end=end_datetime),
            'texts': self.text_to_db()
        }


class WeekdayIntervalRecurrence(WeekdayRecurrence):

    """ Object in charge of normalizing recurrent weekdays *intervals*

    The only logic differing from the WeekdayRecurrence class is the
    way the weekdays are set.

    """

    def _set_weekdays(self):
        """ Return the list of reccurent days index

        Example: if 'start_day' == 'lundi' and 'end_day' == 'vendredi',
        the output is [0, 1, 2, 3, 4]

        """
        start_weekday = self.data['start_weekday'].rstrip('s')
        start_weekday_number = WEEKDAY[self.lang][start_weekday]
        end_weekday = self.data['end_weekday'].rstrip('s')
        end_weekday_number = WEEKDAY[self.lang][end_weekday]

        if start_weekday_number < end_weekday_number:
            return range(start_weekday_number, end_weekday_number + 1)
        else:
            return range(start_weekday_number, 7) + range(end_weekday_number + 1)


class AllWeekdayRecurrence(WeekdayRecurrence):

    """ Object in charge of the normalisation of a recurrence rule ocurring
        all days of the week

    """

    def _set_weekdays(self):
        return range(0, 7)
