import re
import html
from typing import Union, List

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

filters.custom_command = filters.command


def get_prefixes(flt, app):
    if flt.prefixes is None:
        current_prefixes = app.get_command_prefixes()
        if current_prefixes is None:
            return ('/',)
        return current_prefixes

    return flt.prefixes


def dynamic_command(
        commands: Union[str, List[str]],
        prefixes: Union[str, List[str]] = None,
        case_sensitive: bool = False
):
    command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")


    async def func(flt, client, message):
        username = client.me.username or ""
        text = message.text or message.caption
        message.command = None

        if not text:
            return False

        for prefix in flt.get_prefixes:
            if not text.startswith(prefix):
                continue

            without_prefix = text[len(prefix):]

            for cmd in flt.commands:
                if not re.match(rf"^(?:{cmd}(?:@?{username})?)(?:\s|$)", without_prefix,
                                flags=re.IGNORECASE if not flt.case_sensitive else 0):
                    continue

                without_command = re.sub(rf"{cmd}(?:@?{username})?\s?", "", without_prefix, count=1,
                                         flags=re.IGNORECASE if not flt.case_sensitive else 0)

                # match.groups are 1-indexed, group(1) is the quote, group(2) is the text
                # between the quotes, group(3) is unquoted, whitespace-split text

                # Remove the escape character from the arguments
                message.command = [cmd] + [
                    re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
                    for m in command_re.finditer(without_command)
                ]

                return True

        return False

    commands = commands if isinstance(commands, list) else [commands]
    commands = {c if case_sensitive else c.lower() for c in commands}

    prefixes = [] if prefixes is None else prefixes
    prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
    prefixes = set(prefixes) if prefixes else {""}

    return filters.create(
        func,
        "CommandFilter",
        commands=commands,
        prefixes=prefixes,
        get_prefixes=get_prefixes,
        case_sensitive=case_sensitive
    )
