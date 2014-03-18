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


def lack_of_precise_time_lapse(drrule):
    """ Check if a duration rule offer a precise lapse time.

    :returns: Boolean

    """
    # Only currently found solution to identify
    # where date begin/end undefined
    timed = timedelta(days=365, hours=23, minutes=59, seconds=59)
    return (not drrule.rrule.until
            or drrule.rrule.dtstart +
            timed == drrule.rrule.until)


def append_dr2_weekday_in_dr1(dr1, dr2):
    """ Try to append weekday of dr2 to dr1 if frequence is daily
    or weekly for dr1 and weekly for dr2.

    :returns: Boolean days appended

    """
    if (dr1.rrule.freq in [3, 2]  # daily, weekly
        and dr2.rrule.freq == 2
            and dr2.rrule.byweekday):
        if dr1.rrule._byweekday:
            dr1.rrule._byweekday = set(
                dr1.rrule._byweekday)
        else:
            dr1.rrule._byweekday = set()
        dr1.rrule._byweekday = dr1.rrule._byweekday.union(
            dr2.rrule._byweekday)
        dr1.rrule._freq = dr2.rrule.freq
        return True


def append_dr2_time_in_dr1(dr1, dr2):
    if lack_of_precise_time_lapse(dr2):
        dr1.rrule._byhour = dr2.rrule.byhour
        dr1.rrule._byminute = dr2.rrule.byminute
        dr1._duration = dr2.duration
        if dr2.duration == 0:
            dr1.rrule._count = 1


class CohesiveDurationRRuleTimeLinter(object):

    """ CohesiveDurationRRuleLinter allow to compare two DurationRRule.

    It analyse both if there is mergeable it modify first rrule
    and return true.

    """

    def __init__(self, examined_dur_rrule, cur_dur_rrule):
        self.dr1 = examined_dur_rrule
        self.dr2 = cur_dur_rrule

    def same_time_or_dr1_time_undefined(self):
        """ Check dr1 and dr2 happen at same time, or if dri is undefined.

       :returns: Boolean

        """
        return ((self.dr1.rrule.byhour == self.dr2.rrule.byhour
                and self.dr1.rrule.byminute == self.dr2.rrule.byminute)
                or (self.dr1.rrule.byhour and self.dr1.rrule.byhour[0] == 0
                    and self.dr1.rrule.byminute[0] == 0))

    def dr2_end_in_dr1_lapse(self):
        """ Check dr2 lapse end in dr2 lapse.

            By example:
                literal dr1 = "du 20 au 25 mars"
                literal dr2 = "du 18 au 20 mars"

        :returns: Boolean

        """
        return (self.dr1.start_datetime < self.dr2.end_datetime
                and self.dr2.end_datetime < self.dr1.end_datetime)

    def dr2_begin_in_dr1_lapse(self):
        """ Check dr2 lapse begin in dr2 lapse.

            By example:
                literal dr1 = "du 20 au 25 mars"
                literal dr2 = "du 24 au 28 mars"

        :returns: Boolean

        """
        return (self.dr1.start_datetime < self.dr2.start_datetime
                and self.dr2.start_datetime < self.dr1.end_datetime)

    def dr1_sublapse_dr2(self):
        """ Check dr1 sublapse of dr2 lapse.

            By example:
                literal dr1 = "du 20 au 25 mars"
                literal dr2 = "du 21 au 24 mars"

        :returns: Boolean

        """
        return (self.dr2.start_datetime <= self.dr1.start_datetime
                and self.dr1.end_datetime <= self.dr2.end_datetime
                and not lack_of_precise_time_lapse(self.dr2))

    def dr2_sublapse_dr1(self):
        """ Check dr2 sublapse of dr1 lapse.

            By example:
                literal dr1 = "du 21 au 24 mars"
                literal dr2 = "du 20 au 25 mars"

        :returns: Boolean

        """
        return (self.dr1.start_datetime <= self.dr2.start_datetime
                and self.dr2.end_datetime <= self.dr1.end_datetime
                and not lack_of_precise_time_lapse(self.dr1))

    def dr_end_stick_dr_begin(self, dr1, dr2):
        """ Check dr1 lapse end is contigous with dr2 lapse.

            By example:
                literal dr1 = "du 20 au 25 mars"
                literal dr2 = "du 26 au 28 mars"
                or:
                    literal dr1 = "20 mars"
                    literal dr2 = "21 mars"

        :returns: Boolean

        """
        return (dr1.end_datetime == dr2.start_datetime
                or (dr2.rrule.count == 1
                    and (
                        dr1.end_datetime == dr2.start_datetime -
                        timedelta(minutes=1)
                        or dr1.end_datetime == dr2.start_datetime - timedelta(days=1)
                    )))

    def is_precisely_same_lapse(self):
        """ Check drrule are contained in same lapse time.

        :returns: Boolean

        """
        return (self.dr1.start_datetime == self.dr2.start_datetime
                and self.dr1.end_datetime == self.dr2.end_datetime)

    def __call__(self):
        """ Check if two drrules can merged with timelapse infos.

        :returns: Boolean if dr1 has been modified and contain dr2 in it.

        """
        more_cohesion = False
        if self.same_time_or_dr1_time_undefined():

            if self.is_precisely_same_lapse():
                more_cohesion = True

            if self.dr1_sublapse_dr2():
                # case 1 time_repr: <rr1- <rr2- -rr2> -rr1>
                self.dr1.rrule._dtstart = self.dr2.rrule.dtstart
                self.dr1.rrule._until = self.dr2.end_datetime
                more_cohesion = True

            if self.dr2_sublapse_dr1():
                # case 2 time_repr: <rr2- <rr1- -rr1> -rr2>
                more_cohesion = True

            if self.dr_end_stick_dr_begin(self.dr1, self.dr2):
                # case 3 time_repr: <rr1- -rr1><rr2- -rr2> with same time
                # precision
                if not self.dr2.rrule.until:
                    self.dr1.rrule._until = self.dr2.start_datetime
                else:
                    self.dr1.rrule._until = self.dr2.until
                    self.dr1.rrule._count = None
                more_cohesion = True

            if self.dr_end_stick_dr_begin(self.dr2, self.dr1):
                # case 4 time_repr: <rr2- -rr2><rr1- -rr1> with same time
                # if time is same precision
                self.dr1.rrule._dtstart = self.dr2.rrule.dtstart
                more_cohesion = True

            if (self.dr2_end_in_dr1_lapse()
                    and not self.dr2_begin_in_dr1_lapse()):
                # case 5 time_repr: <rr2 - <rr1 - -rr2 > -rr1 >
                self.dr1.rrule._dtstart = self.dr2.start_datetime
                more_cohesion = True

            if (self.dr2_begin_in_dr1_lapse()
                    and not self.dr2_end_in_dr1_lapse()):
                # case 6 time_repr: <rr1- <rr2- -rr1> -rr2>
                self.dr1.rrule._until = self.dr2.end_datetime
                more_cohesion = True

            if more_cohesion:
                append_dr2_weekday_in_dr1(self.dr1, self.dr2)
                append_dr2_time_in_dr1(self.dr1, self.dr2)

        return more_cohesion


class RRuleAnalyser(object):

    """RRuleAnalyser. """

    def __init__(self, dict_rrule):
        """."""
        self.as_obj = DurationRRule(dict_rrule)
        self.as_dict = dict_rrule

    @property
    def has_day(self):
        return ("FREQ=WEEKLY" in self.as_dict['rrule'] and not
                "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;" in self.as_dict['rrule'])

    @property
    def has_time(self):
        return ("BYHOUR=" in self.as_dict['rrule']
                and "BYMINUTE=" in self.as_dict['rrule']
                and not 'BYHOUR=0;BYMINUTE=0;' in self.as_dict['rrule'])

    @property
    def has_timelapse(self):
        timed = timedelta(days=365)  # , hours=23, minutes=59, seconds=59
        return ("DTSTART:" in self.as_dict['rrule']
                and "UNTIL=" in self.as_dict['rrule']
                and (self.as_obj.rrule.dtstart + timed)
                != self.as_obj.rrule.until)

    @property
    def has_date(self):
        return ("DTSTART:" in self.as_dict['rrule']
                and "COUNT=1" in self.as_dict['rrule']
                and not self.as_obj.rrule.until)

    def is_same_timelapse(self, drrule):
        """."""
        pass

    def is_same_date(self, drrule):
        """."""
        pass

    def is_same_day(self, drrule):
        """."""
        pass

    def is_same_time(self, drrule):
        """."""
        pass

    def is_same(self, drrule_analyser):
        """."""
        is_same = True
        # TODO compartive system
        if self.has_timelapse:
            is_same = self.is_same_timelapse(drrule_analyser)
        if self.has_date:
            is_same = self.is_same_date(drrule_analyser)
        if self.has_day:
            is_same = self.is_same_day(drrule_analyser)
        if self.has_time:
            is_same = self.is_same_time(drrule_analyser)
        return is_same

    def export(self):
        return " ".join([str(int(self.has_timelapse)),
                         str(int(self.has_date)),
                         str(int(self.has_day)),
                         str(int(self.has_time))])


class CohesiveDurationRRuleLinter(object):

    """ CohesiveDurationRRuleLinter allow to compare DurationRRule.

    and analyse if there are mergeable in modify first rrule
    and return true.

    """

    def __init__(self, drrules):
        self.drrules = [RRuleAnalyser(rr) for rr in drrules]

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
            ex = rr.export()
            if not ex in drrules['signature']:
                drrules['signature'][ex] = []
            drrules['signature'][ex].append(rr)
        return drrules

    def avoid_doubles(self):
        """ . """
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

    def merge_timelapse(self):
        """ . """
        drrules = (self.drrules_by['has_timelapse']
                   + self.drrules_by['has_date'])

        consumed_drrules = []
        for examinated_drrule in drrules:
            if not examinated_drrule in consumed_drrules:
                for cur_drrule in drrules:
                    if (not examinated_drrule is cur_drrule
                            and not cur_drrule in consumed_drrules):
                        ctl = CohesiveDurationRRuleTimeLinter(
                            examinated_drrule.as_obj, cur_drrule.as_obj)
                        if ctl():
                            examinated_drrule.as_obj = ctl.dr1
                            consumed_drrules.append(cur_drrule)

        remain_drrules = [drr for drr in drrules
                          if drr not in consumed_drrules]

        self.drrules = remain_drrules + \
            self.drrules_by['has_not_timelapse_or_date']

    def skip_weekly_occurence(self):
        """ TODO. """
        pass

    def make_drrule_compositions(self):
        """ TODO. """
        root = self.drrules_by['has_timelapse'][0]
        for drr in self.drrules_by['has_day']:
            append_dr2_weekday_in_dr1(root.as_obj, drr.as_obj)

        if self.drrules_by['has_time']:
            rrules = []
            for drr in self.drrules_by['has_time']:
                root_copy = deepcopy(root)
                append_dr2_time_in_dr1(root_copy.as_obj, drr.as_obj)
                rrules.append(root_copy)
        else:
            rrules = [root]

        self.drrules = rrules

    def __call__(self):
        """."""
        self.avoid_doubles()
        self.merge_timelapse()

        # Check nbr of occurences of root
        qte_gen_root = (len(self.drrules_by['has_timelapse'])
                        + len(self.drrules_by['has_date']))
        if 1 == qte_gen_root:
            # if one generate all
            self.make_drrule_compositions()
        elif 1 < qte_gen_root:
            # if (< 1) >> try to skip daily occurence if issets
            self.skip_weekly_occurence()

        self.drrules = [{'duration': drr.as_obj.duration,
                         'rrule': makerrulestr(
                             drr.as_obj.rrule.dtstart,
                             end=drr.as_obj.rrule.until,
                             freq=drr.as_obj.rrule.freq,
                             rule=drr.as_obj.rrule)
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
