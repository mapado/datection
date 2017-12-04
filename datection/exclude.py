# -*- coding: utf-8 -*-

"""
Definition of classes in charge of the exclusion of a timepoint
from another one.

"""

from builtins import object
from dateutil.rrule import rrulestr

from datection.utils import makerrulestr
from datection.utils import stringify_rrule
from datection.timepoint import Datetime
from datection.timepoint import DatetimeInterval
from datection.timepoint import DateInterval
from datection.timepoint import WeeklyRecurrence
from datection.timepoint import Date
from datection.timepoint import DateList
from dateutil.rrule import FREQNAMES


class TimepointExcluder(object):

    """Performs an exclusion betweeen a constructive rrule and an
    excluded one.

    """

    def __init__(self, timepoint, excluded):
        self.timepoint = timepoint
        self.excluded = excluded

    def exclude(self):
        """Return the RRule excluding self.excluded from self.timepoint

        The exclusion strategy depends on the type of each timepoint.

        """
        if isinstance(self.timepoint, DateInterval):
            # Exclude date from date interval
            if isinstance(self.excluded, Date):
                return self.date_interval_exclude_date(
                    self.timepoint, self.excluded)
            # Exclude date list from date interval
            if isinstance(self.excluded, DateList):
                return self.date_interval_exclude_datelist(
                    self.timepoint, self.excluded)
            # Exclude date interval from date interval
            if isinstance(self.excluded, DateInterval):
                return self.date_interval_exclude_dateinterval(
                    self.timepoint, self.excluded)
            # Exclude every occurence of weekday(s) from the date interval
            elif isinstance(self.excluded, WeeklyRecurrence):
                return self.weekdays_exclusion_rrule(
                    self.timepoint, self.excluded)
        elif isinstance(self.timepoint, DatetimeInterval):
            # Exclude a date from a datetime interval
            if isinstance(self.excluded, Date):
                return self.datetime_interval_exclude_date(
                    self.timepoint, self.excluded)
            # Exclude every occurence of weekday(s) from the datetime interval
            elif isinstance(self.excluded, WeeklyRecurrence):
                return self.weekdays_exclusion_rrule(
                    self.timepoint, self.excluded)
        elif isinstance(self.timepoint, WeeklyRecurrence):
            # Exclude a date from a weekly recurrence
            if isinstance(self.excluded, Date):
                return self.weekly_recurrence_exclude_date(
                    self.timepoint, self.excluded)
            # Usecase: "tous les jours sauf jeudi"
            elif isinstance(self.excluded, WeeklyRecurrence):
                # "tous les jours sauf le jeudi, à 18h"
                if (self.timepoint.time_interval.undefined and
                   not self.excluded.time_interval.undefined):
                    self.timepoint.time_interval = self.excluded.time_interval
                if (not self.timepoint.date_interval.undefined and
                   self.excluded.date_interval.undefined):
                    self.excluded.date_interval = self.timepoint.date_interval
                return self.excluded.export()['rrule']

    @staticmethod
    def date_interval_exclude_date(date_interval, excluded_date):
        """Return an exclusion RRule for the excluded date from the
        date interval.

        If the excluded date is missing a year, it will inherit it from
        the date_interval end_date.

        """
        if not excluded_date.year:
            excluded_date.year = date_interval.end_date.year
        return excluded_date.export()['rrule']

    @staticmethod
    def date_interval_exclude_datelist(date_interval, excluded_datelist):
        """Return an exclusion RRule for the excluded date list from the
        date interval.

        If the excluded date list is missing a year, it will inherit it from
        the date_interval end_date.

        """
        if not excluded_datelist.year:
            excluded_datelist.year = date_interval.end_date.year
        return [excluded_date['rrule'] for excluded_date in excluded_datelist.export()]

    @staticmethod
    def date_interval_exclude_dateinterval(
            date_interval, excluded_dateinterval):
        """Return an exclusion RRule for the excluded date interval from the
        date interval.

        If the excluded date interval is missing a year, it will inherit it from
        the date_interval end_date.

        """
        if not excluded_dateinterval.year:
            excluded_dateinterval.year = date_interval.end_date.year
        return excluded_dateinterval.export()['rrule']

    @staticmethod
    def datetime_interval_exclude_date(datetime_interval, excluded_date):
        """Return an exclusion RRule for the excluded date from the
        datetime interval.

        If the excluded date is missing a year, it will inherit it from
        the date interval end_date.

        """
        if not excluded_date.year:
            excluded_date.year = datetime_interval.date_interval.end_date.year
        excluded_datetime = Datetime(
            excluded_date,
            datetime_interval.time_interval.start_time,
            datetime_interval.time_interval.end_time)
        return excluded_datetime.export()['rrule']

    @staticmethod
    def weekly_recurrence_exclude_date(weekly_recurrence, excluded_date):
        """Return an exclusion RRule for the excluded date from the
        weekly recurrence.

        If the excluded date is missing a year, it will inherit it from
        the weekly recurrence date interval end_date.

        """
        if not excluded_date.year:
            excluded_date.year = weekly_recurrence.date_interval.end_date.year
        excluded_weekly_recurrence = WeeklyRecurrence(
            DateInterval(excluded_date, excluded_date),
            weekly_recurrence.time_interval,
            weekly_recurrence.weekdays)
        return excluded_weekly_recurrence.export()['rrule']

    @staticmethod
    def weekdays_exclusion_rrule(timepoint, excluded_weekdays):
        """Return an exclusion RRule for the excluded weekdays from the
        constructive timepoint.

        """
        excluded_rrule = rrulestr(timepoint.export()['rrule'])
        excluded_rrule._freq = FREQNAMES.index('WEEKLY')
        excluded_rrule._original_rule['byweekday'] = [
            d for d in excluded_weekdays.weekdays]

        return makerrulestr(
            start=excluded_rrule._dtstart.date(),
            end=excluded_rrule._until,
            rule=stringify_rrule(excluded_rrule))
