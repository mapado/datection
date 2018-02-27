# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
import sys
import six
import datetime
from collections import defaultdict
import locale as _locale

from datection.models import DurationRRule
from datection.timepoint import DAY_START
from datection.timepoint import DAY_END


def get_drr(drr):
    """Return a DurationRRule object given a dict or a DurationRRule."""
    return DurationRRule(drr) if isinstance(drr, dict) else drr


def get_date(d):
    """ Return a date object, given a datetime or a date. """
    return d.date() if isinstance(d, datetime.datetime) else d


def get_current_date():
    """ Return the current date. """
    return datetime.date.today()


def get_time(d):
    """Return a time object, given a datetime or a time."""
    return d.time() if isinstance(d, datetime.datetime) else d


def all_day(start, end):
    """Return True if the start/end bounds correspond to an entie day."""
    start_time = get_time(start)
    if start_time == datetime.time(0, 0):
        if end is None:
            return True
        end_time = get_time(end)
        if (end_time == datetime.time(23, 59) or end_time == datetime.time(0, 0)):
            return True
    return False


def group_recurring_by_day(recurrings):
    """
    Groups the given WeeklyRecurences by weekay index

    @param recurrings: list(WeeklyRecurences)
    """
    out = defaultdict(list)
    for rec in recurrings:
        key = "_".join([str(i) for i in rec.weekday_indexes])
        out[key].append(rec)
    return [v for k, v in sorted(out.items())]

def hash_same_date_pattern(time_group):
    """
    Get hash with unique string for pattern with same date

    :time_group: [{'start': datetime(), 'end': datetime()},]
    :return: unique string for pattern with same date
    """
    return "|".join(["{} {}".format(
        tp['start'].date(),
        tp['end'].date()
    ) for tp in time_group])


def groupby_consecutive_dates(dt_intervals):
    """
    Group the members of dt_intervals by consecutivity

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
    """
    Group the dt_intervals list by start/end time

    All the schedules with the same start/end time are grouped together
    and sorted in increasing order.
    """
    times = defaultdict(list)
    for inter in dt_intervals:
        start_time, end_time = inter['start'].time(), inter['end'].time()
        grp = '%s-%s' % (start_time.isoformat(), end_time.isoformat())
        times[grp].append(inter)  # group dates by time
    return sorted([group
        for time_group, group in sorted(times.items())],
        key=lambda item:item[0]["start"])

def groupby_date(dt_intervals):
    """
    Group the dt_intervals list by start date

    All the schedules with the same start time are grouped together
    and sorted in increasing order.
    """
    dates = defaultdict(list)
    for inter in dt_intervals:
        start_date = inter['start'].date()
        dates[start_date.isoformat()].append(inter)  # group dates by time
    return sorted([group
        for date_group, group in sorted(dates.items())],
        key=lambda item:item[0]["start"])

def group_recurring_by_date_interval(recurrings):
    """
    Groups the given WeeklyRecurences by date interval

    @param recurrings: list(WeeklyRecurences)
    """
    out = defaultdict(list)
    for rec in recurrings:
        out[rec.date_interval].append(rec)
    return [value for (key, value) in sorted(out.items())]


def consecutives(date1, date2):
    """ If two dates are consecutive, return True, else False"""
    date1 = date1['start'].date()
    date2 = date2['start'].date()
    return (date1 + datetime.timedelta(days=1) == date2 or
            date1 + datetime.timedelta(days=-1) == date2)


def get_shortest(item1, item2):
    """Return item with shortest lenght"""
    return item1 if len(item1) < len(item2) else item2


def to_start_end_datetimes(schedule, start_bound=None, end_bound=None):
    """
    Convert each schedule member (DurationRRule instance) to a dict
    of start/end datetimes.
    """
    out = []
    for drr in schedule:
        for start_date in drr:
            hour = list(drr.rrule._byhour)[0] if drr.rrule._byhour else 0
            minute = list(drr.rrule._byminute)[0] if drr.rrule._byminute else 0
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
            if (end.date() == start.date() + datetime.timedelta(days=1)) and end.hour <= 7:
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

class TemporaryLocale(object):  # pragma: no cover
    """
    Temporarily change the current locale using a context manager.
    """
    def __init__(self, category, locale):
        self.category = category
        if not six.PY3:
            self.locale = locale.encode('utf-8')
        else:
            self.locale = locale
        self.oldlocale = _locale.getlocale(category)

    def __enter__(self):
        _locale.setlocale(self.category, self.locale)

    def __exit__(self, exception_type, exception_value, traceback):
        _locale.setlocale(self.category, self.oldlocale)
