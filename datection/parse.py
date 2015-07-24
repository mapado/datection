# -*- coding: utf-8 -*-

from datection.lang import detect_language
from datection.tokenize import Tokenizer
from datection.schedule import Schedule
from datection.year_inheritance import YearTransmitter
from datection.coherency import TimepointCoherencyFilter


def parse(text, lang, valid=True, reference=None):
    """Extract and normalized all timepoints in the argument text, using
    the grammar of the argument language.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If valid is True, only valid Timepoints will be returned.

    """
    if isinstance(text, str):
        text = text.decode('utf-8')
    text = text.lower()

    lang = detect_language(text, lang)

    schedule = Schedule()
    token_groups = Tokenizer(text, lang).tokenize()
    for token_group in token_groups:
        if token_group.is_single_token:
            token = token_group[0]
            if not token.is_exclusion:
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
            schedule.add(
                timepoint=token.timepoint, excluded=excluded.timepoint)

    # remove any redundancy
    timepoints = list(set(schedule._timepoints))

    # Perform year inheritance, when necessary
    timepoints = YearTransmitter(timepoints, reference=reference).transmit()

    # Remove timepoints already defined by others, thus removing
    # duplicate content
    # Avoid fix/recurrent propositions
    timepoints = TimepointCoherencyFilter(timepoints).apply_coherency_rules()

    if valid:  # only return valid Timepoints
        # Now that all the missing year inheritance has been performed
        # if a Timepoint is still missing a year, we consider it as invalid
        for timepoint in timepoints:
            timepoint.allow_missing_year = False
        return [match for match in timepoints if match.valid]
    return timepoints
