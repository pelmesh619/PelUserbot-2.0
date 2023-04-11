import copy
import logging
import os
import re
import json
import time
from typing import Union, List, Tuple

from pyrogram.filters import Filter
from pyrogram import filters

from .attribute import Attribute
from .bot_object import BotObject
from .author import Author
from .module_strings import ModuleStrings
from .module_database import ModuleDatabase
from .command import Command

from utils import text_utils, time_utils

log = logging.Logger(__name__)


class Module(BotObject):
    attributes = [
        Attribute('module_id', str, None),
        Attribute('name', str, None),
        Attribute('authors', list, []),
        Attribute('description', str, None),
        Attribute('version', str, ''),
        Attribute('release_date', str, None),
        Attribute('strings', dict, {}),
        Attribute('strings_source_filename', str, None),
        Attribute('database', ModuleDatabase, None),
        Attribute('database_schema', str, None),
        Attribute('config', dict, {}),
        Attribute('requirements', list, []),
        Attribute('changelog', dict, {})
    ]

    module_id: str
    name: str
    authors: List[Author]
    description: str
    version: str
    release_date: str
    strings: ModuleStrings
    strings_source_filename: str
    database: ModuleDatabase
    database_schema: str
    config: dict
    requirements: list
    changelog: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.strings, dict):
            self.strings = ModuleStrings(self.strings)
            self.strings.strings_filename = self.strings_source_filename
        self.strings.module = self
        self.app = None
        self.handlers = None
        self.installation_date = 1
        self.default_config = {}
        self.python_module = None
        self.commands = []

    def init(self, app, module_id, added_handlers, python_module):
        self.app = app
        self.module_id = module_id
        self.strings.module_id = self.module_id
        self.handlers = added_handlers
        self.installation_date = time.time()
        self.default_config = copy.deepcopy(getattr(self, 'config', {}))
        self.python_module = python_module
        self.resolve_commands()

        config_filename = os.path.join(
            self.app.get_config_parameter('module_configs_directory'),
            self.module_id + '.json'
        )
        if os.path.exists(config_filename):
            self.load_config()
        elif self.config:
            self.save_config()

        if not self.database:
            if self.database_schema:
                self.database = ModuleDatabase(self.database_schema)
        if self.database:
            self.database.init(self)

    def full_name(self):
        """
        Makes module's full name
        Example: name is Tester, module_id is test, full_name is Tester (test)

        :return: module's full name
        """
        return ('<i>' + self.decode_string(self.name) + '</i> (<code>' + self.module_id + '</code>)'
                if self.name else '<code>' + self.module_id + '</code>')

    def get_string(self, string_id, default=None, lang_code=None, _module_id=None, **kwargs):
        if _module_id is not None:
            return self.app.get_string(
                string_id, default=default, lang_code=lang_code,
                _module_id=_module_id, **kwargs
            )
        return self.strings.get_string(string_id, default=default, lang_code=lang_code, **kwargs)

    def get_string_form(self, string_id, value, default=None, lang_code=None, _module_id=None, **kwargs):
        if _module_id is not None:
            return self.app.get_string_form(
                string_id, value, default=default, lang_code=lang_code,
                _module_id=_module_id, **kwargs
            )
        return self.strings.get_string_form(string_id, value, default=default, lang_code=lang_code, **kwargs)

    def get_config(self):
        self.load_config()
        return self.config

    def get_config_parameter(self, key, default=None):
        return self.get_config().get(key, default)

    def set_config_parameter(self, key, value):
        self.config[key] = value
        self.save_config()

    def load_config(self):
        config_filename = os.path.join(
            self.app.get_config_parameter('module_configs_directory'),
            self.module_id + '.json'
        )
        try:
            config = json.load(open(config_filename, encoding='utf8'))
        except Exception as e:
            log.error(f'While loading config of module {self.module_id} error is raised', exc_info=e)
        else:
            self.config = config

    def save_config(self):
        filename = os.path.join(
            self.app.get_config_parameter('module_configs_directory'),
            self.module_id + '.json'
        )

        json.dump(self.config, open(filename, 'w', encoding='utf8'), ensure_ascii=False, indent=4)

    def remove_handler(self, handler, group):
        self.handlers.remove((handler, group))

    def resolve_commands(self):
        for func in self.handlers:
            for handler, group in func.handlers:
                docs = func.__doc__
                handler_type = type(handler).__name__
                command = Command(func, handler, group, handler.filters, documentation=docs, handler_type=handler_type)
                command.module = self
                self.commands.append(command)

    def decode_string(self, attr):
        if re.search(r'^string_id=([\w\-_.]+)', str(attr)):
            return self.get_string(re.search(r'^string_id=([\w\-_.]+)', str(attr)).group(1))
        return attr

    def get_full_info(self):

        authors_strings = []
        authors = self.authors if isinstance(self.authors, list) else [self.authors]
        for author in authors:
            if author.telegram_username:
                author_string = f'<a href="t.me/{author.telegram_username.strip("@")}">{author.name}</a>'
            else:
                author_string = author.name
            if author.link:
                author_string += f' ({author.link})'
            if author.job:
                author_string += f' — {self.decode_string(author.job)}'
            authors_strings.append(author_string)

        all_strings = {}
        localization = {}
        for lang in self.strings.strings:
            all_strings.update(self.strings.strings[lang])
            localization[lang] = len(self.strings.strings[lang])

        all_strings_count = len(all_strings)

        return self.app.get_core_string(
            'module_full_info_template',
            name=self.full_name(),
            author_form=self.app.get_core_string_form('author_form', len(authors)),
            authors=', '.join(authors_strings) if self.authors
            else self.app.get_core_string('author_unknown'),
            version=self.decode_string(self.version) or
                    self.app.get_core_string('version_unknown'),
            description_template=self.app.get_core_string(
                'description_template',
                description=self.decode_string(self.description),
            ) if self.description else '',
            localization_template=self.app.get_core_string(
                'localization_template',
                languages=', '.join(
                    [self.app.get_core_string(lang + '_language', default=lang) +
                     ' (' + str(round(strings_count * 100 / all_strings_count, 2)) + '%)'
                     for lang, strings_count in localization.items()]
                ),
            ) if all_strings_count > 0 else '',
            handlers_template=self.app.get_core_string(
                'handlers_template',
                handlers_count=len(self.commands),
                handlers_form=self.app.get_core_string_form('handler_form', len(self.commands)),
                module_id=self.module_id,
                first_handler='<code>' + self.commands[0].func.__name__ + '</code>',
                first_handler_filter_string=self.commands[0].repr_filter_with_get_string(),
                first_handler_type=self.app.get_core_string(
                    'handler_' + self.commands[0].handler_type,
                ),
                first_handler_docs=':\n          ' + text_utils.cut_text(
                    self.decode_string(self.commands[0].documentation).strip('\n')
                )
                if self.commands[0].documentation else '',
                and_handlers_more=self.app.get_core_string(
                    'and_handlers_more',
                    and_handlers_count_more=len(self.commands) - 1,
                    and_handler_more_form=self.app.get_core_string_form('handler_form', len(self.commands) - 1),
                ) if len(self.commands) > 1 else '',
            ) if self.handlers else self.app.get_core_string('handlers_there_are_no_handlers'),
            requirements_template=self.app.get_core_string(
                'requirements_template',
                requirements=', '.join(self.requirements),
            ) if self.requirements else '',
            config_template=self.app.get_core_string(
                'config_template',
                configs_count=len(self.config),
                parameter_form=self.app.get_core_string_form('parameter_form', len(self.config)),
                module_id=self.module_id,
            ) if self.config else '',
            changelog_template=self.app.get_core_string(
                'changelog_template',
                current_version=self.decode_string(self.version),
                changelog_current_version=self.decode_string(self.changelog.get(self.version)),
                module_id=self.module_id,
            ) if self.version and self.changelog.get(self.version)
            else self.app.get_core_string(
                'changelog_there_is_no_changelog_of_this_version',
                current_version=self.decode_string(self.version),
                module_id=self.module_id,
            ) if self.version and not self.changelog.get(self.version) and self.changelog
            else self.app.get_core_string(
                'changelog_version_is_not_set',
                module_id=self.module_id,
            ) if not self.version and self.changelog else '',
        )

    def get_short_info(self):
        return self.app.get_core_string(
            'module_short_info',
            module_name=self.full_name(),
            handlers_count=len(self.commands),
            handler_form=self.app.get_core_string_form('handler_form', len(self.commands)),
            description=':\n    ' + text_utils.cut_text(
                self.decode_string(self.description)) if self.description else '',
            module_id=self.module_id,
        )

    def command(
            self,
            commands: Union[str, List[str], Tuple[str]],
            prefixes: Union[str, List[str], Tuple[str]] = '/',
            case_sensitive: bool = False,
            separator: str = '#'
    ) -> Filter:

        commands = commands if isinstance(commands, (list, tuple)) else [commands]
        commands = [self.module_id + separator + command for command in commands]

        return filters.command(commands, prefixes, case_sensitive)

    def get_strings_by_lang_code(self, lang_code):
        return type(
            'ModuleStrings{}'.format(lang_code.upper()),
            (ModuleStrings, ),
            {
                'lang_code': lang_code,
                '__call__': wrapper(self.strings.get_string, lang_code),
                'get_string': wrapper(self.strings.get_string, lang_code),
                'get_string_form': wrapper(self.strings.get_string_form, lang_code),
                'get_core_string': wrapper(self.app.get_core_string, lang_code),
                'get_core_string_form': wrapper(self.app.get_core_string_form, lang_code),
                'time_to_string': wrapper(time_utils.time_to_string, lang_code, self.app),
                'date_to_string': wrapper(time_utils.date_to_string, lang_code, self.app),
            }
        )()


def wrapper(func, lang_code, app=None):
    def f(*args, **kwargs):
        if 'lang_code' not in kwargs or kwargs.get('lang_code', None) is None:
            kwargs['lang_code'] = lang_code
        if app is not None and 'app' not in kwargs or kwargs.get('app', None) is None:
            kwargs['app'] = app

        return func(*args, **kwargs)

    return staticmethod(f)
