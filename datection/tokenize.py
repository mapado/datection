# -*- coding: utf-8 -*-

"""Utilities used for tokenizing a string into time-related tokens."""

import re
import unicodedata


from datection.regex import TIMEPOINT_REGEX
from datection.context import probe
from datection.utils import cached_property
from datection.utils import ensure_unicode


class Token(object):

    """A fragment of text, with a positon and a tag."""

    def __init__(self, content, match, tag, span, action):
        self.content = content
        self.match = match
        self.tag = tag
        self.span = span
        self.action = action

    def __repr__(self):
        return u'<%s - %s - (%d, %d)>' % (
            self.action,
            self.tag,
            self.start,
            self.end)

    def __unicode__(self):
        return self.content

    def __str__(self):
        return unicode(self).encode('utf-8')

    @property
    def start(self):
        return self.span[0]

    @property
    def end(self):
        return self.span[1]

    @property
    def ignored(self):
        return self.action in ['IGNORE', 'TEXT']

    @property
    def is_match(self):
        return self.action == 'MATCH'

    @property
    def is_exclusion(self):
        return self.action == 'EXCLUDE'


class Tokenizer(object):

    """Splits text into time-related tokens."""

    def __init__(self, text, lang):
        self.text = text
        self.lang = lang

    @cached_property
    def timepoint_families(self):
        """The list of all time-related regex in the Tokenizer language."""
        return [det for det in TIMEPOINT_REGEX[self.lang].keys()
                if not det.startswith('_')]

    @staticmethod
    def _remove_subsets(matches):
        """ Remove items contained which span is contained into others'.

        Each item is a Timepoint subclass (Time, DateTime, etc).
        All items which start/end span is contained into other item
        spans will be removed from the output list.

        The span is removed from each returned item, and the output list
        is sorted by the start position of each item span.

        Example: the second and third matches are subsets of the first one.
        Input: [
            (match1, set(5, ..., 15), 'datetime'),
            (match2, set(5, ..., 10), 'date')
            (match3, set(11, ..., 15), 'time')
            (match4, set(0, ... 3), 'time')
        ]
        Output: [(match4, 'time'), (match1, 'datetime')]

        """
        out = matches[:]  # shallow copy
        for tpt1, family1, ctx1 in matches:
            for tpt2, family2, ctx2 in matches:
                if tpt1 != tpt2:  # avoid self comparison
                    span1, span2 = (
                        set(range(*tpt1.span())), set(range(*tpt2.span())))
                    if span1.intersection(span2):
                        # if A ⊃ B or A = B: remove B
                        if span1.issuperset(span2) or span1 == span2:
                            if (tpt2, family2, ctx2) in out:
                                out.remove((tpt2, family2, ctx2))
                        # if A ⊂ B: remove A
                        elif span1.issubset(span2):
                            if (tpt1, family1, ctx1) in out:
                                out.remove((tpt1, family1, ctx1))
        # sort list by match position
        out = sorted(out, key=lambda item: item[0].span()[0])
        return out

    @staticmethod
    def is_separator(text):
        """Return True if the text is only formed of spaces and punctuation
        marks, else, return False.

        If the text is composed of less than 6 chars, it is considered as
        a separator.

        """
        if len(text) < 6:
            return True
        separator_classes = [
            'Pd',  # Punctuation, dash
            'Po',  # Punctuation, other
            'Zs',  # Separator, space
        ]
        return all(unicodedata.category(c) in separator_classes for c in text)

    def search_context(self, context):
        """Return all the non-overlapping time-related regex matches
        from the input textual context.

        """
        matches = []
        for family in self.timepoint_families:
            for pattern in TIMEPOINT_REGEX[self.lang][family]:
                ctx = unicode(context)
                matches.extend(
                    [(m, family, context) for m in re.finditer(pattern, ctx)])
        return matches

    def create_token(self, tag, text=None, match=None, span=None):
        if tag == 'exclusion':
            action = 'EXCLUDE'
        elif tag == 'sep':
            if self.is_separator(text):
                action = 'IGNORE'
            else:
                action = 'TEXT'
        else:
            action = 'MATCH'
        return Token(
            match=match,
            content=match.group() if match is not None else text,
            span=match.span() if match is not None else span,
            tag=tag,
            action=action)

    def create_separator_token(self, start, end):
        span = (start, end)
        text = self.text[span[0]: span[1]]
        if text:
            sep_token = self.create_token(span=span, tag='sep', text=text)
            if not sep_token.ignored:
                return sep_token

    def create_tokens(self, matches):
        """Create a list of tokens from a list of non overlapping matches."""
        tokens = []
        start = 0
        for match, tag, ctx in matches:
            token = self.create_token(
                match=match,
                tag=tag,
                span=ctx.position_in_text(match.span()))
            sep_start, sep_end = ctx.position_in_text((start, token.start))
            sep_token = self.create_separator_token(sep_start, sep_end)
            if sep_token:
                tokens.append(sep_token)
            tokens.append(token)
            start = token.end
        return tokens

    @ensure_unicode
    def tokenize(self):
        contexts = probe(self.text, self.lang)
        if not contexts:
            return []

        matches = []
        for ctx in contexts:
            matches.extend(self.search_context(ctx))
        non_overlapping_matches = self._remove_subsets(matches)
        tokens = self.create_tokens(non_overlapping_matches)
        return tokens


def group_tokens(tokens):
    if len(tokens) == 1:
        return tokens
    out, group = [], [tokens[0]]
    i = 1
    for j, token in enumerate(tokens[1:]):
        if j == len(tokens[1:]) - 1:  # last iteration
            group.append(token)
            out.append(group)
        elif (
            group[i - 1].is_match and token.is_exclusion
            or group[i - 1].is_exclusion and token.is_match
        ):
            group.append(token)
            i += 1
        else:
            out.append(group)
            group = [token]
            i = 1
    return out
