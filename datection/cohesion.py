# -*- coding: utf-8 -*-

"""
Module in charge of transforming set of rrule + duration object into a
more cohesive rrule set.

"""
from datetime import timedelta, datetime
from copy import deepcopy

from dateutil.rrule import WEEKLY
from dateutil.rrule import DAILY
from dateutil.rrule import rrule
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from datection.models import DurationRRule
from datection.utils import makerrulestr


class DurationRRuleAnalyser(DurationRRule):

    """ DurationRRuleAnalyser extend duration rrule by adding more
    metadata info and ability to compare with other duration rrule.
    It also manipulate merge from one to another drrule.
    """

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
                and self.rrule._byweekday != (MO, TU, WE, TH, FR, SA, SU))

    @property
    def has_time(self):
        """ Check if given duration rrule precise time. """
        return not ((not self.rrule._byminute or self.rrule._byminute[0] == 0)
                    and (not self.rrule._byhour or self.rrule._byhour[0] == 0)
                    )

    @property
    def has_timelapse(self):
        """ Check if given duration rrule appear in a lapse time.

            !! it supose that duration higher that 365 day are not timelapse
             (we guess this info is false)
        """
        year = timedelta(days=365)
        return (self.end_datetime < self.start_datetime + year
                and self.end_datetime >= self.start_datetime - timedelta(days=1))

    @property
    def has_date(self):
        """ Check if given duration rrule appear in a precise date. """
        return (self.rrule._count == 1)

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
                    and self.rrule._count == 1)

    def is_same_weekdays(self, drrule):
        """ Check drrule has same weekday as another DurationRRuleAnalyser. """
        return ((not (self.rrule._freq == WEEKLY and drrule.rrule._freq == DAILY
                      and drrule.rrule._count == 1)
                 or (drrule.end_datetime.weekday() in self.rrule._byweekday))
                and
                (not (self.rrule._freq == WEEKLY and drrule.rrule._freq == WEEKLY)
                 or (self.rrule._byweekday == drrule.rrule._byweekday)))

    def is_same_time(self, drrule):
        """ Check drrule has same time as another DurationRRuleAnalyser."""
        if self.has_time and drrule.has_time:
            return (self.rrule._byhour == drrule.rrule._byhour
                    and self.rrule._byminute == drrule.rrule._byminute)

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
                     or ((self.rrule._freq == DAILY and drrule.rrule._freq == DAILY
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
            self.rrule._byhour = drrule.rrule._byhour
            self.rrule._byminute = drrule.rrule._byminute
            self_endlapsetime = timedelta(hours=self.end_datetime.hour,
                                          minutes=self.end_datetime.minute)
            drrule_endlapsetime = timedelta(hours=drrule.end_datetime.hour,
                                            minutes=drrule.end_datetime.minute)
            return True

    def take_weekdays_of(self, drrule):
        """ Concat weekday of another drrule if frequence is daily
        or weekly and weekly for the other drrule.

        :returns: Boolean days appended

        """
        if (drrule.has_day
            and (not self.has_time or self.is_same_time(drrule))
            and self.rrule._freq in [WEEKLY, DAILY]
            and drrule.rrule._freq == WEEKLY
                and drrule.rrule._byweekday):
            if self.rrule._byweekday:
                self.rrule._byweekday = set(
                    self.rrule._byweekday)
            else:
                self.rrule._byweekday = set()
            self.rrule._byweekday = self.rrule._byweekday.union(
                drrule.rrule._byweekday)
            self.rrule._freq = drrule.rrule._freq
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
                    self.rrule._until = drrule.rrule._until
                more_cohesion = True

            if drrule.is_end_stick_begin_lapse_of(self):
                # case 4 time_repr: <rr2- -rr2><rr1- -rr1> with same time
                # if time is same precision
                self.rrule._dtstart = drrule.rrule._dtstart
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
            'has_days_and_time': [],
            'has_only_time': [],
            'has_only_days': [],
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
            if (rr.has_day and not rr.has_timelapse
                    and not rr.has_date
                    and not rr.has_time):
                drrules['has_only_days'].append(rr)
            if (rr.has_time and not rr.has_timelapse
                    and not rr.has_date
                    and not rr.has_day):
                drrules['has_only_time'].append(rr)
            if (rr.has_time and rr.has_time
                    and not rr.has_timelapse
                    and not rr.has_date):
                drrules['has_days_and_time'].append(rr)
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
                    if (not examinated_drrule is cur_drrule and
                            cur_drrule.is_same(examinated_drrule)):
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

        gen_rrules = []
        # make composition between lonely time and lonely days
        composed_days_time = []
        drr_days = self.drrules_by['has_only_days']
        drr_time = self.drrules_by['has_only_time']

        composed_days_time.extend(self.drrules_by['has_days_and_time'])

        if drr_days and drr_time:
            for drr_day in drr_days:
                for drr_t in drr_time:
                    drr_day_copy = deepcopy(drr_day)
                    drr_day_copy.take_time_of(drr_t)
                    composed_days_time.append(drr_day_copy)
        elif not drr_days and drr_time:
            for drr in drr_time:
                composed_days_time.append(drr)
        elif not drr_time and drr_days:
            for drr in drr_days:
                composed_days_time.append(drr)

        if composed_days_time:
            # if same time and timelapse/date try merge days
            consumed = []
            for cdt in composed_days_time:
                if cdt not in consumed:
                    for ndt in composed_days_time:
                        if (ndt not in consumed and ndt is not cdt
                            and ndt.is_same_time(cdt)
                            and (ndt.is_same_timelapse(cdt)
                                 or (not ndt.has_timelapse and not cdt.has_timelapse))
                                ):
                            cdt.take_weekdays_of(ndt)
                            consumed.append(ndt)

            composed_days_time = [c for c in composed_days_time
                                  if c not in consumed]

            if root.has_time and root.has_day:
                gen_rrules.append(root)
            for drr in composed_days_time:
                root_copy = deepcopy(root)
                root_copy.take_time_of(drr)
                root_copy.take_weekdays_of(drr)
                gen_rrules.append(root_copy)
            self.drrules = gen_rrules

    def __call__(self):
        """Lint a list of DurationRRule and transform it to a set of
        more cohesive one."""
        self.avoid_doubles()
        self.merge()

        # Check nbr of occurences of root
        roots = self.drrules_by['has_timelapse'] + self.drrules_by['has_date']
        if len(roots) == 1 and self.drrules > 1:
            # if one generate all
            self.make_drrule_compositions(roots[0])

        return drrule_analysers_to_dict_drrules(self.drrules)


def cohesive_rrules(drrules):
    """ Take a rrule set and try to merge them into more cohesive rrule set.

    :rrules: list(dict()) containing duration rrule in string format
                          foreach dict.
    :returns: list(dict()) containing duration rrule in string format
                          foreach dict.

    """
    return CohesiveDurationRRuleLinter(drrules)()


def cleanup_drrule(drrules):
    """ Use properity beginning _ that have been modified during cohesion
    process to regenerate rrule.
    """
    def gen_drrule_dict(dr):
        rr = rrule(
            freq=dr.rrule._freq,
            dtstart=dr.rrule._dtstart,
            interval=dr.rrule._interval,
            wkst=dr.rrule._wkst,
            count=dr.rrule._count,
            until=dr.rrule._until,
            bysetpos=dr.rrule._bysetpos,
            bymonth=dr.rrule._bymonth,
            bymonthday=dr.rrule._bymonthday,
            byyearday=dr.rrule._byyearday,
            byeaster=dr.rrule._byeaster,
            byweekno=dr.rrule._byweekno,
            byweekday=dr.rrule._byweekday,
            byhour=dr.rrule._byhour,
            byminute=dr.rrule._byminute,
            cache=False)

        return {
            'rrule': makerrulestr(
                dr.start_datetime,
                end=dr.end_datetime,
                freq=rr.freq,
                rule=rr),
            'duration': dr.duration,
            'span': (0, 0),
        }
    return [
        DurationRRuleAnalyser(gen_drrule_dict(dr))
        for dr in drrules
    ]


def drrule_analysers_to_dict_drrules(drrules):

    drrules = cleanup_drrule(drrules)
    # ensure uniqueness
    gen_drrules = {}
    for drr in drrules:

        dstart = drr.start_datetime
        dend = drr.end_datetime
        # following avoid error at datection.display
        if dstart and dstart.year == 1000:
            dstart = datetime.now()
            dend = datetime.now() + timedelta(days=365)
            dstart = dstart.replace(
                hour=0, minute=0, second=0, microsecond=0)
            dend = dend.replace(
                hour=0, minute=0, second=0, microsecond=0)
        str_rrule = makerrulestr(
            dstart,
            end=dend,
            freq=drr.rrule.freq,
            rule=drr.rrule)
        gen_drrules[str(drr.duration) + str_rrule] = {
            'duration': drr.duration,
            'rrule': str_rrule
        }
    return gen_drrules.values()
