# -*- coding: utf-8 -*-

import re
import datetime

from dateutil.rrule import rrule, WEEKLY
from datection.regex import WEEKDAY
from datection.regex import MONTH
from datection.regex import TIMEPOINT_REGEX
from datection.regex import SHORT_MONTH
from datection.utils import makerrulestr
from datection.utils import normalize_2digit_year
from datection.utils import digit_to_int
from datection.utils import duration


ALL_DAY = 1439  # number of minutes from midnight to 23:59


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
    return factory[detector]._from_groupdict(data, lang, **kwargs)


class Timepoint(object):

    """ The mother class for all timepoint classes. """

    def __init__(self, lang=None, text=None):
        self.lang = lang
        self.text = text

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

    def __init__(self, year, day, month=None, month_name=None, **kwargs):
        super(Date, self).__init__(**kwargs)
        # if the year is None, set its value to datetime.MINYEAR (= 1)
        # in this case, the date will be considered as invalid
        if year:
            if len(str(year)) == 4:
                self.year = int(year)
            elif len(str(year)) == 2:
                # if a 2 digit year has been passed as argument, it needs
                # to be normalized
                self.year = normalize_2digit_year(year)
            else:
                self.year = year
        else:
            self.year = datetime.MINYEAR

        # if month is not given but month name is, deduce month from it
        if month:
            self.month = int(month)
        elif month_name:
            # deduce month number from month name
            self.month = self._set_month(month_name, kwargs['lang'])
        else:
            self.month = None

        self.day = int(day)

    def __repr__(self):
        return '{d}/{m}/{y}'.format(d=self.day, m=self.month, y=self.year)

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        """Create a Date instance from a regex match groupdict."""
        year = cls._set_year(groupdict.get('year'))
        month = cls._set_month(groupdict.get('month_name'), lang)
        day = cls._set_day(groupdict.get('day'))
        return Date(year=year, month=month, day=day, **kwargs)

    @classmethod
    def _set_year(cls, year):
        """ Set and normalise the date year

        If year is None (missing year) we replace it by the next year
        Elif the year is numeric but only 2 digit long, we guess in which
        century it is (ex: dd/mm/13 -> 1913, 2013, etc ?)
        Else, make sure the year is an int

        """
        if not year:
            # if year is not given, set year as next year
            return datetime.date.today().year + 1

        # Case of a numeric date with short year format
        if len(str(year)) == 2:
            return normalize_2digit_year(year)
        else:
            return int(year)

    @classmethod
    def _set_month(cls, month_name, lang):
        """Set the date month from the date month name

        If the month name is an integer, return it as is.
        If the month name is a string, return is numeric value,
        whether the month name is abbreviated or not.

        """
        if isinstance(month_name, basestring):  # string date
            if month_name.isdigit():
                return int(month_name)
            # if month name is whole
            elif month_name.lower() in MONTH[lang]:
                return MONTH[lang][month_name.lower()]
            # if month name is abbreviated
            else:
                # remove trailing dot, if any
                month_name = month_name.rstrip('.')
                if month_name.lower() in SHORT_MONTH[lang]:
                    return SHORT_MONTH[lang][month_name.lower()]
        elif isinstance(month_name, int):  # numeric date
            return month_name
        else:
            return None

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

    def __init__(self, dates, **kwargs):
        """ Initialize the DateList object. """
        super(DateList, self).__init__(**kwargs)
        self.dates = dates

    def __iter__(self):
        """Iterate over the list of dates"""
        for date in self.dates:
            yield date

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        """Instanciate a DateList from a regex match groupdict."""
        groupdict = digit_to_int(groupdict)
        dates = cls._set_dates(groupdict, lang, text=kwargs['text'])

        # make the dates without a year inherit from the one which does
        # if needed
        dates = cls._set_year(dates)

        # make the dates without a month inherit from the one which does
        # if needed
        dates = cls._set_month(dates)
        return DateList(dates, **kwargs)

    @classmethod
    def _set_dates(cls, groupdict, lang, text):
        """Normalize the dates and return a list of Date objects."""
        dates = []
        for date in re.finditer(TIMEPOINT_REGEX[lang]['_date_in_list'][0],
                                groupdict['date_list']):
            # Assign datetime.MINYEAR to year, if year is None
            # It will be a marker allowing the year to be replaced
            # by the same value as the last year of the list
            # Ex: 2, 3 & 5 juin 2013 → 2/06/13, 3/06/13 & 5/06/13
            groupdict = date.groupdict()
            if not groupdict['year']:
                groupdict['year'] = datetime.MINYEAR
            date = Date._from_groupdict(groupdict, lang=lang, text=text)
            dates.append(date)

        return dates

    @staticmethod
    def _set_year(dates):
        """ All dates without a year will inherit from the end date year """
        end_date = dates[-1]
        if end_date.year:
            if end_date.year == datetime.MINYEAR:
                end_date.year = datetime.date.today().year + 1
            for date in dates[:-1]:
                if date.year == datetime.MINYEAR:
                    date.year = end_date.year
        return dates

    @staticmethod
    def _set_month(dates):
        """ All dates without a month will inherit from the end date month """
        end_date = dates[-1]
        if end_date.month:
            for date in dates[:-1]:
                if not date.month:
                    date.month = end_date.month
        return dates

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

    def __init__(self, start_date, end_date, **kwargs):
        super(DateInterval, self).__init__(**kwargs)
        self.start_date = start_date
        self.end_date = end_date

    def __iter__(self):
        """ Iteration through the self.dates list. """
        for date in [self.start_date, self.end_date]:
            yield date

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        start_date, end_date = cls._set_dates(groupdict, lang)
        return DateInterval(start_date, end_date, **kwargs)

    @classmethod
    def _set_dates(cls, groupdict, lang):
        """ Restore all missing groupdict and serialize the start and end date """
        # start date inherits from end month name if necessary
        if (not groupdict.get('start_month_name')
            and groupdict.get('end_month_name')):
            groupdict['start_month_name'] = groupdict['end_month_name']

        if not groupdict.get('start_year') and groupdict.get('end_year'):
            groupdict['start_year'] = groupdict['end_year']
        elif not (groupdict.get('start_year') or groupdict.get('end_year')):
            groupdict['start_year'] = datetime.date.today().year + 1
            groupdict['end_year'] = groupdict['start_year']

        # Create normalised start date of Date type
        if groupdict.get('start_month_name'):
            start_date = Date(year=groupdict['start_year'],
                              month_name=groupdict['start_month_name'],
                              day=groupdict['start_day'],
                              lang=lang)
        else:
            start_date = Date(year=groupdict['start_year'],
                              month=groupdict['start_month'],
                              day=groupdict['start_day'],
                              lang=lang)

        # create normalized end date of Date type
        if groupdict.get('end_month_name'):
            end_date = Date(year=groupdict['end_year'],
                            month_name=groupdict['end_month_name'],
                            day=groupdict['end_day'],
                            lang=lang)
        else:
            end_date = Date(year=groupdict['end_year'],
                            month=groupdict['end_month'],
                            day=groupdict['end_day'],
                            lang=lang)

        # warning, if end month occurs before start month, then end month
        # is next year
        if end_date.month < start_date.month:
            if start_date.year == end_date.year:
                start_date.year -= 1
            elif not groupdict['end_year']:
                end_date.year += 1

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

    def __init__(self, start_time, end_time=None, **kwargs):
        super(TimeInterval, self).__init__(**kwargs)
        self.start_time = start_time
        self.end_time = end_time

    def __iter__(self):
        """ Iteration over the start and end time. """
        for time in [self.start_time, self.end_time]:
            yield time

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

    def __init__(self, date, time, **kwargs):
        super(DateTime, self).__init__(**kwargs)
        self.date = date
        self.time = time

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        year = groupdict.get('year') or datetime.date.today().year + 1
        month_name = groupdict.get('month_name')
        day = groupdict.get('day')
        start_time = groupdict.get('start_time')
        end_time = groupdict.get('end_time')
        date = cls._set_date(year, month_name, day, lang)
        time = cls._set_time(start_time, end_time, lang)
        return DateTime(date, time, **kwargs)

    @classmethod
    def _set_date(cls, year, month_name, day, lang):
        """Set the datetime date, as a Date object."""
        return Date(year=year, month_name=month_name, day=day, lang=lang)

    @classmethod
    def _set_time(cls, start_time, end_time, lang):
        """Set the datetime time, as a TimeInterval object."""
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
        start_datetime = datetime.datetime(
            year=self.date.year,
            month=self.date.month,
            day=self.date.day,
            hour=self.time.start_time.hour,
            minute=self.time.start_time.minute)

        if self.time.end_time:
            end_datetime = datetime.datetime(
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
        text = kwargs['text']
        start_time = groupdict.get('start_time')
        end_time = groupdict.get('end_time')
        date_list = groupdict.get('date_list')
        datetimes = cls._set_datetimes(date_list, start_time, end_time,
                                       lang, text)
        return DateTimeList(datetimes, **kwargs)

    @classmethod
    def _set_datetimes(cls, dates, start_time, end_time, lang, text):
        """ Associate the time interval to each date in the date list.

        The normalization process will instanciate DateTime objects,
        and store them in self.datetimes.

        """
        datetimes = []
        # Extract the date list and create a DateList object
        for date_list_pattern in TIMEPOINT_REGEX[lang]['date_list']:
            dl = re.search(date_list_pattern, dates)
            if dl:
                date_list = DateList._from_groupdict(
                    dl.groupdict(), text=dl.group(0), lang=lang)
                break
        # extract the time interval and create a TimeInterval object
        st = re.search(TIMEPOINT_REGEX[lang]['_time'][0], start_time)
        st = Time._from_groupdict(st.groupdict())
        if not end_time:
            ti = TimeInterval(start_time=st, end_time=None, lang=lang)
        else:
            et = re.search(TIMEPOINT_REGEX[lang]['_time'][0], end_time)
            et = Time._from_groupdict(et.groupdict())
            ti = TimeInterval(start_time=st, end_time=et, lang=lang)

        # Populate self.datetimes with Datetimes objects
        for date in date_list:
            datetimes.append(
                DateTime(date=date, time=ti, lang=lang, text=text))
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

    def __init__(self, date_interval, time_interval, **kwargs):

        super(DateTimeInterval, self).__init__(**kwargs)
        self.date_interval = date_interval
        self.time_interval = time_interval

    def __iter__(self):
        """ Iteration over the start and end datetime. """
        for date in self.date_interval:
            yield date

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        time_interval = cls._set_time_interval(groupdict, lang)
        date_interval = cls._set_date_interval(groupdict, lang)
        return DateTimeInterval(date_interval, time_interval, **kwargs)

    @classmethod
    def _set_time_interval(self, groupdict, lang):
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
                out.append((i_start_datetime, i_start_datetime))

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

    def future(self, reference=datetime.date.today()):
        return self.end_datetime.future(reference)

    @property
    def rrulestr(self):
        """Return the ContinuousDatetimeInterval RRule string."""
        start_dt = self.start_datetime.to_python()
        start_time = start_dt.time()
        start_date = start_dt.date()
        end_dt = datetime.datetime.combine(
            self.end_datetime.to_python().date(),
            datetime.time(23, 59, 59))
        return makerrulestr(
            start_date, end_dt,
            interval=1, byhour=start_time.hour, byminute=start_time.minute)

    def to_db(self):
        """Export the ContinuousDatetimeInterval to a database-ready format."""
        return {
            'rrule': self.rrulestr,
            'duration': duration(start=self.start_datetime.to_python(),
                                 end=self.end_datetime.to_python()),
            'texts': self.text_to_db(),
            'continuous': True,
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

    def __init__(self, weekdays, start_datetime, end_datetime, **kwargs):
        super(WeekdayRecurrence, self).__init__(**kwargs)
        self.weekdays = weekdays
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

    def __eq__(self, other):
        """ Equality is based on the RFC syntax """
        return str(self) == str(other)

    def __str__(self):
        return self.rrulestr

    @classmethod
    def _from_groupdict(cls, groupdict, lang, **kwargs):
        groupdict = digit_to_int(groupdict)
        weekdays = cls._set_weekdays(groupdict, lang)
        start_datetime, end_datetime = cls._set_datetime_interval(
            groupdict, lang)
        return WeekdayRecurrence(weekdays, start_datetime, end_datetime, **kwargs)

    @classmethod
    def _set_weekdays(cls, groupdict, lang):
        """ Return the list of reccurent days index

        For example, if groupdict['weekdays'] == 'le lundi, mardi et mercredi',
        it returns [0, 1, 2]

        """
        return sorted([
            WEEKDAY[lang][day.group(0)] for day in
            re.finditer(
                r'|'.join(WEEKDAY[lang].keys()),
                groupdict['weekdays'].lower())])

    @classmethod
    def _set_datetime_interval(cls, groupdict, lang):
        """ Return the start and end date of the recurrence.

        If not specified, the default start date value is datetime.now().
        If not specified, the default end date value is one year after
        datetime.now().

        """
        if groupdict.get('date_interval') and groupdict.get('time_interval'):
            datetime_interval = DateTimeInterval._from_groupdict(
                groupdict,
                lang=lang).\
                to_python()
            start_datetime = datetime_interval[0][0]
            end_datetime = datetime_interval[-1][-1]

        elif groupdict.get('date_interval') and not groupdict.get('time_interval'):
            # normalize darte interval from regex matches
            date_interval = DateInterval._from_groupdict(
                groupdict,
                lang=lang,
                text=groupdict['date_interval'])
            # extract the start and end dates from date interval
            start_date = date_interval.start_date.to_python()
            end_date = date_interval.end_date.to_python()

            # Create datetimes from the start and end dates by associatng
            # each of them with a default time
            start_time = datetime.time(hour=0, minute=0, second=0)
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_time = datetime.time(hour=23, minute=59, second=59)
            end_datetime = datetime.datetime.combine(end_date, end_time)

        elif groupdict.get('time_interval') and not groupdict.get('date_interval'):
            # normalize darte interval from regex matches
            time_interval = TimeInterval._from_groupdict(
                groupdict,
                lang=lang,
                text=groupdict['time_interval'])
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

    @classmethod
    def _set_weekdays(cls, groupdict, lang):
        """ Return the list of reccurent days index

        Example: if 'start_day' == 'lundi' and 'end_day' == 'vendredi',
        the output is [0, 1, 2, 3, 4]

        """
        start_weekday = groupdict['start_weekday'].rstrip('s').lower()
        start_weekday_number = WEEKDAY[lang][start_weekday]
        end_weekday = groupdict['end_weekday'].rstrip('s').lower()
        end_weekday_number = WEEKDAY[lang][end_weekday]

        if start_weekday_number < end_weekday_number:
            return range(start_weekday_number, end_weekday_number + 1)
        else:
            return range(start_weekday_number, 7) + range(end_weekday_number + 1)


class AllWeekdayRecurrence(WeekdayRecurrence):

    """ Object in charge of the normalisation of a recurrence rule ocurring
        all days of the week

    """

    @classmethod
    def _set_weekdays(cls, groupdict, lang):
        return range(0, 7)
