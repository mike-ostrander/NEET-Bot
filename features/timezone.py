from datetime import datetime
from pytz import timezone, all_timezones


def print_timezones():
    for zone in all_timezones:
        print(zone)
