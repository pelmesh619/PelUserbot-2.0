import re
import html
import logging
import hashlib
import inspect

import pyrogram
from pyrogram import Client, filters, handlers

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
            'module_name': 'Алиасы',
            'description': 'Управляет алиасами - сокращениями команд и прочего. /aliases - посмотреть все алиасы',

            'True': 'да',
            'False': 'нет',
            'alias_info': 'Алиас "<code>{alias}</code>" (регулярное выраж. - {is_regex}), заменяется на:'
                          '\n    {text_to_replace}'
                          '\n\n<code>/alias{aliasregex} {alias_for_command} <новое значение></code> - изменить алиас\n'
                          '<code>/aliasdel {alias_for_command}</code> - удалить алиас',
            'alias_added': 'Алиас "<code>{alias}</code>" (регулярное выраж. - {is_regex}), который заменяется на:'
                           '\n    {text_to_replace}\n\n'
                           'добавлен.\n<code>/alias {alias_for_command}</code> - посмотреть алиас',
            'alias_changed': 'Алиас "<code>{alias}</code>" (регулярное выраж. - {is_regex}) изменен. '
                             '\nСтарое значение: {old_text_to_replace}'
                             '\nНовое значение: {text_to_replace}\n\n'
                             '<code>/alias {alias_for_command}</code> - посмотреть алиас',
            'alias_deleted': 'Алиас "<code>{alias}</code>" (регулярное выраж. - {is_regex}), который заменяется на:'
                             '\n    {text_to_replace}\n\n'
                             'удален.\nВведите <code>/alias{aliasregex} {alias_for_command} {text_to_replace}</code>, '
                             'чтобы восстановить алиас',
            'aliases': 'Алиасы, всего {aliases_count}:\n\n',
            'alias_hint': '\nЧтобы создать алиас, введите команду <code>/alias <заменяемый текст> <заменяющий '
                          'текст></code>',
            'alias_not_found': 'Алиас <i>{alias}</i> не найден. '
                               'Введите <code>/aliases</code>, чтобы посмотреть алиасы',
            'alias_template': '{num}. <code>{alias}</code> - {text_to_replace} '
                              '(<code>/alias{aliasregex} {alias_for_command}</code>)\n',
            'alias_wrong_input': 'Введите команду <code>/aliases</code>, чтобы посмотреть все алиасы\n'
                                 '<code>/alias <алиас></code> - посмотреть алиас\n'
                                 '<code>/alias <заменяемый текст> <заменяющий текст></code> - создать алиас',
            'aliasdel_wrong_input': 'Введите команду <code>/aliasdel <алиас></code>, чтобы удалить алиас\n'
                                    '<code>/aliases</code> - посмотреть алиасы',
            'alias_filter_docs': 'совпадающие алиасам',
            # TODO docs for handlers
        },
        'en': {
        },
    },
    database=ModuleDatabase(
        schema='CREATE TABLE IF NOT EXISTS aliases (\n'
               'alias_hash BIGINT PRIMARY KEY,\n'
               'alias TEXT,\n'
               'text_to_replace TEXT,\n'
               'is_regex BOOLEAN DEFAULT false\n'
               ');'
    )
)


def wrap_quote(string):
    if ' ' in string:
        return '"' + string + '"'
    return string


@Client.on_message(filters.me & filters.command(['alias', 'aliasregex']))
async def alias_handler(_, message):
    aliases = module.database.execute_and_fetch('SELECT * FROM aliases;')
    reply = message.reply_to_message
    is_regex = message.command[0] == 'aliasregex'
    if not message.command[1:]:
        await message.reply(
            message.get_string('alias_wrong_input')
        )
        return

    alias_guess = message.command[1]
    alias_guess2 = ' '.join(message.command[1:])

    alias_row = None
    for row in aliases:
        if is_regex and row[1] in [alias_guess, alias_guess2]:
            alias_row = row
            break
        elif row[1] in [re.escape(alias_guess), re.escape(alias_guess2)]:
            alias_row = row
            break

    if alias_row:
        text_to_replace = ' '.join(message.command[2:])
        if not text_to_replace and reply:
            text_to_replace = reply.text

        if not text_to_replace or text_to_replace == alias_row[2]:
            await message.edit(
                message.get_string(
                    'alias_info',
                    alias=alias_row[1],
                    alias_for_command=wrap_quote(alias_row[1]),
                    text_to_replace=html.escape(alias_row[2], quote=False),
                    is_regex=message.get_string(str(bool(alias_row[3]))),
                    aliasregex='regex' if alias_row[3] else '',
                )
            )
            return

        old_text_to_replace = alias_row[2]
        alias_hash = alias_row[0]
        module.database.execute(f'UPDATE aliases SET text_to_replace = \'{text_to_replace}\', '
                                f'is_regex = {"true" if is_regex else "false"}'
                                f'WHERE alias_hash = {alias_hash}')

        await message.edit(
            message.get_string(
                'alias_changed',
                alias=alias_row[1],
                alias_for_command=wrap_quote(alias_row[1]),
                text_to_replace=html.escape(text_to_replace, quote=False),
                old_text_to_replace=old_text_to_replace,
                is_regex=message.get_string(str(is_regex)),
            )
        )
        return

    alias = message.command[1]
    text_to_replace = ' '.join(message.command[2:])
    if not text_to_replace and reply:
        alias = ' '.join(message.command[1:])
        text_to_replace = reply.text

    if not text_to_replace:
        await message.edit(
            message.get_string(
                'alias_not_found',
                alias=alias,
            )
        )
        return

    if not is_regex:
        alias_to_hash = re.escape(alias)
    else:
        alias_to_hash = alias

    alias_hash = int(hashlib.md5(alias_to_hash.encode()).hexdigest(), 16)

    module.database.execute(f'INSERT INTO aliases VALUES ({alias_hash}, \'{alias}\', '
                            f'\'{text_to_replace}\', {"true" if is_regex else "false"});')

    await message.edit(
        message.get_string(
            'alias_added',
            alias=alias,
            alias_for_command=wrap_quote(alias),
            text_to_replace=html.escape(text_to_replace, quote=False),
            is_regex=message.get_string(str(bool(is_regex))),
        )
    )


@Client.on_message(filters.me & filters.command('aliasdel'))
async def delete_alias_handler(_, message):
    aliases = module.database.execute_and_fetch('SELECT * FROM aliases;')

    alias = ' '.join(message.command[1:])

    if not alias:
        await message.reply(
            message.get_string('aliasdel_wrong_input')
        )
        return

    alias_row = None
    for row in aliases:
        if row[1] == alias:
            alias_row = row
            break

    if alias_row:
        module.database.execute(f'DELETE FROM aliases WHERE alias_hash = {alias_row[0]};')
        await message.edit(
            message.get_string(
                'alias_deleted',
                alias=alias_row[1],
                alias_for_command=wrap_quote(alias_row[1]),
                text_to_replace=html.escape(alias_row[2], quote=False),
                is_regex=message.get_string(str(bool(alias_row[3]))),
                aliasregex='regex' if alias_row[3] else '',
            )
        )
        return

    await message.reply(
        message.get_string(
            'alias_not_found',
            alias=alias,
        )
    )


@Client.on_message(filters.me & filters.command('aliases'))
async def show_aliases_handler(_, message):
    aliases = module.database.execute_and_fetch('SELECT * FROM aliases;')

    respond = message.get_string('aliases', aliases_count=len(aliases))

    for i, alias in enumerate(aliases, start=1):
        respond += message.get_string(
            'alias_template',
            num=i,
            alias=alias[1],
            text_to_replace=html.escape(alias[2], quote=False),
            alias_for_command=wrap_quote(alias[1]),
            aliasregex='regex' if alias[3] else '',
        )

    respond += message.get_string('alias_hint')

    await message.edit(respond)


def alias_work_filter(_, __, message):
    """string_id=alias_filter_docs

    Filter messages that match existing aliases
    """

    aliases = module.database.execute_and_fetch('SELECT * FROM aliases;')

    for alias_row in aliases:
        alias = alias_row[1]
        if not alias_row[3]:
            alias = re.escape(alias)
        if re.match(alias, message.text, re.I):
            message.text = re.sub(alias, alias_row[2], message.text, re.I)
            return True


@Client.on_message(filters.me & (filters.text | filters.caption) &
                   filters.create(alias_work_filter, __doc__=alias_work_filter.__doc__))
async def alias_handler_worker(app, message):
    await message.edit(message.text)

    dispatcher = app.dispatcher
    try:
        for group in list(dispatcher.groups.values()):
            for handler in group:

                if isinstance(handler, handlers.MessageHandler):
                    try:
                        if not await handler.check(app, message):
                            continue
                    except Exception as e:
                        log.error(e, exc_info=True)
                        continue

                try:
                    if handler.callback == alias_handler_worker:
                        continue
                    if inspect.iscoroutinefunction(handler.callback):
                        await handler.callback(app, message)
                    else:
                        await dispatcher.loop.run_in_executor(
                            app.executor,
                            handler.callback,
                            app,
                            message
                        )

                except pyrogram.StopPropagation:
                    raise
                except pyrogram.ContinuePropagation:
                    continue
                except Exception as e:
                    log.error(e, exc_info=True)
                raise pyrogram.StopPropagation
    except pyrogram.StopPropagation:
        raise
    except Exception as e:
        log.error(e, exc_info=True)
