# -*- coding: utf-8 -*-
from builtins import range
from datection.rendering.base import BaseFormatter
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
            'de_DE': {
                'weekday_interval': u'{start_weekday} - {end_weekday}',
            },
            'ru_RU': {
                'weekday_interval': u'{start_weekday} - {end_weekday}',
            },
            'default': {
                'weekday': u'{prefix} {weekday}',
                'weekdays': u'{prefix} {weekdays} {_and} {last_weekday}',
                'weekday_interval':
                u'{_from} {start_weekday} {_to} {end_weekday}',
            },
        }

    def display_exclusion(self, excluded):
        """
        Render the exclusion rrule into a human-readable format.

        The rrule can either define weekdays or a single date(time).
        """
        # excluded_rrule = excluded.exclusion_rrules[0]
        result = ""
        # excluded recurrent weekdays
        if all(exclusion._byweekday for exclusion in excluded.exclusion_rrules):
            excluded_weekdays = set(
                wk for exclusion in excluded.exclusion_rrules for wk in exclusion._byweekday)
            result = self.display_excluded_weekdays(list(excluded_weekdays))

        elif excluded.exclusion_rrules[0]._byweekday:
            excluded_weekdays = excluded.exclusion_rrules[0]._byweekday
            result = self.display_excluded_weekdays(excluded_weekdays)
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

    def display_excluded_weekdays(self, excluded_weekdays):
        """
        Render the excluded weekdays into a human-readable format.

        The excluded weekdays can be a single weekday, a weekday interval
        or a weekday list.
        """
        # single excluded recurrent weekday
        if (excluded_weekdays is not None) and len(excluded_weekdays) == 1:
            return self.get_template('weekday').format(
                prefix=self._('the'),
                weekday=self.day_name(excluded_weekdays[0]))
        else:
            indices = sorted(list(excluded_weekdays))
            # excluded day range
            if indices and indices == list(range(indices[0], indices[-1] + 1)):
                return self.get_template('weekday_interval').format(
                    _from=self._('from_day'),
                    start_weekday=self.day_name(indices[0]),
                    _to=self._('to_day'),
                    end_weekday=self.day_name(indices[-1]))
            # excluded day list
            else:
                weekdays = u', '.join(self.day_name(i) for i in indices[:-1])
                return self.get_template('weekdays').format(
                    prefix=self._('the'),
                    weekdays=weekdays,
                    _and=self._('and'),
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
