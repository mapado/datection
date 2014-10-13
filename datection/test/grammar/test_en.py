# -*- coding: utf-8 -*-

"""Test suite of the english grammar."""


from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import Date
from datection.grammar.en import TIME
from datection.grammar.en import TIME_INTERVAL
from datection.grammar.en import TIME_PATTERN
from datection.grammar.en import BRITISH_DATE
from datection.grammar.en import AMERICAN_DATE
from datection.grammar.en import BRITISH_NUMERIC_DATE
from datection.grammar.en import AMERICAN_NUMERIC_DATE
from datection.grammar.en import NUMERIC_DATE
from datection.grammar.en import DATE
from datection.grammar.en import DATE_PATTERN
from datection.test.test_grammar import TestGrammar
from datection.test.test_grammar import set_pattern


class TestTime(TestGrammar):

    pattern = TIME_PATTERN

    @set_pattern(TIME)
    def test_parse_time(self):
        self.assert_parse_equal(u'10am', Time(10, 0))
        self.assert_parse_equal(u'10 am', Time(10, 0))
        self.assert_parse_equal(u'10AM', Time(10, 0))
        self.assert_parse_equal(u'10pm', Time(22, 0))
        self.assert_parse_equal(u'10PM', Time(22, 0))
        self.assert_parse_equal(u'10 pm', Time(22, 0))
        self.assert_parse_equal(u'10:15pm', Time(22, 15))
        self.assert_parse_equal(u'10:00pm', Time(22, 0))

    @set_pattern(TIME_INTERVAL)
    def test_parse_time_interval(self):
        self.assert_parse_equal(
            u'10am - 3pm', TimeInterval(Time(10, 0), Time(15, 0)))
        self.assert_parse_equal(
            u'from 10am to 3pm', TimeInterval(Time(10, 0), Time(15, 0)))
        self.assert_parse_equal(
            u'bewteen 10am and 3pm', TimeInterval(Time(10, 0), Time(15, 0)))

    def test_parse_time_pattern(self):
        self.assert_parse_equal(
            u'10am', TimeInterval(Time(10, 0), Time(10, 0)))
        self.assert_parse_equal(
            u'10 am', TimeInterval(Time(10, 0), Time(10, 0)))
        self.assert_parse_equal(
            u'10AM', TimeInterval(Time(10, 0), Time(10, 0)))
        self.assert_parse_equal(
            u'10pm', TimeInterval(Time(22, 0), Time(22, 0)))
        self.assert_parse_equal(
            u'10PM', TimeInterval(Time(22, 0), Time(22, 0)))
        self.assert_parse_equal(
            u'10 pm', TimeInterval(Time(22, 0), Time(22, 0)))
        self.assert_parse_equal(
            u'10:15pm', TimeInterval(Time(22, 15), Time(22, 15)))
        self.assert_parse_equal(
            u'10:00pm', TimeInterval(Time(22, 0), Time(22, 0)))
        self.assert_parse_equal(
            u'10am - 3pm', TimeInterval(Time(10, 0), Time(15, 0)))
        self.assert_parse_equal(
            u'from 10am to 3pm', TimeInterval(Time(10, 0), Time(15, 0)))
        self.assert_parse_equal(
            u'bewteen 10am and 3pm', TimeInterval(Time(10, 0), Time(15, 0)))

    def test_parse_several_time_intervals(self):
        timepoints = self.pattern.parseString(u'at 2pm, 3pm, and 6pm')
        self.assertEqual(
            list(timepoints),
            [
                TimeInterval(Time(14, 0), Time(14, 0)),
                TimeInterval(Time(15, 0), Time(15, 0)),
                TimeInterval(Time(18, 0), Time(18, 0)),
            ])


class TestDate(TestGrammar):

    pattern = DATE_PATTERN

    @set_pattern(BRITISH_DATE)
    def test_parse_british_date(self):
        self.assert_parse(u"1st of december 2014")
        self.assert_parse(u"2nd january, 2014")
        self.assert_parse(u"3rd feb. 2014")
        self.assert_parse(u"4th march 2014")

    @set_pattern(AMERICAN_DATE)
    def test_parse_american_date(self):
        self.assert_parse(u"december the 1st, 2014")
        self.assert_parse(u"january 2nd 2014")
        self.assert_parse(u"feb. 3rd 2014")
        self.assert_parse(u"march 4th 2014")

    @set_pattern(DATE)
    def test_parse_date(self):
        self.assert_parse(u"december the 1st, 2014")
        self.assert_parse(u"january 2nd 2014")
        self.assert_parse(u"feb. 3rd 2014")
        self.assert_parse(u"march 4th 2014")
        self.assert_parse(u"1st of december 2014")
        self.assert_parse(u"2nd january, 2014")
        self.assert_parse(u"3rd feb. 2014")
        self.assert_parse(u"4th march 2014")

    @set_pattern(BRITISH_NUMERIC_DATE)
    def test_parse_british_numeric_date(self):
        self.assert_parse(u'05/02/2014')
        self.assert_parse(u'5/2/14')

    @set_pattern(AMERICAN_NUMERIC_DATE)
    def test_parse_american_numeric_date(self):
        self.assert_parse(u'2014/02/05')
        self.assert_parse(u'2014/2/5')

    @set_pattern(NUMERIC_DATE)
    def test_parse_numeric_date(self):
        self.assert_parse(u'2014/02/05')
        self.assert_parse(u'2014/2/5')
        self.assert_parse(u'05/02/2014')
        self.assert_parse(u'5/2/14')

    def test_parse_date_pattern(self):
        self.assert_parse_equal(u"december the 1st, 2014", Date(2014, 12, 1))
        self.assert_parse_equal(u"january 2nd 2014", Date(2014, 1, 2))
        self.assert_parse_equal(u"feb. 3rd 2014", Date(2014, 2, 3))
        self.assert_parse_equal(u"march 4th 2014", Date(2014, 3, 4))
        self.assert_parse_equal(u"1st of december 2014", Date(2014, 12, 1))
        self.assert_parse_equal(u"2nd january, 2014", Date(2014, 1, 2))
        self.assert_parse_equal(u"3rd feb. 2014", Date(2014, 2, 3))
        self.assert_parse_equal(u"4th march 2014", Date(2014, 3, 4))
        self.assert_parse_equal(u'2014/02/05', Date(2014, 2, 5))
        self.assert_parse_equal(u'2014/2/5', Date(2014, 2, 5))
        self.assert_parse_equal(u'05/02/2014', Date(2014, 2, 5))
        self.assert_parse_equal(u'5/2/14', Date(2014, 2, 5))

        # with weekdays
        self.assert_parse_equal(
            u"monday december the 1st, 2014", Date(2014, 12, 1))
        self.assert_parse_equal(u"wed. january 2nd 2014", Date(2014, 1, 2))
