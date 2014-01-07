# -*- coding: utf-8 -*-

"""
Datection exporters to python and database compliant formats.
"""

from datection.parse import parse
from datection.merge import merge


def to_db(text, lang, valid=True, only_future=True, **kwargs):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of dicts, each containing a recurrence rule
    describing the extracted time reference, and a duration,
    linking each start date/time to an end date/time

    """
    timepoints = parse(text, lang, valid)
    timepoints = merge(timepoints)
    out = []
    # filter out all past timepoints, if only_future == True
    if only_future:
        timepoints = [tp for tp in timepoints if tp.future(**kwargs)]
    for timepoint in timepoints:
        rrules = timepoint.to_db()
        if isinstance(rrules, list):
            out.extend(rrules)
        elif isinstance(rrules, dict):
            out.append(rrules)
    return out


def to_mongo(text, lang, valid=True, only_future=True, **kwargs):
    """ Obsolete function, kept for backwards compatibility reasons

    Now, it's just a proxy to the to_db function
    """
    return to_db(text, lang, valid, only_future, **kwargs)


def to_python(text, lang, valid=True, only_future=True, **kwargs):
    """ Perform a timepoint detection on text, and normalize each result to
        python standard objects.

    Return a list of standard datetime python objects
    """
    timepoints = parse(text, lang, valid)
    if only_future:
        return [timepoint.to_python() for timepoint in timepoints
                if timepoint.future(**kwargs)]
    return [timepoint.to_python() for timepoint in timepoints]
