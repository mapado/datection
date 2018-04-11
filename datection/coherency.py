# -*- coding: utf-8 -*-

"""Definition of utilities ensuring the coherency of a series of
Timepoint objects. The Timepoints bringing redundancy will be removed.

"""

from builtins import object
from copy import deepcopy
from collections import Counter
from datetime import datetime

from datection.timepoint import AbstractDate
from datection.timepoint import AbstractDateInterval
from datection.timepoint import WeeklyRecurrence
from datection.timepoint import DateInterval
from datection.timepoint import ORDERED_DAYS
from datection.timepoint import Date
from datection.timepoint import Datetime
from datection.timepoint import TimeInterval


class TimepointCoherencyFilter(object):

    """Object in charge of removing Timepoints from a list when it only
    bring redundant information.

    """

    def __init__(self, timepoints):
        self.timepoints = timepoints

    @property
    def date_intervals(self):
        """
        The list of all date(time) intervals instances among the
        timepoint list.

        """
        return [
            t for t in self.timepoints
            if isinstance(t, AbstractDateInterval)]

    @property
    def dates(self):
        """
        The list of all date(time) instances among the timepoint list.
        """
        return [t for t in self.timepoints if isinstance(t, AbstractDate)]

    @property
    def weekly_recurrences(self):
        return [t for t in self.timepoints if isinstance(t, WeeklyRecurrence)]

    def deduplicate_date_interval_and_dates(self):
        """
        Remove the date intervals which dates are all re-defined by
        other independant dates in the timepoint list.

        Example:
        >>> timepoints = [
            <DateInterval: 2015/03/02 - 2015/03/03>,
            Date(2015, 03, 02),
            Date(2015, 03, 03)]
        >>> cf = CoherencyFilter(timepoints)
        >>> cf.deduplicate_date_interval_and_dates()
        >>> cf.timepoints
        [Date(2015, 03, 02), Date(2015, 03, 03)]

        """
        timepoints = self.timepoints[:]
        indep_generated_dates = (d.to_python() for d in self.dates)
        indep_generated_dates = [
            (d.date() if isinstance(d, datetime) else d)
            for d in indep_generated_dates]

        # Remove an interval from the timepoints if all its dates are
        # already generated by simple dates
        for interval in self.date_intervals:
            if all([d in indep_generated_dates for d in interval.to_python()]):
                timepoints.remove(interval)
        self.timepoints = timepoints

    def inherit_date_lapse(self):
        """
        Intersect datetime range timepoint with infinite patterns

        Example:
        >>> timepoints = [
            <DatetimeInterval (2014/10/02 - 2014/10/11) (0:00 - 23:59)>,
            <WeeklyRecurrence -
                (0001/01/01 - 9999/12/31) ([TH, FR, SA]) (0:00 - 23:59)>]
        >>> cf = CoherencyFilter(timepoints)
        >>> cf.intersect_weeklyreccurence_and_datetimeinterval()
        >>> cf.timepoints
            [<WeeklyRecurrence -
                (2014/10/02 - 2014/10/11) ([TH, FR, SA]) (19:00 - 23:00)>]]
        """
        tp_infinites = []
        tp_date_ranges = []
        tp_not_concerned = []

        for tp in self.timepoints[:]:
            if isinstance(tp, WeeklyRecurrence):
                if 'UNTIL' not in tp.date_interval.rrulestr:
                    tp_infinites.append(tp)
                else:
                    tp_date_ranges.append(tp)
            elif isinstance(tp, AbstractDateInterval):
                tp_date_ranges.append(tp)
            else:
                tp_not_concerned.append(tp)

        if tp_date_ranges and tp_infinites:
            # pattern identified now intersect
            timepoints = []
            for tp_dr in tp_date_ranges:
                for tp_inf in tp_infinites[:]:
                    if isinstance(tp_dr, DateInterval):
                        if tp_inf.date_interval.undefined:
                            tp_inf.date_interval = tp_dr
                    else:
                        if tp_inf.time_interval.undefined:
                            tp_inf.time_interval = tp_dr.time_interval

                        if tp_inf.date_interval.undefined:
                            tp_inf.date_interval = tp_dr.date_interval

                    timepoints.append(tp_inf)
            self.timepoints = timepoints + tp_not_concerned

    def deduplicates_weekly_recurrences_and_dates(self):
        """
        When we have a very general weekly recurrence that matches a single date (
        same weekday and timing), it is most likely that this weekly recurrence was
        wrongly parsed.
        """
        def date_match_weekly(date, weekly):
            """"""
            return (
                len(weekly.weekdays) == 1 and
                weekly.weekdays[0] == ORDERED_DAYS[date.day_of_week()] and (
                    isinstance(date, Date) and weekly.time_interval == TimeInterval.make_all_day() or
                    isinstance(date, Datetime) and date.start_time == weekly.time_interval.start_time
                )
            )

        timepoints = self.timepoints[:]
        for weekly in self.weekly_recurrences:
            if any(date_match_weekly(date, weekly) for date in self.dates):
                timepoints.remove(weekly)
        self.timepoints = timepoints

    def apply_coherency_rules(self):
        """Call every coherency rules."""
        self.inherit_date_lapse()
        self.deduplicate_date_interval_and_dates()
        self.deduplicates_weekly_recurrences_and_dates()
        return self.timepoints


class RRuleCoherencyFilter(object):

    """Object in charge of removing rrules from a list by applying a set
    of heuristics.

    """

    MAX_SINGLE_DATE_RRULES = 40
    MAX_SMALL_DATE_INTERVAL_RRULES = 5
    MAX_LONG_DATE_INTERVAL_RRULES = 2
    MAX_UNLIMITED_DATE_INTERVAL_RRULES = 1

    def __init__(self, drrs):
        self.drrs = drrs

    def apply_single_date_coherency_heuristics(self):
        """If at least one rrule describing a single date is present in
        the DurationRRule list, remove all rrules not describing another
        single date or a small date interval.

        """
        if any(drr.single_date for drr in self.drrs):
            out = [
                drr for drr in self.drrs
                if drr.single_date
                or drr.small_date_interval]
            self.drrs = out

    def apply_long_date_interval_coherency_heuristics(self):
        """If at least one rrule describing a long date interval is
        present in the DurationRRule list, remove all rrules not
        describing another long date interval.

        """
        if any(drr.long_date_interval for drr in self.drrs):
            out = [
                drr for drr in self.drrs if drr.long_date_interval]
            self.drrs = out

    def apply_unlimited_date_interval_coherency_heuristics(self):
        """If at least one rrule describing a, unlimited date interval
        is present in the DurationRRule list, remove all rrules not
        describing another unlimited date interval.

        """
        if any(drr.unlimited_date_interval for drr in self.drrs):
            out = [
                drr for drr in self.drrs if drr.unlimited_date_interval]
            self.drrs = out

    def apply_single_date_number_coherency_heuristics(self):
        """Keep the 40 first single date rrules."""
        out = []
        kept_single_date_rrules = 0
        for drr in self.drrs:
            if drr.single_date:
                if kept_single_date_rrules < self.MAX_SINGLE_DATE_RRULES:
                    kept_single_date_rrules += 1
                    out.append(drr)
            else:
                out.append(drr)
        self.drrs = out

    def apply_small_date_interval_number_coherency_heuristics(self):
        """Keep only the 5 first small date interval rrules."""
        out = []
        kept_small_date_interval_rrules = 0
        for drr in self.drrs:
            if drr.small_date_interval:
                if (kept_small_date_interval_rrules <
                        self.MAX_SMALL_DATE_INTERVAL_RRULES):
                    kept_small_date_interval_rrules += 1
                    out.append(drr)
            else:
                out.append(drr)
        self.drrs = out

    def apply_long_date_interval_number_coherency_heuristics(self):
        """Keep only the 2 long date interval rrules per weekday."""
        def authorized_weekday(w):
            return (kept_long_date_intervals[w] <
                    self.MAX_LONG_DATE_INTERVAL_RRULES)

        out = []
        kept_long_date_intervals = Counter()
        for drr in self.drrs:
            if drr.long_date_interval:
                if drr.rrule._byweekday:
                    if all([authorized_weekday(w) for w in drr.rrule._byweekday]):
                        for w in drr.rrule._byweekday:
                            kept_long_date_intervals[w] += 1
                        _drr = deepcopy(drr)
                        out.append(drr)
                    else:
                        for w in drr.rrule._byweekday:
                            if authorized_weekday(w):
                                kept_long_date_intervals[w] += 1
                                _drr = deepcopy(drr)
                                _drr.set_weekdays((w, ))
                                out.append(_drr)
            else:
                out.append(drr)
        self.drrs = out

    def apply_unlimited_date_interval_number_coherency_heuristics(self):
        """Keep only the 1 unlimited date interval rrules per weekday."""

        def authorized_weekday(w):
            return (kept_unlimited_date_intervals[w] <
                    self.MAX_UNLIMITED_DATE_INTERVAL_RRULES)

        out = []
        kept_unlimited_date_intervals = Counter()
        for drr in self.drrs:
            if drr.unlimited_date_interval:
                if drr.rrule._byweekday:
                    if all([authorized_weekday(w) for w in drr.rrule._byweekday]):
                        for w in drr.rrule._byweekday:
                            kept_unlimited_date_intervals[w] += 1
                        _drr = deepcopy(drr)
                        out.append(drr)
                    else:
                        for w in drr.rrule._byweekday:
                            if authorized_weekday(w):
                                kept_unlimited_date_intervals[w] += 1
                                _drr = deepcopy(drr)
                                _drr.set_weekdays((w, ))
                                out.append(_drr)
            else:
                out.append(drr)
        self.drrs = out

    def apply_day_level_collison_coherency_heuristics(self):
        pass

    def apply_rrule_type_coherency_heuristics(self):
        """Apply coherency heuristics based on the type of the rrules.

        * Single dates can only cohabit with other single dates and
        small date intervals. All the other rrules must be discarded.
        * Large date interval can only cohabit with other long date
        intervals. All other rrules must be discarded.
        * Unlimited date intervals can only cohabit with other unlimited
        date intervals. All other rrules must be discarded.

        """
        self.apply_single_date_coherency_heuristics()
        self.apply_long_date_interval_coherency_heuristics()
        self.apply_unlimited_date_interval_coherency_heuristics()

    def apply_rrule_size_coherency_heuristics(self):
        """Apply coherency heuristics based on the size of the rrules.

        * There can be at most 40 single dates rrules
        * There can be at most 5 small date interval rrules
        * There can be at most 2 long date interval rrules per
        described weekday
        * There can be at most 1 unlimited date interval rrule per
        described weekday

        """
        self.apply_single_date_number_coherency_heuristics()
        self.apply_small_date_interval_number_coherency_heuristics()
        self.apply_long_date_interval_number_coherency_heuristics()

    def apply_rrule_day_level_coherency_heuristics(self):
        """Apply coherency heuristics based on the day level of the
        rrules.

        * Several RRules cannot generate the same day AND the same time.

        """
        self.apply_day_level_collison_coherency_heuristics()

    def apply_coherency_heuristics(self):
        """Apply all coherency heuristics, and return the filtered list
        of DurationRRule objects.

        """
        self.apply_rrule_type_coherency_heuristics()
        self.apply_rrule_size_coherency_heuristics()
        self.apply_rrule_day_level_coherency_heuristics()
        return self.drrs
