# -*- coding: utf-8 -*-

"""
Module regrouping common functions for combining rrules
"""
from builtins import next
from builtins import range
from datetime import timedelta


def have_same_days(wrec1, wrec2):
    """
    Checks if the two weekly recurrences have the same
    days of week
    """
    days1 = set(wrec1.weekday_indexes)
    days2 = set(wrec2.weekday_indexes)
    return (days1 == days2)


def get_first_of_weekly(wrec):
    """
    Returns the first occurence of the weekly rrule
    """
    return next(d.date() for d in wrec if d.weekday() in wrec.weekday_indexes)


def real_last_date(drr):
    """ Returns the first day of the DurationRRule """
    if drr.is_recurring:
        return get_last_of_weekly(drr)
    else:
        return drr.end_datetime.date()


def real_first_date(drr):
    """ Returns the last day of the DurationRRule """
    if drr.is_recurring:
        return get_first_of_weekly(drr)
    else:
        return drr.start_datetime.date()


def get_last_of_weekly(wrec):
    """
    Returns the last occurence of the weekly rrule
    """
    end_day = wrec.end_datetime.date()
    for i in range(7):
        tmp_date = end_day - timedelta(days=i)
        if tmp_date.weekday() in wrec.weekday_indexes:
            return tmp_date
    return end_day


def are_overlapping(cont1, cont2):
    """
    Checks if the two continuous rrules are overlapping
    """
    if cont1.unlimited and cont2.unlimited:
        return True

    if cont1.unlimited:
        return (cont1.start_datetime <= cont2.end_datetime)

    if cont2.unlimited:
        return (cont2.start_datetime <= cont1.end_datetime)

    if cont1.end_datetime <= cont2.end_datetime:
        return (cont1.end_datetime >= cont2.start_datetime)

    if cont2.end_datetime <= cont1.end_datetime:
        return (cont2.end_datetime >= cont1.start_datetime)

    return False


def have_same_timings(drr1, drr2, light_match=False):
    """
    Checks if the given drrs have the same timing and duration
    """
    if light_match and not drr1.has_timings:
        return True

    return (
        drr1.duration == drr2.duration and
        drr1.rrule._byhour == drr2.rrule._byhour and
        drr1.rrule._byminute == drr2.rrule._byminute
    )


def has_date_inbetween(drr1, drr2):
    """
    Checks if drr1 starts between the beginning and the end
    of drr2.
    """
    return (
        drr1.start_datetime >= drr2.start_datetime and
        (drr2.unlimited or drr1.end_datetime <= drr2.end_datetime)
    )


def has_weekday_included(single, weekly):
    """
    Checks if the single date is a day of the week
    contained in the weekly recurrence.
    """
    sing_day = single.start_datetime.weekday()
    weekly_days = weekly.weekday_indexes
    if weekly_days:
        return (sing_day in weekly_days)
    return False


def are_wrecs_overlapping(wrec1, wrec2):
    """ Checks if two weekly recurrences are overlapping """
    wrec1_days = set(wrec1.weekday_indexes)
    wrec2_days = set(wrec2.weekday_indexes)
    if len(wrec1_days.intersection(wrec2_days)) == 0:
        return False

    if wrec1.unlimited and wrec2.unlimited:
        return True

    if wrec1.unlimited:
        return (get_first_of_weekly(wrec1) <= get_last_of_weekly(wrec2))

    if wrec2.unlimited:
        return (get_first_of_weekly(wrec2) <= get_last_of_weekly(wrec1))

    if get_last_of_weekly(wrec1) <= get_last_of_weekly(wrec2):
        return (get_last_of_weekly(wrec1) >= get_first_of_weekly(wrec2))

    if get_last_of_weekly(wrec2) <= get_last_of_weekly(wrec1):
        return (get_last_of_weekly(wrec1) >= get_first_of_weekly(wrec2))

    return False


def are_cont_and_wrec_overlapping(cont, wrec):
    """
    Checks if a continuous rrule and a weekly recurrence are overlapping
    """
    return (
        have_same_timings(cont, wrec) and
        are_overlapping(cont, wrec)
    )


def is_sing_in_wrec(sing, wrec):
    """ Checks if a single date is in a weekly recurrences """
    return (
        have_same_timings(sing, wrec) and
        has_weekday_included(sing, wrec) and
        has_date_inbetween(sing, wrec)
    )


def is_wrec_inside_cont(wrec, cont):
    """
    Checks if a weekly recurrence is inside a continuous rrule.
    """
    return (
        have_same_timings(wrec, cont) and
        has_date_inbetween(wrec, cont)
    )


def are_conts_overlapping(cont1, cont2):
    """ Checks if two continuous rrules are overlapping """
    return (
        have_same_timings(cont1, cont2) and
        are_overlapping(cont1, cont2)
    )


def is_cont_inside_cont(cont1, cont2):
    """
    Checks if a continuous rrule is included in another continuous rrule
    """
    return (
        have_same_timings(cont1, cont2) and
        has_date_inbetween(cont1, cont2)
    )


def is_sing_in_cont(sing, cont):
    """ Checks if a single date is in a continuous rrule """
    return (
        has_date_inbetween(sing, cont) and
        have_same_timings(sing, cont)
    )


def is_same_sing(sing1, sing2):
    """ Checks if two single dates are equals """
    return (
        have_same_timings(sing1, sing2) and
        sing1.start_datetime == sing2.start_datetime
    )
