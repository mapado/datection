import unittest
import mock
import datetime


class GetCurrentDayMocker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.get_current_date_patch = mock.patch(
            'datection.rendering.utils.get_current_date')
        cls.get_current_date_mock = cls.get_current_date_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.get_current_date_patch.stop()

    def setUp(self):
        self.set_current_date(datetime.date(2012, 1, 1))

    def set_current_date(self, date):
        self.get_current_date_mock.return_value = date
