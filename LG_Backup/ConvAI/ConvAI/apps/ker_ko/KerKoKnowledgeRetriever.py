"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import importlib
import json
import time
import os

import pandas as pd
from django.http import HttpResponse
from engines.KnowledgeRetriever import KnowledgeRetriever

from .ker_engine import KerEngine
from .knowledge_extraction.constants import params as cs
from .knowledge_extraction.constants.params import IOConstants as const
from .file_based_test import FileBasedTesting

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class KerKoKnowledgeRetriever(KnowledgeRetriever):
    """
    defines the method to parse configurations of KER server and
    forward requests to KER and sends back response to client
    """

    def __init__(self):
        logger.info('---KerKoKnowledgeRetriever init')
        self.QUERY = "question"
        self.RESP_QUES = 'Question'
        self.RESPONSE_STR = "Response"
        self.PART_NO = "part_no"
        self.KER_CNTXT = "ker_context"
        self.REQ_ID = "request_id"

        try:
            logger.info("Init KerKnowledgeRetriever")
            self.ker_engine = KerEngine()
            self.file_based_test = FileBasedTesting()
        except Exception as e:
            logger.exception("Exception: %s", e)

    def __del__(self):
        logger.info('KerKoKnowledgeRetriever delete')

    def process(self, request_json={}):
        """
            This function is used to forward the request to
            KER system and sends back response to client

            Args:
                request_json : json - Input request from client
            Returns:
                Response text : Http response of KER response
        """
        logger.info("request_json=%s", str(request_json))
        # extract ker specific dictionary and give to KER server
        ker_request = request_json['query']
        if request_json.get("request_type", None):
            ker_response = self.process_user_query(request_json)
            http_status_code = cs.SUCCESS
            request_json = ker_response
        else:
            http_status_code, ker_response = self.__process_kms_request(ker_request)
            logger.debug("ker_response : %s, %s, status_code=%d", ker_response, type(ker_response), http_status_code)

            # update ker response in kms response
            request_json['query'] = ker_response
        logger.debug("process response : %s", request_json)
        return request_json

    def __process_kms_request(self, request_json):
        """
        call the KER system to get the response for the user question

        Args:
            request_json: input json
        return:
            JSON response from KER system
        """
        response_json = self.ker_engine.process_request(request_json, cs.ClientType.KMS)

        if self.REQ_ID in request_json:
            req_id = request_json[self.REQ_ID]
            logger.debug("Input to KER=%s request_id=%s", request_json, req_id)
            logger.debug("response from KER=%s", response_json)

            response_json["request_id"] = req_id
        # Currently removing extracted_info and part_no from outer json. If needed will enable later
        response_json.pop(const.EXTRACTED_INFO, None)
        response_json.pop(const.PART_NO, None)

        # extract http status code
        http_status_code = response_json.get(const.HTTP_ERR_CODE, -1)
        # pop http status code from json string
        response_json.pop(const.HTTP_ERR_CODE, None)

        # As KER component is updated to return response as json, currently below function call is commented
        # json = self._frame_response_json(response_json)
        logger.debug("Return response from KER=%s", response_json)
        return http_status_code, response_json
        
    def get_supported_products(self):
        """
        get the product details from the DB

        Args:
            None
        Return:
            HTTPResponse with product_details dict
        """

        models_dict = self.ker_engine.get_product_models()
        new_model_dict ={}
        # key[0] -> product type , key[1] -> sub product type
        for key in models_dict.keys():
          if key[0] not in new_model_dict.keys():
            new_model_dict[key[0]]= {}
          new_model_dict[key[0]][key[1]]=models_dict[key]
        response_code = cs.ExternalErrorCode.MKG_SUCCESS
        return response_code, new_model_dict

    def process_user_query(self, request_json, send_http_response=False):
        """
            call the KER system to get the response for the user question

            Args:
                request_json: input json
                Ex:
                {
                "request_type": "asking_question",
                "query": {
                "part_no" : "MFL71485465",
                "question":"IE error",
                "selected_option":"",
                "ker_context": {},
                "request_id":1
                }
                }
            return:
                JSON response from KER system
                Ex:
                {
                    "query": {
                        "question": "IE error",
                        "selected_option": "",
                        "ker_context": {},
                        "request_id": 1,
                        "answer": {
                            "Troubleshooting": {
                                "ie": "kg"
                            }
                        },
                        "response_code": 0,
                        "response_message": 200
                    },
                    "response_type": "asking_question"
                }
        """
        recommendation = []
        best_matches = []
        answer = {}
        response_code = cs.ExternalErrorCode.MKG_SUCCESS

        logger.info("Input to KER = %s send_http_response=%d", request_json,send_http_response)
        ker_request_json = request_json[const.QUERY]
        req_id = ker_request_json[self.REQ_ID]
        logger.debug("Input to KER=%s request_id=%d", ker_request_json, req_id)

        # get request_type from input json and pop it
        request_type = request_json[const.HY_REQ_TYPE]

        # send mapped L1 keys for user query
        if request_type == const.HY_RES_STATUS_ASKING_QUESTION:
            logger.info("asking_question")
            # call mapped keys
            response_code, answer, best_matches, recommendation = self.ker_engine.find_mapped_keys(ker_request_json)
        elif request_type == const.HY_SEE_MANUAL_CONTENTS:
            # Frame response with supported sections and return
            response_code, answer = self.ker_engine.get_resp_for_manual_contents()
        elif request_type == const.HY_SEE_SECTION_CONTENTS:
            # get manual keys from doc/kg approaches and returns
            response_code, answer = self.ker_engine.get_section_content_answer(ker_request_json)
        # send actual response present in manual for the selected key and section for user query
        elif request_type == const.HY_RES_STATUS_SATISFIED:
            logger.info("Retrieve answer from KG/doc ")
            response_code, answer, recommendation = self.ker_engine.get_query_response(request_json)
        elif request_type == const.HY_RES_STATUS_NOT_SATISFIED:
            logger.info("Handling not satisfied with results")
            response_code, answer = self.ker_engine.not_satisfied_with_results_response(request_json)
        elif request_type == const.HY_RES_STATUS_SUPPORTED_PRODUCT:
            response_code, answer = self.get_supported_products()
            logger.info("response frm get_supported_products : %s", answer)
        else:
            logger.info("Invalid case")

        # forms final response
        response = self.ker_engine.form_response(request_json, request_type, answer, response_code, recommendation,
                                        best_matches)
        if send_http_response:
            http_response = HttpResponse(json.dumps(response), content_type="application/json")
            return http_response
        else:
            return response

    def get_common_problems(self, request_json):
        """
            call the KER system to get the response for the user question

            Args:
                request_json: input json
            return:
                JSON response from KER system
        """
        logger.debug("Input to KER = %s ", request_json)
        ker_request_json = request_json[cs.IOConstants.QUERY]
        req_id = ker_request_json[self.REQ_ID]
        logger.debug("Input to KER=%s request_id=%d", ker_request_json, req_id)

        # send mapped L1 keys for user query
        if request_json["request_type"] == "common_problems":
            logger.debug("common_problems")
            # call mapped keys
            if request_json[cs.IOConstants.QUERY][cs.IOConstants.PRODUCT] == "":
                request_json[cs.IOConstants.QUERY][cs.IOConstants.PRODUCT] = cs.CommonProblemConstants.DEFAULT_PRODUCT
                request_json[cs.IOConstants.QUERY][self.PART_NO] = cs.CommonProblemConstants.DEFAULT_PART_NO
            request_json[cs.IOConstants.QUERY][cs.IOConstants.ANSWER] = {}
            request_json[cs.IOConstants.QUERY][cs.IOConstants.ANSWER] = \
                cs.CommonProblemConstants.COMMON_PROBLEM_MAPPING[
                    request_json[cs.IOConstants.QUERY][cs.IOConstants.PRODUCT]]
            request_json[cs.IOConstants.QUERY][cs.IOConstants.RESP_CODE] = cs.ExternalErrorCode.MKG_SUCCESS
            request_json[cs.IOConstants.QUERY][cs.IOConstants.RESP_MSG] = \
                cs.ExternalErrorMsgs.ERR_MSGS[cs.ExternalErrorCode.MKG_SUCCESS][cs.ExternalErrorMsgs.MSG]
        else:
            request_json[cs.IOConstants.QUERY][cs.IOConstants.RESP_CODE] = cs.ExternalErrorCode.MKG_INVALID_REQUEST
            request_json[cs.IOConstants.QUERY][cs.IOConstants.RESP_MSG] = \
                cs.ExternalErrorMsgs.ERR_MSGS[cs.ExternalErrorCode.MKG_INVALID_REQUEST][cs.ExternalErrorMsgs.MSG]
        http_response = HttpResponse(json.dumps(request_json), content_type="application/json")
        return http_response

    def process_uploaded_file(self, file_name):
        """
        Process the uploaded file and get the response for each

        Args:
            file_name:Name of the file uploaded
        Return:
            status: processed status
        """
        status = self.file_based_test.process_uploaded_file(file_name)
        return status
