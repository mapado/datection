# -*- coding: utf-8 -*-
from datection.rendering.base import BaseFormatter
from datection.rendering.base import NextDateMixin
from datection.rendering.base import NextChangesMixin
from datection.rendering.exclusion import ExclusionFormatter
from datection.rendering.long import LongFormatter
from datection.rendering.wrappers import cached_property
from datection.rendering.wrappers import postprocess
from datection.models import DurationRRule


class FullFormatter(BaseFormatter, NextDateMixin, NextChangesMixin):
    """
    Displays a schedule in the current locale without trying to use
    as few characters as possible.
    """
    def __init__(self, schedule, locale='fr_FR.UTF8', apply_exlusion=True):
        super(FullFormatter, self).__init__(locale)
        self._schedule = schedule
        self.schedule = [
            DurationRRule(drr, apply_exlusion) for drr in schedule]
        self.schedule = self.deduplicate(self.schedule)
        self.schedule = self.filter_non_informative(self.schedule)

    @cached_property
    def excluded(self):
        return [drr for drr in self.schedule if drr.exclusion_rrules]

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

    @postprocess(strip=False, trim_whitespaces=False, rstrip_pattern=',')
    def display(self, *args, **kwargs):
        """
        Return a human readable string describing self.schedule as shortly
        as possible(without using abbreviated forms), in the right language.
        """
        out = []
        kwargs['force_year'] = True

        # format rrules having an exclusion pattern
        for exc in self.excluded:
            out.append(ExclusionFormatter(exc, self.locale).display(*args, **kwargs))
        exclusion_out = self.format_output(out)

        no_exclusion = [drr.duration_rrule for drr in self.schedule if not drr.exclusion_rrules]
        other_out = LongFormatter(no_exclusion, self.locale).display(*args, **kwargs)

        output = [exclusion_out, other_out]
        output = [s for s in output if s != ""]
        return "\n".join(output)

    @staticmethod
    def format_output(lines):
        """Capitalize each line."""
        return '\n'.join([line.capitalize() for line in lines])

    def next_changes(self):
        """Return None, as a LongFormatter display output never varies."""
        return None
