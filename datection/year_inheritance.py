# -*- coding: utf-8 -*-

"""Implementation of the year iheritance strategies."""

from datection.timepoint import AbstractDate
from datection.timepoint import AbstractDateInterval
from datection.timepoint import get_extreme_months
from datection.timepoint import is_activity_ongoing


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

    def transmit(self):
        """Make all yearless timepoints inherit from a year, when possible.

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
        delta = 3
        if self.reference:
            for yearless_timepoint in self.year_undefined_timepoints:
                ref_month = self.reference.month
                start_month, end_month = get_extreme_months(yearless_timepoint)
                is_ongoing = is_activity_ongoing(yearless_timepoint, self.reference)
                is_upcomming = ((ref_month - start_month) % 12) > delta

                if is_ongoing or is_upcomming:
                    # ref: 15/05/2016 | tp: 15/09/???? -> 2016
                    if ref_month <= end_month:
                        yearless_timepoint.year = self.reference.year

                    # ref: 15/10/2016 | tp: 15/01/???? -> 2017
                    else:
                        yearless_timepoint.year = self.reference.year + 1

                # the activity is passed
                else:
                    # ref: 15/05/2016 | tp: 15/04/???? -> 2016
                    if ref_month >= end_month:
                        yearless_timepoint.year = self.reference.year

                    # ref: 15/01/2016 | tp: 15/12/???? -> 2015
                    else:
                        yearless_timepoint.year = self.reference.year - 1

        return self.timepoints
