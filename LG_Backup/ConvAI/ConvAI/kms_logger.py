"""
reference : https://codereview.stackexchange.com/questions/233146/python-logging-wrapper
The refernce code is capsulized into the KMSLogger class.
"""

import logging
import sys
import logging.handlers
import threading

lock = threading.Lock()

LOG_FMT = '%(asctime)s — %(message)s — %(name)s — %(funcName)s:%(lineno)d — %(levelname)s'
DEFAULT_LOG_LEVEL = logging.DEBUG


class KMSLoggerSingleton(type):
    """
    A class to make KMSLogger Singleton
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(KMSLoggerSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class KMSLogger(metaclass=KMSLoggerSingleton):
    @staticmethod
    def logger_factory(name, handlers_list, format, level):
        """
        wrapping logger logger factory

        :param name: logger name
        :param handlers_list: logger name
        :param format: log format. default LOG_FMT
        :param level: ERROR, WARNING, INFO, DEBUG
        :returns: logger
        :rtype: Logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if not isinstance(handlers_list, (list, tuple)):
            handlers_list = [handlers_list]
        for handler in handlers_list:
            handler.setFormatter(logging.Formatter(format))
            logger.addHandler(handler)

        return logger

    def create_console_logger(self, name, format=LOG_FMT, level=DEFAULT_LOG_LEVEL):
        """
        Creates console logger
        :returns: console logger
        :rtype: Logger
        """
        return self.logger_factory(name, handlers_list=[logging.StreamHandler(sys.stdout)],
                format=format, level=level)

    def create_file_logger(self, name, log_file="execution.log", format=LOG_FMT, level=DEFAULT_LOG_LEVEL):
        """
        Creates file logger
        :return: file logger
        :rtype: Logger
        """
        return self.logger_factory(name, handlers_list=[logging.FileHandler(log_file)],
                format=format, level=level)

    def create_rotating_file_logger(self, name, log_file="out.log", max_log_bytes=2000000, max_log_backup_files=20,
                format=LOG_FMT, level=DEFAULT_LOG_LEVEL):
        """ Creates rotating file logger with the given file name, max_log_bytes, max_log_backup_files and format.
         :param log_file: log file name
         :param max_log_bytes: the maximum size of file in Bytes
         :param max_log_backup_files: the number of backup files to store
         :param format: custom format as logging.Formatter object
         :param level: logging level
         :return: logging.Logger
        """
        handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_log_bytes, backupCount=max_log_backup_files)
        return self.logger_factory(name, handlers_list=[handler],
                format=format, level=level)

    def create_file_console_logger(self, name, log_file="execution.log", format=LOG_FMT, level=DEFAULT_LOG_LEVEL):
        """
        Creates file and console logger
        :return: file and console logger
        :rtype: Logger
        """
        handlers = [logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)]
        return self.logger_factory(name, handlers_list=handlers, format=format, level=level)


if __name__ == "__main__":
    # To get a console handler, run this code
    console_logger = KMSLogger().create_console_logger(name="logger1")
    console_logger.debug("Hello World")

    # To get a file logger, run this code
    file_logger = KMSLogger().create_file_logger(name="logger3", log_file="out.log")
    file_logger.critical("This is a critical message")

    # To get a console and file logger, run this code
    console_file_logger = KMSLogger().create_file_console_logger(name="my_logging2", log_file="out3.log")
    console_file_logger.error("Error: This is from console file logger")

