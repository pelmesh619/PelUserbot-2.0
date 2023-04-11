import asyncio
import time

import pyrogram

from pyrogram import Client, filters

from utils import bot_utils


@Client.on_message(filters.me & filters.command('restart'))
async def restart_handler(app, message):
    message = await message.reply(app.get_core_string('restart_confirm'))

    answer = await bot_utils.wait_answer(message, filters.me & filters.regex(r'^y|n$'), timeout=120)
    if answer is None:
        await message.edit_text(message.text.html + '\n\n' + app.get_core_string('message_is_outdated'))
    elif answer.text == 'y':
        await answer.edit_text(app.get_core_string('restarting'))
        await app.restart(block=False)
        await answer.edit_text(app.get_core_string('restart_succeed'))
        await message.edit_text(message.text.html + '\n\n' + app.get_core_string('restart_succeed'))
        app.last_restart_time = time.time()
        # await asyncio.sleep(5)
        # await answer.delete()
        # raise pyrogram.StopPropagation()
    elif answer.text == 'n':
        await answer.edit_text(app.get_core_string('restart_cancel'))
        await message.edit_text(message.text.html + '\n\n' + app.get_core_string('restart_cancel'))
        await asyncio.sleep(5)
        await answer.delete()


