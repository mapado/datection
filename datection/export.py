# -*- coding: utf-8 -*-

"""
Datection exporters to python and database compliant formats.
"""

from datection.parse import parse


def to_db(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of dicts, each containing a recurrence rule
    describing the extracted time reference, and a duration,
    linking each start date/time to an end date/time

    """
    out = [
        timepoint.to_db() for timepoint in parse(text, lang, valid)
    ]
    return [item for item in out if item]


def to_mongo(text, lang, valid=True):
    """ Obsolete function, kept for backwards compatibility reasons

    Now, it's just a proxy to the to_db function
    """
    return to_db(text, lang, valid)


def to_python(text, lang, valid=True):
    """ Perform a timepoint detection on text, and normalize each result to
        python standard objects.

    Return a list of standard datetime python objects
    """
    out = [
        timepoint.to_python() for timepoint in parse(text, lang, valid)
    ]
    return [item for item in out if item]
