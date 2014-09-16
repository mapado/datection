# -*- coding: utf-8 -*-

"""Utilities used for tokenizing a string into time-related tokens."""

import unicodedata

from datection.context import probe
from datection.utils import cached_property
from datection.utils import ensure_unicode


class Match(object):

    """A pattern match found in a text."""

    def __init__(self, timepoint, timepoint_type, start_index, end_index):
        self.timepoint = timepoint
        self.timepoint_type = timepoint_type
        self.start_index = start_index
        self.end_index = end_index

    def __eq__(self, other):
        return self.timepoint == other.timepoint

    @property
    def span(self):
        return (self.start_index, self.end_index)


class Token(object):

    """A fragment of text, with a position, a tag and an action."""

    def __init__(self, content, timepoint, tag, span, action):
        self.content = content
        self.timepoint = timepoint
        self.tag = tag
        self.span = span
        self.action = action

    def __repr__(self):  # pragma:: no cover
        return u'<%s %s(%s) [%d:%d]>' % (
            self.__class__.__name__,
            self.action,
            self.tag,
            self.start,
            self.end)

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


class TokenGroup(object):

    """A list of tokens that can either contain a single token or
    two tokens linked by an exclusion one.

    """

    def __init__(self, tokens):  # pragma:: no cover
        if isinstance(tokens, list):
            self.tokens = tokens
        else:
            self.tokens = [tokens]

    def __getitem__(self, index):  # pragma:: no cover
        return self.tokens[index]

    def __repr__(self):  # pragma:: no cover
        return '<%s: [%s]>' % (
            self.__class__.__name__,
            ', '.join(tok.tag for tok in self.tokens))

    def append(self, *args):
        for token in args:
            self.tokens.append(token)

    @property
    def is_single_token(self):
        return len(self.tokens) == 1

    @property
    def is_exclusion_group(self):
        return (
            len(self.tokens) == 3
            and self.tokens[0].is_match
            and self.tokens[1].is_exclusion
            and self.tokens[2].is_match
        )


class Tokenizer(object):

    """Splits text into time-related tokens."""

    def __init__(self, text, lang):
        self.text = text
        self.lang = lang

    @cached_property
    def timepoint_patterns(self):  # pragma: no cover
        """The list of all time-related patterns in the Tokenizer language."""
        lang_grammar_mod = __import__(
            'datection.grammar.%s' % (self.lang),
            fromlist=['grammar'])
        return lang_grammar_mod.TIMEPOINTS

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
        for tpt1, ctx1 in matches:
            for tpt2, ctx2 in matches:
                if tpt1 is not tpt2:  # avoid self comparison
                    span1, span2 = (
                        set(range(*tpt1.span)),
                        set(range(*tpt2.span))
                    )
                    if span1.intersection(span2):
                        # if A ⊃ B or A = B: remove B
                        if span1.issuperset(span2) or span1 == span2:
                            if (tpt2, ctx2) in out:
                                out.remove((tpt2, ctx2))
                        # if A ⊂ B: remove A
                        elif span1.issubset(span2):
                            if (tpt1, ctx1) in out:
                                out.remove((tpt1, ctx1))
        # sort list by match position
        out = sorted(out, key=lambda item: item[0].start_index)
        return out

    @staticmethod
    def trim_text(text, start, end):
        if text.find(' ') == -1:
            return start, end
        new_text = text.lstrip()
        new_start = start + (len(text) - len(new_text))
        new_text = new_text.rstrip()
        new_end = end - (len(text) - len(new_text)) + 1
        return new_start, new_end

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
        ctx = unicode(context)
        for pname, pattern in self.timepoint_patterns:
            for match, start, end in pattern.scanString(ctx):
                start, end = self.trim_text(ctx[start:end], start, end)
                match = Match(match[0], pname, start, end)
                matches.append((match, context))
        return matches

    # pragma: no cover
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
            timepoint=match.timepoint,
            content=text,
            span=match.span if match is not None else span,
            tag=tag,
            action=action)

    def create_tokens(self, matches):
        """Create a list of tokens from a list of non overlapping matches."""
        tokens = []
        start = 0
        for match, ctx in matches:
            token = self.create_token(
                match=match,
                tag=match.timepoint_type,
                text=ctx[match.start_index: match.end_index],
                span=ctx.position_in_text(match.span)
            )
            sep_start, sep_end = ctx.position_in_text((start, token.start))
            tokens.append(token)
            start = token.end
        return tokens

    @staticmethod
    def group_tokens(tokens):
        """Regroup tokens in TokenGroup when they belong together.

        An example of tokens belonging together is two MATCH tokens
        separated by an EXCLUDE one.

        """
        if len(tokens) < 3:
            return [TokenGroup(tok) for tok in tokens]
        out = []
        i = 0
        while i <= len(tokens) - 1:
            window = tokens[i: i + 3]
            window_sep = [tok.action for tok in window]
            if window_sep == ['MATCH', 'EXCLUDE', 'MATCH']:
                out.append(TokenGroup(window))
                i += 3
            else:
                out.append(TokenGroup(tokens[i]))
                i += 1
        return out

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
        token_groups = self.group_tokens(tokens)
        return token_groups
