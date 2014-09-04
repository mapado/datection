# -*- coding: utf-8 -*-

from datection.normalize import timepoint_factory
from datection.tokenize import Tokenizer


def normalize_token(token, lang):
    return timepoint_factory(
        detector=token.tag,
        data=token.match.groupdict(),
        lang=lang,
        span=token.span)


def parse(text, lang, valid=True):
    """ Perform a date detection on text with all timepoint regex.

    Returns a list of non overlapping normalized timepoints
    expressions.

    If ``valid=True``, only valid Timepoints will be returned.
    Else, invalid Timepoints can also be returned.

    """
    out = []
    token_groups = Tokenizer(text, lang).tokenize()
    for token_group in token_groups:
        if token_group.is_single_token:
            token = token_group[0]
            normalized_timepoint = normalize_token(token, lang)
        elif token_group.is_exclusion_group:
            timepoint = normalize_token(token_group[0], lang)
            exclusion = normalize_token(token_group[2], lang)
            normalized_timepoint = timepoint - exclusion

        out.append(normalized_timepoint)

    out = list(set(out))  # remove any redundancy (by security)
    if valid:  # only return valid Timepoints
        return [match for match in out if match.valid]
    return out
