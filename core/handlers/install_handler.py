import importlib
import os
import logging
import hashlib
import re
import shutil

from pyrogram import Client, filters

from utils import bot_utils
from core.bot_types import filters as custom_filters

log = logging.getLogger(__name__)


@Client.on_message(filters.me & filters.command('install'))
async def install_handler(app, message):
    module_name = None
    if len(message.command) > 1:
        module_name = message.command[1]

    module_file = None
    if message.reply_to_message and message.reply_to_message.document:
        module_file = message.reply_to_message.document

    if not (module_file or module_name):
        await message.reply_text(app.get_core_string('install_enter_module_name'))
        return

    if module_name and module_file:
        module_file = None

    is_module_was_installed = False
    bot_message = None
    if app.get_module(module_name) and not module_file:
        module = app.get_module(module_name)
        await message.reply(
            message.get_string(
                'install_this_module_was_installed',
                module_id=module.module_id,
                module_name=module.full_name()
            )
        )
        return

    is_cached = False
    if not module_name and module_file:
        module_filename = module_file.file_name
        filename_in_downloads = os.path.join(
            app.get_config_parameter('downloads_directory'), module_filename
        )
        download_mode_text = 'downloading'
        if os.path.exists(filename_in_downloads):
            bot_message = await message.reply(
                message.get_string(
                    'install_there_is_file_with_that_name_in_downloads',
                    existing_file_name=filename_in_downloads,
                    existing_file_size=message.get_string.memory_to_string(os.path.getsize(filename_in_downloads)),
                    existing_file_last_edit_date=message.get_string.date_to_string(
                        os.path.getmtime(filename_in_downloads)
                    ),
                    downloading_file_name=module_filename,
                    downloading_file_size=message.get_string.memory_to_string(module_file.file_size),

                )
            )
            while True:
                answer = await bot_utils.wait_answer(
                    bot_message,
                    filters.me &
                    custom_filters.identify_string(['cancel_reply', 'rename_reply', 'rewrite_reply']),
                    timeout=120
                )

                if answer is None:
                    await bot_message.edit(bot_message.text + '\n\n' + message.get_string('message_is_outdated'))
                    return
                if answer.identified_string_id == 'cancel_reply':
                    await answer.reply(
                        message.get_string('install_downloading_was_canceled', filename=module_filename)
                    )
                    return
                if answer.identified_string_id == 'rename_reply':
                    new_filename = answer.match.group(1)
                    if not new_filename.endswith('.py'):
                        new_filename += '.py'
                    if not re.search(r'^[a-zA-Z0-9_]+\.py$', new_filename):
                        bot_message = await message.reply(
                            message.get_string(
                                'install_wrong_name_file_in_downloads',
                                downloading_file_name=module_filename,
                                downloading_file_size=message.get_string.memory_to_string(
                                    module_file.file_size
                                ),
                            )
                        )
                        continue

                    filename_in_downloads = os.path.join(
                        app.get_config_parameter('downloads_directory'), new_filename
                    )

                    if os.path.exists(filename_in_downloads):
                        bot_message = await message.reply(
                            message.get_string(
                                'install_there_is_file_with_that_name_in_downloads',
                                existing_file_name=filename_in_downloads,
                                existing_file_size=message.get_string.memory_to_string(
                                    os.path.getsize(filename_in_downloads)),
                                existing_file_last_edit_date=message.get_string.date_to_string(
                                    os.path.getmtime(filename_in_downloads)
                                ),
                                downloading_file_name=module_filename,
                                downloading_file_size=message.get_string.memory_to_string(
                                    module_file.file_size
                                )
                            )
                        )
                        continue
                    download_mode_text = 'downloading'
                    module_filename = new_filename
                    break

                if answer.identified_string_id == 'rewrite_reply':
                    download_mode_text = 'rewriting'
                    break

        respond = message.get_string(
            'install_downloading_' + download_mode_text,
            module_filename=module_filename,
        )

        bot_message = await message.reply(respond)
        bot_message.get_string = message.get_string

        await app.download_media(
            module_file,
            filename_in_downloads,
            progress=bot_utils.get_progress_func(bot_message, progress_type='memory')
        )
        file_content = open(filename_in_downloads, 'rb').read()
        file_content_hash = hashlib.sha256(file_content).hexdigest()
        del file_content

        module_name = re.sub(r'\.py$', '', module_filename)

        solution_for_conflict_in_modules = 'moving'
        filename_in_modules = os.path.join(app.plugins['root'], module_name + '.py')

        if os.path.exists(filename_in_modules):
            existing_file_content = open(filename_in_modules, 'rb').read()
            existing_file_content_hash = hashlib.sha256(existing_file_content).hexdigest()
            del existing_file_content
            bot_message = await message.reply(
                message.get_string(
                    'install_there_is_file_with_that_name_in_modules',
                    existing_file_name=filename_in_modules,
                    existing_file_size=message.get_string.memory_to_string(os.path.getsize(filename_in_modules)),
                    existing_file_last_edit_date=message.get_string.date_to_string(
                        os.path.getmtime(filename_in_modules)
                    ),
                    downloaded_file_name=module_filename,
                    downloaded_file_size=message.get_string.memory_to_string(os.path.getsize(filename_in_downloads)),
                    is_content_same=message.get_string('install_the_contents_are_same')
                    if file_content_hash == existing_file_content_hash else ''

                )
            )
            while True:
                answer = await bot_utils.wait_answer(
                    bot_message,
                    filters.me &
                    custom_filters.identify_string(['cancel_reply', 'rename_reply', 'rewrite_reply']),
                    timeout=120
                )

                if answer is None:
                    await bot_message.edit(bot_message.text + '\n\n' + message.get_string('message_is_outdated'))
                    return
                if answer.identified_string_id == 'cancel_reply':
                    await answer.reply(
                        message.get_string('install_resolving_conflict_was_canceled', filename=module_filename)
                    )
                    return
                if answer.identified_string_id == 'rename_reply':
                    new_filename = answer.match.group(1)
                    if not new_filename.endswith('.py'):
                        new_filename += '.py'
                    if not re.search(r'^[a-zA-Z0-9_]+\.py$', new_filename):
                        bot_message = await message.reply(
                            message.get_string(
                                'install_wrong_name_file_in_modules',
                                downloaded_file_name=module_filename,
                                downloaded_file_size=message.get_string.memory_to_string(
                                    module_file.file_size
                                ),
                            )
                        )
                        continue

                    filename_in_modules = os.path.join(app.plugins['root'], new_filename)

                    existing_file_content = open(filename_in_modules, 'rb').read()
                    existing_file_content_hash = hashlib.sha256(existing_file_content).hexdigest()
                    del existing_file_content

                    if os.path.exists(filename_in_modules):
                        bot_message = await message.reply(
                            message.get_string(
                                'install_there_is_file_with_that_name_in_modules',
                                existing_file_name=filename_in_modules,
                                existing_file_size=message.get_string.memory_to_string(
                                    os.path.getsize(filename_in_modules)),
                                existing_file_last_edit_date=message.get_string.date_to_string(
                                    os.path.getmtime(filename_in_modules)
                                ),
                                downloading_file_name=module_filename,
                                downloading_file_size=message.get_string.memory_to_string(
                                    module_file.file_size
                                ),
                                is_content_same=message.get_string('install_the_contents_are_same')
                                if file_content_hash == existing_file_content_hash else ''
                            )
                        )
                        continue
                    solution_for_conflict_in_modules = 'moving'
                    module_filename = new_filename
                    shutil.copyfile(filename_in_downloads, filename_in_modules)
                    break

                if answer.identified_string_id == 'rewrite_reply':
                    solution_for_conflict_in_modules = 'rewriting'
                    is_cached = True
                    shutil.copyfile(filename_in_modules, os.path.join('cache', module_name+'.py'))
                    shutil.copyfile(filename_in_downloads, filename_in_modules)

                    break
        else:
            shutil.copyfile(filename_in_downloads, filename_in_modules)

        module_name = re.sub(r'(\.py)?$', '', module_filename)

        respond = message.get_string(
            'install_module_was_moved_' + solution_for_conflict_in_modules,
            module_name=module_name
        )
        bot_message = await message.reply(respond)

    if module_file and app.get_module(module_name):
        module = app.get_module(module_name)
        app.uninstall_module(module.module_id)
        is_module_was_installed = True

    try:
        importlib.reload(importlib.import_module(app.plugins['root'] + '.' + module_name))
        module = app.install_module(app.plugins['root'] + '.' + module_name, module_id=module_name)
    except Exception as e:
        log.error('Error raised while installing a module', exc_info=e)
        if bot_message:
            method = bot_message.edit
        else:
            method = message.reply
        is_backup = False
        module_fullname = None
        module_version = None
        if is_cached and is_module_was_installed:
            shutil.copyfile(
                os.path.join('cache', module_name + '.py'),
                os.path.join(app.plugins['root'], module_name + '.py')
            )
            if is_module_was_installed:
                importlib.reload(importlib.import_module(app.plugins['root'] + '.' + module_name))
                module = app.install_module(app.plugins['root'] + '.' + module_name, module_id=module_name)
                module_fullname = module.full_name()
                module_version = module.version
            is_backup = True

        await method(
            app.get_core_string(
                'install_error_was_raised' + ('_backup' if is_backup else ''),
                module_name=module_name,
                module_fullname=module_fullname,
                version=module_version,
                error=repr(e)
            )
        )

        return

    if bot_message:
        method = bot_message.edit
    else:
        method = message.reply

    await method(
        app.get_string(
            'install_module_was_installed',
            module_name=module.full_name(),
            handlers_count=len(module.commands),
            handler_form=app.get_string_form('handler_form', len(module.commands), _module_id='core.handlers'),
            added_form=app.get_string_form('added_form', len(module.commands), _module_id='core.handlers'),
            _module_id='core.handlers'
        )
    )
