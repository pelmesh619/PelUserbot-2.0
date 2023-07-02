import json
import datetime
import re

import requests

from pyrogram import Client, filters
from core import Module, Author

PUBLIC_API_KEY = 'eb78e92a555e98fa454b38da71c816c9'

module = Module(
    name='string_id=module_name',
    authors=Author('pelmeshke', telegram_username='i44444444444444i', job='string_id=creator'),
    strings_source_filename='weather.json',
    config={
        'api_key': PUBLIC_API_KEY,
        'latitude': 55.75,
        'longitude': 37.5,
        'units': None,
        'lang': 'ru'
    }
)

API_ENDPOINT = 'https://api.openweathermap.org/data/2.5/onecall'
GEOCODING_API_ENDPOINT = 'http://api.openweathermap.org/geo/1.0/direct'
REVERSE_GEOCODING_API_ENDPOINT = 'http://api.openweathermap.org/geo/1.0/reverse'
TIME_FORMAT = '%H:%M:%S %d.%m'


def format_coords(message, lat, lon):
    return '{} {}, {} {}'.format(
        round(lat, 6),
        message.get_string('north_latitude' if lat > 0 else 'south_latitude'),
        round(lon, 6),
        message.get_string('east_longitude' if lon > 0 else 'west_longitude'),
    )


def get_city_name(message, lat, lon, default=None):
    city_name_result = requests.get(
        REVERSE_GEOCODING_API_ENDPOINT,
        params={
            'appid': module.get_config_parameter('api_key'),
            'lat': lat,
            'lon': lon,
            'limit': 1
        }
    )

    if city_name_result.status_code == 200:
        city_name_result = json.loads(city_name_result.text)
        if city_name_result:
            answer = city_name_result[0]
            local_name = answer['name']
            if 'local_names' in answer:
                local_name = answer['local_names'].get(
                    module.get_config_parameter('lang'),
                    list(answer['local_names'].values())[0]
                )

            country = (' (' + message.get_string('country_' + answer['country'], default=answer['country']) + '{})') \
                if 'country' in answer else ''
            state = (', ' + answer['state']) if 'state' in answer else ''

            country = country.format(state)

            return message.get_string('city_short_template', name=local_name, country=country)

    if default is not None:
        return format_coords(message, lat, lon)
    return default



def get_weather_raw_data(**weather_parameters):
    if not weather_parameters:
        weather_parameters = {
            'appid': PUBLIC_API_KEY,
            'lat': 50.5519,
            'lon': 36.574,
            'units': 'metric',
            'lang': 'ru'
        }

    weather_parameters['exclude'] = 'minutely,hourly,daily'

    result = requests.get(
        API_ENDPOINT,
        params=weather_parameters
    )

    if result.status_code == 200:
        return json.loads(result.text)

    return result


@Client.on_message(filters.me & filters.command('weather'))
async def weather_today_handler(_, message):
    weather_module_config = module.get_config()

    if not weather_module_config['api_key']:
        return  # fuck

    if not weather_module_config['longitude'] and not weather_module_config['latitude']:
        return  # fuck

    if not weather_module_config['longitude']:
        return  # fuck

    if not weather_module_config['latitude']:
        return  # fuck

    units = weather_module_config['units'] or 'metric'

    await message.edit(module.get_string('api_request'))
    result = get_weather_raw_data(
        appid=weather_module_config['api_key'],
        lat=weather_module_config['latitude'],
        lon=weather_module_config['longitude'],
        units=units,
        lang=weather_module_config['lang']
    )

    if isinstance(result, dict):
        city_name = get_city_name(
            message,
            weather_module_config['latitude'],
            weather_module_config['longitude']
        )

        respond = module.get_string(
            'today_template',
            name=city_name,
            emoji=module.get_string('weather_emoji_' + result['current']['weather'][0]['main']),
            description=module.get_string('weather_type_' + str(result['current']['weather'][0]['id'])),
            temp_value=round(result['current']['temp'], 1),
            feels_like_value=round(result['current']['feels_like'], 1),
            temp_units=module.get_string('units_temp_' + units),
            wind_value=round(result['current']['wind_speed'], 1),
            wind_units=module.get_string('units_wind_' + units),
            direction=module.get_string('wind_direction_' + str(result['current']['wind_deg'] // 45 * 45)),
            pressure_value=round(result['current']['pressure'] / 10, 1),
            pressure_bar_value=round(result['current']['pressure'] / 1000, 1),
            humidity_value=result['current']['humidity'],
            clouds_value=result['current']['clouds'],
            sunrise_dt=datetime.datetime.fromtimestamp(
                result['current']['sunrise'] + result['timezone_offset']).strftime(TIME_FORMAT),
            sunset_dt=datetime.datetime.fromtimestamp(result['current']['sunset'] + result['timezone_offset']).strftime(
                TIME_FORMAT),
        )

        if result.get('alerts', None):
            respond += '\n\n' + '\n'.join(
                [
                    module.get_string(
                        'alert',
                        sender=(module.get_string('warns', sender=alert['sender_name']) + ': \n') if alert[
                            'sender_name'] else '',
                        start_dt=datetime.datetime.fromtimestamp(alert['start'] + result['timezone_offset']).strftime(
                            TIME_FORMAT),
                        end_dt=datetime.datetime.fromtimestamp(alert['end'] + result['timezone_offset']).strftime(
                            TIME_FORMAT),
                        event=alert['event'],
                        description=alert['description']

                    )
                    for alert in result['alerts']
                ]
            )

        await message.edit(respond)

    else:
        print('error', getattr(result, 'status', None), result.text)


@Client.on_message(filters.me & filters.command('weather_forecast'))
async def weather_forecast_handler(_, message):
    weather_module_config = module.get_config()

    if not weather_module_config['api_key']:
        return  # fuck

    if not weather_module_config['longitude'] and not weather_module_config['latitude']:
        return  # fuck

    if not weather_module_config['longitude']:
        return  # fuck

    if not weather_module_config['latitude']:
        return  # fuck

    units = weather_module_config['units'] or 'metric'

    await message.edit(module.get_string('api_request'))
    result = requests.get(
        API_ENDPOINT,
        params={
            'appid': weather_module_config['api_key'],
            'lat': weather_module_config['latitude'],
            'lon': weather_module_config['longitude'],
            'exclude': 'current,minutely,hourly,alerts',
            'units': units,
            'lang': weather_module_config['lang'] or 'ru'
        }
    )

    if result.status_code == 200:
        result = json.loads(result.text)
        print(result)

        days_forecast = []

        for day in result['daily']:
            days_forecast.append(
                message.get_string(
                    'day_template',
                    date=message.get_string.date_to_string(day['dt']),
                    emoji=module.get_string('weather_emoji_' + day['weather'][0]['main']),
                    description=module.get_string('weather_type_' + str(day['weather'][0]['id'])),
                    temp_day_value=round(day['temp']['day'], 1),
                    temp_night_value=round(day['temp']['night'], 1),
                    feels_like_day_value=round(day['feels_like']['day'], 1),
                    feels_like_night_value=round(day['feels_like']['night'], 1),
                    temp_units=module.get_string('units_temp_' + units),
                    wind_value=round(day['wind_speed'], 1),
                    wind_units=module.get_string('units_wind_' + units),
                    direction=module.get_string('wind_direction_' + str(day['wind_deg'] // 45 * 45)),
                    pressure_value=round(day['pressure'] / 10, 1),
                    humidity_value=day['humidity'],
                    clouds_value=day['clouds'],
                )
            )

        respond = module.get_string(
            'forecast_template',
            coords='{} {}, {} {}'.format(
                weather_module_config['latitude'],
                module.get_string('north_latitude' if weather_module_config['latitude'] > 0 else 'south_latitude'),
                weather_module_config['longitude'],
                module.get_string('east_longitude' if weather_module_config['longitude'] > 0 else 'west_longitude'),
            ),
            forecasts='\n\n'.join(days_forecast)
        )
        await message.edit(respond)

    else:
        print('error', getattr(result, 'status', None), result.text)


@Client.on_message(filters.me & filters.command('geocoding'))
async def geocoding_handler(_, message):
    if not module.get_config_parameter('api_key'):
        return  # fuck

    await message.edit(module.get_string('api_request'))
    result = requests.get(
        GEOCODING_API_ENDPOINT,
        params={
            'appid': module.get_config_parameter('api_key'),
            'q': ' '.join(message.command[1:]),
            'limit': 20
        }
    )

    if result.status_code == 200:
        result = json.loads(result.text)
        print(result)

        answers_strings = []

        for answer in result:
            local_name = None
            if 'local_names' in answer:
                local_name = answer['local_names'].get(
                    module.get_config_parameter('lang'),
                    list(answer['local_names'].values())[0]
                )
            answers_strings.append(
                message.get_string(
                    'city_answer_template',
                    name=(' (' + answer['name'] + ')') if local_name else '',
                    local_name=local_name or answer['name'],
                    country=message.get_string('country_' + answer['country'], default=answer['country']),
                    state=(', ' + answer['state']) if 'state' in answer else '',
                    coords=format_coords(message, answer['lat'], answer['lon']),
                    lat=answer['lat'],
                    lon=answer['lon'],
                )
            )

        respond = module.get_string(
            'city_answers_template',
            answers='\n\n'.join(answers_strings),
            city=' '.join(message.command[1:])
        )
        await message.edit(respond)

    else:
        print('error', getattr(result, 'status', None), result.text)


@Client.on_message(filters.me & filters.command('fuck'))
async def reverse_geocoding_handler(_, message):
    if not module.get_config_parameter('api_key'):
        return  # fuck
    if not module.get_config_parameter('latitude'):
        return  # fuck
    if not module.get_config_parameter('longitude'):
        return  # fuck

    lat = module.get_config_parameter('latitude')
    lon = module.get_config_parameter('longitude')

    await message.edit(module.get_string('api_request'))
    result = requests.get(
        REVERSE_GEOCODING_API_ENDPOINT,
        params={
            'appid': module.get_config_parameter('api_key'),
            'lat': lat,
            'lon': lon,
            'limit': 20
        }
    )

    if result.status_code == 200:
        result = json.loads(result.text)
        print(result)

        answers_strings = []

        for answer in result:
            local_name = None
            if 'local_names' in answer:
                local_name = answer['local_names'].get(
                    module.get_config_parameter('lang'),
                    list(answer['local_names'].values())[0]
                )
            answers_strings.append(
                message.get_string(
                    'city_answer_template',
                    name=(' (' + answer['name'] + ')') if local_name else '',
                    local_name=local_name or answer['name'],
                    country=message.get_string('country_' + answer['country'], default=answer['country']),
                    state=(', ' + answer['state']) if 'state' in answer else '',
                    coords=format_coords(message, answer['lat'], answer['lon']),
                    lat=answer['lat'],
                    lon=answer['lon'],
                )
            )

        respond = module.get_string(
            'reverse_city_answers_template',
            answers='\n\n'.join(answers_strings),
            coords='{} {}, {} {}'.format(
                lat,
                module.get_string('north_latitude' if lat > 0 else 'south_latitude'),
                lon,
                module.get_string('east_longitude' if lon > 0 else 'west_longitude'),
            ),
        )
        await message.edit(respond)

    else:
        print('error', getattr(result, 'status', None), result.text)


@Client.on_message(filters.me & filters.command('set_coords'))
async def set_coords_handler(_, message):
    if not len(message.command) >= 3:
        return await message.edit('fuck')

    lat, lon = message.command[1:3]

    if not re.search(r'-?\d+(\.\d+)?', lat):
        if not re.search(r'-?\d+(\.\d+)?', lon):
            return await message.edit('latlon')
        return await message.edit('lat')
    if not re.search(r'-?\d+(\.\d+)?', lon):
        return await message.edit('lon')

    lat, lon = float(lat), float(lon)

    if not -90 <= lat <= 90:
        return await message.edit('fuck')
    if not -180 <= lon <= 180:
        return await message.edit('fuck')

    old_lat = module.get_config_parameter('latitude')
    old_lon = module.get_config_parameter('longitude')

    module.set_config_parameter('latitude', lat)
    module.set_config_parameter('longitude', lon)

    old_city_name = get_city_name(message, old_lat, old_lon, default='')
    new_city_name = get_city_name(message, lat, lon, default='')

    await message.edit(
        message.get_string(
            'your_coords_was_changed',
            old_location=old_city_name,
            old_coords=format_coords(message, old_lat, old_lon),
            new_location=new_city_name,
            new_coords=format_coords(message, lat, lon),
            old_lat=old_lat,
            old_lon=old_lon
        )
    )
