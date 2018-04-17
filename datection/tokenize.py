# -*- coding: utf-8 -*-

"""Utilities used for tokenizing a string into time-related tokens."""
from __future__ import division
import six

from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import re
import unicodedata

from collections import Counter, defaultdict
from datection.timepoint import NormalizationError
from datection.context import probe, Context
from datection.utils import cached_property


def get_repetitions(txt):
    """ Detect list of repetions in a text with statistics

        for pattern based on numbers

        return list of dict
          {
           'coverage': float,
            'start': int,
            'end': int,
            'qte': int,
            'context': Context,
          }
    """
    r = re.compile(r"(.{6,}?)\1+")
    tok_txt = re.sub(r"\d", 'X', txt).replace('\n', '')

    repetitions = []
    for match in r.finditer(tok_txt):
        idx_start = match.start()
        pattern = match.group(1)
        idx_end = match.end()
        real_case = txt[idx_start: len(pattern) + idx_start]
        qte = old_div(len(match.group(0)), len(pattern))

        context = Context(idx_start, idx_end, real_case, [])
        repetitions.append({
            'context': context,
            'start': idx_start,
            'end': idx_end,
            'qte': qte,
            'coverage': old_div(float(len(pattern) * qte), len(txt))
        })
    return repetitions


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

    def __repr__(self):
        return '%s [%s:%s]' % (self.timepoint_type, self.start_index, self.end_index)


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
            len(self.tokens) >= 3
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
    def language_module(self):
        """The grammar module object related to the Tokenizer language."""
        return __import__(
            'datection.grammar.%s' % (self.lang),
            fromlist=['grammar'])

    @property
    def timepoint_patterns(self):  # pragma: no cover
        """The list of all time-related patterns in the Tokenizer language."""
        return self.language_module.TIMEPOINTS

    @property
    def timepoint_patterns_hierarchy(self):
        """
        Dictionary of patterns complexities
        """
        hierarchy = defaultdict(set)
        for pattern in self.timepoint_patterns:
            if len(pattern) == 3:
                for subpattern in pattern[2]:
                    hierarchy[pattern[0]].add(subpattern[0])
        return hierarchy

    @property
    def language_expressions(self):  # pragma: no cover
        """The list of all time-related expressions in the Tokenizer language.

        """
        return self.language_module.EXPRESSIONS

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
        def spanset(span):
            return frozenset(list(range(span[0], span[1])))

        matches = [(tpt, ctx, spanset(tpt.span)) for tpt, ctx in matches]
        out = matches[:]  # shallow copy

        # First, remove all timepoints which span set is a subset of
        # other timepoints span set
        for group1 in matches:
            for group2 in matches:
                if group1 is group2:
                    continue
                (tpt1, ctx1, span1), (tpt2, ctx2, span2) = group1, group2
                if span1.intersection(span2):
                    if span1 == span2:
                        continue
                    # if A ⊃ B or A = B: remove B
                    elif span1.issuperset(span2) or span1 == span2:
                        if (tpt2, ctx2, span2) in out:
                            out.remove((tpt2, ctx2, span2))
                    # if A ⊂ B: remove A
                    elif span1.issubset(span2):
                        if (tpt1, ctx1, span1) in out:
                            out.remove((tpt1, ctx1, span1))

        # Now, remove all timepoints which span set is intersecting with at
        # least 2 other ones.
        intersections = Counter()
        for group1 in out:
            for group2 in out:
                if group1 is group2:
                    continue
                # Tolerate spans that are exactly the same (they do not really
                # intersect)
                if span1 == span2:
                    continue
                (tpt1, ctx1, span1), (tpt2, ctx2, span2) = group1, group2
                if span1.intersection(span2):
                    intersections[id(group1)] += 1
        out = [(group[0], group[1])
               for group in out if intersections[id(group)] < 2]

        # sort list by match position
        out = sorted(out, key=lambda item: item[0].start_index)

        return out

    def _remove_simpler_patterns(self, matches):
        """
        Removes simple patterns when more complex pattern with same span exists
        """
        def exists_more_complex_match_with_same_span(match, matches):
            """ Checks if more complex pattern with same span exists """
            return any(
                match.timepoint_type in ['weekly_rec'] and
                match.start_index == other.start_index and
                match.end_index == other.end_index and
                other.timepoint_type in self.timepoint_patterns_hierarchy[match.timepoint_type]
                for other, _ in matches
            )

        out = list()
        for match, ctx in matches:
            if exists_more_complex_match_with_same_span(match, matches):
                continue
            out.append((match, ctx))

        out = sorted(out, key=lambda item: item[0].start_index)
        return out

    @staticmethod
    def trim_text(text, start, end):
        """Modify the start/end span so that it does not contain point
        to whitespaces as first and last characters.

        """
        if text.find(' ') == -1:
            return start, end
        new_text = text.lstrip()
        new_start = start + (len(text) - len(new_text))
        new_text = new_text.rstrip()
        new_end = end - (len(text) - len(new_text))
        return new_start, new_end

    @staticmethod
    def clean_context(ctx):
        """Replace certain tokens by whitespaces, to avoid complexifying
        the pyparsing patterns.

        Warning: the context must have the exact same length after
        having being cleaned!

        """
        ctx = re.sub('\n\n', '  ', ctx)
        ctx = re.sub(
            r'\s?(:)\s',
            lambda m: '   ' if m.group().startswith(' ') else '  ',
            ctx)
        ctx = re.sub(r'\(', ' ', ctx)
        ctx = re.sub(r'\)', ' ', ctx)
        ctx = re.sub(r'\.\n', '. ', ctx)
        return ctx

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
        if six.PY2:
            ctx = unicode(context)
        else:
            ctx = context.text[context.start: context.end]
        ctx = self.clean_context(ctx)

        # replacement expression
        for expression, translation in self.language_expressions.items():
            ctx = re.sub(expression, translation, ctx, flags=re.I)

        # if no weekday avoid weekday more complex pattern
        probe_kinds = self._update_probe_kinds(context.probe_kind, ctx)
        timepoints = self.timepoint_patterns
        if 'weekday' not in probe_kinds:
            timepoints = [tp for tp in timepoints if tp[0] != 'weekly_rec']
        n_timepoints = None
        analyse_subpattern = True
        pattern_list = None
        if len(ctx) > 200:
            # if pattern is always same pattern repetion desactive other
            # timepoints
            n_timepoints, patterns = self._extract_timepoint_from_patterns(
                ctx, timepoints)
            if n_timepoints:
                timepoints = n_timepoints
                pattern_list = patterns  # patterns found in the sub-context

        dmatches = self._search_matches_timepoints(
            timepoints, context, ctx, analyse_subpattern, pattern_list
        )
        matches = [t for mt in list(dmatches.values()) for t in mt]
        return matches

    def _extract_timepoint_from_patterns(self, ctx, timepoints):
        """Get useful timepoints from identified patterns with high coverage"""
        pattern_repetitions = get_repetitions(ctx)

        if len(pattern_repetitions) == 1:
            pat = pattern_repetitions[0]
            if pat['coverage'] > 0.9:
                dt_matches = self._search_matches_timepoints(
                    timepoints, pat['context'], pat['context'])
                tps = list(self._get_valid_timepoints(dt_matches, timepoints))
                return tps, list(dt_matches.keys())
        return None, None

    def _search_matches_timepoints(
            self, timepoints, context, ctx, analyse_subpattern=True,
            pattern_list=None):
        """ Find all matches given a list of timepoint parse rules """
        dmatches = defaultdict(list)
        for tp in timepoints:
            mchs = self._search_matches_timepoint(tp, context, ctx)
            if mchs:
                dmatches[tp[0]].extend(mchs)

        # Validate simple pattern before matching related more complex ones
        if analyse_subpattern:
            for tp in self._get_valid_timepoints(dmatches, timepoints):
                if len(tp) == 3:
                    subpatterns = tp[2]
                    # filter on a restricted list of complex patterns for
                    # time efficiency
                    if pattern_list is not None:
                        subpatterns = [sp for sp in subpatterns if sp[0] in
                                       pattern_list]
                    for sp in subpatterns:
                        mchs = self._search_matches_timepoint(sp, context, ctx)
                        if mchs:
                            dmatches[sp[0]].extend(mchs)
        return dmatches

    def _update_probe_kinds(self, found_probe_kinds, new_text):
        """ Catch probe that was not found before replace"""
        probes = __import__(
            'datection.grammar.' + self.lang, fromlist=['grammar']).PROBES
        not_yet_found_probes = (prob for prob in probes if not any(
            pk == prob.resultsName for pk in found_probe_kinds))

        probe_kinds = found_probe_kinds
        for tp_probe in not_yet_found_probes:
            for match, _, _ in tp_probe.scanString(new_text, maxMatches=1):
                probe_kinds = probe_kinds.union(list(match.keys()))
        return probe_kinds

    def _get_valid_timepoints(self, dmatches, timepoints):
        """If all date matches in datetime matches skip date more complex """
        validated_tp = []
        contain_datetime_and_date = True
        if 'date' in dmatches and 'datetime' in dmatches:
                datetime_spans = (dm[0].span for dm in dmatches['datetime'])
                date_spans = (dm[0].span for dm in dmatches['date'])

                contain_datetime_and_date = any(
                    not any(
                        datetime_span[0] <= date_span[0] and
                        datetime_span[1] >= date_span[1]
                        for datetime_span in datetime_spans
                    ) for date_span in date_spans
                )

        if contain_datetime_and_date or ('weekly_rec' in dmatches):
            validated_tp = (
                tp for tp in timepoints if tp[0] in list(dmatches.keys()))
        else:
            sub_pattern = [
                tp for tp in timepoints if tp[0] == 'datetime'
                if tp[0] in list(dmatches.keys())
            ]
            # if only one subpattern and subpattern
            if len(sub_pattern) == 1:

                datetime_spans = (dm[0].span for dm in dmatches['datetime'])
                sub_pattern_spans = (
                    dm[0].span for dm in dmatches[sub_pattern[0][0]]
                )

                contain_both_pattern_and_subpattern = any(
                    not any(
                        sps[0] <= ds[0] and sps[1] >= ds[1]
                        for sps in sub_pattern_spans
                    ) for ds in datetime_spans
                )

                if not contain_both_pattern_and_subpattern:
                    validated_tp = sub_pattern
        return validated_tp

    def _search_matches_timepoint(self, tp, context, ctx):
        """ Try to match regex of this timepoint in given context """
        pname = tp[0]
        pattern = tp[1]
        local_matches = []
        ctx = str(ctx)
        try:
            idx_offset = context.start
            for pattern_matches, start, end in pattern.scanString(ctx):
                start, end = self.trim_text(ctx[start:end], start, end)
                for pattern_match in pattern_matches:
                    match = Match(
                        pattern_match,
                        pname,
                        idx_offset + start,
                        idx_offset + end
                    )
                    local_matches.append((match, context))

        except NormalizationError:
            pass

        return local_matches

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
        if [tok.action for tok in tokens] == ['EXCLUDE', 'MATCH']:
            return []
        if len(tokens) < 3:
            return [TokenGroup(tok) for tok in tokens]
        out = []
        i = 0
        while i < len(tokens):
            window = tokens[i: i + 3]
            window_sep = [tok.action for tok in window]
            if window_sep == ['MATCH', 'EXCLUDE', 'MATCH']:
                token_group = TokenGroup(window)
                i += 3
                # the exlcusion potentially concerns multiple matches,
                # keeps grouping as long as the matches have the same tag
                excluded_tag = window[-1].tag
                while (i < len(tokens)) and (tokens[i].tag == excluded_tag):
                    token_group.tokens.append(tokens[i])
                    i += 1
                out.append(token_group)
            else:
                if tokens[i].is_match:
                    out.append(TokenGroup(tokens[i]))
                i += 1
        return out

    def tokenize(self):
        text = self.text
        # replacement expression
        for expression, translation in six.iteritems(self.language_expressions):
            text = text.replace(expression, translation)

        contexts = probe(text, self.lang)
        if not contexts:
            return []
        matches = []
        for ctx in contexts:
            matches.extend(self.search_context(ctx))
        non_overlapping_matches = self._remove_subsets(matches)
        most_complex_matches = self._remove_simpler_patterns(non_overlapping_matches)
        tokens = self.create_tokens(most_complex_matches)
        token_groups = self.group_tokens(tokens)
        return token_groups
