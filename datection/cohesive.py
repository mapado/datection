# -*- coding: utf-8 -*-

"""
Module in charge of transforming set of rrule + duration object into a
more cohesive rrule set.

"""
from datetime import timedelta

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


class CohesiveDurationRRuleLinter(object):

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
                or (self.dr1.rrule.byhour and self.dr2.rrule.byhour
                    and self.dr1.rrule.byhour[0] == 0
                    and self.dr2.rrule.byhour[0] == 0))

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

    def append_dr2_weekday_in_dr1(self):
        """ Try to append weekday of dr2 to dr1 if frequence is daily
        or weekly for dr1 and weekly for dr2.

        :returns: Boolean days appended

        """
        if (self.dr1.rrule.freq in [3, 2]  # daily, weekly
            and self.dr2.rrule.freq == 2
                and self.dr2.rrule.byweekday):
            if self.dr1.rrule._byweekday:
                self.dr1.rrule._byweekday = set(
                    self.dr1.rrule._byweekday)
            else:
                self.dr1.rrule._byweekday = set()
            self.dr1.rrule._byweekday = self.dr1.rrule._byweekday.union(
                self.dr2.rrule._byweekday)
            self.dr1.rrule._freq = self.dr2.rrule.freq
            return True

    def is_precisely_same_lapse(self):
        """ Check drrule are contained in same lapse time.

        :returns: Boolean

        """
        return (self.dr1.start_datetime == self.dr2.start_datetime
                and self.dr1.end_datetime == self.dr2.end_datetime)

    def __call__(self):
        """ Check if two drrules can be merged with case by case heuristics.

        :returns: Boolean if dr1 has been modified and contain dr2 in it.

        """
        more_cohesion = False
        might_need_time_detail = (self.dr1.duration == 1439)

        if lack_of_precise_time_lapse(self.dr2) and might_need_time_detail:
            self.dr1.rrule._byhour = self.dr2.rrule.byhour
            self.dr1.rrule._byminute = self.dr2.rrule.byminute
            self.dr1.duration_rrule = self.dr2.duration_rrule

        if self.same_time_or_dr1_time_undefined():
            if self.append_dr2_weekday_in_dr1():
                more_cohesion = True

            if self.is_precisely_same_lapse():
                return True

            if (self.dr2_end_in_dr1_lapse()
                    and not self.dr2_begin_in_dr1_lapse()):
                # case 1 time_repr: <rr2 - <rr1 - -rr2 > -rr1 >
                self.dr1.rrule._dtstart = self.dr2.start_datetime
                return True

            if (self.dr2_begin_in_dr1_lapse()
                    and not self.dr2_end_in_dr1_lapse()):
                # case 2 time_repr: <rr1- <rr2- -rr1> -rr2>
                self.dr1.rrule._until = self.dr2.end_datetime
                return True

            if self.dr1_sublapse_dr2():
                # case 3 time_repr: <rr1- <rr2- -rr2> -rr1>
                self.dr1.rrule._dtstart = self.dr2.rrule.dtstart
                self.dr1.rrule._until = self.dr2.end_datetime
                return True

            if self.dr_end_stick_dr_begin(self.dr1, self.dr2):
                # case 4 time_repr: <rr1- -rr1><rr2- -rr2> with same time
                # precision
                if not self.dr2.rrule.until:
                    self.dr1.rrule._until = self.dr2.start_datetime
                else:
                    self.dr1.rrule._until = self.dr2.until
                self.dr1.rrule._count = None
                return True

            if self.dr_end_stick_dr_begin(self.dr2, self.dr1):
                # case 5 time_repr: <rr2- -rr2><rr1- -rr1> with same time
                # if time is same precision
                self.dr1.rrule._dtstart = self.dr2.rrule.dtstart
                return True
        return more_cohesion


def cohesive_rrules(rrules):
    """ Take a rrule set and try to merge them into more cohesive rrule set.

    :rrules: list(dict()) containing duration rrule in string format
                          foreach dict.
    :returns: list(dict()) containing duration rrule in string format
                          foreach dict.

    """
    dur_rrules = [DurationRRule(rr) for rr in rrules]
    dur_rrules_to_del = set()

    for examined_dur_rrule in dur_rrules:
        if examined_dur_rrule not in dur_rrules_to_del:
            for cur_dur_rrule in dur_rrules:
                if cur_dur_rrule != examined_dur_rrule:
                    if (CohesiveDurationRRuleLinter(
                            examined_dur_rrule, cur_dur_rrule)()):
                        dur_rrules_to_del.add(cur_dur_rrule)

    # Ensure rrule unicity in the list
    dur_rrules_dict = {}
    for r in dur_rrules:
        if r not in dur_rrules_to_del:
            rrule = makerrulestr(
                r.rrule.dtstart, end=r.rrule.until, rule=r.rrule)
            dur_rrules_dict[str(r.duration) + rrule] = {
                'duration': r.duration,
                'rrule': rrule
            }
    dur_rrules = dur_rrules_dict.values()

    return dur_rrules
