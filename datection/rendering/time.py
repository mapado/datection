# -*- coding: utf-8 -*-
from builtins import str
import datetime
from datection.rendering.base import BaseFormatter
from datection.rendering.utils import get_time
from datection.rendering.utils import all_day
from datection.rendering.utils import TemporaryLocale
import locale as _locale


class TimeFormatter(BaseFormatter):

    """ Formats a time using the current locale. """

    def __init__(self, time, locale='fr_FR.UTF8'):
        super(TimeFormatter, self).__init__(locale)
        self.time = get_time(time)
        self.templates = {
            'fr_FR': u'{prefix} {hour} h {minute}',
            'default': u'{prefix} {hour}:{minute}',
        }

    def format_hour(self):
        """ Format the time hour using the current locale. """
        return str(self.time.hour)

    def format_minute(self):
        """ Format the time hour using the current locale. """
        if self.time.minute == 0:
            if self.language_code == 'fr_FR':
                return u''
            elif self.language_code in ['en_US', 'en_GB']:
                return u'00'
        with TemporaryLocale(_locale.LC_TIME, self.locale):
            return self.time.strftime('%M')

    def display(self, prefix=False):
        """
        Format the time using the template associated with the locale
        """
        if self.time == datetime.time(0, 0):
            return self._('midnight')
        template = self.get_template()
        hour = self.format_hour()
        minute = self.format_minute()
        prefix = self._('at') if prefix else ''
        fmt = template.format(prefix=prefix, hour=hour, minute=minute)
        fmt = fmt.strip()
        return fmt


class TimePatternFormatter(BaseFormatter):

    """ Formats a time pattern using the current locale. """

    def __init__(self, start_time, end_time, locale='fr_FR.UTF8'):
        super(TimePatternFormatter, self).__init__(locale)
        self.start_time = get_time(start_time)
        self.end_time = get_time(end_time) if end_time else None
        self.templates = {
            'default': {
                'interval': u'{_from} {start_time} {_to} {end_time}',
            },
        }

    def display(self, prefix=False):
        """
        Format the time using the template associated with the locale
        """
        # all day long
        if all_day(self.start_time, self.end_time):
            return u''

        # single time
        elif self.start_time == self.end_time or self.end_time is None:
            return TimeFormatter(self.start_time, self.locale).display(prefix)

        # time interval
        template = self.get_template('interval')
        start_time_fmt = TimeFormatter(self.start_time, self.locale).display()
        end_time_fmt = TimeFormatter(self.end_time, self.locale).display()
        fmt = template.format(
            _from=self._('from_hour'),
            start_time=start_time_fmt,
            _to=self._('to_hour'),
            end_time=end_time_fmt)
        return fmt


class TimeIntervalListFormatter(BaseFormatter):
    """
    Formats list of time intervals
    """

    def __init__(self, interval_list, locale='fr_FR.UTF8'):
        super(TimeIntervalListFormatter, self).__init__(locale)
        self.interval_list = interval_list
        self.templates = {
            'fr_FR': u'{time} + autres horaires',
            'en_US': u'{time} + more schedules',
            'de_DE': u'{time} + mehr Zeitpläne',
            'es_ES': u'{time} + más horarios',
            'it_IT': u'{time} + altre orari',
            'pt_BR': u'{time} + mais horários',
            'nl_NL': u"{time} + meer schema's",
            'ru_RU': u'{time} + больше расписаний',
        }

    def display(self, prefix=False):
        # 'time_interval'
        if len(self.interval_list) == 1:
            time_inter = self.interval_list[0]
            return TimePatternFormatter(time_inter[0],
                                        time_inter[1],
                                        self.locale).display(prefix)

        # 'time_interval_1 and time_interval_2'
        elif len(self.interval_list) == 2:
            time1 = self.interval_list[0]
            time1_fmt = TimePatternFormatter(time1[0],
                                             time1[1]).display(prefix)
            time2 = self.interval_list[1]
            time2_fmt = TimePatternFormatter(time2[0],
                                             time2[1],
                                             self.locale).display(False)
            fmt = '%s %s %s' % (time1_fmt, self._('and'), time2_fmt)
            return fmt

        # 'time_interval_1 + more schedules'
        else:
            template = self.get_template()
            time_inter = self.interval_list[0]
            time_fmt = TimePatternFormatter(time_inter[0],
                                            time_inter[1],
                                            self.locale).display(prefix)
            fmt = template.format(time=time_fmt)
            return fmt
