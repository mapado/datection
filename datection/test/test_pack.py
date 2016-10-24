# -*- coding: utf-8 -*-

""" Functional tests on datection.pack """

import unittest

from datection.models import DurationRRule
from datection import pack


class TestPack(unittest.TestCase):

    def assertPackEqual(self, rrules, result):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        result_drr = DurationRRule(result)
        packer = pack.RrulePacker(drrs)
        packed = packer.pack_rrules()
        self.assertEqual(len(packed), 1)
        self.assertEqual(packed[0], result_drr)

    def assertNotPack(self, rrules):
        drrs = [DurationRRule(rrule) for rrule in rrules]
        packer = pack.RrulePacker(drrs)
        packed = packer.pack_rrules()
        self.assertItemsEqual(drrs, packed)

    def test_include_sing_in_cont(self):        
        single = {'duration': 30,
                  'rrule': ('DTSTART:20161018\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30,
                'continuous': True}
        self.assertPackEqual([single, cont], cont)

    def test_not_include_sing_in_cont(self):       
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30,
                  'continuous': True}
        
        single_date = {'duration': 30,
                       'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_date])        
        
        single_hour = {'duration': 30,
                       'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_hour])
        
        single_minu = {'duration': 30,
                       'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=8;BYHOUR=3')}
        self.assertNotPack([cont, single_minu])
        
        single_dura = {'duration': 5,
                       'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_dura])

    def test_include_sing_in_wrec(self):        
        single = {'duration': 60,
                  'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                            'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        self.assertPackEqual([single, weekly], weekly)
        
        weekly_2 = {'duration': 60,
                    'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                              'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        self.assertPackEqual([single, weekly_2], weekly_2)

    def test_not_include_sing_in_wrec(self):
        
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}  

        single_hour = {'duration': 60,
                        'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                                  'COUNT=1;BYMINUTE=0;BYHOUR=9')}
        self.assertNotPack([weekly, single_hour]) 

        single_minu = {'duration': 60,
                        'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                                  'COUNT=1;BYMINUTE=1;BYHOUR=8')} 
        self.assertNotPack([weekly, single_minu]) 

        single_day = {'duration': 60,
                      'rrule': ('DTSTART:20150318\nRRULE:FREQ=DAILY;'
                                'COUNT=1;BYMINUTE=0;BYHOUR=8')} 
        self.assertNotPack([weekly, single_day]) 

        single_dura = {'duration': 90,
                        'rrule': ('DTSTART:20150317\nRRULE:FREQ=DAILY;'
                                  'COUNT=1;BYMINUTE=0;BYHOUR=8')} 
        self.assertNotPack([weekly, single_dura]) 

    def test_extend_cont_with_sing(self):
        single_before = {'duration': 30,
                         'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        single_after = {'duration': 30,
                        'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                                  'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30,
                'continuous': True}
        
        result = {'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161024T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30}
        self.assertPackEqual([single_before, cont, single_after], result)

    def test_not_extend_cont(self): 
        cont = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                          'UNTIL=20161023T235959;INTERVAL=1;'
                          'BYMINUTE=0;BYHOUR=3'),
                'duration': 30,
                'continuous': True}

        single_too_soon = {'duration': 30,
                           'rrule': ('DTSTART:20161008\nRRULE:FREQ=DAILY;'
                                     'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_too_soon])

        single_too_late = {'duration': 30,
                           'rrule': ('DTSTART:20161025\nRRULE:FREQ=DAILY;'
                                     'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_too_late])

        single_hour = {'duration': 30,
                       'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=4')}
        self.assertNotPack([cont, single_hour])

        single_minute = {'duration': 30,
                         'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=10;BYHOUR=3')}
        self.assertNotPack([cont, single_minute])

        single_duration = {'duration': 90,
                           'rrule': ('DTSTART:20161009\nRRULE:FREQ=DAILY;'
                                     'COUNT=1;BYMINUTE=0;BYHOUR=3')}
        self.assertNotPack([cont, single_duration])

    def test_extend_wrec_with_sing(self):
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}        
        sing_before = {'duration': 60,
                       'rrule': ('DTSTART:20150303\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=8')}        
        sing_after = {'duration': 60,
                       'rrule': ('DTSTART:20150331\nRRULE:FREQ=DAILY;'
                                 'COUNT=1;BYMINUTE=0;BYHOUR=8')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20150303\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150331T235959')}
        
        self.assertPackEqual([weekly, sing_before, sing_after], result)

    def test_not_extend_wrec(self):
        weekly = {'duration': 60,
                  'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        
        sing_too_soon = {'duration': 60,
                         'rrule': ('DTSTART:20150217\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=0;BYHOUR=8')}    
        self.assertNotPack([weekly, sing_too_soon])

        sing_too_late = {'duration': 60,
                         'rrule': ('DTSTART:20150407\nRRULE:FREQ=DAILY;'
                                   'COUNT=1;BYMINUTE=0;BYHOUR=8')}   
        self.assertNotPack([weekly, sing_too_late])

        sing_wrong_day = {'duration': 60,
                          'rrule': ('DTSTART:20150225\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=0;BYHOUR=8')}    
        self.assertNotPack([weekly, sing_wrong_day])

        sing_wrong_dur = {'duration': 61,
                          'rrule': ('DTSTART:20150224\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=0;BYHOUR=8')}    
        self.assertNotPack([weekly, sing_wrong_dur])

        sing_wrong_min = {'duration': 60,
                          'rrule': ('DTSTART:20150224\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=5;BYHOUR=8')}
        self.assertNotPack([weekly, sing_wrong_min])

        sing_wrong_hou = {'duration': 60,
                          'rrule': ('DTSTART:20150224\nRRULE:FREQ=DAILY;'
                                    'COUNT=1;BYMINUTE=0;BYHOUR=9')}   
        self.assertNotPack([weekly, sing_wrong_hou])

    def test_fusion_cont_overlap(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        result = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30,
                  'continuous': True}
        self.assertPackEqual([cont1, cont2], result)

    def test_fusion_cont_extend(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        cont2 = {'rrule': ('DTSTART:20161024\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        result = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                            'UNTIL=20161030T235959;INTERVAL=1;'
                            'BYMINUTE=0;BYHOUR=3'),
                  'duration': 30,
                  'continuous': True}
        self.assertPackEqual([cont1, cont2], result)

    def test_no_fusion_cont_gap(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        cont2 = {'rrule': ('DTSTART:20161025\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        self.assertNotPack([cont1, cont2])

    def test_no_fusion_cont_diff(self):
        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=2'),
                 'duration': 30,
                 'continuous': True}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        self.assertNotPack([cont1, cont2])

        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=10;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        self.assertNotPack([cont1, cont2])

        cont1 = {'rrule': ('DTSTART:20161010\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161023T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 30,
                 'continuous': True}
        cont2 = {'rrule': ('DTSTART:20161015\nRRULE:FREQ=DAILY;'
                           'UNTIL=20161030T235959;INTERVAL=1;'
                           'BYMINUTE=0;BYHOUR=3'),
                 'duration': 40,
                 'continuous': True}
        self.assertNotPack([cont1, cont2])
 
    def test_fusion_wrec_overlap(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        result = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150414T235959')}
        self.assertPackEqual([weekly1, weekly2], result)
 
    def test_fusion_wrec_extend(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150329\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        result = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150414T235959')}
        self.assertPackEqual([weekly1, weekly2], result)
 
    def test_fusion_wrec_days(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20161011\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161019T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20161004\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161018T235959')}
        result = {'duration': 60,
                  'rrule': ('DTSTART:20161010\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                            'BYHOUR=8;BYMINUTE=0;UNTIL=20161018T235959')}
        self.assertPackEqual([weekly1, weekly2], result)
 
    def test_no_fusion_wrec_gap(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150405\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

    def test_no_fusion_wrec_diff(self):
        weekly1 = {'duration': 30,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=9;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150305\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=10;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])

        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20150302\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150326T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20150310\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20150420T235959')}
        self.assertNotPack([weekly1, weekly2])
 
    def test_no_fusion_wrec_days(self):
        weekly1 = {'duration': 60,
                   'rrule': ('DTSTART:20161011\nRRULE:FREQ=WEEKLY;BYDAY=TU;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161019T235959')}
        weekly2 = {'duration': 60,
                   'rrule': ('DTSTART:20161003\nRRULE:FREQ=WEEKLY;BYDAY=MO;'
                             'BYHOUR=8;BYMINUTE=0;UNTIL=20161018T235959')}
        self.assertNotPack([weekly1, weekly2])
