import os
import logging
import importlib

from .time_utils import *
from .text_utils import *


def is_var_special(name):
    return name.startswith('__') and name.endswith('__')


directory = os.path.join(*os.path.split(__file__)[:-1])
for filename in os.listdir(directory):
    if filename.endswith('.py') and not is_var_special(filename[:-3]):
        # print(filename)
        try:
            module = importlib.import_module(__name__ + '.' + filename[:-3])

        except Exception as e:
            logging.error(f'\nModule {filename} did not connected. Error:', exc_info=e)
        else:
            try:
                module = importlib.reload(module)
            except Exception as e:
                logging.error(f'\nModule {filename} has not reloaded. Cached version of the module will '
                              f'be used instead. Error:', exc_info=e)
            variables = {k: v for k, v in vars(module).items() if not is_var_special(k)}
            globals().update(variables)
