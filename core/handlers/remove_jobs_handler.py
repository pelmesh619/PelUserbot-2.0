from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('remove_jobs'))
async def remove_jobs_handler(app, message):

    all_jobs = app.scheduler.get_jobs()

    if len(all_jobs) == 0:
        return await message.reply(app.get_core_string('remove_jobs_there_are_no_jobs'))

    app.scheduler.remove_all_jobs()
    await message.reply(
        app.get_core_string(
            'remove_jobs_all_jobs_are_removed',
            jobs=len(all_jobs),
            job_form=app.get_core_string_form('job_form', len(all_jobs)),
            removed_form=app.get_core_string_form('removed_feminine_form', len(all_jobs))
        )
    )

