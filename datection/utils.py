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
