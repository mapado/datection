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


def to_mongo(text, lang, valid=True):
    """ Detect and normalize all timepoints in the text and convert the
        result into a mongoDB-tailored format, a list of dict

        [
            {'start': start_datetime, 'end': end_datetime},
            ...
        ]

    """
    out = []
    # parse the text and normalize the result into database format
    timepoints = [
        timepoint.to_db()
        for timepoint in parse(text, lang, valid)
    ]

    # convert the database format into specific mongodb format
    timepoints = [item for item in timepoints if item]
    for i, tp_group in enumerate(timepoints):
        out.append(list())
        for tp in tp_group:
            start, end = tp
            out[i].append({'start': start, 'end': end})
    return out


def to_python(text, lang, valid=True):
    """ Perform a timepoint detection on text, and normalize each result to
        python standard objects.

    Return a list of standard datetime python objects
    """
    out = [
        timepoint.to_python() for timepoint in parse(text, lang, valid)
    ]
    return [item for item in out if item]
