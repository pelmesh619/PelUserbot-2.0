from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('reload'))
async def reload_handler(app, message):
    if len(message.command) > 1:
        module_name = message.command[1]
    else:
        await message.reply_text(app.get_string('reload_enter_module_name', _module_id='core.handlers'))
        return

    try:
        module = app.get_module(module_name)
    except KeyError:
        await message.reply_text(
            app.get_string('reload_module_not_found', module_name=module_name, _module_id='core.handlers')
        )
        return
    if module.module_id != 'core.handlers':
        module_path = app.plugins['root'] + '.' + module_name
    else:
        module_path = 'core.handlers'

    old_handlers = sum([[j[0].callback.__name__ for j in i.handlers] for i in module.handlers], start=[])
    uninstall_respond = app.get_string(
        'reload_module_was_uninstalled',
        module_name=module.full_name(),
        _module_id='core.handlers'
    )

    module = app.uninstall_module(module_name)  # TODO error messages

    message = await message.reply_text(uninstall_respond)

    app.reload_module(module_path)
    module = app.install_module(module_path, module_id=module_name)
    new_handlers = sum([[j[0].callback.__name__ for j in i.handlers] for i in module.handlers], start=[])


    removed_handlers = 0
    reloaded_handlers = 0
    for old_handler in old_handlers:
        for new_handler in new_handlers:
            if old_handler == new_handler:
                reloaded_handlers += 1
                break
        else:
            removed_handlers += 1

    added_handlers = len(new_handlers) - reloaded_handlers

    respond = app.get_string(
        'reload_module_was_reloaded',
        module_name=module.full_name(),
        handlers_count=len(module.commands),
        added_handlers=app.get_string(
            'added_handlers_template',
            added_handlers_count=added_handlers,
            added_handler_form=app.get_string_form('handler_form', added_handlers, _module_id='core.handlers'),
            added_form=app.get_string_form('added_form', added_handlers, _module_id='core.handlers'),
            _module_id='core.handlers'
        ) if added_handlers else '',
        removed_handlers=app.get_string(
            'removed_handlers_template',
            removed_handlers_count=removed_handlers,
            removed_handler_form=app.get_string_form('handler_form', removed_handlers, _module_id='core.handlers'),
            removed_form=app.get_string_form('removed_form', removed_handlers, _module_id='core.handlers'),
            _module_id='core.handlers'
        ) if removed_handlers else '',
        reloaded_handlers=app.get_string(
            'reloaded_handlers_template',
            reloaded_handlers_count=reloaded_handlers,
            reloaded_handler_form=app.get_string_form('handler_form', reloaded_handlers, _module_id='core.handlers'),
            reloaded_form=app.get_string_form('reloaded_form', reloaded_handlers, _module_id='core.handlers'),
            _module_id='core.handlers'
        ) if reloaded_handlers else '',
        _module_id='core.handlers'
    )

    await message.edit(respond)
