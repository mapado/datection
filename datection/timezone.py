
from datetime import datetime
from dateutil import tz


def get_timezone_offset(timezone):
    """
    Returns timedelta that corresponds to the offset of the timezone
    compared to UTC.
    """
    return timezone.utcoffset(datetime.today())


def is_valid_timezone(timezone_name):
    """
    """
    if timezone_name is None:
        return False

    return (tz.gettz(timezone_name) is not None)


def add_timezone_offset(datetime, timezone_name):
    """
    Attempts to set the tzinfo field of the datetime based
    on the timezone name.
    """
    timezone = tz.gettz(timezone_name)

    if timezone is None:
        return datetime

    return datetime + get_timezone_offset(timezone)


def add_timezone(datetime_wo_timezone, timezone_name):
    """
    Replaces tzinfo with the timezone correponding to timezone_name.
    """
    return datetime_wo_timezone.replace(tzinfo=tz.gettz(timezone_name))


def remove_timezone(datetime_w_timezone):
    """
    Removes tzinfo.
    """
    return datetime_w_timezone.replace(tzinfo=None)


def local_time_to_utc_no_timezone(local_wo_timezone, timezone_name):
    """
    Transforms a local time with no tzinfo to UTC based on the supposed
    timezone_name timezone.
    """
    local_w_timezone = add_timezone(local_wo_timezone, timezone_name)
    utc_w_timezone = local_w_timezone.astimezone(tz.UTC)
    utc_wo_timezone = remove_timezone(utc_w_timezone)

    return utc_wo_timezone


def now_local_time_no_timezone(timezone_name):
    """
    Returns local time (with no tzinfo) of now().
    """
    utc_now = datetime.utcnow()

    timezone = tz.gettz(timezone_name)
    if timezone is None:
        return utc_now

    local_now = utc_now + get_timezone_offset(timezone)
    local_now = remove_timezone(local_now)

    return local_now
