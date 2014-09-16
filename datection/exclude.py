# -*- coding: utf-8 -*-

"""Definition of classes in charge of the exclusion of a timepoint
from another.

"""

from dateutil.rrule import rrulestr

from datection.utils import makerrulestr
from datection.timepoint import Datetime
from datection.timepoint import DatetimeInterval
from datection.timepoint import DateInterval
from datection.timepoint import WeeklyRecurrence
from datection.timepoint import Date
from datection.timepoint import Weekdays


class TimepointExcluder(object):

    def __init__(self, timepoint, excluded):
        self.timepoint = timepoint
        self.excluded = excluded

    def exclude(self):
        if isinstance(self.timepoint, DateInterval):
            if isinstance(self.excluded, Date):
                return self.date_interval_exclude_date(
                    self.timepoint, self.excluded)
            elif isinstance(self.excluded, Weekdays):
                return self.weekdays_exclusion_rrule(
                    self.timepoint, self.excluded)
        elif isinstance(self.timepoint, DatetimeInterval):
            if isinstance(self.excluded, Date):
                return self.datetime_interval_exclude_date(
                    self.timepoint, self.excluded)
            elif isinstance(self.excluded, Weekdays):
                return self.weekdays_exclusion_rrule(
                    self.timepoint, self.excluded)
        elif isinstance(self.timepoint, WeeklyRecurrence):
            if isinstance(self.excluded, Date):
                return self.weekly_recurrence_exclude_date(
                    self.timepoint, self.excluded)
            elif isinstance(self.excluded, Weekdays):
                return self.weekdays_exclusion_rrule(
                    self.timepoint, self.excluded)

    @staticmethod
    def date_interval_exclude_date(date_interval, excluded_date):
        return excluded_date.export()['rrule']

    @staticmethod
    def datetime_interval_exclude_date(datetime_interval, excluded_date):
        if not excluded_date.year:
            excluded_date.year = datetime_interval.date_interval.end_date.year
        if not excluded_date.month:
            excluded_date.month = datetime_interval.date_interval.end_date.month
        excluded_datetime = Datetime(
            excluded_date,
            datetime_interval.time_interval.start_time,
            datetime_interval.time_interval.end_time)
        return excluded_datetime.export()['rrule']

    @staticmethod
    def weekly_recurrence_exclude_date(weekly_recurrence, excluded_date):
        if not excluded_date.year:
            excluded_date.year = weekly_recurrence.date_interval.end_date.year
        if not excluded_date.month:
            excluded_date.month = weekly_recurrence.date_interval.end_date.month
        excluded_weekly_recurrence = WeeklyRecurrence(
            DateInterval(excluded_date, excluded_date),
            weekly_recurrence.time_interval,
            weekly_recurrence.weekdays)
        return excluded_weekly_recurrence.export()['rrule']

    @staticmethod
    def weekdays_exclusion_rrule(timepoint, excluded_weekdays):
        excluded_rrule = rrulestr(timepoint.export()['rrule'])
        excluded_rrule._byweekday = [d.weekday for d in excluded_weekdays.days]
        return makerrulestr(
            start=excluded_rrule.dtstart.date(),
            end=excluded_rrule.until,
            rule=str(excluded_rrule))

    @property
    def valid(self):
        """Wether both timepoints are valid."""
        return self.timepoint.valid and self.excluded.valid

    def future(self, reference=None):
        """A TimepointExclusion is future if the constructive timepoint is."""
        return self.timepoint.future(reference)
