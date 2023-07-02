import asyncio
import os
import logging
import json
import time
from collections import OrderedDict
from concurrent.futures.thread import ThreadPoolExecutor

import pyrogram
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, List, Callable

from pyrogram import enums, types, raw
from pyrogram.client import Client, Cache
from pyrogram.filters import Filter
from pyrogram.methods import Methods
from pyrogram.parser import Parser
from pyrogram.session import Session
from pyrogram.session.internals import MsgId
from pyrogram.storage import MemoryStorage, FileStorage
from pyrogram.types import User

from .config_manager import ConfigManager
from .module_manager import ModuleManager
from core.bot_types.peldispatcher import Peldispatcher
from core.bot_types.error_handler import ErrorHandler

log = logging.getLogger(__name__)


class Peluserbot(Client, ConfigManager, ModuleManager):
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
    MAX_CONCURRENT_TRANSMISSIONS = 1

    MODULE_CONFIGS_DIRECTORY = 'module_configs'
    RESOURCES_DIRECTORY = 'resources'
    DOWNLOADS_DIRECTORY = 'downloads'
    DATABASE_DIRECTORY = 'database'
    LOGS_DIRECTORY = 'logs'
    DEFAULT_CONFIG = {
        'module_configs_directory': MODULE_CONFIGS_DIRECTORY,
        'resources_directory': RESOURCES_DIRECTORY,
        'downloads_directory': DOWNLOADS_DIRECTORY,
        'database_directory': DATABASE_DIRECTORY,
        'logs_directory': LOGS_DIRECTORY,
        'will_error_message_send': True,
        'replace_string_from_other_languages': True,
        'message_prefix': '',
        'command_prefix': '/',
        'debug': True
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
            max_concurrent_transmissions: int = MAX_CONCURRENT_TRANSMISSIONS,
            config_filename: str = None
    ):
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
            'database_directory',
            'logs_directory',
        ]:
            if not os.path.exists(self.get_config_parameter(directory)):
                os.mkdir(self.get_config_parameter(directory))

        self.modules = []
        self.answers = {}
        self.error_handlers = OrderedDict()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

        self.get_string_calls = 0
        self.handlers_activated = 0
        self.handlers_handled = 0
        self.handlers_crushed = 0
        self.starting_time = time.time()
        self.last_restart_time = self.starting_time

        Methods.__init__(self)

        self.name = name
        self.api_id = int(api_id) if api_id else None
        self.api_hash = api_hash
        self.app_version = app_version
        self.device_model = device_model
        self.system_version = system_version
        self.lang_code = lang_code.lower()
        self.ipv6 = ipv6
        self.proxy = proxy
        self.test_mode = test_mode
        self.bot_token = bot_token
        self.session_string = session_string
        self.in_memory = in_memory
        self.phone_number = phone_number
        self.phone_code = phone_code
        self.password = password
        self.workers = workers
        self.workdir = Path(workdir)
        self.plugins = plugins
        self.parse_mode = parse_mode
        self.no_updates = no_updates
        self.takeout = takeout
        self.sleep_threshold = sleep_threshold
        self.hide_password = hide_password
        self.max_concurrent_transmissions = max_concurrent_transmissions

        self.executor = ThreadPoolExecutor(self.workers, thread_name_prefix="Handler")

        if self.session_string:
            self.storage = MemoryStorage(self.name, self.session_string)
        elif self.in_memory:
            self.storage = MemoryStorage(self.name)
        else:
            self.storage = FileStorage(self.name, self.workdir)

        self.dispatcher = Peldispatcher(self)

        self.rnd_id = MsgId

        self.parser = Parser(self)

        self.session = None

        self.media_sessions = {}
        self.media_sessions_lock = asyncio.Lock()

        self.save_file_semaphore = asyncio.Semaphore(self.max_concurrent_transmissions)
        self.get_file_semaphore = asyncio.Semaphore(self.max_concurrent_transmissions)

        self.is_connected = None
        self.is_initialized = None

        self.takeout_id = None

        self.disconnect_handler = None

        self.me: Optional[User] = None

        self.message_cache = Cache(10000)

        # Sometimes, for some reason, the server will stop sending updates and will only respond to pings.
        # This watchdog will invoke updates.GetState in order to wake up the server and enable it sending updates again
        # after some idle time has been detected.
        self.updates_watchdog_task = None
        self.updates_watchdog_event = asyncio.Event()
        self.last_update_time = datetime.now()

        self.loop = asyncio.get_event_loop()

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

    def get_all_handlers(self):
        for group in self.dispatcher.groups:
            for handler in self.dispatcher.groups[group]:
                yield handler, group

    def get_command_prefixes(self):
        return self.get_config_parameter('command_prefixes', None) or ('/',)

    def get_command_prefix(self):
        return self.get_command_prefixes()[0]

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

    def set_state(self, chat_id, state, user_id=None):
        if not user_id:
            user_id = chat_id

        core_module = self.get_module('core.handlers')
        user_note = core_module.database.execute_and_fetch(
            f'SELECT * FROM user_states WHERE user_id = {user_id} AND chat_id = {chat_id}'
        )
        if user_note:
            core_module.database.execute(
                f'UPDATE user_states SET state_id = \'{state.state_id}\', module_id = \'{state.module.module_id}\''
                f'WHERE user_id = {user_id} AND chat_id = {chat_id}'
            )
        else:
            core_module.database.execute(
                f'INSERT INTO user_states (chat_id, user_id, module_id, state_id)'
                f'VALUES ({chat_id}, {user_id}, \'{state.module.module_id}\', \'{state.state_id}\')'
            )

    def get_state(self, chat_id, user_id=None):
        if not user_id:
            user_id = chat_id

        core_module = self.get_module('core.handlers')
        user_note = core_module.database.execute_and_fetch(
            f'SELECT * FROM user_states WHERE user_id = {user_id} AND chat_id = {chat_id}'
        )
        if user_note:
            module_id = user_note[0][3]
            state_id = user_note[0][4]

            module = self.get_module(module_id)
            if not module:
                return

            state = module.get_state_by_id(state_id)

            return state
        else:
            return None

    def remove_state(self, chat_id, user_id=None):
        if not user_id:
            user_id = chat_id

        core_module = self.get_module('core.handlers')
        user_note = core_module.database.execute_and_fetch(
            f'SELECT * FROM user_states WHERE user_id = {user_id} AND chat_id = {chat_id}'
        )
        if user_note:
            core_module.database.execute(
                f'DELETE FROM user_states WHERE user_id = {user_id} AND chat_id = {chat_id};'
            )

    def add_error_handler(self, handler, group=0):
        if group not in self.error_handlers:
            self.error_handlers[group] = []
            self.error_handlers = OrderedDict(sorted(self.error_handlers.items()))

        self.error_handlers[group].append(handler)

    def on_error(
            self=None,
            filters=None,
            group: int = 0
    ) -> Callable:
        """Decorator for handling errors that was raised while executing other handlers.

        This does the same thing as :meth:`~pyrogram.Client.add_handler` using the
        :obj:`~pyrogram.handlers.ErrorHandler`.

        Parameters:
            filters (:obj:`~pyrogram.filters`, *optional*):
                Pass one or more filters to allow only a subset of messages to be passed
                in your function.

            group (``int``, *optional*):
                The group identifier, defaults to 0.
        """

        # noinspection PyUnresolvedReferences
        def decorator(func: Callable) -> Callable:
            if isinstance(self, pyrogram.Client):
                self.add_error_handler(ErrorHandler(func, filters), group)
            elif isinstance(self, Filter) or self is None:
                if not hasattr(func, "handlers"):
                    func.handlers = []

                func.handlers.append(
                    (
                        ErrorHandler(func, self),
                        group if filters is None else filters
                    )
                )

            return func

        return decorator
