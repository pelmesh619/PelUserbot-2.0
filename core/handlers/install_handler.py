from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('install'))
async def install_handler(app, message):
    if len(message.command) > 1:
        module_name = message.command[1]
    else:
        await message.reply_text(app.get_string('install_enter_module_name', _module_id='core.handlers'))
        return

    module = app.install_module(app.plugins['root'] + '.' + module_name, module_id=module_name)

    await message.reply_text(
        app.get_string(
            'install_module_was_installed',
            module_name=module.full_name(),
            handlers_count=len(module.commands),
            handler_form=app.get_string_form('handler_form', len(module.commands), _module_id='core.handlers'),
            added_form=app.get_string_form('added_form', len(module.commands), _module_id='core.handlers'),
            _module_id='core.handlers'
        )
    )
