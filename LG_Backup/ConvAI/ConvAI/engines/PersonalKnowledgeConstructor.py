import importlib


kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class PKnowledgeConstructor(object):
    def __init__(self):
        logger.debug('PKnowledgeConstructor init')

    def __del__(self):
        logger.debug('PKnowledgeConstructor delete')

    def process(self, request_json):
        logger.debug('PKnowledgeConstructor process')
        from_ = request_json["from"]
        request_json["from"] = "KMS"
        request_json["to"] = from_
        return request_json
