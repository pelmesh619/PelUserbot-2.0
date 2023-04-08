import html

from pyrogram import Client, filters

from utils import text_utils


@Client.on_message(filters.me & filters.command('commands'))
async def commands_handler(app, message):
    module_name = ' '.join(message.command[1:])
    if not module_name:
        await message.reply_text(app.get_string('commands_enter_module_name', _module_id='core.handlers'))
        return

    try:
        module = app.get_module(module_name)
    except KeyError as e:
        await message.reply_text(
            app.get_string('commands_module_not_found', module_name=module_name, _module_id='core.handlers')
        )
    else:
        if not module.commands:
            return message.reply_text(
                app.get_string(
                    'commands_module_does_not_have_handlers',
                    module_name=module_name,
                    _module_id='core.handlers'
                )
            )

        commands = ''
        for i, handler in enumerate(module.commands):
            commands += app.get_string(
                'short_command_template',
                num=i+1,
                handler=handler.func.__name__,
                handler_type=app.get_string(
                    'handler_'+handler.handler_type,
                    _module_id='core.handlers'
                ),
                filter_string=handler.repr_filter_with_get_string(),
                docs=':\n    ' + text_utils.cut_text(module.decode_string(handler.documentation).strip('\n'))
                if handler.documentation else '',
                module_id=module.module_id,
                _module_id='core.handlers'
            ) + '\n\n'

        respond = app.get_string(
            'commands_template',
            module_name=module.full_name(),
            commands=commands,
            handlers_count=len(module.commands),
            handlers_form=app.get_string_form('handler_form', len(module.commands), _module_id='core.handlers'),
            _module_id='core.handlers'
        )

        await message.reply_text(text=respond, disable_web_page_preview=True)
