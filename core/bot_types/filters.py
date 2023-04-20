import re
import html

from pyrogram import filters, enums
from pyrogram.types import CallbackQuery, Message, InlineQuery

filters.old_me = filters.me


async def admin(f, b, m):
    if isinstance(m, CallbackQuery):
        m = m.message
        user = m.from_user
    elif isinstance(m, Message):
        user = m.from_user
    else:
        return False

    chat_member = await b.get_chat_member(m.chat.id, user.id)
    return chat_member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]


filters.admin = filters.create(admin)


def identify_string(string_ids, matching_func=re.search, flags=0):
    string_ids = string_ids if isinstance(string_ids, (list, tuple)) else [string_ids]

    async def func(f, b, m):
        if isinstance(m, Message):
            text = m.text or m.caption
        elif isinstance(m, InlineQuery):
            text = m.query
        else:
            text = None
        if not text:
            return

        if hasattr(text, 'html'):
            text = text.html.replace('&lt;', '<').replace('&gt;', '>')
            text = text.replace("&quot;", '"').replace('&#x27;', '\'')

        result = m.get_string.identify_string(text, matching_func, flags=flags)
        if result:
            string_id, lang, match = result
        else:
            return False

        if string_id in string_ids:
            m.identified_string_id = string_id
            m.match = match
            return True
        else:
            return False

    return filters.create(func)


filters.identify_string = identify_string


def reply_identify_string(string_ids, matching_func=re.search, flags=0):
    string_ids = string_ids if isinstance(string_ids, list) else [string_ids]

    async def func(f, b, m):
        reply = m.reply_to_message
        if not reply:
            return False

        text = reply.text or reply.caption
        if not text:
            return
        if hasattr(text, 'html'):
            text = text.html.replace('&lt;', '<').replace('&gt;', '>')
            text = text.replace("&quot;", '"').replace('&#x27;', '\'')

        result = m.get_string.identify_string(text, matching_func, flags=flags)
        if result:
            string_id, lang, match = result
        else:
            return False

        if string_id and string_id in string_ids:
            m.identified_string_id = string_id
            m.match = match
            return True
        else:
            return False

    return filters.create(func)


filters.reply_identify_string = reply_identify_string


