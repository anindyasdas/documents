"""
/*-------------------------------------------------
* Copyright(c) 2021-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import logging as logger
import importlib
import jsonschema
from configparser import ConfigParser
import os
import json

from .knowledge_extraction.constants import params as cs
from .knowledge_extraction.constants.params import IOConstants as const
from .knowledge_extraction.dialogue_manager.dialoguemanager import DialogueManager
from .nlp_engine_client import NlpEngineClient

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, 'knowledge_extraction', 'config', 'configuration.ini')

class InputValidator(object):


    def __init__(self):
        self.nlp_eng_client = NlpEngineClient.get_instance()
        self.diag_mgr = DialogueManager.get_instance()
        self.request_schema = self._read_request_schema()

    def _read_request_schema(self):
        """
        read the request schema

        Return:
            request schema json
        """
        logger.info("CONFIG_PATH : %s", CONFIG_PATH)
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        request_schema_file = os.path.join(current_path, 'knowledge_extraction',
                                           config_parser.get("json_schema", "request_schema"))
        with open(request_schema_file, "r") as pf:
            request_schema = json.load(pf)

        return request_schema

    def __validate_model_no(self, input_json, client_type):
        """
            This function is used to get validate model number of
            input_json
            Args:
                input_json : dict
                           Ker_engine input json
                client_type : int
                           HTML-1/ RCS-2 / KMS-3
            Returns:
                res : bool
                    True/False
        """
        res = False
        logger.info("Begin : input_json in __validate_model_no=%s" % (str(input_json)))
        # check model no in question
        _, model_no = self.diag_mgr.get_model_no(input_json[const.QUESTION], input_json[const.MODEL_NO], client_type)
        if (model_no is not None) and (len(model_no.strip()) > 0):
            logger.debug("modelno in question=%s" % model_no)
            # if model_no present in question, will give priority to this
            # future reference : model_no, prd_type = close_match_model(model_no)
            # future reference : logger.debug("closed match model number : %s",model_no)
            input_json[const.MODEL_NO] = model_no
            res = True
        # check model_no in the input json
        elif const.MODEL_NO in input_json:
            model_no = input_json.get(const.MODEL_NO, None)
            # future reference : model_no, prd_type = close_match_model(model_no)
            # future reference : logger.debug("closed match model number : %s", model_no)
            if (model_no is not None) and (len(model_no.strip()) > 0):
                res = True
            logger.debug("modelno from context=%s" % model_no)
        logger.debug("End : __validate_model_no input_json=%s res=%d" % (str(input_json), res))
        return res

    def __validate_part_no(self, input_json, client_type):
        """
            This function is used to get validate model number of
            input_json
            Args:
                input_json : dict
                           Ker_engine input json
                client_type : int
                           HTML-1/ RCS-2 / KMS-3
            Returns:
                res : bool
                    True/False
        """
        res = False
        logger.info("Begin : input_json in __validate_part_no=%s" % (str(input_json)))
        # check part no in question
        partnumber = self.diag_mgr.get_part_no(input_json[const.QUESTION], input_json[cs.IOConstants.PART_NO])
        if (partnumber is not None) and (len(partnumber.strip()) > 0):
            logger.debug("partnumber in question=%s" % partnumber)
            # if model_no present in question, will give priority to this
            # future reference : model_no, prd_type = close_match_model(model_no)
            # future reference : logger.debug("closed match model number : %s",model_no)
            input_json[cs.IOConstants.PART_NO] = partnumber
            res = True

        logger.debug("End : __validate_part_no input_json=%s res=%d" % (str(input_json), res))
        return res

    def __validate_product_type(self, input_json, client_type):
        isvalid = True
        resp_code, product, sub_prd_type = self.diag_mgr.get_product_type(input_json[cs.IOConstants.PART_NO],
                                                                          input_json[const.QUESTION],
                                                                          input_json[const.KER_CONTEXT], client_type)
        if (product is None) or (len(product.strip()) <= 0):
            logger.error("Dialogua manager returns no product")
            isvalid = False
            if (resp_code == cs.ResponseCode.CLIENT_ERROR) or (resp_code == cs.ResponseCode.CONNECTION_ERROR) or \
                    (resp_code == cs.ResponseCode.INTERNAL_ERROR):
                return isvalid, None, None, cs.ExternalErrorCode.MKG_KG_CONNECTION_ERROR
            return isvalid, None, None, cs.ExternalErrorCode.MKG_QUERY_PART_NO_NOT_FOUND
        return isvalid, product, sub_prd_type, cs.ExternalErrorCode.MKG_SUCCESS

    def __validate_classifier_output(self, category, follow_up, intent, section, sub_section):
        """
            for spec section, section and follow_up is mandatory fields
            for troubleshooting, section,sub_section and intent are mandatory fields
            for operation section , intent,sub_section,ques_type and category are mandatory fields
        """
        if ((section != cs.Section.SPEC) or (follow_up is None)) and (
                (section != cs.Section.TROB) or (intent is None) or (sub_section is None)) and (
                (section != cs.Section.OPERATION) or (intent is None) or (sub_section is None) or (category is None)):
            logger.debug("classifier info keys dict validation fails")
            isvalid = False
        else:
            isvalid = True

        logger.debug("End : __validate_classifier_output=%d", isvalid)
        return isvalid

    def __validate_classifier_info(self, input_json, product):
        logger.debug("Begin : input_json in classifier_info=%s" % (str(input_json)))
        # get classifier info and assign None if key not present
        classifier_res = input_json.get(const.CLASSIFIER_INFO, None)
        logger.debug("classi_resp=%s", str(classifier_res))
        # check classifier key info and it has non-empty dictionary
        if (classifier_res is None) or (classifier_res is not None and not bool(classifier_res)):
            classifier_res, class_resp_code = self.nlp_eng_client.get_classifier_output(input_json[const.QUESTION],
                                                                                        product)
            logger.debug("from nlp client classifier info=%s", classifier_res)
            if classifier_res is None:
                # update status to return error code
                isvalid = False
                error_code = cs.ExternalErrorCode.internal_to_ext_err_code[class_resp_code]
                return isvalid, error_code
        else:
            logger.debug("input_json has valid classifier key already")
            classifier_res = input_json[const.CLASSIFIER_INFO]

        # validate classifier_info
        section = classifier_res.get(cs.ProblemTypes.SECTION, None)
        sub_section = classifier_res.get(cs.ProblemTypes.SUB_SECTION, None)
        follow_up = classifier_res.get(cs.ProblemTypes.FOLLOW_UP, False)
        intent = classifier_res.get(cs.ProblemTypes.INTENT, cs.CAUSES_SOL_KEY)
        ques_type = classifier_res.get(cs.ProblemTypes.QUES_TYPE, None)
        category = classifier_res.get(cs.ProblemTypes.CATEGORY, None)
        logger.debug("section=%s sub-section=%s intent=%s ques_type=%s", section, sub_section, intent, ques_type)
        # validate classifier outputs and returns true/false
        isvalid = self.__validate_classifier_output(category, follow_up, intent, section, sub_section)

        if isvalid:
            # update classifier info key,value in dict
            input_json[const.CLASSIFIER_INFO] = classifier_res
        logger.debug("End : input_json in classifier_info=%s" % (str(input_json)))
        return isvalid


    def __validate_similarity_key(self, input_json, product, sub_prd_type):
        """
            This function is used to get validate similarity key
            Args:
                input_json : dict
                           Ker_engine input json
                client_type : int
                           HTML-1/ RCS-2 / KMS-3
                question : str
                           user question
            Returns:
                res : bool
                    True/False
        """
        isvalid = True

        logger.info("Begin : input_json in __validate_similarity_key=%s" % (str(input_json)))
        # get classifier info and assign None if key not present
        similarity_resp = input_json.get(const.SIMILARITY_KEY, None)
        logger.debug("similarity_resp=%s", str(similarity_resp))
        # check similarity key info and it has non-empty dictionary
        if (similarity_resp is None) or (similarity_resp is not None and (len(similarity_resp) <= 0)):
            # extract question from input_json
            question = input_json[const.QUESTION]
            isvalid = True
            # extract section from classifier info
            section = input_json[const.CLASSIFIER_INFO][cs.ProblemTypes.SECTION]
            # extract sub section from classifier info
            sub_section = input_json[const.CLASSIFIER_INFO][cs.ProblemTypes.SUB_SECTION]

            # call nlp_engine_client to get similarity_key
            similarity_key, simi_resp_code = self.nlp_eng_client.get_similarity_output(question, section, product,
                                                                                       sub_prd_type, sub_section)

            if similarity_key is None:
                # update status to return error code
                isvalid = False
                error_code = cs.ExternalErrorCode.internal_to_ext_err_code[simi_resp_code]
                return isvalid, error_code

            # update classifier info key,value in dict
            input_json[const.SIMILARITY_KEY] = similarity_key

        logger.debug("End : isvalid=%d input_json in __validate_similarity_key=%s" % (isvalid, str(input_json)))
        return isvalid, cs.ExternalErrorCode.MKG_SUCCESS

    def __validate_input_message_format(self, input_json, client_type):
        """
            Function is used to get validate input json and get
            NLP modules output for any missing informations and get the
            result for user question
            Args:
                input_json : dict
                           Ker_engine input json
                client_type : int
                           HTML/RCS/KMS
            Returns:
                bool : True/False
                error_code : int
                    error code value
        """
        is_valid = True
        resp_code = cs.ExternalErrorCode.MKG_SUCCESS
        req_id = input_json.get(const.REQ_ID, -1)


        try:
            logger.info("request json : %s", input_json)
            jsonschema.validate(instance=input_json, schema=self.request_schema)

            if (isinstance(req_id, str)) or (req_id == -1):
                logger.error("request id is missing")
                # set invalid request error code
                error_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
                return False, error_code

            question = input_json.get(const.QUESTION, None)
            # check input question is empty or not
            if (question is None) or (len(question.strip()) <= 0):
                logger.error("question is missing")
                # set invalid request error code
                error_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
                return False, error_code

            # Update the current context from the current request
            ker_cntxt = input_json.get(const.KER_CONTEXT, None)
            self.diag_mgr.validate_cntxt_and_fill(ker_cntxt)

            # validate part no
            is_partno_present = self.__validate_part_no(input_json, client_type)
            logger.debug("is_partno_present=%d", is_partno_present)
            if not is_partno_present:
                logger.error("Part no is missing")
                # set invalid request error code
                error_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
                return False, error_code

            is_valid, product, sub_prd_type, resp_code = self.__validate_product_type(input_json, client_type)
            logger.debug("is_valid:{0}, product:{1}, sub_prd_type:{2}, resp_code:{3}".format(is_valid, product,
                                                                                             sub_prd_type, resp_code))

            if resp_code == cs.ExternalErrorCode.MKG_SUCCESS:
                # validate classifier results
                input_json[cs.IOConstants.PRODUCT] = product
                input_json[cs.IOConstants.SUB_PRODUCT] = sub_prd_type
                is_valid = self.__validate_classifier_info(input_json, product)
                logger.debug("is_valid classifier_info =%d", is_valid)
                if not is_valid:
                    logger.error("Error in classifier_info")
                    # set invalid request error code
                    error_code = cs.ExternalErrorCode.MKG_INVALID_REQUEST
                    return False, error_code

                # validate similarity key
                is_valid, resp_code = self.__validate_similarity_key(input_json, product, sub_prd_type)
                logger.debug("is_valid similarity_key =%d", is_valid)
                if not is_valid:
                    logger.error("Error in similarity key info")
                    # set invalid request error code
                    error_code = resp_code
                    return False, error_code
            return is_valid, resp_code
        except jsonschema.exceptions.ValidationError as err:
            # incase of input request validation against json schema failed
            logger.exception("exception in json schema validation : " + str(err))
            return False, cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
        except Exception as e:
            # Any generic exception raise internal error
            logger.exception("exception in request format : " + str(e))
            return False, cs.ExternalErrorCode.MKG_INTERNAL_ERROR

    def validate_and_fill_nlp_data(self, input_json, client_type):
        validate_flag, resp_code = self.__validate_input_message_format(input_json, client_type)
        logger.debug("validate_flag:{0}, resp_code:{1}".format(validate_flag, resp_code))
        return validate_flag, resp_code