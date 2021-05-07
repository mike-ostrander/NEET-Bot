from datetime import datetime
from pytz import timezone, all_timezones, utc


def print_timezones():
    for zone in all_timezones:
        print(zone)


def convert_time(time, old_tz, new_tz):
    time = format_time((datetime.strftime(time, '%H:%M')).upper())
    old_tz = adjust_tz(old_tz.upper())
    new_tz = adjust_tz(new_tz.upper())
    old_tz = timezone(old_tz)
    time_dt = datetime.strptime(time, '%H:%M')
    localized_time = old_tz.localize(time_dt, is_dst=None)
    converted_time = localized_time.astimezone(timezone(new_tz))
    return format_dt(converted_time, 'time')


def format_time(time):
    pm_times = [['01:', '13:'], ['02:', '14:'], ['03:', '15:'], ['04:', '16:'], ['05:', '17:'], ['06:', '18:'],
                ['07:', '19:'], ['08:', '20:'], ['09:', '21:'], ['10:', '22:'], ['11:', '23:']]
    if 'PM' in time:
        time = time.replace('PM', '')
        c = 0
        while c < len(pm_times):
            if pm_times[c][0] in time:
                time = time.replace(pm_times[c][0], pm_times[c][1])
                break
            c += 1
    elif 'AM' in time:
        time = time.replace('AM', '')
        time = time.replace('12:', '00:')
    return time


def adjust_tz(tz):
    if tz == 'CST' or tz == 'CT' or tz == 'CDT':
        tz = 'CST6CDT'
    elif tz == 'EDT':
        tz = 'EST5EDT'
    return tz


def format_dt(dt, dt_format):
    if dt_format == 'date and time':
        return dt.strftime("%Y-%m-%d %I:%M%p")
    elif dt_format == 'date':
        return dt.strftime("%Y-%m-%d")
    elif dt_format == 'time':
        return dt.strftime("%H:%M")
    elif dt_format == 'hour':
        return dt.strftime("%I")

