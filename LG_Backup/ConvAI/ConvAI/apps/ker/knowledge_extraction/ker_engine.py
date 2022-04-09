"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import logging as logger

from .constants import params as cs
from .constants.params import IOConstants as const
from .dialogue_manager.dialoguemanager import DialogueManager
from .nlp_engine_client import NlpEngineClient
from .requestvalidator import InputRequestSerializer
# from .mapping.model_no_mapper import close_match_model
import importlib
# constants for client types
HTML_CLIENT = 1
RCS_CLIENT = 2
KMS_CLIENT = 3

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class KerEngine(object):
    """
    defines the method to communicate to communicate with KER modules and get the
    output
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if KerEngine.__instance is None:
            KerEngine()
        return KerEngine.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if KerEngine.__instance is not None:
            logger.error("KerEngine is not instantiable")
            raise Exception("KerEngine is not instantiable")
        else:
            logger.debug("*** KerEngine constructor")
            # instance  of nlp engine client module
            self.nlp_eng_client = NlpEngineClient.get_instance()

            # instance of dialogue manager
            self.diag_mgr = DialogueManager.get_instance()
            self.diag_mgr.load_rcs_config()
            KerEngine.__instance = self

    def __update_response_code_in_error(self, resp_code, input_json):
        """
           This function is used to add response code in json and send back
           response
           Args:
                input_json : dict
                           Ker_engine input json
                resp_code : int
                           response code
           Returns:
               input_json : dict
                           resp_code updated json
        """
        input_json[cs.resp_code] = resp_code
        # add template error response as per resp_code
        resp_msg = cs.ExternalErrorMsgs.ERR_MSGS[resp_code][cs.ExternalErrorMsgs.MSG]
        input_json[cs.IOConstants.ANSWER] = resp_msg
        input_json[cs.IOConstants.HTTP_ERR_CODE] = cs.ExternalErrorMsgs.ERR_MSGS[resp_code][cs.ExternalErrorMsgs.HTTP_CODE]
        input_json[cs.IOConstants.RESP_MSG] = resp_msg
        return input_json

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
        logger.debug("Begin : input_json in __validate_model_no=%s" % (str(input_json)))
        # check model no in question
        model_no = self.diag_mgr.get_model_no(input_json[const.QUESTION], input_json[const.MODEL_NO], client_type)
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
        else:
            # check model no in context if the client is RCS or HTML
            if client_type == RCS_CLIENT or client_type == HTML_CLIENT:
                # validate model no in context
                res = self.diag_mgr.validate_model_no_from_context()
                if not res:
                    return False
                # update ker_context in input_json
                ker_context = self.diag_mgr.get_context()
                logger.debug("ker_context from diagmgr=%s" % str(ker_context))
                # update ker context
                input_json.update(ker_context)
                res = True
        logger.debug("End : __validate_model_no input_json=%s res=%d" % (str(input_json), res))
        return res

    def __validate_classifier_info(self, input_json):
        """
            This function is used to get validate classifier info
            Args:
                input_json : dict
                           Ker_engine input json
            Returns:
                res : bool
                    True/False
        """
        isvalid = False

        logger.debug("Begin : input_json in classifier_info=%s" % (str(input_json)))
        # get classifier info and assign None if key not present
        classifier_res = input_json.get(const.CLASSIFIER_INFO, None)
        logger.debug("classi_resp=%s", str(classifier_res))
        # check classifier key info and it has non-empty dictionary
        if (classifier_res is None) or (classifier_res is not None and not bool(classifier_res)):
            # call nlp_engine_client to get classifier_info
            classifier_res, class_resp_code = self.nlp_eng_client.get_classifier_output(input_json[const.QUESTION])
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
        logger.debug("section=%s sub-section=%s intent=%s",section,sub_section,intent)
        """
        # for spec section, section and follow_up is mandatory fields
        # for troubleshooting, section,sub_section and intent are mandatory fields
        # for operation section , intent,sub_section,ques_type and category are mandatory fields
        """
        if (section != cs.Section.SPEC or follow_up is None) and (
                (section != cs.Section.TROB) or (intent is None) or (sub_section is None)) and (
                (section != cs.Section.OPERATION) or (intent is None) or (sub_section is None) or (ques_type is None)
                or (category is None)):
            logger.debug("classifier info keys dict validation fails")
            isvalid = False
        else:
            isvalid = True

        if isvalid:
            # update classifier info key,value in dict
            input_json[const.CLASSIFIER_INFO] = classifier_res
        logger.debug("End : input_json in classifier_info=%s" % (str(input_json)))
        return isvalid

    def __validate_similarity_key(self, input_json, client_type, question):
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
        isvalid = False

        logger.debug("Begin : input_json in __validate_similarity_key=%s" % (str(input_json)))
        # get classifier info and assign None if key not present
        similarity_resp = input_json.get(const.SIMILARITY_KEY, None)
        logger.debug("similarity_resp=%s", str(similarity_resp))
        # check similarity key info and it has non-empty dictionary
        if (similarity_resp is None) or (similarity_resp is not None and (len(similarity_resp) <= 0)):
            # get product from dialogue manager to give to info engine to find similarity keys
            resp_code, product = self.diag_mgr.get_product_type(input_json[const.MODEL_NO], question,
                                                     input_json[const.KER_CONTEXT], client_type)
            logger.debug("product from dialogue manager=%s", product)
            # if product is not valid
            if (product is None) or (len(product.strip()) <= 0):
                logger.error("Dialogua manager returns no product")
                isvalid = False
                if (resp_code == cs.ResponseCode.CLIENT_ERROR) or (resp_code == cs.ResponseCode.CONNECTION_ERROR) or \
                    (resp_code == cs.ResponseCode.INTERNAL_ERROR):
                    return isvalid, cs.ExternalErrorCode.MKG_KG_CONNECTION_ERROR
                return isvalid, cs.ExternalErrorCode.MKG_QUERY_MODEL_NOT_FOUND
            # extract question from input_json
            question = input_json[const.QUESTION]
            isvalid = True
            # extract section from classifier info
            section = input_json[const.CLASSIFIER_INFO][cs.ProblemTypes.SECTION]
            # extract sub section from classifier info
            sub_section = input_json[const.CLASSIFIER_INFO][cs.ProblemTypes.SUB_SECTION]
            logger.debug("sub section : %s",sub_section)
            # call nlp_engine_client to get similarity_key
            similarity_key, simi_resp_code = self.nlp_eng_client.get_similarity_output(question, section, product)
            if similarity_key is None:
                # update status to return error code
                isvalid = False
                error_code = cs.ExternalErrorCode.internal_to_ext_err_code[simi_resp_code]
                return isvalid, error_code

            # update classifier info key,value in dict
            input_json[const.SIMILARITY_KEY] = similarity_key

        logger.debug("End : isvalid=%d input_json in __validate_similarity_key=%s" % (isvalid, str(input_json)))
        return isvalid, cs.ExternalErrorCode.MKG_SUCCESS

    def __validate_rcs_client_message(self, input_bot_request):
        """
            This function is used to validate RCS bot message and update
            input json with rcs modified request in case registarion message
            Args:
                input_bot_request : str
                           bot request message
            Returns:
                None
        """
        # if new_bot_user_initiation , set the request no to support text based
        modified_request, is_init_register = self.diag_mgr.is_bot_init_registration(input_bot_request)
        logger.debug("### bot_request=%s modified_request=%s is_init_register=%d", input_bot_request, modified_request,
                     is_init_register)
        if is_init_register:
            input_bot_request = modified_request
        return input_bot_request

    def __check_bot_registration(self, bot_request):
        """
           This function is used to get check bot request relates to registration or not
            Args:
                bot_request : str
                           bot request message
            Returns:
                res : bool
                    True/False
        """
        res = self.diag_mgr.check_bot_registration(bot_request)
        return res

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
        error_code = cs.ExternalErrorCode.MKG_SUCCESS

        req_id = input_json.get(const.REQ_ID, -1)
        if (isinstance(req_id, str)) or (req_id == -1):
            logger.error("request id is missing")
            # set invalid request error code
            error_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
            return False, error_code

        question = input_json.get(const.QUESTION, None)
        # check input question is empty or not
        if (question is None) or (len(question.strip()) <= 0):
            logger.error("Not a valid question")
            # set invalid request error code
            error_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
            return False, error_code

        if client_type == cs.ClientType.KMS:
            ker_cntxt = input_json.get(const.KER_CONTEXT, None)
            self.diag_mgr.validate_cntxt_and_fill(ker_cntxt)

        # validate model no
        is_modelno_present = self.__validate_model_no(input_json, client_type)
        logger.debug("is_modelno_present=%d", is_modelno_present)
        if not is_modelno_present:
            logger.error("Model no is not available")
            # set invalid request error code
            error_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
            return False, error_code

        # validate classifier results
        is_valid = self.__validate_classifier_info(input_json)
        logger.debug("is_valid classifier_info =%d", is_valid)
        if not is_valid:
            logger.error("Error in classifier_info")
            # set invalid request error code
            error_code = cs.ExternalErrorCode.MKG_INVALID_REQUEST
            return False, error_code

        # validate similarity key
        is_valid, resp_code = self.__validate_similarity_key(input_json, client_type, question)
        logger.debug("is_valid similarity_key =%d", is_valid)
        if not is_valid:
            logger.error("Error in similarity key info")
            # set invalid request error code
            error_code = resp_code
            return False, error_code
        return is_valid, error_code

    def __prepare_error_response_message(self, error_code, input_json):
        """
            Function is used to form error response as per error_code
            Args:
                error_code : int
                            Error code value
                input_json : dict
                           Ker_engine input json
            Returns:
                error_response : json string
                    json string of response for user query
        """
        logger.error("Not a valid question")
        # form bad request and send
        error_response = self.__update_response_code_in_error(error_code, input_json)
        error_response.pop(const.SIMILARITY_KEY, None)
        error_response.pop(const.CLASSIFIER_INFO, None)
        error_response[const.EXTRACTED_INFO] = {}
        return error_response

    def process_request(self, input_json, client_type):
        """
            Function is used to get validate input and get
            NLP modules output for any missing informations and get the
            result for user question
            Args:
                input_json : dict
                           Ker_engine input json
                client_type : int
                           HTML/RCS/KMS
            Returns:
                json_response : json string
                    json string of response for user query
        """
        ip_serializer = InputRequestSerializer(data=input_json)

        try:
            # validate the input request details using serializer
            if ip_serializer.is_valid():
                logger.debug("type of input_json=%s input=%s client_type=%d" % (type(input_json), str(input_json), client_type))
                # if client is rcs client, check for registration message or QA message
                if client_type == RCS_CLIENT:
                    input_bot_request = input_json[const.QUESTION]
                    bot_request = self.__validate_rcs_client_message(input_bot_request)
                    # check for bot register messages
                    res = self.__check_bot_registration(bot_request)
                    # if bot request is registration message
                    if res:
                        bot_response = self.diag_mgr.bot_registration(bot_request)
                        query_response = {}
                        query_response[cs.IOConstants.ANSWER] = bot_response
                        return query_response

                # validate input json and returns response if not valid
                is_valid, error_code = self.__validate_input_message_format(input_json, client_type)
                if not is_valid:
                    # prepare error response as per client type and return json str response
                    response_msg = self.__prepare_error_response_message(error_code, input_json)
                    return response_msg

                logger.debug("formed json=%s" % str(input_json))
                # extract informations from input json to call diag mgr
                question = input_json[const.QUESTION]
                model_no = input_json[const.MODEL_NO]
                classifier_info = input_json[const.CLASSIFIER_INFO]
                similarity_info = input_json[const.SIMILARITY_KEY]
                ker_cntxt = input_json[const.KER_CONTEXT]

                # call dialogue manager to get response
                query_response = self.diag_mgr.handle_user_query(question,
                                                                 classifier_info, similarity_info, model_no, client_type,
                                                                 ker_cntxt)
                logger.debug("response frm dialoguemanager : %s", query_response)
                return query_response
            else:
                logger.debug("validation failed")
                framed_resp = self.__update_response_code_in_error(cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING, input_json)
                return framed_resp
        except Exception as e:
            logger.exception("Exception in manage context : " + str(e))
            framed_resp = self.__update_response_code_in_error(cs.ExternalErrorCode.MKG_INTERNAL_ERROR,
                                                               input_json)
            return framed_resp

    def get_product_models(self):
        """
            call to get product models from dialogue manager
            Args: None
            Returns : dict
                     product models dictionary
        """
        return self.diag_mgr.get_product_models()

    def update_product_pref(self, json_obj):
        """
            call to get update preference json to maintain context
            Args: json_obj
                   context json
            Returns : int
                     status of preference update
        """
        return self.diag_mgr.update_product_pref(json_obj)

    def reset_preference(self):
        """
            call to reset preference
            Args: None
            Returns : int
                     status of preference update
        """
        return self.diag_mgr.reset_preference()

    def get_context(self):
        """
            call to get context from dialogue manager
            Args: None
            Returns : dict
                     context dictionary
        """
        return self.diag_mgr.get_context()

    def get_thinq_settings(self):
        """
            call to get thinq settings information
            Args: None
            Returns : dict
                     product db as dictionary
        """
        return self.diag_mgr.get_thinq_settings()

    def clear_thinq_settings(self):
        """
            call to clear thinq settings
            Args: None
            Returns : int
                     status of thinq settings clear
        """
        return self.diag_mgr.clear_thinq_settings()
