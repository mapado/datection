# -*- coding: utf-8 -*-
"""
Inter rrule distance calculation module
"""

from __future__ import division

from dateutil.rrule import rrulestr
from datetime import timedelta, time, datetime


def jaccard_distance(set1, set2):
    """Compute a jaccard distance on the two input sets

    Return the length of the insersection of the 2 sets over the lengt
    of their union
    """
    if not set1 and not set2:
        return 1.
    try:
        return len(set1.intersection(set2)) / len(set1.union(set2))
    except ZeroDivisionError:
        return 0


def discretise_time_slot(rrule_struct):
    """Discretise the time interval of rrule_struct by 30 minutes slots
    """
    out = []
    rrule = rrulestr(rrule_struct['rrule'])
    start_datetime = datetime.combine(
        rrule.dtstart,
        time(rrule.byhour[0], rrule.byminute[0]))
    end_datetime = start_datetime + timedelta(
        minutes=rrule_struct['duration'])
    discrete_time = start_datetime
    while discrete_time <= end_datetime:
        out.append(discrete_time.time())
        discrete_time += timedelta(minutes=30)
    return out


def discretise_day_interval(rrule):
    """Discretise the day interval of rrule_struct by 1 day slots
    """
    out = []
    discrete_day = rrule.dtstart
    if not rrule.until:
        return [rrule.dtstart]
    while discrete_day <= rrule.until:
        out.append(discrete_day.date())
        discrete_day += timedelta(days=1)
    return out


def combine_weekdays(schedule):
    weekdays = set()
    for rrule_struct in schedule:
        rrule = (rrulestr(rrule_struct['rrule']))
        for wk in (w.weekday for w in rrule.byweekday):
            weekdays.add(wk)
    return weekdays


def combine_duration(schedule):
    day_span = set()
    for rrule_struct in schedule:
        rrule = (rrulestr(rrule_struct['rrule']))
        for day in discretise_day_interval(rrule):
            day_span.add(day)
    return day_span


def combine_schedule(schedule):
    time_span = set()
    for rrule_struct in schedule:
        for t in discretise_time_slot(rrule_struct):
            time_span.add(t)
    return time_span


def weekday_similarity(weekdays1, weekdays2):
    """Return the weekday similarity bewteen the two weekday sets

    The weekday similarity is defined as the jaccard distance of the weekday
    set of each rrule.

    The similarity is expressed as a float between 0 and 1, 1 being
    total similarity.

    """
    return jaccard_distance(weekdays1, weekdays2)


def schedule_similarity(time_slot1, time_slot2):
    """Return the schedule similarity bewteen the two time slots set

    The weekday similarity is defined as the jaccard distance of the
    discretised time slots intervals set of each rrule_struct.

    The rrule time slot are discretised with an interval of 30 minutes.

    The similarity is expressed as a float between 0 and 1, 1 being
    total similarity.

    """
    return jaccard_distance(time_slot1, time_slot2)


def duration_similarity(day_set1, day_set2):
    """Return the duration similarity bewteen the two rrules

    The schedule similarity is defined as the jaccard distance of the
    day set of each rrule_struct.

    The similarity is expressed as a float between 0 and 1, 1 being
    total similarity.

    """
    return jaccard_distance(day_set1, day_set2)


def similarity(schedule1, schedule2):
    """Compute the similarity score bewteen the two argument schedules

    The similarity score is expressed as a float between 0 and 1, 1 being
    total similarity, and is calculated as the average of the jaccard
    similarity coefficient of the following attributes:
     * weekday
     * schedule
     * duration (in days)

    """
    weekday_set1 = combine_weekdays(schedule1)
    weekday_set2 = combine_weekdays(schedule2)
    wk_sim = weekday_similarity(weekday_set1, weekday_set2)

    day_set1 = combine_duration(schedule1)
    day_set2 = combine_duration(schedule2)
    du_sim = duration_similarity(day_set1, day_set2)

    time_slots1 = combine_schedule(schedule1)
    time_slots2 = combine_schedule(schedule2)
    sc_sim = schedule_similarity(time_slots1, time_slots2)

    return sum((wk_sim, sc_sim, du_sim)) / 3
