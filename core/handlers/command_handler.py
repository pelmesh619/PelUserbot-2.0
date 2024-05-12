import html
import re

from pyrogram import Client, filters

from core.bot_types.module import Module

this_module = Module()



@Client.on_message(filters.me & this_module.command('command'))
async def command_handler(app, message):
    if len(message.command) >= 2:
        module_name = message.command[1]

        try:
            module = app.get_module(module_name)
        except KeyError:
            await message.reply_text(
                app.get_string(
                    'command_module_not_found' + ('_and_enter_command' if len(message.command) < 3 else ''),
                    module_name=module_name,
                    _module_id='core.handlers'
                )
            )
            return
    else:
        await message.reply_text(app.get_string('command_enter_module_name', _module_id='core.handlers'))
        return

    if len(message.command) >= 3:
        command = message.command[2]

        index = int(command) if command.isdigit() else None
        command_name = command if not command.isdigit() else None

        found_commands = {}
        for com_index, com in enumerate(module.commands):
            if index == com_index + 1:
                found_commands[com_index] = com
            if com.func.__name__ == command_name:
                found_commands[com_index] = com

        if not found_commands:
            await message.reply_text(
                app.get_string(
                    'command_command_not_found' + ('_by_command' if command_name else '_by_index'),
                    module_name=module.full_name(),
                    command_name=command_name,
                    index=index,
                    count_of_handlers=len(module.commands),
                    handler_form=app.get_string_form('handler_form', len(module.commands)),
                    module_id=module.module_id,
                    _module_id='core.handlers'
                )
            )
            return

    else:
        await message.reply_text(app.get_string('command_enter_command', _module_id='core.handlers'))
        return

    await message.reply_text(
        app.get_string(
            'command_info_template',
            num=list(found_commands.keys())[0] + 1,
            module_name=module.full_name(),
            handler_type=app.get_string(
                'handler_' + list(found_commands.values())[0].handler_type,
                _module_id='core.handlers'
            ).capitalize(),
            filter_string=list(found_commands.values())[0].repr_filter_with_get_string(),
            func_name=list(found_commands.values())[0].func.__name__,
            docs_template=app.get_string(
                'command_docs_template',
                docs=module.decode_string(list(found_commands.values())[0].documentation).strip('\n'),
                _module_id='core.handlers'
            ) if list(found_commands.values())[0].documentation else '',
            _module_id='core.handlers'
        )
    )
