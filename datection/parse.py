# -*- coding: utf-8 -*-

import six

# remove newlines from default whitespace characters
from pyparsing import ParserElement
ParserElement.setDefaultWhitespaceChars(' \t')

from datection.lang import detect_language
from datection.tokenize import Tokenizer
from datection.schedule import Schedule
from datection.year_inheritance import YearTransmitter
from datection.coherency import TimepointCoherencyFilter
from datection.timepoint import Time
from datection.timepoint import TimeInterval


def parse(text, lang, valid=True, reference=None):
    """Extract and normalized all timepoints in the argument text, using
    the grammar of the argument language.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If valid is True, only valid Timepoints will be returned.

    """
    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')
    text = text.lower()

    lang = detect_language(text, lang)

    schedule = Schedule()
    token_groups = Tokenizer(text, lang).tokenize()

    # if we only have timings and no date, we rather
    # return no timepoint than inferring a day (today?
    # every day?)
    if all(
        type(token.timepoint) in [Time, TimeInterval]
        for token_group in token_groups
        for token in token_group
    ):
        return []

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
            excluded_tps = []
            for tok in token_group[2:]:
                tok.timepoint.span = tok.span
                excluded_tps.append(tok.timepoint)
            # hack, transmit the span at the last minute so that it gets
            # exported
            token.timepoint.span = token.span[0], token_group[-1].span[1]
            schedule.add(
                timepoint=token.timepoint, excluded_tps=excluded_tps)

    # Merge unassigned timings with dates that have no timings
    schedule.complete_timings()

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
