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
    return len(set1.intersection(set2)) / len(set1.union(set2))

def weekday_similarity(rrule1, rrule2):
    """Return the weekday similarity bewteen the two rrules

    The weekday similarity is defined as the jaccard distance of the weekday
    set of each rrule.

    The similarity is expressed as a float between 0 and 1, 1 being
    total similarity.

    """
    weekdays1 = set([wk.weekday for wk in rrule1.byweekday])
    weekdays2 = set([wk.weekday for wk in rrule2.byweekday])
    return jaccard_distance(weekdays1, weekdays2)


def schedule_similarity(rrule_struct1, rrule_struct2):
    """Return the schedule similarity bewteen the two rrules

    The weekday similarity is defined as the jaccard distance of the
    discretised time slots intervals set of each rrule_struct.

    The rrule time slot are discretised with an interval of 30 minutes.

    The similarity is expressed as a float between 0 and 1, 1 being
    total similarity.

    """
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
            out.append(discrete_time)
            discrete_time += timedelta(minutes=30)
        return out

    time_slot1 = set(discretise_time_slot(rrule_struct1))
    time_slot2 = set(discretise_time_slot(rrule_struct2))
    return jaccard_distance(time_slot1, time_slot2)


def duration_similarity(rrule1, rrule2):
    """Return the duration similarity bewteen the two rrules

    The schedule similarity is defined as the jaccard distance of the
    day set of each rrule_struct.

    The similarity is expressed as a float between 0 and 1, 1 being
    total similarity.

    """
    def discretise_day_interval(rrule):
        """Discretise the day interval of rrule_struct by 1 day slots
        """
        out = []
        discrete_day = rrule.dtstart
        if not rrule.until:
            return [rrule.dtstart]
        while discrete_day <= rrule.until:
            out.append(discrete_day)
            discrete_day += timedelta(days=1)
        return out
    day_set1 = set(discretise_day_interval(rrule1))
    day_set2 = set(discretise_day_interval(rrule2))
    return jaccard_distance(day_set1, day_set2)


def rrule_similarity(rrule_struct1, rrule_struct2):
    """Compute the similarity score bewteen the two argument rrule_struct

    The similarity score is expressed as a float between 0 and 1, 1 being
    total similarity, and is calculated as the average of the jaccard
    similarity coefficient of the following attributes:
     * weekday
     * schedule
     * duration (in days)

    """
    rrule1 = rrulestr(rrule_struct1['rrule'])
    rrule2 = rrulestr(rrule_struct2['rrule'])
    wk_sim = weekday_similarity(rrule1, rrule2)
    sc_sim = schedule_similarity(rrule_struct1, rrule_struct2)
    du_sim = duration_similarity(rrule1, rrule2)
    return sum((wk_sim, sc_sim, du_sim)) / 3


def timepoint_similarity(rrule_struct1, rrule_struct2):
    """Compute the similarity score bewteen the two argument rrule_struct

    The similarity score is expressed as a float between 0 and 1, 1 being
    total similarity, and is calculated as the average of the jaccard
    similarity coefficient of the following attributes:
     * schedule
     * duration (in days)

    """
    rrule1 = rrulestr(rrule_struct1['rrule'])
    rrule2 = rrulestr(rrule_struct2['rrule'])
    sc_sim = schedule_similarity(rrule_struct1, rrule_struct2)
    du_sim = duration_similarity(rrule1, rrule2)
    return sum((sc_sim, du_sim)) / 2


def similarity(rrule_struct1, rrule_struct2):
    if ('BYDAY' in rrule_struct1['rrule']
        and 'BYDAY' in rrule_struct2['rrule']):
        return rrule_similarity(rrule_struct1, rrule_struct2)
    elif ('BYDAY' not in rrule_struct1['rrule']
        and 'BYDAY' not in rrule_struct2):
        return timepoint_similarity(rrule_struct1, rrule_struct2)
    else:
        raise ValueError('RRule structures not comparable.'
            'One is a recurrence, the other is simple timepoints.')