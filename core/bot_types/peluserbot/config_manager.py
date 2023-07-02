import os
import json
import logging

log = logging.getLogger(__name__)


class ConfigManager:
    name: str
    DEFAULT_CONFIG: dict
    DEFAULT_CONFIG_FILENAME: str
    _config: dict
    _config_filename: str

    def is_config_existing(self):
        if hasattr(self, '_config'):
            if hasattr(self, '_config_filename'):
                if os.path.exists(self._config_filename):
                    return 'Alles ist gut.'
                else:
                    json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'))
                    log.warning(f'[{self.name}] Client\'s config file at "{self._config_filename}" was not found,'
                                f'creating a new one.')

            else:
                if os.path.exists(self.DEFAULT_CONFIG_FILENAME):
                    counter = 0
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                    while os.path.exists(self._config_filename):
                        self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                        counter += 1
                else:
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME
                json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'))
                log.warning(f'[{self.name}] Client\'s config filename was not set, '
                            f'default filename "{self._config_filename}" was used, config file was saved.')
        else:
            if hasattr(self, '_config_filename'):
                if os.path.exists(self._config_filename):
                    try:
                        self._config = json.load(open(self._config_filename, 'r', encoding='utf8'))
                    except Exception as e:
                        counter = 0
                        new_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                        while os.path.exists(new_filename):
                            new_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                            counter += 1
                        self._config = self.DEFAULT_CONFIG.copy()
                        json.dump(self._config, open(new_filename, 'w', encoding='utf8'))

                        log.error(
                            f'[{self.name}] While opening client\'s config file at "{self._config_filename}" '
                            f'error was raised. Config was reset to default values and saved at "{new_filename}". '
                            'Error:',
                            e
                        )
                        self._config_filename = new_filename
                    else:
                        log.warning(
                            f'[{self.name}] Client\' config was restored from file at "{self._config_filename}".'
                        )
                else:
                    self._config = self.DEFAULT_CONFIG.copy()
                    json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'))
                    log.error(f'[{self.name}] Client\'s config was not found, '
                              f'config file at "{self._config_filename}" was not found. '
                              f'Config was reset to default values and saved at "{self._config_filename}".'
                              )
            else:
                if os.path.exists(self.DEFAULT_CONFIG_FILENAME):
                    counter = 0
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                    while os.path.exists(self._config_filename):
                        self._config_filename = self.DEFAULT_CONFIG_FILENAME[:-5] + str(counter) + '.json'
                        counter += 1
                else:
                    self._config_filename = self.DEFAULT_CONFIG_FILENAME
                json.dump(self._config, open(self._config_filename, 'w', encoding='utf8'
                                             ))
                log.error(f'[{self.name}] Client\'s config was not found, '
                          f'config filename was not set. '
                          f'Config was reset to default values and saved at "{self._config_filename}".'
                          )

    def get_config_parameter(self, param, default=None):
        try:
            self._config = json.loads(
                open(
                    self._config_filename, 'r', encoding='utf8'
                ).read().encode().decode('utf-8-sig')
            )
        except Exception as e:
            log.error('App\'s config file was not reloaded, error was raised', exc_info=e)
        self.is_config_existing()
        if param in self._config:
            return self._config[param]
        if default is None:
            return self.DEFAULT_CONFIG.get(param, None)
        return default

    def set_config_parameter(self, param, value):
        self.is_config_existing()
        if param in self._config:
            self._config[param] = value
            open(self._config_filename, 'w', encoding='utf8')\
                .write(json.dumps(self._config, ensure_ascii=False, indent=4))
