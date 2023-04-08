from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('uninstall'))
async def uninstall_handler(app, message):
    if len(message.command) > 1:
        module_name = message.command[1]
    else:
        await message.reply_text(app.get_string('uninstall_enter_module_name', _module_id='core.handlers'))
        return

    try:
        module = app.get_module(module_name)
    except KeyError:
        await message.reply_text(
            app.get_string(
                'uninstall_module_not_found',
                module_name=module_name,
                _module_id='core.handlers'
            )
        )
        return

    app.uninstall_module(module.module_id)


    await message.reply_text(
        app.get_string(
            'uninstall_module_was_uninstalled',
            module_name=module.full_name(),
            handlers_count=len(module.commands),
            handler_form=app.get_string_form('handler_form', len(module.commands), _module_id='core.handlers'),
            removed_form=app.get_string_form('removed_form', len(module.commands), _module_id='core.handlers'),
            _module_id='core.handlers'
        )
    )
