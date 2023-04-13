import os
import sqlite3
import logging

from .attribute import Attribute
from .bot_object import BotObject


class ModuleDatabase(BotObject):
    attributes = [
        Attribute('schema', str)
    ]
    schema: str
    module_id: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None

    def init(self, module):
        self.module_id = module.module_id
        try:
            self.connection = sqlite3.connect(
                os.path.join(module.app.get_config_parameter('database_directory'), f'{self.module_id}.sqlite3'),
                check_same_thread=False
            )
        except Exception as e:
            logging.error(f'Module\'s database of `{self.module_id}` was not connected', exc_info=e)
            return

        self.execute(self.schema)

    def execute(self, sql):
        cur = self.connection.cursor()
        try:
            cur.executescript(sql)
            self.connection.commit()
        except Exception as e:
            logging.error(f'Error while executing `{sql}` in database of module `{self.module_id}`', exc_info=e)
            cur.close()
            return e

        cur.close()
        return True

    def execute_and_fetch(self, sql):
        cur = self.connection.cursor()
        try:
            cur.execute(sql)
        except Exception as e:
            logging.error(f'Error while executing `{sql}` in database of module `{self.module_id}`', exc_info=e)
            cur.close()
            return e

        result = cur.fetchall()
        cur.close()
        return result

