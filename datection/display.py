# -*- coding: utf-8 -*-

"""
Module in charge of transforming a rrule + duraction object into the shortest
human-readable string possible.
"""

import datetime
import calendar
import gettext

# Set up message catalog access
from os.path import abspath, join, dirname
popath = abspath(join(dirname(__file__), 'po'))

from collections import defaultdict
from dateutil.rrule import rrulestr

from datection.lang import getlocale


# define _ translator in global variables
_ = None

def lazy_property(f):
    """Lazy loading decorator for object properties"""
    attr_name = '_' + f.__name__

    @property
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, f(self, *args, **kwargs))
        return getattr(self, attr_name)
    return wrapper


def to_start_end_datetimes(schedule, start_bound=None, end_bound=None):
    out = []
    for rrule_struct in schedule:
        rrule = rrulestr(rrule_struct['rrule'])
        for start_date in rrule:
            hour = rrule.byhour[0] if rrule.byhour else 0
            minute = rrule.byminute[0] if rrule.byminute else 0
            start = datetime.datetime.combine(
                start_date,
                datetime.time(hour, minute))
            end = datetime.datetime.combine(
                start_date,
                datetime.time(hour, minute)) + \
                datetime.timedelta(minutes=int(rrule_struct['duration']))

            # convert the bounds to datetime if dates were given
            if isinstance(start_bound, datetime.date):
                start_bound = datetime.datetime.combine(
                    start_bound, datetime.time(0, 0, 0))
            if isinstance(end_bound, datetime.date):
                end_bound = datetime.datetime.combine(
                    end_bound, datetime.time(23, 59, 59))

            # filter out all start/end pairs outside of given boundaries
            if (
                (start_bound and end_bound
                    and start >= start_bound and end <= end_bound)

                or (start_bound and not end_bound and start >= start_bound)
                or (not start_bound and end_bound and end <= end_bound)
                or (not start_bound and not end_bound)):
                out.append({'start': start, 'end': end})
    return out


def recurring(schedule):
    """Select the recurring rrules from schedule"""
    return [
        struct for struct in schedule
        if 'BYDAY' in struct['rrule']]


def non_recurring(schedule):
    """Select the non recurring rrules from schedule"""
    return [
        struct for struct in schedule
        if not 'BYDAY' in struct['rrule']]


def consecutives(date1, date2):
    """ If two dates are consecutive, return True, else False"""
    return (
        date1['start'].date() + datetime.timedelta(days=1) == date2['start'].date()
        or date1['start'].date() + datetime.timedelta(days=-1) == date2['start'].date())


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
            if consecutives(inter, dt_intervals[i+1]):
                continue
            else:
                conseq.append(dt_intervals[start: i+1])
                start = i + 1  # next group starts at next item
        else:  # special case of the last item in the list: border effect
            # we text the consecutivity with the previous inter
            if consecutives(inter, dt_intervals[i-1]):
                # add last item to last group
                conseq.append(dt_intervals[start: i+1])
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


class BaseScheduleFormatter(object):
    """Base class for all schedule formatters, defining basic
    formatting methods.

    """
    def __init__(self, schedule, lang):
        self.schedule = schedule
        self.lang = lang

    @lazy_property
    def recurring(self):
        """Select recurring rrules from self.schedule"""
        return recurring(self.schedule)

    @lazy_property
    def non_recurring(self):
        """Select non recurring rrules from self.schedule"""
        return non_recurring(self.schedule)

    @staticmethod
    def format_output(fmt):
        return '\n'.join([item.capitalize().strip() for item in fmt])

    @staticmethod
    def format_day(day):
        return u'1er' if day == 1 else unicode(day)

    @staticmethod
    def dayname(day):
        return calendar.day_name[day].decode('utf-8')

    @staticmethod
    def abbr_dayname(day):
        return calendar.day_abbr[day].decode('utf-8')

    @staticmethod
    def monthname(month):
        return calendar.month_name[month].decode('utf-8')

    @staticmethod
    def abbr_monthname(month):
        return calendar.month_abbr[month].decode('utf-8')

    def format_date(self, dtime):
        """ Format a single date using the litteral month name

        Example: date(2013, 5, 6) -> 6 mai 2013 (in French)

        """
        date = dtime.date()
        return '%s %s %s' % (
            self.format_day(date.day),
            self.monthname(date.month),
            date.year)

    def format_date_interval(self, dt_intervals):
        """ Format a date interval, using the litteral month names

        The dt_intervals list is expected to be sorted.

        3 cases are taken into account:
        1 - different years
        2 - same year but different months
        3 - same year and same month

        Examples:
        1 - 1/2/2013 - 1/2/2014: u"du 1er février 2013 au 1er février 2014"
        2 - 2/4/2013 - 4/6/2013: u"du 2 avril au 4 juin 2013"
        3 - 2/7/2013 - 5/7/2013: u"du 2 au 7 juillet 2013"

        """
        start_day = dt_intervals[0]['start'].day
        start_year = dt_intervals[0]['start'].year
        end_year = dt_intervals[-1]['end'].year
        start_month = dt_intervals[0]['start'].month
        end_month = dt_intervals[-1]['end'].month
        if start_year != end_year:  # different year
            interval = _(u'du %(start)s au %(end)s') % {
                'start': self.format_date(dt_intervals[0]['start']),
                'end': self.format_date(dt_intervals[-1]['end'])}
        elif start_month != end_month:  # same year, different month
            interval = _(u'du %(start_day)s %(start_month)s au %(end)s') % {
                'start_day': self.format_day(start_day),
                'start_month': self.monthname(start_month),
                'end': self.format_date(dt_intervals[-1]['end'])}
        else:  # same year, same month
            interval = _(u'du %(start)s au %(end)s') % {
                'start': self.format_day(start_day),
                'end': self.format_date(dt_intervals[-1]['end'])}
        return interval

    def format_time(self, dt_interval):
        """ Format a single time or a time interval

        In the case where minute = 0, only the hour is displayed

        Examples of single times (where start = end):
        * time(10, 30) -> u"10 h 30"
        * time(20, 30) -> u"20 h"

        Examples of time interval
        * time(10, 20), time(15, 30) -> u"de 10 h 20 à 15 h 30"
        * time(10, 0), time(15, 30) -> u"de 10 h à 15 h 30"

        If start == time(0, 0, 0) and end == time(23, 59, 0), then
        it means that no time must be displayed.

        """
        start = dt_interval['start'].time()
        end = dt_interval['end'].time()

        # case of no specified time (entire day)
        if (start == datetime.time(0, 0, 0) and
            (end == datetime.time(23, 59, 0) or
                end == datetime.time(0, 0, 0))):
            interval = ''
        # case of a single time (no end time)
        elif start.hour == end.hour and start.minute == end.minute:
            interval = _(u'à %(hour)s h %(minute)s') % {
            'hour': start.hour,
            'minute': start.minute or ''}
        else:  # start time and end time
            interval = _(u'de %(st_hour)s h %(st_minute)s à %(en_hour)s h %(en_minute)s') % {
                'st_hour': start.hour or '',
                'st_minute': start.minute or '',
                'en_hour': end.hour or '',
                'en_minute': end.minute or ''}

        # replace potential double spaces (ex: "de 15 h  à ..")
        # because minute == ''
        interval = interval.replace('  ', ' ').strip()
        return interval

    def format_rrule(self, rrule_struct):
        """Format a weekday recurrence rule associated with a duration"""
        rrule = rrulestr(rrule_struct['rrule'])
        # format weekdays
        if len(rrule.byweekday) == 1:
            weekdays = u'le ' + self.dayname(rrule.byweekday[0].weekday)
        else:
            start_wkd, end_wkd = rrule.byweekday[0], rrule.byweekday[-1]
            weekdays_index = [wk.weekday for wk in rrule.byweekday]
            if weekdays_index == range(0, 7):
                weekdays = 'tous les jours'
            elif weekdays_index == range(start_wkd.weekday, end_wkd.weekday + 1):
                weekdays = _(u'du %(start_day)s au %(end_day)s') % {
                    'start_day': self.dayname(start_wkd.weekday),
                    'end_day': self.dayname(end_wkd.weekday)}
            else:
                weekdays = _(u'le') + ' ' + ', '.join(
                    [self.dayname(i) for i in weekdays_index])

        # format dates boundaries
        if rrule.until:
            dates = [{
                'start': rrule.dtstart,
                'end': rrule.until
            }]
            if (dates[0]['end'] - dates[0]['start']).days == 365:
                interval = u""
            else:
                interval = self.format_date_interval(dates)

        # format time interval
        if not rrule.byhour and not rrule.byminute:
            start = datetime.datetime.combine(
                datetime.date.today(),
                datetime.time(0, 0))
        else:
            start = datetime.datetime.combine(
                datetime.date.today(),
                datetime.time(rrule.byhour[0], rrule.byminute[0]))
        end = start + datetime.timedelta(minutes=int(rrule_struct['duration']))
        times = self.format_time({'start': start, 'end': end})

        # assemble
        fmt = ', '.join([part for part in [weekdays, interval, times] if part])
        return fmt


class LongScheduleFormatter(BaseScheduleFormatter):
    """Object in charge of generating the shortest human readable
    representation of a datection context-free schedule list

    """
    @lazy_property
    def time_groups(self):
        """Non recurring rrules grouped by start/end datetimes"""
        _time_groups = to_start_end_datetimes(self.non_recurring)
        # convert rrule structures to start/end datetime lists
        _time_groups = groupby_time(_time_groups)
        for group in _time_groups:
            group.sort(key=lambda date: date['start'])
        return _time_groups

    @lazy_property
    def conseq_groups(self):
        """Group each time group by consecutivity"""
        _conseq_groups = []
        for group in self.time_groups:
            conseq = groupby_consecutive_dates(group)
            _conseq_groups.append(conseq)
        return _conseq_groups

    @staticmethod
    def _shortest(item1, item2):
        """Return item with shortest lenght"""
        return item1 if len(item1) < len(item2) else item2

    @staticmethod
    def _filterby_year_and_month(dates, year, month):
        """ Return all dates in dates occuring at argument year and month """
        return [
            date for date in dates
            if date['start'].year == year
            and date['start'].month == month
        ]

    def format_single_dates_and_interval(self, time_group):
        """ First formatting technique, using dates interval

        This formatting technique uses self.consecutive_groups,
        and displays single dates using the self.format_date method
        and date intervals using the format_date_interval method.

        Example: [[15 mars 2013], [17 mars 2013, 18 mars 2013]]
        Output: u"le 15 mars 2013, du 17 au 18 mars 2013"

        """
        out = []
        for i, conseq_group in enumerate(time_group):
            if len(conseq_group) == 1:  # single start/end datetime in group
                start, end = conseq_group[0]['start'], conseq_group[0]['end']
                if start.date() == end.date():  # a single date
                    # Add prefix before the first date of the group
                    fmt = 'le ' + self.format_date(start) if i == 0 \
                        else self.format_date(start)
                else:  # a date interval
                    fmt = self.format_date_interval(conseq_group)
                out.append(fmt)
            else:
                out.append(self.format_date_interval(conseq_group))
        return out

    def format_date_list(self, time_group):
        """ Second formatting technique, using non-consecutive dates lists

        All the non-consecutive dates are first grouped by years and then by
        months, and returned as a simple list of human readable time expressions,
        expressed in self.lang.

        Example:
        Input: [1 mars 2013, 4 mars 2013, 6 juin 2013, 5 juillet 2014]
        Output: u"le 1er, 4 mars 2013, le 6 juin 2013, le 5 juillet 2014"

        """
        # group the sparse dates by year first
        years = list(set([date['start'].year for date in time_group]))
        out = []
        for year in years:
            # now group the dates by month
            months = sorted(list(set([
                date['start'].month
                for date in time_group
                if date['start'].year == year])))

            # all dates happen in the same month
            if len(months) == 1:
                month = months[0]
                monthdates = self._filterby_year_and_month(time_group, year, month)
                fmt = u'{prefix} {day_list} {month}'.format(
                    prefix=_(u'le') if len(monthdates) == 1 else _(u'les'),
                    day_list=u', '.join(
                        [self.format_day(date['start'].day) for date in monthdates]),
                    month=self.monthname(month))
                out.append(fmt)
            else:  # the dates happen in different months

                for month in months:
                    fmt = _('les') + ' '
                    for i, month in enumerate(months):
                        monthdates = self._filterby_year_and_month(time_group, year, month)
                        fmt += u'{day_list} {month}'.format(
                            day_list=u', '.join(
                                [self.format_day(date['start'].day) for date in monthdates]),
                            month=self.monthname(month))
                        if i != len(months) - 1:
                            if i == len(months) - 2:
                                fmt += ' ' + _(u'et') + ' '
                            else:
                                fmt += ', '
                out.append(fmt)
            # add the year after the last date in the month group
            out[-1] += ' %d' % (year)
        return out

    def display(self):
        fmt = []
        # format recurring rrules
        for rec in self.recurring:
            fmt.append(self.format_rrule(rec))

        # format non recurring rrules
        for time_group, conseq_group in zip(self.time_groups, self.conseq_groups):
            list_fmt = ', '.join(
                self.format_date_list(time_group))
            conseq_fmt = ', '.join(
                self.format_single_dates_and_interval(conseq_group))

            # pick shortest render
            date_fmt = self._shortest(list_fmt, conseq_fmt)

            # concatenate dates and time
            time_fmt = ' ' + self.format_time(time_group[0])
            fmt.append(date_fmt + time_fmt)

        # finally, apply global formatting rules
        return self.format_output(fmt)


class ShortScheduleFormatter(BaseScheduleFormatter):
    """Object in charge of generating the shortest human readable
    representation of a datection schedule list, using a temporal
    reference.

    """
    def __init__(self, schedule, start, end, lang):
        super(ShortScheduleFormatter, self).__init__(schedule, lang)
        self.start, self.end  = start, end

    @lazy_property
    def dates(self):
        """Convert self.schedule to a start/end datetime list and filter
        out the obtained values outside of the (self.start, self.end)
        datetime range

        """
        start = self.start or datetime.date.today()  # filter out passed dates
        dtimes = to_start_end_datetimes(self.schedule, start, self.end)
        # group the filtered values by date
        return sorted(groupby_date(dtimes))

    def format_output(self, text):
        return ', '.join(text).capitalize()

    def format_date(self, dtime, reference):
        d = dtime.date()
        if d == reference:
            return _(u"aujourd'hui")
        elif d == reference + datetime.timedelta(days=1):
            return _(u"demain")
        elif reference < d < reference + datetime.timedelta(days=6):
            # if d is next week, use its weekday name
            return self.dayname(d.isocalendar()[2] - 1)
        else:
            return _(u'le %(shortdate)s') % {
                'shortdate': self.format_short_date(dtime)}

    def format_short_date(self, dtime):
        """ Format a single date using the abbreviated litteral month name

        Example: date(2013, 12, 6) -> 6 déc. (in French)

        """
        date = dtime.date()
        return '%s %s' % (
            self.format_day(date.day),
            self.abbr_monthname(date.month))

    def format_date_summary(self):
        """Format the next dates summary

        Examples:
            * + 1 date
            * + 3 dates

        """
        num = len(self.dates) - 1
        # handle plural/singular case
        msg = gettext.ngettext(
            '+ %(num)d date', '+ %(num)d dates', num) % {'num': num}
        return msg

    def display(self, reference):
        out = []
        if not self.dates:
            return ''
        dt_intervals = self.dates[0]
        fmt_date = self.format_date(dt_intervals[0]['start'], reference)
        fmt_times = [
            self.format_time(dt_interval) for dt_interval in dt_intervals]

        # filter empty results to avoid formatting problems
        fmt_times = filter(lambda x: x, fmt_times)

        if len(fmt_times) == 1:
            msg = u'%s %s' % (fmt_date, fmt_times[0])
        else:

            msg = _('%(date)s %(times)s et %(last_time)s') % {
                'date': fmt_date,
                'times': ', '.join(fmt_times[:-1]),
                'last_time': fmt_times[-1]}
        out.append(msg)
        if len(self.dates) > 1:
            out.append(self.format_date_summary())
        return self.format_output(out)


def display(
        schedule, lang,
        short=False, bounds=(None, None), reference=datetime.date.today()):
    """Format a schedule into the shortest human readable sentence possible

    args:
        schedule: (list) a list of rrule dicts, containing a duration and a RFC rrule
        lang: (str) the wanted output language
        short: (bool) if True
    """
    with calendar.TimeEncoding(getlocale(lang)):
        gettext_lang = getlocale(lang).replace('.UTF-8', '')
        t = gettext.translation(
            domain='display',
            localedir=popath,
            languages=[gettext_lang],
            fallback=True)
        global _
        _ = t.ugettext
        if short:
            start, end = bounds
            return ShortScheduleFormatter(schedule, start, end, lang).\
                display(reference)
        else:
            return LongScheduleFormatter(schedule, lang).display()
