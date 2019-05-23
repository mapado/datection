# -*- coding: utf-8 -*-

"""
Module in charge of transforming packing a list of rrule together
"""
from __future__ import division
from builtins import zip
from builtins import range
from past.utils import old_div
from builtins import object
from datection.models import DurationRRule
from datetime import timedelta
from datetime import datetime
from dateutil.rrule import weekdays
from copy import deepcopy
from collections import defaultdict
from datetime import time


def have_same_timings(drr1, drr2, light_match=False):
    """
    Checks if the given drrs have the same timing and duration
    """
    if light_match and not drr1.has_timings:
        return True

    return (
        drr1.duration == drr2.duration and
        drr1.rrule._byhour == drr2.rrule._byhour and
        drr1.rrule._byminute == drr2.rrule._byminute
    )


def has_date_inbetween(drr1, drr2):
    """
    Checks if drr1 starts between the beginning and the end
    of drr2.
    """
    return (
        drr1.start_datetime >= drr2.start_datetime and
        (drr2.unlimited or drr1.end_datetime <= drr2.end_datetime)
    )


def has_weekday_included(single, weekly):
    """
    Checks if the single date is a day of the week
    contained in the weekly recurrence.
    """
    sing_day = single.start_datetime.weekday()
    weekly_days = weekly.weekday_indexes
    if weekly_days:
        return (sing_day in weekly_days)
    return False


def is_a_day_before(single, cont):
    """
    Checks if the given single rrule starts one day before
    the beginning of the continuous rrule.
    """
    sing_date = single.start_datetime.date()
    cont_date = cont.start_datetime.date()
    return (sing_date == cont_date - timedelta(days=1))


def is_a_day_after(single, cont):
    """
    Checks if the given single rrule starts one day after
    the end of the continuous rrule.
    """
    if cont.bounded:
        sing_date = single.start_datetime.date()
        cont_date = cont.end_datetime.date()
        return (sing_date == cont_date + timedelta(days=1))
    return False


def is_a_week_before(single, weekly):
    """
    Checks if the single rrule occurs during
    the week before the weekly recurrence
    """
    sing_date = single.start_datetime.date()
    week_date = weekly.start_datetime.date()
    if sing_date < week_date:
        return (sing_date + timedelta(days=7) > week_date)
    return False


def is_a_week_after(single, weekly):
    """
    Checks if the single rrule occurs during
    the week after the weekly recurrence
    """
    if weekly.bounded:
        sing_date = single.start_datetime.date()
        week_date = weekly.end_datetime.date()
        if sing_date > week_date:
            return (week_date + timedelta(days=7) > sing_date)
    return False


def are_overlapping(cont1, cont2):
    """
    Checks if the two continuous rrules are overlapping
    """
    if cont1.unlimited and cont2.unlimited:
        return True

    if cont1.unlimited:
        return (cont1.start_datetime <= cont2.end_datetime)

    if cont2.unlimited:
        return (cont2.start_datetime <= cont1.end_datetime)

    if cont1.end_datetime <= cont2.end_datetime:
        return (cont1.end_datetime >= cont2.start_datetime)

    if cont2.end_datetime <= cont1.end_datetime:
        return (cont2.end_datetime >= cont1.start_datetime)

    return False


def are_contiguous(cont1, cont2):
    """
    Checks if one of the continuous begins right after the other
    """
    if cont1.end_datetime.date() == cont2.start_datetime.date() - timedelta(days=1):
        return True
    if cont2.end_datetime.date() == cont1.start_datetime.date() - timedelta(days=1):
        return True
    return False


def extend_cont(single, cont):
    """
    Extends the continuous rrule with the single rrule
    """
    if is_a_day_before(single, cont):
        cont.set_startdate(single.start_datetime.date())
    elif is_a_day_after(single, cont):
        cont.set_enddate(single.end_datetime)


def merge_cont(cont1, cont2):
    """
    Merges the two continuous rrules
    """
    first_date = min(cont1.start_datetime, cont2.start_datetime)
    cont1.set_startdate(first_date.date())
    if cont1.unlimited or cont2.unlimited:
        cont1.set_enddate(None)
    else:
        last_date = max(cont1.end_datetime, cont2.end_datetime)
        cont1.set_enddate(last_date)


def get_first_of_weekly(wrec):
    """
    Returns the first occurence of the weekly rrule
    """
    start_day = wrec.start_datetime.date()
    for i in range(7):
        tmp_date = start_day + timedelta(days=i)
        if tmp_date.weekday() in wrec.weekday_indexes:
            return tmp_date
    return start_day


def get_last_of_weekly(wrec):
    """
    Returns the last occurence of the weekly rrule
    """
    end_day = wrec.end_datetime.date()
    for i in range(7):
        tmp_date = end_day - timedelta(days=i)
        if tmp_date.weekday() in wrec.weekday_indexes:
            return tmp_date
    return end_day


def are_close(wrec1, wrec2):
    """
    Checks if one of the weekly recurrences is the
    continuity of the other
    """
    if wrec1.bounded:
        end_wrec1 = get_last_of_weekly(wrec1)
        start_wrec2 = get_first_of_weekly(wrec2)
        return (end_wrec1 + timedelta(days=7) == start_wrec2)

    if wrec2.bounded:
        end_wrec2 = get_last_of_weekly(wrec2)
        start_wrec1 = get_first_of_weekly(wrec1)
        return (end_wrec2 + timedelta(days=7) == start_wrec1)

    return False


def have_compatible_bounds(wrec1, wrec2):
    """
    Checks if the two weekly recurrences have compatible
    bounds, i.e that their first and last occurences occur
    respectively in a 7 days range.
    """
    first1 = get_first_of_weekly(wrec1)
    first2 = get_first_of_weekly(wrec2)
    delta = abs((first2 - first1).days)

    if delta < 7:
        if wrec1.unlimited or wrec2.unlimited:
            return True
        last1 = get_last_of_weekly(wrec1)
        last2 = get_last_of_weekly(wrec2)
        return (abs((last2 - last1).days) < 7)

    return False


def have_same_days(wrec1, wrec2):
    """
    Checks if the two weekly recurrences have the same
    days of week
    """
    days1 = set(wrec1.weekday_indexes)
    days2 = set(wrec2.weekday_indexes)
    return (days1 == days2)


def extend_wrec(single, wrec):
    """
    Extends the weekly recurrence with the single date
    """
    sing_date = single.start_datetime.date()
    wrec_begin = wrec.start_datetime.date()
    wrec_end = wrec.end_datetime.date()
    if sing_date < wrec_begin:
        wrec.set_startdate(sing_date)
    elif sing_date > wrec_end:
        wrec.set_enddate(single.start_datetime)


def merge_wrec(wrec1, wrec2):
    """
    Merges the two weekly recurrences
    """
    first_date = min(get_first_of_weekly(wrec1), get_first_of_weekly(wrec2))
    last_date = max(get_last_of_weekly(wrec1), get_last_of_weekly(wrec2))
    wrec1_days = set(wrec1.weekday_indexes)
    wrec2_days = set(wrec2.weekday_indexes)
    days = sorted(wrec1_days.union(wrec2_days))
    wrec1.set_startdate(first_date)
    last_datetime = datetime.combine(last_date, wrec1.end_datetime.time())
    wrec1.set_enddate(last_datetime)
    wrec1.set_weekdays([weekdays[d] for d in days])


def break_seq(sing1, sing2, seq_freq):
    """
    Checks if the two given single dates could belong to a sequence.
    seq_freq handles the sequence frequency, e.g seq_freq=1 is for
    continuous sequence and seq_freq=7 is for weekly recurrence
    """
    return (
        not have_same_timings(sing1, sing2) or
        sing1.start_datetime + timedelta(days=seq_freq) != sing2.start_datetime
    )


class RrulePacker(object):

    def __init__(self, input_drrs, pack_no_timings=False):
        """
        input_drrs : list(DurationRRule)
        """
        self._pack_no_timings = pack_no_timings
        self._input_drrs = input_drrs
        self._single_dates = self.get_single_dates_container()
        self._single_dates = sorted(self._single_dates,
                                    key=lambda s: s.start_datetime.date())
        self._single_dates_by_time = defaultdict(list)
        for (idx, sing) in enumerate(self._single_dates):
            self._single_dates_by_time[sing.start_datetime.time()].append((idx, sing))
        self._continuous = self.get_continuous_container()
        self._weekly_rec = self.get_weekly_rec_container()
        self._others = self.get_other_drrs()

    def get_single_dates_container(self):
        """ Gets all the drrs corresponding to single dates """
        return [drr for drr in self._input_drrs if drr.single_date]

    def get_continuous_container(self):
        """ Gets all the drrs corresponding to continuous dates """
        return [drr for drr in self._input_drrs if (drr.is_continuous or
                drr.is_every_day_recurrence) and not drr.single_date]

    def get_weekly_rec_container(self):
        """ Gets all the drrs corresponding to recurrent dates """
        return [drr for drr in self._input_drrs if drr.is_recurring]

    def get_other_drrs(self):
        """ Gets all other drrs """
        return [drr for drr in self._input_drrs if not (drr.is_recurring or
                drr.is_continuous or drr.single_date or
                drr.is_every_day_recurrence)]

    def create_cont_from_sings(self, sing_list):
        """
        Creates a continuous rule based on a list of single dates.
        """
        new_continuous = DurationRRule(sing_list[0].duration_rrule)
        new_continuous.remove_count()
        new_continuous.add_interval_ind()
        new_continuous.add_enddate(sing_list[-1].start_datetime.date())
        return new_continuous

    def create_week_from_sings(self, sing_list):
        """
        Creates a weekly recurrence based on a list of single dates.
        """
        new_weekly = DurationRRule(sing_list[0].duration_rrule)
        new_weekly.remove_count()
        new_weekly.add_enddate(sing_list[-1].start_datetime.date())
        new_weekly.set_frequency('WEEKLY')
        new_weekly.add_weekdays([weekdays[sing_list[0].start_datetime.date().weekday()]])
        return new_weekly

    def merge_sing_dates(self, type_merge, ids, tim):
        """
        Delegates the merge of single dates
        """
        sings_to_merge = [s[1] for i, s in enumerate(self._single_dates_by_time[tim]) if i in ids]

        if type_merge == 'week':
            new_weekly = self.create_week_from_sings(sings_to_merge)
            self._weekly_rec.append(new_weekly)

        elif type_merge == 'cont':
            new_continuous = self.create_cont_from_sings(sings_to_merge)
            self._continuous.append(new_continuous)

        self._single_dates_by_time[tim] = [s for i, s in enumerate(self._single_dates_by_time[tim]) if i not in ids]

    def probe_continuous(self, probe_list, tim):
        """
        Looks for group of single dates that can be merged into continuous rules.

        Returns a dict {type: 'cont', 'ids': [list of mergeable single dates indexes]}
        """
        consecutives = []
        sing_dates = self._single_dates_by_time[tim]
        for idx, (main_idx, sing) in enumerate(sing_dates):
            if (len(consecutives) > 0) and break_seq(sing_dates[idx-1][1], sing,seq_freq=1):
                probe_list.append({'type': 'cont',
                                   'ids': consecutives,
                                   'count': len(consecutives)})
                consecutives = []
            consecutives.append((idx, main_idx))

        if len(consecutives) > 0:
            probe_list.append({'type': 'cont',
                               'ids': consecutives,
                               'count': len(consecutives)})

    def probe_weekly(self, probe_list, tim):
        """
        Looks for group of single dates that can be merged into weekly
        recurrences.

        Returns a dict {type: 'week', 'ids': [list of mergeable single dates indexes]}
        """
        sing_dates = self._single_dates_by_time[tim]
        for day in range(7):
            single_dates = [(i, (main_idx, sing))
                            for i, (main_idx, sing) in enumerate(sing_dates) if
                            sing.start_datetime.date().weekday() == day]

            if len(single_dates) == 0:
                continue

            consecutives = []
            last_idx = single_dates[0][0]
            for idx, (main_idx, sing) in single_dates:
                if (len(consecutives) > 0) and break_seq(sing_dates[last_idx][1], sing, seq_freq=7):
                    probe_list.append({'type': 'week',
                                       'ids': consecutives,
                                       'count': len(consecutives)})
                    consecutives = []
                consecutives.append((idx, main_idx))
                last_idx = idx

            if len(consecutives) > 0:
                probe_list.append({'type': 'week',
                                   'ids': consecutives,
                                   'count': len(consecutives)})
                consecutives = []

    def remove_duplicate_single_dates(self):
        """
        Removes duplicates single dates. Hash(DurationRRule) is not
        sufficient as it only compares the RRULE string and two different
        strings can represent the same DurationRRule.
        """
        def select_best_single_date(sing_idxs_list):
            """
            For a given start_datetime, the best (= most englobing) single date
            is the one with the latest end_datetime
            """
            return max(sing_idxs_list, key=lambda idx: self._single_dates[idx].end_datetime)

        sing_idxs_by_start_datetime = defaultdict(list)
        for idx, sing in enumerate(self._single_dates):
            sing_idxs_by_start_datetime[sing.start_datetime].append(idx)

        idxs_to_keep = set(select_best_single_date(sing_idxs_list) for sing_idxs_list in sing_idxs_by_start_datetime.values())
        self._single_dates = [s for i, s in enumerate(self._single_dates) if i in idxs_to_keep]

    def pack_single_dates(self):
        """
        Packs single dates into continuous or weekly rules depending on
        what merge is the best.
        """
        def select_best_probe(probe_list):
            """ Returns the best probe (in term of merge efficiency) """
            max_probe = max(probe_list, key=lambda x: x['count'])
            max_match = max_probe['count']
            filtered_probes = [p for p in probe_list if p['count'] == max_match]
            filtered_cont = [p for p in filtered_probes if p['type'] == 'cont']
            filtered_week = [p for p in filtered_probes if p['type'] == 'week']

            # preference on weekly recurrence over continuous
            if max_match >= 2:
                if len(filtered_week) > 0 and max_match >= 3:
                    return filtered_week[0]
                elif len(filtered_cont) > 0:
                    return filtered_cont[0]
            return None

        sing_to_remove_idxs = set()
        for tim in list(self._single_dates_by_time.keys()):
            attemptPacking = True
            while attemptPacking and len(self._single_dates_by_time[tim]) > 0:
                attemptPacking = False
                probe_list = []
                self.probe_continuous(probe_list, tim)
                self.probe_weekly(probe_list, tim)
                best_probe = select_best_probe(probe_list)
                if best_probe:
                    tim_idxs, main_idxs = list(zip(*best_probe['ids']))
                    sing_to_remove_idxs.update(main_idxs)
                    self.merge_sing_dates(best_probe['type'],
                                          tim_idxs, tim)
                    attemptPacking = True
        self._single_dates = [s for i, s in enumerate(self._single_dates) if i not in sing_to_remove_idxs]

    def include_sing_in_cont(self):
        """
        Removes single dates that are contained in a continuous
        rule.

        e.g: Removes (13/05/2015) if (from 10/05/2015 to 15/05/2015) exists
        """

        def is_in_continuous(sing, cont):
            """ Returns True if the single date is in the continuous rule """
            return (
                has_date_inbetween(sing, cont) and
                have_same_timings(sing, cont, light_match=self._pack_no_timings)
            )

        idxs_to_remove = set()
        for idx, sing in enumerate(self._single_dates):
            for cont in self._continuous:
                if is_in_continuous(sing, cont):
                    idxs_to_remove.add(idx)

        self._single_dates = [sg for i, sg in enumerate(self._single_dates) if
                              i not in idxs_to_remove]

    def include_sing_in_wrec(self):
        """
        Removes single dates that are contained in a weekly
        recurrence rule.

        e.g: Removes (Tuesday 13/05/2015) if (Every Tuesday) exists
        """

        def is_in_weekly(sing, weekly):
            """ Returns True if the single date is in the weekly recurrence """
            return (
                has_date_inbetween(sing, weekly) and
                have_same_timings(sing, weekly, light_match=self._pack_no_timings) and
                has_weekday_included(sing, weekly)
            )

        idxs_to_remove = set()
        for idx, sing in enumerate(self._single_dates):
            for weekly in self._weekly_rec:
                if is_in_weekly(sing, weekly):
                    idxs_to_remove.add(idx)
        self._single_dates = [sg for i, sg in enumerate(self._single_dates) if
                              i not in idxs_to_remove]

    def find_matching_cont_and_extend(self, single):
        """
        Search for a continuous rrule extendable by the given
        single rrule. Extend it and return True if found.
        """
        def match_cont(single, cont):
            """ Returns True if the single rrule can extend the continuous rrule """
            return (
                not cont.unlimited and
                have_same_timings(single, cont, light_match=self._pack_no_timings) and
                (is_a_day_before(single, cont) or
                 is_a_day_after(single, cont))
            )

        for cont in self._continuous:
            if match_cont(single, cont):
                extend_cont(single, cont)
                return True
        return False

    def find_matching_weekly_and_extend(self, single):
        """
        Search for a recurrent rrule extendable by the given
        single rrule. Extend it and return True if found.
        """
        def match_weekly(single, weekly):
            """ Returns True if the single rrule can extend the recurrent rrule """
            return (
                have_same_timings(single, weekly, light_match=self._pack_no_timings) and
                has_weekday_included(single, weekly) and
                (is_a_week_before(single, weekly) or
                 is_a_week_after(single, weekly))
            )

        for weekly in self._weekly_rec:
            if match_weekly(single, weekly):
                extend_wrec(single, weekly)
                return True
        return False

    def _generic_extend_with_single(self, find_and_extend_func):
        """
        Generic method to extend continuous/weekly rules with a single
        date.

        @param find_and_extend_func(func): functions that performs
                                           the extension
        """
        attemptPacking = True
        while attemptPacking and len(self._single_dates) > 0:

            attemptPacking = False
            idx_to_remove = None

            for idx, single in enumerate(self._single_dates):
                if find_and_extend_func(single):
                    idx_to_remove = idx
                    break

            if idx_to_remove is not None:
                self._single_dates.pop(idx_to_remove)
                attemptPacking = True

    def extend_cont_with_sing(self):
        """
        Extends continuous rules with single dates

        e.g: (09/05/2015) + (from 10/05/2015 to 15/05/2015)
             => (from 09/05/2015 to 15/05/2015)
        """
        self._generic_extend_with_single(self.find_matching_cont_and_extend)

    def extend_wrec_with_sing(self):
        """
        Extends weekly recurrences with single dates

        e.g: (Tu. 03/05/2015) + (Every Tu. from 10/05/2015 to 15/05/2015)
             => (Every Tueday from 03/05/2015 to 15/05/2015)
        """
        self._generic_extend_with_single(self.find_matching_weekly_and_extend)

    def find_mergeable_cont(self):
        """
        Checks if there are 2 continuous rules that are mergeable. Returns
        their indices if found.
        """

        def are_cont_mergeable(cont, cont2):
            """ Returns True if the two given continuous rrules are mergeable """
            return (
                have_same_timings(cont, cont2) and
                (are_overlapping(cont, cont2) or
                 are_contiguous(cont, cont2))
            )

        for idx, cont in enumerate(self._continuous):
            for idx2, cont2 in enumerate(self._continuous[idx + 1:]):
                if are_cont_mergeable(cont, cont2):
                    return idx, idx+1+idx2
        return None, None

    def fusion_cont_cont(self):
        """
        Fusions mergeable continuous rules

        e.g: (from 10/03 to 15/03) + (from 16/03 to 17/03)
             => (from 10/03 to 17/03)
        """
        attemptPacking = True
        while attemptPacking:
            attemptPacking = False
            idx, idx2 = self.find_mergeable_cont()
            if (idx is not None) and (idx2 is not None):
                merge_cont(self._continuous[idx], self._continuous[idx2])
                self._continuous.pop(idx2)
                attemptPacking = True

    def find_mergeable_wrec(self):
        """
        Checks if there are 2 weekly recurrences that are mergeable. Returns
        their indices if found.
        """

        def are_wrec_mergeable(wrec, wrec2):
            """ Returns True if the two given recurrent rrules are mergeable """
            if have_same_timings(wrec, wrec2):
                if have_compatible_bounds(wrec, wrec2):
                    return True
                elif have_same_days(wrec, wrec2) and (are_close(wrec, wrec2) or are_overlapping(wrec, wrec2)):
                    return True
            return False

        for idx, wrec in enumerate(self._weekly_rec):
            for idx2, wrec2 in enumerate(self._weekly_rec[idx + 1:]):
                if are_wrec_mergeable(wrec, wrec2):
                    return idx, idx+1+idx2
        return None, None

    def fusion_wrec_wrec(self):
        """
        Fusions mergeable weekly recurrences

        e.g: (Every Mo. from 15/02 to 15/03) + (Every Fr. from 15/02 to 15/03)
             => (Every Monday and Friday from 15/02 to 15/03)
        """
        attemptPacking = True

        while attemptPacking:
            attemptPacking = False
            idx, idx2 = self.find_mergeable_wrec()
            if idx is not None and idx2 is not None:
                merge_wrec(self._weekly_rec[idx], self._weekly_rec[idx2])
                self._weekly_rec.pop(idx2)
                attemptPacking = True

    def get_rrules(self):
        """ Returns all DurationRRules """
        return (self._single_dates +
                self._continuous +
                self._weekly_rec +
                self._others)

    def pack_rrules(self):
        """
        """
        self.remove_duplicate_single_dates()
        self.pack_single_dates()
        self.include_sing_in_cont()
        self.include_sing_in_wrec()
        self.extend_cont_with_sing()
        self.extend_wrec_with_sing()
        self.fusion_cont_cont()
        self.fusion_wrec_wrec()

        return self.get_rrules()


def is_gap_small(drr1, drr2, ratio=0.3):
    """
    Checks that the gap between two DurationRRule is small, i.e that
    the ratio (length(gap) / length(full date range)) is below the
    given ratio.

    Assumes there are no overlap between drr1 and drr2 as
    they would have been packed before.
    """
    limits = [drr1.start_datetime, drr1.end_datetime,
              drr2.start_datetime, drr2.end_datetime]
    limits = sorted(limits)
    gap = float((limits[2] - limits[1]).days)
    total = float((limits[3] - limits[0]).days)
    return (old_div(gap, total)) <= ratio


def continuous_gap(continuous1, continuous2):
    """
    Returns a DurationRRule corresponding to the gap between
    continuous1 and continuous2.
    Can be a continuous rrule or a single date

    Assumes there are no overlap between cont1 and cont2 as
    they would have been packed before.
    """
    limits = [continuous1.start_datetime,
              continuous1.end_datetime,
              continuous2.start_datetime,
              continuous2.end_datetime]
    limits = sorted(limits)
    gap = deepcopy(continuous1)
    gap.set_startdate(limits[1].date() + timedelta(days=1))
    gap.set_enddate(limits[2].date() - timedelta(days=1))
    if gap.start_datetime.date() == gap.end_datetime.date():
        gap.set_enddate(None)
        gap.remove_interval_ind()
        gap.add_count()
    return gap


def weekly_recurrence_gap(weekly_recurrence1, weekly_recurrence2):
    """
    Returns a DurationRRule corresponding to the gap between
    weekly_recurrence1 and wrec2.

    Assumes there are no overlap between wrec1 and wrec2 as
    they would have been packed before.
    """
    limits = [weekly_recurrence1.start_datetime,
              weekly_recurrence1.end_datetime,
              weekly_recurrence2.start_datetime,
              weekly_recurrence2.end_datetime]
    limits = sorted(limits)
    gap = deepcopy(weekly_recurrence1)
    gap.add_interval_ind()
    gap.set_frequency('DAILY')
    gap.remove_weekdays()
    gap.set_startdate(limits[1].date() + timedelta(days=1))
    gap.set_enddate(limits[2].date() - timedelta(days=1))
    return gap


class RrulePackerWithGaps(RrulePacker):

    def __init__(self, drrs):
        RrulePacker.__init__(self, drrs)

    def find_mergeable_cont_with_gaps(self):
        """
        Checks if there are 2 continuous rules that are mergeable. Returns
        their indices if found.
        """

        def are_cont_mergeable(cont, cont2):
            """ Returns True if the two given continuous rrules are mergeable """
            return (
                have_same_timings(cont, cont2) and
                is_gap_small(cont, cont2)
            )

        for idx, cont in enumerate(self._continuous):
            for idx2, cont2 in enumerate(self._continuous[idx + 1:]):
                if are_cont_mergeable(cont, cont2):
                    return idx, idx+1+idx2
        return None, None

    def fusion_cont_cont_with_gaps(self):
        """
        Fusions mergeable continuous rules

        e.g: (from 10/02 to 15/03) + (from 25/03 to 10/04)
             => (from 10/02 to 10/04 except from 16/03 to 24/03)
        """
        attemptPacking = True
        while attemptPacking:
            attemptPacking = False
            idx, idx2 = self.find_mergeable_cont_with_gaps()
            if (idx is not None) and (idx2 is not None):
                gap = continuous_gap(
                    self._continuous[idx],
                    self._continuous[idx2])
                merge_cont(self._continuous[idx], self._continuous[idx2])
                self._continuous[idx].add_exclusion_rrule(gap)
                self._continuous.pop(idx2)
                attemptPacking = True

    def find_mergeable_wrec_with_gaps(self):
        """
        Checks if there are 2 weekly recurrences that are mergeable. Returns
        their indices if found.
        """

        def are_wrec_mergeable(wrec, wrec2):
            """ Returns True if the two given recurrent rrules are mergeable """
            return (
                have_same_timings(wrec, wrec2) and
                have_same_days(wrec, wrec2) and
                is_gap_small(wrec, wrec2)
            )

        for idx, wrec in enumerate(self._weekly_rec):
            for idx2, wrec2 in enumerate(self._weekly_rec[idx + 1:]):
                if are_wrec_mergeable(wrec, wrec2):
                    return idx, idx+1+idx2
        return None, None

    def fusion_wrec_wrec_with_gaps(self):
        """
        Fusions mergeable weekly recurrences

        e.g: (Every Mo. from 10/02 to 15/03) + (Every Fr. from 25/03 to 10/04)
             => (Every Monday and Friday from 10/02 to 10/04 except from 16/03 to 24/03)
        """
        attemptPacking = True

        while attemptPacking:
            attemptPacking = False
            idx, idx2 = self.find_mergeable_wrec_with_gaps()
            if idx is not None and idx2 is not None:
                gap = weekly_recurrence_gap(
                    self._weekly_rec[idx],
                    self._weekly_rec[idx2])
                merge_wrec(self._weekly_rec[idx], self._weekly_rec[idx2])
                self._weekly_rec[idx].add_exclusion_rrule(gap)
                self._weekly_rec.pop(idx2)
                attemptPacking = True

    def pack_with_gaps(self):
        """"""
        self.pack_rrules()
        self.fusion_cont_cont_with_gaps()
        self.fusion_wrec_wrec_with_gaps()

        return self.get_rrules()
