# -*- coding: utf-8 -*-

from builtins import str
import six
import unittest

from datetime import datetime
from datetime import time
from dateutil.rrule import MO, WE, TH, FR, SA, SU

from datection.models import DurationRRule
from datection.utils import isoformat_concat
from datection.utils import normalize_2digit_year
from datection.utils import duration
from datection.utils import group_facebook_hours
from datection.utils import sort_facebook_hours
from datection.utils import normalize_fb_hours
from datection.timepoint import Time
from datection.timepoint import TimeInterval
from datection.timepoint import DateInterval
from datection.timepoint import Weekdays
from datection.timepoint import WeeklyRecurrence


class UtilsTest(unittest.TestCase):

    def test_isoformat_concat(self):
        dt = datetime(2013, 8, 4, 8, 30, 0)
        fmt = isoformat_concat(dt)
        self.assertEqual(fmt, '20130804T083000')

    def test_rrule_duration_wrapper_recurrence(self):
        duration_rrule = {
            # le lundi, du 5 au 30 avril 2014, de 8h à 9h
            'duration': 60,
            'rrule': ('DTSTART:20140405\nRRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;'
                      'BYMINUTE=0;UNTIL=20140430')
        }
        wrapper = DurationRRule(duration_rrule)
        self.assertEqual(wrapper.duration, 60)
        self.assertEqual(
            str(wrapper.rrule), 'DTSTART:20140405T000000\nRRULE:FREQ=WEEKLY;UNTIL=20140430T000000;BYDAY=MO;BYHOUR=8;BYMINUTE=0')
        self.assertTrue(wrapper.is_recurring)
        self.assertFalse(wrapper.is_all_year_recurrence)

    def test_rrule_duration_wrapper_allyear_recurrence(self):
        duration_rrule = {
            # le lundi de 8h à 9h
            'duration': 60,
            'rrule': ('DTSTART:20140405\nRRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;'
                      'BYMINUTE=0;UNTIL=20150405')
        }
        wrapper = DurationRRule(duration_rrule)
        self.assertTrue(wrapper.is_recurring)
        self.assertTrue(wrapper.is_all_year_recurrence)

    def test_rrule_duration_wrapper_no_recurrence(self):
        duration_rrule = {
            # du 5 au 30 avril 2014, de 8h à 9h
            'duration': 60,
            'rrule': ('DTSTART:20140405\nRRULE:FREQ=DAILY;BYHOUR=8;BYMINUTE=0;'
                      'INTERVAL=1;UNTIL=20140430T235959')
        }
        wrapper = DurationRRule(duration_rrule)
        self.assertFalse(wrapper.is_recurring)
        self.assertFalse(wrapper.is_all_year_recurrence)

    def test_serialize_2digit_year(self):
        self.assertEqual(normalize_2digit_year(12), 2012)
        self.assertEqual(normalize_2digit_year(20), 2020)
        self.assertEqual(normalize_2digit_year(40), 1940)
        self.assertEqual(normalize_2digit_year(80), 1980)

    def test_duration_time(self):
        start_time = time(20, 0)
        end_time = time(21, 0)
        self.assertEqual(duration(start_time, end_time), 60)

    def test_duration_Time(self):
        start_time = Time(hour=20, minute=0)
        end_time = Time(hour=21, minute=0)
        self.assertEqual(duration(start_time, end_time), 60)

    def test_duration_datetime_same_day(self):
        start_datetime = datetime(2013, 8, 4, 20, 0)
        end_datetime = datetime(2013, 8, 4, 21, 0)
        self.assertEqual(duration(start_datetime, end_datetime), 60)

    def test_duration_datetime_next_day(self):
        start_datetime = datetime(2013, 8, 4, 20, 0)
        end_datetime = datetime(2013, 8, 5, 21, 0)
        self.assertEqual(duration(start_datetime, end_datetime), 1500)

    def test_duration_datetime(self):
        start_datetime = datetime(2013, 8, 4, 20, 0)
        end_datetime = datetime(2013, 8, 6, 18, 0)
        self.assertEqual(duration(start_datetime, end_datetime), 2760)


class TestFacebookScheduleNormalization(unittest.TestCase):

    def setUp(self):
        self.fb_hours = {
            "mon_2_open": "14:00",
            "mon_2_close": "18:00",
            "mon_1_open": "10:00",
            "mon_1_close": "12:00",
            "wed_1_open": "10:00",
            "wed_1_close": "18:00",
            "thu_1_open": "10:00",
            "thu_1_close": "18:00",
            "fri_1_open": "10:30",
            "fri_1_close": "18:00",
            "sat_1_open": "10:00",
            "sat_1_close": "18:00",
            "sun_1_open": "10:00",
            "sun_1_close": "18:00"
        }

    def test_sort_facebook_hours(self):
        expected = [
            ("mon_1_open", "10:00"), ("mon_1_close", "12:00"),
            ("mon_2_open", "14:00"), ("mon_2_close", "18:00"),
            ("wed_1_open", "10:00"), ("wed_1_close", "18:00"),
            ("thu_1_open", "10:00"), ("thu_1_close", "18:00"),
            ("fri_1_open", "10:30"), ("fri_1_close", "18:00"),
            ("sat_1_open", "10:00"), ("sat_1_close", "18:00"),
            ("sun_1_open", "10:00"), ("sun_1_close", "18:00")
        ]
        self.assertEqual(sort_facebook_hours(self.fb_hours), expected)

    def test_sort_facebook_hours_no_closing(self):
        fb_hours = {
            "mon_2_open": "14:00",
            "mon_2_close": "18:00",
            "mon_1_open": "10:00",
            "mon_1_close": "12:00",
            "wed_1_open": "10:00",
            "wed_1_close": "18:00",
            "thu_1_open": "10:00",
            "fri_1_open": "10:30",
            "fri_1_close": "18:00",
            "sat_1_open": "10:00",
            "sun_1_open": "10:00",
            "sun_1_close": "18:00"
        }
        expected = [
            ("mon_1_open", "10:00"), ("mon_1_close", "12:00"),
            ("mon_2_open", "14:00"), ("mon_2_close", "18:00"),
            ("wed_1_open", "10:00"), ("wed_1_close", "18:00"),
            ("thu_1_open", "10:00"),
            ("fri_1_open", "10:30"), ("fri_1_close", "18:00"),
            ("sat_1_open", "10:00"),
            ("sun_1_open", "10:00"), ("sun_1_close", "18:00")
        ]
        self.assertEqual(sort_facebook_hours(fb_hours), expected)

    def test_group_facebook_hour(self):
        expected = [
            [("mon_1_open", "10:00"), ("mon_1_close", "12:00")],
            [("mon_2_open", "14:00"), ("mon_2_close", "18:00")],
            [("wed_1_open", "10:00"), ("wed_1_close", "18:00")],
            [("thu_1_open", "10:00"), ("thu_1_close", "18:00")],
            [("fri_1_open", "10:30"), ("fri_1_close", "18:00")],
            [("sat_1_open", "10:00"), ("sat_1_close", "18:00")],
            [("sun_1_open", "10:00"), ("sun_1_close", "18:00")]
        ]
        fb_hours = sort_facebook_hours(self.fb_hours)
        self.assertEqual(group_facebook_hours(fb_hours), expected)

    def test_group_facebook_hour_no_closing(self):
        fb_hours = {
            "mon_2_open": "14:00",
            "mon_2_close": "18:00",
            "mon_1_open": "10:00",
            "mon_1_close": "12:00",
            "wed_1_open": "10:00",
            "wed_1_close": "18:00",
            "thu_1_open": "10:00",
            "fri_1_open": "10:30",
            "fri_1_close": "18:00",
            "sat_1_open": "10:00",
            "sun_1_open": "10:00",
            "sun_1_close": "18:00"
        }
        expected = [
            [("mon_1_open", "10:00"), ("mon_1_close", "12:00")],
            [("mon_2_open", "14:00"), ("mon_2_close", "18:00")],
            [("wed_1_open", "10:00"), ("wed_1_close", "18:00")],
            [("thu_1_open", "10:00")],
            [("fri_1_open", "10:30"), ("fri_1_close", "18:00")],
            [("sat_1_open", "10:00")],
            [("sun_1_open", "10:00"), ("sun_1_close", "18:00")]
        ]
        fb_hours = sort_facebook_hours(fb_hours)
        self.assertEqual(group_facebook_hours(fb_hours), expected)

    def test_normalize_fb_hours(self):
        fb_hours = {
            "mon_2_open": "14:00",
            "mon_2_close": "18:00",
            "mon_1_open": "10:00",
            "mon_1_close": "12:00",
            "wed_1_open": "10:00",
            "wed_1_close": "18:00",
            "thu_1_open": "10:00",
            "fri_1_open": "10:30",
            "fri_1_close": "18:00",
            "sat_1_open": "10:00",
            "sun_1_open": "10:00",
            "sun_1_close": "18:00"
        }
        expected = [
            WeeklyRecurrence(
                date_interval=DateInterval.make_undefined(),
                time_interval=TimeInterval(Time(10, 0), Time(12, 0)),
                weekdays=Weekdays([MO])).export(),
            WeeklyRecurrence(
                date_interval=DateInterval.make_undefined(),
                time_interval=TimeInterval(Time(14, 0), Time(18, 0)),
                weekdays=Weekdays([MO])).export(),
            WeeklyRecurrence(
                date_interval=DateInterval.make_undefined(),
                time_interval=TimeInterval(Time(10, 0), Time(18, 0)),
                weekdays=Weekdays([WE])).export(),
            WeeklyRecurrence(
                date_interval=DateInterval.make_undefined(),
                time_interval=TimeInterval(Time(10, 0), Time(10, 0)),
                weekdays=Weekdays([TH])).export(),
            WeeklyRecurrence(
                date_interval=DateInterval.make_undefined(),
                time_interval=TimeInterval(Time(10, 30), Time(18, 00)),
                weekdays=Weekdays([FR])).export(),
            WeeklyRecurrence(
                date_interval=DateInterval.make_undefined(),
                time_interval=TimeInterval(Time(10, 0), Time(10, 0)),
                weekdays=Weekdays([SA])).export(),
            WeeklyRecurrence(
                date_interval=DateInterval.make_undefined(),
                time_interval=TimeInterval(Time(10, 0), Time(18, 0)),
                weekdays=Weekdays([SU])).export(),
        ]
        six.assertCountEqual(self, normalize_fb_hours(fb_hours), expected)
