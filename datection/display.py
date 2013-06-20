# -*- coding: utf-8 -*-

import datetime

from export import to_mongo

text = "Du 2 au 5 juin 2013 de 15h à 18h plop plop le 29 juin 2013 de 15h à 18h plop 27 juillet 2014 à 16h"
data = to_mongo(text, 'fr')

# THe main hypothesis tested by this prototype is that we can work
# without keeping the datamined contexts, only with a flat list
# containing datetimes

# Here, we flatten the data
context_free = []
for context in data:
    context_free.extend(context)
data = context_free


def consecutives(date1, date2):
    """ If two dates are consecutive, return True, else False

    date1 and date2 are consecutive if date1.day == date2.day +/- 1
    in the same year

    """
    if date1['start'].year != date2['start'].year:
        return False
    return abs(date1['start'].day - date2['start'].day) == 1


def group_schedules_by_consecutive_dates(schedules):
    """ Group the input schedule list by gathering consecutive dates together

    Example:
    Input: [01/02/2013, 03/02/2013, 04/02/2013, 06/02/2013]
    Output: [[01/02/2013], [03/02/2013, 04/02/2013], [06/02/2013]]

    """
    conseq = []
    schedules = sorted(schedules, key=lambda x: x['start'])
    start = 0
    for i, schedule in enumerate(schedules):
        if i != len(schedules) - 1:
            if consecutives(schedule, schedules[i+1]):
                continue
            else:
                conseq.append(schedules[start: i+1])
                start = i + 1
        else:  # special case of the last item in the list
            if consecutives(schedule, schedules[i-1]):
                conseq.append(schedules[start: i+1])
            else:
                conseq.append([schedule])

    return conseq


def group_schedule_by_time(schedules):
    """ Group the input schedule list by time

    All the schedules with the same start/end time are grouped together

    """
    times = {}
    for schedule in schedules:
        start, end = schedule['start'], schedule['end']
        start_time = datetime.time(hour=start.hour, minute=start.minute)
        end_time = datetime.time(hour=end.hour, minute=end.minute)
        display_time = '%s-%s' % (start_time.isoformat(), end_time.isoformat())
        if display_time not in times:
            times[display_time] = [schedule]
        else:
            times[display_time].append(schedule)
    return times.values()


def format_single_date(sched):
    """ Format a single date """
    date = datetime.date(year=sched.year, month=sched.month, day=sched.day)
    return u'le ' + datetime.date.isoformat(date)


def format_sparse_dates(dates):
    # group the sparse dates by year first
    yeargroups = list(set([date['start'].year for date in dates]))
    out = []
    for year in yeargroups:
        monthgroups = list(set([date['start'].month for date in dates if date['start'].year == year]))
        if len(monthgroups) == 1:
            month = monthgroups[0]
            monthdates = [
                date for date in dates
                if date['start'].year == year
                and date['start'].month == month]
            prefix = 'le ' if len(monthdates) == 1 else 'les '
            fmt = prefix + ', '.join([str(date['start'].day) for date in monthdates]) + ' %d %d' % (
                month, year)
            out.append(fmt)
        else:
            for month in monthgroups:
                fmt = 'les '
                for i, month in enumerate(monthgroups):
                    monthgroup = [date for date in dates if date['start'].year == year and date['start'].month == month]
                    fmt += ', '.join([str(date['start'].day) for date in monthgroup]) + ' %d' % (month)
                    if i != len(monthgroups) - 1:
                        if len(monthgroups) == 2:
                            fmt += ' et '
                        else:
                            fmt += ', '
                    else:
                        fmt += ' %d' % (year)
            out.append(fmt)
    return out


def format_date_interval(group):
    """ Format a date interval """
    start_day = group[0]['start'].day
    start_year = group[0]['start'].year
    end_day = group[-1]['start'].day
    end_month = group[-1]['start'].month
    end_year = group[-1]['start'].year
    if start_year != end_year:
        interval = u'du %s au %s' % (group[0]['start'].isoformat(), group[-1]['end'].isoformat())
    else:
        interval = u'du %d au %d/%d/%d' % (start_day, end_day, end_month, end_year)
    return interval


def format_time(sched):
    """ Format a single time or a time interval """
    start_hour = sched['start'].hour
    start_minute = sched['start'].minute
    end_hour = sched['end'].hour
    end_minute = sched['end'].minute

    if start_hour == end_hour and start_minute == end_minute:
        interval = u'à %dh%s' % (start_hour, start_minute or '')
    else:
        interval = u'de %dh%s à %dh%s' % (start_hour, start_minute or '', end_hour, end_minute or '')
    return interval


def display(groups):
    out = []
    for time_group in groups:
        fmt = []
        for conseq_group in time_group:
            if len(conseq_group) == 1:
                date = conseq_group[0]['start']
                fmt.append(format_single_date(date))
            else:
                fmt.append(format_date_interval(conseq_group))
        fmt.append(format_time(time_group[0][0]))
        out.append(', '.join(fmt))
    return out

if __name__ == '__main__':
    by_time = group_schedule_by_time(data)
    conseq = []
    for i, group in enumerate(by_time):
        conseq.append(group_schedules_by_consecutive_dates(group))

    print u' | '.join(display(conseq))
    dates = [{'end': datetime.datetime(2013, 6, 14, 20, 0),
   'start': datetime.datetime(2013, 6, 14, 20, 0)},
  {'end': datetime.datetime(2013, 6, 18, 20, 0),
   'start': datetime.datetime(2013, 6, 18, 20, 0)},
  {'end': datetime.datetime(2013, 6, 20, 20, 0),
   'start': datetime.datetime(2013, 6, 20, 20, 0)},
  {'end': datetime.datetime(2013, 6, 21, 20, 0),
   'start': datetime.datetime(2013, 6, 21, 20, 0)},
  {'end': datetime.datetime(2013, 6, 22, 20, 0),
   'start': datetime.datetime(2013, 6, 22, 20, 0)},
  {'end': datetime.datetime(2013, 6, 25, 20, 0),
   'start': datetime.datetime(2013, 6, 25, 20, 0)},
  {'end': datetime.datetime(2014, 7, 26, 20, 0),
   'start': datetime.datetime(2014, 7, 26, 20, 0)}]
    print format_sparse_dates(dates)
    by_time = group_schedule_by_time(dates)
    conseq = []
    for i, group in enumerate(by_time):
        conseq.append(group_schedules_by_consecutive_dates(group))

    print u' | '.join(display(conseq))