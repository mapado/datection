# -*- coding: utf-8 -*-

from datection.tokenize import Tokenizer
from datection.schedule import Schedule


def parse(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If ``valid=True``, only valid Timepoints will be returned.
    Else, invalid Timepoints can also be returned.

    """
    schedule = Schedule()
    token_groups = Tokenizer(text, lang).tokenize()
    for token_group in token_groups:
        if token_group.is_single_token:
            token = token_group[0]
            schedule.add(timepoint=token.timepoint)
        elif token_group.is_exclusion_group:
            token = token_group[0]
            excluded = token_group[2]
            schedule.add(timepoint=token.timepoint, excluded=excluded.timepoint)

    out = list(set(schedule._timepoints))  # remove any redundancy (by security)
    if valid:  # only return valid Timepoints
        return [match for match in out if match.valid]
    return out
