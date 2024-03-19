import importlib
import logging

from pyrogram.handlers.handler import Handler

from core.bot_types.module import Module
from core.bot_types.error_handler import ErrorHandler

log = logging.getLogger(__name__)


class ModuleManager:
    name: str
    modules: list

    def add_handler(self, handler, group):
        pass

    def remove_handler(self, handler, group):
        pass

    def get_module(self, module_id):
        for module in self.modules:
            if module.module_id == module_id:
                return module
        else:
            return

    def get_module_by_handler(self, handler, group):
        for module in self.modules:
            for func in module.handlers:
                for func_handler, func_group in getattr(func, 'handlers', []):
                    if func_handler == handler and func_group == group:
                        return module
        else:
            return

    def remove_module(self, module):
        self.modules.remove(module)

    def install_module(self, module_path, handlers=None, module_id=None):
        if module_id is None:
            module_id = module_path

        module = self.get_module(module_id)
        if module:
            return

        warn_non_existent_functions = True

        module = importlib.import_module(module_path)

        if handlers is None:
            handlers = vars(module).keys()
            warn_non_existent_functions = False

        added_handlers = []
        error_handlers = []
        for name in handlers:
            # noinspection PyBroadException
            try:
                for handler, group in getattr(module, name).handlers:
                    if isinstance(handler, ErrorHandler) and isinstance(group, int):
                        error_handlers.append((handler, group))
                        handler.module_id = module_id

                        log.info('[{}] [LOAD] {}("{}") in group {} from "{}"'.format(
                            self.name, type(handler).__name__, name, group, module_path))
                    elif isinstance(handler, Handler) and isinstance(group, int):
                        self.add_handler(handler, group)
                        handler.module_id = module_id

                        log.info('[{}] [LOAD] {}("{}") in group {} from "{}"'.format(
                            self.name, type(handler).__name__, name, group, module_path))

                added_handlers.append(getattr(module, name))

            except Exception:
                if warn_non_existent_functions:
                    log.warning('[{}] [LOAD] Ignoring non-existent function "{}" from "{}"'.format(
                        self.name, name, module_path))

        for name, value in vars(module).items():
            if isinstance(value, Module) or name == '__module_info__' and isinstance(value, dict):
                if isinstance(value, Module):
                    module_object = value
                else:
                    module_object = Module.from_dict(value)
                break
        else:
            module_object = Module(
                module_id=module_id
            )

        module_object.init(self, module_id, added_handlers, module, error_handlers)

        self.modules.append(module_object)
        return module_object

    def uninstall_module(self, module_id, handlers=()):
        """Uninstalls module with `module_id` id.
        Can uninstall list of handlers that in `handlers` (maybe)
        Returns what handlers were uninstalled and what were not
        :param module_id: `str` - module's id
        :param handlers: `list[str]` - list of handlers to uninstall
        :return: `dict`
        """

        warn_non_existent_functions = True

        module = self.get_module(module_id)

        if handlers is None:
            warn_non_existent_functions = False
        removed_handlers = []
        not_removed_handlers = {}
        for func in module.handlers:
            try:
                for handler, group in func.handlers:
                    if isinstance(handler, Handler) and isinstance(group, int):
                        self.remove_handler(handler, group)
                        removed_handlers.append(func.__name__)

                        log.info('[{}] [UNLOAD] {} from group {} in "{}"'.format(
                            self.name, type(handler).__name__, group, module_id))

            except Exception as e:
                if warn_non_existent_functions:
                    log.warning('[{}] [UNLOAD] Ignoring non-existent function "{}" from "{}"'.format(
                        self.name, func.__name__, module_id))
                not_removed_handlers[func.__name__] = e

        if getattr(module.database, 'connection', False):
            module.database.connection.close()
        self.remove_module(module)
        return {
            'uninstalled': removed_handlers,
            'not_uninstalled_handlers': not_removed_handlers
        }

    @staticmethod
    def reload_module(module_path):
        module = importlib.import_module(module_path)
        for var in list(vars(module)):
            if var.startswith('__') and var.endswith('__'):
                continue
            delattr(module, var)

        module = importlib.reload(importlib.import_module(module_path))
        return module
