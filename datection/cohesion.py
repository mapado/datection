# -*- coding: utf-8 -*-

"""
Module in charge of transforming set of rrule + duration object into a
more cohesive rrule set.

"""
from datetime import timedelta
from copy import deepcopy

from dateutil.rrule import WEEKLY
from dateutil.rrule import DAILY
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from datection.models import DurationRRule
from datection.utils import makerrulestr


class DurationRRuleAnalyser(DurationRRule):

    """DurationRRuleAnalyser. TODO"""

    def __unicode__(self):
        """ Return string that uniquely identify the type of rrule.

        Type are based on main fields existance in duration rrule.

        """
        return u" ".join(map(lambda x: str(int(x)),
                             [self.has_timelapse, self.has_date,
                             self.has_day, self.has_time]))

    @property
    def has_day(self):
        """ Check if given duration rrule has weekdays occurences. """
        return (self.rrule.freq == WEEKLY
                and self.rrule.byweekday != (MO, TU, WE, TH, FR, SA, SU))

    @property
    def has_time(self):
        """ Check if given duration rrule precise time. """
        return not ((not self.rrule.byminute or self.rrule.byminute[0] == 0)
                    and (not self.rrule.byhour or self.rrule.byhour[0] == 0))

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
                ]
                and self.end_datetime >= self.start_datetime - timedelta(days=1))

    @property
    def has_date(self):
        """ Check if given duration rrule appear in a precise date. """
        return (self.rrule.count == 1)

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
            return (self.start_datetime.date() == drrule.start_datetime.date()
                    and self.end_datetime.date() == drrule.end_datetime.date()
                    and self.rrule.count == 1)

    def is_same_weekdays(self, drrule):
        """ Check drrule has same weekday as another DurationRRuleAnalyser. """
        return ((not (self.rrule.freq == WEEKLY and drrule.rrule.freq == DAILY
                      and drrule.rrule.count == 1)
                 or (drrule.end_datetime.weekday() in self.rrule._byweekday))
                and
                (not (self.rrule.freq == WEEKLY and drrule.rrule.freq == WEEKLY)
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
                         and ((self.rrule.freq == DAILY and drrule.rrule.freq == DAILY
                               and self.end_datetime >= drrule.start_datetime - timedelta(days=1)
                               and self.end_datetime <= drrule.start_datetime
                               )
                              or (self.is_same_weekdays(drrule)
                                  and self.end_datetime >= drrule.start_datetime - timedelta(days=8)
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
            and (not self.has_time or self.is_same_time(drrule))
            and self.rrule.freq in [WEEKLY, DAILY]  # daily, weekly
            and drrule.rrule.freq == WEEKLY
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
        more_cohesion = False

        if ((not self.has_time
             or not drrule.has_time
             or self.is_same_time(drrule))
                and (not self.has_day or self.is_same_weekdays(drrule))):

            if (self.is_same_timelapse(drrule)
                    or self.is_same_date(drrule)):
                more_cohesion = True

            if drrule.is_sublapse_of(self):
                # case 1 time_repr: <rr1- <rr2- -rr2> -rr1>
                more_cohesion = True

            if self.is_sublapse_of(drrule):
                # case 2 time_repr: <rr2- <rr1- -rr1> -rr2>
                self.rrule._dtstart = drrule.rrule.dtstart
                self.rrule._until = drrule.end_datetime
                more_cohesion = True

            if self.is_end_stick_begin_lapse_of(drrule):
                # case 3 time_repr: <rr1- -rr1><rr2- -rr2> with same time
                # precision
                if not drrule.rrule.until:
                    self.rrule._until = drrule.start_datetime
                    self.rrule._count = None
                else:
                    self.rrule._until = drrule.rrule.until
                more_cohesion = True

            if drrule.is_end_stick_begin_lapse_of(self):
                # case 4 time_repr: <rr2- -rr2><rr1- -rr1> with same time
                # if time is same precision
                self.rrule._dtstart = drrule.rrule.dtstart
                more_cohesion = True

            if (self.is_containing_end_lapse_of(drrule)
                    and not self.is_containing_start_lapse_of(drrule)):
                # case 5 time_repr: <rr2 - <rr1 - -rr2 > -rr1 >
                self.rrule._dtstart = drrule.start_datetime
                more_cohesion = True

            if (self.is_containing_start_lapse_of(drrule)
                    and not self.is_containing_end_lapse_of(drrule)):
                self.rrule._until = drrule.end_datetime
                more_cohesion = True

        if self.is_same_date(drrule) and not self.has_time and drrule.has_time:
            more_cohesion = True

        if (self.has_day and drrule.has_day
            and not self.has_timelapse
            and not drrule.has_timelapse
            and self.is_same_time(drrule)
                and not self.is_same_weekdays(drrule)):
            more_cohesion = True

        if more_cohesion:
            self.take_weekdays_of(drrule)
            self.take_time_of(drrule)

        return more_cohesion


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
            sign = unicode(rr)
            if not sign in drrules['signature']:
                drrules['signature'][sign] = []
            drrules['signature'][sign].append(rr)
        return drrules

    def avoid_doubles(self):
        """ Aim to generate a Set of duration rrule. """
        kept_rrules = []
        for drrules in self.drrules_by['signature'].values():
            for examinated_drrule in drrules:
                keep_drrule = True
                for cur_drrule in drrules:
                    if not examinated_drrule is cur_drrule:
                        if cur_drrule.is_same(examinated_drrule):
                            keep_drrule = False
                            if keep_drrule:
                                kept_rrules.append(examinated_drrule)
                                self.drrules = kept_rrules

    def merge(self):
        """ Reduce Set of Duration rrule by cohesive unification of drrule. """

        def drrule_try_to_absorb_set(examinated_drrule, drrules, consumed_drrules):
            for cur_drrule in drrules:
                if (not examinated_drrule is cur_drrule
                        and not cur_drrule in consumed_drrules):
                    if examinated_drrule.absorb_drrule(cur_drrule):
                        consumed_drrules.append(cur_drrule)
                        # reexamine previously not absorbed cur_drrule
                        drrule_try_to_absorb_set(
                            examinated_drrule, drrules, consumed_drrules)
            return consumed_drrules

        def merge_in_group(drrules):
            consumed_drrules = []
            for examinated_drrule in drrules:
                if not examinated_drrule in consumed_drrules:
                    consumed_drrules = drrule_try_to_absorb_set(
                        examinated_drrule, drrules, consumed_drrules)

            return [drr for drr in drrules if drr not in consumed_drrules]

        dated_drrule = merge_in_group((self.drrules_by['has_timelapse']
                                       + self.drrules_by['has_date']))
        if not dated_drrule:
            self.drrules = merge_in_group(
                self.drrules_by['has_not_timelapse_or_date'])
        else:
            self.drrules = dated_drrule + \
                self.drrules_by['has_not_timelapse_or_date']

    def make_drrule_compositions(self, root):
        """ Compose all possible drrule based on a set of enrichment drrule and
        the unique drrule to have a 'timelapse'. """

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
        roots = self.drrules_by['has_timelapse'] + self.drrules_by['has_date']
        if len(roots) == 1:
            # if one generate all
            self.make_drrule_compositions(roots[0])

        # ensure uniqueness
        gen_drrules = {}
        for drr in self.drrules:
            rrule = makerrulestr(
                drr.rrule.dtstart,
                end=drr.rrule.until,
                freq=drr.rrule.freq,
                rule=drr.rrule)
            gen_drrules[str(drr.duration) + rrule] = {
                'duration': drr.duration,
                'rrule': rrule
            }
        return gen_drrules.values()


def cohesive_rrules(drrules):
    """ Take a rrule set and try to merge them into more cohesive rrule set.

    :rrules: list(dict()) containing duration rrule in string format
                          foreach dict.
    :returns: list(dict()) containing duration rrule in string format
                          foreach dict.

    """
    return CohesiveDurationRRuleLinter(drrules)()
