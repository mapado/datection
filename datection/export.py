# -*- coding: utf-8 -*-

"""Datection exporters to database compliant formats."""

from builtins import next
from datetime import datetime
from datetime import timedelta
from datection.timepoint import DAY_START, DAY_END
from datection.parse import parse
from datection.models import DurationRRule
from datection.coherency import RRuleCoherencyFilter
from datection.pack import RrulePacker
from datection.timezone import local_time_to_utc_no_timezone
from datection.timezone import now_local_time_no_timezone
from datection.timezone import is_valid_timezone


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
    possible exclusion rrules

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
    [{'duration': 600,
      'rrule': ('DTSTART:20150405\nRRULE:FREQ=DAILY;BYHOUR=22;BYMINUTE=0;'
                'INTERVAL=1;UNTIL=20150406T235959'),
      'span': (0, 38)}]

    >>> export(u"tous les lundis à 8h", "fr")
    [{'duration': 0,
      'rrule': ('DTSTART:\nRRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;'
                'BYMINUTE=0'),
      'span': (0, 21)}]

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

    packed = RrulePacker(drrs).pack_rrules()
    seen = sorted(packed, key=lambda drr: drr.start_datetime)

    if not kwargs.get('keep_every_pattern', False):
        seen = seen[:10]

    out = [drr.duration_rrule for drr in seen]
    return out


def to_db(text, lang, valid=True, only_future=True, **kwargs):
    return export(text, lang, valid=True, only_future=True, **kwargs)


def schedule_to_discretised_days(schedule, forced_lower_bound=None,
            forced_upper_bound=None):
    """Export the schedule to a list of datetime (one datetime for .
    each day)
    """
    discretised_days = set()
    for drr in schedule:
        drr = DurationRRule(dict(drr), forced_lower_bound = forced_lower_bound,
            forced_upper_bound = forced_upper_bound)
        for dt in drr:
            discretised_days.add(dt)
    return sorted(discretised_days)


def schedule_first_date(schedule, timezone_name=""):
    """ Export the first date of a duration rrule list
    """
    curmin = None
    if schedule:
        for drr in schedule:
            drr = DurationRRule(dict(drr))
            sdt = drr.start_datetime
            if not curmin or curmin > sdt:
                curmin = sdt

    if curmin is not None and is_valid_timezone(timezone_name):
        curmin = local_time_to_utc_no_timezone(curmin, timezone_name)

    return curmin


def schedule_last_date(schedule, timezone_name=""):
    """ Export the last date of a duration rrule list
    """
    curmax = None
    if schedule:
        for drr in schedule:
            drr = DurationRRule(dict(drr))
            edt = drr.end_datetime
            if drr.duration_rrule['duration'] == 0 and edt.time() == DAY_START:
                edt = datetime.combine(edt.date(), DAY_END)
            if not curmax or curmax < edt:
                curmax = edt

    if curmax is not None and is_valid_timezone(timezone_name):
        curmax = local_time_to_utc_no_timezone(curmax, timezone_name)

    return curmax


def schedule_next_date(schedule, timezone_name=""):
    """ Export the next date of a duration rrule list
    """
    curnext = None
    if schedule:

        nowdate = datetime.utcnow()
        if is_valid_timezone(timezone_name):
            nowdate = now_local_time_no_timezone(timezone_name)

        for drr in schedule:
            drr = DurationRRule(dict(drr), forced_lower_bound=nowdate)
            try:
                ndt = next(drr.__iter__())
            except StopIteration:
                ndt = None
            if ndt and (not curnext or curnext > ndt) and ndt > nowdate:
                curnext = ndt

    if curnext is not None and is_valid_timezone(timezone_name):
        curnext = local_time_to_utc_no_timezone(curnext, timezone_name)

    return curnext


def split_past_and_future(schedule, keep_all_day=False, reference_date=None):
    """
    Splits the given schedule into past and future ones.
    """
    past_schedule, future_schedule = [], []

    threshold_date = reference_date
    if threshold_date is None:
        threshold_date = datetime.utcnow()

    if not isinstance(threshold_date, datetime):
        threshold_date = datetime.combine(threshold_date, DAY_START)

    if keep_all_day:
        threshold_date = datetime.combine(threshold_date.date(), DAY_START)

    for drr_string in schedule:
        drr = DurationRRule(drr_string)
        end_datetime = drr.end_datetime
        if end_datetime < threshold_date:
            past_schedule.append(drr_string)
        else:
            future_schedule.append(drr_string)

    return past_schedule, future_schedule


def terminate_infinite_schedule(schedule, new_end=datetime.utcnow()):
    """
    Sets the new end date to recurring schedule without end.
    """
    schedule_has_changed = False

    for idx, drr_string in enumerate(schedule):
        drr = DurationRRule(drr_string)
        if drr.is_recurring and not drr.has_end:
            drr.add_enddate(new_end.date())
            schedule[idx] = drr.duration_rrule
            schedule_has_changed = True

    return schedule_has_changed, schedule


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
            if dt.isoweekday() == 7:
                out.add("%s-%s_sunday_full" % (isocal[0], isocal[1]))

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
