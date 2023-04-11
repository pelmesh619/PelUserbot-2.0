from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('scheduler', '!'))
async def scheduler_handler(app, message):

    for j in app.scheduler.get_jobs():
        print(j.trigger)
        print(j.id)
        print(j.name)
        print(j.func)

