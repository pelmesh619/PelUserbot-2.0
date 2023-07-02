import io
import os
import textwrap

from pyrogram import Client, filters
from pyrogram import types
import requests
import pilmoji
from PIL import Image, ImageDraw, ImageFont, ImageChops

from core.bot_types import Module, pelmeshke


module = Module(
    name='string_id=module_name',
    description='string_id=description',
    authors=pelmeshke,
    version='v1.0.0',
    release_date='13-04-2023',
    strings={
        'ru': {
            'module_name': 'Демотиватор',
            'description': 'Создаёт демотиватор из фото с подписью (попробуйте сами, чтобы понять). '
                           'Также создает "мем славика".',
        },
    },
    requirements=[],
    changelog={},
    config={
        'photo_size': [1536, 1536],
        'default_caption': 'ГДЕ ПОДПИСЬ, БЛЯДЬ!!!',

    }

)

LOBSTER_FONT = requests.get('https://github.com/pelmesh619/fonts/blob/main/Lobster.ttf?raw=true').content
TIMESNEWROMAN_FONT = requests.get('https://github.com/pelmesh619/fonts/blob/main/TimesNewRoman.ttf?raw=true').content


@Client.on_message(filters.me & filters.reply & filters.command('demot'))
async def demotivator_handler(peluserbot, message):
    photo = message.reply_to_message.photo or message.reply_to_message.from_user.photo.big_file_id

    await message.edit_text('🔄<b>Скачиваю фото</b>🔄')
    photo_path = await peluserbot.download_media(photo, in_memory=True)

    caption = ' '.join(message.text.split(' ')[1:]) or \
              message.reply_to_message.text or \
              message.reply_to_message.caption or \
              module.get_config_parameter('default_caption')

    await message.edit_text('🔄<b>Фотожоплю</b>🔄')

    out = await demotivator(photo_path, caption, module.get_config_parameter('photo_size'))

    await message.edit_text('🔄<b>Отправляю</b>🔄')

    await message.reply_to_message.reply_photo(out)
    await message.delete()


async def demotivator(file, caption, size):
    image = Image.open(file)

    black_image = Image.new('RGB', size, (0, 0, 0))

    image = image.resize((int(size[0] * .8), int(size[1] * .7)))

    black_image.paste(image, (int(size[0] * .1), int(size[1] * 0.05)))

    text_image = Image.new("RGB", black_image.size, (0, 0, 0))

    font = ImageFont.truetype(io.BytesIO(TIMESNEWROMAN_FONT), size[1] // 20)

    d = ImageDraw.Draw(text_image)

    text_xy = d.multiline_textsize(caption, font=font)
    text_xy = (size[0] - text_xy[0]) // 2, (size[1] * 0.25 - text_xy[1]) // 2 + int(size[1] * 0.75)

    if text_xy[0] < 0:
        caption = '\n'.join(textwrap.wrap(caption, width=40))

    text_xy = d.multiline_textsize(caption, font=font)
    text_xy = (size[0] - text_xy[0]) // 2, (size[1] * 0.25 - text_xy[1]) // 2 + int(size[1] * 0.75)

    with pilmoji.Pilmoji(text_image) as pilmoji_:
        pilmoji_.text(
            (int(text_xy[0]), int(text_xy[1])),
            caption.strip(),
            fill=(255, 255, 255),
            font=font,
            align='center'
        )

    lines_xy = (
        int(size[0] * .1 - size[0] * .01),
        int(size[0] * .9 + size[0] * .01),
        int(size[1] * 0.05 - size[1] * 0.01),
        int(size[1] * 0.75 + size[1] * 0.01),
    )

    d.line(((lines_xy[0], lines_xy[2]), (lines_xy[0], lines_xy[3])), width=int(size[0] * .005))
    d.line(((lines_xy[1], lines_xy[2]), (lines_xy[1], lines_xy[3])), width=int(size[0] * .005))
    d.line(((lines_xy[0], lines_xy[2]), (lines_xy[1], lines_xy[2])), width=int(size[0] * .005))
    d.line(((lines_xy[0], lines_xy[3]), (lines_xy[1], lines_xy[3])), width=int(size[0] * .005))

    out = ImageChops.add(black_image, text_image)

    output = io.BytesIO()
    output.name = 'demot.png'
    out.save(output, "PNG")
    output.seek(0)

    return output





async def slavik(file, caption):
    image = Image.open(file)
    d = ImageDraw.Draw(image)

    i = image.size[1] // 12
    while i > 0:
        font = ImageFont.truetype(io.BytesIO(LOBSTER_FONT), i)
        text_xy = d.multiline_textsize(caption, font=font)

        if text_xy[0] < image.size[0] * .9:
            break
        i -= 2

    text_xy = (image.size[0] - text_xy[0]) // 2, image.size[1] - image.size[1] // 8
    d.multiline_text((text_xy[0] + 1, text_xy[1] + 1), caption, font=font, fill=(0, 0, 0), align='center')
    d.multiline_text(text_xy, caption, font=font, fill=(255, 255, 255), align='center')

    out = io.BytesIO()
    out.name = 'slavik.png'
    image.save(out, "PNG")
    out.seek(0)

    print('done')
    return out


async def slavik_gif(path, caption):
    gif = Image.open(path)
    size = gif.size

    images = []

    for i in range(gif.n_frames):
        gif.seek(i)
        image = gif.convert('RGBA')

        d = ImageDraw.Draw(image)
        if i == 0:
            j = size[1] // 10
            while j > 0:
                font = ImageFont.truetype(io.BytesIO(LOBSTER_FONT), j)
                text_xy = d.multiline_textsize(caption, font=font)

                if text_xy[0] < size[0] * .9:
                    break
                j -= 2

            text_xy = (size[0] - text_xy[0]) // 2, size[1] - size[1] // 7
        d.multiline_text((text_xy[0] + 1, text_xy[1] + 1), caption, font=font, fill=(0, 0, 0), align='center')
        d.multiline_text(text_xy, caption, font=font, fill=(255, 255, 255), align='center')

        images.append(image)

    out = io.BytesIO()
    out.name = 'slavik.gif'
    images[0].save(out, 'GIF', save_all=True, append_images=images[1:], optimize=True)
    out.seek(0)

    print('done')
    return out


