# -*- coding: utf-8 -*-
"""
Inter rrule distance calculation module
"""

from __future__ import division

from dateutil.rrule import rrulestr
from datetime import timedelta


def jaccard_distance(set1, set2):
    """Compute a jaccard distance on the two input sets

    Return the length of the insersection of the 2 sets over the length
    of their union
    """
    if not set1.intersection(set2):
        return 0
    return len(set1.intersection(set2)) / len(set1.union(set2))


def discretise_day_interval(start_datetime, end_datetime):
    """Discretise the day interval of rrule_struct by 1 day slots
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
    for rrule_struct in schedule:
        rrule = rrulestr(rrule_struct['rrule'])
        for timepoint in list(rrule):
            discrete_interval = discretise_day_interval(
                start_datetime=timepoint,
                end_datetime=timepoint + timedelta(
                    minutes=int(rrule_struct['duration'])))
            for d_timepoint in discrete_interval:
                sc_set.add(d_timepoint)
    return sc_set


def similarity(schedule1, schedule2):
    """Returns the jaccard similarity distance bewteen the schedules"""
    discrete_schedule1 = discretise_schedule(schedule1)
    discrete_schedule2 = discretise_schedule(schedule2)
    return jaccard_distance(discrete_schedule1, discrete_schedule2)
