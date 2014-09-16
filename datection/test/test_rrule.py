# -*- coding: utf-8 -*-

"""
Test the generation of recurrence rules during the normalisation process
of a timepoint
"""

import unittest
import datetime

from dateutil.rrule import rrulestr

from datection import parse


class TestDateRecurrence(unittest.TestCase):

    """ Test the generation of recurrence rules for datection Date objects """

    def setUp(self):
        lang = 'fr'
        text = u"Le 25 janvier 2013"
        self.date = parse(text, lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        target = 'DTSTART:20130125\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=0'
        self.assertEqual(self.date.rrulestr, target)

    def test_export(self):
        """ Test the format returned by the 'export' Date method """
        target = {
            'rrule': self.date.rrulestr,
            'duration': 1439,
            'span': (3, 18)
        }
        self.assertEqual(self.date.export(), target)

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
        text = u"Le 25, 26 janvier 2013"
        self.datelist = parse(text, lang)[0]

    def test_export(self):
        """Test the format returned by the 'export' DateList method."""
        target = [
            {
                'rrule': self.datelist.dates[0].rrulestr,
                'duration': 1439,
                'span': (3, 22)
            },
            {
                'rrule': self.datelist.dates[1].rrulestr,
                'duration': 1439,
                'span': (3, 22)
            }
        ]
        self.assertEqual(self.datelist.export(), target)

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
        self.text = u"du 25 au 30 mars 2013"
        self.interval = parse(self.text, lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        target = ('DTSTART:20130325\nRRULE:FREQ=DAILY;BYHOUR=0;'
                  'BYMINUTE=0;INTERVAL=1;UNTIL=20130330')
        self.assertEqual(self.interval.rrulestr, target)

    def test_export(self):
        """ Test the format returned by the 'export' Date method """
        target = {
            'rrule': self.interval.rrulestr,
            'duration': 1439,
            'span': (0, 21)
        }
        self.assertEqual(self.interval.export(), target)

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
        self.text = u"Le 30 mars 2013 à 15h30"
        self.datetime = parse(self.text, self.lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        target = ('DTSTART:20130330\nRRULE:FREQ=DAILY;COUNT=1;'
                  'BYMINUTE=30;BYHOUR=15')
        self.assertEqual(self.datetime.rrulestr, target)

    def test_export(self):
        """ Test the format returned by the 'export' Date method """
        target = {
            'rrule': self.datetime.rrulestr,
            'duration': 0,
            'span': (3, 23)
        }
        self.assertEqual(self.datetime.export(), target)

    def test_datetime_generation(self):
        """ Test the format the dates generated by the recurrence rule """
        target = [datetime.datetime(2013, 3, 30, 15, 30)]
        self.assertEqual(list(rrulestr(self.datetime.rrulestr)), target)

    def test_to_rrule_with_endtime(self):
        """ Test the format of the recurrence rule string when the
            datetime specified an end time.

        """
        text = u"Le 30 mars 2013 de 12h à 15h30"
        dt = parse(text, self.lang)[0]
        target = ('DTSTART:20130330\nRRULE:FREQ=DAILY;COUNT=1;'
                  'BYMINUTE=0;BYHOUR=12')
        self.assertEqual(dt.rrulestr, target)

    def test_export_with_endtime(self):
        """ Test the format returned by the 'export' Date method """
        text = u"Le 30 mars 2013 de 12h à 15h30"
        dt = parse(text, self.lang)[0]
        target = {
            'rrule': dt.rrulestr,
            'duration': 210,
            'span': (3, 30)
        }
        self.assertEqual(dt.export(), target)

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
        text = u"du 25 au 30 mars 2013 de 15h à 16h"
        self.interval = parse(text, self.lang)[0]

    def test_to_rrule(self):
        """ Test the format of the recurrence rule string """
        _rrulestr = self.interval.rrulestr
        target = ('DTSTART:20130325\nRRULE:FREQ=DAILY;BYHOUR=15;'
                  'BYMINUTE=0;INTERVAL=1;UNTIL=20130330T235959')
        self.assertEqual(_rrulestr, target)

    def test_export(self):
        """ Test the format returned by the 'export' Date method """
        target = {
            'rrule': self.interval.rrulestr,
            'duration': 60,
            'span': (0, 34)
        }
        self.assertEqual(self.interval.export(), target)

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
        text = u"du 25 au 30 mars 2013 à 15h"
        interval = parse(text, self.lang)[0]
        target = ('DTSTART:20130325\nRRULE:FREQ=DAILY;BYHOUR=15;'
                  'BYMINUTE=0;INTERVAL=1;UNTIL=20130330T235959')
        self.assertEqual(interval.rrulestr, target)

    def test_export_no_endtime(self):
        """ Test the format returned by the 'export' Date method """
        text = u"du 25 au 30 mars 2013 à 15h"
        interval = parse(text, self.lang)[0]
        target = {
            'rrule': interval.rrulestr,
            'duration': 0,
            'span': (0, 27)
        }
        self.assertEqual(interval.export(), target)

    def test_datetime_generation_no_endtime(self):
        """ Test the format the dates generated by the recurrence rule """
        text = u"du 25 au 30 mars 2013 à 15h"
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
        text_nodatetime = u'le lundi'
        text_notime = u'le lundi, du 1 au 15 mars 2013'
        text_full = u'le lundi du 1er au 15 mars 2013, de 5h à 7h'
        self.rec_nodatetime = parse(text_nodatetime, lang)[0]
        self.rec_notime = parse(text_notime, lang)[0]
        self.rec_full = parse(text_full, lang)[0]

    def test_export_no_datetime(self):
        """ Test the format returned by the 'export' WeekdayRecurrence method
             when no start/end datetime is specified

        """
        target = {
            'rrule': self.rec_nodatetime.rrulestr,
            'duration': 1439,
            'span': (0, 8),
            'unlimited': True
        }
        self.assertEqual(self.rec_nodatetime.export(), target)

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
                  'UNTIL=20130315T235959')
        self.assertEqual(rrulestr, target)

    def test_export_no_time(self):
        """ Test the format returned by the 'export' WeekdayRecurrence method
             when no start/end time is specified

        """
        target = {
            'rrule': self.rec_notime.rrulestr,
            'duration': 1439,
            'span': (0, 30)
        }
        self.assertEqual(self.rec_notime.export(), target)

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
                  'BYHOUR=5;BYMINUTE=0;UNTIL=20130315T235959')
        self.assertEqual(rrulestr, target)

    def test_export_fulldata(self):
        """ Test the format returned by the 'export' WeekdayRecurrence method

        """
        target = {
            'rrule': self.rec_full.rrulestr,
            'duration': 120,
            'span': (0, 43),
        }
        self.assertDictEqual(self.rec_full.export(), target)

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
        text = u"les lundis, mardis et mercredis"
        wkrec = parse(text, "fr")[0]
        self.assertEqual(wkrec.weekdays, [0, 1, 2])


class TestWeekdayIntervalRecurrence(unittest.TestCase):

    def test_weekdays_list(self):
        rec = parse(u"du lundi au mercredi", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 3))

        rec = parse(u"du lundi au dimanche", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))

        rec = parse(u"du vendredi au lundi", "fr")[0]
        self.assertEqual(rec.weekdays, [4, 5, 6, 0])


class TestAllDayWeekdayRecurrence(unittest.TestCase):

    def test_allweekdays_date(self):
        rec = parse(u"tous les jours, du 5 au 15 mars 2013", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))
        self.assertEqual(rec.start_date, datetime.date(2013, 3, 5))
        self.assertEqual(rec.end_date, datetime.date(2013, 3, 15))
        self.assertEqual(rec.start_time, datetime.time(0, 0))
        self.assertEqual(rec.end_time, datetime.time(23, 59, 59))

    def test_allweekdays_time(self):
        rec = parse(u"tous les jours, de 4h à 8h", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))
        self.assertEqual(rec.start_date, datetime.date.today())
        self.assertEqual(rec.start_time, datetime.time(4, 0, 0))
        self.assertIsNone(rec.end_date)
        self.assertEqual(rec.end_time, datetime.time(8, 0, 0))

    def test_allweekdays_datetime(self):
        rec = parse(
            u"tous les jours, du 5 au 15 mars 2013, de 4h à 8h", "fr")[0]
        self.assertEqual(rec.weekdays, range(0, 7))
        self.assertEqual(rec.start_date, datetime.date(2013, 3, 5))
        self.assertEqual(rec.end_date, datetime.date(2013, 3, 15))
        self.assertEqual(rec.start_time, datetime.time(4, 0))
        self.assertEqual(rec.end_time, datetime.time(8, 0))
