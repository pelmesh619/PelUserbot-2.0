import re

import pyrogram
from pyrogram import Client, filters
import googletrans

from core import Module, Author

module = Module(
    name='string_id=module_name',
    author=Author('pelmeshke', telegram_username='@pelmeshke', job='string_id=creator'),
    version='v1.0.0',
    description='string_id=description',
    strings={
        'ru': {
            'module_name': 'Переводчик',
            'creator': 'Создатель',
            'description': 'Переводит текст по команде /trans',
            'translating': '<b>Переводиться...</b>',
            'translation': '[Перевод] <i>{text}</i>',
            'enter_text_to_translate': 'Введите текст для перевода или ответьте командой на переводимый текст',
            'destination_language_was_not_found': '\n\n<b>Язык перевода не был найден, '
                                                  'язык перевода по умолчанию был использован</b>'

        }
    },

    requirements=[],
    changelog={},
    config={
        'default_destination_language': 'ru'
    }
)


def are_all_letters_latin(string):
    for i in string:
        if not (97 <= ord(i) <= 122 or ord(i) == 45):
            return False

    return True


def is_language_code(code):
    if code in googletrans.LANGUAGES:
        return True


def is_like_language_code(code):
    return re.fullmatch(r'([a-z]{2}(([a-z])|(-[a-z]{2}))?)', code)


@Client.on_message(filters.me & filters.command('trans'))
async def translate_handler(app, message):
    await message.edit_text(module.get_string('translating'))

    args = message.command[1:]
    if args and is_like_language_code(args[0]):
        destination_language = args[0]
        text = ' '.join(args[1:])
    else:
        destination_language = app.get_config_parameter('default_destination_language', app.lang_code)
        text = ' '.join(args[0:])


    if not text and message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    elif not text:
        await message.edit_text(module.get_string('enter_text_to_translate'))
        return

    if destination_language not in googletrans.LANGUAGES:
        warning = module.get_string('destination_language_was_not_found', destination_language=destination_language)
        if args[1:]:
            text = ' '.join(args[0:])
        destination_language = app.get_config_parameter('default_destination_language', app.lang_code)

    else:
        warning = ''

    translation_client = googletrans.Translator()
    source_language = 'auto'  # TODO selecting source language
    respond = translation_client.translate(text, src=source_language, dest=destination_language)

    await message.edit_text(
        module.get_string('translation', text=respond.text) + warning,
        parse_mode=pyrogram.enums.ParseMode.HTML
    )

# TODO more information about translation via command
