# -*- coding: utf-8 -*-
from builtins import range
from datection.models import DurationRRule
from datection.rendering.base import BaseFormatter
from datection.rendering.wrappers import postprocess


class PlaceSummaryFormatter(BaseFormatter):
    """
    Class that handles the short formatting for places.

    Timings are not displayed. Focus on day of week.
    """

    def __init__(self, schedule, locale='fr_FR.UTF8'):
        """"""
        super(PlaceSummaryFormatter, self).__init__(locale)
        self.drrs = [DurationRRule(sched) for sched in schedule]

    def get_open_weekdays(self):
        """
        """
        open_weekdays = set()
        for drr in self.drrs:
            if drr.is_recurring:
                for w in drr.weekday_indexes:
                    open_weekdays.add(w)
            elif drr.is_continuous or drr.unlimited:
                return list(range(7))

        return open_weekdays

    def display_list(self, weekdays):
        """
        Display a list of abbreviated weekdays in the correct locale

        @param weekdays: list of weekday to display
        """
        sorted_weekdays = sorted(weekdays)
        output = self.day_name(sorted_weekdays[0], abbrev=True)
        if len(sorted_weekdays) > 1:
            for weekday in sorted_weekdays[1:-1]:
                output += u', %s' % self.day_name(weekday, abbrev=True)
            last_weekday = self.day_name(sorted_weekdays[-1], abbrev=True)
            output += u' %s %s' % (self._('and'), last_weekday)
        return output

    def display_with_except(self, weekdays):
        """
        Display 'Every day except #weekday list#' in the correct locale
        Weekdays are abbreviated

        @param weekdays: list of weekday when the place is open
        """
        every_day = self.display_every_day()
        closed_weekdays = [d for d in range(7) if d not in weekdays]
        closed_str = self.display_list(closed_weekdays)
        return u'%s %s %s' % (every_day, self._('except'), closed_str)

    def display_every_day(self):
        """
        Display 'Every day' in the correct locale
        """
        return self._('every day')

    @postprocess(capitalize=True)
    def display(self, *args, **kwargs):
        """
        """
        weekdays = self.get_open_weekdays()
        nb_weekdays = len(weekdays)
        if nb_weekdays == 0:
            return u''
        elif nb_weekdays <= 4:
            return self.display_list(weekdays)
        elif nb_weekdays < 7:
            return self.display_with_except(weekdays)
        else:
            return self.display_every_day()
