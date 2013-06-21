import unittest

from datection.future import is_future, filter_future

from datetime import datetime


class TestFuture(unittest.TestCase):

    def test_future_start_end_before_reference(self):
        start = datetime(year=2013, month=6, day=10, hour=12, minute=0)
        end = datetime(year=2013, month=6, day=10, hour=18, minute=0)
        # reference after end timepoint
        reference = datetime(year=2013, month=7, day=10, hour=18, minute=0)
        self.assertFalse(is_future((start, end), reference))

    def test_future_start_end_after_reference(self):
        start = datetime(year=2013, month=6, day=10, hour=12, minute=0)
        end = datetime(year=2013, month=6, day=10, hour=18, minute=0)
        # reference before start and end timepoints
        reference = datetime(year=2013, month=5, day=10, hour=18, minute=0)
        self.assertTrue(is_future((start, end), reference))

    def test_future_reference_between_start_end(self):
        start = datetime(year=2013, month=6, day=8, hour=12, minute=0)
        end = datetime(year=2013, month=6, day=10, hour=18, minute=0)
        # reference bewteen start and end timepoints
        reference = datetime(year=2013, month=6, day=9, hour=18, minute=0)
        self.assertTrue(is_future((start, end), reference))

    def test_filter_future(self):
        reference = datetime(2012, 6, 10, 6, 6)
        schedules = [
            [
                {  # PAST
                    'start': datetime(2012, 6, 9, 0, 0),
                    'end': datetime(2012, 6, 9, 23, 59, 59)
                }
            ],
            [
                {  # FUTURE
                    'start': datetime(2012, 6, 7, 0, 0),
                    'end': datetime(2012, 6, 12, 23, 59, 59)
                }
            ]
        ]
        futures = filter_future(schedules, reference=reference)
        assert len(futures) == 1
        assert futures == schedules[1]
