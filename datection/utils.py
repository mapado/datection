""" Some utility functions """

import re

from dateutil.rrule import rrulestr
from datetime import timedelta


class DurationRRule(object):

    """Wrapper around a rrule + duration object"""

    def __init__(self, duration_rrule):
        self.duration_rrule = duration_rrule

    @property
    def rrule(self):
        return rrulestr(self.duration_rrule['rrule'])

    @property
    def duration(self):
        return int(self.duration_rrule['duration'])

    @property
    def is_recurring(self):
        return 'BYDAY' in self.duration_rrule['rrule']

    @property
    def is_all_year_recurrence(self):
        if not self.is_recurring:
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
