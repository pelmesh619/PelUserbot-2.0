from pyrogram import Client, filters
from core import Module, Author


module = Module(
    name='string_id=module_name',
    description='string_id=description',
    authors=Author('pelmeshke', telegram_username='pelmeshke', job='string_id=author_creator'),
    strings={
        'ru': {
            'module_name': 'ASCII-детектор',
            'description': 'Подчеркивает все ASCII-символы в тексте сообщения',
            'author_creator': 'Создатель',
            'bot_works': 'Бот работает',
            'docs_ascii_handler': 'Подчеркивает ASCII-символы в тексте сообщения, на которое дается ответ командой {_cmd_pref}ascii',
            'ascii_symbols': 'Вот ASCII-символы в этом сообщении: {text}',
            'no_reply': 'Ответьте командой на сообщение'
        },
    },
    strings_source_filename=None,
    update_source_link=None,
    config={},
    requirements=[],
    changelog={}
)


@Client.on_message(filters.command('ascii'))
async def ascii_handler(_, msg):
    """string_id=docs_ascii_handler"""
    reply = msg.reply_to_message
    if not reply:
        return await msg.reply(msg.get_string('no_reply'))

    text = list(reply.text)
    for i in range(len(text)):
        if 32 < ord(text[i]) <= 126:
            text[i] = '<u>' + text[i] + '</u>'

    await msg.reply(msg.get_string('ascii_symbols', text=''.join(text)))
