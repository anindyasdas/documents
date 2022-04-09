import threading
import schedule
import time
import importlib

from config.config_manager import ConfigManager

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class Scheduler(object):
    def __init__(self, kg_constructor):
        """
        Read update period config and Init update thread

        :param kg_constructor: knowledge constructor to update
        """
        logger.debug('Scheduler init')
        self.kg_constructor = kg_constructor
        logger.debug(ConfigManager().get('update_param', 'period'))
        self.update_period_min = int(ConfigManager().get('update_param', 'period'))
        logger.info("Checking period to update KG DB: " + str(self.update_period_min) + " minutes")
        if self.update_period_min != 0:
            thread = threading.Thread(target=self.update_task)
            thread.daemon = True
            thread.start()

    def update_task(self):
        """
        internal update for each update_period_min
        """
        logger.debug("ontology update thread start..")

        schedule.every(self.update_period_min).minutes.do(self.kg_constructor.load)

        while True:
            schedule.run_pending()
            time.sleep(1)


