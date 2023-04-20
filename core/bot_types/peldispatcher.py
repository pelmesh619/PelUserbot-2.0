import inspect
import logging

import pyrogram
from pyrogram.handlers.handler import Handler
from pyrogram.types import Message, CallbackQuery, InlineQuery
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers import RawUpdateHandler

log = logging.getLogger(__name__)


class Peldispatcher(Dispatcher):
    async def handler_worker(self, lock):
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
                            if isinstance(parsed_update, (Message, CallbackQuery, InlineQuery)):
                                lang_code = None
                                if self.client.me.is_bot:
                                    user = getattr(parsed_update, 'from_user', None)
                                    lang_code = getattr(user, 'language_code', None)
                                if lang_code is None:
                                    lang_code = self.client.lang_code

                                module = self.client.get_module(getattr(handler, 'module_id', None))
                                if module:
                                    parsed_update.get_string = module.get_strings_by_lang_code(lang_code)
                                    parsed_update.get_string_form = parsed_update.get_string.get_string_form

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
                                        await send_error_message(self, args[0], e, handler, module)

                                log.exception(e)
                                self.client.handlers_crushed += 1
                            else:
                                self.client.handlers_handled += 1

                            break
            except pyrogram.StopPropagation:
                pass
            except Exception as e:
                log.exception(e)






async def send_error_message(
        dispatcher: Peldispatcher,
        message: Message,
        error: Exception,
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
        dispatcher.client.get_string(
            'error_raised_while_handler_was_proceed' +
            ('_in_module' if module else ''),
            error=repr(error),
            func=handler.callback.__name__,
            module_name=module_name,
            _module_id='core.handlers'
        )
    )
