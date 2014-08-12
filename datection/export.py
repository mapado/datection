# -*- coding: utf-8 -*-

"""
Datection exporters to python and database compliant formats.
"""

from datetime import datetime
from datetime import timedelta
from datection.parse import parse
from datection.models import DurationRRule


def to_db(text, lang, valid=True, only_future=True, **kwargs):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of dicts, each containing a recurrence rule
    describing the extracted time reference, and a duration,
    linking each start date/time to an end date/time

    """
    out = []
    timepoints = parse(text, lang, valid)

    # filter out all past timepoints, if only_future == True
    if only_future:
        timepoints = [tp for tp in timepoints if tp.future(**kwargs)]
    for timepoint in timepoints:
        rrules = timepoint.to_db()
        if isinstance(rrules, list):
            out.extend(rrules)
        elif isinstance(rrules, dict):
            out.append(rrules)
    return out


def to_mongo(text, lang, valid=True, only_future=True, **kwargs):
    """ Obsolete function, kept for backwards compatibility reasons

    Now, it's just a proxy to the to_db function
    """
    return to_db(text, lang, valid, only_future, **kwargs)


def to_python(text, lang, valid=True, only_future=True, **kwargs):
    """ Perform a timepoint detection on text, and normalize each result to
        python standard objects.

    Return a list of standard datetime python objects
    """
    timepoints = parse(text, lang, valid)
    if only_future:
        return [timepoint.to_python() for timepoint in timepoints
                if timepoint.future(**kwargs)]
    return [timepoint.to_python() for timepoint in timepoints]


def export_non_continuous_schedule(schedule, start, end):
    """Export the non continuous schedule to a SQL compliant format.

    Returns a list of start/end datetime, one for each day of the
    schedule, comprised bewteen the start and end argument boundaries.

    """
    out = []
    datetime_list = schedule.rrule.between(start, end, inc=True)
    for start_dt in datetime_list:
        end_dt = start_dt + timedelta(minutes=schedule.duration)
        out.append((start_dt, end_dt))
    return out


def export_continuous_schedule(schedule, start, end):
    """Export the continuous schedule to a SQL compliant format.

    Returns a list of start/end datetime, one for each day of the
    schedule, comprised bewteen the start and end argument boundaries.

    """
    out = []
    datetime_list = schedule.rrule.between(start, end, inc=True)
    for i, dt in enumerate(datetime_list):
        if i == 0:
            start_dt = dt
        else:
            start_dt = dt.replace(hour=0, minute=0, second=0)
        if i != len(datetime_list) - 1:
            end_dt = dt.replace(hour=23, minute=59)
        else:
            end_dt = schedule.end_datetime
        out.append((start_dt, end_dt))
    return out


def schedule_to_start_end_list(schedule, start=None, end=None):
    """Export the schedule to a SQL compliant format.

    Each duration / rrule structure will be converted to a list of
    *future * start / end datetime that will be encapsulated dict.

    Note:
        there is a difference bewteen continuous and non-continuous
    rrules. A non-continuous rrule with a time interval "projects" the
    time interval on each date in its date interval. A continuous rrule
    is only defined by a start datetime and an end datetime. The entire
    in-bewteen interval is thus defined.

    In the case of an infinite interval, returns the dates bewteen the
    day of the function call and one year later.

    If the schedule is past, returns [].

    """
    out = []
    if not start:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    if not end:
        end = (start + timedelta(days=365)).replace(hour=23, minute=59)
    for drr in schedule:
        drr = DurationRRule(drr)
        if drr.is_continuous:
            export = export_continuous_schedule(drr, start, end)
        else:
            export = export_non_continuous_schedule(drr, start, end)
        for start_dt, end_dt in export:
            adt = {
                "start": start_dt,
                "end": end_dt
            }

            out.append(adt)
    return out


def schedule_to_discretised_days(schedule):
    """Export the schedule to a list of datetime (one datetime for .
    each day)
    """
    discretised_days = set()
    for drr in schedule:
        drr = DurationRRule(drr)
        for dt in drr.rrule:
            discretised_days.add(dt)
    return sorted(discretised_days)

def schedule_first_date(schedule):
    """ Export the first date of a duration rrule list
    """
    curmin = None
    if schedule:
        for drr in schedule:
            drr = DurationRRule(drr)
            sdt = drr.start_datetime
            if not(curmin) or curmin > sdt:
                curmin = sdt

    return curmin

def schedule_last_date(schedule):
    """ Export the last date of a duration rrule list
    """
    curmax = None
    if schedule:
        for drr in schedule:
            drr = DurationRRule(drr)
            sdt = drr.end_datetime
            if not(curmax) or curmax < sdt:
                curmax = sdt

    return curmax

def discretised_days_to_scheduletags(discretised_days):
    """ Convert a list of days to a format suitable for
    Elasticsearch filtering
    """
    out = set()
    for dt in discretised_days:
        adt = datetime.strftime(dt, "%Y-%m-%d_fullday")
        out.add(adt)
        if dt.hour < 20:
            adt = datetime.strftime(dt, "%Y-%m-%d_day")
        elif dt.hour:
            adt = datetime.strftime(dt, "%Y-%m-%d_night")
        out.add(adt)
        adt = datetime.strftime(dt, "%Y_fullyear")
        out.add(adt)
        if dt.isoweekday() in [6,7]:
            adt = datetime.strftime(dt, "%Y-%W_fullweekend")
            out.add(adt)
            if dt.hour < 20:
                adt = datetime.strftime(dt, "%Y-%W_weekend_day")
                out.add(adt)
            elif dt.hour:
                adt = datetime.strftime(dt, "%Y-%W_weekend_night")
                out.add(adt)
    if len(out) == 0:
        out.add("no_schedule")
    return list(out)
