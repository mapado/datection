# -*- coding: utf-8 -*-

"""Test suite of the datection tokenization utilities."""

import unittest

from datection.tokenize import Tokenizer
from datection.tokenize import TokenGroup
from datection.tokenize import Token
from datection.context import Context


class TestToken(unittest.TestCase):

    """Test suite of the Token class."""

    def setUp(self):
        self.token = Token(
            content=u"Du 8 au 25 mars 2015",
            match=None,
            tag='date_interval',
            span=(20, 40),
            action='MATCH')

    def test_start(self):
        self.assertEqual(self.token.start, 20)

    def test_end(self):
        self.assertEqual(self.token.end, 40)

    def test_match_not_ignored(self):
        self.assertFalse(self.token.ignored)

    def test_text_ignored(self):
        self.token.action = 'TEXT'
        self.assertTrue(self.token.ignored)

    def test_ignored_ignored(self):
        self.token.action = 'IGNORE'
        self.assertTrue(self.token.ignored)

    def test_match(self):
        self.assertTrue(self.token.is_match)
        self.token.action = "IGNORE"
        self.assertFalse(self.token.is_match)

    def test_exclusion(self):
        self.assertFalse(self.token.is_exclusion)
        self.token.action = "EXCLUDE"
        self.assertTrue(self.token.is_exclusion)


class TestTokenGroup(unittest.TestCase):

    def setUp(self):
        self.token_group = TokenGroup([])

    def test_append(self):
        self.assertEqual(len(self.token_group.tokens), 0)
        self.token_group.append('x')
        self.assertEqual(len(self.token_group.tokens), 1)

    def test_is_single_token(self):
        self.assertFalse(self.token_group.is_single_token)
        self.token_group.append(Token(
            content=u"Du 8 au 25 mars 2015",
            match=None,
            tag='date_interval',
            span=(20, 40),
            action='MATCH'))
        self.assertTrue(self.token_group.is_single_token)

    def test_is_exclusion_group(self):
        tok1 = Token(None, None, 'date_interval', None, 'MATCH')
        tok2 = Token(None, None, 'exclusion', None, 'EXCLUDE')
        tok3 = Token(None, None, 'weekly_recurrence', None, 'MATCH')
        self.token_group.append(tok1, tok2, tok3)
        self.assertTrue(self.token_group.is_exclusion_group)


class TestTokenizer(unittest.TestCase):

    """Test suite of the Tokenizer class."""

    class T(object):

        def __init__(self, action):
            self.action = action
            self.tag = action.lower()

    def setUp(self):
        self.tok = Tokenizer(u"Du 5 au 29 mars 2015, sauf les lundis", "fr")

    def test_remove_subsets(self):
        class Timepoint(object):

            def __init__(self, span):
                self._span = span

            def span(self):
                return self._span
        matches = [
            (Timepoint((0, 10)), 'date', 'CONTEXT'),
            (Timepoint((13, 18)), 'time', 'CONTEXT'),
            (Timepoint((0, 18)), 'datetime', 'CONTEXT'),
            (Timepoint((38, 50)), 'date', 'CONTEXT'),
        ]
        expected = matches[2:]
        self.assertEqual(Tokenizer._remove_subsets(matches), expected)

    def test_is_separator(self):
        self.assertTrue(Tokenizer.is_separator(u' le '))
        self.assertTrue(Tokenizer.is_separator(u', '))
        self.assertTrue(Tokenizer.is_separator(u' - '))
        self.assertTrue(Tokenizer.is_separator(u':'))
        self.assertFalse(Tokenizer.is_separator(u"horaires d'ouverture"))

    def test_search_context(self):
        ctx = Context(0, len(self.tok.text), self.tok.text)
        result = self.tok.search_context(ctx)
        families = [r[1] for r in result]
        self.assertItemsEqual(
            families,
            ['date',  # 29 mars 2015
             'date_interval',  # du 5 au 29 mars 2015
             'exclusion',  # sauf
             'weekday_recurrence'])  # les lundis

    def assertTokenGroupEquals(self, tokens, expected_token_groups):
        tokens = [self.T(tok) for tok in tokens]
        token_groups = Tokenizer.group_tokens(tokens)
        out = []
        for group in token_groups:
            tks = []
            for token in group.tokens:
                tks.append(token.action)
            out.append(tks)
        self.assertEqual(out, expected_token_groups)

    def test_group_tokens(self):
        tokens = ['MATCH']
        expected = [['MATCH']]
        self.assertTokenGroupEquals(tokens, expected)

        tokens = ['MATCH', 'MATCH']
        expected = [['MATCH'], ['MATCH']]
        self.assertTokenGroupEquals(tokens, expected)

        tokens = ['MATCH', 'MATCH', 'MATCH']
        expected = [['MATCH'], ['MATCH'], ['MATCH']]
        self.assertTokenGroupEquals(tokens, expected)

        tokens = ['MATCH', 'MATCH', 'MATCH', 'EXCLUDE']
        expected = [['MATCH'], ['MATCH'], ['MATCH'], ['EXCLUDE']]
        self.assertTokenGroupEquals(tokens, expected)

        tokens = ['MATCH', 'MATCH', 'EXCLUDE', 'MATCH']
        expected = [['MATCH'], ['MATCH', 'EXCLUDE', 'MATCH']]
        self.assertTokenGroupEquals(tokens, expected)

        tokens = ['MATCH', 'EXCLUDE', 'MATCH']
        expected = [['MATCH', 'EXCLUDE', 'MATCH']]
        self.assertTokenGroupEquals(tokens, expected)

    def assertTokenEquals(self, token, attrs):
        tok_attrs = (token.content, token.action, token.tag)
        self.assertEqual(tok_attrs, attrs)

    def test_tokenize(self):
        token_groups = self.tok.tokenize()
        self.assertTokenEquals(
            token_groups[0][0],
            (u"Du 5 au 29 mars 2015", "MATCH", "date_interval"))
        self.assertTokenEquals(
            token_groups[0][1],
            (u"sauf", "EXCLUDE", "exclusion"))
        self.assertTokenEquals(
            token_groups[0][2],
            (u"les lundis", "MATCH", "weekday_recurrence"))

    def test_tokenize_no_context(self):
        self.tok.text = u"BLAH BLAH BLAH"
        self.assertEqual(self.tok.tokenize(), [])
