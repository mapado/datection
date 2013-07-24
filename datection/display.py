# -*- coding: utf-8 -*-
"""
Module in charge of transforming a rrule + duraction object into the shortest
human-readable string possible.
"""

import datetime

from dateutil.rrule import *
from collections import defaultdict

from datection.datenames import REVERSE_MONTH, REVERSE_WEEKDAY


class _TimepointGrouper(object):
    """ Object in charge of grouping the result of a to_mongo export,
        to pass it to a TimepointFormatter.

    """
    def __init__(self, schedule):
        """ Flatten the list of list of schedules into a flat list,
            and sort it by start time.

        """
        self.recurring, non_recurring = self.classify_rrules(schedule)
        self.non_recurring = []
        for non_rec in non_recurring:
            self.non_recurring.extend(self.generate_start_end_struct(non_rec))

    @staticmethod
    def generate_start_end_struct(struct):
        out = []
        rrule = rrulestr(struct['rrule'])
        for start_date in list(rrule):
            start = datetime.datetime.combine(
                start_date,
                datetime.time(rrule.byhour[0], rrule.byminute[0]))
            end = datetime.datetime.combine(
                start_date,
                datetime.time(rrule.byhour[0], rrule.byminute[0])) + \
                datetime.timedelta(minutes=struct['duration'])
            out.append({'start': start, 'end': end})
        return out

    @staticmethod
    def classify_rrules(schedule):
        """Classify the rrules into 4 groups:
        recurrent, allday, punctual and time_slot
        """
        # classify the rrules bewteen recurring and non-recurring
        non_recurring = [
            struct for struct in schedule
            if 'BYDAY' not in struct['rrule']]
        recurring = [
            struct for struct in schedule
            if struct not in non_recurring]
        return recurring, non_recurring

    @staticmethod
    def _consecutives(date1, date2):
        """ If two dates are consecutive, return True, else False"""
        return (
            date1['start'] + datetime.timedelta(days=1) == date2['start']
            or date1['start'] + datetime.timedelta(days=-1) == date2['start'])

    def groupby_consecutive_dates(self, time_groups):
        """ Group each group in input time_groups by gathering consecutive dates together

        Example:
        Input: [01/02/2013, 03/02/2013, 04/02/2013, 06/02/2013]
        Output: [[01/02/2013], [03/02/2013, 04/02/2013], [06/02/2013]]

        """
        out = []
        for group in time_groups:
            conseq = []
            start = 0
            for i, date in enumerate(group):
                if i != len(group) - 1:  # if date is not the last item
                    if self._consecutives(date, group[i+1]):
                        continue
                    else:
                        conseq.append(group[start: i+1])
                        start = i + 1  # next group starts at next item
                else:  # special case of the last item in the list: border effect
                    # we text the consecutivity with the previous date
                    if self._consecutives(date, group[i-1]):
                        # add last item to last group
                        conseq.append(group[start: i+1])
                    else:
                        # create new group with only last date
                        conseq.append([date])
            out.append(sorted(conseq, key=lambda item: item[0]['start']))
        return out

    def groupby_time(self):
        """ Group the self.schedule list by start/end time

        All the schedules with the same start/end time are grouped together

        """
        times = defaultdict(list)
        for date in self.non_recurring:
            start_time, end_time = date['start'].time(), date['end'].time()
            grp = '%s-%s' % (start_time.isoformat(), end_time.isoformat())
            times[grp].append(date)  # group dates by time
        return [sorted(group, key=lambda item: item['start']) for group in times.values()]

    def group(self):
        """ Group self.non_recurring by time and also by consecutivity

        The schedules are first grouped by time, ie, all schedules
        occuring at the same start/end time are grouped together.

        Then, each time group is divised into subgroups, containing
        consecutive items.

        Examples (using human readable representations):
        Schedule: [
            15 mars 2013 à 20h,
            16 mars 2013 à 20h,
            18 mars 2013 à 20h,
            20 mars 2013 à 21h]
        Time groups: [
            '20h': [15 mars 2013, 16 mars 2013, 18 mars 2013]
            '21h': [20 mars 2013]
        ]
        Consecutive time groups: [
        '20h': [[15 mars 2013, 16 mars 2013], [18 mars 2013]]
        '21h': [[20 mars 2013]]
        ]

        Both representations are returned.

        """
        time_groups = self.groupby_time()
        for group in time_groups:
            group.sort(key=lambda date: date['start'])
        return time_groups, self.groupby_consecutive_dates(time_groups)


class ScheduleFormatter(object):
    """ Object in charge of generating the shortest human readable
        representation of a datection context-free schedule list

    """
    def __init__(self, schedule, lang):
        """ Group the input schedule by time and consecutivity.

        The time groups are used by the date list formatting technique,
        and the consecutive time groups are used by the time range formatting
        technique.

        """
        tp = _TimepointGrouper(schedule)
        self.time_groups, self.consecutive_groups = tp.group()
        self.recurring = tp.recurring
        self.lang = lang

    @staticmethod
    def _sentencize(fmt):
        return '\n'.join([item.capitalize().strip() for item in fmt])

    @staticmethod
    def _shortest(item1, item2):
        return item1 if len(item1) < len(item2) else item2

    @staticmethod
    def _filterby_year_and_month(dates, year, month):
        """ Return all dates in dates occuring at argument year and month """
        return [
            date for date in dates
            if date['start'].year == year
            and date['start'].month == month
        ]

    def _litteral_month(self, month_number):
        """ Return the litteral month name associated with input month number
            in the language defined by self.lang

        """
        return REVERSE_MONTH[self.lang][str(month_number)]

    @staticmethod
    def format_day(day):
        return u'1er' if day == 1 else unicode(day)

    def format_date(self, schedule):
        """ Format a single date using the litteral montn name

        Example: date(2013, 5, 6) -> 6 mai 2013 (in French)

        """
        date = schedule.date()
        return '%s %s %s' % (
            self.format_day(date.day),
            self._litteral_month(date.month),
            date.year)

    def format_date_interval(self, group):
        """ Format a date interval, using the litteral month names

        3 cases are taken into account:
        1 - different years
        2 - same year but different months
        3 - same year and same month

        Examples:
        1 - 1/2/2013 - 1/2/2014: u"du 1er février 2013 au 1er février 2014"
        2 - 2/4/2013 - 4/6/2013: u"du 2 avril au 4 juin 2013"
        3 - 2/7/2013 - 5/7/2013: u"du 2 au 7 juillet 2013"

        """
        start_day = group[0]['start'].day
        start_year = group[0]['start'].year
        end_year = group[-1]['end'].year
        start_month = group[0]['start'].month
        end_month = group[-1]['end'].month
        if start_year != end_year:  # different year
            interval = u'du %s au %s' % (
                self.format_date(group[0]['start']),
                self.format_date(group[-1]['end']))
        elif start_month != end_month:  # same year, different month
            interval = u'du %s %s au %s' % (
                self.format_day(start_day),
                self._litteral_month(start_month),
                self.format_date(group[-1]['end']))
        else:  # same year, same month
            interval = u'du %s au %s' % (
                self.format_day(start_day), self.format_date(group[-1]['end']))
        return interval

    @staticmethod
    def format_time(sched):
        """ Format a single time or a time interval

        In the case where minute = 0, only the hour is displayed

        Examples of single times (where start = end):
        * time(10, 30) -> u"10h30"
        * time(20, 30) -> u"20h"

        Examples of time interval
        * time(10, 20), time(15, 30) -> u"de 10h20 à 15h30"
        * time(10, 0), time(15, 30) -> u"de 10h à 15h30"

        If start == time(0, 0, 0) and end == time(23, 59, 0), then
        it means that no time must be displayed.

        """
        start = sched['start'].time()
        end = sched['end'].time()

        # case of no specified time (entire day)
        if (start == datetime.time(0, 0, 0) and
            (end == datetime.time(23, 59, 0) or
                end == datetime.time(0, 0, 0))):
            interval = ''
        # case of a single time (no end time)
        elif start.hour == end.hour and start.minute == end.minute:
            interval = u'à %dh%s' % (start.hour, start.minute or '')
        else:  # start time and end time
            interval = u'de %dh%s à %dh%s' % (
                start.hour, start.minute or '', end.hour, end.minute or '')
        return interval

    def format_rrule(self, item):
        """Format a recurrence rule associated with a duration"""
        rrule = rrulestr(item['rrule'])
        # format weekdays
        if len(rrule.byweekday) == 1:
            weekdays = 'le ' + REVERSE_WEEKDAY[self.lang][rrule.byweekday[0].weekday]
        else:
            start_wkd, end_wkd = rrule.byweekday[0], rrule.byweekday[-1]
            weekdays_index = [wk.weekday for wk in rrule.byweekday]
            if weekdays_index == range(0, 7):
                weekdays = 'tous les jours'
            elif weekdays_index == range(start_wkd.weekday, end_wkd.weekday + 1):
                weekdays = 'du %s au %s' % (
                    REVERSE_WEEKDAY[self.lang][start_wkd.weekday],
                    REVERSE_WEEKDAY[self.lang][end_wkd.weekday])
            else:
                weekdays = 'le ' + ', '.join(
                    [REVERSE_WEEKDAY[self.lang][i] for i in weekdays_index])

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
        end = start + datetime.timedelta(minutes=item['duration'])
        dates = {'start': start, 'end': end}
        times = self.format_time(dates)

        # assemble
        fmt = ', '.join([part for part in [weekdays, interval, times] if part])
        return fmt

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
                    fmt = 'le ' + self.format_date(start) if i == 0 else self.format_date(start)
                else:  # a date interval
                    fmt = self.format_date_interval(conseq_group)
                out.append(fmt)
            else:
                out.append(self.format_date_interval(conseq_group))
        return out

    def format_date_list(self, time_group):
        """ Second formatting technique, using non-consecutive dates lists

        All the non-consecutive dates are first grouped by years and then by
        months, and displayed as a simple list.

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
                    prefix='le' if len(monthdates) == 1 else 'les',
                    day_list=', '.join(
                        [self.format_day(date['start'].day) for date in monthdates]),
                    month=self._litteral_month(month))
                out.append(fmt)
            else:  # the dates happen in different months

                for month in months:
                    fmt = 'les '
                    for i, month in enumerate(months):
                        monthdates = self._filterby_year_and_month(time_group, year, month)
                        fmt += u'{day_list} {month}'.format(
                            day_list=', '.join(
                                [self.format_day(date['start'].day) for date in monthdates]),
                            month=self._litteral_month(month))
                        if i != len(months) - 1:
                            if i == len(months) - 2:
                                fmt += ' et '
                            else:
                                fmt += ', '
                out.append(fmt)
            # add the year after the last date in the month group
            out[-1] += ' %d' % (year)
        return out

    def display(self):
        fmt = []
        for rec in self.recurring:
            fmt.append(self.format_rrule(rec))
        for time_group, conseq_time_group in zip(self.time_groups, self.consecutive_groups):
            list_fmt = ', '.join(self.format_date_list(time_group))
            conseq_fmt = ', '.join(self.format_single_dates_and_interval(conseq_time_group))
            date_fmt = self._shortest(list_fmt, conseq_fmt)
            time_fmt = ' ' + self.format_time(time_group[0])
            fmt.append(date_fmt + time_fmt)
        return self._sentencize(fmt)


def display(schedule, lang):
    return ScheduleFormatter(schedule, lang).display()
