import time

from pyrogram import filters, Client


@Client.on_message(filters.me & filters.command('taskmgr'))
async def taskmgr_handler(app, msg):
    dp = app.dispatcher

    respond = []
    for i in range(len(dp.handler_worker_tasks)):
        lock = dp.locks_list[i]
        if lock.locked():
            module_name = None
            if getattr(lock, 'module', False):
                module_name = lock.module.full_name()

            chat_name = None
            if getattr(lock, 'update', False):
                chat_name = lock.update.chat.title or lock.update.chat.first_name
            respond.append(
                msg.get_string(
                    'process_info',
                    num=i,
                    handler_name=getattr(lock, 'handler_name', None),
                    module_name=module_name,
                    seconds=round(time.time() - getattr(lock, 'start_time', 0), 4),
                    second_form=msg.get_string_form(
                        'second_ago_form',
                        round(time.time() - getattr(lock, 'start_time', 0), 4)
                    ),
                    chat_name=chat_name,
                )
            )

    await msg.reply(
        msg.get_string('task_manager', processes='\n\n'.join(respond), workers=len(dp.handler_worker_tasks))
    )