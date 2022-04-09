"""
/*-------------------------------------------------
* Copyright(c) 2021-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import importlib
import os
import logging as logger
import json

import pandas as pd
from django.http import HttpResponse

from .ker_engine import KerEngine
from .knowledge_extraction.constants import params as cs
from .knowledge_extraction.constants.params import IOConstants as const

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class FileBasedTesting():

    def __init__(self):
        self.ker_engine = KerEngine.get_instance()
        self.QUERY = "question"
        self.RESP_QUES = 'Question'
        self.RESPONSE_STR = "Response"
        self.MODEL_NO = "model_no"
        self.KER_CNTXT = "ker_context"
        self.REQ_ID = "request_id"

    def get_extension(self, file_name):
        """
        get the file extension from the file_name

        Args:
            file_name: name of the uploaded file
        Return:
            file_ext: Extension of the file
        """
        file_ext = file_name.split(".")[1]
        return file_ext


    def get_df_based_on_ext(self, ext, file_path):
        """
        load the file pandas dataframe based on extension

        Args:
            ext: file extension
            file_path: path of the uploaded file
        Return:
            df: Dataframe of the file
        """
        df = None
        if ext == "csv":
            df = pd.read_csv(file_path)
        elif ext == "xlsx":
            df = pd.read_excel(file_path)
        return df


    def write_to_file(self, df, file_ext, file_path):
        """
        Write to the file based on file extension

        Args:
            df: Processed dataframe with reponse
            file_ext: Extension of the file
            file_path: Path of the file to be downloaded
        """
        if file_ext == "csv":
            df.to_csv(file_path, header=True, index=False, encoding="utf-8-sig")
        elif file_ext == "xlsx":
            df.to_excel(file_path, header=True, index=False, encoding="utf-8-sig")


    def _frame_request(self, question, model_no, req_type, selected_option=None):
        """
        Frame the request based on the question, model number

        Args:
            question:question from the file
            model_no: model number from file
            req_type: request type
            selected_option: choosen option
        Return:
            request: request dict framed
        """
        request = {}
        request[cs.IOConstants.QUERY] = {}
        request[cs.IOConstants.QUERY][cs.IOConstants.KER_CNTXT] = {}
        request[cs.IOConstants.QUERY][cs.IOConstants.MODEL_NO] = model_no
        request[cs.IOConstants.QUERY][cs.IOConstants.QUESTION] = question
        request[cs.IOConstants.QUERY][cs.IOConstants.REQ_ID] = 1
        if selected_option is None:
            request[cs.IOConstants.QUERY][cs.IOConstants.HY_SELECTED_OPTION] = {}
        else:
            request[cs.IOConstants.QUERY][cs.IOConstants.HY_SELECTED_OPTION] = selected_option
        request[cs.IOConstants.HY_REQ_TYPE] = req_type
        return request


    def _choose_selected_option(self, key_in_file, ask_result_response):
        """
        Choose the option based based on option mentioned in file

        Args:
            key_in_file: key mentioned in file
            ask_result_response: Ask question type response
        Return:
            select_option: choosen option dict
        """
        options = ask_result_response[cs.IOConstants.QUERY][cs.IOConstants.HY_BEST_MATCHES]

        for idx, selected_option in enumerate(options):

            if key_in_file == selected_option['key']:
                selected_option.pop("score")
                return idx, selected_option

        return -1, None


    def get_product_detail(self, req_json):
        """
        get the product details from the DB

        Args:
            req_json: request json
        Return:
            HTTPResponse with product_details dict
        """

        models_dict = self.ker_engine.get_product_models()
        new_model_dict ={}
        # considering index 1-sub product from (product type, sub prroduct type) tuple
        for key in models_dict.keys():
            new_model_dict[key[1]] = models_dict[key]
        req_json["response_type"] = req_json.pop("request_type", None)
        req_json[cs.IOConstants.QUERY][cs.IOConstants.RESP_CODE] = cs.ExternalErrorCode.MKG_SUCCESS
        req_json[cs.IOConstants.QUERY][cs.IOConstants.RESP_MSG] \
            = cs.ExternalErrorMsgs.ERR_MSGS[cs.ExternalErrorCode.MKG_SUCCESS][cs.ExternalErrorMsgs.MSG]
        req_json[cs.IOConstants.QUERY][cs.IOConstants.ANSWER] = new_model_dict
        http_response = HttpResponse(json.dumps(req_json), content_type="application/json")
        return http_response

    def process_user_query(self, request_json, send_http_response=False):
        """
            call the KER system to get the response for the user question

            Args:
                request_json: input json
                Ex:
                {
                "request_type": "asking_question",
                "query": {
                "model_no" : "F214DD",
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
            response_code, answer = self.get_product_detail(request_json)
            logger.info("response frm get_product_detail : %s", answer)
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

    def _process_req_frm_file(self, df):
        """
        Process the file based inputs

        Args:
            df: Dataframe read from the uploaded file
        Return:
            df: return Dataframe with processed input and reponse
        """
        questions = df["Questions"]
        models = df["Models"]
        options = df["Select option"]
        selected_option_list = []
        response_list = []

        for question, model_no, option in zip(questions, models, options):
            request_dict = self._frame_request(question, model_no, const.HY_RES_STATUS_ASKING_QUESTION)
            ask_result_dict = self.process_user_query(request_dict)
            option_cnt, selected_option = self._choose_selected_option(option, ask_result_dict)
            selected_option_list.append(option_cnt + 1)
            if selected_option is None:
                response_list.append("Key not found")
                continue
            request_dict = self._frame_request(question, model_no, const.HY_RES_STATUS_SATISFIED, selected_option)
            satisfied_with_result = self.process_user_query(request_dict)
            response_list.append(
                satisfied_with_result[cs.IOConstants.QUERY][cs.IOConstants.ANSWER]["content"][0]["solution"])
        logger.debug("select_option : %s", selected_option_list)
        df["Option Choosed"] = selected_option_list
        df["Answer"] = response_list
        return df


    def process_uploaded_file(self, file_name):
        """
        Process the uploaded file and get the response for each

        Args:
            file_name:Name of the file uploaded
        Return:
            status: processed status
        """
        current_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        media_path = os.path.join(current_path, '..', '..', 'media', file_name)
        file_ext = self.get_extension(file_name)
        df = self.get_df_based_on_ext(file_ext, media_path)
        df = self._process_req_frm_file(df)
        self.write_to_file(df, file_ext, media_path)
        return 0
