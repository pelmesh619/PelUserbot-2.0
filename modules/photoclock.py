import io
import logging
import os
import time
import asyncio
import datetime
from typing import Tuple

from pyrogram import Client, filters

from PIL import Image, ImageFont, ImageDraw, ImageFilter

from core import Module, Author

from . import weather
from .weather import get_weather_raw_data

log = logging.getLogger(__name__)

module = Module(
    module_id='photoclock',
    name='string_id=test_module_name',
    description='string_id=description',
    authors=Author('pelmeshke', telegram_username='pelmeshke', job='string_id=author_creator'),
    version='v1.0.0',
    strings={
        'ru': {
            'temperature': '{temp}{units}',
            'feels_like': 'Ощущается как {temp}{units}',
            'wind': 'Ветер: {speed}{units} {direction}',
            "units_temp_metric": "°C",
            "units_temp_imperial": "°F",
            "units_temp_standard": "K",
            "units_wind_metric": "м/с",
            "units_wind_imperial": "миль/ч",
            "units_wind_standard": "м/с",

            'wind_direction_0': 'С',
            'wind_direction_45': 'СВ',
            'wind_direction_90': 'В',
            'wind_direction_135': 'ЮВ',
            'wind_direction_180': 'Ю',
            'wind_direction_225': 'ЮЗ',
            'wind_direction_270': 'З',
            'wind_direction_315': 'СЗ',
            'wind_direction_360': 'С',

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
            'clock_was_turned_on': '<b>Часы включены</b>',
            'clock_was_turned_off': '<b>Часы выключены</b>',
        }
    },
    config={
        'size': [1024, 1024],
        'nixie_tube_font_filename': 'NixieOne-Regular.ttf',
        'comfortaa_font_filename': 'Comfortaa.ttf',

    }
)
module.is_turned_on = False


@Client.on_message(filters.me & filters.command('photoclock'))
async def turning(app, message):
    if module.is_turned_on:
        module.is_turned_on = False
        await delete_photos(app, is_stopped=True)

        await message.edit(message.get_string('clock_was_turned_off'))
    else:
        module.is_turned_on = True
        await message.edit(message.get_string('clock_was_turned_on'))
        await cycle(app)


def get_weather(app):
    weather_raw_data = get_weather_raw_data()
    weather.module.app = app
    units = weather.module.get_config_parameter('units')

    if weather_raw_data:
        weather_raw_data = weather_raw_data['current']
        weather_data = [
            app.get_string(
                'temperature',
                temp=round(weather_raw_data['temp'], 1),
                units=app.get_string(f'units_temp_{units}', _module_id=module.module_id),
                _module_id=module.module_id
            ),
            app.get_string(
                'weather_type_' + str(weather_raw_data['weather'][0]['id']),
                _module_id=module.module_id
            ),
            app.get_string(
                'feels_like',
                temp=round(weather_raw_data['feels_like'], 1),
                units=app.get_string(f'units_temp_{units}', _module_id=module.module_id),
                _module_id=module.module_id
            ),
            app.get_string(
                'wind',
                speed=round(weather_raw_data['wind_speed'], 1),
                units=app.get_string(f'units_wind_{units}', _module_id=module.module_id),
                direction=app.get_string(
                    f'wind_direction_{round(weather_raw_data["wind_deg"] / 45) * 45}',
                    _module_id=module.module_id
                ),
                _module_id=module.module_id
            )
        ]
    else:
        weather_data = []

    return weather_data


async def cycle(app):
    old_time = 0
    weather_data = []
    while module.is_turned_on:
        if not module.is_turned_on:
            break

        now = datetime.datetime.now()

        current_time = (now.hour, now.minute)

        if current_time != old_time:
            if now.minute % 5 == 0 or old_time == 0:
                weather_data = get_weather(app)

            photo = get_photo(weather_data=weather_data)
            await app.set_profile_photo(photo=photo)

            old_time = current_time

            await delete_photos(app)

        if not module.is_turned_on:
            break

        await asyncio.sleep(2.5)


async def delete_photos(app, is_stopped=False):
    photos_to_delete = []
    async for i in app.get_chat_photos('me'):
        if i and ((10 if not is_stopped else -1) < time.time() - i.date.timestamp() < 5 * 60):
            photos_to_delete.append(i.file_id)

    try:
        await app.delete_profile_photos(photos_to_delete)

    except Exception as e:
        print(photos_to_delete, repr(e), sep='\n')
    else:
        print('deleted')


def get_photo(weather_data=None):
    current_time = datetime.datetime.now()
    text = str(current_time.hour) + ':' + str(current_time.minute).zfill(2)

    nixie_tube_font = open(
        os.path.join(
            module.app.get_config_parameter('resources_directory'),
            module.get_config_parameter('nixie_tube_font_filename')
        ), 'rb'
    ).read()
    comfortaa_font = open(
        os.path.join(
            module.app.get_config_parameter('resources_directory'),
            module.get_config_parameter('comfortaa_font_filename')
        ), 'rb'
    ).read()

    clock_font = ImageFont.truetype(io.BytesIO(nixie_tube_font), size=320)

    size = (1024, 1024)

    if current_time.hour >= 20 or current_time.hour <= 8:
        text_color = (238, 113, 11)
        halo_color = (193, 49, 14)
        stroke_color = (209, 55, 5)
        background_color = (14, 8, 59)
        stroke_width = 2
        halo_range = (1, 22, 5)
        gaussian_filter_radius = 20

    else:
        text_color = (11, 80, 146)
        halo_color = (50, 130, 170)
        stroke_color = (30, 100, 146)
        background_color = (255, 255, 255)
        stroke_width = 2
        halo_range = (1, 11, 5)
        gaussian_filter_radius = 10

    image = draw_image_with_clock(
        text, clock_font, size,
        background_color, text_color, halo_color, stroke_color,
        stroke_width, halo_range, gaussian_filter_radius
    )
    image_canvas = ImageDraw.Draw(image)

    if weather_data:
        draw_weather_info(image_canvas, weather_data, comfortaa_font, size, text_color)

    output = io.BytesIO()
    output.name = 'photoclock.png'
    image.save(output, "PNG")
    output.seek(0)

    return output


def draw_text_with_halo(
        text: str,
        font: ImageFont,
        size: Tuple[int, int],
        text_color: Tuple[int, int, int],
        halo_color: Tuple[int, int, int],
        stroke_color: Tuple[int, int, int],
        stroke_width: int = 2,
        halo_range: Tuple[int, int, int] = (1, 22, 5),
        gaussian_filter_radius: int = 20
):
    text_image = Image.new('RGBA', size, (0, 0, 0, 0))
    text_canvas = ImageDraw.Draw(text_image)

    clock_text_size = text_canvas.textbbox((0, 0), text, font=font)
    clock_text_size = clock_text_size[2], clock_text_size[3]
    clock_text_position = (size[0] - clock_text_size[0]) // 2, (size[1] - clock_text_size[1]) // 2

    x, y = clock_text_position

    # Drawing a stroke
    text_canvas.text((x - stroke_width, y - stroke_width), text, font=font, fill=stroke_color)
    text_canvas.text((x + stroke_width, y - stroke_width), text, font=font, fill=stroke_color)
    text_canvas.text((x - stroke_width, y + stroke_width), text, font=font, fill=stroke_color)
    text_canvas.text((x + stroke_width, y + stroke_width), text, font=font, fill=stroke_color)

    # Drawing a text
    text_canvas.text(clock_text_position, text, font=font, fill=text_color)

    if not halo_color:
        return text_image

    halo_image = Image.new('RGBA', size, (0, 0, 0, 0))

    halo_canvas = ImageDraw.Draw(halo_image)

    # Drawing multiple times sames text but with offset
    for i in range(*halo_range):
        for j in range(*halo_range):
            halo_canvas.text((x - i, y - j), text, font=font, fill=halo_color)
            halo_canvas.text((x + i, y - j), text, font=font, fill=halo_color)
            halo_canvas.text((x - i, y + j), text, font=font, fill=halo_color)
            halo_canvas.text((x + i, y + j), text, font=font, fill=halo_color)

    # Then blurring this mess with gaussian filter
    halo_image = halo_image.filter(ImageFilter.GaussianBlur(gaussian_filter_radius))

    halo_image.paste(text_image, (0, 0), text_image)

    return halo_image


def draw_image_with_clock(
        text: str,
        font: ImageFont,
        size: Tuple[int, int],
        background_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int],
        halo_color: Tuple[int, int, int],
        stroke_color: Tuple[int, int, int],
        stroke_width: int = 2,
        halo_range: Tuple[int, int, int] = (1, 22, 5),
        gaussian_filter_radius: int = 20
):
    background_image = Image.new('RGB', size, background_color)
    text_image = draw_text_with_halo(
        text, font, size,
        text_color, halo_color, stroke_color,
        stroke_width, halo_range, gaussian_filter_radius
    )

    background_image.paste(text_image, (0, 0), text_image)
    return background_image


def draw_weather_info(image_canvas, weather_data, font, size, text_color):
    first_line_font = ImageFont.truetype(io.BytesIO(font), int(size[1] / 8))

    first_line_position = int(size[0] * (13 / 40)), int(size[1] * (1 / 10))
    image_canvas.text(first_line_position, weather_data[0],
                      font=first_line_font, fill=text_color, align='left')

    next_lines_font = ImageFont.truetype(io.BytesIO(font), int(size[1] / 30))
    next_lines = '\n'.join(weather_data[1:])

    next_lines_position = int(size[0] * (13 / 40)), int(size[1] * (15 / 66))
    image_canvas.multiline_text(next_lines_position, next_lines,
                                font=next_lines_font, fill=text_color, align='left')
