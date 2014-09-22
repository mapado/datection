# -*- coding: utf-8 -*-

"""TODO"""

from dateutil.rrule import weekdays as all_weekdays

from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import Date
from datection.timepoint import DateList
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import DatetimeList
from datection.timepoint import DatetimeInterval
from datection.timepoint import ContinuousDatetimeInterval
from datection.timepoint import WeeklyRecurrence
from datection.exclude import TimepointExcluder


class Times(object):

    """Stores time related structures (Time or TimeInterval) in
    different lists.

    """

    def __init__(self, singles=[], intervals=[], continuous_intervals=[]):
        self.singles = singles
        self.intervals = intervals
        self.continuous_intervals = continuous_intervals

    @classmethod
    def from_time_interval(cls, time_interval):
        if time_interval.is_single_time():
            return Times(singles=[time_interval.start_time])
        else:
            return Times(intervals=[time_interval])


class DateSchedule(object):

    """Associate a date with several possible times."""

    def __init__(self, date, times):
        self.date = date
        self.times = times

    @classmethod
    def from_date(cls, date):
        times = Times(intervals=[Time(0, 0), Time(23, 59)])
        return DateSchedule(date, times)

    @classmethod
    def from_datetime(cls, datetime):
        if datetime.start_time == datetime.end_time:
            times = Times(singles=[datetime.start_time])
        else:
            interval = TimeInterval(datetime.start_time, datetime.end_time)
            times = Times(intervals=[interval])
        return DateSchedule(datetime.date, times)


class DateListSchedule(object):

    """Associate a list of dates with several possible times."""

    def __init__(self, dates, times):
        self.dates = dates
        self.times = times

    @classmethod
    def from_datelist(cls, date_list):
        return DateListSchedule(date_list.dates, Times)

    @classmethod
    def from_datetime_list(cls, datetime_list):
        times = Times.from_time_interval(datetime_list.time_interval)
        return DateListSchedule(
            datetime_list.dates,
            times)


class DateIntervalSchedule(object):

    """Associate a date interval with several possible times and weekdays."""

    def __init__(self, date_interval, times, weekdays, excluded):
        self.date_interval = date_interval
        self.times = times
        self.weekdays = weekdays
        self.excluded = excluded

    @classmethod
    def from_weekly_recurrence(cls, weekly_rec):
        times = Times.from_time_interval(weekly_rec.time_interval)
        return DateIntervalSchedule(
            weekly_rec.date_interval,
            times,
            weekly_rec.weekdays,
            weekly_rec.excluded)

    @classmethod
    def from_date_interval(cls, date_interval):
        return DateIntervalSchedule(
            date_interval,
            Times(intervals=[Time(0, 0), Time(23, 59)]),
            all_weekdays,
            date_interval.excluded)

    @classmethod
    def from_datetime_interval(cls, datetime_interval):
        times = Times.from_time_interval(datetime_interval.time_interval)
        return DateIntervalSchedule(
            datetime_interval.date_interval,
            times,
            all_weekdays,
            datetime_interval.excluded)

    @classmethod
    def from_continuous_datetime_interval(cls, co_datetime_interval):
        ti = TimeInterval(
            co_datetime_interval.start_time,
            co_datetime_interval.end_time)
        di = DateInterval(
            co_datetime_interval.start_date,
            co_datetime_interval.end_date)
        times = Times(continuous_intervals=[ti])
        return DateIntervalSchedule(
            date_interval=di,
            times=times,
            weekdays=all_weekdays,
            excluded=[])


class Schedule(object):

    """Container of timepoints, all coherent with each other.

    All normalized timepoint objects, coherent with each other, are
    contained in a schedule, by being transformed and mapped into 4
    containers:
    * dates
    * date_lists
    * date_intervals
    * continuous_date_intervals

    The 'dates', 'date_lists' and 'continuous_date_intervals' lists
    contain one or several isinstances of respectively DateSchedule,
    DateListSchedule and ContinuousDateIntervalSchedule classes.

    Each instance of these classes has a 'times' attribute, that holds
    two list attributes:
    * singles: a list of TimeInterval which start_time is equal to its
      end_time
    * intervals: a list if TimeInterval which start_time is unequal to
      its end_time

    The 'date_intervals' list attribute contains instances of the
    DateIntervalSchedule class, that also holds a 'times' attribute, and
    also a 'weekdays' list, holding a list of dateutil.rrule.weekday
    isinstances.

    The fact of mapping the timepoints onto such a tree allows for a
    coherency check, and prevents invalid timepoints to be exported
    as an RRule.

    """
    router = {
        Date: (
            'dates',
            DateSchedule.from_date),
        Datetime: (
            'dates',
            DateSchedule.from_datetime),
        DateList: (
            'date_lists',
            DateListSchedule.from_datelist),
        DatetimeList: (
            'date_lists',
            DateListSchedule.from_datetime_list),
        DateInterval: (
            'date_intervals',
            DateIntervalSchedule.from_date_interval),
        DatetimeInterval: (
            'date_intervals',
            DateIntervalSchedule.from_datetime_interval),
        ContinuousDatetimeInterval: (
            'date_intervals',
            DateIntervalSchedule.from_continuous_datetime_interval),
        WeeklyRecurrence: (
            'date_intervals',
            DateIntervalSchedule.from_weekly_recurrence)
    }

    def __init__(self):
        self.dates = []
        self.date_lists = []
        self.date_intervals = []
        self._timepoints = []  # TEMPORARY

    def add(self, timepoint, excluded=None):
        """Add the timepoint to the one of the schedule internal lists,
        if its class is found in the schedule router.

        """
        if type(timepoint) in self.router:
            if not excluded:
                # Get the timepoint transformation method
                container_name, constructor = self.router[type(timepoint)]
            else:
                # perform the exclusion bewteen the 'timepoint' and 'excluded'
                # Timepoints
                excluder = TimepointExcluder(timepoint, excluded)
                excluded = excluder.exclude()
                if excluded is not None:
                    timepoint.excluded.append(excluded)

                # Get the timepoint transformation method
                container_name, constructor = self.router[
                    type(excluder.timepoint)]

            # add timepoint to the schedule
            getattr(self, container_name).append(constructor(timepoint))
            self._timepoints.append(timepoint)  # TEMPORARY
