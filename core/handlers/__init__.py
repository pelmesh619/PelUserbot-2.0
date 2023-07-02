import os
import logging
import importlib
import re

from core import Module, Author, ModuleDatabase


module_info = Module(
    module_id='core.handlers',
    name='string_id=core_module_name',
    description='string_id=description',
    authors=Author('pelmeshke', telegram_username='pelmeshke', job='string_id=author_creator'),
    version='v0.1.0-alpha',
    release_date='01-01-1970',
    strings={},
    strings_source_filename='core_strings.json',
    config={},
    requirements=[],
    changelog={
        "v0.1.0-alpha": 'string_id=changelog_v0.1.0-alpha'
    },
    database_schema='CREATE TABLE IF NOT EXISTS user_states (\n'
                    'id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
                    'chat_id BIGINT,\n'
                    'user_id BIGINT,\n'
                    'module_id TEXT,\n'
                    'state_id TEXT\n'
                    ');'
)


def is_var_special(name):
    return name.startswith('__') and name.endswith('__')


def reload_variables():
    directory = os.path.join(*os.path.split(__file__)[:-1])
    for filename in os.listdir(directory):
        filename = str(filename)
        if (filename.endswith('.py') or not re.search(r'\.\w+$', filename)) and not is_var_special(filename[:-3]):
            #print(filename)
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


reload_variables()
