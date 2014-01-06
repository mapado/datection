# -*- coding: utf-8 -*-

import re

from .regex import TIMEPOINT_REGEX
from .normalize import timepoint_factory
from .context import probe


def parse(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If ``valid=True``, only valid Timepoints will be returned.
    Else, invalid Timepoints can also be returned.

    """
    out = []
    if isinstance(text, unicode):
        text = text.encode('utf-8')

    # if not event simple date markers could be found, stop here
    contexts = probe(text, lang)
    if not contexts:
        return []

    timepoint_families = [
        det for det in TIMEPOINT_REGEX[lang].keys()
        if not det.startswith('_')
    ]

    for context in contexts:
        matches = []
        for family in timepoint_families:
            for detector in TIMEPOINT_REGEX[lang][family]:
                matches.extend(
                    [(m, family) for m in re.finditer(detector, context)])

        matches = _remove_subsets(matches)  # rm overlapping matches
        for match, family in matches:
            try:
                timepoint = timepoint_factory(
                    family, match.groupdict(),
                    text=match.group(0), lang=lang)
            except NotImplementedError:
                pass
            else:
                out.append(timepoint)

    out = list(set(out))  # remove any redundancy (by security)
    if valid:  # only return valid Timepoints
        return [match for match in out if match.valid]
    return out


def _remove_subsets(matches):
    """ Remove items contained which span is contained into others'.

    Each item is a Timepoint subclass (Time, DateTime, etc).
    All items which start/end span is contained into other item
    spans will be removed from the output list.

    The span is removed from each returned item, and the output list
    is sorted by the start position of each item span.

    Example: the second and third matches are subsets of the first one.
    Input: [
    (match1, set(5, ..., 15), 'datetime'),
    (match2, set(5, ..., 10), 'date')
    (match3, set(11, ..., 15), 'time')
    (match4, set(0, ... 3), 'time')
    ]
    Output: [(match4, 'time'), (match1, 'datetime')]

    """
    out = matches[:]  # shallow copy
    for t1, family1 in matches:
        for t2, family2 in matches:
            if t1 != t2:  # avoid self comparison
                s1, s2 = set(range(*t1.span())), set(range(*t2.span()))
                if s1.intersection(s2):
                    # if A ⊃ B or A = B: remove B
                    if s1.issuperset(s2) or s1 == s2:
                        if (t2, family2) in out:
                            out.remove((t2, family2))
                    # if A ⊂ B: remove A
                    elif s1.issubset(s2):
                        if (t1, family1) in out:
                            out.remove((t1, family1))
    # sort list by match position
    out = sorted(out, key=lambda item: item[0].span()[0])
    return out
