from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('kill_all'))
async def kill_all_handler(app, msg):
    dp = app.dispatcher

    try:
        count = dp.kill_all_processes()
    except Exception as e:
        await msg.reply(msg.get_string('all_processes_kill_error', error=repr(e)))
        return

    await msg.reply(
        msg.get_string(
            'all_processes_was_killed',
            worker_count=count,
            stopped_form=app.get_core_string_form('stopped_form', count),
            worker_form=app.get_core_string_form('worker_form', count)
        )
    )
