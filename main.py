from pyrogram import filters, idle

filters.me = filters.user(1134950789)

from core import Peluserbot

__version__ = '2.0.0-alpha1'

client = Peluserbot(app_version=__version__, config_filename='config.json')


@client.on_message(filters.me & filters.command('huh'))
async def fuck(_, message):
    await message.reply('h')
    print('huh', message.from_user)
    # await message.reply('\n'.join(map(str, app.modules)))

client.run()
