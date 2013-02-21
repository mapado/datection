# -*- coding: utf8 -*-

import re
import datetime
import json

from regex import *


def timepoint_factory(detector, data, **kwargs):
    """ Return the appropriate Timepoint childclass
        given the detector value.

    """
    detector = detector.replace('numeric_', '')  # numeric date is a date
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

    def __repr__(self):
        return '%s: %s' % (self.__class__, self.text)

    def __eq__(self, other):
        if isinstance(other, Timepoint):
            return self.to_dict() == other.to_dict()
        else:
            raise TypeError(other, "must inherit from the Timepoint class")

    def __ne__(self, other):
        return not self == other

    def to_json(self, **kwargs):
        """ Serialize the Timepoint object to JSON format """
        d = self.to_dict()
        # the 'valid' and 'timepoint' members are only shown at the root level
        # not at children level, to avoid filling the JSON struct
        # with partial validity indicators
        d.update({'valid': self.valid, 'timepoint': self.timepoint})
        return json.dumps(d, **kwargs)


class Date(Timepoint):
    """ A class representing a simple date.

    Examples:
    * le 15 février 2013
    * mardi 15 Mars
    * 31 janvier
    * 15/01/2013
    * 15/12/13
    """

    def __init__(self, data, year=None, month_name=None, day=None, **kwargs):
        super(Date, self).__init__(data, **kwargs)
        if year:
            self.year = year
        if month_name:
            self.month_name = month_name
        if day:
            self.day = day
        self._normalize()

    def __repr__(self):
        """ Print the date using the mm/dd/yyy format.

        All missing data will be replaced by '?'.

        """
        day = self.day or '??'
        month = self.month or '??'
        year = self.year or '????'
        return '%s/%s/%s' % (str(day), str(month), str(year))

    def _normalize(self):
        """ Convert month name to normalized month number """
        if hasattr(self, 'lang'):
            if isinstance(self.month_name, basestring):  # string date
                # if month name is whole
                if self.month_name.lower() in MONTH_VALUE[self.lang]:
                    self.month = MONTH_VALUE[self.lang][self.month_name.lower()]
                # if month name is abbreviated
                elif self.month_name.lower() in SHORT_MONTH_VALUE[self.lang]:
                    self.month = SHORT_MONTH_VALUE[self.lang][self.month_name.lower()]
            elif isinstance(self.month_name, int):  # numeric date
                self.month = self.month_name
            else:
                self.month = None
        else:
            raise Warning('A language must be given to Date constructor '
                        'to be able to normalize the month name.')
        if len(str(self.year)) == 2:  # numeric date with shortened year format
            # ex xx/xx/12 --> xx/xx/2012
            self.year = int(str(datetime.date.today().year)[:2] + str(self.year))

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

    def to_dict(self):
        return {
            'day': self.day,
            'month': self.month,
            'year': self.year}


class DateList(Timepoint):
    """ A datelist contains several dates.

    Examples:
    * le 5, 6, 7 et 8 octobre 2013
    * mardi 5 et mercredi 15 Mars

    """
    def __init__(self, data, dates=None, **kwargs):
        """ Initialize the DateList object. """
        super(DateList, self).__init__(data, **kwargs)
        if dates:
            self.dates = dates
        self._normalize()


    def __iter__(self):
        """ Iterate over the dates in self.dates. """
        for date in self.dates:
            yield date

    def _normalize(self):
        """ Restore all missing date from dates in the date list.

        All dates (in the date list) with missing data will be given
        the corresponding data from the last date.

        Example: 5, 6 et 7 février 2013
        --> [5/02/2013, 6/02/2013, 7/02/2013]

        """
        # store all dates in self.dates list
        self.dates = []
        for date in re.finditer(TIMEPOINT_REGEX[self.lang]['_date_in_list'], self.date_list):
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

    def to_dict(self):
        return {
            'timepoint': 'date_list',
            'dates': [date.to_dict() for date in self.dates],
            }


class DateInterval(Timepoint):
    """ A class representing a date interval

    Examples:
    * du 5 au 15 octobre
    * 5-7 avril 2013

    """
    def __init__(self, data, start_date=None, end_date=None, **kwargs):
        super(DateInterval, self).__init__(data, **kwargs)
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        self._normalize()

    def __repr__(self):
        return '%s: %s-%s' % (self.__class__, self.start_date, self.end_date)

    def __iter__(self):
        """ Iteration through the self.dates list. """
        for date in [self.start_date, self.end_date]:
            yield date

    def _normalize(self):
        """ Restore all missing data and normalize the start and end date """
        # start year inherits from the end date year and month name
        if not self.start_year and self.end_year:
            self.start_year = self.end_year
        if not self.start_month_name and self.end_month_name:
            self.start_month_name = self.end_month_name

        # Create normalised start date of Date type
        if not hasattr(self, 'start_date'):
            self.start_date = Date({}, year=self.start_year,
                                        month_name=self.start_month_name,
                                        day=self.start_day,
                                        lang=self.lang)
        # create normalized end date of Date type
        if not hasattr(self, 'end_date'):
            self.end_date = Date({}, year=self.end_year,
                                        month_name=self.end_month_name,
                                        day=self.end_day,
                                        lang=self.lang)

    @property
    def valid(self):
        """ Check that start and end date are valid. """
        return all([self.start_date.valid, self.end_date.valid])

    def to_dict(self):
        return {
        'start_date': self.start_date.to_dict(),
        'end_date': self.end_date.to_dict(),
        }


class Time(Timepoint):
    """ A class representing a time.

    Examples: 15h30, 15h, 8h, 08 h, 20:30

    """
    def __init__(self, data, hour=None, minute=None, **kwargs):
        super(Time, self).__init__(data, **kwargs)
        if hour:
            self.hour = hour
        if minute:
            self.minute = minute
        self._normalize()

    def __repr__(self):
        """ Print with HHhmm format """
        if len(str(self.minute)) == 1:
            minute = '0' + str(self.minute)
        else:
            minute = str(self.minute)
        return '%dh%s' % (self.hour, minute)

    def _normalize(self):
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

    def to_dict(self):
        return {
            'hour': self.hour,
            'minute': self.minute}


class TimeInterval(Timepoint):
    """ A class representing a simple time interval.

    Examples: 15h30-18h, de 15h à 18h

    """
    def __init__(self, data, start_time=None, end_time=None, **kwargs):
        super(TimeInterval, self).__init__(data, **kwargs)
        # store TimeInterval specific arguments
        if start_time:
            self.start_time = start_time
        if end_time:
            self.end_time = end_time
        self._normalize()

    def __repr__(self):
        end_time = self.end_time or ''
        return '%s-%s' % (self.start_time, self.end_time)

    def __iter__(self):
        """ Iteration over the start and end time. """
        for time in [self.start_time, self.end_time]:
            yield time

    def _normalize(self):
        """ Convert the self.start_time and self.end_time into Time objects. """
        # normalization of self.start_time into a Time object
        st = re.search(TIMEPOINT_REGEX[self.lang]['_time'], self.start_time)
        self.start_time = Time(st.groupdict(), lang=self.lang)

        if self.end_time:
            # normalization of self.end_time into a Time object
            et = re.search(TIMEPOINT_REGEX[self.lang]['_time'], self.end_time)
            self.end_time = Time(et.groupdict(), lang=self.lang)

    @property
    def valid(self):
        """ Check that both self.start_time and self.end_time (if any) are valid. """
        if self.end_time:
            return all([self.start_time.valid, self.end_time.valid])
        else:
            return self.start_time.valid

    def to_dict(self):
        if not self.end_time:
            end_time = None
        else:
            end_time = self.end_time.to_dict()
        return {
            'start_time': self.start_time.to_dict(),
            'end_time': end_time}


class DateTime(Timepoint):
    """ A datetime has a fixed date, and either a start time, or a time interval.

    Examples: lundi 15 mars à 15h30, le 8 octobre 2013 de 15h30 à 16h

    """
    def __init__(self, data, date=None, time=None, **kwargs):
        """ Initialize the DateTime object.

        ``date`` argument is of type ``Date``.
        ``time`` argument is of type ``Time``.
        """
        super(DateTime, self).__init__(data, **kwargs)
        if date:
            self.date = date
        if time:
            self.time = time
        self._normalize()

    def __repr__(self):
        return '%s: %s:%s' % (self.__class__, self.date, self.time)

    def _normalize(self):
        """ Convert date and time groupdicts into Date and TimeInterval objects.

        If date and/or time arguments were passed manually, they are considered
        as already converted.
        """
        if not hasattr(self, 'date'):
            d = re.search(TIMEPOINT_REGEX[self.lang]['date'], self.text)
            self.date = Date(d.groupdict(), text=d.group(0), lang=self.lang)
        if not hasattr(self, 'time'):
            ti = re.search(TIMEPOINT_REGEX[self.lang]['time_interval'], self.text)
            self.time = TimeInterval(ti.groupdict(), text=ti.group(0), lang=self.lang)

    @property
    def valid(self):
        """ Checks that both self.time and self.date are valid. """
        return all([self.time.valid and self.date.valid])

    def to_dict(self):
        return {
            'date': self.date.to_dict(),
            'time': self.time.to_dict()}


class DateTimeList(Timepoint):
    """ A datetime list refers to a specific timing for a list of dates.

    Examples:
    * le 5, 6, 7 décembre 2013 à 15h30
    * mardi 5 et mercredi 15 septembre de 15h30 à 19h15

    """
    def __init__(self, data, **kwargs):
        super(DateTimeList, self).__init__(data, **kwargs)
        self._normalize()

    def __iter__(self):
        """ Iteration over self.datetimes list """
        for dt in self.datetimes:
            yield dt

    def _normalize(self):
        """ Associate the time interval to each date in the date list.

        The normalization process will instanciate DateTime objects,
        and store them in self.datetimes.

        """
        self.datetimes = []

        # Extract the date list and create a DateList object
        dl = re.search(TIMEPOINT_REGEX[self.lang]['date_list'], self.text)
        date_list = DateList(
            dl.groupdict(), text=dl.group(0),lang=self.lang)
        # extract the time interval and create a TimeInterval object
        ti = re.search(TIMEPOINT_REGEX[self.lang]['time_interval'], self.text).groupdict()
        time = TimeInterval(ti, lang=self.lang)

        # Populate self.datetimes with Datetimes objects
        for date in date_list:
            self.datetimes.append(DateTime(ti, date=date, time=time, lang=self.lang))

    @property
    def valid(self):
        """ Check the validity of each datetime in self.datetimes. """
        return all([datetime.valid for datetime in self.datetimes])

    def to_dict(self):
        return {
            'datetimes': [dt.to_dict() for dt in self.datetimes]}


class DateTimeInterval(Timepoint):
    """ A datetime interval refers to a interval of date, with specified time. """
    def __init__(self, data, **kwargs):
        super(DateTimeInterval, self).__init__(data, **kwargs)
        self._normalize()

    def __repr__(self):
        return '%s: %s-%s: %s' % (self.__class__, self.start_datetime.date,
                                    self.end_datetime.date, self.start_datetime.time)

    def __iter__(self):
        """ Iteration over the start and end datetime. """
        for time in [self.start_datetime, self.end_datetime]:
            yield time


    def _normalize(self):
        """ Normalisation of start and end datetimes."""
        ti = TimeInterval({'start_time': self.start_time, 'end_time': self.end_time},
                            lang=self.lang)
        # normalized start date and end date
        sd, ed = DateInterval(
            re.search(
                TIMEPOINT_REGEX[self.lang]['date_interval'], self.text).groupdict(),
            lang=self.lang)
        self.start_datetime = DateTime({},
                                    date=sd,
                                    time=ti,
                                    lang=self.lang)
        self.end_datetime = DateTime({},
                                    date=ed,
                                    time=ti,
                                    day=self.end_day,
                                    lang=self.lang)

    @property
    def valid(self):
        """ Checks that start and end datetimes are valid. """
        return all([self.start_datetime.valid, self.end_datetime.valid])

    def to_dict(self):
        return {
        'start_datetime': self.start_datetime.to_dict(),
        'end_datetime': self.end_datetime.to_dict()}


# class Recurrence(Timepoint):
#     """ A class handling recurrent timepoints. """

#     def __init__(self, data, **kwargs):
#         super(Recurrence, self).__init__(data, **kwargs)
#         self._normalize()

#     def _normalize(self):
#         """ Convert the weekday_name in weekday number."""
#         if self.start_weekday_name:
#             # whole weekday name
#             if self.start_weekday_name in WEEKDAY_VALUE[self.lang]:
#                 self.weekday = WEEKDAY_VALUE[self.lang][self.start_weekday_name]
#             elif self.start_weekday_name in SHORT_WEEKDAY_VALUE:
#                 self.weekday = SHORT_WEEKDAY_VALUE[self.lang][self.start_weekday_name]
