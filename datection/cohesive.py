# -*- coding: utf-8 -*-

"""
Module in charge of transforming set of rrule + duration object into a
more cohesive rrule set.

"""
from datetime import timedelta, datetime
from copy import deepcopy

import datection
from datection.models import DurationRRule
from datection.utils import makerrulestr


class DurationRRuleAnalyser(DurationRRule):

    """DurationRRuleAnalyser. """

    def __init__(self, dict_rrule):
        """."""
        super(DurationRRuleAnalyser, self).__init__(dict_rrule)

    @property
    def has_day(self):
        """ Check if given duration rrule has weekdays occurences. """
        return ("FREQ=WEEKLY" in self.duration_rrule['rrule']
                and not "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;"
                in self.duration_rrule['rrule'])

    @property
    def has_time(self):
        """ Check if given duration rrule precise time. """
        return ("BYHOUR=" in self.duration_rrule['rrule']
                and "BYMINUTE=" in self.duration_rrule['rrule']
                and not 'BYHOUR=0;BYMINUTE=0;'
                in self.duration_rrule['rrule'])

    @property
    def has_timelapse(self):
        """ Check if given duration rrule appear in a lapse time. """
        year = timedelta(days=365)
        yearp1 = year + timedelta(hours=23, minutes=59, seconds=59)
        return ("DTSTART:" in self.duration_rrule['rrule']
                and "UNTIL=" in self.duration_rrule['rrule']
                and self.rrule.until not in [
                    self.rrule.dtstart + year,
                    self.rrule.dtstart + yearp1
                ])

    @property
    def has_date(self):
        """ Check if given duration rrule appear in a precise date. """
        return ("DTSTART:" in self.duration_rrule['rrule']
                and "COUNT=1" in self.duration_rrule['rrule']
                and not self.rrule.until)

    def is_same_timelapse(self, drrule):
        """ Check drrule occur in same lapse time.

        :returns: Boolean

        """
        if self.has_timelapse and drrule.has_timelapse:
            return (self.start_datetime == drrule.start_datetime
                    and self.end_datetime == drrule.end_datetime
                    and self.start_datetime != self.end_datetime)

    def is_same_date(self, drrule):
        """ Check drrule has same date as another DurationRRuleAnalyser. """
        if self.has_date and drrule.has_date:
            return (self.start_datetime == drrule.start_datetime
                    and self.end_datetime == drrule.end_datetime
                    and self.count == 1)

    def is_same_weekdays(self, drrule):
        """ Check drrule has same weekday as another DurationRRuleAnalyser. """
        return ((not (self.rrule.freq == 2 and drrule.rrule.freq == 3
                      and drrule.rrule.count == 1)
                 or (drrule.end_datetime.weekday() in self.rrule._byweekday))
                and
                (not (self.rrule.freq == 2 and drrule.rrule.freq == 2)
                 or (self.rrule._byweekday == drrule.rrule._byweekday)))

    def is_same_time(self, drrule):
        """ Check drrule has same time as another DurationRRuleAnalyser."""
        if self.has_time and drrule.has_time:
            return (self.rrule.byhour == drrule.rrule.byhour
                    and self.rrule.byminute == drrule.rrule.byminute)

    def is_same(self, drrule_analyser):
        """ Check drrule has same timelapse, date, day, and time if isset."""
        is_same = True
        if self.has_timelapse:
            is_same = self.is_same_timelapse(drrule_analyser)
        if self.has_date:
            is_same = self.is_same_date(drrule_analyser)
        if self.has_day:
            is_same = self.is_same_weekdays(drrule_analyser)
        if self.has_time:
            is_same = self.is_same_time(drrule_analyser)
        return is_same

    def is_containing_start_lapse_of(self, drrule):
        """ Check drrule lapse begin in current 'self' object timelapse.

            By example:
                literal self = "du 20 au 25 mars"
                literal drrule = "du 24 au 28 mars"

        :returns: Boolean

        """
        return (self.start_datetime < drrule.start_datetime
                and drrule.start_datetime < self.end_datetime)

    def is_containing_end_lapse_of(self, drrule):
        """ Check drrule lapse end in current 'self' object timelapse.

            By example:
                literal dr1 = "du 20 au 25 mars"
                literal dr2 = "du 18 au 20 mars"

        :returns: Boolean

        """
        return (self.start_datetime < drrule.end_datetime
                and drrule.end_datetime < self.end_datetime)

    def is_end_stick_begin_lapse_of(self, drrule):
        """ Check self lapse end is contigous with drrule timelapse.

            By example:
                literal self = "du 20 au 25 mars"
                literal drrule = "du 26 au 28 mars"
                or:
                    literal self = "20 mars"
                    literal drrule = "21 mars"

        :returns: Boolean

        """
        return (not self.is_sublapse_of(drrule)
                and not drrule.is_sublapse_of(self)
                and (self.end_datetime == drrule.start_datetime
                     or (drrule.rrule.count == 1
                         and ((self.rrule.freq == 3 and drrule.rrule.freq == 3
                               and self.end_datetime >= drrule.start_datetime - timedelta(days=1)
                               and self.end_datetime <= drrule.start_datetime
                               )
                              or (self.is_same_weekdays(drrule)
                                  and self.end_datetime >= drrule.start_datetime - timedelta(days=7)
                                  and self.end_datetime <= drrule.start_datetime
                                  )
                              )
                         )
                     )
                )

    def is_sublapse_of(self, drrule):
        """ Check self sublapse of rrule timelapse.

            By example:
                literal self = "du 20 au 25 mars"
                literal rrule = "du 21 au 24 mars"

        :returns: Boolean

        """
        return (drrule.start_datetime <= self.start_datetime
                and self.end_datetime <= drrule.end_datetime
                and drrule.has_timelapse
                # if weekday
                and self.is_same_weekdays(drrule))

    def take_time_of(self, drrule):
        """ Get time of another drrule if the current has no time specified."""
        if not self.has_time and drrule.has_time:
            self.duration_rrule['duration'] = drrule.duration
            self.rrule._byhour = drrule.rrule.byhour
            self.rrule._byminute = drrule.rrule.byminute
            return True

    def take_weekdays_of(self, drrule):
        """ Concat weekday of another drrule if frequence is daily
        or weekly and weekly for the other drrule.

        :returns: Boolean days appended

        """
        if (drrule.has_day
            and (self.is_same_time(drrule))
            and self.rrule.freq in [3, 2]  # daily, weekly
            and drrule.rrule.freq == 2
                and drrule.rrule.byweekday):
            if self.rrule._byweekday:
                self.rrule._byweekday = set(
                    self.rrule._byweekday)
            else:
                self.rrule._byweekday = set()
            self.rrule._byweekday = self.rrule._byweekday.union(
                drrule.rrule._byweekday)
            self.rrule._freq = drrule.rrule.freq
            return True

    def absorb_drrule(self, drrule):
        """ Try to unify/absorb the proposed DurationRRule in the current one
        without losing information and be inconsistant. """
        self.debug = False
        more_cohesion = False
        case = []
        if (not self.has_time and
                (not self.has_day or self.is_same_weekdays(drrule))
                or self.is_same_time(drrule)):

            if (self.is_same_timelapse(drrule)
                    or self.is_same_date(drrule)):
                case.append('==')
                more_cohesion = True

            if drrule.is_sublapse_of(self):
                # case 1 time_repr: <rr1- <rr2- -rr2> -rr1>
                case.append('<rr1- <rr2- -rr2> -rr1>')
                more_cohesion = True

            if self.is_sublapse_of(drrule):
                # case 2 time_repr: <rr2- <rr1- -rr1> -rr2>
                case.append('<rr2- <rr1- -rr1> -rr2>')
                self.rrule._dtstart = drrule.rrule.dtstart
                self.rrule._until = drrule.end_datetime
                more_cohesion = True

            if self.is_end_stick_begin_lapse_of(drrule):
                # case 3 time_repr: <rr1- -rr1><rr2- -rr2> with same time
                # precision
                case.append('<rr1- -rr1><rr2- -rr2>')
                if not drrule.rrule.until:
                    self.rrule._until = drrule.start_datetime
                    self.rrule._count = None
                else:
                    self.rrule._until = drrule.rrule.until
                more_cohesion = True

            if drrule.is_end_stick_begin_lapse_of(self):
                # case 4 time_repr: <rr2- -rr2><rr1- -rr1> with same time
                # if time is same precision
                case.append('<rr2- -rr2><rr1- -rr1>')
                self.rrule._dtstart = drrule.rrule.dtstart
                more_cohesion = True

            if (self.is_containing_end_lapse_of(drrule)
                    and not self.is_containing_start_lapse_of(drrule)):
                # case 5 time_repr: <rr2 - <rr1 - -rr2 > -rr1 >
                case.append('<rr2 - <rr1 - -rr2 > -rr1 >')
                self.rrule._dtstart = drrule.start_datetime
                more_cohesion = True

            if (self.is_containing_start_lapse_of(drrule)
                    and not self.is_containing_end_lapse_of(drrule)):
                # case 6 time_repr: <rr1- <rr2- -rr1> -rr2>
                case.append('<rr1- <rr2- -rr1> -rr2>')
                self.rrule._until = drrule.end_datetime
                more_cohesion = True

            if more_cohesion:
                self.take_weekdays_of(drrule)
                self.take_time_of(drrule)

        if self.debug and more_cohesion:
            print case
            print 'dr1 \t-', datection.display([self.duration_rrule], 'fr')
            print 'dr2 \t-', datection.display([drrule.duration_rrule], 'fr')
            print 'become \t-', datection.display([
                {'duration': self.duration,
                    'rrule': makerrulestr(
                        self.rrule.dtstart,
                        end=self.rrule.until,
                        freq=self.rrule.freq,
                        rule=self.rrule)
                 }], 'fr'), '\n'
        return more_cohesion

    def type_signature(self):
        """ Return string that uniquely identify the type of rrule.

        Type are based on main fields existance in duration rrule.

        """
        return " ".join(map(lambda x: str(int(x)),
                            [self.has_timelapse, self.has_date,
                             self.has_day, self.has_time]))


class CohesiveDurationRRuleLinter(object):

    """ CohesiveDurationRRuleLinter allow to compare DurationRRule.

    and analyse if there are mergeable in modify first rrule
    and return true.

    """

    def __init__(self, drrules):
        self.drrules = [DurationRRuleAnalyser(rr) for rr in drrules]

    @property
    def drrules_by(self):
        """ Structure access to rrules groups by specificity. """
        drrules = {
            'has_day': [],
            'has_time': [],
            'has_timelapse': [],
            'has_date': [],
            'has_not_timelapse_or_date': [],
            'signature': {}
        }

        for rr in self.drrules:
            if rr.has_day:
                drrules['has_day'].append(rr)
            if rr.has_time:
                drrules['has_time'].append(rr)
            if rr.has_timelapse:
                drrules['has_timelapse'].append(rr)
            if rr.has_date:
                drrules['has_date'].append(rr)
            if not rr.has_date and not rr.has_timelapse:
                drrules['has_not_timelapse_or_date'].append(rr)
            ex = rr.type_signature()
            if not ex in drrules['signature']:
                drrules['signature'][ex] = []
            drrules['signature'][ex].append(rr)
        return drrules

    def avoid_doubles(self):
        """ Aim to generate a Set of duration rrule. """
        keeped_rrules = []
        for drrules in self.drrules_by['signature'].values():
            for examinated_drrule in drrules:
                keep_drrule = True
                for cur_drrule in drrules:
                    if not examinated_drrule is cur_drrule:
                        if cur_drrule.is_same(examinated_drrule):
                            keep_drrule = False
                            if keep_drrule:
                                keeped_rrules.append(examinated_drrule)
                                self.drrules = keeped_rrules

    def merge(self):
        """ Reduce Set of Duration rrule by cohesive unification of drrule. """
        drrules = (self.drrules_by['has_timelapse']
                   + self.drrules_by['has_date'])

        consumed_drrules = []
        for examinated_drrule in drrules:
            if not examinated_drrule in consumed_drrules:
                for cur_drrule in drrules:
                    if (not examinated_drrule is cur_drrule
                            and not cur_drrule in consumed_drrules):
                        if examinated_drrule.absorb_drrule(cur_drrule):
                            consumed_drrules.append(cur_drrule)

        remain_drrules = [drr for drr in drrules
                          if drr not in consumed_drrules]

        self.drrules = remain_drrules + \
            self.drrules_by['has_not_timelapse_or_date']

    def make_drrule_compositions(self):
        """ Compose all possible drrule based on a set of enrichment drrule and
        the unique drrule to have a 'timelapse'. """
        root = self.drrules_by['has_timelapse'][0]
        for drr in self.drrules_by['has_day']:
            root.take_weekdays_of(drr)

        if self.drrules_by['has_time']:
            rrules = []
            for drr in self.drrules_by['has_time']:
                root_copy = deepcopy(root)
                root_copy.take_time_of(drr)
                rrules.append(root_copy)
        else:
            rrules = [root]

        self.drrules = rrules

    def __call__(self):
        """Lint a list of DurationRRule and transform it to a set of
        more cohesive one."""
        self.avoid_doubles()
        self.merge()

        # Check nbr of occurences of root
        qte_gen_root = (len(self.drrules_by['has_timelapse'])
                        + len(self.drrules_by['has_date']))
        if 1 == qte_gen_root:
            # if one generate all
            self.make_drrule_compositions()

        self.drrules = [{'duration': drr.duration,
                         'rrule': makerrulestr(
                             drr.rrule.dtstart,
                             end=drr.rrule.until,
                             freq=drr.rrule.freq,
                             rule=drr.rrule)
                         }
                        for drr in self.drrules]

        return self.drrules


def cohesive_rrules(drrules):
    """ Take a rrule set and try to merge them into more cohesive rrule set.

    :rrules: list(dict()) containing duration rrule in string format
                          foreach dict.
    :returns: list(dict()) containing duration rrule in string format
                          foreach dict.

    """
    return CohesiveDurationRRuleLinter(drrules)()
