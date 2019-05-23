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


def split_short_continuous_schedules(schedules, count_threshold=2):
    """
    """
    drrs = [DurationRRule(schedule) for schedule in schedules]
    idxs_to_remove = set()
    new_drrs = []

    for idx, drr in enumerate(drrs):
        if drr.is_continuous:
            nb_of_days = (drr.end_datetime.date() - drr.start_datetime.date()).days
            if nb_of_days < count_threshold:
                idxs_to_remove.add(idx)
                for i in range(nb_of_days + 1):
                    new_single = DurationRRule(drr.duration_rrule.copy())
                    new_single.set_startdate(drr.rrule._dtstart + timedelta(days=i))
                    new_single.add_count()
                    new_single.remove_interval_ind()
                    new_single.set_enddate(None)
                    new_drrs.append(new_single)

    drrs = [drr for i, drr in enumerate(drrs) if i not in idxs_to_remove]
    output = [drr.duration_rrule for drr in drrs]
    output.extend(drr.duration_rrule for drr in new_drrs)

    return output
