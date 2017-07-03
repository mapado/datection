# -*- coding: utf-8 -*-
from datection.models import DurationRRule
from copy import deepcopy
from datetime import timedelta


def split_schedules(schedules, split_date):
    """
    Splits the given schedules into two lists:
        - past schedules
        - future schedules
    Schedules containing the split date are split.
    """
    drrs = [DurationRRule(schedule) for schedule in schedules]

    past_schedules, future_schedules = [], []

    for drr in drrs:
        if drr.end_datetime.date() < split_date:
            past_schedules.append(drr.duration_rrule)
        elif drr.start_datetime.date() >= split_date:
            future_schedules.append(drr.duration_rrule)
        else:
            # split DurationRRule in two
            copy_future = deepcopy(drr)
            copy_future.set_startdate(split_date)
            future_schedules.append(copy_future.duration_rrule)

            drr.set_enddate(split_date - timedelta(days=1))
            past_schedules.append(drr.duration_rrule)

    return past_schedules, future_schedules
