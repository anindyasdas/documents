import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class KnowledgeConstructor(object):
    def __init__(self, gk_constructor, pk_constructor):
        logger.debug('KnowledgeConstructor init')
        self.gk_constructor = gk_constructor
        self.pk_constructor = pk_constructor

    def __del__(self):
        logger.debug('KnowledgeConstructor delete')

    def construct(self, request_json):
        logger.debug('KnowledgeConstructor construct')
        # Interim implementation
        if request_json['process'] == 'global_construction':
            return self.gk_constructor.process(request_json)

    def load(self):
        logger.debug('KnowledgeConstructor re-load')
        # TODO: 1) reload, 2) compare backup & current, 3) backup
        diff = True
        if diff is True:
            self.gk_constructor.process()
            self.pk_constructor.process()

