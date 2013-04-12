# -*- coding: utf-8 -*-

"""
Datection exporters to JSON and SQL-compliant formats.
"""

from datection.parse import parse


def to_json(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of serialized, non overlapping normalized timepoints
    expressions.

    """
    return [timepoint.serialize() for timepoint in parse(text, lang, valid)]


def to_sql(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of datetime tuples
    ([start_datetime, end_datetime]) for sql insertion
    """
    out = [
        timepoint.to_sql() for timepoint in parse(text, lang, valid)
    ]
    return [item for item in out if item]
