from datetime import datetime


def is_future(timepoint, reference=datetime.today()):
    """ If the timepoint is located in the future, return True, else False.

    A timepoint is considered to be in the future if its startting point is
    after the time reference, or if the reference is included between the
    timepoint starting and ending point.

    The default reference is datetime.datetime.today(), meaning that each
    time the method is called, the reference will be evaluated as the function
    calling time.

    Warning: this function is only intended to be used with standard datetime
    input, groupes by (start, end) 2-tuples, such as the ones returned by the
    datection.export.to_db function.

    """
    start, end = timepoint
    return (start > reference or start < reference < end)
