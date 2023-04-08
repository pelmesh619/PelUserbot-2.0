from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('module'))
async def module_handler(app, message):
    module_name = ' '.join(message.command[1:])
    if not module_name:
        await message.reply_text(app.get_string('module_enter_module_name', _module_id='core.handlers'))
        return

    try:
        module = app.get_module(module_name)
    except KeyError as e:
        await message.reply_text(app.get_string('module_module_not_found', module_name=module_name, _module_id='core.handlers'))
    else:
        respond = module.get_full_info()

        await message.reply_text(text=respond, disable_web_page_preview=True)
