from .attribute import Attribute
from .bot_object import BotObject


class fuck(BotObject):
    pass


class Author(fuck):
    attributes = [
        Attribute('name', str),
        Attribute('link', str, None),
        Attribute('telegram_username', str, None),
        Attribute('job', str, None),
    ]

    name: str
    link: str
    telegram_username: str
    job: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


pelmeshke = Author('pelmeshke', telegram_username='pelmeshke')
