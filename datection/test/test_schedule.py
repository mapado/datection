# -*- coding: utf-8 -*-

"""Test suite of the datection.schedule module"""

import unittest

from dateutil.rrule import weekdays as all_weekdays
from dateutil.rrule import MO, TU, FR

from datection.timepoint import Date
from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import DateList
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import DatetimeInterval
from datection.timepoint import DatetimeList
from datection.timepoint import ContinuousDatetimeInterval
from datection.timepoint import Weekdays
from datection.timepoint import WeeklyRecurrence
from datection.schedule import Times
from datection.schedule import DateSchedule
from datection.schedule import DateListSchedule
from datection.schedule import DateIntervalSchedule


class TestTimes(unittest.TestCase):

    def test_from_time_interval_with_single_time(self):
        ti = TimeInterval(Time(19, 0), Time(19, 0))
        times = Times.from_time_interval(ti)
        self.assertEqual(times.singles, [Time(19, 0)])
        self.assertEqual(times.intervals, [])
        self.assertEqual(times.continuous_intervals, [])

    def test_from_time_interval(self):
        ti = TimeInterval(Time(19, 0), Time(20, 0))
        times = Times.from_time_interval(ti)
        self.assertEqual(times.intervals, [ti])
        self.assertEqual(times.singles, [])
        self.assertEqual(times.continuous_intervals, [])


class TestDateSchedule(unittest.TestCase):

    def test_from_date(self):
        d = Date(2015, 4, 12)
        dsch = DateSchedule.from_date(d)
        self.assertEqual(dsch.times.intervals,
                         [TimeInterval(Time(0, 0), Time(23, 59))])
        self.assertEqual(dsch.date, d)

    def test_from_datetime(self):
        dt = Datetime(Date(2015, 4, 12), Time(19, 0))
        dsch = DateSchedule.from_datetime(dt)
        self.assertEqual(dsch.times.singles, [Time(19, 0)])
        self.assertEqual(dsch.date, dt.date)


class TestDateListSchedule(unittest.TestCase):

    def test_from_datelist(self):
        dl = DateList([Date(2015, 6, 1), Date(2015, 6, 2)])
        dlsch = DateListSchedule.from_datelist(dl)
        self.assertEqual(dlsch.dates[0], dl.dates[0])
        self.assertEqual(dlsch.dates[1], dl.dates[1])
        self.assertEqual(dlsch.times.intervals, [
                         TimeInterval(Time(0, 0), Time(23, 59))])

    def test_from_datetime_list(self):
        dtl = DatetimeList([
            Datetime(Date(2015, 6, 1), Time(18, 0)),
            Datetime(Date(2015, 6, 2), Time(18, 0))
        ])
        dlsch = DateListSchedule.from_datetime_list(dtl)
        self.assertEqual(dlsch.dates[0], dtl.dates[0])
        self.assertEqual(dlsch.dates[1], dtl.dates[1])
        self.assertEqual(dlsch.times.singles, [Time(18, 0)])


class TestDateIntervalSchedule(unittest.TestCase):

    def test_from_weekly_recurrence(self):
        wk = WeeklyRecurrence(
            date_interval=DateInterval(Date(2015, 6, 1), Date(2015, 7, 15)),
            time_interval=TimeInterval(Time(18, 0), Time(22, 30)),
            weekdays=Weekdays([MO, TU, FR])
        )
        disch = DateIntervalSchedule.from_weekly_recurrence(wk)
        self.assertEqual(
            disch.times.intervals,
            [TimeInterval(Time(18, 0), Time(22, 30))])
        self.assertEqual(
            disch.date_interval,
            DateInterval(Date(2015, 6, 1), Date(2015, 7, 15)))
        self.assertEqual(disch.weekdays, [MO, TU, FR])

    def test_from_date_interval(self):
        di = DateInterval(Date(2015, 6, 2), Date(2015, 6, 28))
        disch = DateIntervalSchedule.from_date_interval(di)
        self.assertEqual(disch.date_interval, di)
        self.assertEqual(disch.times.intervals, [
                         TimeInterval(Time(0, 0), Time(23, 59))])
        self.assertEqual(disch.weekdays, all_weekdays)

    def test_from_datetime_interval(self):
        dti = DatetimeInterval(
            date_interval=DateInterval(Date(2015, 6, 2), Date(2015, 6, 28)),
            time_interval=TimeInterval(Time(18, 0), Time(23, 0))
        )
        disch = DateIntervalSchedule.from_datetime_interval(dti)
        self.assertEqual(disch.date_interval, dti.date_interval)
        self.assertEqual(disch.times.intervals, [
                         TimeInterval(Time(18, 0), Time(23, 0))])
        self.assertEqual(disch.weekdays, all_weekdays)

    def test_from_continuous_datetime_interval(self):
        cdti = ContinuousDatetimeInterval(
            start_date=Date(2015, 6, 2),
            end_date=Date(2015, 6, 3),
            start_time=Time(18, 0),
            end_time=Time(8, 0)
        )
        disch = DateIntervalSchedule.from_continuous_datetime_interval(cdti)
        self.assertEqual(
            disch.date_interval, DateInterval(cdti.start_date, cdti.end_date))
        self.assertEqual(disch.times.continuous_intervals, [
                         TimeInterval(Time(18, 0), Time(8, 0))])
        self.assertEqual(disch.weekdays, all_weekdays)
