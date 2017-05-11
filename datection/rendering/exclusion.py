# -*- coding: utf-8 -*-
from datection.rendering.base import BaseFormatter
from datection.rendering.time import TimeIntervalFormatter
from datection.rendering.date import DateFormatter
from datection.rendering.long import LongFormatter
from datection.models import DurationRRule


class ExclusionFormatter(BaseFormatter):
    """
    Render exclusion rrules into a human readabled format.
    """
    def __init__(self, excluded, locale='fr_FR.UTF8'):
        super(ExclusionFormatter, self).__init__(locale)
        self.excluded = excluded
        self.templates = {
            'fr_FR': {
                'weekday': u'le {weekday}',
                'weekdays': u'le {weekdays} et {last_weekday}',
                'weekday_interval': u'du {start_weekday} au {end_weekday}',
                'date': u'le {date}',
            },
            'en_US': {
                'weekday': u'{weekday}',
                'weekdays': u'{weekdays} and {last_weekday}',
                'weekday_interval': u'from {start_weekday} to {end_weekday}',
                'date': u'{date}',
            },
        }

    def display_exclusion(self, excluded):
        """
        Render the exclusion rrule into a human-readable format.

        The rrule can either define weekdays or a single date(time).
        """
        excluded_rrule = excluded.exclusion_rrules[0]
        result = ""
        # excluded recurrent weekdays
        if excluded_rrule._byweekday:
            result = self.display_excluded_weekdays(excluded_rrule)
        # excluded date(time)
        else:
            result = self.display_excluded_date(
                rrule=excluded.duration_rrule['excluded'][0],
                duration=excluded.duration)

        return result

    def display_excluded_date(self, rrule, duration):
        """
        Render the excluded date into a human readable format.

        The excluded date can either be a date or a datetime, but the
        time will not be formated, as it's already present in the
        constructive pattern formatting.
        """
        drr = DurationRRule({
            'rrule': rrule,
            'duration': duration
        })
        fmt = DateFormatter(drr.date_interval[0], self.locale)
        return fmt.display(prefix=True)

    def display_excluded_weekdays(self, excluded):
        """
        Render the excluded weekdays into a human-readable format.

        The excluded weekdays can be a single weekday, a weekday interval
        or a weekday list.
        """
        # single excluded recurrent weekday
        if (excluded._byweekday is not None) and len(excluded._byweekday) == 1:
            return self.get_template('weekday').format(
                weekday=self.day_name(excluded._byweekday[0]))
        else:
            indices = set([bywk.weekday() for bywk in excluded])
            indices = sorted(list(indices))
            # excluded day range
            if indices and indices == range(indices[0], indices[-1] + 1):
                return self.get_template('weekday_interval').format(
                    start_weekday=self.day_name(indices[0]),
                    end_weekday=self.day_name(indices[-1]))
            # excluded day list
            else:
                weekdays = u', '.join(self.day_name(i) for i in indices[:-1])
                return self.get_template('weekdays').format(
                    weekdays=weekdays,
                    last_weekday=self.day_name(indices[-1]))

    def display(self, *args, **kwargs):
        """Render an exclusion rrule into a human readable format."""
        # format the constructive pattern
        fmt = LongFormatter(
            schedule=[self.excluded.duration_rrule],
            apply_exlusion=False,
            format_exclusion=False,
            locale=self.locale)
        constructive = fmt.display(*args, **kwargs)
        # format the excluded pattern
        excluded = self.display_exclusion(self.excluded)
        # join the both of them
        return u"{constructive}, {_except} {excluded}".format(
            constructive=constructive,
            _except=self._('except'),
            excluded=excluded)
