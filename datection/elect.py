# -*- coding: utf-8 -*-

"""
Election of the best of several schedules.

The common scenario is the merge of several similar documents, with
similar, but not identical schedules. In this case, the best schedule
of all must be picked.

The metric used to elect the best schedule is its precision. The
schedule with rrules generating the less timepoints of all will be
chosen.

"""
from __future__ import division
from past.utils import old_div
from datection.similarity import discretise_schedule


def common_elements(set_list):
    """Return the set of elemets common to all sets."""
    return set(set_list[0]).intersection(*set_list)


def similarity_score(discrete_schedule, common):
    return old_div(len(common), float(len(discrete_schedule)))


def best_schedule(schedules):
    """Return the schedule with the highest similarity with the set
    of datetimes common to all discretised schedules.

    """
    # discretise each schedule into datetimes
    discretised = [discretise_schedule(schedule, grain_level="min", grain_quantity=30)
                   for schedule in schedules]

    # find the datetime subset common to all schedules
    common = common_elements(discretised)
    if not common:
        return None

    # return the schedule with the highest similarity w.r.t. the
    # common datetime subset
    similarity_scores = [similarity_score(discrete, common)
                         for discrete in discretised]
    max_score_idx = similarity_scores.index(max(similarity_scores))
    return schedules[max_score_idx]
