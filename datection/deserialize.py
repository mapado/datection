# -*- coding: utf-8 -*-

import serialize


def deserialize(serialized):
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
    date = serialize.Date(
        day=ser['day'],
        month=ser['month'],
        year=ser['year'])
    if timepoint:
        date.timepoint = ser['timepoint']
    return date


def create_date_list(ser):
    dates = [create_date(d, timepoint=False) for d in ser['dates']]
    return serialize.DateList(
        dates=dates,
        timepoint=ser['timepoint'])


def create_date_interval(ser, timepoint=True):
    start_date = create_date(ser['start_date'], timepoint=False)
    end_date = create_date(ser['end_date'], timepoint=False)
    di = serialize.DateInterval(start_date=start_date, end_date=end_date)
    if timepoint:
        di.timepoint = ser['timepoint']
    return di


def create_time(ser, timepoint=True):
    hour, minute = ser['hour'], ser['minute']
    time = serialize.Time(
        hour=hour,
        minute=minute)
    if timepoint:
        time.timepoint = ser['timepoint']
    return time


def create_time_interval(ser, timepoint=True):
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
    date = create_date(ser['date'], timepoint=False)
    time = create_time_interval(ser['time'], timepoint=False)
    dt = serialize.DateTime(date=date, time=time)
    if timepoint:
        dt.timepoint = ser['timepoint']
    return dt


def create_datetime_list(ser):
    dts = [create_datetime(dt, timepoint=False) for dt in ser['datetimes']]
    return serialize.DateTimeList(datetimes=dts, timepoint=ser['timepoint'])


def create_datetime_interval(ser):
    di = create_date_interval(ser['date_interval'], timepoint=False)
    ti = create_time_interval(ser['time_interval'], timepoint=False)
    return serialize.DateTimeInterval(
        date_interval=di, time_interval=ti, timepoint=ser['timepoint'])
