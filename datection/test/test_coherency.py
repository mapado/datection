# -*- coding: utf-8 -*-

"""Test suite of the timepoint coherency filter."""

import unittest

from datection.timepoint import Date
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import Time

from datection.models import DurationRRule
from datection.coherency import TimepointCoherencyFilter


class TestTimepointCoherencyFilter(unittest.TestCase):

    """Test suite of the timepoint coherency filter."""

    def test_deduplicate_date_interval_and_dates(self):
        timepoints = [
            DateInterval(Date(2014, 11, 12), Date(2014, 11, 14)),
            Date(2014, 11, 12),
            Date(2014, 11, 13),
            Date(2014, 11, 14)
        ]
        cf = TimepointCoherencyFilter(timepoints)
        cf.deduplicate_date_interval_and_dates()

        self.assertEqual(
            cf.timepoints,
            [
                Date(2014, 11, 12),
                Date(2014, 11, 13),
                Date(2014, 11, 14)
            ]
        )

    def test_deduplicate_date_interval_and_datetimes(self):
        timepoints = [
            DateInterval(Date(2014, 11, 12), Date(2014, 11, 14)),
            Datetime(Date(2014, 11, 12), Time(18, 0), Time(20, 0)),
            Datetime(Date(2014, 11, 13), Time(18, 0), Time(20, 0)),
            Datetime(Date(2014, 11, 14), Time(18, 0), Time(20, 0))
        ]
        cf = TimepointCoherencyFilter(timepoints)
        cf.deduplicate_date_interval_and_dates()

        self.assertEqual(
            cf.timepoints,
            [
                Datetime(Date(2014, 11, 12), Time(18, 0), Time(20, 0)),
                Datetime(Date(2014, 11, 13), Time(18, 0), Time(20, 0)),
                Datetime(Date(2014, 11, 14), Time(18, 0), Time(20, 0))
            ]
        )
