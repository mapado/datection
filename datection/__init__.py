# -*- coding: utf8 -*-

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

__version__= '0.1'

import re

from datection.regex import TIMEPOINT_REGEX
from datection.normalizer import timepoint_factory


def parse(text, lang, valid=False):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If ``valid=True``, only valid Timepoints will be returned.
    Else, invalid Timepoints can also be returned.

    """
    out = []
    detectors = [
        det for det in TIMEPOINT_REGEX[lang].keys()
        if not det.startswith('_')
    ]
    for detector in detectors:
        for match in re.finditer(TIMEPOINT_REGEX[lang][detector], text):
            out.append(
                timepoint_factory(
                    detector,
                    match.groupdict(),
                    text=match.group(0),
                    span=match.span(),
                    lang=lang)
                )
    out = remove_subsets(out)  # remove overlapping matches from results
    if valid:  # only return valid Timepoints
        return [match for match in out if match.valid]
    return out


def parse_to_json(text, lang, valid=False **kwargs):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of json serialized, non overlapping normalized timepoints
    expressions.

    All kwargs will be passed to ``to_json`` method of each Timepoint.

    """
    return [timepoint.to_json(**kwargs) for timepoint in parse(text, lang, valid)]


def parse_to_dict(text, lang):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of non overlapping normalized timepoints
    expressions.

    """
    return [timepoint.to_dict() for timepoint in parse(text, lang, valid)]


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
