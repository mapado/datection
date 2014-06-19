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


def schedule_to_start_end_list(schedule):
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
    start = datetime.utcnow().replace(hour=0, minute=0, second=0)
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

