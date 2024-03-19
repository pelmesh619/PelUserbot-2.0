import asyncio
import importlib
import shutil
import os
import logging

from pyrogram import Client, filters
import requests

log = logging.getLogger(__name__)


@Client.on_message(filters.me & filters.command('update'))
async def update_handler(app, message):
    module_name = ' '.join(message.command[1:])
    if not module_name:
        await message.reply_text(app.get_string('update_enter_module_name', _module_id='core.handlers'))
        return

    try:
        module = app.get_module(module_name)
    except KeyError as e:
        await message.reply_text(app.get_core_string('update_module_not_found', module_name=module_name))
        return

    old_version = module.version
    if not module.update_source_link:
        await message.reply_text(app.get_core_string('update_there_is_no_link', module_name=module.full_name()))
        return
    module_path = app.plugins['root'] + '.' + module_name
    module_name = module.full_name()
    module_id = module.module_id

    bot_message = await message.reply_text(
        message.get_string(
            'update_module_is_downloading',
            module_name=module_name,
            update_link=module.update_source_link
        ),
        disable_web_page_preview=True
    )

    shutil.copyfile(os.path.join(app.plugins['root'], module_id + '.py'),
                    os.path.join('cache', module_id + f'_{old_version}.py')
                    )

    try:
        result = requests.get(module.update_source_link).content

    except Exception as e:
        log.error(f'Error while updating module {module_id}', exc_info=e)
        await bot_message.edit(app.get_core_string('update_link_error', module_name=module_name, error=repr(e)))
        return

    await bot_message.edit(
        message.get_string(
            'update_module_is_downloaded',
            module_name=module_name,
            update_link=module.update_source_link
        ),
        disable_web_page_preview=True
    )
    await asyncio.sleep(0.4)
    old_handlers = sum([[j[0].callback.__name__ for j in i.handlers] for i in module.handlers], start=[])
    uninstall_respond = app.get_core_string(
        'update_module_was_uninstalled',
        module_name=module_name,
    )

    app.uninstall_module(module_id)  # TODO error messages
    await bot_message.edit(uninstall_respond)

    open(os.path.join(app.plugins['root'], module_id + '.py'), 'wb+').write(result)



    try:
        app.reload_module(module_path)
    except Exception as e:
        log.error('Error while reloading updated module', exc_info=e)
        await bot_message.edit(
            app.get_core_string(
                'update_module_has_an_error_backup',
                module_name=module_name,
            )
        )
        shutil.copyfile(os.path.join('cache', module_id + f'_{old_version}.py'),
                        os.path.join(app.plugins['root'], module_id + '.py')
                        )
        app.reload_module(module_path)
        module = app.install_module(module_path, module_id=module_id)
        respond = app.get_core_string(
            'update_module_backup_loaded',
            module_name=module.full_name(),
            handlers_count=len(module.commands),
            handler_form=app.get_core_string_form('handler_form', len(module.commands)),
        )

        await bot_message.edit(respond)
        return

    module = app.install_module(module_path, module_id=module_id)
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
        'update_module_was_updated',
        module_name=module.full_name(),
        handlers_count=len(module.commands),
        update_link=module.update_source_link,
        new_version=module.version,
        old_version=old_version,
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

    await bot_message.edit(respond)
