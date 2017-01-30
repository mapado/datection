# -*- coding: utf-8 -*-


class NoFutureOccurence(Exception):
    """
    Exception raised when a DurationRRule does not yield future dates.
    """
    pass


class TooManyMonths(Exception):
    """
    Exception raised in SEO formatting when a schedule related to
    more than two months or when the two months are of a different year.
    """
    pass
