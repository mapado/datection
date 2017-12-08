# -*- coding: utf-8 -*-
from builtins import next
import six
from datection.rendering.base import BaseFormatter
from datection.rendering.base import NextDateMixin
from datection.rendering.base import NextChangesMixin
from datection.rendering.exceptions import TooManyMonths
from datection.rendering.date import DateFormatter
from datection.models import DurationRRule
import itertools


class SeoFormatter(BaseFormatter, NextDateMixin, NextChangesMixin):
    """
    Generates SEO friendly human readable dates.
    """

    MAX_MONTHS = 2

    def __init__(self, schedule, locale='fr_FR.UTF8'):
        super(SeoFormatter, self).__init__(locale)
        self._schedule = schedule
        self.schedule = [DurationRRule(drr) for drr in schedule]
        self.schedule = self.deduplicate(self.schedule)
        self.templates = {
            'default': {
                'two_months': u'{month1} {_and} {month2}',
                'full': u'{months} {year}'
            }
        }

    def get_monthyears(self):
        """
        Return a list of datetimes which month and year describe the whole
        schedule.

        If the length of the output list exceeds self.MAX_MONTHS, or if several
        months with different associated years are returned, a TooManyMonths
        exception is raised.
        """
        monthyears = set()
        datetimes, out = [], []
        for drr in self.schedule:
            datetimes.extend([dt for dt in drr])
        monthyear = lambda dt: (dt.month, dt.year)
        for key, group in itertools.groupby(sorted(datetimes), key=monthyear):
            monthyears.add(key)
            out.append(next(group))
            if len(monthyears) > self.MAX_MONTHS:
                raise TooManyMonths

        # Make sure both months have the same year
        if len(out) > 1 and out[0].year != out[1].year:
            raise TooManyMonths
        return out

    def display(self):
        """
        Generates SEO friendly human readable dates in the current locale.
        """
        try:
            dates = self.get_monthyears()
        except TooManyMonths:
            return u''
        if len(dates) == 0:
            return u''
        elif len(dates) == 1:
            date_fmt = DateFormatter(dates[0], self.locale)
            if not six.PY3:
                month_fmt = date_fmt.format_month().decode('utf-8')
            else:
                month_fmt = date_fmt.format_month()
        else:
            month_tpl = self.get_template('two_months')
            if not six.PY3:
                month_fmt = month_tpl.format(
                    month1=DateFormatter(
                        dates[0], self.locale).format_month().decode('utf-8'),
                    _and=self._('and'),
                    month2=DateFormatter(
                        dates[1], self.locale).format_month().decode('utf-8'))
            else:
                month_fmt = month_tpl.format(
                    month1=DateFormatter(
                        dates[0], self.locale).format_month(),
                    _and=self._('and'),
                    month2=DateFormatter(
                        dates[1], self.locale).format_month())
        year_fmt = DateFormatter(dates[0], self.locale).format_year(force=True)
        tpl = self.get_template('full')
        fmt = tpl.format(months=month_fmt, year=year_fmt)
        return fmt
