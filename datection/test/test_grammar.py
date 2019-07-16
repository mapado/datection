# -*- coding: utf-8 -*-

"""Test suite of the language agnostic pyparsing regexes."""

import unittest

from pyparsing import ParseException

from datection.grammar import DAY_NUMBER
from datection.grammar import YEAR
from datection.grammar import HOUR
from datection.grammar import MINUTE
from datection.grammar import NUMERIC_MONTH
from datection.grammar import NUMERIC_YEAR


def set_pattern(pattern):
    """Set the argument pattern on the instance only during the test."""
    def decorator(test):
        def wrapper(instance, *args, **kwargs):
            # get the original pattern
            if hasattr(instance, 'pattern'):
                old_pattern = instance.pattern
            else:
                old_pattern = None
            instance.pattern = pattern

            # run the test with the new pattern
            test(instance, *args, **kwargs)

            # restore of the old (or the lack of) pattern
            if old_pattern:
                instance.pattern = old_pattern
            else:
                del instance.pattern
        return wrapper
    return decorator


class TestGrammar(unittest.TestCase):

    """Base class for all regex test classes."""

    def assert_parse(self, text):
        """Return True if the text matches the pattern,
        else return False.

        """
        try:
            self.pattern.parseString(text)
        except ParseException:
            raise AssertionError('Unparsable text "%r"' % (text))

    def assert_unparsable(self, text):
        """Return False if the text matches the pattern,
        else return True.

        """
        try:
            self.pattern.parseString(text)
        except ParseException:
            pass
        else:
            raise AssertionError('Parsable text "%r"' % (text))

    def assert_parse_equal(self, text, expected):
        result = self.pattern.parseString(text)
        if result[0] != expected:
            raise AssertionError("%r != %r" % (result[0], expected))


class TestLanguageAgnosticRegexes(TestGrammar):

    """Test suite of the language agnostic pyparsing regexes."""

    @set_pattern(DAY_NUMBER)
    def test_parse_day_number(self):
        self.assert_parse(u'8')
        self.assert_parse(u'08')
        self.assert_parse(u'12')
        self.assert_parse(u'31')

    @set_pattern(DAY_NUMBER)
    def test_unparsable_day_number(self):
        self.assert_unparsable(u'00')
        self.assert_unparsable(u'32')

    @set_pattern(YEAR)
    def test_parse_year(self):
        self.assert_parse(u'1000')
        self.assert_parse(u'1900')
        self.assert_parse(u'2000')
        self.assert_parse(u'2999')

    @set_pattern(DAY_NUMBER)
    def test_unparsable_year(self):
        self.assert_unparsable(u'999')
        self.assert_unparsable(u'3001')
        self.assert_unparsable(u'h4')
        self.assert_unparsable(u'h30')

    @set_pattern(HOUR)
    def test_parse_hour(self):
        self.assert_parse(u'8')
        self.assert_parse(u'08')
        self.assert_parse(u'24')
        self.assert_parse(u'0')
        self.assert_parse(u'00')

    @set_pattern(HOUR)
    def test_unparsable_hour(self):
        self.assert_unparsable(u'25')
        self.assert_unparsable(u'001')

    @set_pattern(MINUTE)
    def test_parse_minute(self):
        self.assert_parse(u'00')
        self.assert_parse(u'59')

    @set_pattern(MINUTE)
    def test_unparsable_minute(self):
        self.assert_unparsable(u'0')
        self.assert_unparsable(u'60')

    @set_pattern(NUMERIC_MONTH)
    def test_parse_numeric_month(self):
        self.assert_parse(u'01')
        self.assert_parse(u'1')
        self.assert_parse(u'12')

    @set_pattern(NUMERIC_MONTH)
    def test_unparsable_numeric_month(self):
        self.assert_unparsable(u'00')
        self.assert_unparsable(u'0')
        self.assert_unparsable(u'13')

    @set_pattern(NUMERIC_YEAR)
    def test_parse_numeric_year(self):
        self.assert_parse(u'1000')
        self.assert_parse(u'1900')
        self.assert_parse(u'2000')
        self.assert_parse(u'2999')
        self.assert_parse(u'12')
        self.assert_parse(u'00')
        self.assert_parse(u'10')

    @set_pattern(NUMERIC_YEAR)
    def test_unparsable_numeric_year(self):
        self.assert_unparsable(u'100')
        self.assert_unparsable(u'999')
        self.assert_unparsable(u'0')
