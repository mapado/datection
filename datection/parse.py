# -*- coding: utf-8 -*-

import re

from datection.regex import TIMEPOINT_REGEX
from datection.normalize import timepoint_factory
from datection.context import probe


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

    timepoint_families = (det for det in TIMEPOINT_REGEX[lang].keys()
                          if not det.startswith('_'))

    for context in contexts:
        matches = []
        for family in timepoint_families:
            for detector in TIMEPOINT_REGEX[lang][family]:
                matches.extend(
                    [(m, family) for m in re.finditer(detector, str(context))])

        matches = _remove_subsets(matches)  # rm overlapping matches
        for match, family in matches:
            try:
                timepoint = timepoint_factory(
                    detector=family, data=match.groupdict(),
                    lang=lang, span=context.position_in_text(match.span()))
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
    for tpt1, family1 in matches:
        for tpt2, family2 in matches:
            if tpt1 != tpt2:  # avoid self comparison
                span1, span2 = (
                    set(range(*tpt1.span())), set(range(*tpt2.span())))
                if span1.intersection(span2):
                    # if A ⊃ B or A = B: remove B
                    if span1.issuperset(span2) or span1 == span2:
                        if (tpt2, family2) in out:
                            out.remove((tpt2, family2))
                    # if A ⊂ B: remove A
                    elif span1.issubset(span2):
                        if (tpt1, family1) in out:
                            out.remove((tpt1, family1))
    # sort list by match position
    out = sorted(out, key=lambda item: item[0].span()[0])
    return out
