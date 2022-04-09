""" =========================================================================\n
    KMS App framework : class and APIs to create engine components
    =========================================================================
"""
import sys
import importlib
from abc import ABC, abstractmethod
from kms_error import KMSError

# engine module
from engines.KnowledgeRetriever import KnowledgeRetriever
from engines.GlobalKnowledgeConstructor import GKnowledgeConstructor
from engines.PersonalKnowledgeConstructor import PKnowledgeConstructor
from engines.KnowledgeConstructor import KnowledgeConstructor

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


def load_module(module):
    """
    Load module for dynamic import of app module
    """
    module_path = module
    if module_path in sys.modules:
        return sys.modules[module_path]
    else:
        ret = __import__(module_path, fromlist=[module])
        if ret is not None:
            return ret
        else:
            raise KMSError(30)


class EngineFactory(ABC):
    """
    Abstract Factory Pattern, Make EngineFactory inheriting this Factory
    """
    def __init__(self, app_name):
        """
        Set app_name and app_module
        """
        self.app_name = app_name
        self.app_module = "apps." + app_name

    @abstractmethod
    def create_retriever(self) -> KnowledgeRetriever:
        """
        Abstract method to make Retriever inheriting this method
        """
        pass

    @abstractmethod
    def create_gk_constructor(self) -> GKnowledgeConstructor:
        """
        Abstract method to make Global Knowledge Constructor inheriting this method
        """
        pass

    @abstractmethod
    def create_pk_constructor(self) -> PKnowledgeConstructor:
        """
        Abstract method to make Personal Knowledge Constructor inheriting this method
        """
        pass

    @abstractmethod
    def create_constructor(self, pk_constructor, gk_constructor) -> KnowledgeConstructor:
        """
        Abstract method to make Ontology Manager inheriting this method
        """
        pass


class TestEngineFactory(EngineFactory):
    def __init__(self, app_name):
        EngineFactory.__init__(self, app_name)
        try:
            self.app_retriever = load_module(self.app_module + ".TestKnowledgeRetriever")
        except KMSError as e:
            logger.error(e)

    def create_retriever(self) -> KnowledgeRetriever:
        return self.app_retriever.TestKnowledgeRetriever()

    def create_gk_constructor(self) -> GKnowledgeConstructor:
        return GKnowledgeConstructor()

    def create_pk_constructor(self) -> PKnowledgeConstructor:
        return PKnowledgeConstructor()

    def create_constructor(self, pk_constructor, gk_constructor) -> KnowledgeConstructor:
        return KnowledgeConstructor(pk_constructor, gk_constructor)


class KerEnEngineFactory(EngineFactory):
    def __init__(self, app_name):
        EngineFactory.__init__(self, app_name)
        self.app_retriever = load_module(self.app_module + ".KerKnowledgeRetriever")

    def create_retriever(self) -> KnowledgeRetriever:
        return self.app_retriever.KerKnowledgeRetriever()

    def create_gk_constructor(self) -> GKnowledgeConstructor:
        return GKnowledgeConstructor()

    def create_pk_constructor(self) -> PKnowledgeConstructor:
        return PKnowledgeConstructor()

    def create_constructor(self, pk_constructor, gk_constructor) -> KnowledgeConstructor:
        return KnowledgeConstructor(pk_constructor, gk_constructor)


class KerKoEngineFactory(EngineFactory):
    def __init__(self, app_name):
        EngineFactory.__init__(self, app_name)
        self.app_retriever = load_module(self.app_module + ".KerKoKnowledgeRetriever")

    def create_retriever(self) -> KnowledgeRetriever:
        return self.app_retriever.KerKoKnowledgeRetriever()

    def create_gk_constructor(self) -> GKnowledgeConstructor:
        return GKnowledgeConstructor()

    def create_pk_constructor(self) -> PKnowledgeConstructor:
        return PKnowledgeConstructor()

    def create_constructor(self, pk_constructor, gk_constructor) -> KnowledgeConstructor:
        return KnowledgeConstructor(pk_constructor, gk_constructor)