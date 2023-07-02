import html
import re

from pyrogram import filters
from pyrogram.handlers.handler import Handler
from pyrogram.filters import Filter, OrFilter, AndFilter, InvertFilter

from .attribute import Attribute
from .bot_object import BotObject

from utils import text_utils

all_filters = ['me', 'bot', 'text', 'reply', 'audio', 'document', 'photo',
               'caption', 'forwarded', 'contact', 'sticker', 'incoming', 'outgoing',
               'all', 'animation', 'game', 'video', 'media_group', 'voice', 'video_note',
               'location', 'venue', 'web_page', 'poll', 'dice', 'private', 'media_spoiler',
               'group', 'channel', 'new_chat_members', 'left_chat_member', 'new_chat_title',
               'new_chat_photo', 'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created',
               'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message',
               'game_high_score', 'reply_keyboard', 'inline_keyboard', 'mentioned', 'via_bot',
               'video_chat_started', 'video_chat_ended', 'video_chat_members_invited', 'service',
               'media', 'scheduled', 'from_scheduled', 'linked_channel',
               'from_command', 'from_commands', 'from_user', 'from_users', 'from_chat', 'from_chats', 'regex',
               'and', 'or', 'not',
               'i_am_user', 'i_am_bot', 'admin'
               ]

re_flags = [
    'template_mode',  # template mode
    'ignore_case',  # ignore case sensitivity
    'locale',  # use current locale
    'multiline',  # treat target as multiline string
    'dotall',  # dot matches \n
    'unicode',  # use unicode "locale"
    'verbose',  # ignore whitespace and comments
    'debug',  # debug mode
    'ascii',  # use ascii "locale"
]


class Command(BotObject):
    attributes = [
        Attribute('func', callable),
        Attribute('handler', Handler),
        Attribute('group', int),
        Attribute('filters', Filter),
        Attribute('filter_string', str, ''),
        Attribute('documentation', str, None),
        Attribute('handler_type', str, ''),
    ]

    filter_string: str
    filters: Filter
    documentation: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = None
        self.command_filters = []
        self.resolved_filters = resolve_filter(self.filters, self.command_filters)

    def init(self, module):
        self.module = module
        self.filter_string = self.filter_string if self.filter_string else repr_filter(self, self.filters)

    def repr_filter_with_get_string(self):
        to_replace = re.finditer(r'\{(filter_(.+?))}', self.filter_string)
        to_replace = filter(lambda x: x.group(2), to_replace)

        filter_string = text_utils.format_text(
            self.filter_string,
            **{flt.group(1): self.module.app.get_core_string(flt.group(1))
               for flt in to_replace},
        )

        for match in re.finditer(r'\{__doc__=(.+?)}', filter_string, re.DOTALL):
            doc = match.group(1)
            filter_string = re.sub(fr'{{__doc__={doc}}}', self.module.decode_string(doc), filter_string, re.DOTALL)
        return filter_string


def combine(a, b):
    for i in a:
        for j in b:
            yield i, j


def resolve_filter(filter_, commands=None):
    if commands is None:
        commands = []
    if isinstance(filter_, AndFilter):
        return {
            '_type': 'and',
            'filter1': resolve_filter(filter_.base, commands),
            'filter2': resolve_filter(filter_.other, commands)
        }
    if isinstance(filter_, OrFilter):
        return {
            '_type': 'or',
            'filter1': resolve_filter(filter_.base, commands),
            'filter2': resolve_filter(filter_.other, commands)
        }
    if isinstance(filter_, InvertFilter):
        return {'_type': 'not', 'filter1': resolve_filter(filter_.base, commands)}

    if filter_.__class__.__name__ == 'CommandFilter' and \
            hasattr(filter_, 'commands') and hasattr(filter_, 'prefixes'):
        commands.append(filter_)

    return filter_


def repr_filter(self, filter_):
    if isinstance(filter_, AndFilter):
        if isinstance(filter_.base, OrFilter):
            if isinstance(filter_.other, OrFilter):
                return f'({repr_filter(self, filter_.base)}) {{filter_and}} ({repr_filter(self, filter_.other)})'
            return f'({repr_filter(self, filter_.base)}) {{filter_and}} {repr_filter(self, filter_.other)}'
        if isinstance(filter_.other, OrFilter):
            return f'{repr_filter(self, filter_.base)} {{filter_and}} ({repr_filter(self, filter_.other)})'
        return f'{repr_filter(self, filter_.base)} {{filter_and}} {repr_filter(self, filter_.other)}'
    if isinstance(filter_, OrFilter):
        return f'{repr_filter(self, filter_.base)} {{filter_or}} {repr_filter(self, filter_.other)}'
    if isinstance(filter_, InvertFilter):
        if isinstance(filter_.base, (AndFilter, OrFilter)):
            return '{{filter_not}} (' + repr_filter(self, filter_.base) + ')'
        return '{{filter_not}} ' + repr_filter(self, filter_.base)

    if filter_.__class__.__name__ == 'CommandFilter':
        filter_.client = self.module.app
        commands = []
        for p, c in combine(filter_.prefixes, filter_.commands):
            commands.append(p + c)
        if len(commands) == 1:
            return '{{filter_from_command}} {commands}'.format(
                commands=', '.join([f'<code>{i}</code>' for i in commands]))
        else:
            return '{{filter_from_commands}} {commands}'.format(
                commands=', '.join([f'<code>{i}</code>' for i in commands]))

    if filter_.__class__.__name__ == 'RegexFilter':
        pattern = filter_.p.pattern
        flags = bin(filter_.p.flags)[2:][::-1]
        flags_string = []
        for i in range(len(flags)):
            if flags[i] == '1':
                flags_string.append('{filter_re_flag_' + re_flags[i] + '}')
        if not flags_string:
            flags_string = ['{filter_re_no_flag}']

        flags_string = ', '.join(flags_string)
        return '{{filter_regex}} {regular_expression} ({{filter_regex_flags}} {flags})'.format(
            regular_expression=f'<code>r{repr(pattern)}</code>',
            flags=flags_string
        )

    if isinstance(filter_, filters.user):
        users = ['uid=' + str(user) for user in filter_]
        if len(filter_) == 1:
            return '{{filter_from_user}} {}'.format(', '.join(users))
        else:
            return '{{filter_from_users}} {}'.format(', '.join(users))

    if isinstance(filter_, filters.chat):
        chats = ['chid=' + str(chat) for chat in filter_]
        if len(filter_) == 1:
            return '{{filter_from_chat}} {}'.format(', '.join(chats))
        else:
            return '{{filter_from_chats}} {}'.format(', '.join(chats))

    for flt in all_filters:
        if hasattr(filters, flt) and getattr(filters, flt) == filter_:
            return f'{{filter_{flt}}}'

    if hasattr(filter_, '__doc__') and filter_.__doc__:
        return f"{{__doc__={filter_.__doc__}}}"

    return html.escape(repr(filter_))
