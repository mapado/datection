# -*- coding: utf-8 -*-

"""
Merge several datection Timepoints objects together
"""

import itertools
import datetime

from .normalize import DateInterval, DateTimeInterval, WeekdayRecurrence, \
    WeekdayIntervalRecurrence, AllWeekdayRecurrence

WEEKDAY_REC = (
    WeekdayRecurrence,
    WeekdayIntervalRecurrence,
    AllWeekdayRecurrence)

INTERVALS = (DateInterval, DateTimeInterval)


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
            filtered = [t for t in timepoints if t not in wk_rec if t not in intervals]
            return filtered + merged_bounds
        else:
            filtered = [t for t in timepoints if t not in wk_rec]
            return filtered + merged_wk_rec
    else:
        return timepoints


def _merge_weekdays(weekday_recurrences):
    """Merge weekday recurrences sharing the same start/end bounds"""
    merges = []
    boundaries = lambda wk: (wk.start_datetime, wk.end_datetime)
    weekday_recurrences = sorted(
        weekday_recurrences, key=boundaries)
    for bounds, group in itertools.groupby(weekday_recurrences, key=boundaries):
        weekday_set = list(set([day for rec in group for day in rec.weekdays]))
        merge = WeekdayRecurrence(
            weekdays=weekday_set, start=bounds[0], end=bounds[1])
        merges.append(merge)
    return merges


def _merge_date_bounds(bounded, weekday_recurrences):
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
        out.append(rec)
    return out
