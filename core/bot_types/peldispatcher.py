import asyncio
import html
import inspect
import json
import logging
import re
import sys
import time
from datetime import datetime
from enum import Enum

import pyrogram
from pyrogram.handlers.handler import Handler
from pyrogram.types import Message, CallbackQuery, InlineQuery
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers import RawUpdateHandler

from core.bot_types.module_strings import ModuleStrings
from core.bot_types.error_handler import ErrorHandler
from core.bot_types.dispatcher_logger import GeneralLoggerHandler, UpdateLoggerHandler
from core.handlers.blacklist_middleware import blacklist_middleware
from utils import format_traceback

log = logging.getLogger(__name__)


def default(obj):
    if isinstance(obj, bytes):
        return repr(obj)
    if isinstance(obj, (str, int, bool, float)) or obj is None:
        return obj

    if isinstance(obj, re.Match):
        return repr(obj)

    if isinstance(obj, Enum):
        return str(obj)

    if isinstance(obj, datetime):
        return str(obj)

    if isinstance(obj, ModuleStrings):
        return repr(ModuleStrings)

    if isinstance(obj, pyrogram.types.Chat):
        attrs = ['id', 'type', 'title', 'first_name', 'last_name', 'username']
    elif isinstance(obj, pyrogram.types.User):
        attrs = ['id', 'first_name', 'last_name', 'username', 'is_bot', 'is_deleted']
    elif isinstance(obj, pyrogram.types.Message):
        attrs = ['id', 'text', 'caption', 'date', 'from_user', 'chat', 'service', 'media']
    else:
        attrs = filter(lambda x: not x.startswith("_"), obj.__dict__)

    return {
        "_": obj.__class__.__name__,
        **{
            attr: (
                "*" * 9 if attr == "phone_number" else
                getattr(obj, attr)
            )
            for attr in attrs if getattr(obj, attr, None) is not None
        }
    }


def filter_update(data):
    if isinstance(data, (tuple, set)):
        data = list(data)

    if not isinstance(data, (list, dict)):
        data = default(data)

    if isinstance(data, (str, int, bool, float)) or data is None:
        return data

    if isinstance(data, list):
        return [filter_update(i) for i in data]
    else:
        return {filter_update(i): filter_update(j) for i, j in data.items()}


class Peldispatcher(Dispatcher):
    def __init__(self, client: "core.bot_types.peluserbot.Peluserbot"):
        super().__init__(client)

        self.general_logger = logging.getLogger('dispatcher_general')
        handler = GeneralLoggerHandler(self, 'dispatcher_general')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(levelno)s %(name)s: %(message)s'))
        self.general_logger.addHandler(handler)
        self.general_logger.setLevel(logging.DEBUG)

        self.update_logger = logging.getLogger('dispatcher_updates')
        handler = UpdateLoggerHandler(self, 'dispatcher_updates')
        handler.setLevel(logging.DEBUG)
        self.update_logger.addHandler(handler)
        self.update_logger.setLevel(logging.DEBUG)

    async def start(self):
        if not self.client.no_updates:
            for i in range(self.client.workers):
                self.locks_list.append(asyncio.Lock())

                self.handler_worker_tasks.append(
                    self.loop.create_task(
                        self.handler_worker(self.locks_list[-1], is_for_core_handlers=True if i == 0 else False)
                    )
                )

            self.general_logger.info(f'Dispatcher is running with {self.client.workers} '
                                     f'handler worker{"s" if self.client.workers > 1 else ""}')
            print('Dispatcher is running')

    async def stop(self):
        if not self.client.no_updates:
            for i in range(self.client.workers):
                self.updates_queue.put_nowait(None)

            for i in self.handler_worker_tasks:
                await i

            self.handler_worker_tasks.clear()
            self.groups.clear()

            self.general_logger.info(f'Dispatcher was stopped with {self.client.workers} '
                                     f'handler worker{"s" if self.client.workers > 1 else ""}')

    def kill_process(self, index):
        task = self.handler_worker_tasks[index]

        task.cancel()
        lock = self.locks_list[index]
        del self.handler_worker_tasks[index]
        del self.locks_list[index]
        self.general_logger.info(f'Handler worker with lock id {id(lock)} and index {index} was killed')

        self.locks_list.append(asyncio.Lock())
        task = self.loop.create_task(
            self.handler_worker(self.locks_list[-1], is_for_core_handlers=True if index == 0 else False)
        )
        self.handler_worker_tasks.append(task)

    def kill_all_processes(self):
        count = 0
        for i in range(len(self.handler_worker_tasks)):
            task = self.handler_worker_tasks[i]
            lock = self.locks_list[i]
            if lock.locked():
                count += 1

            lock_id = id(lock)

            try:
                task.cancel()
                del task
                del lock
            except Exception as e:
                print(e)

            self.general_logger.info(f'Handler worker with lock id {lock_id} and index {i} was killed')

        self.handler_worker_tasks.clear()
        self.locks_list.clear()

        for i in range(self.client.workers):
            self.locks_list.append(asyncio.Lock())
            task = self.loop.create_task(
                self.handler_worker(self.locks_list[-1], is_for_core_handlers=True if i == 0 else False)
            )
            self.handler_worker_tasks.append(task)

        return count

    async def handler_worker(self, lock, is_for_core_handlers=False):
        self.general_logger.info(f'Handler worker with lock id {id(lock)} was started')
        while True:
            packet = await self.updates_queue.get()

            if packet is None:
                break

            try:
                update, users, chats = packet
                parser = self.update_parsers.get(type(update), None)

                parsed_update, handler_type = (
                    await parser(update, users, chats)
                    if parser is not None
                    else (None, type(None))
                )

                async with lock:
                    for group_number, group in self.groups.items():
                        for handler in group:
                            args = None

                            if isinstance(handler, handler_type):
                                try:
                                    if await handler.check(self.client, parsed_update):
                                        args = (parsed_update,)
                                except Exception as e:
                                    log.exception(e)
                                    continue

                            elif isinstance(handler, RawUpdateHandler):
                                args = (update, users, chats)

                            if args is None:
                                continue

                            module = None
                            if isinstance(parsed_update, (Message, CallbackQuery, InlineQuery)):
                                lang_code = None
                                if self.client.me.is_bot:
                                    user = getattr(parsed_update, 'from_user', None)
                                    lang_code = getattr(user, 'language_code', self.client.lang_code)
                                if lang_code is None:
                                    lang_code = self.client.lang_code

                                module = self.client.get_module(getattr(handler, 'module_id', None))
                                if module:
                                    parsed_update.get_string = module.get_strings_by_lang_code(lang_code)
                                    parsed_update.get_string_form = parsed_update.get_string.get_string_form
                                parsed_update._module = module
                                lock.module = module

                                if module and module.module_id != 'core.handlers' and is_for_core_handlers:
                                    continue

                            lock.handler_name = handler.callback.__name__
                            lock.start_time = time.time()
                            lock.update = parsed_update

                            if id(handler.callback) != id(blacklist_middleware):
                                self.update_logger.info(
                                    'New message',
                                    extra={
                                        'module_id': module.module_id if module else None,
                                        'handler': handler.callback.__name__,
                                        'update_type': args[0].__class__.__name__,
                                        # fix this
                                        'update': filter_update(args[0]),
                                    }
                                )

                            try:
                                self.client.handlers_activated += 1
                                if inspect.iscoroutinefunction(handler.callback):
                                    await handler.callback(self.client, *args)
                                else:
                                    await self.loop.run_in_executor(
                                        self.client.executor,
                                        handler.callback,
                                        self.client,
                                        *args
                                    )

                            except pyrogram.StopPropagation:
                                raise
                            except pyrogram.ContinuePropagation:
                                continue
                            except Exception as e:
                                if self.client.get_config_parameter('will_error_message_send'):
                                    if isinstance(args[0], Message):
                                        result = False
                                        if parsed_update._module and parsed_update._module.error_handlers:
                                            parsed_update.exc_info = sys.exc_info()
                                            parsed_update.exception = parsed_update.exc_info[1]
                                            result = await self.handle_error(parsed_update, module)

                                        if not result and self.client.error_handlers:
                                            parsed_update.exc_info = sys.exc_info()
                                            parsed_update.exception = parsed_update.exc_info[1]
                                            result = await self.handle_error(parsed_update)

                                        if not result:
                                            await send_error_message(self, args[0], sys.exc_info(), handler, module)

                                log.exception(e)
                                self.client.handlers_crushed += 1
                            else:
                                self.client.handlers_handled += 1

                            break
            except pyrogram.StopPropagation:
                pass
            except Exception as e:
                log.exception(e)
        self.general_logger.info(f'Handler worker with lock id {id(lock)} finished his execution')

    async def handle_error(self, update, module=None):
        if module is None:
            module = self.client
        try:
            for group in module.error_handlers:
                for handler in module.error_handlers[group]:
                    try:
                        assert isinstance(handler, ErrorHandler)
                        if not await handler.check(self.client, update):
                            continue
                    except AssertionError:
                        continue
                    except Exception as e:
                        log.exception(e)
                        continue

                    try:
                        self.client.handlers_activated += 1
                        if inspect.iscoroutinefunction(handler.callback):
                            await handler.callback(self.client, update)
                        else:
                            await self.loop.run_in_executor(
                                self.client.executor,
                                handler.callback,
                                self.client,
                                update
                            )

                    except pyrogram.StopPropagation:
                        raise
                    except pyrogram.ContinuePropagation:
                        continue
                    except Exception as e:
                        if self.client.get_config_parameter('will_error_message_send'):
                            if isinstance(update, Message):
                                await send_error_message(
                                    self, update,
                                    sys.exc_info(), handler,
                                    module if module != self.client else None
                                )
                        log.exception(e)
                        self.client.handlers_crushed += 1
                    else:
                        self.client.handlers_handled += 1

                    return True
        except pyrogram.StopPropagation:
            return True
        except Exception as e:
            log.exception(e)

        return False


async def send_error_message(
        dispatcher: Peldispatcher,
        message: Message,
        error: tuple,
        handler: Handler,
        module=None
):
    if message.chat and message.chat.type != pyrogram.enums.ChatType.CHANNEL:
        chat = message.chat.id
    else:
        chat = 'me'

    if module:
        module_name = module.full_name()
    else:
        module_name = None

    await dispatcher.client.send_message(
        chat,
        dispatcher.client.get_core_string(
            'error_raised_while_handler_was_proceed' +
            ('_in_module' if module else ''),
            error=html.escape(format_traceback(error, dispatcher.client)),
            func=handler.callback.__name__,
            module_name=module_name,
        )
    )
