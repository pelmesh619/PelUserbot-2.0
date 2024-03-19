import asyncio
import time

import pyrogram

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.bot_types import bot_filters
from utils import bot_utils


@Client.on_message(filters.me & bot_filters.i_am_user & filters.command('restart'))
async def restart_handler(app, message):
    message = await message.reply(app.get_core_string('restart_confirm'))

    answer = await bot_utils.wait_answer(message, filters.me & filters.regex(r'^y|n$'), timeout=120)
    if answer is None:
        await message.edit_text(message.text.html + '\n\n' + app.get_core_string('message_is_outdated'))
    elif answer.text == 'y':
        bot_message = await answer.reply_text(app.get_core_string('restarting'))
        await app.restart(block=False)
        await bot_message.edit_text(app.get_core_string('restart_succeed'))
        await message.edit_text(app.get_core_string('restart_confirm') +
                                '\n\n' + app.get_core_string('restart_succeed'))
        app.last_restart_time = time.time()

    elif answer.text == 'n':
        await answer.reply_text(app.get_core_string('restart_cancel'))
        await message.edit_text(message.text.html + '\n\n' + app.get_core_string('restart_cancel'))


@Client.on_message(filters.me & bot_filters.i_am_bot & filters.command('restart'))
async def restart_for_bot_handler(app, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(app.get_core_string('restart_confirm_button'), callback_data='core#restart_confirm')],
            [InlineKeyboardButton(app.get_core_string('restart_cancel_button'), callback_data='core#restart_cancel')],
        ]
    )
    await message.reply(app.get_core_string('restart_confirm'), reply_markup=keyboard)


@Client.on_callback_query(filters.me & filters.regex('core#restart_confirm'))
async def restart_confirm_handler(app, call):
    await call.message.edit_text(app.get_core_string('restarting'))
    await app.restart(block=False)
    await call.message.edit_text(app.get_core_string('restart_succeed'))
    app.last_restart_time = time.time()


@Client.on_callback_query(filters.me & filters.regex('core#restart_cancel'))
async def restart_cancel_handler(app, call):
    await call.message.edit_text(app.get_core_string('restart_cancel'))

