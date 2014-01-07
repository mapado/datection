# -*- coding: utf-8 -*-

"""
Merge several datection Timepoints objects together
"""

import itertools
import datetime

from datection.normalize import DateInterval
from datection.normalize import DateTimeInterval
from datection.normalize import WeekdayRecurrence
from datection.normalize import WeekdayIntervalRecurrence
from datection.normalize import AllWeekdayRecurrence

# Recurrence scenarios
WEEKDAY_REC = (
    WeekdayRecurrence,
    WeekdayIntervalRecurrence,
    AllWeekdayRecurrence)

# Interval scenarios
INTERVALS = (DateInterval, DateTimeInterval)

# all day interval
DAY_START_END = [datetime.time(0, 0, 0), datetime.time(23, 59, 59)]


def merge(timepoints):
    intervals = [t for t in timepoints if isinstance(t, INTERVALS)]
    wk_rec = [t for t in timepoints if isinstance(t, WEEKDAY_REC)]
    if len(wk_rec) > 0:
        merged_wk_rec = _merge_weekdays(wk_rec)
        if len(intervals) == 1:
            # merged_wk_rec = _merge_weekdays(wk_rec)
            merged_bounds = _merge_date_bounds(
                bounded=intervals[0],
                weekday_recurrences=merged_wk_rec)
            filtered = [
                t for t in timepoints if t not in wk_rec if t not in intervals]
            return filtered + merged_bounds
        else:
            filtered = [t for t in timepoints if t not in wk_rec]
            return filtered + merged_wk_rec
    else:
        return timepoints


def _merge_weekdays(recurrences):
    """Merge weekday recurrences sharing the same start/end date bounds"""
    merges = []
    # group weekday recurrences by date
    boundaries = lambda wk: (wk.start_datetime.date(), wk.end_datetime.date())
    day_start_end = lambda t: True if t not in DAY_START_END else False

    recurrences = sorted(recurrences, key=boundaries)
    for bounds, group in itertools.groupby(recurrences, key=boundaries):
        group = list(group)
        weekday_set = list(set([day for rec in group for day in rec.weekdays]))
        # As we grouped together weekday recurrences with potential different
        # start/end time, we need to select the most specific one
        # ie: not 00:00:00 and 23:59:59
        start_time = (filter(
            day_start_end,
            [rec.start_datetime.time() for rec in group])
            or [datetime.time(0, 0)])
        end_time = (filter(
            day_start_end,
            [rec.end_datetime.time() for rec in group])
            or [datetime.time(23, 59)])

        # if several start/end times coexist, do not merge the group
        if len(set(start_time)) > 1 or len(set(end_time)) > 1:
            merges.extend(group)
        else:
            start = datetime.datetime.combine(bounds[0], start_time[0])
            end = datetime.datetime.combine(bounds[1], end_time[0])
            merge = WeekdayRecurrence(
                weekdays=weekday_set, start_datetime=start, end_datetime=end,
                text=[item.text for item in group])
            merges.append(merge)
    return merges


def _merge_date_bounds(bounded, weekday_recurrences):
    """


    """
    out = []
    for rec in weekday_recurrences:
        if isinstance(bounded, DateTimeInterval):
            # make the weekday recurrence inherit from the datetime
            # boudaries of the DateTimeInterval
            start = datetime.datetime.combine(
                bounded.date_interval.start_date.to_python(),
                bounded.time_interval.start_time.to_python())
            rec.start_datetime = start
            end = datetime.datetime.combine(
                bounded.date_interval.end_date.to_python(),
                (bounded.time_interval.end_time
                    or bounded.time_interval.start_time).to_python())
            rec.end_datetime = end
        else:
            # make the weekday recurrence inherit from the date
            # boundaries of the DateInterval, combining them with the
            # (possible) time boundaries of the weekday recurrence

            if rec.start_datetime.time() != datetime.time(0, 0):
                start_time = rec.start_datetime.time()
            else:
                start_time = datetime.time(0, 0)
            if rec.end_datetime.time() != datetime.time(23, 59):
                end_time = rec.end_datetime.time()
            else:
                end_time = datetime.time(23, 59)

            start = datetime.datetime.combine(
                bounded.start_date.to_python(),
                start_time)
            rec.start_datetime = start
            end = datetime.datetime.combine(
                bounded.end_date.to_python(),
                end_time)
            rec.end_datetime = end

        # merge all timepoints text together
        if isinstance(rec.text, basestring):
            rec.text = [rec.text, bounded.text]
        else:
            rec.text.append(bounded.text)

        out.append(rec)
    return out
