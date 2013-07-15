# -*- coding: utf-8 -*-

"""
Test the generation of recurrence rules during the normalisation process
of a timepoint
"""

import unittest
import datetime

from dateutil.rrule import *

from datection import parse
from datection.normalize import *


class TestDateRecurrence(unittest.TestCase):
    """ Test the generation of recurrence rules for datection Date objects """

    def setUp(self):
        lang = 'fr'
        text = "Le 25 janvier 2013"
        self.date = parse(text, lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        rrulestr = self.date.rrulestr
        target = 'DTSTART:20130125\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'
        self.assertEqual(rrulestr, target)

    def test_to_db(self):
        """ Test the format returned by the 'to_db' Date method """
        target = {
            'rrule': self.date.rrulestr,
            'duration': 1439
        }
        self.assertEqual(self.date.to_db(), target)

    def test_datetime_generation(self):
        """ Test the format the dates generated by the recurrence rule """
        target = [datetime.datetime(2013, 1, 25, 0, 0)]
        self.assertEqual(list(rrulestr(self.date.rrulestr)), target)

    def test_future(self):
        self.assertFalse(self.date.future())
        self.assertTrue(self.date.future(reference=datetime.date(2012, 1, 1)))


class TestDateListRecurrence(unittest.TestCase):
    """ Test the generation of recurrence rules for datection DateList objects

    """
    def setUp(self):
        lang = 'fr'
        text = "Le 25, 26 janvier 2013"
        self.datelist = parse(text, lang)[0]

    def test_to_db(self):
        """ Test the format returned by the 'to_db' DateList method """
        target = [
            {
                'rrule': self.datelist.dates[0].rrulestr,
                'duration': 1439
            },
            {
                'rrule': self.datelist.dates[1].rrulestr,
                'duration': 1439
            }
        ]
        self.assertEqual(self.datelist.to_db(), target)

    def test_future(self):
        self.assertFalse(self.datelist.future())
        self.assertTrue(
            self.datelist.future(reference=datetime.date(2012, 1, 1)))


class TestDateIntervalRecurrence(unittest.TestCase):
    """ Test the generation of recurrence rules for datection
        DateInterval objects

    """
    def setUp(self):
        lang = 'fr'
        text = "du 25 au 30 mars 2013"
        self.interval = parse(text, lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        rrulestr = self.interval.rrulestr
        target = ('DTSTART:20130325\nRRULE:FREQ=DAILY;BYHOUR=0;'
            'BYMINUTE=0;INTERVAL=1;UNTIL=20130330')
        self.assertEqual(rrulestr, target)

    def test_to_db(self):
        """ Test the format returned by the 'to_db' Date method """
        target = {
            'rrule': self.interval.rrulestr,
            'duration': 1439
        }
        self.assertEqual(self.interval.to_db(), target)

    def test_datetime_generation(self):
        """ Test the format the dates generated by the recurrence rule """
        target = [
            datetime.datetime(2013, 3, 25, 0, 0, 0),
            datetime.datetime(2013, 3, 26, 0, 0, 0),
            datetime.datetime(2013, 3, 27, 0, 0, 0),
            datetime.datetime(2013, 3, 28, 0, 0, 0),
            datetime.datetime(2013, 3, 29, 0, 0, 0),
            datetime.datetime(2013, 3, 30, 0, 0, 0),
        ]
        self.assertEqual(list(rrulestr(self.interval.rrulestr)), target)

    def test_future(self):
        self.assertFalse(self.interval.future())
        self.assertTrue(
            self.interval.future(reference=datetime.date(2012, 1, 1)))


class TestDateTimeRecurrence(unittest.TestCase):
    """ Test the generation of recurrence rules for datection
        DateTime objects

    """
    def setUp(self):
        self.lang = 'fr'
        text = "Le 30 mars 2013 à 15h30"
        self.datetime = parse(text, self.lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        rrulestr = self.datetime.rrulestr
        target = ('DTSTART:20130330\nRRULE:FREQ=DAILY;COUNT=1;'
            'BYMINUTE=30;BYHOUR=15')
        self.assertEqual(rrulestr, target)

    def test_to_db(self):
        """ Test the format returned by the 'to_db' Date method """
        target = {
            'rrule': self.datetime.rrulestr,
            'duration': 0
        }
        self.assertEqual(self.datetime.to_db(), target)

    def test_datetime_generation(self):
        """ Test the format the dates generated by the recurrence rule """
        target = [datetime.datetime(2013, 3, 30, 15, 30)]
        self.assertEqual(list(rrulestr(self.datetime.rrulestr)), target)

    def test_to_rrule_with_endtime(self):
        """ Test the format of the recurrence rule string when the
            datetime specified an end time.

        """
        text = "Le 30 mars 2013 de 12h à 15h30"
        dt = parse(text, self.lang)[0]
        target = ('DTSTART:20130330\nRRULE:FREQ=DAILY;COUNT=1;'
            'BYMINUTE=0;BYHOUR=12')
        self.assertEqual(dt.rrulestr, target)

    def test_to_db_with_endtime(self):
        """ Test the format returned by the 'to_db' Date method """
        text = "Le 30 mars 2013 de 12h à 15h30"
        dt = parse(text, self.lang)[0]
        target = {
            'rrule': dt.rrulestr,
            'duration': 210
        }
        self.assertEqual(dt.to_db(), target)

    def test_future(self):
        self.assertFalse(self.datetime.future())
        self.assertTrue(
            self.datetime.future(reference=datetime.date(2012, 1, 1)))


class TestDateTimeIntervalRecurrence(unittest.TestCase):
    """ Test the generation of recurrence rules for datection
        DateInterval objects

    """
    def setUp(self):
        self.lang = 'fr'
        text = "du 25 au 30 mars 2013 de 15h à 16h"
        self.interval = parse(text, self.lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        rrulestr = self.interval.rrulestr
        target = ('DTSTART:20130325\nRRULE:FREQ=DAILY;BYHOUR=15;'
            'BYMINUTE=0;INTERVAL=1;UNTIL=20130330T235959')
        self.assertEqual(rrulestr, target)

    def test_to_db(self):
        """ Test the format returned by the 'to_db' Date method """
        target = {
            'rrule': self.interval.rrulestr,
            'duration': 60
        }
        self.assertEqual(self.interval.to_db(), target)

    def test_datetime_generation(self):
        """ Test the format the dates generated by the recurrence rule """
        target = [
            datetime.datetime(2013, 3, 25, 15, 0, 0),
            datetime.datetime(2013, 3, 26, 15, 0, 0),
            datetime.datetime(2013, 3, 27, 15, 0, 0),
            datetime.datetime(2013, 3, 28, 15, 0, 0),
            datetime.datetime(2013, 3, 29, 15, 0, 0),
            datetime.datetime(2013, 3, 30, 15, 0, 0),
        ]
        self.assertEqual(list(rrulestr(self.interval.rrulestr)), target)

    def test_to_rrule_no_endtime(self):
        """ Test the format of the recurrence rule string """
        text = "du 25 au 30 mars 2013 à 15h"
        interval = parse(text, self.lang)[0]
        rrulestr = interval.rrulestr
        target = ('DTSTART:20130325\nRRULE:FREQ=DAILY;BYHOUR=15;'
            'BYMINUTE=0;INTERVAL=1;UNTIL=20130330T235959')
        self.assertEqual(rrulestr, target)

    def test_to_db_no_endtime(self):
        """ Test the format returned by the 'to_db' Date method """
        text = "du 25 au 30 mars 2013 à 15h"
        interval = parse(text, self.lang)[0]
        target = {
            'rrule': interval.rrulestr,
            'duration': 0
        }
        self.assertEqual(interval.to_db(), target)

    def test_datetime_generation_no_endtime(self):
        """ Test the format the dates generated by the recurrence rule """
        text = "du 25 au 30 mars 2013 à 15h"
        interval = parse(text, self.lang)[0]
        target = [
            datetime.datetime(2013, 3, 25, 15, 0, 0),
            datetime.datetime(2013, 3, 26, 15, 0, 0),
            datetime.datetime(2013, 3, 27, 15, 0, 0),
            datetime.datetime(2013, 3, 28, 15, 0, 0),
            datetime.datetime(2013, 3, 29, 15, 0, 0),
            datetime.datetime(2013, 3, 30, 15, 0, 0),
        ]
        self.assertEqual(list(rrulestr(interval.rrulestr)), target)

    def test_future(self):
        self.assertFalse(self.interval.future())
        self.assertTrue(
            self.interval.future(reference=datetime.date(2012, 1, 1)))


class TestWeekdayRecurrence(unittest.TestCase):
    """ Test the generation of recurrence rules for datection
        WeekdayRecurrence objects

    """
    def setUp(self):
        lang = 'fr'
        text_nodatetime = 'le lundi'
        text_notime = 'le lundi, du 1 au 15 mars 2013'
        text_full = 'le lundi du 1er au 15 mars 2013, de 5h à 7h'
        self.rec_nodatetime = parse(text_nodatetime, lang)[0]
        self.rec_notime = parse(text_notime, lang)[0]
        self.rec_full = parse(text_full, lang)[0]

    def test_to_db_no_datetime(self):
        """ Test the format returned by the 'to_db' WeekdayRecurrence method
             when no start/end datetime is specified

        """
        target = {
            'rrule': self.rec_nodatetime.rrulestr,
            'duration': 0
        }
        self.assertEqual(self.rec_nodatetime.to_db(), target)

    def test_datetime_generation_no_datetime(self):
        """ Test the number the dates generated by the recurrence rule
            when no start/end datetime is specified

        """
        self.assertIn(
            len(list(rrulestr(self.rec_nodatetime.rrulestr))),
            range(52, 53+1))

    def test_future_no_datetime(self):
        self.assertTrue(self.rec_nodatetime.future())
        self.assertTrue(
            self.rec_nodatetime.future(reference=datetime.date(2012, 1, 1)))

    def test_rrulestr_no_time(self):
        """ Test the format of the sstrrule when no start/end time is
            specified

        """
        rrulestr = self.rec_notime.rrulestr
        target = ('DTSTART:20130301\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
            'UNTIL=20130315')
        self.assertEqual(rrulestr, target)

    def test_to_db_no_time(self):
        """ Test the format returned by the 'to_db' WeekdayRecurrence method
             when no start/end time is specified

        """
        target = {
            'rrule': self.rec_notime.rrulestr,
            'duration': 1439
        }
        self.assertEqual(self.rec_notime.to_db(), target)

    def test_datetime_generation_no_time(self):
        """ Test the format of the dates generated by the recurrence rule
            when no start/end time is specified

        """
        target = [
            datetime.datetime(2013, 3, 4, 0, 0),
            datetime.datetime(2013, 3, 11, 0, 0),
        ]
        self.assertEqual(list(rrulestr(self.rec_notime.rrulestr)), target)

    def test_future_no_time(self):
        self.assertFalse(self.rec_notime.future())
        self.assertTrue(
            self.rec_notime.future(reference=datetime.date(2012, 1, 1)))

    def test_rrulestr_fulldata(self):
        """ Test the format of the sstrrule """
        rrulestr = self.rec_full.rrulestr
        target = ('DTSTART:20130301\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
            'BYHOUR=5;BYMINUTE=0;UNTIL=20130315')
        self.assertEqual(rrulestr, target)

    def test_to_db_fulldata(self):
        """ Test the format returned by the 'to_db' WeekdayRecurrence method

        """
        target = {
            'rrule': self.rec_full.rrulestr,
            'duration': 120
        }
        self.assertEqual(self.rec_full.to_db(), target)

    def test_datetime_generation_fulldata(self):
        """ Test the format of the dates generated by the recurrence rule

        """
        target = [
            datetime.datetime(2013, 3, 4, 5, 0),
            datetime.datetime(2013, 3, 11, 5, 0),
        ]
        self.assertEqual(list(rrulestr(self.rec_full.rrulestr)), target)

    def test_future_fulldata(self):
        self.assertFalse(self.rec_full.future())
        self.assertTrue(
            self.rec_full.future(reference=datetime.date(2012, 1, 1)))

    def test_plural_weekdays(self):
        text = "les lundis, mardis et mercredis"
        wkrec = parse(text, "fr")[0]
        self.assertEqual(wkrec.weekdays, [0, 1, 2])


class TestWeekdayIntervalRecurrence(unittest.TestCase):

    def test_weekdays_list(self):
        rec = parse("du lundi au mercredi", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 3))

        rec = parse("du lundi au dimanche", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))

        rec = parse("du vendredi au lundi", "fr")[0]
        self.assertEqual(rec.weekdays, [4, 5, 6, 0])


class TestAllDayWeekdayRecurrence(unittest.TestCase):

    def test_allweekdays_date(self):
        rec = parse("tous les jours, du 5 au 15 mars 2013", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))
        self.assertEqual(
            rec.start_datetime, datetime.datetime(2013, 03, 5, 0, 0, 0))
        self.assertEqual(
            rec.end_datetime, datetime.datetime(2013, 03, 15, 23, 59, 59))

    def test_allweekdays_time(self):
        rec = parse("tous les jours, de 4h à 8h", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))
        self.assertEqual(
            rec.start_datetime,
            datetime.datetime.combine(
                datetime.date.today(),
                datetime.time(4, 0, 0)))
        self.assertEqual(
            rec.end_datetime,
            datetime.datetime.combine(
                datetime.date.today() + datetime.timedelta(days=365),
                datetime.time(8, 0, 0)))

    def test_allweekdays_datetime(self):
        rec = parse(
            "tous les jours, du 5 au 15 mars 2013, de 4h à 8h", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))
        self.assertEqual(
            rec.start_datetime, datetime.datetime(2013, 03, 5, 4, 0, 0))
        self.assertEqual(
            rec.end_datetime, datetime.datetime(2013, 03, 15, 8, 0, 0))