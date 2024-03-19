from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('kill'))
async def kill_handler(app, msg):
    dp = app.dispatcher
    if not msg.command[1:]:
        await msg.reply('kill_enter_to_kill')
        return

    handler_name = msg.command[1]
    if handler_name.isdigit():
        handler_name = int(handler_name)

    for i in range(len(dp.handler_worker_tasks)):
        lock = dp.locks_list[i]

        handler = getattr(lock, 'handler_name', None)
        if lock.locked() and (handler == handler_name or i == handler_name):
            try:
                dp.kill_process(i)
            except Exception as e:
                await msg.reply(msg.get_string('process_kill_error', num=i, handler=handler, error=repr(e)))
                return

            await msg.reply(msg.get_string('process_killed', num=i, handler=handler))
            return
        elif not lock.locked() and i == handler_name:
            await msg.reply(msg.get_string('process_was_not_running', num=i))
            return

    await msg.reply(msg.get_string('process_was_not_found', handler=handler_name))
