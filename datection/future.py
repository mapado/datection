# -*- coding: utf-8 -*-

import datetime

from datection.models import DurationRRule


def is_future(schedule, reference=datetime.datetime.now()):
    """Return True if any of the input schedule is future, else False"""
    future = False
    for duration_rrule in schedule:
        drr = DurationRRule(duration_rrule)
        if any([date for date in list(drr.rrule) if date > reference]):
            future = True
            break
    return future
