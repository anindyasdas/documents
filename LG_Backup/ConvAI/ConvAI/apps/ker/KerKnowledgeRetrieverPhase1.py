import logging
from engines.KnowledgeRetriever import KnowledgeRetriever
import requests
import json
from django.http import HttpResponse
from configparser import ConfigParser
import os
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)


class KerKnowledgeRetriever(KnowledgeRetriever):
    """
    defines the method to parse configurations of KER server and
    forward requests to KER and sends back response to client
    """
    def __init__(self):
        logger.debug('---KerKnowledgeRetriever init')
        logger.debug("Read config in KerKnowledgeRetriever")
        try:
            # read the ker url info from config file
            config_parser = ConfigParser()
            abspath_path = os.path.abspath(os.path.join(os.path.dirname(
                os.path.realpath(__file__)))) + '/configuration.ini'
            logger.debug('config file path=%s', abspath_path)

            # read the configurations
            config_parser.read(abspath_path)
            self.ker_url = config_parser.get("ker", "url")
            self.ker_url_headers = json.loads(config_parser.get("ker", "headers"))

            logger.debug("Read config is completed in KerKnowledgeRetriever")
            logger.debug("Ker url from config files=%s", self.ker_url)
            logger.debug("Ker headers from config files=%s", self.ker_url_headers)
        except Exception as e:
            logger.error("Exception:", e)

    def __del__(self):
        logger.debug('KerKnowledgeRetriever delete')

    def process(self, request_json):
        """
            This function is used to forward the request to
            KER system and sends back response to client

            Args:
                request_json : json - Input request from client
            Returns:
                Response text : Http response of KER response
        """
        logger.debug('KerKnowledgeRetriever process url=%s',self.ker_url)
        logger.info("request_json=%s",str(request_json))

        # posting the client request to KER system
        ker_response = requests.post(self.ker_url, data=request_json, headers=self.ker_url_headers)

        logger.debug("***Response code from KER=%d", int(ker_response.status_code))
        logger.info("KER response=%s",str(ker_response.text))
        return HttpResponse(ker_response.text)