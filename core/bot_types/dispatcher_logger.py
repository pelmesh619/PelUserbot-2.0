import datetime
import json
import logging
import os


class UpdateLoggerHandler(logging.Handler):
    def __init__(self, dispatcher, route):
        super().__init__()
        self.dispatcher = dispatcher
        self.route = route

    def emit(self, record):
        app = self.dispatcher.client
        directory = app.get_log_directory(self.route)

        today = datetime.date.today()
        file_name = f'{self.route}_log_{today.year}_{str(today.month).zfill(2)}_{str(today.day).zfill(2)}.json'
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
            'message': record.getMessage(),

            'module_id': record.__dict__['module_id'],
            'handler': record.__dict__['handler'],
            'update_type': record.__dict__['update_type'],
            'update': record.__dict__['update'],
        }

        log_content.append(log_record)
        file = open(file_path, 'w', encoding='utf8')
        log_content = json.dumps(log_content, indent=4, ensure_ascii=False)
        # print(log_record)
        file.write(log_content)
        file.close()


class GeneralLoggerHandler(logging.Handler):
    def __init__(self, dispatcher, route):
        super().__init__()
        self.dispatcher = dispatcher
        self.route = route

    def emit(self, record):
        app = self.dispatcher.client
        directory = app.get_log_directory(self.route)

        today = datetime.date.today()
        file_name = f'{self.route}_log_{today.year}_{str(today.month).zfill(2)}_{str(today.day).zfill(2)}.log'
        file_path = os.path.join(directory, file_name)
        if not os.path.exists(file_path):
            open(file_path, 'w', encoding='utf8')

        file = open(file_path, 'a', encoding='utf8')
        file.write(self.format(record) + '\n')
        file.close()
