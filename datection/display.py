# -*- coding: utf-8 -*-

"""
Module in charge of transforming a rrule + duraction object into the shortest
human-readable string possible.
"""

import datetime
import locale
import calendar
import re
import itertools

from functools import wraps
from collections import defaultdict

from datection.models import DurationRRule
from datection.utils import cached_property
from datection.lang import DEFAULT_LOCALES
from datection.lang import getlocale


translations = {
    'fr_FR': {
        'today': u"aujourd'hui",
        'tomorrow': u'demain',
        'this': u'ce',
        'midnight': u'minuit',
        'every day': u'tous les jours',
        'the': u'le',
        'and': u'et',
        'at': u'à',
    }
}


def get_date(d):
    return d.date() if isinstance(d, datetime.datetime) else d


def get_time(d):
    return d.time() if isinstance(d, datetime.datetime) else d


def get_drr(drr):
    return DurationRRule(drr) if isinstance(drr, dict) else drr


def all_day(start, end):
    start_time, end_time = get_time(start), get_time(end)
    return (start_time == datetime.time(0, 0)
            and end_time == datetime.time(23, 59))


def postprocess(strip=True, trim_whitespaces=True, lstrip_pattern=None,
                capitalize=False, rstrip_pattern=None):
    """Post processing text formatter decorator."""
    def wrapped_f(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            s = f(*args, **kwargs)
            s = s.replace(', ,', ', ')
            if trim_whitespaces:
                s = re.sub(r'\s+', ' ', s)
            if lstrip_pattern:
                s = s.lstrip(lstrip_pattern)
            if rstrip_pattern:
                s = s.rstrip(rstrip_pattern)
            if strip:
                s = s.strip()
            if capitalize:
                s = s.capitalize()
            return s
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
        # make sure the rrule does not generate an infinite stream of
        # datetimes if unbounded, by setting the until bound to the
        # end_bound argument value
        if not drr.rrule.until:
            drr.rrule._until = end_bound

        for start_date in drr.rrule:
            hour = drr.rrule.byhour[0] if drr.rrule.byhour else 0
            minute = drr.rrule.byminute[0] if drr.rrule.byminute else 0
            start = datetime.datetime.combine(
                start_date,
                datetime.time(hour, minute))
            end = datetime.datetime.combine(
                start_date,
                datetime.time(hour, minute)) + \
                datetime.timedelta(minutes=drr.duration)

            # convert the bounds to datetime if dates were given
            if isinstance(start_bound, datetime.date):
                start_bound = datetime.datetime.combine(
                    start_bound, datetime.time(0, 0, 0))
            if isinstance(end_bound, datetime.date):
                end_bound = datetime.datetime.combine(
                    end_bound, datetime.time(23, 59, 59))

            # filter out all start/end pairs outside of given boundaries
            if ((start_bound and end_bound
                    and start >= start_bound and end <= end_bound)
                    or (start_bound and not end_bound and start >= start_bound)
                    or (not start_bound and end_bound and end <= end_bound)
                    or (not start_bound and not end_bound)):
                out.append({'start': start, 'end': end})
    return out


class NoFutureOccurence(Exception):
    pass


class BaseFormatter(object):

    def __init__(self):
        self.language_code, self.encoding = locale.getlocale(locale.LC_TIME)

    def _(self, key):
        return translations[self.language_code][key]

    def get_template(self, key=None):
        if key is None:
            return self.templates[self.language_code]
        return self.templates[self.language_code][key]

    def day_name(self, weekday_index):
        """Return the weekday name associated wih the argument index
        using the current locale.

        """
        return calendar.day_name[weekday_index].decode('utf-8')


class DateFormatter(BaseFormatter):

    """Formats a date into using the current locale."""

    def __init__(self, date):
        super(DateFormatter, self).__init__()
        self.date = get_date(date)

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': {
                'all': u'{prefix} {dayname} {day} {month} {year}',
                'no_year': u'{prefix} {dayname} {day} {month}',
                'no_year_no_month': u'{prefix} {dayname} {day}',
            }
        }

    def format_day(self):
        """Format the date day using the current locale."""
        return u'1er' if self.date.day == 1 else unicode(self.date.day)

    def format_dayname(self, abbrev=False):
        """Format the date day using the current locale."""
        if abbrev:
            return self.date.strftime('%a')
        return self.date.strftime('%A')

    def format_month(self, abbrev=False):
        """Format the date month using the current locale."""
        if abbrev:
            return self.date.strftime('%b')
        return self.date.strftime('%B')

    def format_year(self, abbrev=False):
        """Format the date year using the current locale."""
        if abbrev:
            return self.date.strftime('%y')
        return self.date.strftime('%Y')

    def format_all_parts(self, include_dayname, abbrev_dayname,
                         abbrev_monthname, abbrev_year, prefix):
        template = self.get_template('all')
        if include_dayname or abbrev_dayname:
            dayname = self.format_dayname(abbrev_dayname)
        else:
            dayname = u''
        day = self.format_day()
        month = self.format_month(abbrev_monthname).decode('utf-8')
        year = self.format_year(abbrev_year)
        fmt = template.format(
            prefix=prefix, dayname=dayname, day=day, month=month, year=year)
        fmt = re.sub(r'\s+', ' ', fmt)
        return fmt

    def format_no_year(self, include_dayname, abbrev_dayname, abbrev_monthname,
                       prefix):
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
                abbrev_year=False, reference=None, prefix=False):
        """Format the date using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If include_month is True, the month will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If include_year is True, the year will be included.
        If abbrev_year is True, a 2 digit year format will be used.
        If relative is True, a temporal reference (like 'today', 'tomorrow',
        etc) may be used to refer to the date.

        """
        if reference:
            if self.date == reference:
                return self._('today')
            elif self.date == reference + datetime.timedelta(days=1):
                return self._('tomorrow')
            elif reference < self.date < reference + datetime.timedelta(days=6):
                # if d is next week, use its weekday name
                return u'%s %s' % (
                    self._('this'),
                    self.format_dayname(abbrev_dayname))

        prefix = self._('the') if prefix else u''
        if include_month and include_year:
            return self.format_all_parts(include_dayname, abbrev_dayname,
                                         abbrev_monthname, abbrev_year, prefix)
        elif include_month and not include_year:
            return self.format_no_year(
                include_dayname, abbrev_dayname, abbrev_monthname, prefix)
        else:
            return self.format_no_month_no_year(include_dayname, abbrev_dayname,
                                                prefix)


class DateIntervalFormatter(BaseFormatter):

    """Formats a date interval using the current locale."""

    def __init__(self, start_date, end_date):
        super(DateIntervalFormatter, self).__init__()
        self.start_date = get_date(start_date)
        self.end_date = get_date(end_date)

    @property
    def templates(self):
        return {
            'fr_FR': u'du {start_date} au {end_date}',
        }

    def same_day_interval(self):
        """Return True if the start and end datetime have the same date,
        else False.

        """
        return self.start_date == self.end_date

    def same_month_interval(self):
        """Return True if the start and end date have the same month,
        else False.

        """
        return self.start_date.month == self.end_date.month

    def same_year_interval(self):
        """Return True if the start and end date have the same year,
        else False.

        """
        return self.start_date.year == self.end_date.year

    def format_same_month(self, *args, **kwargs):
        template = self.get_template()
        start_kwargs = kwargs.copy()
        start_kwargs['include_month'] = False
        start_kwargs['include_year'] = False
        start_date_fmt = DateFormatter(
            self.start_date).display(*args, **start_kwargs)
        end_date_fmt = DateFormatter(self.end_date).display(*args, **kwargs)
        return template.format(start_date=start_date_fmt, end_date=end_date_fmt)

    def format_same_year(self, *args, **kwargs):
        template = self.get_template()
        start_kwargs = kwargs.copy()
        start_kwargs['include_year'] = False
        start_date_fmt = DateFormatter(
            self.start_date).display(*args, **start_kwargs)
        end_date_fmt = DateFormatter(self.end_date).display(*args, **kwargs)
        return template.format(start_date=start_date_fmt, end_date=end_date_fmt)

    @postprocess()
    def display(self, *args, **kwargs):
        """Format the date interval using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If abbrev_year is True, a 2 digit year format will be used.

        """
        if self.same_day_interval():
            kwargs['prefix'] = True
            return DateFormatter(self.start_date).display(*args, **kwargs)
        elif self.same_month_interval():
            return self.format_same_month(*args, **kwargs)
        elif self.same_year_interval():
            return self.format_same_year(*args, **kwargs)
        else:
            template = self.get_template()
            start_date_fmt = DateFormatter(
                self.start_date).display(*args, **kwargs)
            end_date_fmt = DateFormatter(
                self.end_date).display(*args, **kwargs)
            fmt = template.format(
                start_date=start_date_fmt, end_date=end_date_fmt)
            return fmt


class DateListFormatter(BaseFormatter):

    """Formats a date list using the current locale."""

    def __init__(self, date_list):
        super(DateListFormatter, self).__init__()
        self.date_list = [get_date(d) for d in date_list]

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': u'les {date_list} et {last_date}',
        }

    @postprocess()
    def display(self, *args, **kwargs):
        """Format a date list using the current locale."""
        if len(self.date_list) == 1:
            kwargs['prefix'] = True
            return DateFormatter(self.date_list[0]).display(*args, **kwargs)
        template = self.get_template()
        date_list = ', '.join([DateFormatter(d).display(
            include_month=False, include_year=False)
            for d in self.date_list[:-1]])
        last_date = DateFormatter(self.date_list[-1]).display()
        fmt = template.format(date_list=date_list, last_date=last_date)
        return fmt


class TimeFormatter(BaseFormatter):

    """Formats a time using the current locale."""

    def __init__(self, time):
        super(TimeFormatter, self).__init__()
        self.time = get_time(time)

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': u'{prefix} {hour} h {minute}'
        }

    def format_hour(self):
        """Format the time hour using the current locale."""
        return unicode(self.time.hour)

    def format_minute(self):
        """Format the time hour using the current locale."""
        if self.time.minute == 0:
            return u''
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

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': {
                'interval': u'de {start_time} à {end_time}',
                'single_time': u'à {time}'
            }
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

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': u'{date} à {time}'
        }

    def display(self, *args, **kwargs):
        """Format the datetime using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If abbrev_year is True, a 2 digit year format will be used.

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

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': {
                'single_day': u'le {date} {time_interval}',
                'single_time': u'{date_interval} à {time}',
                'date_interval': u'{date_interval} {time_interval}',
            }
        }

    def same_time(self):
        return self.start_datetime.time() == self.end_datetime.time()

    @postprocess()
    def display(self, *args, **kwargs):
        """Format the datetime interval using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If abbrev_year is True, a 2 digit year format will be used.

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

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': u'du {start_date} à {start_time} au {end_date} à {end_time}'
        }

    @postprocess()
    def display(self, *args, **kwargs):
        template = self.get_template()
        # do not include the year if both dates are in the same year
        sd_kwargs = kwargs.copy()
        if self.start.year == self.end.year:
            sd_kwargs['include_year'] = False
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

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': {
                'one_day': u'le {weekday}',
                'interval': u'du {start_weekday} au {end_weekday}',
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
        if (self.drr.end_datetime - self.drr.start_datetime).days == 365:
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
        template = self.get_template('weekday_reccurence')
        weekdays = self.format_weekday_interval()
        dates = self.format_date_interval()
        time = self.format_time_interval()
        fmt = template.format(weekdays=weekdays, dates=dates, time=time)
        return fmt


class NextOccurenceFormatter(BaseFormatter):

    """Object in charge of generating the shortest human readable
    representation of a datection schedule list, using a temporal
    reference.

    """

    def __init__(self, schedule, start, end):
        super(NextOccurenceFormatter, self).__init__()
        self._schedule = schedule
        self.schedule = [DurationRRule(drr) for drr in schedule]
        self.start, self.end = start, end

    @property
    def templates(self):
        return {
            'fr_FR': u'{date} + autres dates'
        }

    @cached_property
    def regrouped_dates(self):
        """Convert self.schedule to a start / end datetime list and filter
        out the obtained values outside of the(self.start, self.end)
        datetime range

        """
        start = self.start or datetime.date.today()  # filter out passed dates
        dtimes = to_start_end_datetimes(self.schedule, start, self.end)
        # group the filtered values by date
        dtimes = sorted(groupby_date(dtimes))
        return dtimes

    def next_occurence(self):
        if self.regrouped_dates:
            return self.regrouped_dates[0][0]

    def other_occurences(self):
        return len(self.regrouped_dates) > 1

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
            formatter = DateFormatter(next_occurence['start'])
        else:
            formatter = DatetimeIntervalFormatter(
                next_occurence['start'], next_occurence['end'])
        date_fmt = formatter.display(reference=reference, *args, **kwargs)
        if summarize and self.other_occurences():
            template = self.get_template()
            return template.format(date=date_fmt)
        else:
            return date_fmt


class OpeningHoursFormatter(BaseFormatter):

    """Formats opening hours into a human-readable format using the
    current locale.

    """

    def __init__(self, opening_hours):
        super(OpeningHoursFormatter, self).__init__()
        self._opening_hours = opening_hours
        self.opening_hours = [DurationRRule(drr) for drr in opening_hours]

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': {
                'one_opening': u'{weekday} {time_interval}',
                'several_openings': u'{opening} {time_list} et {last_time}'
            }
        }

    def format_opening(self, opening, day):
        template = self.get_template('one_opening')
        weekday = self.day_name(day)
        start_time, end_time = opening.time_interval
        time_interval = TimeIntervalFormatter(start_time, end_time).display()
        fmt = template.format(weekday=weekday, time_interval=time_interval)
        return fmt

    @postprocess(capitalize=True)
    def format_openings(self, openings, day):
        """Format opening hours for a single day."""
        parts = []
        fmt = self.format_opening(openings[0], day)
        if len(openings) == 1:
            return fmt
        else:
            template = self.get_template('several_openings')
            parts.append(fmt)
            for opening in openings[1:]:
                start_time, end_time = opening.time_interval
                time_fmt = TimeIntervalFormatter(start_time, end_time).display()
                parts.append(time_fmt)
        fmt = template.format(
            opening=parts[0],
            time_list=parts[1:-1] if parts[1:-1] else '',
            last_time=parts[-1])
        return fmt

    def display(self):
        """Format a list of opening hours for a single day."""
        out = []
        for day in xrange(7):
            openings = [rec for rec in self.opening_hours
                        if day in rec.weekday_indexes]
            if openings:
                out.append(self.format_openings(openings, day))
        return '\n'.join([line for line in out])


class LongFormatter(BaseFormatter):

    def __init__(self, schedule):
        super(LongFormatter, self).__init__()
        self._schedule = schedule
        self.schedule = [DurationRRule(drr) for drr in schedule]

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': u'{dates} {time}',
        }

    @cached_property
    def recurring(self):
        """Select recurring rrules from self.schedule"""
        return [drr for drr in self.schedule if drr.is_recurring]

    @cached_property
    def non_recurring(self):
        """Select non recurring rrules from self.schedule"""
        return [drr for drr in self.schedule
                if not drr.is_continuous
                if not drr.is_recurring]

    @cached_property
    def continuous(self):
        """Select continuous rrules from self.schedule."""
        return [drr for drr in self.schedule if drr.is_continuous]

    @cached_property
    def time_groups(self):
        """Non recurring rrules grouped by start/end datetimes"""
        _time_groups = to_start_end_datetimes(self.non_recurring)
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

        Example: [[15 mars 2013], [17 mars 2013, 18 mars 2013]]
        Output: u"le 15 mars 2013, du 17 au 18 mars 2013"

        """
        out = []
        for i, conseq in enumerate(conseq_groups):
            start, end = conseq[0]['start'], conseq[-1]['end']
            fmt = DateIntervalFormatter(start, end).display(*args, **kwargs)
            out.append(fmt)
        return out

    def format_date_list(self, time_group, *args, **kwargs):
        """ Second formatting technique, using non-consecutive dates lists

        All the non-consecutive dates are first grouped by years and then by
        months, and returned as a simple list of human readable time expressions,
        expressed in self.lang.

        Example:
        Input: [1 mars 2013, 4 mars 2013, 6 juin 2013, 5 juillet 2014]
        Output: u"le 1er, 4 mars 2013, le 6 juin 2013, le 5 juillet 2014"

        """
        out = []
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

    @postprocess(strip=False, trim_whitespaces=False, rstrip_pattern=',')
    def display(self, *args, **kwargs):
        """Return a human readable string describing self.schedule as shortly
        as possible (without using abbreviated forms), in the right language.

        """
        out = []
        # format recurring rrules
        for rec in self.recurring:
            out.append(WeekdayReccurenceFormatter(rec).display(*args, **kwargs))

        # format continuous rrules
        for con in self.continuous:
            start, end = con.start_datetime, con.end_datetime
            out.append(ContinuousDatetimeIntervalFormatter(start, end).
                       display(*args, **kwargs))

        # format non recurring rrules
        for time_group, conseq_groups in zip(self.time_groups, self.conseq_groups):
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
            date_fmt = get_shortest(list_fmt, conseq_fmt)

            # concatenate dates and time
            start_time, end_time = time_group[0].values()
            template = self.get_template()
            time_fmt = TimeIntervalFormatter(start_time, end_time).\
                display(prefix=True)
            if time_fmt:
                fmt = template.format(dates=date_fmt, time=time_fmt)
                out.append(fmt)
            else:
                out.append(date_fmt)

        # finally, apply global formatting rules
        return self.format_output(out)

    @staticmethod
    def format_output(l):
        return '\n'.join([line.capitalize() for line in l])


class TooManyMonths(Exception):

    """Exception raised in SEO formatting when a schedule related to
    more than two months.

    """
    pass


class SeoFormatter(BaseFormatter):

    """Generates SEO friendly human readable dates."""

    def __init__(self, schedule):
        super(SeoFormatter, self).__init__()
        self._schedule = schedule
        self.schedule = [DurationRRule(drr) for drr in schedule]
        self.MAX_MONTHS = 2

    @property
    def templates(self):  # pragma: no cover
        return {
            'fr_FR': {
                'two_months': u'{month1} et {month2}',
                'full': u'{months} {year}'
            }
        }

    def get_monthyears(self):
        """Return a list of datetimes which month and year describe the whole
        schedule.

        If the length of the output list exceeds self.MAX_MONTHS, a
        TooManyMonths exception is raised.

        """
        out = []
        monthyears = set()
        datetimes = []
        for drr in self.schedule:
            datetimes.extend([dt for dt in drr.rrule])
        monthyear = lambda dt: (dt.month, dt.year)
        for key, group in itertools.groupby(sorted(datetimes), key=monthyear):
            monthyears.add(key)
            out.append(next(group))
            if len(monthyears) > self.MAX_MONTHS:
                raise TooManyMonths
        return out

    def display(self):
        """Generates SEO friendly human readable dates in the current locale."""
        try:
            dates = self.get_monthyears()
        except TooManyMonths:
            return u''
        if len(dates) == 1:
            date_fmt = DateFormatter(dates[0])
            month_fmt = date_fmt.format_month().decode('utf-8')
        else:
            month_tpl = self.get_template('two_months')
            month_fmt = month_tpl.format(
                month1=DateFormatter(dates[0]).format_month().decode('utf-8'),
                month2=DateFormatter(dates[1]).format_month().decode('utf-8'))
        year_fmt = DateFormatter(dates[0]).format_year()
        tpl = self.get_template('full')
        fmt = tpl.format(months=month_fmt, year=year_fmt)
        return fmt


class TemporaryLocale(object):  # pragma: no cover

    def __init__(self, category, locale):
        self.category = category
        self.locale = locale.encode('utf-8')

    def __enter__(self):
        locale.setlocale(self.category, self.locale)

    def __exit__(self, exception_type, exception_value, traceback):
        locale.resetlocale(self.category)


def display(schedule, loc, short=False, seo=False, bounds=(None, None),
            place=False, reference=datetime.date.today()):
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
        place(bool):
            if True, an OpeningHoursFormatter will be used.
        seo (bool):
            if True, an SeoFormatter will be used

    """
    # make fr_FR.UTF8 the default locale
    if loc not in DEFAULT_LOCALES.values():
        loc = getlocale(loc) if getlocale(loc) else 'fr_FR.UTF8'

    with TemporaryLocale(locale.LC_TIME, loc):
        if place:
            return OpeningHoursFormatter(schedule).display()
        elif seo:
            return SeoFormatter(schedule).display()
        elif not short:
            return LongFormatter(schedule).display()
        else:
            try:
                start, end = bounds
                short_fmt = NextOccurenceFormatter(schedule, start, end).\
                    display(reference, summarize=True, prefix=True)
            except NoFutureOccurence:
                return u''
            else:
                default_fmt = LongFormatter(schedule).display(
                    abbrev_monthname=True)
                return get_shortest(default_fmt, short_fmt)
