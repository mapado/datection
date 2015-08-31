# -*- coding: utf-8 -*-

"""
Module in charge of transforming a rrule + duraction object into the shortest
human-readable string possible.

"""

import calendar
import datetime
import locale as _locale
import re
import itertools

from functools import wraps
from collections import defaultdict
from collections import namedtuple

from datection.models import DurationRRule
from datection.utils import cached_property
from datection.utils import get_current_date
from datection.timepoint import DAY_START
from datection.timepoint import DAY_END
from datection.lang import DEFAULT_LOCALES
from datection.lang import getlocale


locale = 'fr_FR.UTF8'

FormatterTuple = namedtuple("FormatterTuple", ["formatter", "display_args"])


def get_date(d):
    """Return a date object, given a datetime or a date."""
    return d.date() if isinstance(d, datetime.datetime) else d


def get_time(d):
    """Return a time object, given a datetime or a time."""
    return d.time() if isinstance(d, datetime.datetime) else d


def get_drr(drr):
    """Return a DurationRRule object given a dict or a DurationRRule."""
    return DurationRRule(drr) if isinstance(drr, dict) else drr


def all_day(start, end):
    """Return True if the start/end bounds correspond to an entie day."""
    start_time, end_time = get_time(start), get_time(end)
    return (start_time == datetime.time(0, 0)
            and end_time == datetime.time(23, 59))


def hash_same_date_pattern(time_group):
    """ Get hash with unique string for pattern with same date

        :time_group: [{'start': datetime(), 'end': datetime()},]
        :return: unique string for pattern with same date
    """
    return "|".join(["{} {}".format(
        tp['start'].date(),
        tp['end'].date()
    ) for tp in time_group])


def postprocess(strip=True, trim_whitespaces=True, lstrip_pattern=None,
                capitalize=False, rstrip_pattern=None):
    """Post processing text formatter decorator."""
    def wrapped_f(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            text = func(*args, **kwargs)
            text = text.replace(', ,', ', ')
            if trim_whitespaces:
                text = re.sub(r'\s+', ' ', text)
            if lstrip_pattern:
                text = text.lstrip(lstrip_pattern)
            if rstrip_pattern:
                text = text.rstrip(rstrip_pattern)
            if strip:
                text = text.strip()
            if capitalize:
                text = text.capitalize()
            return text
        return wrapper
    return wrapped_f


def groupby_consecutive_dates(dt_intervals):
    """Group the members of dt_intervals by consecutivity

    Example:
    Input: [01/02/2013, 03/02/2013, 04/02/2013, 06/02/2013]
    Output: [[01/02/2013], [03/02/2013, 04/02/2013], [06/02/2013]]

    """
    conseq = []
    start = 0
    for i, inter in enumerate(dt_intervals):
        if i != len(dt_intervals) - 1:  # if inter is not the last item
            if consecutives(inter, dt_intervals[i + 1]):
                continue
            else:
                conseq.append(dt_intervals[start: i + 1])
                start = i + 1  # next group starts at next item
        else:  # special case of the last item in the list: border effect
            # we text the consecutivity with the previous inter
            if consecutives(inter, dt_intervals[i - 1]):
                # add last item to last group
                conseq.append(dt_intervals[start: i + 1])
            else:
                # create new group with only last inter
                conseq.append([inter])
    return sorted(conseq, key=lambda item: item[0]['start'])


def groupby_time(dt_intervals):
    """ Group the dt_intervals list by start/end time

    All the schedules with the same start/end time are grouped together
    and sorted in increasing order.

    """
    times = defaultdict(list)
    for inter in dt_intervals:
        start_time, end_time = inter['start'].time(), inter['end'].time()
        grp = '%s-%s' % (start_time.isoformat(), end_time.isoformat())
        times[grp].append(inter)  # group dates by time
    return [
        sorted(group, key=lambda item: item['start'])
        for group in times.values()]


def groupby_date(dt_intervals):
    """ Group the dt_intervals list by start date

    All the schedules with the same start time are grouped together
    and sorted in increasing order.

    """
    dates = defaultdict(list)
    for inter in dt_intervals:
        start_date = inter['start'].date()
        dates[start_date.isoformat()].append(inter)  # group dates by time
    return [
        sorted(group, key=lambda item: item['start'])
        for group in dates.values()]


def consecutives(date1, date2):
    """ If two dates are consecutive, return True, else False"""
    date1 = date1['start'].date()
    date2 = date2['start'].date()
    return (date1 + datetime.timedelta(days=1) == date2
            or date1 + datetime.timedelta(days=-1) == date2)


def get_shortest(item1, item2):
    """Return item with shortest lenght"""
    return item1 if len(item1) < len(item2) else item2


def to_start_end_datetimes(schedule, start_bound=None, end_bound=None):
    """Convert each schedule member (DurationRRule instance) to a dict
    of start/end datetimes.

    """
    out = []
    for drr in schedule:
        for start_date in drr:
            hour = drr.rrule.byhour[0] if drr.rrule.byhour else 0
            minute = drr.rrule.byminute[0] if drr.rrule.byminute else 0
            start = datetime.datetime.combine(
                start_date,
                datetime.time(hour, minute))

            end = datetime.datetime.combine(
                start_date,
                datetime.time(hour, minute)) + \
                datetime.timedelta(minutes=drr.duration)

            # Patch the after midnight case only if start_date is on another
            # day, and only if the date if before 5:00 am.
            # Concrete case : "Du 1 au 2 de 22h à 4h"
            if end.hour <= 5:
                end += datetime.timedelta(days=-1)

            # convert the bounds to datetime if dates were given
            if isinstance(start_bound, datetime.date):
                start_bound = datetime.datetime.combine(start_bound, DAY_START)
            if isinstance(end_bound, datetime.date):
                end_bound = datetime.datetime.combine(
                    end_bound, DAY_END)

            # filter out all start/end pairs outside of given boundaries
            if ((start_bound and end_bound
                    and start >= start_bound and end <= end_bound)
                    or (start_bound and not end_bound and start >= start_bound)
                    or (not start_bound and end_bound and end <= end_bound)
                    or (not start_bound and not end_bound)):
                out.append({'start': start, 'end': end})
    return out


class NoFutureOccurence(Exception):

    """Exception raised when a DurationRRule does not yield future dates."""
    pass


class BaseFormatter(object):

    """Base class for all schedule formatters."""

    def __init__(self):
        self.language_code, self.encoding = locale.split('.')
        self.templates = None

    @cached_property
    def translations(self):
        """Return a translation dict using the current locale language"""
        lang = self.language_code.split('_')[0]
        mod = __import__('datection.data.' + lang, fromlist=['data'])
        return mod.TRANSLATIONS

    def _(self, key):
        """Return the translation of the key in the instance language."""
        return self.translations[self.language_code][key]

    def prevert_list(self, list_to_fmt):
        """ String list of item concat with simple quote
            then final 'and' before last item
        """
        return '%s %s %s' % (
            ', '.join(list_to_fmt[:-1]),  self._('and'), list_to_fmt[-1])

    def get_template(self, key=None):
        """Return the template corresponding to the instance language
        and key.

        """
        if key is None:
            return self.templates[self.language_code]
        return self.templates[self.language_code][key]

    @staticmethod
    def day_name(weekday_index):
        """Return the weekday name associated wih the argument index
        using the current locale.

        """
        with TemporaryLocale(_locale.LC_TIME, locale):
            return calendar.day_name[weekday_index].decode('utf-8')

    @staticmethod
    def deduplicate(schedule):
        """Remove any duplicate DurationRRule in the schedule."""
        # Note: list(set(schedule)) does not keep the order in that case
        out = []
        for item in schedule:
            if item not in out:
                out.append(item)
        return out


class NextDateMixin(object):

    @cached_property
    def regrouped_dates(self):
        """Convert self.schedule to a start / end datetime list and filter
        out the obtained values outside of the (self.start, self.end)
        datetime range

        """
        if not hasattr(self, 'start'):
            start = get_current_date()
        else:
            start = self.start or get_current_date()  # filter out passed dates

        end = self.end if hasattr(self, 'end') else None
        dtimes = to_start_end_datetimes(self.schedule, start, end)
        # group the filtered values by date
        dtimes = sorted(groupby_date(dtimes))
        return dtimes

    def next_occurence(self):
        """Return the next date, as a start/end datetime dict."""
        if self.regrouped_dates:
            return self.regrouped_dates[0][0]

    def other_occurences(self):
        """Return all dates (bu the next), as a start/end datetime dict."""
        return len(self.regrouped_dates) > 1


class NextChangesMixin(object):

    """Add a next_changes method to output the datetime when the
    display value will change.

    """

    def next_changes(self):
        """ output the value when the display will change
        """
        if not(hasattr(self, 'next_occurence')):
            return None

        current_date = datetime.datetime.combine(
            get_current_date(), datetime.time())

        next_occurence = self.next_occurence()
        if not next_occurence or 'start' not in next_occurence:
            return None

        start = next_occurence['start']
        current_delta = start - current_date

        if current_delta < datetime.timedelta(0):  # past
            return None
        elif current_delta < datetime.timedelta(1):  # today
            return start
        elif current_delta < datetime.timedelta(2):  # tomorrow
            delta = datetime.timedelta(days=0)
        elif current_delta < datetime.timedelta(7):  # this week
            delta = datetime.timedelta(days=1)
        else:  # in more than in a week
            delta = datetime.timedelta(days=6)

        next_changes = start - delta
        next_changes = next_changes.combine(
            next_changes.date(), datetime.time())

        return next_changes


class DateFormatter(BaseFormatter):

    """Formats a date into using the current locale."""

    def __init__(self, date):
        super(DateFormatter, self).__init__()
        self.date = get_date(date)
        self.templates = {
            'fr_FR': {
                'all': u'{prefix} {dayname} {day} {month} {year}',
                'no_year': u'{prefix} {dayname} {day} {month}',
                'no_year_no_month': u'{prefix} {dayname} {day}',
            },
            'en_US': {
                'all': u'{prefix} {dayname} {day} of {month} {year}',
                'no_year': u'{prefix} {dayname} {day} of {month}',
                'no_year_no_month': u'{prefix} {dayname} {day}',
            }
        }

    def format_day(self):
        """Format the date day using the current locale."""
        if self.language_code == 'fr_FR':
            return u'1er' if self.date.day == 1 else unicode(self.date.day)
        elif self.language_code in ['en_US', 'en_GB']:
            if 4 <= self.date.day <= 20 or 24 <= self.date.day <= 30:
                suffix = 'th'
            else:
                suffix = ['st', 'nd', 'rd'][self.date.day % 10 - 1]
            return u'%d%s' % (self.date.day, suffix)

    def format_dayname(self, abbrev=False):
        """Format the date day using the current locale."""
        with TemporaryLocale(_locale.LC_TIME, locale):
            if abbrev:
                return self.date.strftime('%a')
            return self.date.strftime('%A')

    def format_month(self, abbrev=False):
        """Format the date month using the current locale."""
        with TemporaryLocale(_locale.LC_TIME, locale):
            if abbrev:
                return self.date.strftime('%b')
            return self.date.strftime('%B')

    def format_year(self, abbrev=False, force=False):
        """Format the date year using the current locale.

        The year will be formatted if force=True or if the date occurs
        in more than 6 months (6 * 30 days).
        Otherwise, return u''.

        If abbrev = True, only the abbreviated version of the year will
        be returned (ex: 13 instead of 2013).

        """
        if (
                force
                or self.date.year < get_current_date().year
                or (self.date - get_current_date()).days > 6 * 30
        ):
            with TemporaryLocale(_locale.LC_TIME, locale):
                if abbrev:
                    return self.date.strftime('%y')
                return self.date.strftime('%Y')
        else:
            return u''

    def format_all_parts(
        self, include_dayname, abbrev_dayname,
        abbrev_monthname, abbrev_year, prefix, force_year=False
    ):
        """Formats the date in the current locale."""
        template = self.get_template('all')
        if include_dayname or abbrev_dayname:
            dayname = self.format_dayname(abbrev_dayname)
        else:
            dayname = u''
        day = self.format_day()
        month = self.format_month(abbrev_monthname).decode('utf-8')
        if force_year:
            year = self.format_year(abbrev_year, force=True)
        else:
            year = self.format_year(abbrev_year)
        fmt = template.format(
            prefix=prefix, dayname=dayname, day=day, month=month, year=year)
        fmt = re.sub(r'\s+', ' ', fmt)
        return fmt

    def format_no_year(self, include_dayname, abbrev_dayname, abbrev_monthname,
                       prefix):
        """Formats the date in the current locale, omitting the year."""
        template = self.get_template('no_year')
        if include_dayname or abbrev_dayname:
            dayname = self.format_dayname(abbrev_dayname)
        else:
            dayname = u''
        day = self.format_day()
        month = self.format_month(abbrev_monthname).decode('utf-8')
        fmt = template.format(
            prefix=prefix, dayname=dayname, day=day, month=month)
        fmt = re.sub(r'\s+', ' ', fmt)
        return fmt

    def format_no_month_no_year(self, include_dayname, abbrev_dayname, prefix):
        """Formats the date in the current locale, omitting the month
        and year.

        """
        template = self.get_template('no_year_no_month')
        if include_dayname or abbrev_dayname:
            dayname = self.format_dayname(abbrev_dayname)
        else:
            dayname = u''
        day = self.format_day()
        fmt = template.format(prefix=prefix, dayname=dayname, day=day)
        fmt = re.sub(r'\s+', ' ', fmt)
        return fmt

    @postprocess()
    def display(self, include_dayname=False, abbrev_dayname=False,
                include_month=True, abbrev_monthname=False, include_year=True,
                abbrev_year=False, reference=None, abbrev_reference=False,
                prefix=False, force_year=False):
        """Format the date using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If include_month is True, the month will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If include_year is True, the year will be included (if the date
        formatter 'decides' that the year should be displayed.
        If force_year is True, the year will be displayed no matter what.
        If abbrev_year is True, a 2 digit year format will be used.
        If a reference date is given, and it is at least 6 days before
        the formatted date, a relativistic expression will be used (today,
            tomorrow, this {weekday})

        """
        if force_year and not include_year:
            raise ValueError(
                "force_year can't be True if include_year is False")
        if reference:
            if self.date == reference:
                if abbrev_reference:
                    return self._('today_abbrev')
                else:
                    return self._('today')
            elif self.date == reference + datetime.timedelta(days=1):
                return self._('tomorrow')
            elif reference < self.date <= reference + datetime.timedelta(days=6):
                # if d is next week, use its weekday name
                return u'%s %s' % (
                    self._('this'),
                    self.format_dayname(abbrev_dayname))

        prefix = self._('the') if prefix else u''
        if include_month and include_year:
            return self.format_all_parts(
                include_dayname,
                abbrev_dayname,
                abbrev_monthname,
                abbrev_year,
                prefix,
                force_year)
        elif include_month and not include_year:
            return self.format_no_year(
                include_dayname,
                abbrev_dayname,
                abbrev_monthname,
                prefix)
        else:
            return self.format_no_month_no_year(
                include_dayname,
                abbrev_dayname,
                prefix)


class DateIntervalFormatter(BaseFormatter):

    """Formats a date interval using the current locale."""

    def __init__(self, start_date, end_date):
        super(DateIntervalFormatter, self).__init__()
        self.start_date = get_date(start_date)
        self.end_date = get_date(end_date)
        self.templates = {
            'fr_FR': u'du {start_date} au {end_date}',
            'en_US': u'{start_date} - {end_date}',
        }

    def same_day_interval(self):
        """Return True if the start and end datetime have the same date,
        else False.

        """
        return self.start_date == self.end_date

    def same_month_interval(self):
        """Return True if the start and end date have the same month
        and the same year, else False.

        """
        # To be on the same month means that both date have the same
        # month *in the same year*, not just the same monthname!
        if not self.same_year_interval():
            return False
        return self.start_date.month == self.end_date.month

    def same_year_interval(self):
        """Return True if the start and end date have the same year,
        else False.

        """
        return self.start_date.year == self.end_date.year

    def has_two_consecutive_days(self):
        return self.start_date + datetime.timedelta(days=1) == self.end_date

    def format_same_month(self, *args, **kwargs):
        """Formats the date interval when both dates have the same month."""
        template = self.get_template()
        start_kwargs = kwargs.copy()
        start_kwargs['force_year'] = False
        start_kwargs['include_month'] = False
        start_kwargs['include_year'] = False
        start_date_fmt = DateFormatter(
            self.start_date).display(*args, **start_kwargs)
        end_date_fmt = DateFormatter(self.end_date).display(*args, **kwargs)
        return template.format(start_date=start_date_fmt, end_date=end_date_fmt)

    def format_same_year(self, *args, **kwargs):
        """Formats the date interval when both dates have the same year."""
        template = self.get_template()
        start_kwargs = kwargs.copy()
        start_kwargs['force_year'] = False
        start_kwargs['include_year'] = False
        start_date_fmt = DateFormatter(
            self.start_date).display(*args, **start_kwargs)
        end_date_fmt = DateFormatter(self.end_date).display(*args, **kwargs)
        return template.format(start_date=start_date_fmt, end_date=end_date_fmt)

    def format_two_consecutive_days(self, *args, **kwargs):
        return DateListFormatter([
            self.start_date, self.end_date]).display(*args, **kwargs)

    @postprocess()
    def display(self, abbrev_reference=False, *args, **kwargs):
        """Format the date interval using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If abbrev_year is True, a 2 digit year format will be used.

        """
        if self.same_day_interval():
            kwargs['prefix'] = True
            return DateFormatter(self.start_date).display(
                abbrev_reference=abbrev_reference, *args, **kwargs)
        elif self.has_two_consecutive_days():
            pkwargs = {'include_dayname': kwargs.get('include_dayname') }
            return self.format_two_consecutive_days(**pkwargs)
        elif self.same_month_interval():
            return self.format_same_month(*args, **kwargs)
        elif self.same_year_interval():
            return self.format_same_year(*args, **kwargs)
        else:
            template = self.get_template()
            kwargs['force_year'] = True
            start_date_fmt = DateFormatter(self.start_date).\
                display(abbrev_reference, *args, **kwargs)
            end_date_fmt = DateFormatter(self.end_date).\
                display(abbrev_reference, *args, **kwargs)
            fmt = template.format(
                start_date=start_date_fmt, end_date=end_date_fmt)
            return fmt


class DateListFormatter(BaseFormatter):

    """Formats a date list using the current locale."""

    def __init__(self, date_list):
        super(DateListFormatter, self).__init__()
        self.date_list = [get_date(d) for d in date_list]
        self.templates = {
            'fr_FR': u'les {date_list} et {last_date}',
            'en_US': u'{date_list} and {last_date}',
        }

    @postprocess()
    def display(self, *args, **kwargs):
        """Format a date list using the current locale."""
        if len(self.date_list) == 1:
            kwargs['prefix'] = True
            return DateFormatter(self.date_list[0]).display(*args, **kwargs)
        include_dayname = kwargs.get('include_dayname')
        template = self.get_template()
        date_list = ', '.join([DateFormatter(d).display(
            include_month=False, include_year=False, include_dayname=include_dayname)
            for d in self.date_list[:-1]])
        last_date = DateFormatter(self.date_list[-1]).display(*args, **kwargs)
        fmt = template.format(date_list=date_list, last_date=last_date)
        return fmt


class TimeFormatter(BaseFormatter):

    """Formats a time using the current locale."""

    def __init__(self, time):
        super(TimeFormatter, self).__init__()
        self.time = get_time(time)
        self.templates = {
            'fr_FR': u'{prefix} {hour} h {minute}',
            'en_US': u'{prefix} {hour}:{minute}',
        }

    def format_hour(self):
        """Format the time hour using the current locale."""
        return unicode(self.time.hour)

    def format_minute(self):
        """Format the time hour using the current locale."""
        if self.time.minute == 0:
            if self.language_code == 'fr_FR':
                return u''
            elif self.language_code in ['en_US', 'en_GB']:
                return u'00'
        with TemporaryLocale(_locale.LC_TIME, locale):
            return self.time.strftime('%M')

    def display(self, prefix=False):
        """Format the time using the template associated with the locale

        """
        if self.time == datetime.time(0, 0):
            return self._('midnight')
        template = self.get_template()
        hour = self.format_hour()
        minute = self.format_minute()
        prefix = self._('at') if prefix else ''
        fmt = template.format(prefix=prefix, hour=hour, minute=minute)
        fmt = fmt.strip()
        return fmt


class TimeIntervalFormatter(BaseFormatter):

    """Formats a time interval using the current locale."""

    def __init__(self, start_time, end_time):
        super(TimeIntervalFormatter, self).__init__()
        self.start_time = get_time(start_time)
        self.end_time = get_time(end_time) if end_time else None
        self.templates = {
            'fr_FR': {
                'interval': u'de {start_time} à {end_time}',
                'single_time': u'à {time}',
            },
            'en_US': {
                'interval': u'{start_time} - {end_time}',
                'single_time': u'at {time}',
            },
        }

    def display(self, prefix=False):
        """Format the time using the template associated with the locale

        """
        if self.start_time == self.end_time or self.end_time is None:
            return TimeFormatter(self.start_time).display(prefix)
        elif all_day(self.start_time, self.end_time):
            return u''
        template = self.get_template('interval')
        start_time_fmt = TimeFormatter(self.start_time).display()
        end_time_fmt = TimeFormatter(self.end_time).display()
        fmt = template.format(
            start_time=start_time_fmt, end_time=end_time_fmt)
        return fmt


class DatetimeFormatter(BaseFormatter):

    """Formats a datetime using the current locale."""

    def __init__(self, _datetime):
        super(DatetimeFormatter, self).__init__()
        self.datetime = _datetime
        self.templates = {
            'fr_FR': u'{date} à {time}',
            'en_US': u'{date} at {time}',
        }

    def display(self, *args, **kwargs):
        """Format the datetime using the current locale.

        Pass all args and kwargs to the DateFormatter.display method.

        """
        template = self.get_template()
        kwargs['prefix'] = True
        date_fmt = DateFormatter(self.datetime).display(*args, **kwargs)
        time_fmt = TimeFormatter(self.datetime).display()
        fmt = template.format(date=date_fmt, time=time_fmt)
        return fmt


class DatetimeIntervalFormatter(BaseFormatter):

    """Formats a datetime interval using the current locale."""

    def __init__(self, start_datetime, end_datetime):
        super(DatetimeIntervalFormatter, self).__init__()
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.templates = {
            'fr_FR': {
                'single_day': u'le {date} {time_interval}',
                'single_time': u'{date_interval} à {time}',
                'date_interval': u'{date_interval} {time_interval}',
            },
            'en_US': {
                'single_day': u'the {date} {time_interval}',
                'single_time': u'{date_interval} at {time}',
                'date_interval': u'{date_interval} {time_interval}',
            }
        }

    def same_time(self):
        """Return True if self.start_datetime and self.end_datetime have
        the same time.

        """
        return self.start_datetime.time() == self.end_datetime.time()

    @postprocess()
    def display(self, *args, **kwargs):
        """Format the datetime interval using the current locale.

        Pass all args and kwargs to the DateFormatter.display method.

        """
        date_formatter = DateIntervalFormatter(
            self.start_datetime, self.end_datetime)
        date_fmt = date_formatter.display(*args, **kwargs)

        time_fmt = TimeIntervalFormatter(
            self.start_datetime, self.end_datetime).display()
        if not time_fmt:
            return date_fmt
        if self.same_time():
            template = self.get_template('single_time')
            fmt = template.format(
                date_interval=date_fmt, time=time_fmt)
        else:
            template = self.get_template('date_interval')
            fmt = template.format(
                date_interval=date_fmt, time_interval=time_fmt)
        return fmt


class ContinuousDatetimeIntervalFormatter(BaseFormatter):

    """Formats a contiunuous datetime interval using the current locale."""

    def __init__(self, start, end):
        super(ContinuousDatetimeIntervalFormatter, self).__init__()
        self.start = start
        self.end = end
        self.templates = {
            'fr_FR':
            u'du {start_date} à {start_time} au {end_date} à {end_time}',
            'en_US':
            u'{start_date} at {start_time} - {end_date} at {end_time}'
        }

    @postprocess()
    def display(self, *args, **kwargs):
        """Display a continuous datetime interval in the current locale."""
        template = self.get_template()
        # do not include the year if both dates are in the same year
        sd_kwargs = kwargs.copy()
        if self.start.year == self.end.year:
            sd_kwargs['include_year'] = False
            sd_kwargs['force_year'] = False
        start_date_fmt = DateFormatter(self.start).display(*args, **sd_kwargs)
        end_date_fmt = DateFormatter(self.end).display(*args, **kwargs)
        start_time_fmt = TimeFormatter(self.start).display()
        end_time_fmt = TimeFormatter(self.end).display()
        fmt = template.format(
            start_date=start_date_fmt,
            start_time=start_time_fmt,
            end_date=end_date_fmt,
            end_time=end_time_fmt)
        return fmt


class WeekdayReccurenceFormatter(BaseFormatter):

    """Formats a weekday recurrence using the current locale."""

    def __init__(self, drr):
        super(WeekdayReccurenceFormatter, self).__init__()
        self.drr = get_drr(drr)
        self.templates = {
            'fr_FR': {
                'one_day': u'le {weekday}',
                'interval': u'du {start_weekday} au {end_weekday}',
                'weekday_reccurence': u'{weekdays}, {dates}, {time}',
            },
            'en_US': {
                'one_day': u'the {weekday}',
                'interval': u'from {start_weekday} to {end_weekday}',
                'weekday_reccurence': u'{weekdays}, {dates}, {time}',
            }
        }

    def all_weekdays(self):
        """Return True if the RRule describes all weekdays."""
        return self.drr.weekday_indexes == range(7)

    def format_weekday_interval(self):
        """Format the rrule weekday interval using the current locale."""
        if self.all_weekdays():
            return u''
        elif len(self.drr.weekday_indexes) == 1:
            template = self.get_template('one_day')
            weekday = self.day_name(self.drr.weekday_indexes[0])
            return template.format(weekday=weekday)
        else:
            start_idx = self.drr.weekday_indexes[0]
            end_idx = self.drr.weekday_indexes[-1]

            # continuous interval
            # note: to be continuous, the indexes must form a range of
            # more than 2 items, otherwise, we see it as a list
            if (self.drr.weekday_indexes == range(start_idx, end_idx + 1)
                    and start_idx != end_idx - 1):
                template = self.get_template('interval')
                start_weekday = self.day_name(start_idx)
                end_weekday = self.day_name(end_idx)
                fmt = template.format(
                    start_weekday=start_weekday,
                    end_weekday=end_weekday)
                return fmt
            else:
                # discontinuous interval
                fmt = self._('the') + ' ' + ', '.join(
                    [self.day_name(i) for i in self.drr.weekday_indexes[:-1]])
                fmt += ' %s %s' % (
                    self._('and'), self.day_name(end_idx))
                return fmt

    def format_date_interval(self, *args, **kwargs):
        """Format the rrule date interval using the current locale."""
        if not self.drr.bounded:
            return u''
        formatter = DateIntervalFormatter(
            self.drr.start_datetime, self.drr.end_datetime)
        return formatter.display(*args, **kwargs)

    def format_time_interval(self):
        """Format the rrule time interval using the current locale."""
        formatter = TimeIntervalFormatter(
            self.drr.start_datetime, self.drr.end_datetime)
        return formatter.display(prefix=True)

    @postprocess(lstrip_pattern=',')
    def display(self, *args, **kwargs):
        """Display a weekday recurrence using the current locale."""
        template = self.get_template('weekday_reccurence')
        weekdays = self.format_weekday_interval()
        dates = self.format_date_interval()
        time = self.format_time_interval()
        fmt = template.format(weekdays=weekdays, dates=dates, time=time)
        return fmt


class NextOccurenceFormatter(BaseFormatter, NextDateMixin, NextChangesMixin):

    """Object in charge of generating the shortest human readable
    representation of a datection schedule list, using a temporal
    reference.

    """

    def __init__(self, schedule, start, end):
        super(NextOccurenceFormatter, self).__init__()
        self._schedule = schedule
        self.schedule = [DurationRRule(drr) for drr in schedule]
        self.schedule = self.deduplicate(self.schedule)
        self.start, self.end = start, end
        self.templates = {
            'fr_FR': u'{date} + autres dates',
            'en_US': u'{date} + more dates',
        }

    @postprocess(capitalize=True)
    def display(self, reference, summarize=False, *args, **kwargs):
        """Format the schedule next occurence using as few characters
        as possible, using the current locale.

        """
        reference = get_date(reference)
        next_occurence = self.next_occurence()
        if not next_occurence:
            raise NoFutureOccurence
        if all_day(next_occurence['start'], next_occurence['end']):
            formatter = DateFormatter(
                next_occurence['start'])
        else:
            formatter = DatetimeIntervalFormatter(
                next_occurence['start'], next_occurence['end'])
        date_fmt = formatter.display(
            reference=reference,
            abbrev_reference=self.other_occurences() and summarize,
            *args, **kwargs)
        if summarize and self.other_occurences():
            template = self.get_template()
            return template.format(date=date_fmt)
        else:
            return date_fmt


class ExclusionFormatter(BaseFormatter):

    """Render exclusion rrules into a human readabled format."""

    def __init__(self, excluded):
        super(ExclusionFormatter, self).__init__()
        self.excluded = excluded
        self.templates = {
            'fr_FR': {
                'weekday': u'le {weekday}',
                'weekdays': u'le {weekdays} et {last_weekday}',
                'weekday_interval': u'du {start_weekday} au {end_weekday}',
                'date': u'le {date}',
            },
            'en_US': {
                'weekday': u'{weekday}',
                'weekdays': u'{weekdays} and {last_weekday}',
                'weekday_interval': u'from {start_weekday} to {end_weekday}',
                'date': u'{date}',
            },
        }

    def display_exclusion(self, excluded):
        """Render the exclusion rrule into a human-readable format.

        The rrule can either define weekdays or a single date(time).

        """
        excluded_rrule = excluded.exclusion_rrules[0]
        # excluded recurrent weekdays
        if excluded_rrule.byweekday:
            return self.display_excluded_weekdays(excluded_rrule)
        # excluded date(time)
        else:
            return self.display_excluded_date(
                rrule=excluded.duration_rrule['excluded'][0],
                duration=excluded.duration)

    def display_excluded_date(self, rrule, duration):
        """Render the excluded date into a human readable format.

        The excluded date can either be a date or a datetime, but the
        time will not be formated, as it's already present in the
        constructive pattern formatting.

        """
        drr = DurationRRule({
            'rrule': rrule,
            'duration': duration
        })
        fmt = DateFormatter(drr.date_interval[0])
        return fmt.display(prefix=True)

    def display_excluded_weekdays(self, excluded):
        """Render the excluded weekdays into a human-readable format.

        The excluded weekdays can be a single weekday, a weekday interval
        or a weekday list.

        """
        # single excluded recurrent weekday
        if len(excluded.byweekday) == 1:
            return self.get_template('weekday').format(
                weekday=self.day_name(excluded.byweekday[0].weekday))
        else:
            indices = [bywk.weekday for bywk in excluded.byweekday]
            # excluded day range
            if indices == range(indices[0], indices[-1] + 1):
                return self.get_template('weekday_interval').format(
                    start_weekday=self.day_name(indices[0]),
                    end_weekday=self.day_name(indices[-1]))
            # excluded day list
            else:
                weekdays = u', '.join(self.day_name(i) for i in indices[:-1])
                return self.get_template('weekdays').format(
                    weekdays=weekdays,
                    last_weekday=self.day_name(indices[-1]))

    def display(self, *args, **kwargs):
        """Render an exclusion rrule into a human readable format."""
        # format the constructive pattern
        fmt = LongFormatter(
            schedule=[self.excluded.duration_rrule],
            apply_exlusion=False,
            format_exclusion=False)
        constructive = fmt.display(*args, **kwargs)
        # format the excluded pattern
        excluded = self.display_exclusion(self.excluded)
        # join the both of them
        return u"{constructive}, {_except} {excluded}".format(
            constructive=constructive,
            _except=self._('except'),
            excluded=excluded)


class LongFormatter(BaseFormatter, NextDateMixin, NextChangesMixin):

    """Displays a schedule in the current locale without trying to use
    as few characters as possible.

    """

    def __init__(self, schedule, apply_exlusion=True, format_exclusion=True):
        super(LongFormatter, self).__init__()
        self._schedule = schedule
        self.schedule = [
            DurationRRule(drr, apply_exlusion) for drr in schedule]
        self.schedule = self.deduplicate(self.schedule)
        self.format_exclusion = format_exclusion
        self.templates = {
            'fr_FR': u'{dates} {time}',
            'en_US': u'{dates} {time}',
        }

    @cached_property
    def recurring(self):
        """Select recurring rrules from self.schedule"""
        return [drr for drr in self.schedule if drr.is_recurring]

    @cached_property
    def non_special(self):
        """Return all the non-continuous, non-recurring, non-excluded
        DurationRRule objects.

        """
        return [drr for drr in self.schedule
                if not drr.is_continuous
                if not drr.is_recurring
                if not (drr.exclusion_rrules and drr.apply_exclusion)]

    @cached_property
    def continuous(self):
        """Select continuous rrules from self.schedule."""
        return [drr for drr in self.schedule if drr.is_continuous]

    @cached_property
    def excluded(self):
        return [drr for drr in self.schedule if drr.exclusion_rrules]

    @cached_property
    def time_groups(self):
        """Non recurring rrules grouped by start / end datetimes"""
        _time_groups = to_start_end_datetimes(self.non_special)
        # convert rrule structures to start/end datetime lists
        _time_groups = groupby_time(_time_groups)
        for group in _time_groups:
            group.sort(key=lambda date: date['start'])
        return _time_groups

    @cached_property
    def conseq_groups(self):
        """Group each time group by consecutivity"""
        _conseq_groups = []
        for group in self.time_groups:
            conseq = groupby_consecutive_dates(group)
            _conseq_groups.append(conseq)
        return _conseq_groups

    @staticmethod
    def _filterby_year_and_month(dates, year, month):
        """ Return all dates in dates occuring at argument year and month """
        return [date for date in dates
                if date['start'].year == year
                if date['start'].month == month]

    def format_single_dates_and_interval(self, conseq_groups, *args, **kwargs):
        """ First formatting technique, using dates interval

        This formatting technique uses self.consecutive_groups,
        and displays single dates using the self.format_date method
        and date intervals using the format_date_interval method.

        Example:
            [[15 mars 2013], [17 mars 2013, 18 mars 2013]]
        Output:
            u"le 15 mars 2013, du 17 au 18 mars 2013"

        """
        kwargs['force_year'] = True
        out = []
        for conseq in conseq_groups:
            start, end = conseq[0]['start'], conseq[-1]['end']
            fmt = DateIntervalFormatter(start, end).display(*args, **kwargs)
            out.append(fmt)
        return out

    def format_date_list(self, time_group, *args, **kwargs):
        """Second formatting technique, using non - consecutive dates lists

        All the non-consecutive dates are first grouped by years and then by
        months, and returned as a simple list of human readable time
        expressions, expressed in self.lang.

        Example:
        Input:
            [1 mars 2013, 4 mars 2013, 6 juin 2013, 5 juillet 2014]
        Output:
            u"le 1er, 4 mars 2013, le 6 juin 2013, le 5 juillet 2014"

        """
        out = []
        kwargs['force_year'] = True
        # group the sparse dates by year first
        years = list(set([date['start'].year for date in time_group]))
        for year in years:
            # now group the dates by month
            months = sorted(set([date['start'].month for date in time_group
                                 if date['start'].year == year]))

            # all dates happen in the same month
            for month in months:
                mdates = self._filterby_year_and_month(time_group, year, month)
                mdates = [d['start'] for d in mdates]
                fmt = DateListFormatter(mdates).display(*args, **kwargs)
                out.append(fmt)
        return out

    def group_by_common_pattern_except_time(self):
        """ Will be in use with """
        common_pattern_dict = defaultdict(list)
        same_patterns_with_different_times = []
        others = []


        for time_grp, conseq_grps in zip(self.time_groups, self.conseq_groups):
            hash_key = hash_same_date_pattern(time_grp)
            common_pattern_dict[hash_key].append((time_grp, conseq_grps))

        for time_conseq_grp_tup_list in common_pattern_dict.values():
            if len(time_conseq_grp_tup_list) == 1:
                others.extend(time_conseq_grp_tup_list)
            else:
                same_patterns_with_different_times.append(
                    time_conseq_grp_tup_list)

        return (same_patterns_with_different_times, others)

    def _helper_date_fmt(self, time_group, conseq_groups, *args, **kwargs):
        """ Get human readable date given list of datetime group

        :time_group: [{'start': datetime(), 'end': datetime()},]
        :conseq_groups: [{'start': datetime(), 'end': datetime()},]

        :return: date format string
        """
        date_list = self.format_date_list(time_group, *args, **kwargs)
        list_fmt = ', '.join(date_list)
        if len(date_list) > 1:
            list_fmt += ','

        date_conseq = self.format_single_dates_and_interval(
            conseq_groups, *args, **kwargs)
        conseq_fmt = ', '.join(date_conseq)
        if len(date_conseq) > 1:
            conseq_fmt += ','

        # pick shortest render
        return get_shortest(list_fmt, conseq_fmt)

    def _helper_time_fmt(self, time_group):
        """ Get human readable time given list of datetime group

        :time_group: [{'start': datetime(), 'end': datetime()},]

        :return: time format string
        """
        start_time, end_time = time_group[0].values()
        return TimeIntervalFormatter(start_time, end_time).display(prefix=True)

    @postprocess(strip=False, trim_whitespaces=False, rstrip_pattern=',')
    def display(self, *args, **kwargs):
        """Return a human readable string describing self.schedule as shortly
        as possible(without using abbreviated forms), in the right language.

        """
        out = []
        kwargs['force_year'] = True

        # format rrules having an exclusion pattern
        if self.format_exclusion:
            for exc in self.excluded:
                out.append(ExclusionFormatter(exc).display(*args, **kwargs))

        # format recurring rrules
        for rec in self.recurring:
            out.append(
                WeekdayReccurenceFormatter(rec).display(*args, **kwargs))

        # format continuous rrules
        for con in self.continuous:
            start, end = con.start_datetime, con.end_datetime
            out.append(ContinuousDatetimeIntervalFormatter(start, end).
                       display(*args, **kwargs))

        same_patterns_with_different_dates, others = \
            self.group_by_common_pattern_except_time()

        # get nb of days ouput, if <2 display dayname
        nbdates = 0
        for dates in others:
            timespanlist = groupby_consecutive_dates(dates[0])
            for timespan in timespanlist:
                if len(timespan) > 1:
                    nbdates += 2
                else:
                    nbdates += 1
        nbdates += len(same_patterns_with_different_dates)
        if nbdates < 3:
            kwargs['include_dayname'] = True


        template = self.get_template()
        # format non recurring rrules on grouped patterns with different dates
        for time_conseq_grp_tup_list in same_patterns_with_different_dates:
            time_group, conseq_groups = time_conseq_grp_tup_list[0]
            date_fmt = self._helper_date_fmt(
                time_group,
                conseq_groups,
                *args,
                **kwargs
            )

            # concatenate dates and time
            time_fmt_list = []
            for time_group, _ in time_conseq_grp_tup_list:
                time_fmt_list.append(self._helper_time_fmt(time_group))

            time_fmt = self.prevert_list(time_fmt_list)

            if time_fmt:
                fmt = template.format(dates=date_fmt, time=time_fmt)
                out.append(fmt)
            else:
                out.append(date_fmt)

        # format non recurring rrules on grouped patterns with different dates
        for time_group, conseq_groups in others:
            date_fmt = self._helper_date_fmt(
                time_group,
                conseq_groups,
                *args,
                **kwargs
            )

            time_fmt = self._helper_time_fmt(time_group)

            if time_fmt:
                fmt = template.format(dates=date_fmt, time=time_fmt)
                out.append(fmt)
            else:
                out.append(date_fmt)

        # finally, apply global formatting rules
        return self.format_output(out)

    @staticmethod
    def format_output(lines):
        """Capitalize each line."""
        return '\n'.join([line.capitalize() for line in lines])

    def next_changes(self):
        """Return None, as a LongFormatter display output never varies."""
        return None


class TooManyMonths(Exception):

    """Exception raised in SEO formatting when a schedule related to
    more than two months or when the two months are of a different year.

    """
    pass


class SeoFormatter(BaseFormatter, NextDateMixin, NextChangesMixin):

    """Generates SEO friendly human readable dates."""

    MAX_MONTHS = 2

    def __init__(self, schedule):
        super(SeoFormatter, self).__init__()
        self._schedule = schedule
        self.schedule = [DurationRRule(drr) for drr in schedule]
        self.schedule = self.deduplicate(self.schedule)
        self.templates = {
            'fr_FR': {
                'two_months': u'{month1} et {month2}',
                'full': u'{months} {year}'
            },
            'en_US': {
                'two_months': u'{month1} and {month2}',
                'full': u'{months} {year}'
            }
        }

    def get_monthyears(self):
        """Return a list of datetimes which month and year describe the whole
        schedule.

        If the length of the output list exceeds self.MAX_MONTHS, or if several
        months with different associated years are returned, a TooManyMonths
        exception is raised.

        """
        monthyears = set()
        datetimes, out = [], []
        for drr in self.schedule:
            datetimes.extend([dt for dt in drr])
        monthyear = lambda dt: (dt.month, dt.year)
        for key, group in itertools.groupby(sorted(datetimes), key=monthyear):
            monthyears.add(key)
            out.append(next(group))
            if len(monthyears) > self.MAX_MONTHS:
                raise TooManyMonths

        # Make sure both months have the same year
        if len(out) > 1 and out[0].year != out[1].year:
            raise TooManyMonths
        return out

    def display(self):
        """Generates SEO friendly human readable dates in the current locale."""
        try:
            dates = self.get_monthyears()
        except TooManyMonths:
            return u''
        if len(dates) == 0:
            return u''
        elif len(dates) == 1:
            date_fmt = DateFormatter(dates[0])
            month_fmt = date_fmt.format_month().decode('utf-8')
        else:
            month_tpl = self.get_template('two_months')
            month_fmt = month_tpl.format(
                month1=DateFormatter(dates[0]).format_month().decode('utf-8'),
                month2=DateFormatter(dates[1]).format_month().decode('utf-8'))
        year_fmt = DateFormatter(dates[0]).format_year(force=True)
        tpl = self.get_template('full')
        fmt = tpl.format(months=month_fmt, year=year_fmt)
        return fmt


class TemporaryLocale(object):  # pragma: no cover

    """Temporarily change the current locale using a context manager."""

    def __init__(self, category, locale):
        self.category = category
        self.locale = locale.encode('utf-8')
        self.oldlocale = _locale.getlocale(category)

    def __enter__(self):
        _locale.setlocale(self.category, self.locale)

    def __exit__(self, exception_type, exception_value, traceback):
        _locale.setlocale(self.category, self.oldlocale)


class DisplaySchedule(object):

    """Render a schedule using different formatters, and return the best
    possible rendering.

    """

    def __init__(self):
        self.formatter_tuples = []
        self.best_formatter = None

    def _compare_formatters(self, fmt_tuple_1, fmt_tuple_2):
        """Return the formatter tuple generating the smallest rendering

        """
        if not fmt_tuple_1:
            return fmt_tuple_2
        elif not fmt_tuple_2:
            return fmt_tuple_1

        fmt_1 = fmt_tuple_1.formatter.display(**fmt_tuple_1.display_args)
        fmt_2 = fmt_tuple_2.formatter.display(**fmt_tuple_2.display_args)

        return fmt_tuple_1 if len(fmt_1) < len(fmt_2) else fmt_tuple_2

    @cached_property
    def _best_formatter(self):
        """Return the best formatter tuple among self.formatter_tuples"""
        best_formatter = None
        for fmt_tuple in self.formatter_tuples:
            best_formatter = self._compare_formatters(
                best_formatter, fmt_tuple)
        return best_formatter

    def display(self):
        """Return the smallest rendering among all the formatter options

        """
        try:
            return self._best_formatter.formatter.display(
                **self._best_formatter.display_args)
        except NoFutureOccurence:
            return u''

    def next_changes(self):
        """ return the formatter next changes datetime
        """
        return self._best_formatter.formatter.next_changes()


def get_display_schedule(
    schedule, loc, short=False, seo=False, bounds=(None, None),
        reference=get_current_date()):
    """ get a DisplaySchedule object according to the better ouput
    """
    # make fr_FR.UTF8 the default locale
    global locale
    if loc not in DEFAULT_LOCALES.values():
        locale = getlocale(loc) if getlocale(loc) else 'fr_FR.UTF8'

    display_schedule = DisplaySchedule()
    if seo:
        fmt_tuple = FormatterTuple(SeoFormatter(schedule), {})
        display_schedule.formatter_tuples.append(fmt_tuple)
        return display_schedule
    elif not short:
        fmt_tuple = FormatterTuple(LongFormatter(schedule), {})
        display_schedule.formatter_tuples.append(fmt_tuple)
        return display_schedule
    else:
        start, end = bounds
        short_fmt = NextOccurenceFormatter(schedule, start, end)
        default_fmt = LongFormatter(schedule)

        short_fmt_tuple = FormatterTuple(
            short_fmt,
            {
                "reference": reference,
                "summarize": True,
                "prefix": True,
                "abbrev_monthname": True
            })
        display_schedule.formatter_tuples.append(short_fmt_tuple)

        default_fmt_tuple = FormatterTuple(
            default_fmt, {"abbrev_monthname": True})
        display_schedule.formatter_tuples.append(default_fmt_tuple)

        return display_schedule


def display(schedule, loc, short=False, seo=False, bounds=(None, None),
            reference=get_current_date()):
    """Format a schedule into the shortest human readable sentence possible

    args:
        schedule:
            (list) a list of rrule dicts, containing a duration
            and a RFC rrule
        loc:
            (str) the target locale
        short:
            (bool) if True, a shorter sentence will be generated
        bounds:
            limit start / end datetimes beyond which the dates will
            not even be considered
        seo(bool):
            if True, an SeoFormatter will be used

    """
    return get_display_schedule(
        schedule,
        loc,
        short=short,
        seo=seo,
        bounds=bounds,
        reference=reference).display()
