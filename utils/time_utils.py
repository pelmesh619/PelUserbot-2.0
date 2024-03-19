import datetime
import time


def time_to_string(time_value, app, lang_code=None):
    if not lang_code:
        lang_code = getattr(app, 'lang_code', getattr(getattr(app, 'from_user', None), 'lang_code', None))
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
            str(time_values[i]) + ' ' + app.get_core_string_form('time_' + str(i), time_values[i], lang_code=lang_code)
        )

    return ' '.join(time_strings)


def datetime_to_string(unix_time=None, tz: float = None, app=None, lang_code=None):
    if tz is None:
        tz = time.timezone
    tz /= 3600

    if unix_time is None:
        unix_time = time.time()

    date = datetime.datetime.fromtimestamp(unix_time)
    day_week = date.isoweekday()

    string = app.get_core_string(
        'datetime_template',
        hours=str(date.hour).zfill(2),
        minutes=str(date.minute).zfill(2),
        seconds=str(date.second).zfill(2),
        day=str(date.day),
        suffix=app.get_core_string_form('date_day_suffixes', date.day, lang_code=lang_code),
        month=app.get_core_string('date_month_' + str(date.month), default=date.month, lang_code=lang_code),
        day_week=app.get_core_string('date_weekday_' + str(day_week), default=day_week, lang_code=lang_code),
        year=date.year,
        timezone=timezone_to_string(-tz),
        lang_code=lang_code
    )

    return string


def datetime_to_short_string(app, unix_time=None, tz=0, lang_code=None):
    if unix_time is None:
        unix_time = time.time()

    date = datetime.datetime.fromtimestamp(unix_time + time.timezone + tz * 3600)

    string = app.get_core_string(
        'short_datetime_template',
        hours=str(date.hour).zfill(2),
        minutes=str(date.minute).zfill(2),
        seconds=str(date.second).zfill(2),
        day=str(date.day).zfill(2),
        month=str(date.month).zfill(2),
        year=date.year,
        lang_code=lang_code
    )

    return string


def date_to_string(unix_time=None, tz: int = None, app=None, lang_code=None):
    if tz is None:
        tz = time.timezone
    tz /= 3600

    if unix_time is None:
        unix_time = time.time()

    date = datetime.datetime.fromtimestamp(unix_time)
    day_week = date.isoweekday()

    string = app.get_core_string(
        'date_template',
        day=date.day,
        suffix=app.get_core_string_form('date_day_suffixes', date.day, lang_code=lang_code),
        month=app.get_core_string('date_month_' + str(date.month), default=date.month, lang_code=lang_code),
        day_week=app.get_core_string('date_weekday_' + str(day_week), default=day_week, lang_code=lang_code),
        year=date.year,
        timezone=timezone_to_string(-tz),
        lang_code=lang_code,
    )

    return string


def timezone_to_string(tz):
    return ('-' if tz < 0 else '+') + str(int(abs(tz))) + \
        (f':{int(abs(tz) * 60 % 60)}' if int(tz) != tz else '')
