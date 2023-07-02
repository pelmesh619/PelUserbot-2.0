import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait

from core import Module, Author
from utils.bot_utils import call_filters

module = Module(
    name='string_id=purge_module_name',
    description='string_id=description',
    authors=Author('pelmeshke', telegram_username='pelmeshke', job='string_id=author_creator'),
    version='v1.0.0',
    release_date='17-04-2023',
    strings={
        'ru': {
            'purge_module_name': '🧹Очистка сообщений',
            'description': 'Очищает сообщения в чате при помощи команды {_cmd_pref}purge. '
                           'Команда {_cmd_pref}spurge очищает бесшумно',
            'author_creator': 'Создатель',
            'bot_works': 'Бот работает',
            'docs_test_handler': 'На команду `/test` отвечает ответным сообщением. Если сообщение не было '
                                 'отправлено, то с ботом что-то не так. Не принимает аргументов.',
            'docs_test_from_me_handler': 'На команду `!test` изменяет сообщение. Если сообщение не было '
                                         'изменено, то с ботом что-то не так. Не принимает аргументов.',
            'message_form': {
                "lambda x: x % 10 == 1 and x % 100 != 11": "сообщение",
                "lambda x: 1 < x % 10 < 5 and not (11 < x % 100 < 15)": "сообщения",
                "lambda x: True": "сообщений"
            },
            'deleted_form': {
                'lambda x: x % 10 == 1 and x % 100 != 11': 'удалено',
                'lambda x: True': 'удалены',
            },
            'purging': 'Произвожу очистку...',
            'syntax_error': 'При интерпретации фильтра произошла ошибка: <code>{line}\n{pointer}</code>',
            'error_raised': 'Фильтр вызвал ошибку: <code>{error}</code>',
            'not_callable': 'Введенный фильтр не является вызываемым объектом',
            'no_reply': 'Ответьте командой на сообщение с которого вы хотите начать очистку',
            'changelog_v1.0.0': 'Релиз',
            'messages_deleted': 'Очистка произведена, {deleted_form} {count} {message_form}\n\nСреди них:\n{stats}',


        },
        'en': {
            'purge_module_name': '🧹Purge',
            'description': 'Purging messages in chat via command {_cmd_pref}purge. '
                           'Command {_cmd_pref}spurge purges silently',
            'author_creator': 'Creator',
            'message_form': {
                "lambda x: x % 10 == 1 and x % 100 != 11": "message",
                "lambda x: True": "messages"
            },
            'deleted_form': {
                'lambda x: True': 'deleted',
            },
            'purging': 'Doing purge...',
            'syntax_error': 'While interpretation an error was raised: <code>{line}\n{pointer}</code>',
            'error_raised': 'The filter raised an error: <code>{error}</code>',
            'not_callable': 'Entered filter is not callable object',
            'no_reply': 'Reply command to message from which you want to start deletion',
            'changelog_v1.0.0': 'Release',
            'messages_deleted': 'Purge is done, {deleted_form} {count} {message_form}\n\nIncluding:\n{stats}',
        },
    },
    strings_source_filename=None,
    update_source_link='https://raw.githubusercontent.com/pelmesh619/Peluserbot-2.0-Modules/main/purge.py',
    config={},
    requirements=[],
    changelog={
        "v1.0.0": "string_id=changelog_v1.0.0",
    }
)


@Client.on_message(filters.me & filters.command(['purge', 'spurge']))
async def purge(app, message):
    if not message.reply_to_message:
        return await message.reply(message.get_string('no_reply'))

    reply = await app.get_messages(message.chat.id, message.reply_to_message.id)

    purge_filters = ' '.join(message.command[1:]) or 'filters.all'
    filters_vars = {k: v for k, v in vars(filters).items() if not k.startswith('__')}
    vars_ = dict(globals().items())
    vars_.update({'app': app, 'message': message, 'filters': filters, **filters_vars, 'reply_to': reply})
    try:
        purge_filters = eval(purge_filters, vars_)
    except SyntaxError as e:
        return await message.reply(
            message.get_string(
                'syntax_error',
                line=e.args[1][3],
                pointer=' ' * (e.args[1][2] - 1) + '^'
            )
        )
    except Exception as e:
        return await message.edit(message.get_string('error_raise', repr(e)))

    if not callable(purge_filters):
        return await message.edit(message.get_string('not_callable'))

    bot_message = await message.reply(message.get_string('purging'))

    is_silent = message.command[0] == 'spurge'
    if is_silent:
        await message.delete()

    count = 0

    stats = {}

    async for msg in app.get_chat_history(chat_id=reply.chat.id, offset_id=message.id):
        try:
            if msg.id < reply.id:
                break

            if await call_filters(purge_filters, app, msg):
                if not msg.media:
                    if 'text' not in stats:
                        stats['text'] = 0
                    stats['text'] += 1
                else:
                    if msg.media.value not in stats:
                        stats[msg.media.value] = 0
                    stats[msg.media.value] += 1
                try:
                    await msg.delete()
                except FloodWait:
                    await asyncio.sleep(3)
                count += 1

        except Exception:
            pass

    if not is_silent:
        await bot_message.edit(
            message.get_string(
                'messages_deleted',
                deleted_form=message.get_string.get_string_form('deleted_form', count),
                count=count,
                message_form=message.get_string.get_string_form('message_form', count),
                stats='\n'.join([
                    message.get_string.get_core_string('filter_'+k) + ': ' + str(v) for k, v in stats.items()
                ])
            )
        )
    else:
        await bot_message.delete()
