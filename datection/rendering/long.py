# -*- coding: utf-8 -*-
from builtins import zip
from collections import defaultdict

from datection.models import DurationRRule
from datection.rendering.base import BaseFormatter
from datection.rendering.base import NextDateMixin
from datection.rendering.base import NextChangesMixin
from datection.rendering.date import DateIntervalFormatter
from datection.rendering.date import DateListFormatter
from datection.rendering.time import TimePatternFormatter
from datection.rendering.date_time import ContinuousDatetimeIntervalFormatter
from datection.rendering.date_time import DatetimeIntervalFormatter
from datection.rendering.weekday_reccurence import WeekdayReccurenceFormatter
from datection.rendering.weekday_reccurence import WeekdayReccurenceGroupFormatter
from datection.rendering.wrappers import cached_property
from datection.rendering.wrappers import postprocess
import datection.rendering.utils as utils
from datection.timepoint import DAY_START
from datection.timepoint import DAY_END
from datection.combine.split import split_short_continuous_schedules


class LongFormatter(BaseFormatter, NextDateMixin, NextChangesMixin):
    """
    Displays a schedule in the current locale without trying to use
    as few characters as possible.
    """
    def __init__(self, schedule, locale='fr_FR.UTF8',
                 apply_exlusion=True, format_exclusion=True):
        super(LongFormatter, self).__init__(locale)
        self._schedule = schedule
        self.schedule = split_short_continuous_schedules(schedule)
        self.schedule = [
            DurationRRule(drr, apply_exlusion) for drr in self.schedule]
        self.schedule = self.deduplicate(self.schedule)
        self.schedule = self.filter_non_informative(self.schedule)
        self.format_exclusion = format_exclusion
        self.templates = {
            'default': u'{dates} {time}',
        }

    @cached_property
    def recurring(self):
        """Select recurring rrules from self.schedule"""
        return [drr for drr in self.schedule if drr.is_recurring]

    @cached_property
    def bounded_recurrings(self):
        """Select recurring rrules from self.schedule"""
        return [drr for drr in self.schedule if drr.is_recurring and
                drr.has_end]

    @cached_property
    def unlimited_recurrings(self):
        """Select recurring rrules from self.schedule"""
        return [drr for drr in self.schedule if drr.is_recurring and
                not drr.has_end]

    @cached_property
    def multidays_single_dates(self):
        """"""
        return [drr for drr in self.schedule if drr.single_date_on_multiple_days]

    @cached_property
    def non_special(self):
        """
        Return all the non-continuous, non-recurring, non-excluded
        DurationRRule objects.
        """
        return [drr for drr in self.schedule
                if not drr.is_continuous
                if not drr.is_recurring
                if not drr.single_date_on_multiple_days
                if not (drr.exclusion_rrules and drr.apply_exclusion)]

    @cached_property
    def continuous(self):
        """Select continuous rrules from self.schedule."""
        return [drr for drr in self.schedule if drr.is_continuous]

    @cached_property
    def excluded(self):
        return [drr for drr in self.schedule if drr.exclusion_rrules]

    @cached_property
    def time_groups(self):
        """Non recurring rrules grouped by start / end datetimes"""
        _time_groups = utils.to_start_end_datetimes(self.non_special)
        # convert rrule structures to start/end datetime lists
        _time_groups = utils.groupby_time(_time_groups)
        for group in _time_groups:
            group.sort(key=lambda date: date['start'])
        return _time_groups

    @cached_property
    def conseq_groups(self):
        """Group each time group by consecutivity"""
        _conseq_groups = []
        for group in self.time_groups:
            conseq = utils.groupby_consecutive_dates(group)
            _conseq_groups.append(conseq)
        return _conseq_groups

    @staticmethod
    def _filterby_year_and_month(dates, year, month):
        """ Return all dates in dates occuring at argument year and month """
        return [date for date in dates
                if date['start'].year == year
                if date['start'].month == month]

    def filter_non_informative(self, schedules):
        """
        Removes schedules which do not add any information to the
        schedule list. (e.g: more vague than the others).

        @param schedules: list(DurationRRule)
        """
        output = schedules
        has_time_lvl_schedule = any([sched for sched in output if
                                     sched.has_timings])

        if has_time_lvl_schedule:
            output = [sched for sched in output if sched.has_timings]

        return output

    def format_single_dates_and_interval(self, conseq_groups, *args, **kwargs):
        """
        First formatting technique, using dates interval

        This formatting technique uses self.consecutive_groups,
        and displays single dates using the self.format_date method
        and date intervals using the format_date_interval method.

        Example:
            [[15 mars 2013], [17 mars 2013, 18 mars 2013]]
        Output:
            u"le 15 mars 2013, du 17 au 18 mars 2013"
        """
        kwargs['force_year'] = True
        out = []
        for conseq in conseq_groups:
            start, end = conseq[0]['start'], conseq[-1]['end']
            fmt = DateIntervalFormatter(
                start, end, self.locale).display(*args, **kwargs)
            out.append(fmt)
        return out

    def format_date_list(self, time_group, *args, **kwargs):
        """
        Second formatting technique, using non - consecutive dates lists

        All the non-consecutive dates are first grouped by years and then by
        months, and returned as a simple list of human readable time
        expressions, expressed in self.lang.

        Example:
        Input:
            [1 mars 2013, 4 mars 2013, 6 juin 2013, 5 juillet 2014]
        Output:
            u"le 1er, 4 mars 2013, le 6 juin 2013, le 5 juillet 2014"
        """
        out = []
        kwargs['force_year'] = True
        # group the sparse dates by year first
        years = list(set([date['start'].year for date in time_group]))
        for year in years:
            # now group the dates by month
            months = sorted(set([date['start'].month for date in time_group
                                 if date['start'].year == year]))

            # all dates happen in the same month
            for month in months:
                mdates = self._filterby_year_and_month(time_group, year, month)
                mdates = [d['start'] for d in mdates]
                fmt = DateListFormatter(
                    mdates, self.locale).display(*args, **kwargs)
                out.append(fmt)
        return out

    def group_by_common_pattern_except_time(self):
        """ Will be in use with """
        common_pattern_dict = defaultdict(list)
        same_patterns_with_different_times = []
        others = []

        for time_grp, conseq_grps in zip(self.time_groups, self.conseq_groups):
            hash_key = utils.hash_same_date_pattern(time_grp)
            common_pattern_dict[hash_key].append((time_grp, conseq_grps))

        for _, time_conseq_grp_tup_list in sorted(common_pattern_dict.items()):
            if len(time_conseq_grp_tup_list) == 1:
                others.extend(time_conseq_grp_tup_list)
            else:
                same_patterns_with_different_times.append(
                    time_conseq_grp_tup_list)

        return (same_patterns_with_different_times, others)

    def _helper_date_fmt(self, time_group, conseq_groups, *args, **kwargs):
        """
        Get human readable date given list of datetime group

        :time_group: [{'start': datetime(), 'end': datetime()},]
        :conseq_groups: [{'start': datetime(), 'end': datetime()},]

        :return: date format string
        """
        date_list = self.format_date_list(time_group, *args, **kwargs)
        list_fmt = ', '.join(date_list)
        if len(date_list) > 1:
            list_fmt += ','

        date_conseq = self.format_single_dates_and_interval(
            conseq_groups, *args, **kwargs)
        conseq_fmt = ', '.join(date_conseq)
        if len(date_conseq) > 1:
            conseq_fmt += ','

        # pick shortest render
        return utils.get_shortest(list_fmt, conseq_fmt)

    def _helper_time_fmt(self, time_group):
        """
        Get human readable time given list of datetime group

        :time_group: [{'start': datetime(), 'end': datetime()},]

        :return: time format string
        """
        start_time, end_time = time_group[0].get("start"), time_group[0].get("end")
        return TimePatternFormatter(
            start_time, end_time, self.locale).display(prefix=True)


    def should_include_dayname(self, same_patterns_with_different_dates, others, **kwargs):
        """
        """
        # get nb of days ouput, if <2 display dayname
        nbdates = 0
        for dates in others:
            timespanlist = utils.groupby_consecutive_dates(dates[0])
            for timespan in timespanlist:
                if len(timespan) > 1:
                    nbdates += 2
                else:
                    nbdates += 1
        nbdates += len(same_patterns_with_different_dates)
        if nbdates < 3 and 'include_dayname' not in kwargs:
            return  True

        return False


    def format_continuous_rrules(self, *args, **kwargs):
        """
        """
        out = []
        # format continuous rrules
        for con in self.continuous:
            continuous_kwargs = kwargs.copy()
            if 'include_dayname' not in continuous_kwargs:
                continuous_kwargs['include_dayname'] = True
            start, end = con.start_datetime, con.end_datetime
            if start.time() == DAY_START and end.time() == DAY_END:
                out.append(DateIntervalFormatter(
                    start, end, self.locale).display(*args, **continuous_kwargs))
            else:
                out.append(DatetimeIntervalFormatter(
                    start, end, self.locale).display(*args, **continuous_kwargs))
        return out

    def format_multidays_single_dates(self, *args, **kwargs):
        """
        """
        out = []

        for multidays_sing in self.multidays_single_dates:
            start, end = multidays_sing.start_datetime, multidays_sing.end_datetime
            out.append(ContinuousDatetimeIntervalFormatter(start, end).display(*args, **kwargs))

        return out

    def format_recurring_rrules(self, *args, **kwargs):
        """
        """
        out = []

        for rec_group in utils.group_recurring_by_day(self.unlimited_recurrings):
            out.append(WeekdayReccurenceFormatter(rec_group, self.locale).
                       display(*args, **kwargs))
        for rec_group in utils.group_recurring_by_date_interval(self.bounded_recurrings):
            out.append(WeekdayReccurenceGroupFormatter(rec_group, self.locale).
                       display(*args, **kwargs))

        return out

    def format_same_pattern_with_different_dates(self, same_patterns_with_different_dates, *args, **kwargs):
        """
        """
        out = []
        template = self.get_template()
        # format non recurring rrules on grouped patterns with different dates
        for time_conseq_grp_tup_list in same_patterns_with_different_dates:
            time_group, conseq_groups = time_conseq_grp_tup_list[0]
            date_fmt = self._helper_date_fmt(time_group, conseq_groups, *args, **kwargs)

            # concatenate dates and time
            time_fmt_list = []
            for time_group, _ in time_conseq_grp_tup_list:
                time_fmt_list.append(self._helper_time_fmt(time_group))

            time_fmt = self.prevert_list(time_fmt_list)

            if time_fmt:
                fmt = template.format(dates=date_fmt, time=time_fmt)
                out.append(fmt)
            else:
                out.append(date_fmt)
        return out

    def format_other_rrules(self, others, *args, **kwargs):
        """
        """
        out = []
        template = self.get_template()

        # format non recurring rrules on grouped patterns with different dates
        for time_group, conseq_groups in others:
            date_fmt = self._helper_date_fmt(time_group, conseq_groups, *args, **kwargs)
            time_fmt = self._helper_time_fmt(time_group)

            if time_fmt:
                fmt = template.format(dates=date_fmt, time=time_fmt)
                out.append(fmt)
            else:
                out.append(date_fmt)

        return out


    @postprocess(strip=False, trim_whitespaces=False, rstrip_pattern=',')
    def display(self, *args, **kwargs):
        """
        Return a human readable string describing self.schedule as shortly
        as possible(without using abbreviated forms), in the right language.
        """
        out = []
        kwargs['force_year'] = True

        out.extend(self.format_recurring_rrules(*args, **kwargs))
        out.extend(self.format_continuous_rrules(*args, **kwargs))
        out.extend(self.format_multidays_single_dates(*args, **kwargs))

        same_patterns_with_different_dates, others = self.group_by_common_pattern_except_time()

        if self.should_include_dayname(same_patterns_with_different_dates, others, **kwargs):
            kwargs['include_dayname'] = True

        out.extend(self.format_same_pattern_with_different_dates(
            same_patterns_with_different_dates, *args, **kwargs))

        out.extend(self.format_other_rrules(others, *args, **kwargs))

        # finally, apply global formatting rules
        return self.format_output(out)

    @staticmethod
    def format_output(lines):
        """Capitalize each line."""
        return '\n'.join([line.capitalize() for line in lines])

    def next_changes(self):
        """Return None, as a LongFormatter display output never varies."""
        return None
