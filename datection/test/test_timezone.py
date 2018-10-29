import unittest
import datection.timezone as timezone
from datetime import datetime, timedelta
from dateutil import tz
from freezegun import freeze_time


class TestTimezone(unittest.TestCase):
    
    @freeze_time("2018-07-01 12:00:00")
    def test_timezone_offset_1(self):
        """"""
        reference_timezone = tz.gettz('Europe/Paris')
        offset = timezone.get_timezone_offset(reference_timezone)
        self.assertEqual(offset, timedelta(hours=2))

    @freeze_time("2018-12-01 12:00:00")
    def test_timezone_offset_2(self):
        """"""
        reference_timezone = tz.gettz('Europe/Paris')
        offset = timezone.get_timezone_offset(reference_timezone)
        self.assertEqual(offset, timedelta(hours=1))

    def test_add_timezone(self):
        """"""
        base_datetime = datetime.now()
        self.assertIsNone(base_datetime.tzinfo)
        new_datetime = timezone.add_timezone(base_datetime, 'Europe/Paris')
        self.assertIsNotNone(new_datetime.tzinfo)

        # test with non-existent timezone
        base_datetime = datetime.now()
        self.assertIsNone(base_datetime.tzinfo)
        new_datetime = timezone.add_timezone(base_datetime, 'Europe/Gaillac')
        self.assertIsNone(new_datetime.tzinfo)

    def test_remove_timezone(self):
        """"""
        base_datetime = datetime.now(tz=tz.UTC)
        self.assertIsNotNone(base_datetime.tzinfo)
        new_datetime = timezone.remove_timezone(base_datetime)
        self.assertIsNone(new_datetime.tzinfo)

    @freeze_time("2018-07-01 12:00:00")
    def test_local_time_to_utc_no_timezone_1(self):
        """"""
        now_in_paris = datetime.now()
        now_in_paris_utc = timezone.local_time_to_utc_no_timezone(now_in_paris, 'Europe/Paris')
        self.assertIsNone(now_in_paris_utc.tzinfo)
        self.assertEqual(now_in_paris_utc, datetime(2018, 7, 1, 10, 0, 0))

    @freeze_time("2018-12-01 12:00:00")
    def test_local_time_to_utc_no_timezone_2(self):
        """"""
        now_in_paris = datetime.now()
        now_in_paris_utc = timezone.local_time_to_utc_no_timezone(now_in_paris, 'Europe/Paris')
        self.assertIsNone(now_in_paris_utc.tzinfo)
        self.assertEqual(now_in_paris_utc, datetime(2018, 12, 1, 11, 0, 0))

    @freeze_time("2018-07-02 01:00:00")
    def test_local_time_to_utc_no_timezone_3(self):
        """"""
        now_in_paris = datetime.now()
        now_in_paris_utc = timezone.local_time_to_utc_no_timezone(now_in_paris, 'Europe/Paris')
        self.assertIsNone(now_in_paris_utc.tzinfo)
        self.assertEqual(now_in_paris_utc, datetime(2018, 7, 1, 23, 0, 0))

    @freeze_time("2018-10-25 01:00:00")
    def test_now_local_time_no_timezone_1(self):
        """"""
        now_paris = timezone.now_local_time_no_timezone('Europe/Paris')
        self.assertEqual(now_paris, datetime(2018, 10, 25, 3, 0, 0))
        now_tokyo = timezone.now_local_time_no_timezone('Asia/Tokyo')
        self.assertEqual(now_tokyo, datetime(2018, 10, 25, 10, 0, 0))
        now_new_york = timezone.now_local_time_no_timezone('America/New_York')
        self.assertEqual(now_new_york, datetime(2018, 10, 24, 21, 0, 0))

    @freeze_time("2018-12-25 01:00:00")
    def test_now_local_time_no_timezone_2(self):
        """"""
        now_paris = timezone.now_local_time_no_timezone('Europe/Paris')
        self.assertEqual(now_paris, datetime(2018, 12, 25, 2, 0, 0))
