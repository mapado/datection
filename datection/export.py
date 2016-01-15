# -*- coding: utf-8 -*-

"""Datection exporters to database compliant formats."""

from datetime import datetime
from datetime import timedelta
from datection.parse import parse
from datection.models import DurationRRule
from datection.coherency import RRuleCoherencyFilter


def export(text, lang, valid=True, only_future=False, reference=None, **kwargs):
    """Extract and normalize time-related expressions from the text.

    Grammar specific to the argument language will be used on the
    argument text.

    If valid is True, only valid expression exports will be returned.
    If only_future is True, only expressions related to future datetimes
    will be exported.
    A reference can be passed (as a datetime object) to specify the
    reference extraction date. It can be used to determine the year of
    certain dates, when it is missing.

    Returns a list of dicts, each containing a recurrence rule
    describing the extracted time reference, a duration,
    linking each start date/time to an end date/time, a character span,
    possible exclusion rrules, a boolean "continuous" flag indicating the
    that the time interval is continuous, and not repeated for each date,
    and finally, and 'unlimited' boolean flag, indicating that the dates
    occur each year.

    >>> export(u"Le 4 mars 2015 à 18h30", "fr")
    [{'duration': 0,
      'rrule': ('DTSTART:20150304\nRRULE:FREQ=DAILY;COUNT=1;'
        'BYMINUTE=30;BYHOUR=18'),
      'span': (0, 23)}]

    >>> export(u"Du 5 au 29 mars 2015, sauf le lundi", "fr")
    [{'duration': 1439,
      'excluded': [
        ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYDAY=MO;BYHOUR=0;'
            'BYMINUTE=0;UNTIL=20150329T000000')
        ],
      'rrule': ('DTSTART:20150305\nRRULE:FREQ=DAILY;BYHOUR=0;'
        'BYMINUTE=0;INTERVAL=1;UNTIL=20150329'),
      'span': (0, 36)}]

    >>> export(u"Le 4 mars à 18h30", "fr", reference=datetime(2015, 1, 1))
    [{'duration': 0,
      'rrule': ('DTSTART:20150304\nRRULE:FREQ=DAILY;COUNT=1;'
        'BYMINUTE=30;BYHOUR=18'),
      'span': (0, 18)}]

    >>> export(u"Le 4 mars 1990 à 18h30", "fr")
    []

    >>> export(u"Le 4 mars 1990 à 18h30", "fr", only_future=False)
    [{'duration': 0,
      'rrule': ('DTSTART:19900304\nRRULE:FREQ=DAILY;COUNT=1;'
        'BYMINUTE=30;BYHOUR=18'),
      'span': (0, 18)}]

    >>> export(u"Du 5 avril à 22h au 6 avril 2015 à 8h", "fr")
    [{'continuous': True,
      'duration': 600,
      'rrule': ('DTSTART:20150405\nRRULE:FREQ=DAILY;BYHOUR=22;BYMINUTE=0;'
                'INTERVAL=1;UNTIL=20150406T235959'),
      'span': (0, 38)}]

    >>> export(u"tous les lundis à 8h", "fr")
    [{'duration': 0,
      'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;'
                'BYMINUTE=0'),
      'span': (0, 21),
      'unlimited': True}]

    """
    exports = []
    timepoints = parse(text, lang, reference=reference, valid=valid)

    # filter out all past timepoints, if only_future == True
    if only_future:
        timepoints = [tp for tp in timepoints if tp.future(**kwargs)]
    for timepoint in timepoints:
        tp_export = timepoint.export()
        if isinstance(tp_export, list):
            exports.extend(tp_export)
        elif isinstance(tp_export, dict):
            exports.append(tp_export)

    # Deduplicate the output, keeping the order (thus list(set) is not
    # possible)
    drrs, seen = [DurationRRule(export) for export in exports], []

    # Apply rrule coherency heuristics
    drrs = RRuleCoherencyFilter(drrs).apply_coherency_heuristics()

    for drr in drrs:
        if drr not in seen:
            seen.append(drr)

    out = [drr.duration_rrule for drr in seen]
    return out


def to_db(text, lang, valid=True, only_future=True, **kwargs):
    return export(text, lang, valid=True, only_future=True, **kwargs)


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


def schedule_to_discretised_days(schedule, forced_lower_bound=None,
            forced_upper_bound=None):
    """Export the schedule to a list of datetime (one datetime for .
    each day)
    """
    discretised_days = set()
    for drr in schedule:
        drr = DurationRRule(drr, forced_lower_bound = forced_lower_bound,
            forced_upper_bound = forced_upper_bound)
        for dt in drr:
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
            if not curmin or curmin > sdt:
                curmin = sdt

    return curmin


def schedule_last_date(schedule):
    """ Export the last date of a duration rrule list
    """
    curmax = None
    if schedule:
        for drr in schedule:
            drr = DurationRRule(drr)
            edt = drr.end_datetime
            if not curmax or curmax < edt:
                curmax = edt

    return curmax


def schedule_next_date(schedule):
    """ Export the next date of a duration rrule list
    """
    curnext = None
    if schedule:
        nowdate = datetime.now()
        for drr in schedule:
            drr = DurationRRule(drr, forced_lower_bound = nowdate)
            ndt = drr.__iter__().next()
            if (not curnext or curnext > ndt) and ndt > nowdate:
                curnext = ndt

    return curnext

def discretised_days_to_scheduletags(discretised_days):
    """ Convert a list of days to a format suitable for
    Elasticsearch filtering
    """
    out = set()
    for dt in discretised_days:
        # no daytime specific
        out.add(datetime.strftime(dt, "%Y-%m-%d_day_full"))
        out.add(datetime.strftime(dt, "%Y_year_full"))
        if dt.isoweekday() in [6, 7]:
            isocal = datetime.isocalendar(dt)
            out.add("%s-%s_weekend_full" % (isocal[0], isocal[1]))

        # daytime specific
        if dt.hour < 20:
            out.add(datetime.strftime(dt, "%Y-%m-%d_day"))
            out.add(datetime.strftime(dt, "%Y_year_day"))
        elif dt.hour:
            out.add(datetime.strftime(dt, "%Y-%m-%d_night"))
            out.add(datetime.strftime(dt, "%Y_year_night"))

        if dt.isoweekday() in [6, 7]:
            isocal = datetime.isocalendar(dt)
            isoweek = "%s-%s" % (isocal[0], isocal[1])
            if dt.hour < 20:
                out.add("%s_weekend_day" % isoweek)
            elif dt.hour:
                out.add("%s_weekend_night" % isoweek)
    if len(out) == 0:
        out.add("no_schedule")
    return list(out)
