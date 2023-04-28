import time

from pyrogram import Client, filters
from core import Module, Author

module = Module(
    name='string_id=module_name',
    description='string_id=description',
    authors=Author('pelmeshke', telegram_username='pelmeshke', job='string_id=author_creator'),
    version='v1.0.0',
    release_date='15-01-2023',
    strings={
        'ru': {
            'module_name': 'Пинг',
            'description': 'Измеряет задержку между сервером Телеграма и вашим хостингом.',
            'author_creator': 'Создатель',
            'bot_works': 'Бот работает',
            'docs_ping_handler': 'На команду ``/ping`` измеряет задержку между началом и концом запроса в '
                                 'текущем чате и в Избранном. Задержка при отправке запроса в Избранное меньше, '
                                 'потому что данные выбранного чата и данные вашего Избранного могут находиться '
                                 'в разных дата-центрах. Не принимает аргументов.',
            'ping_in_this_chat': '\nПинг в этом чате: {ping} мс',
            'ping_in_saved_messages': '\nПинг в Избранном: {ping} мс',
            'changelog_v1.0.0': 'Релиз',
        },
        'en': {
            'module_name': 'Ping',
            'description': 'Measures the latency between the Telegram server and your hosting.',
            'author_creator': 'Creator',
            'bot_works': 'Bot works',
            'docs_ping_handler': 'The response to the ``/ping`` command measures the delay between the start and '
                                 'end of the request in the current chat and in Saved Messages. '
                                 'The delay when sending a request to Saved Messages is less, '
                                 'because the data of the selected chat and the data of your Saved Messages '
                                 'may be in different data centers. Does not take arguments.',
            'ping_in_this_chat': '\nPing in this chat: {ping} ms',
            'ping_in_saved_messages': '\nPing in Saved Messages: {ping} ms',
            'changelog_v1.0.0': 'Release',
        },
    },
    strings_source_filename=None,
    requirements=[],
    changelog={
        "v1.0.0": "string_id=changelog_v1.0.0",

    },
    is_for_bot=True,
)


@Client.on_message(filters.me & filters.command('ping'))
async def ping_handler(app, message):
    """string_id=docs_ping_handler
    The response to the ``/ping`` command measures the delay between the start and
    end of the request in the current chat and in Saved Messages.
    The delay when sending a request to Saved Messages is less,
    because the data of the selected chat and the data of your Saved Messages
    may be in different data centers. Does not take arguments.
    """
    start_time = time.time()
    respond = module.get_string('bot_works')
    message = await message.reply(respond)
    time_delta_in_this_chat = round((time.time() - start_time) * 1000, 2)

    respond += module.get_string('ping_in_this_chat', ping=time_delta_in_this_chat)
    await message.edit(respond)

    if not (await app.get_me()).is_bot:
        start_time = time.time()
        message_in_saved_messages = await app.send_message('me', '0')
        time_delta_in_saved_messages = round((time.time() - start_time) * 1000, 2)
        await message_in_saved_messages.delete()

        respond += module.get_string('ping_in_saved_messages', ping=time_delta_in_saved_messages)
        await message.edit(respond)

    respond += '\n' + module.get_config_parameter('code')
    await message.edit(respond)
