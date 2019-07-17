# -*- coding: utf-8 -*-

from builtins import object
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
from datection.timepoint import AbstractDateInterval
from datection.timepoint import has_no_timings
from datection.timepoint import has_timings
from datection.timepoint import enrich_with_timings
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
        """Construct a Times object from a TimeInterval instance."""
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
        """Construct a DateSchedule from a Date instance."""
        times = Times(intervals=[TimeInterval(Time(0, 0), Time(23, 59))])
        return DateSchedule(date, times)

    @classmethod
    def from_datetime(cls, datetime):
        """Construct a DateSchedule from a Datetime instance."""
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
        """Construct a DateListSchedule from a DateList instance."""
        times = Times(intervals=[TimeInterval(Time(0, 0), Time(23, 59))])
        return DateListSchedule(date_list.dates, times)

    @classmethod
    def from_datetime_list(cls, datetime_list):
        """Construct a DateListSchedule from a DatetimeList instance."""
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
        """Construct a DateIntervalSchedule from a WeeklyRecurrence instance."""
        times = Times.from_time_interval(weekly_rec.time_interval)
        return DateIntervalSchedule(
            weekly_rec.date_interval,
            times,
            weekly_rec.weekdays,
            weekly_rec.excluded)

    @classmethod
    def from_date_interval(cls, date_interval):
        """Construct a DateIntervalSchedule from a DateInterval instance."""
        return DateIntervalSchedule(
            date_interval,
            Times(intervals=[TimeInterval(Time(0, 0), Time(23, 59))]),
            all_weekdays,
            date_interval.excluded)

    @classmethod
    def from_datetime_interval(cls, datetime_interval):
        """Construct a DateIntervalSchedule from a DatetimeInterval instance."""
        times = Times.from_time_interval(datetime_interval.time_interval)
        return DateIntervalSchedule(
            datetime_interval.date_interval,
            times,
            all_weekdays,
            datetime_interval.excluded)

    @classmethod
    def from_continuous_datetime_interval(cls, co_datetime_interval):
        """Construct a DateIntervalSchedule from a ContunuousDatetimeInterval
        instance.

        """
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
        self.unassigned_timings = []

    @staticmethod
    def transmit_date_interval(timepoint, excluded):
        """
        If the given excluded timepoint is a weekly recurrence with no
        date interval defined, set the date interval of the base timepoint
        (if it has one).
        """
        if (
            isinstance(excluded, WeeklyRecurrence) and
            excluded.date_interval == DateInterval.make_undefined() and
            isinstance(timepoint, (WeeklyRecurrence, AbstractDateInterval))
        ):
            excluded.date_interval = timepoint.date_interval
        return excluded

    def add_exclusion(self, timepoint, excluded_tps):
        """
        Adds the excluded timepoints to the given timepoint

        @param timepoint(Timepoint)
        @param excluded_tps(list(Timepoint) or None)
        """
        if excluded_tps is not None and hasattr(timepoint, 'excluded'):
            for excluded in excluded_tps:
                excluder = TimepointExcluder(timepoint, excluded)
                excluded_str = excluder.exclude()
                if excluded is not None:
                    if isinstance(excluded_str, list):
                        timepoint.excluded.extend(excluded_str)
                    else:
                        timepoint.excluded.append(excluded_str)
                    if (
                        has_timings(timepoint) and
                        has_timings(excluded) and
                        (timepoint.time_interval != excluded.time_interval or
                         timepoint.duration != excluded.duration)
                    ):
                        additional_timepoint = excluded
                        Schedule.transmit_date_interval(
                            timepoint, additional_timepoint)
                        self.add(additional_timepoint)

    def add(self, timepoint, excluded_tps=None):
        """
        Add the timepoint to the one of the schedule internal lists,
        if its class is found in the schedule router.
        """
        if type(timepoint) in self.router:
            # perform the exclusion bewteen the 'timepoint' and 'excluded'
            # Timepoints
            self.add_exclusion(timepoint, excluded_tps)

            # Get the timepoint transformation method
            container_name, constructor = self.router[type(timepoint)]

            # add timepoint to the schedule
            getattr(self, container_name).append(constructor(timepoint))
            if timepoint not in self._timepoints:
                self._timepoints.append(timepoint)  # TEMPORARY

        elif type(timepoint) in [Time, TimeInterval]:
            self.unassigned_timings.append((timepoint, excluded_tps))

    def complete_timings(self):
        """
        Hanldes the unassigned timings by either merging them
        to existing timepoi or by creating new timepoints
        """
        if len(self.unassigned_timings) > 0:

            # Create new timepoints from the timings
            if len(self._timepoints) == 0:
                for timing in self.unassigned_timings:
                    new_tp = WeeklyRecurrence.make_undefined(timing[0])
                    self.add_exclusion(new_tp, timing[1])
                    self._timepoints.append(new_tp)

            # Complete dates without timings with the unassigned timings
            elif any([tp for tp in self._timepoints if has_no_timings(tp)]):
                no_timings = [tp for tp in self._timepoints if has_no_timings(tp)]
                with_timings = [tp for tp in self._timepoints if not has_no_timings(tp)]
                self._timepoints = with_timings

                for tp in no_timings:
                    for timing in self.unassigned_timings:
                        new_tp = enrich_with_timings(tp, timing[0])
                        if tp.span:
                            new_tp.span = tp.span
                        if isinstance(new_tp, (WeeklyRecurrence, AbstractDateInterval)):
                            self.add_exclusion(new_tp, timing[1])
                        self._timepoints.append(new_tp)
