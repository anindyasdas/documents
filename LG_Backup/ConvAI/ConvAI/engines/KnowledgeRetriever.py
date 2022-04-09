from abc import *
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class KnowledgeRetriever(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def __del__(self):
        pass

    def preprocess(self, request_json):
        # from <-> to switch
        logger.debug("preprocess")
        from_ = request_json["from"]
        request_json["from"] = "KMS"
        request_json["to"] = from_
        return request_json

    def process(self, request_json):
        return request_json
