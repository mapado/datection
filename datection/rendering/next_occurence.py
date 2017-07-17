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
            'fr_FR': u'{date} + autres dates',
            'en_US': u'{date} + more dates',
            'de_DE': u'{date} + weitere Termine',
            'es_ES': u'{date} + más fechas',
            'it_IT': u'{date} + più date',
            'pt_BR': u'{date} + mais datas',
            'nl_NL': u'{date} + meer data',
            'ru_RU': u'{date} + больше дат',
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
            template = self.get_template()
            return template.format(date=date_fmt)
        else:
            return date_fmt
