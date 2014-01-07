""" Some utility functions """

import re
import datection

from datetime import datetime
from datetime import date
from datetime import time


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


def duration(start, end):
    """Return the difference, in minutes, bewteen end and start"""
    if end is None:
        return 0

    # convert datection.normalize.Time into datetime.time variables
    if (isinstance(start, datection.normalize.Time)
       and isinstance(end, datection.normalize.Time)):
        start = start.to_python()
        end = end.to_python()

    # return the difference bewteen the end datetime and start datetime
    if isinstance(start, datetime) and isinstance(end, datetime):
        start_date = start.date()
        end_date = end.date()
        if start_date != end_date:
            delta_days = (end_date - start_date).days
            return delta_days * 24 * 60 + (end - start).seconds / 60
        else:
            return (end - start).seconds / 60

    # return the difference bewteen the two times
    if (isinstance(start, time) and isinstance(end, time)):
        today = date.today()
        start_dt = datetime.combine(today, start)
        end_dt = datetime.combine(today, end)
        return (end_dt - start_dt).seconds / 60


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
    for k, v in kwargs.iteritems():
        if v and isinstance(v, basestring):
            if v.isdigit():
                kwargs[k] = int(v)
    return kwargs
