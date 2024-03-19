import datetime
import json
import logging
import os
import re


class LocalizedFormatter(logging.Formatter):
    def __init__(self, module, fmt=None, datefmt=None, style='%', validate=True, *, defaults=None):
        self.module = module
        self._defaults = defaults
        super().__init__(fmt, datefmt, style, validate)

    def format(self, record: logging.LogRecord):
        # defaults do not exist in logging.Formatter on Python<3.10
        if self._defaults:
            record.__dict__ = {**self._defaults, **record.__dict__}

        if re.search(r'^string_id=([\w\-_.]+)', str(record.msg)):
            record.msg = self.module.get_string(re.search(r'^string_id=([\w\-_.]+)', str(record.msg)).group(1))
        record.levelname = self.module.app.get_core_string('logging_level_' + record.levelname,
                                                           default=record.levelname)

        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        return s


class LoggerHandler(logging.Handler):
    def __init__(self, dispatcher, route):
        super().__init__()
        self.dispatcher = dispatcher
        self.route = route

    def emit(self, record):
        app = self.dispatcher.client
        directory = app.get_config_parameter('logs_directory')
        if not os.path.exists(directory):
            os.mkdir(directory)

        directory = os.path.join(directory, self.route)
        if not os.path.exists(directory):
            os.mkdir(directory)

        today = datetime.date.today()
        file_name = f'{self.route}_{today.year}_{str(today.month).zfill(2)}_{str(today.day).zfill(2)}.json'
        file_path = os.path.join(directory, file_name)
        if not os.path.exists(file_path):
            open(file_path, 'w', encoding='utf8')

        file = open(file_path, 'r', encoding='utf8')
        log_content = json.loads(file.read() or '[]')
        file.close()
        if not isinstance(log_content, list):
            log_content = [log_content]
        log_record = {
            'logger_name': record.name,
            'level': record.levelname,
            'levelno': record.levelno,
            'timestamp': record.created,

            'module_id': record.__dict__['module_id'],
            'handler': record.__dict__['handler'],
            'update_type': record.__dict__['update_type'],
            'update': record.__dict__['update'],
        }
        log_content.append(log_record)
        file = open(file_path, 'w', encoding='utf8')
        log_content = json.dumps(log_content, indent=4, ensure_ascii=False)
        print(log_record)
        file.write(log_content)
        file.close()
