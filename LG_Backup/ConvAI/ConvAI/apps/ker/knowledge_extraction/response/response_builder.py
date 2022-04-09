# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk
"""

import logging as logger
import os
import sys

from ..constants import params as cs

from .response_engine import ResponseEngine
from .json_builder import JsonBuilder


class ResponseBuilder(object):
    """
    class used to build the response json based on response code
    """

    def __init__(self):
        self.resp_engine = ResponseEngine()
        self.json_builder = JsonBuilder.get_instance()

    def generate_rcs_prd_reg_response(self, resp_code, model_dict):
        """
        generate the response json based on the response code
        Return:
             response dictionary
         """
        logger.debug("resp_code={0},model_dict:{1}".format(resp_code, model_dict))
        answer = ""
        if resp_code == cs.ResponseCode.SUCCESS:
            answer = self.json_builder.send_prod_types_for_registration(model_dict, True)
        return self._frame_response_json(resp_code, answer)

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
        resp_code, ker_cntxt, user_query, client_type, model_no = kwargs[0], kwargs[1], kwargs[2], kwargs[3], kwargs[4]
        logger.debug("resp_code={0},ker_cntxt:{1},user_query:{2},dict_resp:{3}".format(resp_code, ker_cntxt, user_query,
                                                                                       dict_resp))
        answer = ""
        if resp_code == cs.ResponseCode.SUCCESS:
            answer, resp_code = self.resp_engine.make_response(dict_resp, topic, user_query)

            if (resp_code == cs.ResponseCode.SUCCESS) and (client_type == cs.ClientType.RCS):
                answer = self._get_rcs_response(dict_resp, similarity_key, answer)
                logger.debug("RCS answer : %s",answer)

        return self._frame_response_json(resp_code, answer, model_no, user_query, ker_cntxt, similarity_key)

    def _get_rcs_response(self, dict_resp, similarity_key, template_resp):
        """
        frame the response for the RCS client

        Args:
            dict_resp:response returne dfrom retrieval engine
            similarity_key:extracted info from retrieval engine
            template_resp: template response framed using response engine
        return:
            json string response for RCS client
        """
        spec_dict = dict_resp.get(cs.XMLTags.SPECIFICATION_TAG, None)
        resp_key = ""
        if spec_dict is not None:
            resp_key = spec_dict.get(cs.RESPONSE_KEY, None)
        logger.info("resp_key for bot query=%s", resp_key)
        # call json builder and send bot response
        bot_response = self.json_builder.send_bot_response_for_userquery(similarity_key, dict_resp, template_resp
                                                                         , resp_key)
        logger.debug("RCS bot_response : %s", bot_response)
        return bot_response

    def _frame_response_json(self, resp_code, answer, model_no="", question="", ker_cntxt={}, similarity_key={}):
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
        resp[cs.IOConstants.MODEL_NO] = model_no
        resp[cs.IOConstants.KER_CNTXT] = ker_cntxt
        resp[cs.IOConstants.EXTRACTED_INFO] = similarity_key
        return resp
