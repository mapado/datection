# -*- coding: utf-8 -*-

"""
Module in charge of transforming set of rrule + duration object into a
more cohesive rrule set.

"""
from builtins import str
from builtins import range
from builtins import object
from datetime import timedelta, datetime
from copy import deepcopy

from dateutil.rrule import WEEKLY
from dateutil.rrule import DAILY
from dateutil.rrule import rrule
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from datection.timepoint import ALL_DAY
from datection.models import DurationRRule
from datection.utils import makerrulestr

MAX_DRRULES_QTE = 500
DAYS_IN_YEAR = 365
TIME_DISTANCE_ACCEPTABLE = 30 * 6


class TooManyDrrulesError(Exception):

    """Exception raised when a schedule contains too many rrules."""
    pass


def cohesive_rrules(drrules, created_at=None):
    """ Take a rrule set and try to merge them into more cohesive rrule set.

    :rrules: list(dict()) containing duration rrule in string format
                          foreach dict.
    :returns: list(dict()) containing duration rrule in string format
                          foreach dict.

    """
    return CohesiveDurationRRuleLinter(drrules, created_at=created_at)()


def cleanup_drrule(drrules):
    """ Use property beginning with underscore to regenerate rrule. """
    def gen_drrule_dict(dr):
        dstart = dr.start_datetime
        dend = dr.end_datetime
        # following avoid error at datection.display
        if ((dstart and dstart.year == 1000)
                or (dstart and dend
                    and dstart + timedelta(days=DAYS_IN_YEAR) < dend)):
            dstart = datetime.now()
            dend = datetime.now() + timedelta(days=DAYS_IN_YEAR)
            dstart = dstart.replace(
                hour=0, minute=0, second=0, microsecond=0)
            dend = dend.replace(
                hour=0, minute=0, second=0, microsecond=0)
            if dr.rrule._freq == DAILY:
                dr.rrule._freq = WEEKLY
                dr.rrule._byweekday = (0, 1, 2, 3, 4, 5, 6)

        if dstart and dend and dstart + timedelta(days=1) > dend:
            dr.rrule._count = 1
            dend = None
        else:
            dr.rrule._count = 0

        rr = rrule(
            dtstart=dstart,
            until=dend,
            freq=dr.rrule._freq,
            interval=dr.rrule._interval,
            wkst=dr.rrule._wkst,
            count=dr.rrule._count,
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
                dstart, end=dend, freq=rr._freq, rule=rr),
            'duration': dr.duration,
        }
    return [gen_drrule_dict(dr) for dr in drrules]


def drrule_analysers_to_dict_drrules(drrules):
    """ Build clean list of dict rrules from DurationRRuleAnalyser objects."""
    drrules = cleanup_drrule(drrules)
    # ensure uniqueness
    return list({str(drr['duration']) + drr['rrule']: drr for drr in drrules}.values())


def contains(small, big):
    """ Check a list of items is contained in a larger list. """
    for i in range(len(big) - len(small) + 1):
        for j in range(len(small)):
            if big[i + j] != small[j]:
                break
        else:
            return i, i + len(small)
    return False


class DurationRRuleAnalyser(DurationRRule):

    """ DurationRRuleAnalyser extend duration rrule by adding more
    metadata info and ability to compare with other duration rrule.
    It also manipulate merge from one to another drrule.
    """

    def __unicode__(self):
        """ Return string that uniquely identify the type of rrule.

        Type are based on main fields existance in duration rrule.

        """
        return u" ".join([str(int(x)) for x in [self.has_timelapse, self.has_date,
                              self.has_day, self.has_time]])

    @property
    def has_day(self):
        """ Check if given duration rrule has weekdays occurences. """
        return ((self.rrule._freq == WEEKLY and
            self.rrule._byweekday != (MO, TU, WE, TH, FR, SA, SU)) or
            (self.rrule._byweekday is not None and len(self.rrule._byweekday) > 0))

    @property
    def has_time(self):
        """ Check if given duration rrule precise time. """
        return not ((not self.rrule._byminute or self.rrule._byminute[0] == 0)
                    and (not self.rrule._byhour or self.rrule._byhour[0] == 0)
                    )

    @property
    def has_timelapse(self):
        """ Check if given duration rrule appear in a lapse time.

            !! it supose that duration higher that DAYS_IN_YEAR day are not timelapse
             (we guess this info is false)
        """
        year = timedelta(days=DAYS_IN_YEAR)
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

    def is_everyday(self):
        """ Check a drrule happen every day without specific hour. """
        return (self.start_datetime + timedelta(days=DAYS_IN_YEAR) < self.end_datetime
                and (self.rrule._freq == DAILY
                     or (
                         self.rrule._freq == WEEKLY and
                         self.rrule._byweekday == (MO, TU, WE, TH, FR, SA, SU)
                     ))
                )

    def is_same_time(self, drrule, variation=0):
        """ Check drrule has same time as another DurationRRuleAnalyser."""
        if self.has_time and drrule.has_time:
            var = timedelta(hours=variation)
            s_time = timedelta(hours=self.rrule._byhour[0],
                               minutes=self.rrule._byminute[0])
            dr_time = timedelta(hours=drrule.rrule._byhour[0],
                                minutes=drrule.rrule._byminute[0])
            return s_time <= dr_time and dr_time <= s_time + var

    def is_same(self, drrule_analyser):
        """ Check drrule has same timelapse, date, day, and time if isset."""
        is_same = True
        if self.has_timelapse:
            is_same = is_same and self.is_same_timelapse(drrule_analyser)
        elif drrule_analyser.has_timelapse:
            is_same = False
        if self.has_date:
            is_same = is_same and self.is_same_date(drrule_analyser)
        elif drrule_analyser.has_date:
            is_same = False
        if self.has_day:
            is_same = is_same and self.is_same_weekdays(drrule_analyser)
        elif drrule_analyser.has_day:
            is_same = False
        if self.has_time:
            is_same = is_same and self.is_same_time(
                drrule_analyser, variation=1)
        elif drrule_analyser.has_time:
            is_same = False
        return is_same

    def is_subweekdays_of(self, drrule):
        """ Check drrule has all weekdays contained in self(might be more). """
        return (self.rrule._freq == WEEKLY and drrule.rrule._freq == WEEKLY
                and contains(self.rrule._byweekday, drrule.rrule._byweekday))

    def is_fragment_of(self, drrule_analyser):
        """ Check is drrule is has same time and day facet as self. """
        if not self.is_same(drrule_analyser):
            return (not self.has_date and not self.has_timelapse
                    and ((not self.has_day and not drrule_analyser.has_day)
                         or self.is_subweekdays_of(drrule_analyser))
                    and (not self.has_time or self.is_same_time(drrule_analyser))
                    )

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
                         or (self.rrule._freq == WEEKLY
                             and ((drrule.rrule._freq == WEEKLY
                                   or (drrule.rrule._freq == DAILY
                                       and drrule.rrule._count == 1))
                                  and self.is_same_weekdays(drrule)
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

    def take_time_of(self, drrule, earliest=True):
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
             or self.is_same_time(drrule, variation=1))
                and (not self.has_day or self.is_same_weekdays(drrule))):

            if (self.is_same_timelapse(drrule)
                    or self.is_same_date(drrule)):
                more_cohesion = True

            if drrule.is_sublapse_of(self):
                # case 1 time_repr: <rr1- <rr2- -rr2> -rr1>
                self.rrule._count = None
                more_cohesion = True

            if self.is_sublapse_of(drrule):
                # case 2 time_repr: <rr2- <rr1- -rr1> -rr2>
                self.rrule._count = None
                self.rrule._dtstart = drrule.rrule._dtstart
                self.rrule._until = drrule.end_datetime
                more_cohesion = True

            if self.is_end_stick_begin_lapse_of(drrule):
                # case 3 time_repr: <rr1- -rr1><rr2- -rr2> with same time
                # precision
                self.rrule._count = None
                if not drrule.rrule._until:
                    self.rrule._until = drrule.start_datetime
                else:
                    self.rrule._until = drrule.rrule._until
                more_cohesion = True

            if (self.is_containing_end_lapse_of(drrule)
                    and not self.is_containing_start_lapse_of(drrule)):
                # case 5 time_repr: <rr2 - <rr1 - -rr2 > -rr1 >
                self.rrule._count = None
                self.rrule._dtstart = drrule.start_datetime
                more_cohesion = True

            if (self.is_containing_start_lapse_of(drrule)
                    and not self.is_containing_end_lapse_of(drrule)):
                self.rrule._count = None
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

    def __init__(self, drrules, created_at=None, accept_composition=True):
        self.drrules = [DurationRRuleAnalyser(rr) for rr in list({
            str(drr['duration']) + drr['rrule']: drr
            for drr in drrules
        }.values())]
        self.created_at = created_at
        self.accept_composition = accept_composition

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
            sign = str(rr)
            if not sign in drrules['signature']:
                drrules['signature'][sign] = []
            drrules['signature'][sign].append(rr)
        return drrules

    def avoid_doubles(self):
        """ Aim to generate a Set of duration rrule. """
        kept_rrules = []
        for drrules in list(self.drrules_by['signature'].values()):
            for examinated_drrule in drrules:
                keep_drrule = True
                for cur_drrule in drrules:
                    if (not examinated_drrule is cur_drrule and
                            cur_drrule.is_same(examinated_drrule)):
                        keep_drrule = False
                        if keep_drrule:
                            kept_rrules.append(examinated_drrule)
                            self.drrules = kept_rrules

    def cleanup_weak_drrule(self):
        """
        Example:
            à 20h,
            le jeudi à 20h
            du 15 avril au 20 mars le jeudi à 20h
        Become:
            du 15 avril au 20 mars le jeudi à 20h
        """
        # Delete drrule that happen every day without hour
        # when more specific drrule exist
        exist_specific_drrule = False
        for drr in self.drrules:
            if not drr.is_everyday() and not drr.has_time:
                exist_specific_drrule = True

        consumed_drr = set()
        if exist_specific_drrule:
            for drr in self.drrules:
                if drr.is_everyday() and not drr.has_time:
                    consumed_drr.add(drr)
            self.drrules = [
                drr for drr in self.drrules if drr not in consumed_drr]

        # Delete drrule that happen too far in time
        # let estimate 6 month is too far
        consumed_drr.clear()
        if self.created_at:
            for drr in sorted(self.drrules, key=lambda x: x.start_datetime,
                              reverse=True):
                if (self.created_at + timedelta(days=TIME_DISTANCE_ACCEPTABLE) < drr.start_datetime
                        and len(consumed_drr) + 1 != len(self.drrules)):
                    consumed_drr.add(drr)
            self.drrules = [
                drr for drr in self.drrules if drr not in consumed_drr]

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

        # Delete drrule that exist as part as another one.
        consumed_drr = set()
        for drr in self.drrules:
            if drr not in consumed_drr:
                for cdrr in self.drrules:
                    if (drr is not cdrr
                            and cdrr not in consumed_drr
                            and drr.is_fragment_of(cdrr)):
                        consumed_drr.add(drr)
        self.drrules = [drr for drr in self.drrules if drr not in consumed_drr]

        # more sofisticated drrule
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

    def normalise(self):
        """ Normalise each drrule to be more consistant by itself. """
        for drr in self.drrules:
            if (drr.duration == ALL_DAY and drr.has_time):
                drr.duration_rrule['duration'] = 0
            if (drr.duration == 0 and not drr.has_time):
                drr.duration_rrule['duration'] = ALL_DAY

            if (drr.rrule._byweekday is not None) and len(drr.rrule._byweekday) > 0:
                drr.rrule._freq = WEEKLY
            if drr.rrule._byweekday == (MO, TU, WE, TH, FR, SA, SU):
                drr.rrule._freq = DAILY
                drr.rrule._byweekday = ()

    def __call__(self):
        """Lint a list of DurationRRule and transform it to a set of
        more cohesive one."""
        self.normalise()
        self.cleanup_weak_drrule()
        if len(self.drrules) > MAX_DRRULES_QTE:
            raise TooManyDrrulesError()
        self.avoid_doubles()
        self.merge()

        # Check nbr of occurences of root
        roots = self.drrules_by['has_timelapse'] + self.drrules_by['has_date']
        if len(roots) == 1 and self.drrules > 1 and self.accept_composition:
            # if one generate all
            self.make_drrule_compositions(roots[0])

        #
        consumed_drrule = []
        drr_ti = self.drrules_by['has_only_time']
        if len(drr_ti) == 1:
            drr_days = self.drrules_by['has_only_days']
            drrti = drr_ti[0]
            for drr in drr_days:
                drrti.take_weekdays_of(drr)
                consumed_drrule.append(drr)

        self.drrules = [drr for drr in self.drrules
                        if drr not in consumed_drrule]

        return drrule_analysers_to_dict_drrules(self.drrules)
