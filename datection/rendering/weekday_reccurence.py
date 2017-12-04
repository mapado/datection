# -*- coding: utf-8 -*-
from builtins import range
from datection.rendering.base import BaseFormatter
from datection.rendering.date import DateIntervalFormatter
from datection.rendering.time import TimeIntervalListFormatter
from datection.rendering.wrappers import postprocess
from datection.rendering.utils import get_drr
from datection.rendering.utils import group_recurring_by_day


class WeekdayReccurenceFormatter(BaseFormatter):

    """Formats a weekday recurrence using the current locale."""

    def __init__(self, drr_list, locale='fr_FR.UTF8'):
        super(WeekdayReccurenceFormatter, self).__init__(locale)
        self.drr_list = [get_drr(drr) for drr in drr_list]
        self.drr = self.drr_list[0]
        self.templates = {
            'de_DE': {
                'interval': u'{start_weekday} - {end_weekday}',
            },
            'ru_RU': {
                'interval': u'{start_weekday} - {end_weekday}',
            },
            'default': {
                'one_day': u'{prefix} {weekday}',
                'interval': u'{_from} {start_weekday} {_to} {end_weekday}',
                'weekday_reccurence': u'{weekdays}, {dates}, {time}',
            }
        }

    def all_weekdays(self):
        """Return True if the RRule describes all weekdays."""
        return self.drr.weekday_indexes == list(range(7))

    def format_weekday_interval(self):
        """Format the rrule weekday interval using the current locale."""
        if self.all_weekdays():
            return u''
        elif len(self.drr.weekday_indexes) == 1:
            template = self.get_template('one_day')
            weekday = self.day_name(self.drr.weekday_indexes[0])
            return template.format(prefix=self._('the'), weekday=weekday)
        else:
            start_idx = self.drr.weekday_indexes[0]
            end_idx = self.drr.weekday_indexes[-1]

            # continuous interval
            # note: to be continuous, the indexes must form a range of
            # more than 2 items, otherwise, we see it as a list
            if (self.drr.weekday_indexes == list(range(start_idx, end_idx + 1)) and
                    start_idx != end_idx - 1):
                template = self.get_template('interval')
                start_weekday = self.day_name(start_idx)
                end_weekday = self.day_name(end_idx)
                fmt = template.format(
                    _from=self._('from_day'),
                    start_weekday=start_weekday,
                    _to=self._('to_day'),
                    end_weekday=end_weekday)
                return fmt
            else:
                # discontinuous interval
                fmt = self._('the') + ' ' + ', '.join(
                    [self.day_name(i) for i in self.drr.weekday_indexes[:-1]])
                fmt += ' %s %s' % (
                    self._('and'), self.day_name(end_idx))
                return fmt

    def format_date_interval(self, no_date=False, *args, **kwargs):
        """ Format the rrule date interval using the current locale. """
        if not self.drr.bounded or no_date:
            return u''
        formatter = DateIntervalFormatter(
            self.drr.start_datetime, self.drr.end_datetime, self.locale)
        return formatter.display(*args, **kwargs)

    def format_time_interval(self):
        """Format the rrule time interval using the current locale."""
        time_intervals = [(drr.start_datetime, drr.end_datetime)
                          for drr in self.drr_list]
        formatter = TimeIntervalListFormatter(time_intervals, self.locale)
        return formatter.display(prefix=True)

    @postprocess(lstrip_pattern=',')
    def display(self, no_date=False, *args, **kwargs):
        """ Display a weekday recurrence using the current locale. """
        template = self.get_template('weekday_reccurence')
        weekdays = self.format_weekday_interval()
        dates = self.format_date_interval(no_date)
        time = self.format_time_interval()

        return template.format(weekdays=weekdays, dates=dates, time=time)


class WeekdayReccurenceGroupFormatter(BaseFormatter):
    """
    Formats the group of weekday recurrence sharing the same date interval
    """

    def __init__(self, drr_list, locale='fr_FR.UTF8'):
        """
        @param drr_list: list(WeeklyRecurences) sharing the same date interval
        """
        super(WeekdayReccurenceGroupFormatter, self).__init__(locale)
        self.drr_list = [get_drr(drr) for drr in drr_list]
        self.drr_grouped_by_days = group_recurring_by_day(self.drr_list)

    def display(self, *args, **kwargs):
        """
        Formats the group of weekday recurrence sharing the same date interval
        """
        if len(self.drr_grouped_by_days) == 1:
            fmt = WeekdayReccurenceFormatter(
                self.drr_grouped_by_days[0],
                self.locale)
            return fmt.display()
        else:
            start_date = self.drr_list[0].date_interval[0]
            end_date = self.drr_list[0].date_interval[1]
            date_fmt = DateIntervalFormatter(start_date, end_date, self.locale)
            date_str = date_fmt.display()

            output = date_str + ":\n"
            for rec_grp in self.drr_grouped_by_days:
                fmt = WeekdayReccurenceFormatter(rec_grp, self.locale)
                output += "- %s\n" % fmt.display(no_date=True)

            return output
