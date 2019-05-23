# -*- coding: utf-8 -*-
from __future__ import division
from past.utils import old_div


def add_count_estimation(drr):
    """
    Adds a date count estimation to the DurationRRule
    """
    cnt = 0
    if drr.single_date:
        cnt = 1
    elif drr.is_continuous:
        delta = drr.end_datetime - drr.start_datetime
        cnt = delta.days
    elif drr.is_recurring:
        delta = drr.end_datetime - drr.start_datetime
        nb_weekdays = len(drr.rrule._byweekday)
        cnt = nb_weekdays * ((old_div(delta.days, 7)) + 1)

    drr.duration_rrule['estimated_count'] = cnt
