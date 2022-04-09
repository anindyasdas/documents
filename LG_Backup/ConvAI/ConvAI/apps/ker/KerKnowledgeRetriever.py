import json
import importlib

from apps.ker.knowledge_extraction.constants import params as cs
from apps.ker.knowledge_extraction.constants.params import IOConstants as const
from apps.ker.knowledge_extraction.ker_engine import KerEngine
from django.http import HttpResponse
from engines.KnowledgeRetriever import KnowledgeRetriever

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class KerKnowledgeRetriever(KnowledgeRetriever):
    """
    defines the method to parse configurations of KER server and
    forward requests to KER and sends back response to client
    """

    def __init__(self):
        logger.debug('---KerKnowledgeRetriever init')
        logger.debug("Read config in KerKnowledgeRetriever")
        self.QUERY = "question"
        self.MODEL_NO = "model_no"
        self.KER_CNTXT = "ker_context"
        self.REQ_ID = "request_id"
        try:
            self.knowledge_retriever = KerEngine()
        except Exception as e:
            logger.exception("Exception: %s", e)
        logger.debug('---KerKnowledgeRetriever init done')

    def __del__(self):
        logger.debug('KerKnowledgeRetriever delete')

    def process(self, request_json=""):
        """
            This function is used to forward the request to
            KER system and sends back response to client

            Args:
                request_json : json - Input request from client
            Returns:
                Response text : Http response of KER response
        """
        logger.debug("process")
        logger.info("request_json=%s", str(request_json))
        query = request_json["query"]
        http_status_code, ker_response = self.process_kms_request(query)
        logger.debug("ker_response : %s, %s, status_code=%d", ker_response, type(ker_response), http_status_code)
        request_json["query"] = ker_response
        logger.debug("process response : %s", request_json)
        return request_json

    def process_kms_request(self, json_obj):
        # As KER component is updated to take json as input, currently below extractions are commented
        # sentence = json_obj[self.QUERY]
        # modelno = json_obj[self.MODEL_NO]
        # ker_cntxt = json_obj[self.KER_CNTXT]
        # req_id = json_obj[self.REQ_ID]
        # resp_json = self.get_kms_answer(sentence, modelno, ker_cntxt, req_id)
        http_status_code, resp_json = self.get_kms_answer(json_obj)
        return http_status_code, resp_json

    def get_kms_answer(self, request_json):
        """
        call the KER system to get the response for the user question

        Args:
            request_json: input json
        return:
            JSON response from KER system
        """
        response_json = self.knowledge_retriever.process_request(request_json, cs.ClientType.KMS)

        if self.REQ_ID in request_json:
            req_id = request_json[self.REQ_ID]
            logger.debug("Input to KER=%s request_id=%s", request_json, req_id)
            logger.debug("response from KER=%s", response_json)

            response_json["request_id"] = req_id
        # Currently removing extracted_info and model_no from outer json. If needed will enable later
        response_json.pop(const.EXTRACTED_INFO, None)
        response_json.pop(const.MODEL_NO, None)

        # extract http status code
        http_status_code = response_json.get(const.HTTP_ERR_CODE, -1)
        # pop http status code from json string
        response_json.pop(const.HTTP_ERR_CODE, None)

        # As KER component is updated to return response as json, currently below function call is commented
        # json = self._frame_response_json(response_json)
        logger.debug("Return response from KER=%s", response_json)
        return http_status_code, response_json

    def _frame_response_json(self, response_json):
        """
        frame the response json for the KMS system

        Args:
            req_id: request id
            resp_code: response code
            question: user question
            answer: answer from KER system
            ker_cntxt: current context
        return:
            framed response json
        """
        resp = {}
        resp["request_id"] = req_id
        resp["response_code"] = resp_code
        resp["response_message"] = cs.resp_msg[resp_code]
        resp["question"] = question
        resp["answer"] = answer
        resp.update(ker_cntxt)
        return json.dumps(resp)
