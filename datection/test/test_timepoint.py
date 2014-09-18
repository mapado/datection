# -*- coding: utf-8 -*-

"""Test suite of the datection.normalize module."""

import unittest
import mock

from datetime import time
from datetime import date
from dateutil.rrule import MO, TU, WE, TH

from datection.timepoint import ALL_DAY
from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import Date
from datection.timepoint import DateList
from datection.timepoint import DateInterval
from datection.timepoint import Datetime
from datection.timepoint import DatetimeList
from datection.timepoint import DatetimeInterval
from datection.timepoint import ContinuousDatetimeInterval
from datection.timepoint import WeeklyRecurrence


class CurrentDayMock(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.get_current_date_patch = mock.patch(
            'datection.timepoint.get_current_date')
        cls.get_current_date_mock = cls.get_current_date_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.get_current_date_patch.stop()

    def setUp(self):
        self.set_current_date(date(2012, 1, 1))

    def set_current_date(self, _date):
        self.get_current_date_mock.return_value = _date


class TestTime(unittest.TestCase):

    def test_equal(self):
        self.assertNotEqual(Time(15, 30), Time(18, 30))
        self.assertEqual(Time(18, 30), Time(18, 30))

    def test_to_python(self):
        self.assertEqual(Time(18, 30).to_python(), time(18, 30))

    def test_valid(self):
        self.assertTrue(Time(15, 30).valid)
        self.assertFalse(Time(25, 30).valid)


class TestTimeInterval(unittest.TestCase):

    def test_equal(self):
        ti1 = TimeInterval(Time(15, 30), Time(18, 30))
        ti2 = TimeInterval(Time(12, 00), Time(20, 00))
        self.assertNotEqual(ti1, ti2)
        self.assertEqual(ti1, TimeInterval(Time(15, 30), Time(18, 30)))

    def test_is_single_time(self):
        self.assertTrue(
            TimeInterval(Time(15, 30), Time(15, 30)).is_single_time())
        self.assertFalse(
            TimeInterval(Time(15, 30), Time(19, 00)).is_single_time())

    def test_valid(self):
        self.assertTrue(TimeInterval(Time(15, 30), Time(18, 30)).valid)
        self.assertFalse(TimeInterval(Time(15, 30), Time(25, 30)).valid)


class TestDate(CurrentDayMock):

    def setUp(self):
        self.d = Date(2015, 10, 12)

    def test_equal(self):
        d1, d2 = Date(2015, 10, 12), Date(2012, 11, 10)
        self.assertNotEqual(d1, d2)
        self.assertEqual(d1, Date(2015, 10, 12))

    def test_to_python(self):
        self.assertEqual(self.d.to_python(), date(2015, 10, 12))

    def test_to_python_invalid(self):
        self.assertIsNone(Date(None, 12, 11).to_python())

    def test_valid(self):
        self.assertTrue(self.d.valid)
        self.assertFalse(Date(None, 12, 11).valid)

    def test_export(self):
        expected = {
            'rrule': ("DTSTART:20151012\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;"
                      "BYHOUR=0"),
            'duration': ALL_DAY
        }
        self.assertDictEqual(self.d.export(), expected)

    def test_future(self):
        self.assertTrue(self.d.future())
        self.set_current_date(date(2016, 11, 12))
        self.assertFalse(self.d.future())
        self.assertTrue(self.d.future(reference=date(2014, 11, 12)))


class TestDateList(CurrentDayMock):

    def setUp(self):
        self.dl = DateList([Date(2013, 11, 12), Date(2013, 11, 13)])

    def test_equal(self):
        dl1 = DateList([Date(2013, 11, 12), Date(2013, 11, 13)])
        dl2 = DateList([Date(2014, 10, 03)])
        self.assertEqual(self.dl, dl1)
        self.assertNotEqual(self.dl, dl2)

    def test_valid(self):
        self.assertTrue(self.dl.valid)
        self.dl.dates[0].year = None
        self.assertFalse(self.dl.valid)

    def test_to_python(self):
        exp = [date(2013, 11, 12), date(2013, 11, 13)]
        self.assertEqual(self.dl.to_python(), exp)

    def test_export(self):
        expected = [
            {
                'rrule': ("DTSTART:20131112\nRRULE:FREQ=DAILY;COUNT=1;"
                          "BYMINUTE=0;BYHOUR=0"),
                'duration': ALL_DAY
            },
            {
                'rrule': ("DTSTART:20131113\nRRULE:FREQ=DAILY;COUNT=1;"
                          "BYMINUTE=0;BYHOUR=0"),
                'duration': ALL_DAY
            }
        ]
        self.assertItemsEqual(self.dl.export(), expected)

    def test_future(self):
        self.assertTrue(self.dl.future())  # today: before

        self.set_current_date(date(2016, 11, 12))  # today: after
        self.assertFalse(self.dl.future())

        self.set_current_date(date(2013, 11, 12))  # today: in between
        self.assertTrue(self.dl.future())


class TestDateInterval(CurrentDayMock):

    def setUp(self):
        self.di = DateInterval(Date(2013, 3, 12), Date(2013, 3, 19))

    def test_equal(self):
        di1 = DateInterval(Date(2013, 3, 12), Date(2013, 3, 19))
        di2 = DateInterval(Date(2014, 8, 10), Date(2014, 8, 19))
        self.assertEqual(self.di, di1)
        self.assertNotEqual(self.di, di2)

    def test_valid(self):
        self.assertTrue(self.di.valid)
        self.di.start_date.year = None
        self.assertFalse(self.di.valid)

    def test_to_python(self):
        expected = [
            date(2013, 3, 12),
            date(2013, 3, 13),
            date(2013, 3, 14),
            date(2013, 3, 15),
            date(2013, 3, 16),
            date(2013, 3, 17),
            date(2013, 3, 18),
            date(2013, 3, 19),
        ]
        self.assertEqual(self.di.to_python(), expected)

    def test_export(self):
        expected = {
            'rrule': ("DTSTART:20130312\nRRULE:FREQ=DAILY;BYHOUR=0;"
                      "BYMINUTE=0;INTERVAL=1;UNTIL=20130319"),
            'duration': ALL_DAY
        }
        self.assertDictEqual(self.di.export(), expected)

    def test_future(self):
        self.assertTrue(self.di.future())  # today: before

        self.set_current_date(date(2016, 11, 12))  # today: after
        self.assertFalse(self.di.future())

        self.set_current_date(date(2013, 3, 14))  # today: in between
        self.assertTrue(self.di.future())


class TestDatetime(CurrentDayMock):

    def setUp(self):
        self.dt = Datetime(Date(2013, 12, 11), Time(20, 30))
        self.dt2 = Datetime(Date(2013, 12, 11), Time(20, 30), Time(21, 30))

    def test_init(self):
        dt = Datetime(Date(2013, 12, 11), Time(20, 30))
        self.assertEqual(dt.start_time, dt.end_time)
        dt2 = Datetime(Date(2013, 12, 11), Time(20, 30), Time(21, 30))
        self.assertNotEqual(dt2.start_time, dt2.end_time)

    def test_equal(self):
        dt = Datetime(Date(2013, 12, 11), Time(20, 30))
        dt2 = Datetime(Date(2013, 12, 11), Time(20, 30), Time(21, 30))
        self.assertEqual(self.dt, dt)
        self.assertNotEqual(self.dt, dt2)

    def test_valid(self):
        self.assertTrue(self.dt.valid)
        self.dt.date.year = None
        self.assertFalse(self.dt.valid)

    def test_export(self):
        expected = {
            'rrule': ("DTSTART:20131211\nRRULE:FREQ=DAILY;COUNT=1;"
                      "BYMINUTE=30;BYHOUR=20"),
            'duration': 0
        }
        self.assertDictEqual(self.dt.export(), expected)

    def test_export_with_time_interval(self):
        expected = {
            'rrule': ("DTSTART:20131211\nRRULE:FREQ=DAILY;COUNT=1;"
                      "BYMINUTE=30;BYHOUR=20"),
            'duration': 60
        }
        self.assertDictEqual(self.dt2.export(), expected)

    def test_future(self):
        self.assertTrue(self.dt.future())

        self.set_current_date(date(2016, 11, 12))  # today: after
        self.assertFalse(self.dt.future())


class TestDatetimeList(CurrentDayMock):

    def setUp(self):
        self.dtl = DatetimeList([
            Datetime(Date(2013, 12, 11), Time(20, 30)),
            Datetime(Date(2013, 12, 12), Time(20, 30)),
        ])

    def test_time_interval(self):
        self.assertEqual(
            self.dtl.time_interval, TimeInterval(Time(20, 30), Time(20, 30)))

    def test_dates(self):
        self.assertEqual(
            self.dtl.dates,
            [Date(2013, 12, 11), Date(2013, 12, 12)])

    def test_valid(self):
        self.assertTrue(self.dtl.valid)
        self.dtl[0].date.year = None
        self.assertFalse(self.dtl.valid)

    def test_export(self):
        expected = [
            {
                'rrule': ("DTSTART:20131211\nRRULE:FREQ=DAILY;COUNT=1;"
                          "BYMINUTE=30;BYHOUR=20"),
                'duration': 0
            },
            {
                'rrule': ("DTSTART:20131212\nRRULE:FREQ=DAILY;COUNT=1;"
                          "BYMINUTE=30;BYHOUR=20"),
                'duration': 0
            }
        ]
        self.assertItemsEqual(self.dtl.export(), expected)

    # def test_to_python(self):
    #     self.assertListEqual(
    #         self.dtl.to_python(),
    #         [
    #             (
    #                 datetime(2013, 12, 11, 20, 30),
    #                 datetime(2013, 12, 11, 20, 30)
    #             ),
    #             (
    #                 datetime(2013, 12, 12, 20, 30),
    #                 datetime(2013, 12, 12, 20, 30),
    #             )
    #         ]
    #     )

    def test_future(self):
        self.assertTrue(self.dtl.future())  # today: before

        self.set_current_date(date(2016, 11, 12))  # today: after
        self.assertFalse(self.dtl.future())

        self.set_current_date(date(2013, 12, 12))  # today: in between
        self.assertTrue(self.dtl.future())


class TestDatetimeInterval(CurrentDayMock):

    def setUp(self):
        self.dtl = DatetimeInterval(
            DateInterval(Date(2015, 4, 12), Date(2015, 4, 14)),
            TimeInterval(Time(18, 0), Time(19, 0)),
        )

    def test_equal(self):
        dtl1 = DatetimeInterval(
            DateInterval(Date(2015, 4, 12), Date(2015, 4, 14)),
            TimeInterval(Time(18, 0), Time(19, 0)),
        )
        dtl2 = DatetimeInterval(
            DateInterval(Date(2012, 4, 12), Date(2012, 4, 12)),
            TimeInterval(Time(18, 0), Time(19, 0)),
        )
        self.assertEqual(self.dtl, dtl1)
        self.assertNotEqual(self.dtl, dtl2)

    def test_valid(self):
        self.assertTrue(self.dtl.valid)
        self.dtl.date_interval.start_date.year = None
        self.assertFalse(self.dtl.valid)

    def test_future(self):
        self.assertTrue(self.dtl.future())  # today: before

        self.set_current_date(date(2016, 11, 12))  # today: after
        self.assertFalse(self.dtl.future())

        self.set_current_date(date(2015, 4, 13))  # today: in between
        self.assertTrue(self.dtl.future())

    # def test_to_python(self):
    #     expected = [
    #         (datetime(2015, 4, 12, 18, 0), datetime(2015, 4, 12, 19, 0)),
    #         (datetime(2015, 4, 13, 18, 0), datetime(2015, 4, 13, 19, 0)),
    #         (datetime(2015, 4, 14, 18, 0), datetime(2015, 4, 14, 19, 0)),
    #     ]
    #     self.assertEqual(self.dtl.to_python(), expected)

    def test_export(self):
        expected = {
            'duration': 60,
            'rrule': ("DTSTART:20150412\nRRULE:FREQ=DAILY;BYHOUR=18;"
                      "BYMINUTE=0;INTERVAL=1;UNTIL=20150414T235959")
        }
        self.assertEqual(self.dtl.export(), expected)


class TestContinuousDatetimeInterval(CurrentDayMock):

    def setUp(self):
        self.cdti = ContinuousDatetimeInterval(
            Date(2015, 4, 8),
            Time(18, 30),
            Date(2015, 4, 9),
            Time(5, 0))

    def test_equal(self):
        cdti1 = ContinuousDatetimeInterval(
            Date(2015, 4, 8),
            Time(18, 30),
            Date(2015, 4, 9),
            Time(5, 0))
        cdti2 = ContinuousDatetimeInterval(
            Date(2012, 4, 8),  # diff date
            Time(18, 30),
            Date(2015, 4, 9),
            Time(5, 0))
        self.assertEqual(self.cdti, cdti1)
        self.assertNotEqual(self.cdti, cdti2)

    def test_valid(self):
        self.assertTrue(self.cdti.valid)

    def test_valid_startdate_after_enddate(self):
        cdti = ContinuousDatetimeInterval(
            Date(2015, 4, 9),
            Time(18, 30),
            Date(2015, 4, 8),
            Time(5, 0))
        self.assertFalse(cdti.valid)

    def test_future(self):
        self.assertTrue(self.cdti.future())  # today: before

        self.set_current_date(date(2016, 11, 12))  # today: after
        self.assertFalse(self.cdti.future())

        self.set_current_date(date(2015, 4, 9))  # today: in between
        self.assertTrue(self.cdti.future())

    def test_export(self):
        expected = {
            'continuous': True,
            'duration': 630,
            'rrule': ("DTSTART:20150408\nRRULE:FREQ=DAILY;BYHOUR=18;"
                      "BYMINUTE=30;INTERVAL=1;UNTIL=20150409T235959")
        }
        self.assertDictEqual(self.cdti.export(), expected)


class TestWeeklyRecurrence(CurrentDayMock):

    def setUp(self):
        self.wkr = WeeklyRecurrence(
            DateInterval(Date(2015, 4, 5), Date(2015, 6, 25)),
            TimeInterval(Time(10, 0), Time(18, 30)),
            [MO, TU, WE, TH]
        )

    def test_valid(self):
        self.assertTrue(self.wkr.valid)
        self.wkr.weekdays = []
        self.assertFalse(self.wkr.valid)

    def test_future(self):
        self.assertTrue(self.wkr.future())  # today: before

        self.set_current_date(date(2016, 11, 12))  # today: after
        self.assertFalse(self.wkr.future())

        self.set_current_date(date(2015, 4, 9))  # today: in between
        self.assertTrue(self.wkr.future())

    def test_export(self):
        expected = {
            'duration': 510,
            'rrule': ("DTSTART:20150405\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH;"
                      "BYHOUR=10;BYMINUTE=0;UNTIL=20150625T235959")
        }
        self.assertDictEqual(self.wkr.export(), expected)
