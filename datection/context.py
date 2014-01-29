# -*- coding: utf-8 -*-

"""
This module defines some class and functions used for probing some input text.

If the probe detects some temporal (date/time) references in the text, then
the whole detection/normalisation process can be used. Otherwhise, the text
is not processed.

We use this technique for performance reasons: some regex can be greedy, thus
it makes sense to use it only when necessary.
"""

import re

from datection.regex import TIMEPOINT_PROBE


class Context(object):

    """ An object representing the textual context around a temporal reference
        detected in a text, by the datection regexes.

        :param match_start: the start index of the match span (int)
        :param match_end: the end index of the match span (int)
        :param text: the input text (str)
        :param size: the number of characters of context (int)

        Example: A sequence is matched at the index span (130, 137).
        By creating a Context(130, 137, size=50), we select the string defined
        between the chars of index 80 and 187.

    """

    def __init__(self, match_start, match_end, text, size=30):
        # deduce Context start and end index from match start/end index
        # and context size
        if match_start - size > 0:
            self.start = match_start - size
        else:
            self.start = 0
        self.end = match_end + size
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        self.text = text  # the input text
        self.size = size  # the number of characters of context

    def __add__(self, item):
        """ The result of the addition of two Contexts is a Context which
            start index is the least of both, and which end index is the
            greatest.

            Ex: Context(120, 140) + Context(130, 150) = Context(120, 150)

        """
        return Context(
            match_start=min((self.start, item.start)) + self.size,
            match_end=max((self.end, item.end)) - self.size,
            text=self.text,
            size=self.size,
        )

    def __contains__(self, item):
        """ Context is in another context if their span overlap """
        return item.start in xrange(self.start, self.end)

    def __repr__(self):
        return self.text[self.start: self.end]

    def __eq__(self, item):
        return self.__dict__ == item.__dict__

    def __hash__(self):
        return hash(str(self))

    def __len__(self):
        return self.end - self.start

    def position_in_text(self, span):
        return (self.start + span[0], self.start + span[1])


def probe(text, lang):
    """ Scans the text for very simple markers, indicating the presence of
        temporal patterns.

        :param text: the text to probe (basestring)
        :param lang: the 2 character code of the text language (str)
        :param context_size: the number of character before and after a probe
        match to be taken as context.

        :return: list of non overlapping text fragments, sorted by order of
        appearance in the input text.

    """
    matches = []
    for tp_probe in TIMEPOINT_PROBE[lang]:
        for match in re.finditer(tp_probe, text):
            start, end = match.span()  # start/end indexes of the match in text
            matches.extend(
                [
                    Context(start, end, text)
                    for match in re.finditer(tp_probe, text)
                ]
            )

    out = list(set(matches))  # remove redundant matches
    # sort return list by order of apperance in the text
    out = sorted(out, key=lambda x: x.start)

    # merge overriding contexts
    out = independants(out)
    if not out:
        return []
    return out


def independants(contexts):
    """ Reduce the input context list by combining all overlapping contexts.

    If the start index of a context1 object is bewteen the start and end indexes
    of another context2 object, context1 thus overlapps context2 (and inversely).
    They then need to be merged into a single context.

    :param contexts: a list of datection.context.Context
    :return: a list of non overlapping strings, containing temporal information

    """
    if not contexts:
        return []
    if len(contexts) == 1:  # if only one context, return it as a str
        return [str(contexts[0])]

    out = []
    i = 0
    while i < len(contexts) - 1:
        history = contexts[i]  # make the first context history
        curr = contexts[i + 1]

        # while current context overlaps history, merge them together
        if curr in history:
            while curr in history:
                history += curr
                if i == len(contexts) - 1:
                    break
                i += 1
                curr = contexts[i]  # fetch next context
        else:
            i += 1
        out.append(history)  # add independant context to return list

    # last item
    if curr in history and len(out) > 0:
        # add item to the last context
        out[-1] = out[-1] + curr
    else:   # independant last context
        # create new context
        out.append(curr)
    # convert the Contexts to string and return them
    return sorted(out, key=lambda cx: cx.start)
