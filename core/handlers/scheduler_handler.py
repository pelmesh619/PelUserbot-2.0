import html

from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('scheduler'))
async def scheduler_handler(app, message):

    all_jobs = app.scheduler.get_jobs()

    if len(all_jobs) == 0:
        return await message.reply(app.get_core_string('scheduler_there_are_no_jobs'))

    jobs_strings = []
    for j in all_jobs:
        jobs_strings.append(
            app.get_core_string(
                'scheduler_job_template',
                id=j.id,
                name=html.escape(j.name),
                desc=j.func.__doc__ if j.func.__doc__ else app.get_core_string('scheduler_no_docs'),
                trigger=j.trigger,
            )
        )

    await message.reply(
        app.get_core_string(
            'scheduler_template',
            jobs='\n\n'.join(jobs_strings),
            amount=len(jobs_strings),
            job_form=app.get_core_string_form('job_form', len(jobs_strings))
        )
    )
