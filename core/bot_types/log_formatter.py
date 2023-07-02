import logging
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
        record.levelname = self.module.app.get_core_string('logging_level_'+record.levelname, default=record.levelname)

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
