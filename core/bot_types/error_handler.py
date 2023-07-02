from typing import Callable

from pyrogram.handlers.handler import Handler


class ErrorHandler(Handler):
    def __init__(self, callback: Callable, filters=None):
        super().__init__(callback, filters)

