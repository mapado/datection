# -*- coding: utf-8 -*-

"""
Datection exporters to JSON and SQL-compliant formats.
"""

from datection.parse import parse


def to_db(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of datetime tuples
    ([start_datetime, end_datetime]) for sql insertion
    """
    out = [
        timepoint.to_db() for timepoint in parse(text, lang, valid)
    ]
    return [item for item in out if item]


def to_python(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of datetime tuples
    ([start_datetime, end_datetime]) for sql insertion
    """
    out = [
        timepoint.to_python() for timepoint in parse(text, lang, valid)
    ]
    return [item for item in out if item]
