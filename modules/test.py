import asyncio

from pyrogram import Client, filters
from core import Module, Author

__version__ = '1.1.0'

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
            'description': 'Модуль проверяет работоспособность бота',
            'author_creator': 'Создатель',
            'bot_works': 'Бот работает',
            'docs_test_handler': 'На команду ``/test`` отвечает ответным сообщением. Если сообщение не было '
                                 'отправлено, то с ботом что-то не так. Не принимает аргументов.',
            'changelog_v1.0.0-alpha': 'Пре-релиз, добавлена команда ``/test``',
            'changelog_v1.0.0': 'Релиз',
            'changelog_v1.1.0': 'Добавлена команда ``.test``, работающая только от имени пользователя',

        },
        'en': {
            'test_module_name': 'Test module',
            'description': 'Module checks bot\'s working',
            'author_creator': 'Creator',
            'bot_works': 'Bot works',
            'docs_test_handler': 'Replies message on command ``/test``. If message was not sent there is something '
                                 'wrong with bot. Does not take any arguments.',
            'changelog_v1.0.0-alpha': 'Pre-release, added command ``/test``',
            'changelog_v1.0.0': 'Release',
            'changelog_v1.1.0': 'Added command ``.test`` working only from account itself ',
            'huh': 'sj'
        },
    },
    strings_source_filename=None,
    config={},
    requirements=[],
    changelog={
        "v1.0.0-alpha": 'string_id=changelog_v1.0.0-alpha',
        "v1.0.0": "string_id=changelog_v1.0.0",
        "v1.1.0": "string_id=changelog_v1.1.0"
    }
)


@Client.on_message(filters.command('test'))
async def test_handler(_, msg):
    """string_id=docs_test_handler
    Replies message on command ``/test``. If message was not sent there is something wrong with bot.
    Does not take any arguments.
    """
    await msg.reply(module.get_string('bot_works'))


@Client.on_message(filters.command('test', ['!']) & filters.me)
async def test_from_me_handler(_, msg):
    """
    Edits message on command ``.test``. If message was not edited there is something wrong with bot.
    Does not take any arguments.
    """
    await msg.edit(module.get_string('bot_works'))




@Client.on_message(filters.me & filters.command('bar_test'))
async def test_bars_handler(_, message):
    from utils import bot_utils
    n = 17

    respond = 'Тест 1-ого бара: \n<code>{}</code>'
    message = await message.edit(respond)
    func = bot_utils.get_progress_func(
        message,
        progress_type='bar',
        bar_length=20,
        bar_type=0,
        bar_place_value='left',
        bar_brackets=('[', ']')
    )
    for i in range(n+1):
        message = await func(i / n, 1)
        await asyncio.sleep(0.2)

    respond = message.text.html + '\nТест 3-ого бара:\n<code>{}</code>'
    message = await message.edit(respond)
    func = bot_utils.get_progress_func(
        message,
        progress_type='bar',
        bar_length=20,
        bar_type=2,
        bar_place_value='right',
    )
    for i in range(n+1):
        message = await func(i / n, 1)
        await asyncio.sleep(0.2)

    respond = message.text.html + '\nТест 4-ого бара:\n<code>{}</code>'
    message = await message.edit(respond)
    func = bot_utils.get_progress_func(
        message,
        progress_type='bar',
        bar_length=20,
        bar_type=3,
        bar_place_value='follow',
    )
    for i in range(n+1):
        message = await func(i / n, 1)
        await asyncio.sleep(0.2)

    respond = message.text.html + '\nТест 5-ого бара:\n<code>{}</code>'
    message = await message.edit(respond)
    func = bot_utils.get_progress_func(
        message,
        progress_type='bar',
        bar_length=20,
        bar_type=4,
        bar_place_value='middle',
    )
    for i in range(n+1):
        message = await func(i / n, 1)
        await asyncio.sleep(0.2)

    respond = message.text.html + '\nТест 6-ого бара:\n<code>{}</code>'
    message = await message.edit(respond)
    func = bot_utils.get_progress_func(
        message,
        progress_type='bar',
        bar_length=30,
        bar_type=5,
        bar_place_value='follow',
    )
    for i in range(51):
        await func(i / 50, 1)
        await asyncio.sleep(3)
