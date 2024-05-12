import datetime
import json
import re
import logging

import requests
from pyrogram import Client, filters

from core.bot_types import Module, Author, ModuleDatabase

log = logging.getLogger(__name__)

module = Module(
    name='string_id=module_name',
    version='v1.0.0',
    authors=Author('pelmeshke', telegram_username='@pelmeshke'),
    description='string_id=description',
    changelog={},
    strings={
        'ru': {
            'module_name': 'Доброе утро',
            'description': 'Управляет алиасами - сокращениями команд и прочего. /aliases - посмотреть все алиасы',

            'units_temp_metric': '°C',
            'units_temp_imperial': '°F',
            'units_temp_standard': 'K',
            'units_wind_metric': 'м/с',
            'units_wind_imperial': 'миль/ч',
            'units_wind_standard': 'м/с',

            'wind_direction_0': '⬇️С',
            'wind_direction_45': '↙️СВ',
            'wind_direction_90': '⬅️В',
            'wind_direction_135': '↖️ЮВ',
            'wind_direction_180': '⬆️Ю',
            'wind_direction_225': '↗️ЮЗ',
            'wind_direction_270': '➡️З',
            'wind_direction_315': '↘️СЗ',
            'wind_direction_360': '⬇️С',

            'good_morning': 'Доброе утро, сегодня {weekday}, {day} {month} {year} года, '
                            '{time_hour}:{time_minute} {is_moscow_time}\n\n{weather_respond}',
            'good_afternoon': 'Добрый день, сегодня {weekday}, {day} {month} {year} года, '
                            '{time_hour}:{time_minute} {is_moscow_time}\n\n{weather_respond}',
            'good_evening': 'Добрый вечер, сегодня {weekday}, {day} {month} {year} года, '
                            '{time_hour}:{time_minute} {is_moscow_time}\n\n{weather_respond}',
            'good_night': 'Доброй ночи, сегодня {weekday}, {day} {month} {year} года, '
                            '{time_hour}:{time_minute} {is_moscow_time}\n\n{weather_respond}',

            'moscow_time': 'по московскому времени',
            'in_city': 'в городе {city_name}',
            'enter_city': 'Введите <code>/iamhere <ваш город></code>, чтобы я показывал погоду',

            'today_template': 'Текущая погода {city_name}\n'
                              '\n'
                              '{emoji}{description}\n'
                              '🌡Температура: {temp_value} {temp_units}\n'
                              '✋Ощущается как: {feels_like_value} {temp_units}\n'
                              '💨Ветер: {wind_value} {wind_units}, {direction}\n'
                              '💧Влажность: {humidity_value}%\n'
                              '☁Облачность: {clouds_value}%\n',

            'your_city_was_changed_to': 'Ваше местоположение было изменено на {city_name} (<code>{lat}, {lon}</code>)',


            'weather_emoji_Thunderstorm': '🌩',
            'weather_emoji_Drizzle': '🌧',
            'weather_emoji_Rain': '🌧',
            'weather_emoji_Snow': '🌨',
            'weather_emoji_Mist': '🌫',
            'weather_emoji_Smoke': '🌫',
            'weather_emoji_Haze': '🌫',
            'weather_emoji_Fog': '🌫',
            'weather_emoji_Dust': '🌫',
            'weather_emoji_Sand': '🌫',
            'weather_emoji_Ash': '🌫',
            'weather_emoji_Squall': '💨',
            'weather_emoji_Tornado': '🌪',
            'weather_emoji_Clear': '☀️',
            'weather_emoji_Clouds': '⛅️',

            'weather_type_200': 'Гроза с небольшим дождем',
            'weather_type_201': 'Гроза с дождем',
            'weather_type_202': 'Гроза с сильным дождем',
            'weather_type_210': 'Слабая гроза',
            'weather_type_211': 'Гроза',
            'weather_type_212': 'Сильная гроза',
            'weather_type_221': 'Рваная гроза',
            'weather_type_230': 'Гроза с мелкой моросью',
            'weather_type_231': 'Гроза с моросью',
            'weather_type_232': 'Гроза с сильным дождем',
            'weather_type_300': 'Сильный изморось',
            'weather_type_301': 'Морось',
            'weather_type_302': 'Сильный изморось',
            'weather_type_310': 'Моросящий дождь с интенсивностью света',
            'weather_type_311': 'Моросящий дождь',
            'weather_type_312': 'Сильный моросящий дождь',
            'weather_type_313': 'Ливень и морось',
            'weather_type_314': 'Сильный ливневый дождь и изморось',
            'weather_type_321': 'Морось под дождем',
            'weather_type_500': 'Небольшой дождь',
            'weather_type_501': 'Умеренный дождь',
            'weather_type_502': 'Сильный дождь',
            'weather_type_503': 'Очень сильный дождь',
            'weather_type_504': 'Сильный дождь',
            'weather_type_511': 'Ледяной дождь',
            'weather_type_520': 'Сильный ливневый дождь',
            'weather_type_521': 'Ливень под дождем',
            'weather_type_522': 'Сильный ливневый дождь',
            'weather_type_531': 'Рваный ливневый дождь',
            'weather_type_600': 'Легкий снег',
            'weather_type_601': 'Снег',
            'weather_type_602': 'Сильный снегопад',
            'weather_type_611': 'Мокрый снег',
            'weather_type_612': 'Лёгкий дождь с мокрым снегом',
            'weather_type_613': 'Снежный дождь',
            'weather_type_615': 'Небольшой дождь со снегом',
            'weather_type_616': 'Дождь и снег',
            'weather_type_620': 'Легкий снегопад',
            'weather_type_621': 'Снег ливня',
            'weather_type_622': 'Сильный снегопад',
            'weather_type_701': 'Туман',
            'weather_type_711': 'Дым',
            'weather_type_721': 'Дымка',
            'weather_type_731': 'Вихри песка и пыли',
            'weather_type_741': 'Туман',
            'weather_type_751': 'Песок',
            'weather_type_761': 'Пыль',
            'weather_type_762': 'Вулканический пепел',
            'weather_type_771': 'Шквалы',
            'weather_type_781': 'Торнадо',
            'weather_type_800': 'Чистое небо',
            'weather_type_801': 'Мало облаков: 11-25%',
            'weather_type_802': 'Рассеянные облака: 25-50%',
            'weather_type_803': 'Разрозненные облака: 51-84%',
            'weather_type_804': 'Облачность: 85-100%',
        },
        'en': {
        },
    },
    database=ModuleDatabase(
        schema='CREATE TABLE IF NOT EXISTS users (\n'
               'user_id BIGINT PRIMARY KEY,\n'
               'latitude REAL,\n'
               'longitude REAL,\n'
               'timezone INT\n'
               ');'
    )
)


def wrap_quote(string):
    if ' ' in string:
        return '"' + string + '"'
    return string


GEOCODING_API_ENDPOINT = "http://api.openweathermap.org/geo/1.0/direct"
API_ENDPOINT = "http://api.openweathermap.org/geo/1.0/reverse"
WEATHER_API_ENDPOINT = "https://api.openweathermap.org/data/2.5/onecall"
API_KEY = "eb78e92a555e98fa454b38da71c816c9"


@Client.on_message(
    (filters.regex('^доброе *утро', re.IGNORECASE) |
    filters.regex('^добрый *день', re.IGNORECASE) |
    filters.regex('^добрый *вечер', re.IGNORECASE) |
    filters.regex('^доброй *ночи', re.IGNORECASE)) &
    ~filters.channel
)
async def good_morning_handler(app, message):
    print(1)
    weather_respond = None
    current_time = None
    if message.from_user:
        user_info = module.database.execute_and_fetch(f'SELECT * FROM users WHERE user_id = {message.from_user.id}')

        print(user_info)
        if not user_info or message.from_user.id in [777000, ]:
            pass
        else:
            user_info = user_info[0]
            request = requests.get(
                API_ENDPOINT,
                params={
                    'lat': user_info[1],
                    'lon': user_info[2],
                    'appid': API_KEY
                }
            )

            units = 'metric'

            weather_request = requests.get(
                WEATHER_API_ENDPOINT,
                params={
                    'lat': user_info[1],
                    'lon': user_info[2],
                    'appid': API_KEY,
                    'exclude': 'daily,hourly,minutely,alerts',
                    'units': units
                }
            )

            if request.status_code != 200 or weather_request.status_code != 200:
                print(request)
                print(weather_request)
            else:
                print(request, weather_request)
                city_info = json.loads(request.text)
                weather_info = json.loads(weather_request.text)
                current_time = datetime.datetime.fromtimestamp(weather_info['current']['dt'] - 10800 + weather_info['timezone_offset'])

                if city_info:
                    city_info = city_info[0]
                    if 'local_names' in city_info:
                        if app.lang_code in city_info['local_names']:
                            city_name = city_info['local_names'][app.lang_code]
                        elif 'en' in city_info['local_names']:
                            city_name = city_info['local_names']['en']
                        else:
                            city_name = next(iter(city_info['local_names'].values()))
                    else:
                        city_name = city_info['name']
                else:
                    city_name = ''

                weather_respond = message.get_string(
                    'today_template',
                    city_name=message.get_string('in_city', city_name=city_name) if city_name else '',
                    emoji=message.get_string('weather_emoji_' + weather_info['current']['weather'][0]['main']),
                    description=message.get_string('weather_type_' + str(weather_info['current']['weather'][0]['id'])),
                    temp_value=round(weather_info['current']['temp'], 1),
                    feels_like_value=round(weather_info['current']['feels_like'], 1),
                    temp_units=message.get_string('units_temp_' + units),
                    wind_value=round(weather_info['current']['wind_speed'], 1),
                    wind_units=message.get_string('units_wind_' + units),
                    direction=message.get_string(
                        'wind_direction_' + str(weather_info['current']['wind_deg'] // 45 * 45)),
                    humidity_value=weather_info['current']['humidity'],
                    clouds_value=weather_info['current']['clouds'],
                )

    is_moscow_time = False
    if not current_time:
        current_time = datetime.datetime.now()
        is_moscow_time = True

    greet_type = 'good_morning'
    if 18 <= current_time.hour:
        greet_type = 'good_evening'
    elif 12 <= current_time.hour < 18:
        greet_type = 'good_afternoon'
    elif current_time.hour < 6:
        greet_type = 'good_night'

    respond = message.get_string(
        greet_type,
        weekday=app.get_core_string('date_weekday_' + str(current_time.isoweekday())),
        day=current_time.day,
        month=app.get_core_string('date_month_' + str(current_time.month)),
        year=current_time.year,
        time_hour=current_time.hour,
        time_minute=str(current_time.minute).zfill(2),
        is_moscow_time=message.get_string('moscow_time') if is_moscow_time else '',
        weather_respond=weather_respond if weather_respond else message.get_string('enter_city')
    )

    await message.reply(respond)


@Client.on_message(filters.command('iamhere'))
async def i_am_here_handler(app, message):
    city_name = ' '.join(message.command[1:])
    if not city_name:
        await message.reply('enter city')
        return

    if re.fullmatch('\d+(\.\d+)? +\d+(\.\d+)?', city_name):
        lat, lon = map(float, city_name.split(' '))


    request = requests.get(
        GEOCODING_API_ENDPOINT,
        params={
            'q': city_name,
            'appid': API_KEY
        }
    )

    if request.status_code != 200:
        print(request)
    else:
        city_info = json.loads(request.text)
        if not city_info:
            await message.reply('city was not found')
            return

        city_info = city_info[0]

        user_info = module.database.execute_and_fetch(f'SELECT * FROM users WHERE user_id = {message.from_user.id}')
        if not user_info:
            module.database.execute(
                f'INSERT INTO users VALUES ({message.from_user.id}, {city_info["lat"]}, {city_info["lon"]}, 0)'
            )
        else:
            module.database.execute(
                f'UPDATE users SET latitude = {city_info["lat"]}, longitude = {city_info["lon"]} '
                f'WHERE user_id = {message.from_user.id}'
            )

        if 'local_names' in city_info:
            if app.lang_code in city_info['local_names']:
                city_name = city_info['local_names'][app.lang_code]
            elif 'en' in city_info['local_names']:
                city_name = city_info['local_names']['en']
            elif city_info['local_names']:
                city_name = next(iter(city_info['local_names'].values()))
            else:
                city_name = city_info['name']
        else:
            city_name = city_info['name']

        await message.reply(
            message.get_string(
                'your_city_was_changed_to',
                city_name=city_name,
                lat=city_info["lat"],
                lon=city_info["lon"]
            )
        )




