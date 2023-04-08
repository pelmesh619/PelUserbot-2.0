import datetime
import time


def time_to_string(time_value, app):
    time_value = round(time_value)

    time_values = {
        'month': time_value // (60 * 60 * 24 * 30),
        'day': time_value // (60 * 60 * 24) % 30,
        'hour': time_value // (60 * 60) % 24,
        'minute': time_value // 60 % 60,
        'second': time_value % 60
    }

    time_strings = []
    for i in time_values:
        if time_values[i] == 0:
            continue

        time_strings.append(
            str(time_values[i]) + ' ' + app.get_string.get_string_form('time_' + str(i), time_values[i])
        )

    return ' '.join(time_strings)


def date_to_string(app, unix_time=None, tz=None):
    if tz is None:
        tz = time.timezone / 3600

    if unix_time is None:
        unix_time = time.time()

    date = datetime.datetime.fromtimestamp(unix_time + time.timezone - tz * 3600)
    day_week = date.isoweekday()

    string = app.get_string(
        'date_general',
        hours=add_zero(date.hour),
        minutes=add_zero(date.minute),
        seconds=add_zero(date.second),
        day=add_zero(date.day),
        suffix=app.get_string.get_string_form('date_day_suffixes', date.day),
        month=app.get_string('date_month_' + str(date.month), default=date.month),
        day_week=app.get_string('date_weekday_' + str(day_week), default=day_week),
        year=date.year,
        timezone=timezone_to_string(-tz),
    )

    return string


def date_to_short_string(app, unix_time=None, tz=0):
    if unix_time is None:
        unix_time = time.time()

    date = datetime.datetime.fromtimestamp(unix_time + time.timezone + tz * 3600)

    string = app.get_string(
        'short_date_template',
        hours=add_zero(date.hour),
        minutes=add_zero(date.minute),
        seconds=add_zero(date.second),
        day=add_zero(date.day),
        month=add_zero(date.month),
        year=date.year,
        _module='core.handlers'
    )

    return string


def add_zero(n):
    if len(str(n)) == 1:
        return '0' + str(n)
    else:
        return str(n)


def timezone_to_string(tz):
    return ('-' if tz < 0 else '+') + str(int(abs(tz))) + \
           (f':{int(abs(tz) * 60 % 60)}' if int(tz) != tz else '')
