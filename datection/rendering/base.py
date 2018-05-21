# -*- coding: utf-8 -*-
from builtins import object
import calendar
import datetime
import locale as _locale
import six

from datection.rendering.wrappers import cached_property
import datection.rendering.utils as utils


class BaseFormatter(object):
    """
    Base class for all schedule formatters.
    """
    def __init__(self, locale='fr_FR.UTF8'):
        self.locale = locale
        self.language_code, self.encoding = self.locale.split('.')
        self.templates = None

    @cached_property
    def translations(self):
        """ Return a translation dict using the current locale language """
        lang = self.language_code.split('_')[0]
        mod = __import__('datection.data.' + lang, fromlist=['data'])
        return mod.TRANSLATIONS

    def _(self, key):
        """ Return the translation of the key in the instance language. """
        return self.translations[self.language_code][key]

    def prevert_list(self, list_to_fmt):
        """
        String list of item concat with simple quote
        then final 'and' before last item
        """
        return '%s %s %s' % (
            ', '.join(list_to_fmt[:-1]), self._('and'), list_to_fmt[-1])

    def get_template(self, key=None):
        """
        Return the template corresponding to the instance language
        and key.
        """
        if key is None:
            if self.language_code in self.templates:
                return self.templates[self.language_code]
            else:
                return self.templates['default']
        else:
            if (
                self.language_code in self.templates and
                key in self.templates[self.language_code]
            ):
                return self.templates[self.language_code][key]
            else:
                return self.templates['default'][key]

    # @staticmethod
    def day_name(self, weekday_index, abbrev=False):
        """
        Return the weekday name associated wih the argument index
        using the current locale.
        """
        with utils.TemporaryLocale(_locale.LC_TIME, self.locale):
            if abbrev:
                if six.PY2:
                    return calendar.day_abbr[weekday_index].decode('utf-8')
                else:
                    return calendar.day_abbr[weekday_index]
            if six.PY2:
                return calendar.day_name[weekday_index].decode('utf-8')
            else:
                return calendar.day_name[weekday_index]

    @staticmethod
    def deduplicate(schedule):
        """ Remove any duplicate DurationRRule in the schedule. """
        # Note: list(set(schedule)) does not keep the order in that case
        out = []
        for item in schedule:
            if item not in out:
                out.append(item)
        return out


class NextDateMixin(object):

    @cached_property
    def regrouped_dates(self):
        """
        Convert self.schedule to a start / end datetime list and filter
        out the obtained values outside of the (self.start, self.end)
        datetime range
        """
        if not hasattr(self, 'start'):
            start = utils.get_current_date()
        else:
            start = self.start or utils.get_current_date()  # filter out passed dates

        end = self.end if hasattr(self, 'end') else None
        dtimes = utils.to_start_end_datetimes(self.schedule, start, end)
        # group the filtered values by date
        dtimes = sorted(utils.groupby_date(dtimes), key=lambda x: x[0]["start"])
        return dtimes

    def next_occurence(self):
        """ Return the next date, as a start/end datetime dict. """
        if self.regrouped_dates:
            return self.regrouped_dates[0][0]

    def other_occurences(self):
        """ Return all dates (but the next), as a start/end datetime dict. """
        return len(self.regrouped_dates) > 1

    def other_timings(self):
        """ Returns true if first date has many timings"""
        return (
            self.regrouped_dates and
            len(self.regrouped_dates[0]) > 1
        )


class NextChangesMixin(object):
    """
    Add a next_changes method to output the datetime when the
    display value will change.
    """
    def next_changes(self):
        """ output the value when the display will change """
        if not(hasattr(self, 'next_occurence')):
            return None

        current_date = datetime.datetime.combine(
            utils.get_current_date(), datetime.time())

        next_occurence = self.next_occurence()
        if not next_occurence or 'start' not in next_occurence:
            return None

        start = next_occurence['start']
        current_delta = start - current_date

        if current_delta < datetime.timedelta(0):  # past
            return None
        elif current_delta < datetime.timedelta(1):  # today
            delta = datetime.timedelta(days=-1)
        elif current_delta < datetime.timedelta(2):  # tomorrow
            delta = datetime.timedelta(days=0)
        elif current_delta < datetime.timedelta(7):  # this week
            delta = datetime.timedelta(days=1)
        else:  # in more than in a week
            delta = datetime.timedelta(days=6)

        next_changes = start - delta
        next_changes = next_changes.combine(
            next_changes.date(), datetime.time())

        return next_changes
