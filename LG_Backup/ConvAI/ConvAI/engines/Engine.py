import threading

from config.config_manager import ConfigManager
from engines.EngineFactory import *
from engines.Scheduler import Scheduler

lock = threading.Lock()
kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class EngineSingleton(type):
    """
    A class to make Engine Singleton
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        :param args: variable argument
        :param kwargs : variable argument
        """
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(EngineSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Engine(metaclass=EngineSingleton):
    """
    A class to process to reply rest_api.views.IndexView
    """
    def __init__(self):
        """
        Assemble components to make Engine
        """
        logger.debug('Engine init')
        # Get app_name from config_manger and Set the factory
        try:
            config_manager = ConfigManager()
            app_name = config_manager.app_name
            if app_name == "ker":
                engine_factory = KerEnEngineFactory(app_name)
            elif app_name == "ker_ko":
                engine_factory = KerKoEngineFactory(app_name)
            else:  # default is test
                engine_factory = TestEngineFactory(app_name)

            self.retriever = engine_factory.create_retriever()
            self.gk_constructor = engine_factory.create_gk_constructor()
            self.pk_constructor = engine_factory.create_pk_constructor()
            self.constructor = engine_factory.create_constructor(
                self.gk_constructor,
                self.pk_constructor
            )
            self.scheduler = Scheduler(self.constructor)
            # get html file name from config manager
            self.template_name = config_manager.get("html","template_name")
            logger.debug('Vanitha Template file name=%s', self.template_name)
            logger.debug('Engine init done')
        except Exception as e:
            logger.error('Engine Init error')
            logger.error(e)
            raise KMSError(30)

    def __del__(self):
        """
        Engine Destructor
        """
        logger.debug('Engine delete')

    def retrieve(self, request_json):
        """
        Process for external retrieval of request_json
        : param request_json: external request
        : type str(json)
        : return answer: result of retrieving request_json
        : rtype: JsonResponse
        """
        logger.debug('Retrieve')
        request_json = self.retriever.preprocess(request_json)
        answer = self.retriever.process(request_json=request_json)
        return answer

    def construct(self, request_json):
        """
        Process for external construction request
        """
        logger.debug('Construct')
        return self.constructor.construct(request_json=request_json)

    def process_request(self, request):
        """
        process the user request

        Args:
            request: request from client
        Return:
            HttpResponse instance
        """
        response = self.retriever.process(request)
        return response

    def process_kms_ker_request(self, request):
        """
        process the user request

        Args:
            request: request from client
        Return:
            HttpResponse instance
        """
        response = self.retriever.process_kms_ker(request)
        return response

    def process_pref_request(self):
        """
        get the current context json from the loaded app

        Return:
            HttpResponse with context information
        """
        response = self.retriever.get_pref()
        return response

    def reset_pref_request(self):
        """
        reset the preference

        Return:
            HttpResponse with reset status
        """
        response = self.retriever.reset_pref()
        return response

    def get_updated_thinq_settings(self):
        """
        get the updated thinq settings

        Return:
            HttpResponse with thinq details
        """
        response = self.retriever.get_updated_thinq_settings()
        return response

    def reset_thinq_settings(self):
        """
        reset the thinq settings

        Return:
            HttpResponse with
        """
        response = self.retriever.reset_thinq_settings()
        return response

    def get_template_name(self):
        """
        get the HTML template name

        Return:
            template_name: String
        """
        return self.template_name

    def process_user_query(self, req_json):
        response = self.retriever.process_user_query(req_json,send_http_response=True)
        return response

    def get_common_problems(self, req_json):
        response = self.retriever.get_common_problems(req_json)
        return response

    def process_uploaded_file(self, file_name):
        response = self.retriever.process_uploaded_file(file_name)
        return response
