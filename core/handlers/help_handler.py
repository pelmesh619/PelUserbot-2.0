from pyrogram import Client, filters

from core.bot_types import Module


@Client.on_message(filters.me & filters.command('help'))
async def help_handler(app, message):
    await message.reply(app.get_core_string('help_message'))

