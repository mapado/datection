# -*- coding: utf-8 -*-

import re
import datetime

from regex import *


def timepoint_factory(detector, data, **kwargs):
    """ Return the appropriate Timepoint childclass
        given the detector value.

    """
    kwargs.update({'timepoint': detector})
    if detector == 'date':
        return Date(data, **kwargs)
    elif detector == 'date_interval':
        return DateInterval(data, **kwargs)
    elif detector == 'time_interval':
        return TimeInterval(data, **kwargs)
    elif detector == 'datetime':
        return DateTime(data, **kwargs)
    elif detector == 'date_list':
        return DateList(data, **kwargs)
    elif detector == 'datetime_list':
        return DateTimeList(data, **kwargs)
    elif detector == 'datetime_interval':
        return DateTimeInterval(data, **kwargs)
    else:
        raise NotImplementedError(
            detector + " normalisation is not yet handled.")


class Timepoint(object):
    """ The mother class for all timepoint classes. """

    def __init__(self, data, **kwargs):
        """ Set all key/values in data and kwargs as instance arguments.

        All pure numeric strings are converted to int.
        All non-pure numeric strings are stripped.
        All non-string values are inserted as-is.

        """
        for k, v in data.items() + kwargs.items():
            if v:
                if isinstance(v, basestring):
                    if v.isdigit():  # numbers
                        self.__setattr__(k, int(v))
                    else:  # strings
                        self.__setattr__(k, v.strip())
                else:
                    self.__setattr__(k, v)
            else:
                self.__setattr__(k, v)

    def __eq__(self, other):
        return self._to_dict() == other._to_dict()

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(str(self._to_dict()))

    def serialize(self):
        """ Serialize the Timepoint object to a Python dict """
        d = self._to_dict()
        # the 'valid' and 'timepoint' members are only shown at the root level
        # not at children level, to avoid filling the JSON struct
        # with partial validity indicators
        d.update({'valid': self.valid, 'timepoint': self.timepoint})
        return d

    def to_sql(self):
        """ Default implementation of to_sql

        Return an empty list
        """
        return []

    def future(self, reference=None):
        """Return whether the timepoint is located in the future."""
        return False


class Date(Timepoint):
    """ A class representing a simple date.

    Examples:
    * le 15 février 2013
    * mardi 15 Mars
    * 31 janvier
    * 15/01/2013
    * 15/12/13

    """
    def __init__(self, data={}, year=None, month_name=None, month=None, day=None, **kwargs):
        super(Date, self).__init__(data, **kwargs)
        if year:
            self.year = year
        if month_name:
            self.month_name = month_name
        if day:
            self.day = day
        if month:
            self.month = month
        if not all([day, month, year]):
            self._serialize()

    def _serialize(self):
        """ Convert month name to serialized month number """
        if hasattr(self, 'lang'):
            if isinstance(self.month_name, basestring):  # string date
                # if month name is whole
                if self.month_name.lower() in MONTH[self.lang]:
                    self.month = MONTH[self.lang][self.month_name.lower()]
                # if month name is abbreviated
                elif self.month_name.lower() in SHORT_MONTH[self.lang]:
                    self.month = SHORT_MONTH[self.lang][self.month_name.lower()]
            elif isinstance(self.month_name, int):  # numeric date
                self.month = self.month_name
            else:
                self.month = None
        else:
            raise Warning(
                'A language must be given to Date constructor '
                'to be able to serialize the month name.')
        if len(str(self.year)) == 2:  # numeric date with shortened year format
            # ex xx/xx/12 --> xx/xx/2012
            # WARNING: if a past date is written in this format (ex: 01/06/78)
            # it is impossible to know if it references the year 1978 or 2078.
            # If the 2-digit date is less than 15 years in the future, we consider
            # that it takes place in our century, otherwise, it is considered as a past
            # date
            current_year = datetime.date.today().year
            century = int(str(current_year)[:2])
            if int(str(century) + str(self.year)) - current_year < 15:
                # if year is less than 15 years in the future, it is considered
                # a future date
                self.year = int(str(century) + str(self.year))
            else:
                # else, it is treated as a past date
                self.year = int(str(century - 1) + str(self.year))

    @property
    def valid(self):
        """ Returns whether the date exists. """
        if all([self.year, self.month, self.day]):
            try:  # check if date is valid
                datetime.date(year=self.year, month=self.month, day=self.day)
            except ValueError:
                return False
            else:
                return True
        else:
            return False

    def _to_dict(self):
        return {
            'day': self.day,
            'month': self.month,
            'year': self.year}

    def to_sql(self):
        start_datetime = datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=0,
            minute=0,
            second=0,
        )
        end_datetime = datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=23,
            minute=59,
            second=59,
        )
        return (start_datetime, end_datetime)

    def future(self, reference=datetime.date.today()):
        """Returns whether the Date is located in the future.

        The default time reference is the day of the method execution.

        """
        date = datetime.date(day=self.day, month=self.month, year=self.year)
        return date > reference


class DateList(Timepoint):
    """ A datelist contains several dates.

    Examples:
    * le 5, 6, 7 et 8 octobre 2013
    * mardi 5 et mercredi 15 Mars

    """
    def __init__(self, data={}, dates=None, **kwargs):
        """ Initialize the DateList object. """
        super(DateList, self).__init__(data, **kwargs)
        if dates:
            self.dates = dates
        else:
            self._serialize()

    def __iter__(self):
        """ Iterate over the dates in self.dates. """
        for date in self.dates:
            yield date

    def _serialize(self):
        """ Restore all missing date from dates in the date list.

        All dates (in the date list) with missing data will be given
        the corresponding data from the last date.

        Example: 5, 6 et 7 février 2013
        --> [5/02/2013, 6/02/2013, 7/02/2013]

        """
        # store all dates in self.dates list
        self.dates = []
        for date in re.finditer(TIMEPOINT_REGEX[self.lang]['_date_in_list'][0], self.date_list):
            self.dates.append(Date(date.groupdict(), text=date.group(0), lang=self.lang))
        # All dates without a year will inherit from the end date year
        end_date = self.dates[-1]
        if end_date.year:
            for date in self.dates[:-1]:
                if not date.year:
                    date.year = end_date.year
        # All dates without a month will inherit from the end date month/month_name
        if end_date.month:
            for date in self.dates[:-1]:
                if not date.month:
                    date.month = end_date.month
                if not date.month_name:
                    date.month_name = end_date.month_name

    @property
    def valid(self):
        """ Check that all dates in self.dates are valid. """
        return all([date.valid for date in self.dates])

    def _to_dict(self):
        return {
            'timepoint': 'date_list',
            'dates': [date._to_dict() for date in self.dates],
        }

    def to_sql(self):
        out = []
        for date in self.dates:
            start_datetime = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=0,
                minute=0,
                second=0,
            )
            end_datetime = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=23,
                minute=59,
                second=59,
            )
            out.append((start_datetime, end_datetime))
        return out

    def future(self, reference=datetime.date.today()):
        """Returns whether the DateList is located in the future.

        A DateList is considered future even if a part of its dates
        are future.

        The default time reference is the day of the method execution.

        """
        return any([d.future(reference) for d in self.dates])


class DateInterval(Timepoint):
    """ A class representing a date interval

    Examples:
    * du 5 au 15 octobre
    * 5-7 avril 2013

    """
    def __init__(self, data={}, start_date=None, end_date=None, **kwargs):
        super(DateInterval, self).__init__(data, **kwargs)
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        if not (start_date and end_date):
            self._serialize()

    def __iter__(self):
        """ Iteration through the self.dates list. """
        for date in [self.start_date, self.end_date]:
            yield date

    def _serialize(self):
        """ Restore all missing data and serialize the start and end date """
        # start year inherits from the end date year and month name
        if not self.start_year and self.end_year:
            self.start_year = self.end_year
        if not self.start_month_name and self.end_month_name:
            self.start_month_name = self.end_month_name

        # Create normalised start date of Date type
        if not hasattr(self, 'start_date'):
            self.start_date = Date(
                year=self.start_year,
                month_name=self.start_month_name,
                day=self.start_day,
                lang=self.lang)
        # create serialized end date of Date type
        if not hasattr(self, 'end_date'):
            self.end_date = Date(
                year=self.end_year,
                month_name=self.end_month_name,
                day=self.end_day,
                lang=self.lang)

    @property
    def valid(self):
        """ Check that start and end date are valid. """
        return all([self.start_date.valid, self.end_date.valid])

    def _to_dict(self):
        return {
            'start_date': self.start_date._to_dict(),
            'end_date': self.end_date._to_dict(),
        }

    def to_sql(self):
        """ convert for sql insert """
        start_datetime = datetime.datetime(
            year=self.start_date.year, month=self.start_date.month,
            day=self.start_date.day, hour=0, minute=0, second=0)
        end_datetime = datetime.datetime(
            year=self.end_date.year, month=self.end_date.month,
            day=self.end_date.day, hour=23, minute=59, second=59)
        return start_datetime, end_datetime

    def future(self, reference=datetime.date.today()):
        """Returns whether the DateInterval is located in the future.

        A DateInterval is considered future if its end date is located
        in the future.

        The default time reference is the day of the method execution.

        """
        return self.end_date.future(reference)


class Time(Timepoint):
    """ A class representing a time.

    Examples: 15h30, 15h, 8h, 08 h, 20:30

    """
    def __init__(self, data={}, hour=None, minute=None, **kwargs):
        super(Time, self).__init__(data, **kwargs)
        if hour:
            self.hour = hour
        if minute:
            self.minute = minute
        if not (hour and minute):
            self._serialize()

    def _serialize(self):
        """ Set self.minute to 0 if missing or null """
        # TODO: gérer le cas midi/minuit
        if not hasattr(self, 'minute') or not self.minute:
            self.minute = 0

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

    def _to_dict(self):
        return {
            'hour': self.hour,
            'minute': self.minute}


class TimeInterval(Timepoint):
    """ A class representing a simple time interval.

    Examples: 15h30-18h, de 15h à 18h

    """
    def __init__(self, data={}, start_time=None, end_time=None, **kwargs):
        super(TimeInterval, self).__init__(data, **kwargs)
        # store TimeInterval specific arguments
        if start_time:
            self.start_time = start_time
        if end_time:
            self.end_time = end_time
        if not(start_time):
            self._serialize()

    def __iter__(self):
        """ Iteration over the start and end time. """
        for time in [self.start_time, self.end_time]:
            yield time

    def _serialize(self):
        """ Convert the self.start_time and self.end_time into Time objects. """
        # normalization of self.start_time into a Time object
        st = re.search(TIMEPOINT_REGEX[self.lang]['_time'][0], self.start_time)
        self.start_time = Time(st.groupdict(), lang=self.lang)

        if self.end_time:
            # normalization of self.end_time into a Time object
            et = re.search(TIMEPOINT_REGEX[self.lang]['_time'][0], self.end_time)
            self.end_time = Time(et.groupdict(), lang=self.lang)

    @property
    def valid(self):
        """ Check that both self.start_time and self.end_time (if any) are valid. """
        if hasattr(self, 'end_time') and self.end_time:
            return all([self.start_time.valid, self.end_time.valid])
        else:
            return self.start_time.valid

    def _to_dict(self):
        if not hasattr(self, 'end_time') or not self.end_time:
            end_time = None
        elif self.end_time is not None:
            end_time = self.end_time._to_dict()
        return {
            'start_time': self.start_time._to_dict(),
            'end_time': end_time}


class DateTime(Timepoint):
    """ A datetime has a fixed date, and either a start time, or a time interval.

    Examples: lundi 15 mars à 15h30, le 8 octobre 2013 de 15h30 à 16h

    """
    def __init__(self, data={}, date=None, time=None, **kwargs):
        """ Initialize the DateTime object.

        ``date`` argument is of type ``Date``.
        ``time`` argument is of type ``Time``.
        """
        super(DateTime, self).__init__(data, **kwargs)
        if date:
            self.date = date
        if time:
            self.time = time
        if not (date and time):
            self._serialize()

    def _serialize(self):
        """ Convert date and time groupdicts into Date and TimeInterval objects.

        If date and/or time arguments were passed manually, they are considered
        as already converted.
        """
        if not hasattr(self, 'date'):
            for date_pattern in TIMEPOINT_REGEX[self.lang]['date']:
                d = re.search(date_pattern, self.text)
                if d:
                    self.date = Date(d.groupdict(), text=d.group(0), lang=self.lang)
                    break
        if not hasattr(self, 'time'):
            ti = re.search(TIMEPOINT_REGEX[self.lang]['time_interval'][0], self.text)
            self.time = TimeInterval(ti.groupdict(), text=ti.group(0), lang=self.lang)

    @property
    def valid(self):
        """ Checks that both self.time and self.date are valid. """
        return all([self.time.valid and self.date.valid])

    def _to_dict(self):
        return {
            'date': self.date._to_dict(),
            'time': self.time._to_dict()}

    def to_sql(self):
        """ Export Datetime to sql """
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
        else:
            end_datetime = start_datetime

        return (start_datetime, end_datetime)

    def future(self, reference=datetime.date.today()):
        """Return whether the datetime is located in the future.

        The default time reference is the day of the method execution.

        """
        return self.date.future(reference)


class DateTimeList(Timepoint):
    """ A datetime list refers to a specific timing for a list of dates.

    Examples:
    * le 5, 6, 7 décembre 2013 à 15h30
    * mardi 5 et mercredi 15 septembre de 15h30 à 19h15

    """
    def __init__(self, data={}, datetimes=None, **kwargs):
        super(DateTimeList, self).__init__(data, **kwargs)
        if datetimes:
            self.datetimes = datetimes
        else:
            self._serialize()

    def __iter__(self):
        """ Iteration over self.datetimes list """
        for dt in self.datetimes:
            yield dt

    def _serialize(self):
        """ Associate the time interval to each date in the date list.

        The normalization process will instanciate DateTime objects,
        and store them in self.datetimes.

        """
        self.datetimes = []

        # Extract the date list and create a DateList object
        for date_list_pattern in TIMEPOINT_REGEX[self.lang]['date_list']:
            dl = re.search(date_list_pattern, self.text)
            if dl:
                date_list = DateList(
                    dl.groupdict(), text=dl.group(0), lang=self.lang)
                break
        # extract the time interval and create a TimeInterval object
        ti = re.search(TIMEPOINT_REGEX[self.lang]['time_interval'][0], self.text).groupdict()
        time = TimeInterval(ti, lang=self.lang)

        # Populate self.datetimes with Datetimes objects
        for date in date_list:
            self.datetimes.append(DateTime(ti, date=date, time=time, lang=self.lang))

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

    def _to_dict(self):
        return {
            'datetimes': [dt._to_dict() for dt in self.datetimes]}

    def to_sql(self):
        """ Export Datetime to sql """
        out = []

        for dt in self.datetimes:
            start_datetime = datetime.datetime(
                year=dt.date.year,
                month=dt.date.month,
                day=dt.date.day,
                hour=dt.time.start_time.hour,
                minute=dt.time.start_time.minute,
                second=0
            )

            if dt.time.end_time:
                end_datetime = datetime.datetime(
                    year=dt.date.year,
                    month=dt.date.month,
                    day=dt.date.day,
                    hour=dt.time.end_time.hour,
                    minute=dt.time.end_time.minute,
                    second=0
                )
            else:
                end_datetime = start_datetime

            out.append((start_datetime, end_datetime))

        return out


class DateTimeInterval(Timepoint):
    """ A datetime interval refers to a interval of date, with specified time. """
    def __init__(self, data={}, date_interval=None, time_interval=None, **kwargs):

        super(DateTimeInterval, self).__init__(data, **kwargs)
        if date_interval:
            self.date_interval = date_interval
        if time_interval:
            self.time_interval = time_interval
        if not(date_interval and time_interval):
            self._serialize()

    def __iter__(self):
        """ Iteration over the start and end datetime. """
        for date in self.date_interval:
            yield date

    def _serialize(self):
        """ Normalisation of start and end datetimes."""
        self.time_interval = TimeInterval(
            {
                'start_time': self.start_time,
                'end_time': self.end_time
            },
            lang=self.lang)
        self.date_interval = DateInterval(
            re.search(
                TIMEPOINT_REGEX[self.lang]['date_interval'][0], self.text).groupdict(),
            lang=self.lang)

    @property
    def valid(self):
        """ Checks that start and end datetimes are valid. """
        return all([self.date_interval.valid, self.time_interval.valid])

    def _to_dict(self):
        return {
            'date_interval': self.date_interval._to_dict(),
            'time_interval': self.time_interval._to_dict()
        }

    def to_sql(self):
        """ Export DateTimeInterval to sql """
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
            i_end_datetime = datetime.datetime(
                year=i_date.year,
                month=i_date.month,
                day=i_date.day,
                hour=end_time.hour,
                minute=end_time.minute,
                second=0
            )

            out.append((i_start_datetime, i_end_datetime))

        return out

    def future(self, reference=datetime.date.today()):
        """Returns whether the DateTimeInterval is located in the future.

        A DateTimeInterval is considered future if its end date is located
        in the future.

        The default time reference is the day of the method execution.

        """
        return self.date_interval.end_date.future(reference)
