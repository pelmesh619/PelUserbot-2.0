from pyrogram import Client, filters



@Client.on_message(filters.me & filters.command('modules'))
async def modules_handler(app, message):
    modules = ''
    for mod in app.modules:
        modules += mod.get_short_info()

    await message.reply(
        app.get_string(
            'modules_template',
            modules=modules,
            modules_count=len(app.modules),
            module_form=app.get_string_form('module_form', len(app.modules), _module_id='core.handlers'),
            _module_id='core.handlers'
        )
    )
