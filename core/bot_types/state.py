from pyrogram.types import Message, CallbackQuery
from pyrogram import filters

from .attribute import Attribute
from .bot_object import BotObject
from . import Module


class State(BotObject):
    attributes = [
        Attribute('state_id', str)
    ]
    state_id: str
    module: Module

    @property
    def unique_id(self):
        return self.module.module_id, self.state_id

    @property
    def filter(self):
        async def f(_, app, update):
            if isinstance(update, CallbackQuery):
                update = update.message

            if isinstance(update, Message):
                user_id = update.from_user
                if not user_id:
                    return
                else:
                    user_id = user_id.id

                chat_id = update.chat.id
            else:
                return

            state = app.get_state(chat_id, user_id)
            if not state:
                return
            if state.unique_id == self.unique_id:
                return True

            return

        return filters.create(f)



