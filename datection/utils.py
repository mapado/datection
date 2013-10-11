""" Some utility functions """

import re

from dateutil.rrule import rrulestr
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


class DurationRRule(object):

    """Wrapper around a rrule + duration object"""

    def __init__(self, duration_rrule):
        self.duration_rrule = duration_rrule

    @lazy_property
    def rrule(self):
        return rrulestr(self.duration_rrule['rrule'])

    @property
    def duration(self):
        return int(self.duration_rrule['duration'])

    @property
    def is_recurring(self):
        if not 'BYDAY' in self.duration_rrule['rrule']:
            return False
        if len(self.rrule.byweekday) == 7 and not self.is_all_year_recurrence:
            # if a rrule says "every day from DT_START to DT_END", it is
            # similar to "from DT_START to DT_END", hence it is not a
            # recurrence!
            return False
        return True

    @property
    def is_all_year_recurrence(self):
        if not 'BYDAY' in self.duration_rrule['rrule']:
            return False
        return self.rrule.dtstart + timedelta(days=365) == self.rrule.until


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
