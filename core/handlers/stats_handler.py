import sys
import time

from pyrogram import Client, filters

from utils import time_utils


@Client.on_message(filters.me & filters.command('stats'))
async def stats_handler(app, message):
    respond = app.get_core_string(
        'stats_template',
        version=app.app_version,
        system=sys.platform,
        starting_time=time.time() - app.starting_time,
        last_restart_time=time.time() - app.last_restart_time,
        modules=len(app.modules),
        handlers=len(sum(app.dispatcher.groups.values(), [])),
        handlers_activated=app.handlers_activated,
        handlers_handled=app.handlers_handled,
        handlers_crushed=app.handlers_crushed,
        get_string_calls=app.get_string_calls,
    )
    await message.reply(respond)

