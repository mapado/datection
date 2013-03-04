# -*- coding: utf-8 -*-

"""
Datection provides you with a parser that can extract and normalize
date/time related expressions.

For example, the french expression "le lundi 15 mars, de 15h30 à 16h"
will be normalized into the following JSON structure:

{
    'date':
    {
        'day': 15,
        'month': 3,
        'year': None
    },
    'time':
    {
        'end_time':
        {
            'hour': 16,
            'minute': 0
        },
        'start_time':
        {
            'hour': 15,
            'minute': 30
        }
    }
}

No external dependencies are needed.
"""

__version__ = '0.1'

import re
import signal

from datection.regex import TIMEPOINT_REGEX
from datection.normalizer import timepoint_factory


class Timeout(Exception):
    pass


def signal_handler(signum, frame):
    raise Timeout('Function timed out.')

signal.signal(signal.SIGALRM, signal_handler)


def parse(text, lang, valid=False):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If ``valid=True``, only valid Timepoints will be returned.
    Else, invalid Timepoints can also be returned.

    """
    out = []
    if isinstance(text, unicode):
        text = text.encode('utf-8')

    timepoint_families = [
        det for det in TIMEPOINT_REGEX[lang].keys()
        if not det.startswith('_')
    ]
    for family in timepoint_families:
        for detector in TIMEPOINT_REGEX[lang][family]:
            for match in re.finditer(detector, text):
                signal.alarm(1)  # limit execution time to 1s
                try:
                    out.append(
                        timepoint_factory(
                            family,
                            match.groupdict(),
                            text=match.group(0),
                            span=match.span(),
                            lang=lang)
                        )
                except NotImplementedError:
                    pass
                except AttributeError:
                    # exception often raised when a false detection occurs
                    pass
                except Timeout:
                    raise Timeout
    signal.alarm(0)  # remove all execution time limit
    out = remove_subsets(out)  # remove overlapping matches from results
    if valid:  # only return valid Timepoints
        return [match for match in out if match.valid]
    return out


def parse_to_serialized(text, lang, valid=False):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of serialized, non overlapping normalized timepoints
    expressions.

    """
    return [timepoint.serialize() for timepoint in parse(text, lang, valid)]


def parse_to_dict(text, lang, valid=False):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of non overlapping normalized timepoints
    expressions.

    """
    return [timepoint.to_dict() for timepoint in parse(text, lang, valid)]

def parse_to_sql(text, lang):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of datetime tuples ([start_datetime, end_datetime]) for sql insertion
    """

    out = [timepoint.to_sql() for timepoint in parse(text, lang, True)
                if timepoint.valid]
    return [item for item in out if item]


def remove_subsets(timepoints):
        """ Remove items contained which span is contained into others'.

        Each item is a Timepoint subclass (Time, DateTime, etc).
        All items which start/end span is contained into other item
        spans will be removed from the output list.

        The span is removed from each returned item, and the output list is sorted
        by the start position of each item span.

        Example: the second and third matches are subsets of the first one.
        Input: [
            (match1, set(5, ..., 15), 'datetime'),
            (match2, set(5, ..., 10), 'date')
            (match3, set(11, ..., 15), 'time')
            (match4, set(0, ... 3), 'time')
            ]
        Output: [(match4, 'time'), (match1, 'datetime')]

        """
        out = timepoints[:]  # shallow copy
        for t1 in timepoints:
            for t2 in timepoints:
                if t1 != t2:  # avoid self comparison
                    s1, s2 = set(range(*t1.span)), set(range(*t2.span))
                    if s1.intersection(s2):
                        # if A ⊃ B or A = B: remove B
                        if s1.issuperset(s2) or s1 == s2:
                            if t2 in out:
                                out.remove(t2)
                        # if A ⊂ B: remove A
                        elif s1.issubset(s2):
                            if t1 in out:
                                out.remove(t1)
        out = sorted(out, key=lambda item: item.span[0])  # sort list by match position
        return out
