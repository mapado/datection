""" Some utility functions """

import re
import datection
import itertools as it

from datetime import datetime
from datetime import date
from datetime import timedelta


def lazy_property(f):
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


def makerrulestr(start, end=None, freq='DAILY', rule=None, **kwargs):
    """ Returns an RFC standard rrule string

    If the 'rule' argument is None, all the keyword args will
    be used to construct the rule. Else, the rrule RFC representation
    will be inserted.

    """
    # use dates as start/until points
    dtstart = "DTSTART:%s\n" % isoformat_concat(start)
    if end:
        until = "UNTIL=%s" % isoformat_concat(end)
    else:
        until = ''
    if rule:
        rulestr = "RRULE:" + str(rule) + ";"
        rulestr = rulestr.replace('BYWEEKDAY', 'BYDAY')
    else:
        rulestr = "RRULE:FREQ=%s;" % (freq)
        for arg, val in kwargs.items():
            rulestr += arg.upper() + '=' + str(val) + ';'
    result = '{start}{rule}{end}'.format(
        start=dtstart, rule=rulestr, end=until)
    return result.rstrip(';')


WEEKDAY_IDX = {
    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
}


def _sort_facebook_hours(fb_hours):
    """Sort the items of a facebook hours dict

    The items will be sorted first using the weekdays, then using the
    window number, and finally using the open/close suffix.

    Example:
    >>>fb_hours = {
        "mon_2_open", "14:00",
        "mon_2_close", "18:00",
        "mon_1_open", "10:00",
        "mon_1_close", "12:00",
        "wed_1_open", "10:00",
        "wed_1_close", "18:00",
        "thu_1_open", "10:00",
        "thu_1_close", "18:00",
        "fri_1_open", "10:30",
        "fri_1_close", "18:00",
        "sat_1_open", "10:00",
        "sat_1_close", "18:00",
        "sun_1_open", "10:00",
        "sun_1_close", "18:00"
    }
    >>>_sort_facebook_hours(fb_hours)
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
    def fb_hour_index(fb_hour_key):
        wk_idx = WEEKDAY_IDX[fb_hour_key[:3]]
        window_nb = fb_hour_key[4]
        _open = 0 if fb_hour_key[6:] == 'open' else 1
        idx = '%d%s%d' % (wk_idx, window_nb, _open)
        return idx

    return sorted(fb_hours.items(), key=lambda x: fb_hour_index(x[0]))


def normalize_fb_hours(fb_hours):
    """Convert a Facebook opening hours dict to a recurrent schedule."""

    def chunks(l, n):
        for i in xrange(0, len(l), n):
            yield l[i:i + n]

    # sort the dict items by the order of the weekdays
    fb_hours = _sort_facebook_hours(fb_hours)
    # iterate over each weekday, and create the associated recurrent schedule
    schedules = []
    for weekday, group in it.groupby(fb_hours, key=lambda k: k[0][:3]):
        for opening, closing in chunks(list(group), 2):
            wk_idx = WEEKDAY_IDX[weekday]

            # parse the time strings and convert them to datetime.time objects
            opening_time = datetime.strptime(opening[1], "%H:%M").time()
            closing_time = datetime.strptime(closing[1], "%H:%M").time()

            # set the start/end datetimes of the recurrence
            start = datetime.combine(date.today(), opening_time)
            end = datetime.combine(date.today() + timedelta(days=365),
                                   closing_time)

            # create the WeekdayRecurrence object associated with the
            # opening time
            reccurence = datection.normalize.WeekdayRecurrence(
                weekdays=(wk_idx, ), start=start, end=end)
            schedules.append(reccurence.to_db())
    return schedules
