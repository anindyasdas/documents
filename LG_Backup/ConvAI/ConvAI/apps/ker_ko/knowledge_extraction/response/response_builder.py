# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk
"""
import importlib
from ..constants import params as cs
from .response_engine import ResponseEngine
from .json_builder import JsonBuilder
# KMS Logger
kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class ResponseBuilder(object):
    """
    class used to build the response json based on response code
    """

    def __init__(self):
        self.resp_engine = ResponseEngine()
        self.json_builder = JsonBuilder.get_instance()

    def generate_response(self, *kwargs, topic=None, dict_resp=None, similarity_key=None):
        """
        generate the response json based on the response code

        Args:
            resp_code: response code
            ker_cntxt: current ker context
            user_query: user question
            topic: topic identified from question
            dict_resp: response dict from retrieval engine
            similarity_key: info extraction module output

        Return:
            response dictionary
        """
        resp_code, ker_cntxt, user_query, client_type, part_no = kwargs[0], kwargs[1], kwargs[2], kwargs[3], kwargs[4]
        logger.info("resp_code={0},ker_cntxt:{1},user_query:{2},dict_resp:{3}".format(resp_code, ker_cntxt, user_query,
                                                                                       dict_resp))
        answer = ""
        if resp_code == cs.ResponseCode.SUCCESS:

            if (resp_code == cs.ResponseCode.SUCCESS) and (client_type == cs.ClientType.BNC):
                return self._frame_bnc_response_json(resp_code, dict_resp, part_no, user_query, ker_cntxt, similarity_key)

            answer, resp_code = self.resp_engine.make_response(dict_resp, topic, user_query)

        return self._frame_response_json(resp_code, answer, part_no, user_query, ker_cntxt, similarity_key)

    def _frame_response_json(self, resp_code, answer, part_no="", question="", ker_cntxt={}, similarity_key={}):
        """
        frame the response json

        Args:
            resp_code: response code
            question: user question
            answer: answer from KER system
            ker_cntxt: current context
        return:
            framed response json
        """
        if ker_cntxt is None:
            ker_cntxt = {}
        if similarity_key is None:
            similarity_key = {}
        resp = {}
        ext_error_code = cs.ExternalErrorCode.internal_to_ext_err_code[resp_code]
        resp_msg = cs.ExternalErrorMsgs.ERR_MSGS[ext_error_code][cs.ExternalErrorMsgs.MSG]
        http_code = cs.ExternalErrorMsgs.ERR_MSGS[ext_error_code][cs.ExternalErrorMsgs.HTTP_CODE]

        if resp_code != cs.ResponseCode.SUCCESS:
            answer = resp_msg
        else:
            ker_cntxt[cs.IOConstants.PREV_ANSWER] = answer

        resp[cs.IOConstants.HTTP_ERR_CODE] = http_code
        resp[cs.IOConstants.RESP_CODE] = ext_error_code
        resp[cs.IOConstants.RESP_MSG] = resp_msg
        resp[cs.IOConstants.ANSWER] = answer
        resp[cs.IOConstants.QUESTION] = question
        resp[cs.IOConstants.PART_NO] = part_no
        resp[cs.IOConstants.KER_CNTXT] = ker_cntxt
        resp[cs.IOConstants.EXTRACTED_INFO] = similarity_key
        return resp


    def _frame_bnc_response_json(self, resp_code, dict_resp=None, part_no="", question="", ker_cntxt=None, similarity_key=None):
        """
        frame the response json

        Args:
            resp_code: response code
            question: user question
            answer: answer from KER system
            ker_cntxt: current context
        return:
            framed response json
        """
        if ker_cntxt is None:
            ker_cntxt = {}
        if similarity_key is None:
            similarity_key = {}
        resp = {}
        ext_error_code = cs.ExternalErrorCode.internal_to_ext_err_code[resp_code]
        resp_msg = cs.ExternalErrorMsgs.ERR_MSGS[ext_error_code][cs.ExternalErrorMsgs.MSG]
        http_code = cs.ExternalErrorMsgs.ERR_MSGS[ext_error_code][cs.ExternalErrorMsgs.HTTP_CODE]

        if resp_code != cs.ResponseCode.SUCCESS:
            dict_resp = resp_msg
        else:
            ker_cntxt[cs.IOConstants.PREV_ANSWER] = dict_resp

        resp[cs.IOConstants.HTTP_ERR_CODE] = http_code
        resp[cs.IOConstants.RESP_CODE] = ext_error_code
        resp[cs.IOConstants.RESP_MSG] = resp_msg
        resp[cs.IOConstants.ANSWER] = dict_resp
        resp[cs.IOConstants.QUESTION] = question
        resp[cs.IOConstants.PART_NO] = part_no
        resp[cs.IOConstants.KER_CNTXT] = ker_cntxt
        resp[cs.IOConstants.EXTRACTED_INFO] = similarity_key
        return resp
