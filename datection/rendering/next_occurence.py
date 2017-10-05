# -*- coding: utf-8 -*-
from datection.models import DurationRRule
from datection.rendering.base import BaseFormatter
from datection.rendering.base import NextDateMixin
from datection.rendering.base import NextChangesMixin
from datection.rendering.exceptions import NoFutureOccurence
from datection.rendering.date_time import DatetimeIntervalFormatter
from datection.rendering.date import DateFormatter
from datection.rendering.wrappers import postprocess
import datection.rendering.utils as utils


class NextOccurenceFormatter(BaseFormatter, NextDateMixin, NextChangesMixin):
    """
    Object in charge of generating the shortest human readable
    representation of a datection schedule list, using a temporal
    reference.
    """
    def __init__(self, schedule, start, end, locale='fr_FR.UTF8'):
        super(NextOccurenceFormatter, self).__init__(locale)
        self._schedule = schedule
        self.schedule = [DurationRRule(drr) for drr in schedule]
        self.schedule = self.deduplicate(self.schedule)
        self.start, self.end = start, end
        self.templates = {
            'fr_FR': {'more_date': u'{date} + autres dates',
                      'more_timing': u'{date} + autres horaires'},
            'en_US': {'more_date': u'{date} + more dates',
                      'more_timing': u'{date} + more schedules'},
            'de_DE': {'more_date': u'{date} + weitere Termine',
                      'more_timing': u'{date} + mehr Zeitpläne'},
            'es_ES': {'more_date': u'{date} + más fechas',
                      'more_timing': u'{date} + más horarios'},
            'it_IT': {'more_date': u'{date} + altre date',
                      'more_timing': u'{date} + altre orari'},
            'pt_BR': {'more_date': u'{date} + mais datas',
                      'more_timing': u'{date} + mais horários'},
            'nl_NL': {'more_date': u'{date} + meer data',
                      'more_timing': u"{date} + meer schema's"},
            'ru_RU': {'more_date': u'{date} + больше дат',
                      'more_timing': u'{date} + больше расписаний'},
        }

    @postprocess(capitalize=True)
    def display(self, reference, summarize=False, *args, **kwargs):
        """
        Format the schedule next occurence using as few characters
        as possible, using the current locale.
        """
        reference = utils.get_date(reference)
        next_occurence = self.next_occurence()
        if not next_occurence:
            raise NoFutureOccurence
        if utils.all_day(next_occurence['start'], next_occurence['end']):
            formatter = DateFormatter(
                next_occurence['start'], self.locale)
        else:
            formatter = DatetimeIntervalFormatter(
                next_occurence['start'], next_occurence['end'], self.locale)
        date_fmt = formatter.display(
            reference=reference,
            abbrev_reference=self.other_occurences() and summarize,
            *args, **kwargs)
        if summarize and self.other_occurences():
            template = self.get_template('more_date')
            return template.format(date=date_fmt)
        elif summarize and self.other_timings():
            template = self.get_template('more_timing')
            return template.format(date=date_fmt)
        else:
            return date_fmt
