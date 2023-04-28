import os
import logging
import importlib
import re

from .bot_object import BotObject
from .peluserbot import Peluserbot
from .module import Module
from .author import Author, pelmeshke
from .command import Command
from .module_strings import ModuleStrings
from .module_database import ModuleDatabase
from .filters import *
from .state import State

__version__ = '2.0.0-alpha1'

log = logging.Logger(__name__)


def is_var_special(name: str):
    return name.startswith('__') and name.endswith('__')


def reload_variables():
    directory = os.path.join(*os.path.split(__file__)[:-1])
    for filename in os.listdir(directory):
        filename = str(filename)
        if (filename.endswith('.py') or not re.search(r'\.\w+$', filename)) and not is_var_special(filename[:-3]):
            # print(filename)
            module_name = re.sub('\.py$', '', filename)
            try:
                module = importlib.import_module(__name__ + '.' + module_name)
            except Exception as e:
                logging.error(f'\nModule {filename} did not connected. Error:', exc_info=e)
            else:
                try:
                    for i in list(vars(module)):
                        if not is_var_special(i):
                            delattr(module, i)
                    module = importlib.import_module(__name__ + '.' + module_name)
                    module = importlib.reload(module)
                except Exception as e:
                    logging.error(f'\nModule {filename} has not reloaded. Cached version of the module will '
                                  f'be used instead. Error:', exc_info=e)
                    module = importlib.import_module(__name__ + '.' + re.sub('\.py$', '', filename))
                finally:
                    if getattr(module, 'reload_variables', False):
                        module.reload_variables()
                    variables = {k: v for k, v in vars(module).items() if not is_var_special(k)}
                    globals().update(variables)
