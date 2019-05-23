# -*- coding: utf-8 -*-

"""Test the datection.display function"""

import datection
import datetime
import locale

from datection.render import display
from datection.render import NextOccurenceFormatter
from datection.render import FullFormatter
from datection.test import GetCurrentDayMocker


class TestDisplay(GetCurrentDayMocker):

    """Test the datection.display function."""

    def setUp(self):
        self.locale = 'fr_FR.UTF8'
        locale.setlocale(locale.LC_TIME, self.locale)
        super(TestDisplay, self).setUp()

    def assertDisplayEqual(self, text, result, lang='fr'):
        """Converts the argument text to a list of duration/rrule dicts,
        render them in the argument language, and check that the result
        is the same than the argument result.

        """
        sch = datection.export(text, lang, only_future=False)
        fmt = datection.display(sch, lang)
        self.assertEqual(fmt, result)

    def test_past_date(self):
        self.assertDisplayEqual(
            u'12/06/2013 Période Ouverture 2013', u'Le mercredi 12 juin 2013')

    def test_past_date_interval(self):
        self.assertDisplayEqual(
            u"Du 01/01/2013 au 31/12/2013 Périodes d'ouvertures 2013",
            u'Du mardi 1er janvier au mardi 31 décembre 2013')

    def test_ignore_duplicates(self):
        sch = [
            {
                'rrule': ('DTSTART:20140303\nRRULE:FREQ=DAILY;'
                          'UNTIL=20150303T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=0'),
                'duration': '1439'
            }]
        dup_sch = [sch[0]] * 2
        self.assertEqual(
            datection.display(sch, 'fr'),
            datection.display(dup_sch, 'fr'))

    def test_display_shortest(self):
        schedule = [
            {'duration': 1439,
             'rrule': ('DTSTART:20131215\nRRULE:FREQ=DAILY;COUNT=1;'
                       'BYMINUTE=0;BYHOUR=0'),
             'span': (3, 25)},
            {'duration': 1439,
             'rrule': ('DTSTART:20131216\nRRULE:FREQ=DAILY;COUNT=1;'
                       'BYMINUTE=0;BYHOUR=0'),
             'span': (3, 25)}
        ]
        start = datetime.datetime(2013, 12, 10)
        end = datetime.datetime(2013, 12, 17)
        reference = start
        short = NextOccurenceFormatter(schedule, start, end).display(
            reference, summarize=True, abbrev_dayname=True)
        default = FullFormatter(schedule).display(abbrev_monthname=True)
        shortest_fmt = display(
            schedule,
            self.locale,
            short=True,
            seo=False,
            bounds=(start, end),
            reference=reference)
        self.assertGreater(len(default), len(short))
        self.assertEqual(short,   u'Ce dim. + autres dates')
        self.assertEqual(default, u'Les dimanche 15 et lundi 16 déc. 2013')

    def test_display_recurrence(self):
        schedule = [
            {'duration': 60,
             'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                       'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959'),
             'span': (0, 48)}]
        start = datetime.datetime(2015, 3, 1)
        end = datetime.datetime(2015, 3, 17)
        reference = datetime.datetime(2015, 3, 1)
        short = NextOccurenceFormatter(schedule, start, end).display(
            reference, summarize=True)
        default = FullFormatter(schedule).display(abbrev_monthname=True)
        shortest_fmt = display(
            schedule,
            self.locale,
            short=True,
            seo=False,
            bounds=(start, end),
            reference=reference)
        self.assertGreater(len(default), len(short))
        self.assertEqual(
            default, u'Le mardi, du 5 au 26 mars 2015, de 8 h à 9 h')
        self.assertEqual(
            shortest_fmt, u'Le mardi, du 5 au 26 mars 2015, de 8 h à 9 h')

    def test_display_long_recurrence(self):
        schedule = [
            {'duration': 60,
             'rrule': ('DTSTART:20150301\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                       'BYHOUR=8;BYMINUTE=0;UNTIL=20150330T235959'),
             'span': (0, 48)}]
        start = datetime.datetime(2015, 3, 1)
        end = datetime.datetime(2015, 8, 17)
        shortest_fmt = display(
            schedule,
            self.locale,
            short=True,
            seo=False,
            bounds=(start, end),
            reference=None)
        self.assertEqual(
            shortest_fmt, u'Lun. 2 mars 2015 de 8 h à 9 h + autres dates')

    def test_display_weekday_recurrence(self):
        sch = datection.export(u"Le samedi", "fr")
        self.assertEqual(display(sch, self.locale), u'Le samedi')

    def test_display_weekday_recurrence_time(self):
        sch = datection.export(u"Le samedi à 15h30", "fr")
        self.assertEqual(display(sch, self.locale), u'Le samedi, à 15 h 30')

    def test_display_weekday_recurrence_time_interval(self):
        sch = datection.export(u"Le samedi de 12 h 00 à 15h30", "fr")
        self.assertEqual(
            display(sch, self.locale), u'Le samedi, de 12 h à 15 h 30')

    def test_display_weekday_recurrence_list(self):
        sch = datection.export(u"Le lundi et samedi", "fr")
        self.assertEqual(display(sch, self.locale), u'Le lundi et samedi')

    def test_display_weekday_recurrence_list_time(self):
        sch = datection.export(u"Le lundi et samedi à 15h30", "fr")
        self.assertEqual(
            display(sch, self.locale), u'Le lundi et samedi, à 15 h 30')

    def test_display_weekday_recurrence_list_time_interval(self):
        sch = datection.export(u"Le lundi et mardi de 14 h à 16 h 30", "fr")
        self.assertEqual(
            display(sch, self.locale), u'Le lundi et mardi, de 14 h à 16 h 30')

    def test_display_weekday_recurrence_interval(self):
        sch = datection.export(u"Du samedi au dimanche", "fr")
        self.assertEqual(display(sch, self.locale), u'Le samedi et dimanche')

    def test_display_date(self):
        sch = datection.export(u"Le 15 mars 2013", "fr", only_future=False)
        self.assertEqual(display(sch, self.locale), u'Le vendredi 15 mars 2013')

    def test_display_date_interval(self):
        sch = datection.export(
            u"Le 15 mars 2013 PLOP PLOP 16 mars 2013", "fr", only_future=False)
        self.assertEqual(display(sch, self.locale), u'Les vendredi 15 et samedi 16 mars 2013')

    def test_display_date_list(self):
        sch = datection.export(
            u"Le 15 mars 2013 PLOP PLOP 18 mars 2013", "fr", only_future=False)
        self.assertEqual(display(sch, self.locale), u'Les vendredi 15 et lundi 18 mars 2013')
        sch = datection.export(
            u"15/03/2015 hhhh 16/03/2015 hhh 18/03/2015",
            "fr", only_future=False)
        self.assertEqual(
            display(sch, self.locale), u'Les 15, 16 et 18 mars 2015')

    def test_display_datetime(self):
        sch = datection.export(
            u"Le 15 mars 2013 à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, self.locale), u'Le vendredi 15 mars 2013 à 18 h 30')

    def test_display_datetime_interval(self):
        sch = datection.export(
            u"Le 15 mars 2013 de 16 h à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, self.locale), u'Le vendredi 15 mars 2013 de 16 h à 18 h 30')

    def test_display_datetime_list(self):
        sch = datection.export(
            u"Le 15 et 18 mars 2013 à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, self.locale), u'Les vendredi 15 et lundi 18 mars 2013 à 18 h 30')

    def test_display_datetime_list_time_interval(self):
        sch = datection.export(
            u"Le 15 & 18 mars 2013 de 16 h à 18h30", "fr", only_future=False)
        self.assertEqual(
            display(sch, self.locale),
            u'Les vendredi 15 et lundi 18 mars 2013 de 16 h à 18 h 30')

    def test_display_grouped_time(self):
        sch = [{
            'rrule': ('DTSTART:20140303\nRRULE:FREQ=DAILY;'
                      'COUNT=1;BYMINUTE=30;BYHOUR=10'),
            'duration': '30'
        }, {
            'rrule': ('DTSTART:20140303\nRRULE:FREQ=DAILY;'
                      'COUNT=1;BYMINUTE=30;BYHOUR=13'),
            'duration': '30'
        }, {
            'rrule': ('DTSTART:20140303\nRRULE:FREQ=DAILY;'
                      'COUNT=1;BYMINUTE=30;BYHOUR=12'),
            'duration': '30'
        }]
        self.assertEqual(
            datection.display(sch, 'fr'),
            u'Le lundi 3 mars 2014 de 10 h 30 à 11 h,'
            u' de 12 h 30 à 13 h et de 13 h 30 à 14 h'
        )

    def test_display_grouped_time_with_dateinterval(self):
        sch = [{
            'rrule': ('DTSTART:20140303\nRRULE:FREQ=DAILY;'
                      'UNTIL=20140304T235959;INTERVAL=1;'
                      'BYMINUTE=30;BYHOUR=10'),
            'duration': '30'
        }, {
            'rrule': ('DTSTART:20140303\nRRULE:FREQ=DAILY;'
                      'UNTIL=20140304T235959;INTERVAL=1;'
                      'BYMINUTE=30;BYHOUR=13'),
            'duration': '30'
        }, {
            'rrule': ('DTSTART:20140303\nRRULE:FREQ=DAILY;'
                      'UNTIL=20140304T235959;INTERVAL=1;'
                      'BYMINUTE=30;BYHOUR=12'),
            'duration': '30'
        }]
        self.assertEqual(
            datection.display(sch, 'fr'),
            u'Les lundi 3 et mardi 4 mars 2014 de 10 h 30 à 11 h,'
            u' de 12 h 30 à 13 h et de 13 h 30 à 14 h'
        )

    def test_avoid_display_day_plus_precise_date(self):
        sch = [{
            'duration': 0,
            'rrule': ('DTSTART:20150703\nRRULE:FREQ=DAILY;'
                      'COUNT=1;INTERVAL=1;BYMINUTE=30;'
                      'BYHOUR=19;BYDAY=FR;WKST=MO')
        }]
        date_fmt = datection.display(sch, 'fr')
        self.assertEqual(
            date_fmt,
            u'Le vendredi 3 juillet 2015 à 19 h 30'
        )

    def test_short_absolute_date(self):
        sch = [{
            u'duration': 0,
            u'rrule': u'DTSTART:20140227'
                '\nRRULE:FREQ=DAILY;COUNT=1;BYMINUTE=0;BYHOUR=21',
        }]
        date_fmt = datection.display(sch, 'fr', short=True, reference=None)
        self.assertEqual(
            date_fmt,
            u'Jeu. 27 févr. 2014 à 21 h'
        )

    def test_short_absolute_sequence_date(self):
        sch = [{
            u'duration': '0',
            u'rrule': ('DTSTART:20140227\nRRULE:FREQ=DAILY;'
                        'UNTIL=20140228T235959;INTERVAL=1;'
                        'BYMINUTE=0;BYHOUR=21'),
        }]

        date_fmt = datection.display(sch, 'fr', short=True, reference=None)
        self.assertEqual(
            date_fmt,
            u'27 et 28 févr. 2014 à 21 h'
        )

    def test_short_absolute_long_sequence_date(self):
        sch = [{
            u'duration': '0',
            u'rrule': ('DTSTART:20140227\nRRULE:FREQ=DAILY;'
                        'UNTIL=20140303T235959;INTERVAL=1;'
                        'BYMINUTE=0;BYHOUR=21'),
        }]

        date_fmt = datection.display(sch, 'fr', short=True, reference=None)
        self.assertEqual(
            date_fmt,
            u'Du 27 févr. au 3 mars 2014 à 21 h'
        )
