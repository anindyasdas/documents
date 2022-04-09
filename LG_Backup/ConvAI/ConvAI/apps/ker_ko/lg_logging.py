# -------------------------------------------------
# Copyright(c) 2020 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler
import os
from .components.engine import constants

LOG_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/logs/'

# If we needed handle to the special logs, then do
#   special_log = []
#   spl_handler = SpecialHandler(special_log)  # Otherwise pass None and let it use the default log.
class SpecialHandler(logging.StreamHandler):
    # See the outputs here in this list if using SpecialHandler class
    _default_special_log = []

    def __init__(self, special_logs=None):
        if special_logs is None:
            # self.special_logs has the default static list
            self.special_logs = SpecialHandler._default_special_log
        else:
            self.special_logs = special_logs
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        msg = record.getMessage()
        self.special_logs.append(msg)

    # ToDo: Convert from windows path to native path.
    base_path_mapper = [
        ("knowledge_extraction", "logger"),
        ("components/engine", "similarity_mapper"),
        ("components/classifier", "classifier")
    ]
    base_path_mapper.sort(reverse=True)
    path_mapper = dict()

    @staticmethod
    def path_2_spl_module(record):
        directory = os.path.dirname(record.pathname)
        if directory in SpecialHandler.path_mapper:
            output = SpecialHandler.path_mapper[directory]
        else:
            for path, spl_module in SpecialHandler.base_path_mapper:
                if path in directory:
                    output = spl_module
                    break
            else:
                output = "common"
            SpecialHandler.path_mapper[directory] = output
        record.spl_module = output

    @staticmethod
    def format(record):
        return f"[{record.spl_module}] {record.msg}"

    @staticmethod
    def filter(record):
        SpecialHandler.path_2_spl_module(record)
        return (record.levelno == constants.LG_LOGGING_MODULE_OUTPUT_LVL
                or record.msg.startswith(constants.LG_LOGGING_MODULE_OUTPUT_KEY))

    @staticmethod
    def set_default_logging():
        # create special handler
        log_specialfile = LOG_FOLDER + "logspecialfiles.txt"
        log_file = LOG_FOLDER + "logfiles.txt"
        spl_handler = RotatingFileHandler(log_specialfile, 'a+', maxBytes=10000000, backupCount=5)
        spl_handler.addFilter(SpecialHandler.filter)
        spl_handler.setFormatter(SpecialHandler)

        # logging configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s.%(msecs)03d %(levelname)-8s: [%(filename)s:%(lineno)03d]  %(message)s",
            handlers=[
                logging.StreamHandler(),
                spl_handler,
                RotatingFileHandler(log_file, 'a+', maxBytes=10000000, backupCount=5)
            ],
            datefmt='%Y-%m-%d,%H:%M:%S')
        logging.addLevelName(constants.LG_LOGGING_MODULE_OUTPUT_LVL, constants.LG_LOGGING_MODULE_OUTPUT_NAME)


# test logic in main
if __name__ == "__main__":
    SpecialHandler.set_default_logging()

    ############# Some where some code ######################
    for i in range(1000):
        logging.info("counter is " + str(i))
        if i % 101 == 0:
            logging.info(f"{constants.LG_LOGGING_MODULE_OUTPUT_KEY} The multiple is {i}")
            logging.log(constants.LG_LOGGING_MODULE_OUTPUT_LVL, f"The multiple is {i}")

    #########################################################

    # More details refer http://collab.lge.com/main/x/OG-DRg
