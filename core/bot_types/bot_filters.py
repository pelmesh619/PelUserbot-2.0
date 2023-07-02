import inspect
import re
import html
from typing import Union, List, Callable

from pyrogram import filters, enums
from pyrogram.types import CallbackQuery, Message, InlineQuery

filters.old_me = filters.me


async def admin_filter_function(_, b, m):
    if isinstance(m, CallbackQuery):
        m = m.message
        user = m.from_user
    elif isinstance(m, Message):
        user = m.from_user
    else:
        return False

    chat_member = await b.get_chat_member(m.chat.id, user.id)
    return chat_member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]


admin = filters.create(admin_filter_function)
filters.admin = admin


async def i_am_bot_filter_function(_, b, __):
    return b.me.is_bot


i_am_bot = filters.create(i_am_bot_filter_function)
filters.i_am_bot = i_am_bot


async def i_am_user_filter_function(_, b, __):
    return not b.me.is_bot


i_am_user = filters.create(i_am_user_filter_function)
filters.i_am_user = i_am_user


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

    async def func(_, __, m):
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


def get_prefixes(flt):
    if flt._prefixes is None:
        if flt.client:
            current_prefixes = flt.client.get_command_prefixes()
            if current_prefixes is not None:
                return current_prefixes
        return ('/',)

    return flt._prefixes


def dynamic_command(
        commands: Union[str, List[str]],
        prefixes: Union[str, List[str]] = None,
        case_sensitive: bool = False
):
    command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

    async def func(flt, client, message):
        if flt.client is None:
            flt.client = client
        username = client.me.username or ""
        text = message.text or message.caption
        message.command = None

        if not text:
            return False

        for prefix in flt.get_prefixes():
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

    if prefixes is not None:
        prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
        prefixes = set(prefixes) if prefixes else {""}

    return filters.create(
        func,
        "CommandFilter",
        commands=commands,
        prefixes=property(lambda self: self.get_prefixes()),
        _prefixes=prefixes,
        case_sensitive=case_sensitive,
        get_prefixes=get_prefixes,
        client=None,
    )


filters.command = dynamic_command


def exception(
        exception_type=Exception,
        filter_function: Callable = lambda _, __, ___: True,
):
    async def func(flt, client, update):
        this_exception = update.exception

        if not isinstance(this_exception, exception_type):
            return False

        if inspect.iscoroutinefunction(filter_function):
            x = await filter_function(flt, client, update)
        else:
            x = await client.loop.run_in_executor(
                client.executor,
                filter_function,
                flt, client, update
            )

        if not x:
            return False

        return True

    return filters.create(
        func,
        "ExceptionFilter",
        exception_type=exception_type,
    )


filters.exception = exception
