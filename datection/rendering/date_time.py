# -*- coding: utf-8 -*-
from datection.rendering.base import BaseFormatter
from datection.rendering.date import DateFormatter
from datection.rendering.date import DateIntervalFormatter
from datection.rendering.time import TimeFormatter
from datection.rendering.time import TimePatternFormatter
from datection.rendering.wrappers import postprocess


class DatetimeFormatter(BaseFormatter):

    """ Formats a datetime using the current locale. """

    def __init__(self, _datetime, locale='fr_FR.UTF8'):
        super(DatetimeFormatter, self).__init__(locale)
        self.datetime = _datetime
        self.templates = {
            'default': u'{date} {time}',
        }

    def display(self, *args, **kwargs):
        """
        Format the datetime using the current locale.
        Pass all args and kwargs to the DateFormatter.display method.
        """
        template = self.get_template()

        if 'prefix' not in kwargs:
            kwargs['prefix'] = True

        date_fmt = DateFormatter(
            self.datetime, self.locale).display(*args, **kwargs)
        time_fmt = TimeFormatter(
            self.datetime, self.locale).display(prefix=True)

        return template.format(date=date_fmt, time=time_fmt)


class DatetimeIntervalFormatter(BaseFormatter):

    """ Formats a datetime interval using the current locale. """

    def __init__(self, start_datetime, end_datetime, locale='fr_FR.UTF8'):
        super(DatetimeIntervalFormatter, self).__init__(locale)
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.templates = {
            'default': {
                'date_interval': u'{date_interval} {time_interval}',
            }
        }

    def same_time(self):
        """
        Return True if self.start_datetime and self.end_datetime have
        the same time.
        """
        return self.start_datetime.time() == self.end_datetime.time()

    @postprocess()
    def display(self, *args, **kwargs):
        """
        Format the datetime interval using the current locale.
        Pass all args and kwargs to the DateFormatter.display method.
        """
        date_formatter = DateIntervalFormatter(
            self.start_datetime, self.end_datetime, self.locale)
        date_fmt = date_formatter.display(*args, **kwargs)

        time_fmt = TimePatternFormatter(
            self.start_datetime,
            self.end_datetime,
            self.locale).display(prefix=True)

        template = self.get_template('date_interval')
        fmt = template.format(
            date_interval=date_fmt, time_interval=time_fmt)

        return fmt


class ContinuousDatetimeIntervalFormatter(BaseFormatter):

    """ Formats a contiunuous datetime interval using the current locale. """

    def __init__(self, start, end, locale='fr_FR.UTF8'):
        super(ContinuousDatetimeIntervalFormatter, self).__init__(locale)
        self.start = start
        self.end = end
        self.templates = {
            'de_DE':
            u'{start_date} {start_time} - {end_date} {end_time}',
            'ru_RU':
            u'{start_date} {start_time} - {end_date} {end_time}',
            'default':
            u'{_from} {start_date} {start_time} {_to} {end_date} {end_time}'
        }

    @postprocess()
    def display(self, *args, **kwargs):
        """ Display a continuous datetime interval in the current locale. """
        template = self.get_template()

        # do not include the year if both dates are in the same year
        sd_kwargs = kwargs.copy()
        if self.start.year == self.end.year:
            sd_kwargs['include_year'] = False
            sd_kwargs['force_year'] = False

        start_date_fmt = DateFormatter(
            self.start, self.locale).display(*args, **sd_kwargs)
        end_date_fmt = DateFormatter(
            self.end, self.locale).display(*args, **kwargs)
        start_time_fmt = TimeFormatter(
            self.start, self.locale).display(prefix=True)
        end_time_fmt = TimeFormatter(
            self.end, self.locale).display(prefix=True)

        return template.format(
            _from=self._('from_day'),
            start_date=start_date_fmt,
            start_time=start_time_fmt,
            _to=self._('to_day'),
            end_date=end_date_fmt,
            end_time=end_time_fmt)
