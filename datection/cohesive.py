# -*- coding: utf-8 -*-

"""
Module in charge of transforming set of rrule + duration object into a
more cohesive rrule set.

"""
import re

from datetime import timedelta

import datection
from datection.models import DurationRRule
from datection.utils import makerrulestr


def lack_of_precise_time_lapse(drrule):
    # Only currently found solution to identify
    # where date begin/end undefined
    timed = timedelta(days=365, hours=23, minutes=59, seconds=59)
    return (not drrule.rrule.until
            or drrule.rrule.dtstart +
            timed == drrule.rrule.until)


class DurationRRuleManipulator(object):

    def __init__(self, examined_dur_rrule, cur_dur_rrule):
        self.dr1 = examined_dur_rrule
        self.dr2 = cur_dur_rrule

    def same_time_or_first_drr_time_undefined(self):
        return ((self.dr1.rrule.byhour == self.dr2.rrule.byhour
                and self.dr1.rrule.byminute == self.dr2.rrule.byminute)
                or (self.dr1.rrule.byhour[0] == 0
                    and self.dr1.rrule.byhour[0] == 0))

    def end_inside_drrule_lapse(self):
        return (self.dr1.start_datetime < self.dr2.end_datetime
                and self.dr2.end_datetime < self.dr1.end_datetime)

    def begin_inside_drrule_lapse(self):
        return (self.dr1.start_datetime < self.dr2.start_datetime
                and self.dr2.start_datetime < self.dr1.end_datetime)

    def drrule_sublapse_of_drrule(self):
        return (self.dr2.start_datetime <= self.dr1.start_datetime
                and self.dr1.end_datetime <= self.dr2.end_datetime
                and not lack_of_precise_time_lapse(self.dr2))

    def drr_end_stick_dcrr(self):
        return (self.dr1.end_datetime == self.dr2.start_datetime
                or (self.dr2.rrule.count == 1
                    and (
                        self.dr1.end_datetime == self.dr2.start_datetime -
                        timedelta(minutes=1)
                        or self.dr1.end_datetime == self.dr2.start_datetime - timedelta(days=1)
                    )))

    def drr_begin_stick_dcrr(self):
        return (
            self.dr1.start_datetime == self.dr2.end_datetime
            or (self.dr1.rrule.count == 1
                and (self.dr1.start_datetime == self.dr2.end_datetime + timedelta(minutes=1)
                     or self.dr1.start_datetime == self.dr2.end_datetime + timedelta(days=1)
                     )))

    def append_weekday(self):
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
            return (self.dr1.start_datetime == self.dr2.start_datetime
                    and self.dr1.end_datetime == self.dr2.end_datetime)

    def more_cohesion_between_rrules(self):

        more_cohesion = False

        might_need_time_detail = (self.dr1.duration == 1439)
        end_inside = self.end_inside_drrule_lapse()
        begin_inside = self.begin_inside_drrule_lapse()
        drr_sublapse_of_dcrr = self.drrule_sublapse_of_drrule()

        drr_end_stick_dcrr = self.drr_end_stick_dcrr()
        drr_begin_stick_dcrr = self.drr_begin_stick_dcrr()
        is_unspecified_time = lack_of_precise_time_lapse(self.dr2)

        if is_unspecified_time and might_need_time_detail:
            self.dr1.rrule._byhour = self.dr2.rrule.byhour
            self.dr1.rrule._byminute = self.dr2.rrule.byminute
            self.dr1.duration_rrule = self.dr2.duration_rrule

        if self.same_time_or_first_drr_time_undefined():
            if self.append_weekday():
                more_cohesion = True

            if self.is_precisely_same_lapse():
                return True
            if end_inside and not begin_inside:
                # case 1 time_repr: <rr2 - <rr1 - -rr2 > -rr1 >
                self.dr1.rrule._dtstart = self.dr2.start_datetime
                return True

            if begin_inside and not end_inside:
                # case 2 time_repr: <rr1- <rr2- -rr1> -rr2>
                self.dr1.rrule._until = self.dr2.end_datetime
                return True

            if drr_sublapse_of_dcrr:
                # case 3 time_repr: <rr1- <rr2- -rr2> -rr1>
                self.dr1.rrule._dtstart = self.dr2.rrule.dtstart
                self.dr1.rrule._until = self.dr2.end_datetime
                return True

            if drr_end_stick_dcrr:
                # case 4 time_repr: <rr1- -rr1><rr2- -rr2> with same time
                # precision
                if not self.dr2.rrule.until:
                    self.dr1.rrule._until = self.dr2.start_datetime
                else:
                    self.dr1.rrule._until = self.dr2.until
                self.dr1.rrule._count = None
                return True

            if drr_begin_stick_dcrr:
                # case 5 time_repr: <rr2- -rr2><rr1- -rr1> with same time
                # if time is same precision
                self.dr1.rrule._dtstart = self.dr2.rrule.dtstart
                return True
        return more_cohesion


def cohesive_rrules(rrules):
    """Take a list of rrules and try to merge them into more cohesive systems.

    :dur_rrules: list(datection.models.DurationRRule)
    :returns: list(datection.models.DurationRRule)

    """
    dur_rrules = [DurationRRule(rr) for rr in rrules]
    dur_rrules_to_del = set()

    for examined_dur_rrule in dur_rrules:
        if examined_dur_rrule not in dur_rrules_to_del:
            for cur_dur_rrule in dur_rrules:
                if cur_dur_rrule != examined_dur_rrule:
                    if (DurationRRuleManipulator(
                        examined_dur_rrule, cur_dur_rrule)
                            .more_cohesion_between_rrules()):
                        dur_rrules_to_del.add(cur_dur_rrule)

    dur_rrules = [{
        'duration': r.duration,
        'rrule': makerrulestr(r.rrule.dtstart, end=r.rrule.until, rule=r.rrule)
    } for r in dur_rrules if r not in dur_rrules_to_del]

    return dur_rrules
