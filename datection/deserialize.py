# -*- coding: utf-8 -*-

"""
This module provides a deserialization functionality, able to recreate
python objects from JSON-serialized timepoint structure.
"""

import serialize


def deserialize(serialized):
    """ Deserialize the input JSON strcture and return
        a datection.serialize.Timepoint subclass instance.

    """
    if serialized['timepoint'] == 'date':
        return create_date(serialized)
    elif serialized['timepoint'] == 'date_list':
        return create_date_list(serialized)
    elif serialized['timepoint'] == 'date_interval':
        return create_date_interval(serialized)
    elif serialized['timepoint'] == 'time_interval':
        return create_time_interval(serialized)
    elif serialized['timepoint'] == 'datetime':
        return create_datetime(serialized)
    elif serialized['timepoint'] == 'datetime_list':
        return create_datetime_list(serialized)
    elif serialized['timepoint'] == 'datetime_interval':
        return create_datetime_interval(serialized)


def create_date(ser, timepoint=True):
    """ Instanciate a datection.serialize.Date from a JSON structure.

    If timepoint=True, then the returned DateTime instance will bear an
    timepoint attribute with value 'date'.

    """
    date = serialize.Date(
        day=ser['day'],
        month=ser['month'],
        year=ser['year'])
    if timepoint:
        date.timepoint = ser['timepoint']
    return date


def create_date_list(ser):
    """ Instanciate a datection.serialize.DateList from a JSON structure. """
    dates = [create_date(d, timepoint=False) for d in ser['dates']]
    return serialize.DateList(
        dates=dates,
        timepoint=ser['timepoint'])


def create_date_interval(ser, timepoint=True):
    """ Instanciate a datection.serialize.DateInterval from a JSON structure.

    If timepoint=True, then the returned DateTime instance will bear an
    timepoint attribute with value 'date_interval'.

    """
    start_date = create_date(ser['start_date'], timepoint=False)
    end_date = create_date(ser['end_date'], timepoint=False)
    di = serialize.DateInterval(start_date=start_date, end_date=end_date)
    if timepoint:
        di.timepoint = ser['timepoint']
    return di


def create_time(ser, timepoint=True):
    """ Instanciate a datection.serialize.Time from a JSON structure.

    If timepoint=True, then the returned DateTime instance will bear an
    timepoint attribute with value 'time'.

    """
    hour, minute = ser['hour'], ser['minute']
    time = serialize.Time(
        hour=hour,
        minute=minute)
    if timepoint:
        time.timepoint = ser['timepoint']
    return time


def create_time_interval(ser, timepoint=True):
    """ Instanciate a datection.serialize.TimeInterval from a JSON structure.

    If timepoint=True, then the returned DateTime instance will bear an
    timepoint attribute with value 'time_interval'.

    """
    start_time = create_time(ser['start_time'], timepoint=False)
    if ser['end_time'] is not None:
        end_time = create_time(ser['end_time'], timepoint=False)
    else:
        end_time = None
    ti = serialize.TimeInterval(start_time=start_time, end_time=end_time)
    if timepoint:
        ti.timepoint = ser['timepoint']
    return ti


def create_datetime(ser, timepoint=True):
    """ Instanciate a datection.serialize.DateTime from a JSON structure.

    If timepoint=True, then the returned DateTime instance will bear an
    timepoint attribute with value 'datetime'.

    """
    date = create_date(ser['date'], timepoint=False)
    time = create_time_interval(ser['time'], timepoint=False)
    dt = serialize.DateTime(date=date, time=time)
    if timepoint:
        dt.timepoint = ser['timepoint']
    return dt


def create_datetime_list(ser):
    """ Instanciate a datection.serialize.DateTimeList from a
        JSON structure.

    """
    dts = [create_datetime(dt, timepoint=False) for dt in ser['datetimes']]
    return serialize.DateTimeList(datetimes=dts, timepoint=ser['timepoint'])


def create_datetime_interval(ser):
    """ Instanciate a datection.serialize.DateTimeInterval from a
        JSON structure.

    """
    di = create_date_interval(ser['date_interval'], timepoint=False)
    ti = create_time_interval(ser['time_interval'], timepoint=False)
    return serialize.DateTimeInterval(
        date_interval=di, time_interval=ti, timepoint=ser['timepoint'])
