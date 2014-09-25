# -*- coding: utf-8 -*-

from datection.tokenize import Tokenizer
from datection.schedule import Schedule


def parse(text, lang, valid=True, reference=None):
    """Extract and normalized all timepoints in the argument text, using
    the grammar of the argument language.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If valid is True, only valid Timepoints will be returned.
    Else, invalid Timepoints can also be returned.

    """
    if isinstance(text, str):
        text = text.decode('utf-8')
    schedule = Schedule()
    token_groups = Tokenizer(text, lang, reference).tokenize()
    for token_group in token_groups:
        if token_group.is_single_token:
            token = token_group[0]
            # hack, transmit the span at the last minute so that it gets
            # exported
            token.timepoint.span = token.span
            schedule.add(timepoint=token.timepoint)
        elif token_group.is_exclusion_group:
            token = token_group[0]
            excluded = token_group[2]
            # hack, transmit the span at the last minute so that it gets
            # exported
            token.timepoint.span = token.span[0], excluded.span[1]
            schedule.add(timepoint=token.timepoint, excluded=excluded.timepoint)

    out = list(set(schedule._timepoints))  # remove any redundancy (by security)
    if valid:  # only return valid Timepoints
        return [match for match in out if match.valid]
    return out
