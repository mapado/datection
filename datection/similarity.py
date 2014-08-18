# -*- coding: utf-8 -*-
"""
Inter rrule distance calculation module
"""

from __future__ import division
from itertools import product as cartesian_product

from datetime import timedelta
from datection.models import DurationRRule


def jaccard_distance(set1, set2):
    """Compute a jaccard distance on the two input sets

    Return the length of the insersection of the 2 sets over the length
    of their union
    """
    if not set1.intersection(set2):
        return 0
    return len(set1.intersection(set2)) / len(set1.union(set2))


def discretise_day_interval(start_datetime, end_datetime):
    """Discretise the day interval of duration_rrule by 30 minutes slots
    """
    out = []
    current = start_datetime
    while current <= end_datetime:
        out.append(current)
        current += timedelta(minutes=30)
    return out


def discretise_schedule(schedule):
    """Discretise the schedule in chunks of 30 minutes"""
    sc_set = set()
    for duration_rrule in schedule:
        drr = DurationRRule(duration_rrule)
        for timepoint in list(drr.rrule):
            discrete_interval = discretise_day_interval(
                start_datetime=timepoint,
                end_datetime=timepoint + timedelta(
                    minutes=drr.duration))
            for d_timepoint in discrete_interval:
                sc_set.add(d_timepoint)
    return sc_set


def similarity(schedule1, schedule2):
    """Returns the jaccard similarity distance bewteen the schedules"""
    discrete_schedule1 = discretise_schedule(schedule1)
    discrete_schedule2 = discretise_schedule(schedule2)
    return jaccard_distance(discrete_schedule1, discrete_schedule2)


def min_distance(drrules1, drrules2):
    """ Calculate minimum absolute time delta of the schedules.

    Return minimum absolute time delta between every drrule first date
    of the schedules.
    """
    drrules1 = [DurationRRule(dr) for dr in drrules1 if dr]
    drrules2 = [DurationRRule(dr) for dr in drrules2 if dr]

    current_minimal = timedelta(365)
    for x, y in cartesian_product(drrules1, drrules2):
        if x.rrule and y.rrule:
            ddistance = abs(x.rrule[0] - y.rrule[0])
            if ddistance < current_minimal:
                current_minimal = ddistance
    return current_minimal
