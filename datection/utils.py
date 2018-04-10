# -*- coding: utf-8 -*-

"""Some utility functions"""
from __future__ import division

from future.utils import viewitems

from builtins import str
from past.builtins import basestring
from past.utils import old_div
import re
import datection

from datetime import datetime
from datetime import date
from datetime import time
from dateutil.rrule import weekdays

UNLIMITED_DATE_START        = date(2000, 1, 1)
UNLIMITED_DATE_END          = date(3000, 12, 31)

UNLIMITED_DATETIME_START    = datetime(2000, 1, 1)
UNLIMITED_DATETIME_END      = datetime(3000, 12, 31, 23, 59, 59)

rrule_keywords = ['BYHOUR', 'BYMINUTE', 'BYDAY']
regexp_keywords_equal_null = re.compile('|'.join(['%s=(;|$)' % keyword for keyword in rrule_keywords  ]))

def get_current_date():
    """Return the current date.

    Note: this function is used to enable mocking.

    """
    return date.today()


def cached_property(f):
    """Lazy loading decorator for object properties"""
    attr_name = '_' + f.__name__

    @property
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, f(self))
        return getattr(self, attr_name)
    return wrapper


def isoformat_concat(datetime):
    """ Strip all dots, dashes and ":" from the input datetime isoformat """
    isoformat = datetime.isoformat()
    concat = re.sub(r'[\.:-]', '', isoformat)
    return concat


def is_unlimited_start(start):
    """ Check is "start" match the date 01-01-0001
    """
    # cast to date if datetime
    if type(start) is datetime:
        start = start.date()

    return start == UNLIMITED_DATE_START


def is_unlimited_end(end):
    """ Check is "end" match the date 12-31-9999
    """
    # cast to date if datetime
    if type(end) is datetime:
        end = end.date()

    return end == UNLIMITED_DATE_END


def stringify_rrule(rrule):
    """
    Method to handle the different str() of python-dateutil.rrule
    No implementation of this library is really compliant with RFC 2445
    """
    lines = str(rrule).splitlines(True)
    lines = [line for line in lines if not line.startswith("DTSTART")]
    return "".join(lines)


def cleanup_rrule_string(rrule_str):
    """
    Function to be called before dateutil.rrule.rrulestr for
    compatibility purpose with the non RFC form "DTSTART:\n" 
    """
    rrule_str = rrule_str.replace("DTSTART:\n", "")
    rrule_str = re.sub(regexp_keywords_equal_null, '', rrule_str).strip(';')
    return rrule_str


def makerrulestr(start, end=None, freq='DAILY', rule=None, **kwargs):
    """ Returns an RFC standard RRULE string

    If the 'rule' argument is None, all the keyword args will
    be used to construct the rule. Else, the rrule RFC representation
    will be inserted.

    """
    # set a DTSTART if start date is empty or equal 01-01-0001
    dtstart = ''
    if not is_unlimited_start(start):
        dtstart = isoformat_concat(start)
        dtstart = "DTSTART:%s\n" % dtstart

    # same behaviour for the end date
    until = ''
    if end and not is_unlimited_end(end):
        until = "UNTIL=%s" % isoformat_concat(end)

    if rule:
        rulestr = stringify_rrule(rule) + ";"
        rulestr = rulestr.replace('BYWEEKDAY', 'BYDAY')
    else:
        rulestr = "RRULE:FREQ=%s;" % (freq)
        for arg, val in sorted(kwargs.items()):
            rulestr += arg.upper() + '=' + str(val) + ';'

    if until and (rulestr.find('UNTIL') != -1):
        until = ''

    result = '{start}{rule}{end}'.format(
        start=dtstart, rule=rulestr, end=until)
    return result.rstrip(';')


def duration(start, end):
    """Return the difference, in minutes, bewteen end and start"""
    if end is None:
        return 0

    # convert datection.normalize.Time into datetime.time variables
    if (isinstance(start, datection.timepoint.Time)
       and isinstance(end, datection.timepoint.Time)):
        start = start.to_python()
        end = end.to_python()

    # return the difference bewteen the end datetime and start datetime
    if isinstance(start, datetime) and isinstance(end, datetime):
        return int(old_div((end - start).total_seconds(), 60))

    # return the difference bewteen the two times
    if (isinstance(start, time) and isinstance(end, time)):
        today = date.today()
        start_dt = datetime.combine(today, start)
        end_dt = datetime.combine(today, end)
        return old_div((end_dt - start_dt).seconds, 60)


def normalize_2digit_year(year):
    """ Normalize a 2 digit year into a 4 digit one

    Example: xx/xx/12 --> xx/xx/2012

    WARNING: if a past date is written in this format (ex: 01/06/78)
    it is impossible to know if it references the year 1978 or 2078.
    If the 2-digit date is less than 15 years in the future,
    we consider that it takes place in our century, otherwise,
    it is considered as a past date

    """
    current_year = date.today().year
    century = int(str(current_year)[:2])

    # handle special case where the 2 digit year started with a 0
    # int("07") = 7
    if len(str(year)) == 1:
        year = '0' + str(year)
    else:
        year = str(year)
    if int(str(century) + year) - current_year < 15:
        # if year is less than 15 years in the future, it is considered
        # a future date
        return int(str(century) + year)
    else:
        # else, it is treated as a past date
        return int(str(century - 1) + year)


def digit_to_int(kwargs):
    """Convert all digit values to integer and return the kwargs dict"""
    for k, v in kwargs.items():
        if v and isinstance(v, basestring):
            if v.isdigit():
                kwargs[k] = int(v)
    return kwargs

WEEKDAY_IDX = {
    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
}


def sort_facebook_hours(fb_hours):
    """Sort the items of a facebook hours dict

    The items will be sorted first using the weekdays, then using the
    window number, and finally using the open/close suffix.

    Example:
    >>>fb_hours = {
        "mon_2_open": "14:00",
        "mon_2_close": "18:00",
        "mon_1_open": "10:00",
        "mon_1_close": "12:00",
        "wed_1_open": "10:00",
        "wed_1_close": "18:00",
        "thu_1_open:": "10:00",
        "thu_1_close": "18:00",
        "fri_1_open": "10:30",
        "fri_1_close": "18:00",
        "sat_1_open": "10:00",
        "sat_1_close": "18:00",
        "sun_1_open": "10:00",
        "sun_1_close": "18:00"
    }
    >>>sort_facebook_hours(fb_hours)
    [
        ("mon_1_open", "10:00"), ("mon_1_close", "12:00"),
        ("mon_2_open", "14:00"), ("mon_2_close", "18:00"),
        ("wed_1_open", "10:00"), ("wed_1_close", "18:00"),
        ("thu_1_open", "10:00"), ("thu_1_close", "18:00"),
        ("fri_1_open", "10:30"), ("fri_1_close", "18:00"),
        ("sat_1_open", "10:00"), ("sat_1_close", "18:00"),
        ("sun_1_open", "10:00"), ("sun_1_close", "18:00")
    ]

    """
    def facebook_hour_index(fb_hour_key):
        wk_idx = WEEKDAY_IDX[fb_hour_key[:3]]
        window_nb = fb_hour_key[4]
        _open = 0 if fb_hour_key[6:] == 'open' else 1
        idx = '%d%s%d' % (wk_idx, window_nb, _open)
        return idx

    return sorted(list(fb_hours.items()), key=lambda x: facebook_hour_index(x[0]))


def group_facebook_hours(fb_hours):
    out = []
    previous = []
    for i, fb_hour in enumerate(fb_hours):
        if i == len(fb_hours) - 1:
            previous.append(fb_hour)
            out.append(previous)
        elif fb_hour[0][:5] == fb_hours[i + 1][0][:5]:
            previous.append(fb_hour)
        else:
            previous.append(fb_hour)
            out.append(previous)
            previous = []
    return out


def normalize_fb_hours(fb_hours):
    """Convert a Facebook opening hours dict to a recurrent schedule."""

    def time_from_striptime(data):
        t = datetime.strptime(data, "%H:%M").time()
        return datection.timepoint.Time(t.hour, t.minute)

    # sort the dict items by the order of the weekdays
    fb_hours = sort_facebook_hours(fb_hours)
    fb_hours = group_facebook_hours(fb_hours)
    # iterate over each weekday, and create the associated recurrent schedule
    schedules = []
    for fb_hour_group in fb_hours:
        wk_idx = weekdays[WEEKDAY_IDX[fb_hour_group[0][0][:3]]]
        opening_time = time_from_striptime(fb_hour_group[0][1])
        time_interval = datection.timepoint.TimeInterval(
            opening_time, opening_time)
        if len(fb_hour_group) > 1:
            closing_time = time_from_striptime(fb_hour_group[1][1])
            time_interval = datection.timepoint.TimeInterval(
                opening_time, closing_time)

        reccurence = datection.timepoint.WeeklyRecurrence(
            weekdays=datection.timepoint.Weekdays([wk_idx]),
            date_interval=datection.timepoint.DateInterval.make_undefined(),
            time_interval=time_interval)
        db_format = reccurence.export()
        schedules.append(db_format)
    return schedules
