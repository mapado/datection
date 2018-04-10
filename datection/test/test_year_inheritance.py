# -*- coding: utf-8 -*-

"""Test suite of the year transmission process."""

import unittest

from datetime import date

from datection.timepoint import Date
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import Time
from datection.timepoint import WeeklyRecurrence
from datection.timepoint import TimeInterval
from datection.year_inheritance import YearTransmitter


class TestYearTransmission(unittest.TestCase):

    """Test the year transmission process."""

    def setUp(self):
        self.yearless1 = Datetime(
            Date(None, 4, 11), Time(8, 0), Time(18, 0))
        self.yearless2 = Datetime(
            Date(None, 4, 12), Time(8, 0), Time(18, 0))
        self.date_interval = DateInterval(Date(2015, 4, 11), Date(2015, 4, 12))
        timepoints = [self.yearless1, self.yearless2, self.date_interval]
        self.yt = YearTransmitter(timepoints)

    def test_candidate_container(self):
        # Both yearless1 and yearless2 have dates covered by the date
        # interval
        self.assertEqual(
            self.yt.candidate_container(self.yearless1),
            self.date_interval)
        self.assertEqual(
            self.yt.candidate_container(self.yearless2),
            self.date_interval)

        # yearless3 has a date not covered by the date interval
        yearless3 = Datetime(Date(None, 5, 20), Time(8, 0), Time(18, 0))
        self.assertIsNone(self.yt.candidate_container(yearless3))

    def test_transmit(self):
        new_timepoints = self.yt.transmit()
        self.assertEqual(
            new_timepoints,
            [
                Datetime(Date(2015, 4, 11), Time(8, 0), Time(18, 0)),
                Datetime(Date(2015, 4, 12), Time(8, 0), Time(18, 0)),
                DateInterval(Date(2015, 4, 11), Date(2015, 4, 12)),
            ])

    def test_transmit_with_year_not_covered_by_date_interval(self):
        self.yt.timepoints.append(
            Datetime(Date(None, 5, 12), Time(8, 0), Time(18, 0)))

        # no reference
        new_timepoints1 = self.yt.transmit()
        self.assertEqual(
            new_timepoints1,
            [
                Datetime(Date(2015, 4, 11), Time(8, 0), Time(18, 0)),
                Datetime(Date(2015, 4, 12), Time(8, 0), Time(18, 0)),
                DateInterval(Date(2015, 4, 11), Date(2015, 4, 12)),
                Datetime(Date(None, 5, 12), Time(8, 0), Time(18, 0)),
            ])

        # with reference
        self.yt.reference = date(2014, 12, 12)
        new_timepoints2 = self.yt.transmit()
        self.assertEqual(
            new_timepoints2,
            [
                Datetime(Date(2015, 4, 11), Time(8, 0), Time(18, 0)),
                Datetime(Date(2015, 4, 12), Time(8, 0), Time(18, 0)),
                DateInterval(Date(2015, 4, 11), Date(2015, 4, 12)),
                # this date as taken the year of the reference
                Datetime(Date(2014, 5, 12), Time(8, 0), Time(18, 0)),
            ])

    def test_transmit_year_to_unbounded_weekly(self):
        reference = date(2018, 4, 1)
        timepoints = [WeeklyRecurrence.make_undefined(TimeInterval.make_all_day())]

        new_timepoints = YearTransmitter(timepoints, reference).transmit()
        new_weekly_date_interval = new_timepoints[0].date_interval

        self.assertEqual(new_weekly_date_interval.start_date, Date(2018, 4, 1))
        self.assertEqual(new_weekly_date_interval.end_date, Date(2019, 4, 1))
