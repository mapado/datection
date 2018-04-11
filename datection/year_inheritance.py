# -*- coding: utf-8 -*-

"""Implementation of the year iheritance strategies."""
import re
from builtins import object
from datetime import datetime, timedelta
from datection.timepoint import AbstractDate
from datection.timepoint import AbstractDateInterval
from datection.timepoint import WeeklyRecurrence
from datection.timepoint import DateInterval
from datection.timepoint import Date
from datection.models import DurationRRule


class YearTransmitter(object):

    """Object in charge of making all timepoints without year inherit
    from the year of another timepoint when appropriate, or from a
    reference year, when available.

    """

    def __init__(self, timepoints, reference=None):
        self.timepoints = timepoints
        self.reference = reference if reference is not None else None

    @property
    def year_defined_timepoints(self):
        """Return the list of timepoints with a defined year."""
        return [t for t in self.timepoints if t.year]

    @property
    def year_undefined_timepoints(self):
        """Return the list of timepoints with no defined year."""
        return [t for t in self.timepoints if not t.year]

    @property
    def unbounded_weekly_recurrences(self):
        """"""
        return [
            timepoint for timepoint in self.timepoints if (
                isinstance(timepoint, WeeklyRecurrence) and
                timepoint.date_interval == DateInterval.make_undefined()
            )
        ]

    def candidate_container(self, yearless_timepoint):
        """Return a timepoint that can transmit its year to the argument
        yearless_timepoint.

        For a timepoint to transmit its year, it must generate a date
        which day and month coincide with the ones of the yearless
        timepoint.

        """
        if not isinstance(yearless_timepoint, AbstractDate):
            return

        for candidate in self.year_defined_timepoints:
            if isinstance(candidate, AbstractDateInterval):
                dts = candidate.to_python()
                target_dt = yearless_timepoint.to_python()
                for dt in dts:
                    if dt.month == target_dt.month and dt.day == target_dt.day:
                        return candidate

    def transmit_year_to_exclusion(self, year, exclusion):
        """
        """
        exclusion = re.sub(
            r'(?<=DTSTART:)\d{4}',
            str(year),
            exclusion)
        exclusion = re.sub(
            r'(?<=UNTIL=)\d{4}',
            str(year),
            exclusion)
        return exclusion

    def transmit(self):
        """
        Make all yearless timepoints inherit from a year, when possible.

        Two strategies are used. The first is to find an appropriate
        timepoint for each yearless one, and transmit its year.
        The second one is to make all the remaining yearless timepoints
        inherit from the reference year, if defined.

        """
        # First try to transmit the year from the appropriate timepoints
        for yearless_timepoint in self.year_undefined_timepoints:
            candidate = self.candidate_container(yearless_timepoint)
            if candidate:
                yearless_timepoint.year = candidate.year

        # After the first round of transmission, if there are some
        # yearless timepoints left, give them the reference year,
        # if defined
        if self.reference:
            for yearless_timepoint in self.year_undefined_timepoints:
                yearless_timepoint.year = self.reference.year
                if hasattr(yearless_timepoint, 'excluded'):
                    yearless_timepoint.excluded = [
                        self.transmit_year_to_exclusion(self.reference.year, exclusion)
                        for exclusion in yearless_timepoint.excluded
                    ]

            new_date_interval = DateInterval(
                Date.from_date(self.reference),
                Date.from_date(self.reference + timedelta(days=365)))
            for unbounded_weekly in self.unbounded_weekly_recurrences:
                unbounded_weekly.date_interval = new_date_interval

        return self.timepoints
