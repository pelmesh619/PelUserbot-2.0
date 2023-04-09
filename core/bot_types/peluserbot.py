import os
import logging
import importlib
import json
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, List

from pyrogram import enums, types, raw
from pyrogram.client import Client
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers.handler import Handler
from pyrogram.session import Session

from .module import Module
from .peldispatcher import Peldispatcher

log = logging.getLogger(__name__)
log.level = logging.DEBUG


class Peluserbot(Client):
    """Peluserbot Client. Inherits from Pyrogram Client.


    Parameters:
        name (``str``, *optional*):
            A name for the client, e.g.: "my_account".

        api_id (``int`` | ``str``, *optional*):
            The *api_id* part of the Telegram API key, as integer or string.
            E.g.: 12345 or "12345".

        api_hash (``str``, *optional*):
            The *api_hash* part of the Telegram API key, as string.
            E.g.: "0123456789abcdef0123456789abcdef".

        app_version (``str``, *optional*):
            Application version.
            Defaults to "Pyrogram x.y.z".

        device_model (``str``, *optional*):
            Device model.
            Defaults to *platform.python_implementation() + " " + platform.python_version()*.

        system_version (``str``, *optional*):
            Operating System version.
            Defaults to *platform.system() + " " + platform.release()*.

        lang_code (``str``, *optional*):
            Code of the language used on the client, in ISO 639-1 standard.
            Defaults to "en".

        ipv6 (``bool``, *optional*):
            Pass True to connect to Telegram using IPv6.
            Defaults to False (IPv4).

        proxy (``dict``, *optional*):
            The Proxy settings as dict.
            E.g.: *dict(scheme="socks5", hostname="11.22.33.44", port=1234, username="user", password="pass")*.
            The *username* and *password* can be omitted if the proxy doesn't require authorization.

        test_mode (``bool``, *optional*):
            Enable or disable login to the test servers.
            Only applicable for new sessions and will be ignored in case previously created sessions are loaded.
            Defaults to False.

        bot_token (``str``, *optional*):
            Pass the Bot API token to create a bot session, e.g.: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
            Only applicable for new sessions.

        session_string (``str``, *optional*):
            Pass a session string to load the session in-memory.
            Implies ``in_memory=True``.

        in_memory (``bool``, *optional*):
            Pass True to start an in-memory session that will be discarded as soon as the client stops.
            In order to reconnect again using an in-memory session without having to log in again, you can use
            :meth:`~pyrogram.Client.export_session_string` before stopping the client to get a session string you can
            pass to the ``session_string`` parameter.
            Defaults to False.

        phone_number (``str``, *optional*):
            Pass the phone number as string (with the Country Code prefix included) to avoid entering it manually.
            Only applicable for new sessions.

        phone_code (``str``, *optional*):
            Pass the phone code as string (for test numbers only) to avoid entering it manually.
            Only applicable for new sessions.

        password (``str``, *optional*):
            Pass the Two-Step Verification password as string (if required) to avoid entering it manually.
            Only applicable for new sessions.

        workers (``int``, *optional*):
            Number of maximum concurrent workers for handling incoming updates.
            Defaults to ``min(32, os.cpu_count() + 4)``.

        workdir (``str``, *optional*):
            Define a custom working directory.
            The working directory is the location in the filesystem where Pyrogram will store the session files.
            Defaults to the parent directory of the main script.

        plugins (``dict``, *optional*):
            Smart Plugins settings as dict, e.g.: *dict(root="plugins")*.

        parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
            Set the global parse mode of the client. By default, texts are parsed using both Markdown and HTML styles.
            You can combine both syntaxes together.

        no_updates (``bool``, *optional*):
            Pass True to disable incoming updates.
            When updates are disabled the client can't receive messages or other updates.
            Useful for batch programs that don't need to deal with updates.
            Defaults to False (updates enabled and received).

        takeout (``bool``, *optional*):
            Pass True to let the client use a takeout session instead of a normal one, implies *no_updates=True*.
            Useful for exporting Telegram data. Methods invoked inside a takeout session (such as get_chat_history,
            download_media, ...) are less prone to throw FloodWait exceptions.
            Only available for users, bots will ignore this parameter.
            Defaults to False (normal session).

        sleep_threshold (``int``, *optional*):
            Set a sleep threshold for flood wait exceptions happening globally in this client instance, below which any
            request that raises a flood wait will be automatically invoked again after sleeping for the required amount
            of time. Flood wait exceptions requiring higher waiting times will be raised.
            Defaults to 10 seconds.

        hide_password (``bool``, *optional*):
            Pass True to hide the password when typing it during the login.
            Defaults to False, because ``getpass`` (the library used) is known to be problematic in some
            terminal environments.

        config_filename (``str``, *optional*):
            Set config filename and client will use config for some parameters instead of entering them directly
            Config file will open as .json file, e.g.: *{"name": "Peluserbot", "app_version": "1.32.3-beta"}*
    """

    NAME = 'Peluserbot'
    APP_VERSION = Client.APP_VERSION
    DEVICE_MODEL = Client.DEVICE_MODEL
    SYSTEM_VERSION = Client.SYSTEM_VERSION
    LANG_CODE = Client.LANG_CODE
    WORKERS = Client.WORKERS
    WORKDIR = Client.WORKDIR

    MODULE_CONFIGS_DIRECTORY = 'module_configs'
    RESOURCES_DIRECTORY = 'resources'
    DOWNLOADS_DIRECTORY = 'downloads'
    DATABASE_DIRECTORY = 'database'
    DEFAULT_CONFIG = {
        'module_configs_directory': MODULE_CONFIGS_DIRECTORY,
        'resources_directory': RESOURCES_DIRECTORY,
        'downloads_directory': DOWNLOADS_DIRECTORY,
        'database_directory': DATABASE_DIRECTORY,
        'will_error_message_send': True,
        'replace_string_from_other_languages': True,
    }
    DEFAULT_CONFIG_FILENAME = 'config.json'

    def __init__(
            self,
            name: str = NAME,
            api_id: Union[int, str] = None,
            api_hash: str = None,
            app_version: str = APP_VERSION,
            device_model: str = DEVICE_MODEL,
            system_version: str = SYSTEM_VERSION,
            lang_code: str = LANG_CODE,
            ipv6: bool = False,
            proxy: dict = None,
            test_mode: bool = False,
            bot_token: str = None,
            session_string: str = None,
            in_memory: bool = None,
            phone_number: str = None,
            phone_code: str = None,
            password: str = None,
            workers: int = WORKERS,
            workdir: str = WORKDIR,
            plugins: dict = None,
            parse_mode: "enums.ParseMode" = enums.ParseMode.DEFAULT,
            no_updates: bool = None,
            takeout: bool = None,
            sleep_threshold: int = Session.SLEEP_THRESHOLD,
            hide_password: bool = False,
            config_filename: str = None
    ):
        Dispatcher.handler_worker = Peldispatcher.handler_worker
        if config_filename is not None:
            config_data = json.loads(open(config_filename, encoding='utf8').read().encode().decode('utf-8-sig'))
            self._config = config_data
            self._config_filename = config_filename

            # This code redefines variables if they are in the config
            # If variable was in the config and was taken as argument
            # value that was taken as argument will be set except api_id and api_hash
            name = config_data.get('name', name) \
                if name == self.NAME else name
            api_id = config_data.get('api_id', api_id)
            api_hash = config_data.get('api_hash', api_hash)
            app_version = app_version or config_data.get('app_version', app_version) \
                if app_version == self.APP_VERSION else app_version
            device_model = config_data.get('device_model', device_model) \
                if device_model == self.DEVICE_MODEL else device_model
            lang_code = config_data.get('lang_code', lang_code) \
                if lang_code == self.LANG_CODE else lang_code
            bot_token = bot_token or config_data.get('bot_token', bot_token)
            workdir = config_data.get('workdir', workdir) \
                if workdir == self.WORKDIR else workdir
            plugins = plugins or config_data.get('plugins', plugins)
            parse_mode = config_data.get('parse_mode', parse_mode) \
                if parse_mode == enums.ParseMode.DEFAULT else parse_mode

            for k, v in self.DEFAULT_CONFIG.items():
                if k not in self._config:
                    self._config[k] = v

        # Creating working directories
        if not os.path.exists(workdir):
            os.mkdir(workdir)

        for directory in [
            'module_configs_directory',
            'resources_directory',
            'downloads_directory',
            'database_directory'
        ]:
            if not os.path.exists(self.get_config_parameter(directory)):
                os.mkdir(self.get_config_parameter(directory))

        self.modules = []
        self.answers = {}
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

        self.get_string_calls = 0
        self.handlers_activated = 0
        self.handlers_handled = 0
        self.handlers_crushed = 0
        self.starting_time = time.time()
        self.last_restart_time = self.starting_time

        super().__init__(
            name=name,
            api_id=api_id,
            api_hash=api_hash,
            app_version=app_version,
            device_model=device_model,
            system_version=system_version,
            lang_code=lang_code,
            ipv6=ipv6,
            proxy=proxy,
            test_mode=test_mode,
            bot_token=bot_token,
            session_string=session_string,
            in_memory=in_memory,
            phone_number=phone_number,
            phone_code=phone_code,
            password=password,
            workers=workers,
            workdir=workdir,
            plugins=plugins,
            parse_mode=parse_mode,
            no_updates=no_updates,
            takeout=takeout,
            sleep_threshold=sleep_threshold,
            hide_password=hide_password
        )

    def is_config_existing(self):
        if hasattr(self, '_config'):
            if hasattr(self, '_config_filename'):
                if os.path.exists(self._config_filename):
                    return 'Alles ist gut.'
                else:
                    json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'))
                    log.warning(f'[{self.name}] Client\'s config file at "{self._config_filename}" was not found,'
                                f'creating a new one.')

            else:
                if os.path.exists(self.DEFAULT_CONFIG_FILENAME):
                    counter = 0
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                    while os.path.exists(self._config_filename):
                        self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                        counter += 1
                else:
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME
                json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'))
                log.warning(f'[{self.name}] Client\'s config filename was not set, '
                            f'default filename "{self._config_filename}" was used, config file was saved.')
        else:
            if hasattr(self, '_config_filename'):
                if os.path.exists(self._config_filename):
                    try:
                        self._config = json.load(open(self._config_filename, 'r', encoding='utf8'))
                    except Exception as e:
                        counter = 0
                        new_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                        while os.path.exists(new_filename):
                            new_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                            counter += 1
                        self._config = self.DEFAULT_CONFIG.copy()
                        json.dump(self._config, open(new_filename, 'w', encoding='utf8'))

                        log.error(
                            f'[{self.name}] While opening client\'s config file at "{self._config_filename}" '
                            f'error was raised. Config was reset to default values and saved at "{new_filename}". '
                            'Error:',
                            e
                        )
                        self._config_filename = new_filename
                    else:
                        log.warning(
                            f'[{self.name}] Client\' config was restored from file at "{self._config_filename}".'
                        )
                else:
                    self._config = self.DEFAULT_CONFIG.copy()
                    json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'))
                    log.error(f'[{self.name}] Client\'s config was not found, '
                              f'config file at "{self._config_filename}" was not found. '
                              f'Config was reset to default values and saved at "{self._config_filename}".'
                              )
            else:
                if os.path.exists(self.DEFAULT_CONFIG_FILENAME):
                    counter = 0
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                    while os.path.exists(self._config_filename):
                        self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                        counter += 1
                else:
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME
                json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'
                                             ))
                log.error(f'[{self.name}] Client\'s config was not found, '
                          f'config filename was not set. '
                          f'Config was reset to default values and saved at "{self._config_filename}".'
                          )

    def get_config_parameter(self, param, default=None):
        try:
            self._config = json.loads(
                open(
                    self._config_filename, 'r', encoding='utf8'
                ).read().encode().decode('utf-8-sig')
            )
        except Exception as e:
            log.error('App\'s config file was not reloaded, error was raised', exc_info=e)
        self.is_config_existing()
        if param in self._config:
            return self._config[param]
        return default

    def set_config_parameter(self, param, value):
        self.is_config_existing()
        if param in self._config:
            self._config[param] = value

    def load_plugins(self):
        self.install_module('core.handlers')
        if self.plugins:
            plugins = self.plugins.copy()

            for option in ["include", "exclude"]:
                if plugins.get(option, []):
                    plugins[option] = [
                        (i.split()[0], i.split()[1:] or None)
                        for i in self.plugins[option]
                    ]
        else:
            return

        if plugins.get("enabled", True):
            root = plugins["root"]
            include = plugins.get("include", [])
            exclude = plugins.get("exclude", [])

            count = 0

            if not include:
                for path in sorted(Path(root.replace(".", "/")).rglob("*.py")):
                    module_path = '.'.join(path.parent.parts + (path.stem,))
                    try:
                        self.install_module(module_path, module_id=path.stem)
                    except ImportError:
                        log.warning('[%s] [LOAD] Ignoring non-existent module "%s"', self.name, module_path)
                    else:
                        count += 1
            else:
                for path, handlers in include:
                    module_path = root + "." + path
                    self.install_module(module_path, handlers, module_id=path)
                    count += 1

            if exclude:
                for path, handlers in exclude:
                    try:
                        self.uninstall_module(path, handlers)
                    except KeyError:
                        log.warning('[%s] [UNLOAD] Ignoring non-existent module "%s"', self.name, path)
            if count > 0:
                log.info('[{}] Successfully loaded {} plugin{} from "{}"'.format(
                    self.name, count, "s" if count > 1 else "", root))
            else:
                log.warning('[%s] No plugin loaded from "%s"', self.name, root)

    async def terminate(
        self: "Peluserbot",
    ):
        """Terminate the client by shutting down workers.

        This method does the opposite of :meth:`~pyrogram.Client.initialize`.
        It will stop the dispatcher and shut down updates and download workers.

        Raises:
            ConnectionError: In case you try to terminate a client that is already terminated.
        """
        if not self.is_initialized:
            raise ConnectionError("Client is already terminated")

        if self.takeout_id:
            await self.invoke(raw.functions.account.FinishTakeoutSession())
            log.info("Takeout session %s finished", self.takeout_id)

        await self.storage.save()
        await self.dispatcher.stop()
        self.modules = []

        for media_session in self.media_sessions.values():
            await media_session.stop()

        self.media_sessions.clear()

        self.updates_watchdog_event.set()

        if self.updates_watchdog_task is not None:
            await self.updates_watchdog_task

        self.updates_watchdog_event.clear()

        self.is_initialized = False

    def get_module(self, module_id):
        for module in self.modules:
            if module.module_id == module_id:
                return module
        else:
            raise KeyError('Module "{}" was not founded'.format(module_id))

    def get_module_by_handler(self, handler, group):
        for module in self.modules:
            for func in module.handlers:
                for func_handler, func_group in getattr(func, 'handlers', []):
                    if func_handler == handler and func_group == group:
                        return module
        else:
            return

    def get_all_handlers(self):
        for group in self.dispatcher.groups:
            for handler in self.dispatcher.groups[group]:
                yield handler, group

    def remove_module(self, module):
        self.modules.remove(module)

    def install_module(self, module_path, handlers=None, module_id=None):
        if module_id is None:
            module_id = module_path

        try:
            self.get_module(module_id)
        except KeyError:
            pass
        else:
            return

        warn_non_existent_functions = True

        module = importlib.import_module(module_path)

        if handlers is None:
            handlers = vars(module).keys()
            warn_non_existent_functions = False

        added_handlers = []
        for name in handlers:
            # noinspection PyBroadException
            try:
                for handler, group in getattr(module, name).handlers:
                    if isinstance(handler, Handler) and isinstance(group, int):
                        self.add_handler(handler, group)
                        handler.module_id = module_id

                        log.info('[{}] [LOAD] {}("{}") in group {} from "{}"'.format(
                            self.name, type(handler).__name__, name, group, module_path))
                added_handlers.append(getattr(module, name))

            except Exception:
                if warn_non_existent_functions:
                    log.warning('[{}] [LOAD] Ignoring non-existent function "{}" from "{}"'.format(
                        self.name, name, module_path))

        for name, value in vars(module).items():
            if isinstance(value, Module) or name == '__module_info__' and isinstance(value, dict):
                if isinstance(value, Module):
                    module_object = value
                else:
                    module_object = Module.from_dict(value)
                break
        else:
            module_object = Module(
                module_id=module_id
            )

        module_object.init(self, module_id, added_handlers, module)

        self.modules.append(module_object)
        return module_object

    def uninstall_module(self, module_id, handlers=()):
        """Uninstalls module with `module_id` id.
        Can uninstall list of handlers that in `handlers` (maybe)
        Returns what handlers were uninstalled and what were not
        :param module_id: `str` - module's id
        :param handlers: `list[str]` - list of handlers to uninstall
        :return: `dict`
        """

        warn_non_existent_functions = True

        module = self.get_module(module_id)

        if handlers is None:
            warn_non_existent_functions = False
        removed_handlers = []
        not_removed_handlers = {}
        for func in module.handlers:
            try:
                for handler, group in func.handlers:
                    if isinstance(handler, Handler) and isinstance(group, int):
                        self.remove_handler(handler, group)
                        removed_handlers.append(func.__name__)

                        log.info('[{}] [UNLOAD] {} from group {} in "{}"'.format(
                            self.name, type(handler).__name__, group, module_id))

            except Exception as e:
                if warn_non_existent_functions:
                    log.warning('[{}] [UNLOAD] Ignoring non-existent function "{}" from "{}"'.format(
                        self.name, func.__name__, module_id))
                not_removed_handlers[func.__name__] = e

        self.remove_module(module)
        return {
            'uninstalled': removed_handlers,
            'not_uninstalled_handlers': not_removed_handlers
        }

    @staticmethod
    def reload_module(module_path):
        module = importlib.import_module(module_path)
        for var in list(vars(module)):
            if var.startswith('__') and var.endswith('__'):
                continue
            delattr(module, var)

        module = importlib.reload(importlib.import_module(module_path))
        return module

    def get_string(self, string_id, default=None, lang_code=None, _module_id=None, **format_kwargs):
        try:
            module = self.get_module(_module_id)
        except KeyError as e:
            return print(e)

        return module.get_string(string_id, default=default, lang_code=lang_code, **format_kwargs)

    def get_string_form(self, string_id, value, default=None, lang_code=None, _module_id=None, **format_kwargs):
        try:
            module = self.get_module(_module_id)
        except KeyError as e:
            return print(e)
        return module.get_string_form(string_id, value, default=default, lang_code=lang_code, **format_kwargs)

    def get_core_string(self, string_id, default=None, lang_code=None, **format_kwargs):
        return self.get_string(string_id, default, lang_code, _module_id='core.handlers', **format_kwargs)

    def get_core_string_form(self, string_id, value, default=None, lang_code=None, **format_kwargs):
        return self.get_string_form(string_id, value, default, lang_code, _module_id='core.handlers', **format_kwargs)

    old_send_message = Client.send_message

    async def send_message(
            self: "Peluserbot",
            chat_id: Union[int, str],
            text: str,
            parse_mode: Optional["enums.ParseMode"] = None,
            entities: List["types.MessageEntity"] = None,
            disable_web_page_preview: bool = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            schedule_date: datetime = None,
            protect_content: bool = None,
            reply_markup: Union[
                "types.InlineKeyboardMarkup",
                "types.ReplyKeyboardMarkup",
                "types.ReplyKeyboardRemove",
                "types.ForceReply"
            ] = None

    ) -> "types.Message":
        message_prefix = self.get_config_parameter('message_prefix', str())
        if message_prefix:
            text = message_prefix + text
        return await self.old_send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            schedule_date=schedule_date,
            protect_content=protect_content,
            reply_markup=reply_markup
        )

    old_edit_message_text = Client.edit_message_text

    async def edit_message_text(
            self: "Peluserbot",
            chat_id: Union[int, str],
            message_id: int,
            text: str,
            parse_mode: Optional["enums.ParseMode"] = None,
            entities: List["types.MessageEntity"] = None,
            disable_web_page_preview: bool = None,
            reply_markup: "types.InlineKeyboardMarkup" = None
    ) -> "types.Message":
        message_prefix = self.get_config_parameter('message_prefix', str())
        if message_prefix and not text.startswith(message_prefix):
            text = message_prefix + text

        return await self.old_edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup
        )
