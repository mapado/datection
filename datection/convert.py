# -*- coding: utf-8 -*-
"""
Entry methods to convert a list of DurationRRule into
a concise or plain form.

 * concise is meant for human interaction (display, forms)
 * plain is meant for computation (eventDate generation, merge)

"""
from __future__ import absolute_import
from builtins import str
from .pack import RrulePackerWithGaps
from .pack import RrulePacker
from .combine.remove import RruleRemover
from datection.models import DurationRRule


def _exclusion_rrule_to_drr(excl_rrule, main_drr):
    """
    Convert a exclusion rrule string into a DurationRRule.
    Duration is assumed to be the same as the impacted rrule.
    """
    drr = DurationRRule({
        'rrule': str(excl_rrule),
        'duration': main_drr.duration
    })
    return drr


def convert_to_plain_form(drrs):
    """
    Convert the given DurationRrules to a plain form, i.e
    easy to perform computations with (no overlap and no
    exclusion rrules).
    """
    # 1) remove exceptions from drrs
    plain_drrs = []
    for drr in drrs:
        exceptions_rrules = drr.exclusion_rrules
        exceptions_drrs = [
            _exclusion_rrule_to_drr(rrule, drr)
            for rrule in exceptions_rrules]
        if exceptions_drrs:
            drr.remove_exclusions()  # just removes the field in the object
            remover = RruleRemover([drr])
            remover.remove_rrules(exceptions_drrs)
            plain_drrs.extend(remover.get_remaining_rrules())
        else:
            plain_drrs.append(drr)

    # 2) simple pack result
    packer = RrulePacker(plain_drrs)

    return packer.pack_rrules()


def convert_to_concise_form(drrs):
    """
    Convert the given DurationRrules to a concise form, i.e
    easy to handle by a human (well packed with exclusion rrules).
    """

    # 1) first convert to plain to ensure there are no exceptions
    plain_drrs = convert_to_plain_form(drrs)

    # 2) pack with exceptions
    packer = RrulePackerWithGaps(plain_drrs)

    return packer.pack_with_gaps()
