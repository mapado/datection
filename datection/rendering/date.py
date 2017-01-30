# -*- coding: utf-8 -*-
import locale as _locale
import re
import datetime

from datection.rendering.base import BaseFormatter
from datection.rendering.wrappers import postprocess
import datection.rendering.utils as utils


class DateFormatter(BaseFormatter):

    """ Formats a date into using the current locale. """

    def __init__(self, date, locale='fr_FR.UTF8'):
        super(DateFormatter, self).__init__(locale)
        self.date = utils.get_date(date)
        self.templates = {
            'fr_FR': {
                'all': u'{prefix} {dayname} {day} {month} {year}',
                'no_year': u'{prefix} {dayname} {day} {month}',
                'no_year_no_month': u'{prefix} {dayname} {day}',
            },
            'en_US': {
                'all': u'{prefix} {dayname} {day} of {month} {year}',
                'no_year': u'{prefix} {dayname} {day} of {month}',
                'no_year_no_month': u'{prefix} {dayname} {day}',
            }
        }

    def format_day(self):
        """ Format the date day using the current locale. """
        if self.language_code == 'fr_FR':
            return u'1er' if self.date.day == 1 else unicode(self.date.day)
        elif self.language_code in ['en_US', 'en_GB']:
            if 4 <= self.date.day <= 20 or 24 <= self.date.day <= 30:
                suffix = 'th'
            else:
                suffix = ['st', 'nd', 'rd'][self.date.day % 10 - 1]
            return u'%d%s' % (self.date.day, suffix)

    def format_dayname(self, abbrev=False):
        """ Format the date day using the current locale. """
        with utils.TemporaryLocale(_locale.LC_TIME, self.locale):
            if abbrev:
                return self.date.strftime('%a')
            return self.date.strftime('%A')

    def format_month(self, abbrev=False):
        """ Format the date month using the current locale. """
        with utils.TemporaryLocale(_locale.LC_TIME, self.locale):
            if abbrev:
                return self.date.strftime('%b')
            return self.date.strftime('%B')

    def format_year(self, abbrev=False, force=False):
        """
        Format the date year using the current locale.

        The year will be formatted if force=True or if the date occurs
        in more than 6 months (6 * 30 days).
        Otherwise, return u''.

        If abbrev = True, only the abbreviated version of the year will
        be returned (ex: 13 instead of 2013).
        """
        if (
                force
                or self.date.year < utils.get_current_date().year
                or (self.date - utils.get_current_date()).days > 6 * 30
        ):
            with utils.TemporaryLocale(_locale.LC_TIME, self.locale):
                if abbrev:
                    return self.date.strftime('%y')
                return self.date.strftime('%Y')
        else:
            return u''

    def format_all_parts(
        self, include_dayname, abbrev_dayname,
        abbrev_monthname, abbrev_year, prefix, force_year=False
    ):
        """ Formats the date in the current locale. """
        template = self.get_template('all')
        if include_dayname or abbrev_dayname:
            dayname = self.format_dayname(abbrev_dayname)
        else:
            dayname = u''
        day = self.format_day()
        month = self.format_month(abbrev_monthname).decode('utf-8')
        if force_year:
            year = self.format_year(abbrev_year, force=True)
        else:
            year = self.format_year(abbrev_year)
        fmt = template.format(
            prefix=prefix, dayname=dayname, day=day, month=month, year=year)
        fmt = re.sub(r'\s+', ' ', fmt)
        return fmt

    def format_no_year(self, include_dayname, abbrev_dayname, abbrev_monthname,
                       prefix):
        """ Formats the date in the current locale, omitting the year. """
        template = self.get_template('no_year')
        if include_dayname or abbrev_dayname:
            dayname = self.format_dayname(abbrev_dayname)
        else:
            dayname = u''
        day = self.format_day()
        month = self.format_month(abbrev_monthname).decode('utf-8')
        fmt = template.format(
            prefix=prefix, dayname=dayname, day=day, month=month)
        fmt = re.sub(r'\s+', ' ', fmt)
        return fmt

    def format_no_month_no_year(self, include_dayname, abbrev_dayname, prefix):
        """
        Formats the date in the current locale, omitting the month
        and year.
        """
        template = self.get_template('no_year_no_month')
        if include_dayname or abbrev_dayname:
            dayname = self.format_dayname(abbrev_dayname)
        else:
            dayname = u''
        day = self.format_day()
        fmt = template.format(prefix=prefix, dayname=dayname, day=day)
        fmt = re.sub(r'\s+', ' ', fmt)
        return fmt

    @postprocess()
    def display(self, include_dayname=False, abbrev_dayname=False,
                include_month=True, abbrev_monthname=False, include_year=True,
                abbrev_year=False, reference=None, abbrev_reference=False,
                prefix=False, force_year=False, **kwargs):
        """
        Format the date using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If include_month is True, the month will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If include_year is True, the year will be included (if the date
        formatter 'decides' that the year should be displayed.
        If force_year is True, the year will be displayed no matter what.
        If abbrev_year is True, a 2 digit year format will be used.
        If a reference date is given, and it is at least 6 days before
        the formatted date, a relativistic expression will be used (today,
            tomorrow, this {weekday})
        """
        if force_year and not include_year:
            raise ValueError(
                "force_year can't be True if include_year is False")
        if reference:
            if self.date == reference:
                if abbrev_reference:
                    return self._('today_abbrev')
                else:
                    return self._('today')
            elif self.date == reference + datetime.timedelta(days=1):
                return self._('tomorrow')
            elif reference < self.date <= reference + datetime.timedelta(days=6):
                # if d is next week, use its weekday name
                return u'%s %s' % (
                    self._('this'),
                    self.format_dayname(abbrev_dayname))

        prefix = self._('the') if prefix else u''
        if include_month and include_year:
            return self.format_all_parts(
                include_dayname,
                abbrev_dayname,
                abbrev_monthname,
                abbrev_year,
                prefix,
                force_year)
        elif include_month and not include_year:
            return self.format_no_year(
                include_dayname,
                abbrev_dayname,
                abbrev_monthname,
                prefix)
        else:
            return self.format_no_month_no_year(
                include_dayname,
                abbrev_dayname,
                prefix)


class DateIntervalFormatter(BaseFormatter):

    """Formats a date interval using the current locale."""

    def __init__(self, start_date, end_date, locale='fr_FR.UTF8'):
        super(DateIntervalFormatter, self).__init__(locale)
        self.start_date = utils.get_date(start_date)
        self.end_date = utils.get_date(end_date)
        self.templates = {
            'fr_FR': u'du {start_date} au {end_date}',
            'en_US': u'{start_date} - {end_date}',
        }

    def same_day_interval(self):
        """
        Return True if the start and end datetime have the same date,
        else False.
        """
        return self.start_date == self.end_date

    def same_month_interval(self):
        """
        Return True if the start and end date have the same month
        and the same year, else False.
        """
        # To be on the same month means that both date have the same
        # month *in the same year*, not just the same monthname!
        if not self.same_year_interval():
            return False
        return self.start_date.month == self.end_date.month

    def same_year_interval(self):
        """
        Return True if the start and end date have the same year,
        else False.
        """
        return self.start_date.year == self.end_date.year

    def has_two_consecutive_days(self):
        return self.start_date + datetime.timedelta(days=1) == self.end_date

    def format_same_month(self, *args, **kwargs):
        """Formats the date interval when both dates have the same month."""
        template = self.get_template()
        start_kwargs = kwargs.copy()
        start_kwargs['force_year'] = False
        start_kwargs['include_month'] = False
        start_kwargs['include_year'] = False
        start_date_fmt = DateFormatter(
            self.start_date, self.locale).display(*args, **start_kwargs)
        end_date_fmt = DateFormatter(
            self.end_date, self.locale).display(*args, **kwargs)

        return template.format(
            start_date=start_date_fmt,
            end_date=end_date_fmt)

    def format_same_year(self, *args, **kwargs):
        """Formats the date interval when both dates have the same year."""
        template = self.get_template()
        start_kwargs = kwargs.copy()
        start_kwargs['force_year'] = False
        start_kwargs['include_year'] = False
        start_date_fmt = DateFormatter(
            self.start_date, self.locale).display(*args, **start_kwargs)
        end_date_fmt = DateFormatter(
            self.end_date, self.locale).display(*args, **kwargs)

        return template.format(
            start_date=start_date_fmt,
            end_date=end_date_fmt)

    def format_two_consecutive_days(self, *args, **kwargs):
        return DateListFormatter([self.start_date, self.end_date],
                                 self.locale).display(*args, **kwargs)

    @postprocess()
    def display(self, abbrev_reference=False, *args, **kwargs):
        """
        Format the date interval using the current locale.

        If dayname is True, the dayname will be included.
        If abbrev_dayname is True, the abbreviated dayname will be included.
        If abbrev_monthname is True, the abbreviated month name will be
        included.
        If abbrev_year is True, a 2 digit year format will be used.
        """
        if self.same_day_interval():
            if 'prefix' not in kwargs:
                kwargs['prefix'] = True
            return DateFormatter(self.start_date, self.locale).display(
                abbrev_reference=abbrev_reference, *args, **kwargs)

        if kwargs.get('summarize'):
            kwargs['include_dayname'] = False

        if self.has_two_consecutive_days():
            return self.format_two_consecutive_days(**kwargs)
        elif self.same_month_interval():
            return self.format_same_month(*args, **kwargs)
        elif self.same_year_interval():
            return self.format_same_year(*args, **kwargs)
        else:
            template = self.get_template()
            kwargs['force_year'] = True

            kwargs['abbrev_reference'] = abbrev_reference
            start_date_fmt = DateFormatter(
                self.start_date, self.locale).display(*args, **kwargs)
            end_date_fmt = DateFormatter(
                self.end_date, self.locale).display(*args, **kwargs)
            fmt = template.format(
                start_date=start_date_fmt, end_date=end_date_fmt)
            return fmt


class DateListFormatter(BaseFormatter):

    """ Formats a date list using the current locale. """

    def __init__(self, date_list, locale='fr_FR.UTF8'):
        super(DateListFormatter, self).__init__(locale)
        self.date_list = [utils.get_date(d) for d in date_list]
        self.templates = {
            'fr_FR': u'les {date_list} et {last_date}',
            'en_US': u'{date_list} and {last_date}',
        }

    @postprocess()
    def display(self, *args, **kwargs):
        """ Format a date list using the current locale. """
        if len(self.date_list) == 1:
            if 'prefix' not in kwargs:
                kwargs['prefix'] = True
            return DateFormatter(
                self.date_list[0], self.locale).display(*args, **kwargs)

        include_dayname = kwargs.get('include_dayname')
        if not kwargs.get('prefix', True):
            self.templates['fr_FR'] = u'{date_list} et {last_date}'
        template = self.get_template()
        date_list = ', '.join([DateFormatter(d, self.locale).display(
            include_month=False,
            include_year=False,
            include_dayname=include_dayname)
            for d in self.date_list[:-1]])
        last_date = DateFormatter(
            self.date_list[-1], self.locale).display(*args, **kwargs)
        fmt = template.format(date_list=date_list, last_date=last_date)
        return fmt
