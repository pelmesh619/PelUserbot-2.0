import asyncio
import logging
import time

from pyrogram import Client, filters
from core import Module, Author, LocalizedFormatter, Peluserbot

__version__ = 'v1.2.0-delta'

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


@Client.on_message(filters.me & filters.command('tasks'))
async def tasks_handler(app, msg):
    for i in app.dispatcher.handler_worker_tasks:
        try:
            i.cancel()
        except Exception as e:
            print(e)
    await msg.reply('success')
    for i in app.dispatcher.handler_worker_tasks:
        try:
            i.uncancel()
        except Exception as e:
            print(e)


@Client.on_message(filters.me & filters.command('tasks2'))
async def tasks2_handler(app, msg):
    dp = app.dispatcher

    for i in range(len(dp.handler_worker_tasks)):
        hw = dp.handler_worker_tasks[i]
        lock = dp.locks_list[i]
        print(time.time(), i, 'handler worker deleted', lock)

        try:
            hw.cancel()
            del hw
        except Exception as e:
            print(e)

    dp.handler_worker_tasks.clear()
    dp.locks_list.clear()
    print(dp.handler_worker_tasks, dp.locks_list)

    for i in range(dp.client.workers):
        dp.locks_list.append(asyncio.Lock())

        task = dp.loop.create_task(dp.handler_worker(dp.locks_list[-1]))
        print(time.time(), i, 'handler worker ', dp.locks_list[-1], task)
        dp.handler_worker_tasks.append(task)
    await msg.reply('success')
    print(dp.handler_worker_tasks)


# @Client.on_message(filters.me & filters.command('taskmgr'))
async def taskmgr_handler(app, msg):
    dp = app.dispatcher

    respond = []
    for i in range(len(dp.handler_worker_tasks)):
        lock = dp.locks_list[i]
        if lock.locked():
            module_name = None
            if lock.module:
                module_name = lock.module.full_name()
            respond.append(
                msg.get_string(
                    'process_info',
                    num=i,
                    handler_name=lock.handler_name,
                    module_name=module_name,
                    seconds=round(time.time() - lock.start_time, 4),
                    second_form=msg.get_string_form('second_form', round(time.time() - lock.start_time, 4)),
                    chat_name=lock.update.chat.title or lock.update.chat.first_name,
                )
            )

    await msg.reply(
        msg.get_string('task_manager', processes='\n\n'.join(respond), workers=len(dp.handler_worker_tasks))
    )




@Client.on_message(filters.me & filters.command('go'))
async def go_handler(app, msg):
    for i in range(10):
        await msg.reply(str(i))
        await asyncio.sleep(3)
    await msg.reply('s1')




@Client.on_message(filters.me & filters.command('go2'))
async def go2_handler(app, msg):
    await msg.reply('делаю вещи 60 секунд')
    await asyncio.sleep(60)
    await msg.reply('сделал вещи')
