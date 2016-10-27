# -*- coding: utf-8 -*-

"""
Module in charge of transforming packing a list of rrule together
"""
from datetime import timedelta
from dateutil.rrule import weekdays

def have_same_timings(drr1, drr2):
    """ 
    Checks if the given drrs have the same timing and duration
    """
    return (
        drr1.duration == drr2.duration and
        drr1.rrule.byhour == drr2.rrule.byhour and
        drr1.rrule.byminute == drr2.rrule.byminute
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
        cont.set_enddate(single.end_datetime.date())


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
        cont1.set_enddate(last_date.date())


def get_first_of_weekly(wrec):
    """
    Returns the first occurence of the weekly rrule
    """
    return next(d.date() for d in wrec if d.weekday() in wrec.weekday_indexes)


def get_last_of_weekly(wrec):
    """
    Returns the last occurence of the weekly rrule
    """
    end_day = wrec.end_datetime.date()
    for i in xrange(7):
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
        return (abs((first2 - first1).days) < 7)

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
        wrec.set_enddate(sing_date)


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
    wrec1.set_enddate(last_date)
    wrec1.set_weekdays([weekdays[d] for d in days])


class RrulePacker(object):

    def __init__(self, input_drrs):
        """"""
        self._input_drrs = input_drrs
        self._single_dates = self.get_single_dates_container()
        self._continuous = self.get_continuous_container()
        self._weekly_rec = self.get_weekly_rec_container()
        self._others = self.get_other_drrs()

    def get_single_dates_container(self):
        """ Gets all the drrs corresponding to single dates """
        return [drr for drr in self._input_drrs if drr.single_date]

    def get_continuous_container(self):
        """ Gets all the drrs corresponding to continuous dates """
        return [drr for drr in self._input_drrs if drr.is_continuous]

    def get_weekly_rec_container(self):
        """ Gets all the drrs corresponding to recurrent dates """
        return [drr for drr in self._input_drrs if drr.is_recurring]

    def get_other_drrs(self):
        """ Gets all other drrs"""
        return [drr for drr in self._input_drrs if not (drr.is_recurring or
                drr.is_continuous or drr.single_date)]

    def pack_sing_sing_into_cont(self):
        """"""
        pass

    def pack_sing_sing_into_wrec(self):
        """"""
        pass

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
                have_same_timings(sing, cont)
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
                have_same_timings(sing, weekly) and
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
                have_same_timings(single, cont) and
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
                have_same_timings(single, weekly) and
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
                elif have_same_days(wrec, wrec2) and are_close(wrec, wrec2):
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

    def pack_rrules(self):
        """
        """
        self.pack_sing_sing_into_cont()
        self.pack_sing_sing_into_wrec()
        self.include_sing_in_cont()
        self.include_sing_in_wrec()
        self.extend_cont_with_sing()
        self.extend_wrec_with_sing()
        self.fusion_cont_cont()
        self.fusion_wrec_wrec()

        return (self._single_dates + 
                self._continuous +
                self._weekly_rec +
                self._others)
