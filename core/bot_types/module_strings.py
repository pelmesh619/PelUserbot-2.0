import logging
import json
import os
import re
import time

from .attribute import Attribute
from .bot_object import BotObject

from utils import format_text, time_utils, memory_utils

log = logging.Logger(__name__)


class ModuleStrings(BotObject):
    attributes = [
        Attribute('strings', dict, {}),
        Attribute('strings_filename', str, None),
        Attribute('do_reloading', bool, True),
        Attribute('lang_code', str, None)
    ]

    strings: dict
    strings_filename: str
    do_reloading: bool

    STRINGS_RELOADING_TIME = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._module = None
        self.module_id = ''
        self.last_reloading = 0
        self.lang_code = None

    def get_strings_by_lang_code(self, lang_code):
        module_strings = ModuleStrings(self.strings, self.strings_filename, self.do_reloading, lang_code)
        module_strings._module = self._module
        module_strings.module_id = self._module.module_id
        return module_strings

    def __repr__(self):
        return 'ModuleStrings(module_id=\'{self.module_id}\', lang_code=\'{self.lang_code}\')'

    def __str__(self):
        return self.__repr__()

    def reload_string(self):
        if self.strings_filename and self.do_reloading:
            try:
                filename = os.path.join(
                    self._module.app.get_config_parameter('resources_directory'),
                    'strings',
                    self.strings_filename,
                )
                file = json.load(open(filename, encoding='utf8'))
            except Exception as e:
                log.error(f'Error raised while strings of module "{self.module_id}" were reloading', exc_info=e)
            else:
                self.strings = file
            self.last_reloading = time.time()

    def find_string(self, string_id: str, lang_code: str):
        if self._module:
            if self._module.app:
                self._module.app.get_string_calls += 1

        if self.last_reloading + self.STRINGS_RELOADING_TIME < time.time():
            self.reload_string()

        strings = getattr(self, 'strings', {})

        return_string = None
        if self._module.app:
            replace_string_from_other_languages = self._module.app.get_config_parameter(
                'replace_string_from_other_languages'
            )
        else:
            replace_string_from_other_languages = True

        if lang_code not in strings:
            if string_id in strings:
                return strings[string_id]
            if replace_string_from_other_languages:
                for i in strings:
                    if isinstance(strings[i], dict) and string_id in strings[i]:
                        log.warning(f'[language "{lang_code}" was not found, '
                                    f'replacing from "{i}" {string_id, lang_code, self.module_id}]'
                                    )
                        return strings[i][string_id]
            raise KeyError(f'[language "{lang_code}" was not found {string_id, lang_code, self.module_id}]')
        else:
            if string_id in strings[lang_code]:
                return strings[lang_code][string_id]
            if replace_string_from_other_languages:
                for i in strings:
                    if isinstance(strings[i], dict) and string_id in strings[i]:
                        log.warning(f'[language "{lang_code}" was not found, '
                                    f'replacing from "{i}" {string_id, lang_code, self.module_id}]'
                                    )
                        return strings[i][string_id]
        if not return_string:
            raise KeyError(f'[string "{string_id}" was not found {string_id, lang_code, self.module_id}]')

        return return_string

    def __call__(self, *args, **kwargs):
        return self.get_string(*args, **kwargs)

    def get_string(self, string_id: str, default=None, lang_code: str = None, **format_kwargs):
        if lang_code is None:
            lang_code = self.lang_code
        if lang_code is None:
            if self._module and self._module.app:
                lang_code = self._module.app.lang_code
            else:
                lang_code = 'ru'

        try:
            string = self.find_string(string_id, lang_code=lang_code)
        except KeyError as e:
            log.warning(e.args[0])
            if default:
                string = default
            else:
                string = e.args[0]

        if isinstance(string, str):
            if self._module.app:
                format_kwargs['_cmd_pref'] = self._module.app.get_command_prefix()
            for i in re.finditer('{(time_to_string\((.+)\))}', string):
                key = i.group(2)
                if key in format_kwargs:
                    format_kwargs[i.group(1)] = self.time_to_string(format_kwargs[key])
            string = format_text(string, **format_kwargs)

        return string

    def get_string_form(self, string_id: str, value, default=None, lang_code: str = None, **format_kwargs):
        if lang_code is None:
            lang_code = self.lang_code
        if lang_code is None:
            lang_code = self._module.app.lang_code

        try:
            strings = self.find_string(string_id, lang_code)
        except KeyError as e:
            log.warning(e.args[0])
            if default:
                strings = default
            else:
                strings = e.args[0]

        if not isinstance(strings, dict) or \
                not all([callable(i) or isinstance(i, str) and i.startswith('lambda') for i in strings]):
            return strings

        string = None
        for func, string in strings.items():
            if callable(func) and func(value):
                break
            elif isinstance(func, str) and func.startswith('lambda'):
                try:
                    if eval(func)(value):
                        break
                except SyntaxError as e:
                    log.debug(f'[ModuleStrings.get_string_form, {self.module_id}] '
                              f'filter {func.__name__} has some error in executing: {repr(e)}'
                              )
                except Exception as e:
                    log.debug(f'[ModuleStrings.get_string_form, {self.module_id}] '
                              f'filter {func.__name__} has some error in executing: {repr(e)}'
                              )

        if string is not None:
            format_kwargs['_cmd_pref'] = self._module.app.get_command_prefix()
            for i in re.finditer('{(time_to_string\((.+)\))}', string):
                key = i.group(2)
                if key in format_kwargs:
                    format_kwargs[i.group(1)] = self.time_to_string(format_kwargs[key])
            return format_text(string, **format_kwargs)

        return f'[string form "{string_id}" via value "{value}" was ' \
               f'not found in {string_id, lang_code, self.module_id}]'

    def get_core_string(self, string_id: str, default=None, lang_code: str = None, **format_kwargs):
        if lang_code is None:
            lang_code = self.lang_code

        return self._module.app.get_core_string(string_id, default, lang_code, **format_kwargs)

    def get_core_string_form(self, string_id: str, value, default=None, lang_code: str = None, **format_kwargs):
        if lang_code is None:
            lang_code = self.lang_code

        return self._module.app.get_core_string_form(string_id, value, default, lang_code, **format_kwargs)

    def identify_string(self, string, match_func=re.search, flags=0):
        strings = self.strings
        _special_chars_map = {i: '\\' + chr(i) for i in b'()[]<>{}?*+-|^$\\/.&~#'}

        for lang in strings:
            for str_id in strings[lang]:
                if isinstance(strings[lang][str_id], dict):
                    current_strings = list(strings[lang][str_id].values())
                elif isinstance(strings[lang][str_id], list):
                    current_strings = strings[lang][str_id]
                else:
                    current_strings = [strings[lang][str_id]]

                for current_string in current_strings:

                    pattern = re.compile(re.sub(r'\\\{.*?\\}', '(.*)', current_string.translate(_special_chars_map)),
                                         flags=flags)

                    match = match_func(pattern, string)

                    if match:
                        return str_id, lang, match

        return False

    def get_pattern(self, string_id, default=None, lang_code=None):
        """
        Makes from string got by string_id regex pattern.
        How it works: replacement fields (ex '{abc}') will be replaced by '(.*)',
        other regular special symbols will be replaced with \\
        Example: 'This <i>module</i> is {module}' => 'This \<i\>module\<\/i\> is (.*)'

        Args:
            string_id: `str` - string id of the string
            default: `Any` - if string was not found, `default` will be returned
            lang_code: `str` - language code

        Returns:
            pattern: `str`
        """
        if not lang_code:
            lang_code = self.lang_code

        string = self.find_string(string_id, lang_code=lang_code)

        _special_chars_map = {i: '\\' + chr(i) for i in b'()[]<>{}?*+-|^$\\/.&~#'}
        string = re.compile(re.sub(r'\\\{.*?\\}', '(.*)', string.translate(_special_chars_map)))

        if string == f'[string "{string_id}" was not found {string_id, lang_code}]' or \
                string == f'[language "{lang_code}" was not found {string_id, lang_code}]':
            print(string)
            if default is not None:
                return default

        return string

    def time_to_string(self, time_value, lang_code=None):
        if lang_code is None:
            lang_code = self.lang_code

        return time_utils.time_to_string(time_value, self._module.app, lang_code)

    def date_to_string(self, time_value=None, tz=None, lang_code=None):
        if lang_code is None:
            lang_code = self.lang_code

        return time_utils.date_to_string(time_value, tz, app=self._module.app, lang_code=lang_code)

    def memory_to_string(self, value, measure=None, round_value=2, lang_code=None):
        if lang_code is None:
            lang_code = self.lang_code

        return memory_utils.memory_to_string(
            value,
            measure=measure,
            round_value=round_value,
            app=self._module.app,
            lang_code=lang_code
        )
