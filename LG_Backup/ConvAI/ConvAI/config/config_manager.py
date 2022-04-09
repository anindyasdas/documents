import os.path
import importlib
import threading
from configparser import ConfigParser
from kms_error import KMSError

lock = threading.Lock()
kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class ConfigManagerSingleton(type):
    """
    A class to make ConfigManager Singleton
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(ConfigManagerSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigManager(metaclass=ConfigManagerSingleton):
    """
    A class to read config file
    """
    def __init__(self):
        """
        Read select_app.ini to set the app and set the corresponding config file
        """
        try:
            # Select App
            select_app_path = os.path.join('config', 'select_app.ini')
            select_app_config = ConfigParser()
            select_app_config.read(select_app_path)

            # Setting app config
            self.app_name = select_app_config.get('app', 'name')

        except:
            logger.error("ConfigManager init exception")
            raise KMSError(31)

        app_path = 'apps/' + self.app_name

        if not os.path.exists(app_path):
            logger.warning("No App path " + app_path + ", name: " + self.app_name + "! Use test app as default")
            self.app_name = 'test' # Use test as default
        else:
            logger.info("path: " + app_path + ", name: " + self.app_name)

        logger.info("path: " + app_path + ", name: " + self.app_name)
        self.app_path = 'apps/' + self.app_name
        self.config_file_name = 'config_' + self.app_name + '.ini'

        # Read config file
        config_path = os.path.join('config', self.config_file_name)
        logger.debug(f'{self.config_file_name} {config_path}')

        self.read_config = ConfigParser()
        ret = self.read_config.read(config_path)

        if not ret:
            raise KMSError(31)

    def get(self, index, key):
        """
        Get the config of the index and the key

        :param index: config index
        :param key: config key
        :return: config value
        :rtype: string
        """
        try:
            value = self.read_config.get(index, key)
            return value

        except:
            logger.error(f' No option {index}: {key}')
            raise KMSError(31)


