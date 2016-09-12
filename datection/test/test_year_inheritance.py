# -*- coding: utf-8 -*-

"""Test suite of the year transmission process."""

import unittest

from datetime import date

from datection.timepoint import Date
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import Time
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
                Datetime(Date(2015, 5, 12), Time(8, 0), Time(18, 0)),
            ])

    def test_reference_ongoing(self):
        ref = date(2015, 6, 1)
        timeless = []
        timeless.append(DateInterval(Date(None, 12, 20), Date(None, 6, 14)))
        timeless.append(DateInterval(Date(None, 5, 20), Date(None, 8, 14)))
        timeless.append(DateInterval(Date(None, 5, 20), Date(None, 1, 14)))
        timeless.append(Date(None, 6, 1))
        yt = YearTransmitter(timeless)
        yt.reference = ref

        self.assertEqual(
            yt.transmit(),
            [
                DateInterval(Date(2014, 12, 20), Date(2015, 6, 14)),
                DateInterval(Date(2015, 5, 20), Date(2015, 8, 14)),
                DateInterval(Date(2015, 5, 20), Date(2016, 1, 14)),
                Date(2015, 6, 1),
            ])

    def test_reference_just_passed(self):
        ref = date(2015, 02, 10)
        timeless = []
        timeless.append(Date(None, 02, 05))
        timeless.append(Date(None, 01, 05))
        timeless.append(Date(None, 12, 05))
        timeless.append(DateInterval(Date(None, 12, 05), Date(None, 1, 14)))
        yt = YearTransmitter(timeless)
        yt.reference = ref

        self.assertEqual(
            yt.transmit(),
            [
                Date(2015, 02, 05),
                Date(2015, 01, 05),
                Date(2014, 12, 05),
                DateInterval(Date(2014, 12, 05), Date(2015, 1, 14)),
            ])

    def test_reference_upcomming(self):
        ref = date(2015, 10, 25)
        timeless = []
        timeless.append(Date(None, 02, 05))
        timeless.append(DateInterval(Date(None, 03, 05), Date(None, 9, 14)))
        yt = YearTransmitter(timeless)
        yt.reference = ref

        self.assertEqual(
            yt.transmit(),
            [
                Date(2016, 02, 05),
                DateInterval(Date(2016, 03, 05), Date(2016, 9, 14)),
            ])
