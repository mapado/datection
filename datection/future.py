# -*- coding: utf-8 -*-

import datetime

from dateutil.rrule import *


def is_future(rrules, reference=datetime.datetime.now()):
    """Return True if any of the input schedule is future, else False"""
    future = False
    for rrule_item in rrules:
        if any(
            [date for date in list(rrulestr(rrule_item['rrule']))
                if date > reference]):
            future = True
            break
    return future
