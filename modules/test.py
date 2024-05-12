from pyrogram import Client, filters
from core import Module, Author, Peluserbot

__version__ = 'v1.2.0-epsilon'

from core.bot_types import bot_filters

module = Module(
    module_id='test',
    name='string_id=test_module_name',
    description='string_id=description',
    authors=Author('pelmeshke', telegram_username='pelmeshke', job='string_id=author_creator'),
    version=__version__,
    release_date='08-01-2023',
    strings={
        'ru': {
            'test_module_name': 'Тестовый модуль',
            'description': 'Модуль проверяет работоспособность бота через команду {_cmd_pref}test',
            'author_creator': 'Создатель',
            'bot_works': 'Бот работает',
            'test_error': 'Тестовая ошибка',
            'docs_test_handler': 'На команду `{_cmd_pref}test` отвечает ответным сообщением. Если сообщение не было '
                                 'отправлено, то с ботом что-то не так. Не принимает аргументов.',
            'docs_test_from_me_handler': 'На команду `!test` изменяет сообщение. Если сообщение не было '
                                         'изменено, то с ботом что-то не так. Не принимает аргументов.',
            'runtime_error_is_raised': 'Во время обработки вашего запроса возникла ошибка: {details}',
            'changelog_v1.0.0': 'Релиз',
            'name': 'имя: {name}',

        },
        'en': {
            'test_module_name': 'Test module',
            'description': 'Module checks bot\'s working',
            'author_creator': 'Creator',
            'bot_works': 'Bot works',
            'test_error': 'Testing error',
            'docs_test_handler': 'Replies message on command `{_cmd_pref}test`. If message was not sent there is '
                                 'something wrong with bot. Does not take any arguments.',
            'docs_test_from_me_handler': 'Edits message on command `!test`. If message was not edited '
                                         'there is something wrong with bot. Does not take any arguments.',
            'changelog_v1.0.0': 'Release',

        },
    },
    strings_source_filename=None,
    update_source_link='https://raw.githubusercontent.com/pelmesh619/Peluserbot-2.0-Modules/main/test.py',
    config={},
    requirements=[],
    changelog={
        "v1.0.0": "string_id=changelog_v1.0.0",
    }
)


@Client.on_message(filters.command('test'))
async def test_handler(_, msg):
    """string_id=docs_test_handler
    Replies message on command `/test`. If message was not sent there is something wrong with bot.
    Does not take any arguments.
    """
    await msg.reply(module.get_string('bot_works'))


@Client.on_message(filters.command('test', ['!']) & filters.me)
async def test_from_me_handler(_, msg):
    """string_id=docs_test_from_me_handler
    Edits message on command `!test`. If message was not edited there is something wrong with bot.
    Does not take any arguments.
    """
    await msg.edit(module.get_string('bot_works'))


@Client.on_message(filters.command('error'))
async def error_handler(_, msg):
    raise RuntimeError(msg.get_string('test_error'))


@Peluserbot.on_error(bot_filters.exception(RuntimeError))
async def error_catcher(_, msg):
    await msg.reply(msg.get_string('runtime_error_is_raised', details=msg.exception.args[0]))



