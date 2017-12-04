# -*- coding: utf-8 -*-
"""
Module in charge of removing rrules from other rrules
"""
from builtins import range
from builtins import object
import datection.combine.common as common
from datetime import timedelta
from dateutil.rrule import weekdays
from copy import deepcopy


ONE_DAY = timedelta(days=1)


def remove_sing_from_cont(cont, sing_to_remove):
    """
    Removes a single date from a continuous rrule.
    Returns either:
        - a shortened continuous rrule
        - two continuous rrules resulting from the split of
          the given continuous rrule
    """
    if sing_to_remove.start_datetime.date() == cont.start_datetime.date():
        new_start = sing_to_remove.start_datetime.date() + ONE_DAY
        cont.set_startdate(new_start)
        return [cont]

    elif sing_to_remove.end_datetime.date() == cont.end_datetime.date():
        new_end = sing_to_remove.end_datetime.date() - ONE_DAY
        cont.set_enddate(new_end)
        return [cont]

    else:
        remaining_cont = deepcopy(cont)
        end_cont = sing_to_remove.end_datetime.date() - ONE_DAY
        cont.set_enddate(end_cont)
        start_remaining = sing_to_remove.start_datetime.date() + ONE_DAY
        remaining_cont.set_startdate(start_remaining)
        return [cont, remaining_cont]


def remove_sing_from_wrec(wrec, sing_to_remove):
    """
    Removes a single date from a recurring rrule.
    Returns either:
        - a shortened recurring rrule
        - two recurring rrules resulting from the split of
          the given recurring rrule
    """
    if sing_to_remove.start_datetime.date() == common.get_first_of_weekly(wrec):
        new_start = sing_to_remove.start_datetime.date() + ONE_DAY
        wrec.set_startdate(new_start)
        return [wrec]

    elif sing_to_remove.start_datetime.date() == common.get_last_of_weekly(wrec):
        new_end = sing_to_remove.end_datetime.date() - ONE_DAY
        wrec.set_enddate(new_end)
        return [wrec]

    elif common.has_date_inbetween(sing_to_remove, wrec):
        remaining_wrec = deepcopy(wrec)
        end_cont = sing_to_remove.end_datetime.date() - ONE_DAY
        wrec.set_enddate(end_cont)
        start_remaining = sing_to_remove.start_datetime.date() + ONE_DAY
        remaining_wrec.set_startdate(start_remaining)
        return [wrec, remaining_wrec]

    return [wrec]


def remove_cont_from_cont(cont, cont_to_remove):
    """
    Removes a continuous rrule from another continuous rrule.
    Returns either:
        - a shortened continuous rrule
        - two continuous rrules resulting from the split of
          the given continuous rrule
    """
    if common.has_date_inbetween(cont_to_remove, cont):
        remaining_cont = deepcopy(cont)
        end_cont = common.real_first_date(cont_to_remove) - ONE_DAY
        cont.set_enddate(end_cont)
        start_remaining = common.real_last_date(cont_to_remove) + ONE_DAY
        remaining_cont.set_startdate(start_remaining)
        return [cont, remaining_cont]

    elif cont.start_datetime <= cont_to_remove.end_datetime <= cont.end_datetime:
        new_start = common.real_last_date(cont_to_remove) + ONE_DAY
        cont.set_startdate(new_start)
        return [cont]

    elif cont.start_datetime <= cont_to_remove.start_datetime <= cont.end_datetime:
        new_end = common.real_first_date(cont_to_remove) - ONE_DAY
        cont.set_enddate(new_end)
        return [cont]

    return [cont]


def remove_cont_from_wrec(wrec, cont_to_remove):
    """
    Removes a weekly recurrence from another weekly recurrence.
    Returns either:
        - a shortened weekly recurrence
        - two cweekly recurrences resulting from the split of
          the given weekly recurrence
    """
    return remove_cont_from_cont(wrec, cont_to_remove)


def remove_wrec_from_wrec_begin(wrec, mask_end, remaining_weekdays):
    """
    Removes a weekly recurrence from the beginning of another
    weekly recurrence.

    @param wrec: weekly recurrence to crop
    @param mask_end: end of the weekly recurrence to remove
    @param remaining_weekdays: list of weekdays left after the removal

    Returns two weekly recurrences:
        - one un-touched
        - one with only the remaining weekdays
    """
    remaining_wrec = deepcopy(wrec)
    remaining_wrec.set_enddate(mask_end)
    remaining_wrec.set_weekdays(remaining_weekdays)
    wrec.set_startdate(mask_end + ONE_DAY)
    return [wrec, remaining_wrec]


def remove_wrec_from_wrec_middle(wrec, mask_start, mask_end,
                                 remaining_weekdays):
    """
    Removes a weekly recurrence from the middle of another weekly
    recurrence

    @param wrec: weekly recurrence to crop
    @param mask_start: start of weekly recurrence to remove
    @param mask_end: end of weekly recurrence to remove
    @param remaining_weekdays: list of weekdays left after the removal

    Returns three rrules:
        - one un-touched weekly recurrence(beginning of the original)
        - a weekly recurrence with the remaining weekdays
        - one un-touched weekly recurrence (end of the original)
    """
    remaining_wrec_masked = deepcopy(wrec)
    remaining_wrec_masked.set_startdate(mask_start)
    remaining_wrec_masked.set_enddate(mask_end)
    remaining_wrec_masked.set_weekdays(remaining_weekdays)
    remaining_wrec = deepcopy(wrec)
    remaining_wrec.set_startdate(mask_end + ONE_DAY)
    wrec.set_enddate(mask_start - ONE_DAY)
    return [wrec, remaining_wrec, remaining_wrec_masked]


def remove_wrec_from_wrec_end(wrec, mask_start, remaining_weekdays):
    """
    Removes a weekly recurrence from the end of another
    weekly recurrence.

    @param wrec: weekly recurrence to crop
    @param mask_start: start of the weekly recurrence to remove
    @param remaining_weekdays: list of weekdays left after the removal

    Returns two weekly recurrences:
        - one un-touched
        - one with only the remaining weekdays
    """
    remaining_wrec = deepcopy(wrec)
    remaining_wrec.set_startdate(mask_start)
    remaining_wrec.set_weekdays(remaining_weekdays)
    wrec.set_enddate(mask_start - ONE_DAY)
    return [wrec, remaining_wrec]


def remove_wrec_from_wrec(wrec, wrec_to_remove):
    """
    Removes a weekly recurrence from another weekly recurrence
    """
    exact_mask_wrec = deepcopy(wrec_to_remove)
    wrec_weekdays = set(wrec.weekday_indexes)
    wrec_to_remove_weekdays = set(wrec_to_remove.weekday_indexes)
    days = wrec_weekdays.intersection(wrec_to_remove_weekdays)
    remaining_weekdays = sorted(wrec_weekdays.difference(days))
    remaining_weekdays = [weekdays[d] for d in remaining_weekdays]
    days = [weekdays[d] for d in sorted(days)]
    exact_mask_wrec.set_weekdays(days)

    mask_start = common.get_first_of_weekly(exact_mask_wrec)
    mask_end = common.get_last_of_weekly(exact_mask_wrec)
    wrec_start = common.get_first_of_weekly(wrec)
    wrec_end = common.get_last_of_weekly(wrec)

    # case where there is no weekday left
    if len(remaining_weekdays) == 0:
        if (common.get_first_of_weekly(wrec_to_remove) <= wrec_start and
                wrec_end <= common.get_last_of_weekly(wrec_to_remove)):
            return []
        return remove_cont_from_wrec(wrec, wrec_to_remove)

    if wrec_start <= mask_start <= wrec_end:
        if wrec_start <= mask_end <= wrec_end:
            return remove_wrec_from_wrec_middle(
                wrec, mask_start, mask_end, remaining_weekdays)
        else:
            return remove_wrec_from_wrec_end(
                wrec, mask_start, remaining_weekdays)
    elif wrec_start <= mask_end <= wrec_end:
        return remove_wrec_from_wrec_begin(
            wrec, mask_end, remaining_weekdays)
    else:
        if mask_start <= wrec_start and wrec_end <= mask_end:
            wrec.set_weekdays(remaining_weekdays)
        return [wrec]


def remove_wrec_from_cont_begin(cont, wrec_to_remove, remaining_weekdays):
    """
    Removes a weekly recurrence from the beginning of a continuous rrule

    @param cont: continuous rrule to crop
    @param wrec_to_remove: weekly recurrence to remove
    @param remaining_weekdays: list of weekdays left after the removal

    Returns two rrules:
        - one un-touched continuous rrule
        - a weekly recurrence with the remaining weekdays
    """
    remaining_wrec = deepcopy(wrec_to_remove)
    remaining_wrec.set_startdate(cont.start_datetime.date())
    mask_end = common.get_last_of_weekly(wrec_to_remove)
    remaining_wrec.set_enddate(mask_end)
    remaining_wrec.set_weekdays(remaining_weekdays)
    cont.set_startdate(mask_end + ONE_DAY)
    return [cont, remaining_wrec]


def remove_wrec_from_cont_middle(cont, wrec_to_remove, remaining_weekdays):
    """
    Removes a weekly recurrence from the middle of a continuous rrule

    @param cont: continuous rrule to crop
    @param wrec_to_remove: weekly recurrence to remove
    @param remaining_weekdays: list of weekdays left after the removal

    Returns three rrules:
        - one un-touched continuous rrule (beginning of the original)
        - a weekly recurrence with the remaining weekdays
        - one un-touched continuous rrule (end of the original)
    """
    remaining_wrec = deepcopy(wrec_to_remove)
    remaining_wrec.set_weekdays(remaining_weekdays)
    mask_start = common.get_first_of_weekly(wrec_to_remove)
    mask_end = common.get_last_of_weekly(wrec_to_remove)
    remaining_wrec.set_startdate(mask_start)
    remaining_wrec.set_enddate(mask_end)
    remaining_cont = deepcopy(cont)
    remaining_cont.set_startdate(mask_end + ONE_DAY)
    cont.set_enddate(mask_start - ONE_DAY)
    return [cont, remaining_wrec, remaining_cont]


def remove_wrec_from_cont_end(cont, wrec_to_remove, remaining_weekdays):
    """
    Removes a weekly recurrence from the end of a continuous rrule

    @param cont: continuous rrule to crop
    @param wrec_to_remove: weekly recurrence to remove
    @param remaining_weekdays: list of weekdays left after the removal

    Returns two rrules:
        - one un-touched continuous rrule
        - a weekly recurrence with the remaining weekdays
    """
    remaining_wrec = deepcopy(wrec_to_remove)
    mask_start = common.get_first_of_weekly(wrec_to_remove)
    remaining_wrec.set_startdate(mask_start)
    remaining_wrec.set_enddate(cont.end_datetime.date())
    remaining_wrec.set_weekdays(remaining_weekdays)
    cont.set_enddate(mask_start - ONE_DAY)
    return [cont, remaining_wrec]


def remove_wrec_from_cont_full(cont, wrec_to_remove, remaining_weekdays):
    """
    Removes weekdays from a continuous rrule

    @param cont: continuous rrule to crop
    @param wrec_to_remove: weekly recurrence to remove
    @param remaining_weekdays: list of weekdays left after the removal

    Returns a weekly recurrence with remaining weekdays
    """
    wrec = deepcopy(wrec_to_remove)
    wrec.set_startdate(cont.start_datetime.date())
    wrec.set_enddate(cont.end_datetime.date())
    wrec.set_weekdays(remaining_weekdays)
    return [wrec]


def remove_wrec_from_cont(cont, wrec_to_remove):
    """
    Removes a weekly recurrence from a continuous rrule
    """
    days = set(range(7))
    wrec_weekdays = set(wrec_to_remove.weekday_indexes)
    days = sorted(days.difference(wrec_weekdays))
    remaining_weekdays = [weekdays[d] for d in days]

    mask_start = common.get_first_of_weekly(wrec_to_remove)
    mask_end = common.get_last_of_weekly(wrec_to_remove)
    cont_start = cont.start_datetime.date()
    cont_end = cont.end_datetime.date()

    if cont_start <= mask_start <= cont_end:
        if cont_start <= mask_end <= cont_end:
            return remove_wrec_from_cont_middle(cont, wrec_to_remove,
                                                remaining_weekdays)
        else:
            return remove_wrec_from_cont_end(cont, wrec_to_remove,
                                             remaining_weekdays)
    elif cont_start <= mask_end <= cont_end:
        return remove_wrec_from_cont_begin(cont, wrec_to_remove,
                                           remaining_weekdays)
    else:
        if mask_start <= cont_start and cont_end <= mask_end:
            return remove_wrec_from_cont_full(cont, wrec_to_remove,
                                              remaining_weekdays)
        return [cont]


class RruleRemover(object):

    def __init__(self, drrs):
        """
        """
        self._input_drrs = drrs
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
        """ Gets all other drrs """
        return [drr for drr in self._input_drrs if not (drr.is_recurring or
                drr.is_continuous or drr.single_date)]

    def add_drrs(self, drr_list):
        """
        Dispatch de DurationRRules from drr_list to
        the correct container.
        """
        for drr in drr_list:
            if drr.single_date:
                self._single_dates.append(drr)
            elif drr.is_continuous:
                self._continuous.append(drr)
            elif drr.is_recurring:
                self._weekly_rec.append(drr)
            else:
                self._others.append(drr)

    def _generic_remove(self, container_name, handle_remove, drr_to_remove):
        """
        Generic method to remove a DurationRRule from a DurationRRules
        container.

        @param container_name: name of the container to go through
        @param drrs_to_remove: DurationRRule to remove
        @param handle_remove: function that returns true if a rrule
                              matches the rrule to remove and the result
                              of the removal.
        """
        idxs_to_remove = set()
        drrs_to_add = []
        container = getattr(self, container_name)
        for idx, drr in enumerate(container):
            match, generated = handle_remove(drr, drr_to_remove)
            if match:
                idxs_to_remove.add(idx)
                drrs_to_add.extend(generated)
        remaining_drrs = [drr for idx, drr in enumerate(container)
                          if idx not in idxs_to_remove]
        setattr(self, container_name, remaining_drrs)
        self.add_drrs(drrs_to_add)

    def remove_sing_from_sings(self, sing_to_remove):
        """
        Removes the given single dates from the single dates list
        """
        def handle_sing_sing(sing, sing_to_remove):
            return common.is_same_sing(sing, sing_to_remove), []

        self._generic_remove('_single_dates', handle_sing_sing, sing_to_remove)

    def remove_sing_from_conts(self, sing_to_remove):
        """
        Removes the given single dates from the continuous rrules list
        """
        def handle_sing_cont(cont, sing_to_remove):
            if common.is_sing_in_cont(sing_to_remove, cont):
                return True, remove_sing_from_cont(cont, sing_to_remove)
            return False, []

        self._generic_remove('_continuous', handle_sing_cont, sing_to_remove)

    def remove_sing_from_wrecs(self, sing_to_remove):
        """
        Removes the given single dates from the recurring rrules list
        """
        def handle_sing_wrec(wrec, sing_to_remove):
            if common.is_sing_in_wrec(sing_to_remove, wrec):
                return True, remove_sing_from_wrec(wrec, sing_to_remove)
            return False, []

        self._generic_remove('_weekly_rec', handle_sing_wrec, sing_to_remove)

    def remove_cont_from_sings(self, cont_to_remove):
        """
        Removes the given continuous rrule from the single dates list
        """
        def handle_cont_sing(sing, cont_to_remove):
            return common.is_sing_in_cont(sing, cont_to_remove), []

        self._generic_remove('_single_dates', handle_cont_sing, cont_to_remove)

    def remove_cont_from_conts(self, cont_to_remove):
        """
        Removes the given continuous rrule from the continuous rrules list
        """
        def handle_cont_cont(cont, cont_to_remove):
            if common.is_cont_inside_cont(cont, cont_to_remove):
                return True, []
            elif common.are_conts_overlapping(cont_to_remove, cont):
                return True, remove_cont_from_cont(cont, cont_to_remove)
            return False, []

        self._generic_remove('_continuous', handle_cont_cont, cont_to_remove)

    def remove_cont_from_wrecs(self, cont_to_remove):
        """
        Removes the given continuous rrule from the recurring rrules list
        """
        def handle_cont_wrec(wrec, cont_to_remove):
            if common.is_wrec_inside_cont(wrec, cont_to_remove):
                return True, []
            elif common.are_cont_and_wrec_overlapping(cont_to_remove, wrec):
                return True, remove_cont_from_wrec(wrec, cont_to_remove)
            return False, []

        self._generic_remove('_weekly_rec', handle_cont_wrec, cont_to_remove)

    def remove_wrec_from_sings(self, wrec_to_remove):
        """
        Removes the given recurring rrule from the single dates list
        """
        def handle_wrec_sing(sing, wrec_to_remove):
            return common.is_sing_in_wrec(sing, wrec_to_remove), []

        self._generic_remove('_single_dates', handle_wrec_sing, wrec_to_remove)

    def remove_wrec_from_conts(self, wrec_to_remove):
        """
        Removes the given recurring rrule from the continuous rrules list
        """
        def handle_wrec_cont(cont, wrec_to_remove):
            if common.are_cont_and_wrec_overlapping(cont, wrec_to_remove):
                return True, remove_wrec_from_cont(cont, wrec_to_remove)
            return False, []

        self._generic_remove('_continuous', handle_wrec_cont, wrec_to_remove)

    def remove_wrec_from_wrecs(self, wrec_to_remove):
        """
        Removes the given recurring rrule from the recurring rrules list
        """
        def handle_wrec_wrec(wrec, wrec_to_remove):
            if common.are_wrecs_overlapping(wrec, wrec_to_remove):
                return True, remove_wrec_from_wrec(wrec, wrec_to_remove)
            return False, []

        self._generic_remove('_weekly_rec', handle_wrec_wrec, wrec_to_remove)

    def remove_rrules(self, drrs_to_remove):
        """
        Entry point to remove rrules

        @param drrs_to_remove: list of DurationRRules to remove
        """
        for drr in drrs_to_remove:
            if drr.single_date:
                self.remove_sing_from_sings(drr)
                self.remove_sing_from_conts(drr)
                self.remove_sing_from_wrecs(drr)
            elif drr.is_continuous:
                self.remove_cont_from_sings(drr)
                self.remove_cont_from_conts(drr)
                self.remove_cont_from_wrecs(drr)
            elif drr.is_recurring:
                self.remove_wrec_from_sings(drr)
                self.remove_wrec_from_conts(drr)
                self.remove_wrec_from_wrecs(drr)

    def get_remaining_rrules(self):
        """
        Returns the remaining DurationRRules
        """
        return (self._single_dates +
                self._continuous +
                self._weekly_rec +
                self._others)
