# -*- coding: utf-8 -*-

import unittest

from ..merge import _merge_date_bounds, _merge_weekdays, merge
from ..parse import parse


class MergeScheduleTest(unittest.TestCase):

    def test_merge_weekdays(self):
        reccurences = [
            parse(u'le lundi', 'fr')[0],
            parse(u'le lundi de 8h à 9h', 'fr')[0],
        ]
        self.assertEqual(len(_merge_weekdays(reccurences)), 1)

        merged = _merge_weekdays(reccurences)[0]
        output = merged.to_db()
        self.assertIn(
            'RRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0;',
            output['rrule'])
        self.assertEqual(output['duration'], 60)

    def test_merge_weekdays_different_start_end_bounds(self):
        reccurences = [
            parse(u'le lundi de 8h à 10h', 'fr')[0],
            parse(u'le lundi de 8h à 9h', 'fr')[0],
        ]
        self.assertEqual(_merge_weekdays(reccurences), reccurences)

    def test_merge_date_bounds(self):
        bounds = parse("du 5 au 28 mars 2013, de 5h à 8h", "fr")[0]
        weekday_recurrences = parse("tous les lundis", "fr")
        merged = _merge_date_bounds(bounds, weekday_recurrences)[0]

        rrule = merged.to_db()['rrule']
        duration = merged.to_db()['duration']
        self.assertEqual(rrule, ('DTSTART:20130305\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                                 'BYHOUR=5;BYMINUTE=0;UNTIL=20130328T235959'))
        self.assertEqual(duration, 180)

    def test_merge_time_bounds(self):
        bounds = parse("du 5 au 28 mars 2013", "fr")[0]
        weekday_recurrences = parse("tous les lundis, de 5h à 8h", "fr")
        merged = _merge_date_bounds(bounds, weekday_recurrences)[0]

        rrule = merged.to_db()['rrule']
        duration = merged.to_db()['duration']
        self.assertEqual(rrule, ('DTSTART:20130305\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                                 'BYHOUR=5;BYMINUTE=0;UNTIL=20130328T235959'))
        self.assertEqual(duration, 180)

    @unittest.skip("Corner case not yet handled")
    def test_merge_bounds_no_time(self):
        bounds = parse("du 5 au 28 mars 2013", "fr")[0]
        weekday_recurrences = parse("tous les lundis", "fr")
        merged = _merge_date_bounds(bounds, weekday_recurrences)[0]

        rrule = merged.to_db()['rrule']
        duration = merged.to_db()['duration']
        self.assertEqual(rrule, ('DTSTART:20130305\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                                 'UNTIL=20130328T235959'))
        self.assertEqual(duration, 1439)

    def test_merge(self):
        recurrences = [
            parse(u'le lundi', 'fr')[0],
            parse(u'le lundi de 8h à 9h', 'fr')[0]
        ]
        bounds = parse(u'du 5 au 25 mars 2012', 'fr')
        merged = merge(recurrences + bounds)
        self.assertEqual(len(merged), 1)
        expected = {
            'duration': 60,
            'rrule': ('DTSTART:20120305\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                      'BYHOUR=8;BYMINUTE=0;UNTIL=20120325T235959')
        }
        self.assertEqual(merged[0].to_db(), expected)
