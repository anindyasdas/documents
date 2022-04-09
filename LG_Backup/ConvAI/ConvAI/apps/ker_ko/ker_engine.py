"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import copy
import json
import os
import importlib
import requests
from jsonschema import validate
from configparser import ConfigParser

from .components.mrc_qa.mrc_qa_engine import MrcQaEngine
from .components.passage_retrieval.bm25_retrieval import PassageRetrieval
from apps.ker_ko.components.passage_retrieval.bm25_tokenizers import white_space_tokenizer
from .ker_response_engine import KerResponseEngine
from .knowledge_extraction.constants import params as cs
from .knowledge_extraction.constants.params import IOConstants as const
from .knowledge_extraction.constants.params import GenericProductNameMapping
from .knowledge_extraction.info_extraction.subkey_extractor import SubKeysExtractor
from .knowledge_extraction.dialogue_manager.dialoguemanager import DialogueManager
from .nlp_engine_client import NlpEngineClient
from .knowledge_extraction.dialogue_manager.hybrid_approach_dialog_mgr import HybridApproachDialogManager
from .validation.input_validator import InputValidator

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

# constants for client types
HTML_CLIENT = 1
RCS_CLIENT = 2
KMS_CLIENT = 3

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, 'knowledge_extraction', 'config', 'configuration.ini')


class MrcQaThresholdException(Exception):
    pass


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
            logger.info("*** KerEngine Constructor")
            # instance  of nlp engine client module
            self.nlp_eng_client = NlpEngineClient.get_instance()

            # instance of dialogue manager
            self.diag_mgr = DialogueManager.get_instance()
            self.hybrid_approach_manager = HybridApproachDialogManager()
            KerEngine.__instance = self

            # urls for doc based search approach
            read_config = ConfigParser()
            read_config.read(CONFIG_PATH)
            self.url_for_get_doc_key_results = read_config.get('doc_config', 'graph_output')
            self.url_for_get_doc_manual_keys = read_config.get('doc_config', 'manual_key_output')
            self.url_for_get_passages = read_config.get('doc_config', 'get_manual_passages')
            self.headers = {'Content-Type': 'application/json'}
            # variable to differentiate first request or consequtive.
            # so that model no is appended for doc search approach
            self.is_first_request = True
            self.normalized_section_names_kor = {
                "문제 해결하기": ["troubleshooting", "문제 해결하기"],
                "사용하기": ["operation", "사용하기"],
                "관리하기": ["maintenance", "관리하기"],
                "설치하기": ["installation", "설치하기"],
                "알아보기": ["learn", "알아보기"],
                "안전을 위해 주의하기": ["safety", "안전을 위해 주의하기"],
                "제품 보증서 보기": ["warranty", "제품 보증서 보기"],
                "부록": ["appendix", "부록"],
                "LG ThinQ 사용하기": ["Using lg thinq", "LG ThinQ 사용하기"],
                "안전을 위한 주의 사항": ["safety precaution", "안전을 위한 주의 사항"]
            }
            """ to be deprecated need to define the function using the normalized_section_names_kor
            to compare value with key"""
            self.normalized_section_names_eng = {
                "Troubleshooting": ["troubleshooting", "문제 해결하기"],
                "Operation": ["operation", "사용하기"],
                "Maintenance": ["maintenance", "관리하기"],
                "Installation": ["installation", "설치하기"],
                "Learn": ["learn", "알아보기"],
                "Safety": ["safety", "안전을 위해 주의하기"],
                "Warranty": ["warranty", "제품 보증서 보기"],
                "Appendix": ["appendix", "부록"],
                "Using LG thinq": ["using lg thinq", "LG ThinQ 사용하기"],
                "Safety Precaution": ["safety precaution", "안전을 위한 주의 사항"]
            }

            self.url_for_get_doc_retrieval_results = read_config.get('doc_config', 'retrieval_output')

            self.resp_engine = KerResponseEngine()
            # flag to enable/disable recommendations
            self.enable_recommendations = False
            self.enable_kg_ts = False
            self.enable_doc_oper = True

            # For Handling Not Satisfied with the results
            self.korean_tokenizer = white_space_tokenizer
            self.bm25_passage_retriever = PassageRetrieval(self.korean_tokenizer)
            self.mrc_qa_module = MrcQaEngine()
            self.previous_model_no_to_reload_bm25 = ""
            self.list_of_passages = ""
            self.mrc_qa_threshold = 0.40

            self.filter_textsim_results_with_db = True
            # instance to extract sub product type from info extraction
            self.subkey_extractor = SubKeysExtractor.get_instance()
            self.input_validator = InputValidator()

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

    def get_data_from_db(self, product_entity_type, part_number, product, section, category):
        """
        list of data from DB
        """
        data = None
        response_code , data = self.hybrid_approach_manager.get_ts_section_causes(product_entity_type, section, part_number)
        logger.debug("Response from hybrid diag mgr response_code=%d data=%s",response_code, data)
        return response_code, data

    def _filter_data_by_db(self, input_json):
        """
        filter similarity data considering DB data for the specific part number
        """
        question = input_json[const.QUESTION]
        part_no = input_json[cs.IOConstants.PART_NO]
        product = input_json.pop(cs.IOConstants.PRODUCT)
        sub_prd_type = input_json.pop(cs.IOConstants.SUB_PRODUCT)
        section = input_json[const.CLASSIFIER_INFO][cs.ProblemTypes.SECTION]
        category = input_json[const.CLASSIFIER_INFO][cs.ProblemTypes.SUB_SECTION]
        similarity_key = input_json[const.SIMILARITY_KEY]

        logger.debug("question=%s part_no=%s product=%s section=%s category=%s textsim_results=%s",
                     question, part_no, product, section, category, similarity_key)
        product_entity_type = product
        # if product is kepler/washing machine family, identifying special type washer/dryer
        if sub_prd_type == GenericProductNameMapping.PRD_KEPLER or product == GenericProductNameMapping.WASHING_MACHINE_GEN_NAME:
            product_entity_type = self.subkey_extractor.get_kepler_section_type(question)
        elif (sub_prd_type == GenericProductNameMapping.MINI_WASHER_GEN_NAME) or \
                 (sub_prd_type == GenericProductNameMapping.TOP_LOADER_GEN_NAME):
            product_entity_type = [GenericProductNameMapping.WASHER_SEC_NAME]
        # get results from db if its related to problem/error/noise only as diagnose section has common across manuals
        if category not in [cs.ProblemTypes.DIAG_BEEP, cs.ProblemTypes.DIAG_THINQ]:
            response_code, data = self.get_data_from_db(product_entity_type, part_no, product, section, category)
            # if data from db is successful, filter text similarity results with db results
            if response_code == cs.ExternalErrorCode.MKG_SUCCESS:
                # logic comparison of textsim_results with data_from_db
                similarity_key = [i for i in similarity_key if (i['key'] in data)]
            logger.debug("filtered similarity key=%s", similarity_key)
            input_json[const.SIMILARITY_KEY] = similarity_key

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

    def process_request(self, input_json, client_type, hybrid_approach=False):
        """
            Function is used to get validate input and get
            NLP modules output for any missing informations and get the
            result for user question
            Args:
                input_json : dict
                           Ker_engine input json
                client_type : int
                           HTML/RCS/KMS
                hybrid_approach : bool
                           True/False
            Returns:
                json_response : json string
                    json string of response for user query
        """

        try:
            logger.debug("type of input_json=%s input=%s client_type=%d" % (type(input_json), str(input_json), client_type))
            logger.debug("formed json=%s" % str(input_json))
            # Get the hybrid approach response
            hybrid_response = input_json.get("hybrid_response", {})
            status_from_hybrid_response = hybrid_response.get("status", "")
            # we dont need to validate and call nlp engine for "see section contents"(if case) . for other scenarios like
            # "asking question", "satisfied with results" and normal qa query (else case) validation and call
            if hybrid_approach and status_from_hybrid_response == cs.IOConstants.HY_SEE_SECTION_CONTENTS:
                logger.debug("see section contents")
                classifier_res = input_json[const.CLASSIFIER_INFO]
                section = classifier_res.get(cs.ProblemTypes.SECTION, None)
                # To Search with the actual model number from the Db
                part_no = self.diag_mgr.get_part_no(input_json[const.QUESTION], input_json[cs.IOConstants.PART_NO])
                logger.debug("part_no :" + str(part_no))
                section_contents = self.hybrid_approach_manager.get_section_contents(section, part_no)
                # Now query_response will just be an answer
                query_response = section_contents
            else:
                # validate input json , get nlp modules and returns response if not valid
                is_valid, error_code = self.input_validator.validate_and_fill_nlp_data(input_json, client_type)
                if not is_valid:
                    # prepare error response as per client type and return json str response
                    query_response = self.__prepare_error_response_message(error_code, input_json)
                    return query_response

                if self.filter_textsim_results_with_db:
                    self._filter_data_by_db(input_json)

                query_response = self.__get_response_from_diag_mgr(client_type, hybrid_approach, hybrid_response,
                                                                   input_json, status_from_hybrid_response)
                logger.debug("response frm dialogue manager : %s", query_response)
            return query_response
        except Exception as e:
            logger.exception("Exception in system : " + str(e))
            query_response = {}
            query_response = self.__update_response_code_in_error(cs.ExternalErrorCode.MKG_INTERNAL_ERROR,
                                                               input_json)
            return query_response

    def __get_response_from_diag_mgr(self, client_type, hybrid_approach, hybrid_response, input_json,
                                     status_from_hybrid_response):
        # extract informations from input json to call diag mgr
        question = input_json[const.QUESTION]
        part_no = input_json[cs.IOConstants.PART_NO]
        classifier_info = input_json[const.CLASSIFIER_INFO]
        similarity_info = input_json[const.SIMILARITY_KEY]
        ker_cntxt = input_json[const.KER_CONTEXT]
        # Get the status from hybrid_response. Will be one of the following ['asking_question',
        # 'not_satisfied_with_results' 'satisfied_with_results']
        # TODO handle not_satisfied_with_results
        # call dialogue manager to get response
        if hybrid_approach and status_from_hybrid_response == cs.IOConstants.HY_RES_STATUS_ASKING_QUESTION:
            nlp_module_info = classifier_info, similarity_info
            query_response = self.hybrid_approach_manager.handle_user_query(question,
                                                                            nlp_module_info, part_no, client_type,
                                                                            ker_cntxt, hybrid_response)
        elif hybrid_approach and status_from_hybrid_response == cs.IOConstants.HY_RES_STATUS_SATISFIED:
            similarity_info = [{"key": hybrid_response[cs.IOConstants.HY_RES_CHOSEN_KEY_FROM_USER]}]
            query_response = self.diag_mgr.handle_user_query(question,
                                                             classifier_info, similarity_info, part_no, client_type,
                                                             ker_cntxt)
        else:
            query_response = self.diag_mgr.handle_user_query(question,
                                                             classifier_info, similarity_info, part_no, client_type,
                                                             ker_cntxt)
        return query_response

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

    def get_graphqa_mapped_keys(self, ker_request_json):
        """
        find top mapped keys from graphqa approach
        :param ker_request_json: json input
        :return: response_code : response code from ker engine
        :return top_most_matches : dict of top 5 predictions
        """
        logger.info("Begin: __get_graphqa_mapped_keys=%s", ker_request_json)

        query_response = self.process_request(ker_request_json, cs.ClientType.BNC,
                                                    hybrid_approach=True)
        logger.debug("__get_graphqa_mapped_keys response from ker_engine=%s", str(query_response))
        # if success response from ker_engine
        response_code = query_response[cs.resp_code]
        if response_code == cs.ExternalErrorCode.MKG_SUCCESS:
            user_question, resp_partno, hybrid_response = query_response[cs.IOConstants.QUESTION], \
                                                       query_response[cs.IOConstants.PART_NO], \
                                                       query_response[const.HYBRID_RESPONSE]
            # Get the list of top results from text similarity
            mapped_keys_and_scores_gqa = hybrid_response["mapped_keys"]
        else:
            mapped_keys_and_scores_gqa = {}
        logger.debug("mapped_keys_and_scores from graph qa:" + str(mapped_keys_and_scores_gqa))
        return response_code, mapped_keys_and_scores_gqa

    def get_docsearch_mapped_keys(self, ker_request_json):
        """
        Find top mapped keys from docsearch approach
        :param ker_request_json: json input
        :return: mapped_keys_and_scores_ea : dict of top 5 predictions
        """
        logger.info("__get_docsearch_mapped_keys Begin ker_request_json=%s", ker_request_json)
        user_question = ker_request_json[const.QUESTION]
        part_no = ker_request_json[cs.IOConstants.PART_NO]
        post_object = json.dumps({cs.IOConstants.PART_NO: part_no, const.QUESTION: user_question})
        # post request to doc search for doc key results
        response_doc_results = requests.post(self.url_for_get_doc_key_results, data=post_object,
                                             headers=self.headers)
        logger.debug("doc approach results=%s", str(response_doc_results))
        if "500" in str(response_doc_results):
            mapped_keys_and_scores_ea = {}
            response_code = cs.ExternalErrorCode.MKG_INTERNAL_ERROR
        else:
            response_doc_results = json.loads(response_doc_results.text)
            # Sample response will be in this format
            # {"answer":feature_val, "response_code":response_code, "standardized":standardized }
            mapped_keys_and_scores_ea = response_doc_results[const.HY_RESPONSE][cs.IOConstants.ANSWER]
            response_code = response_doc_results[const.HY_RESPONSE][cs.IOConstants.RESP_CODE]
            if mapped_keys_and_scores_ea is not None:
                mapped_keys_and_scores_ea = dict(
                    sorted(mapped_keys_and_scores_ea.items(), key=lambda item: float(item[1]), reverse=True))
            elif mapped_keys_and_scores_ea is None:
                response_code = cs.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND
                mapped_keys_and_scores_ea = {}
        logger.debug("mapped_keys_and_scores from embedding approach:" + str(mapped_keys_and_scores_ea))
        return response_code, mapped_keys_and_scores_ea

    def check_and_enable_approach(self, enable_kg_ts, enable_doc_oper, enable_doc, enable_kg, keys):
        """
        check the keys and section name and enable approaches based on section
        """
        # if its troubleshooting , disable doc
        if ((keys is not None) and len(keys) > 0) and (("Troubleshooting" in keys[0]) and (enable_kg_ts)):
            logger.debug("Disabled doc search for TS")
            enable_doc = False
        # if its operation, block KG based approach
        if ((keys is not None) and len(keys) > 0) and (("Operation" in keys[0]) and (enable_doc_oper)):
            logger.debug("Disabled KG approach for Operation")
            enable_kg = False
        return enable_doc, enable_kg

    def get_recommendation_for_keywords(self, keys):
        is_detergent_recom = False
        is_descaler_recom = False
        is_d_soil_recom = False
        is_softener_recom = False
        recommendation = []
        for key in keys:
            if (key in cs.RecommendationConstants.RECOMMENDATION_MAPPING["Detergent"]) and (
                    is_detergent_recom == False):
                recommendation.append(cs.RecommendationConstants.RECOMMENDATION_INFO["Detergent"])
                is_detergent_recom = True
            if key in cs.RecommendationConstants.RECOMMENDATION_MAPPING["Descaler"] and is_descaler_recom == False:
                recommendation.append(cs.RecommendationConstants.RECOMMENDATION_INFO["Descaler"])
                is_descaler_recom = True
            if key in cs.RecommendationConstants.RECOMMENDATION_MAPPING["LG D-Soil"] and is_d_soil_recom == False:
                recommendation.append(cs.RecommendationConstants.RECOMMENDATION_INFO["LG D-Soil"])
                is_d_soil_recom = True
            if key in cs.RecommendationConstants.RECOMMENDATION_MAPPING[
                "fabric softener"] and is_softener_recom == False:
                recommendation.append(cs.RecommendationConstants.RECOMMENDATION_INFO["fabric softener"])
                is_softener_recom = True
        return recommendation


    def recommendation_generator(self, query_mode, question, mapped_keys):
        keys = []
        if query_mode:
            keys.append(question)
            for section in mapped_keys.keys():
                for key in mapped_keys[section].keys():
                    keys.append(key)
        else:
            keys.append(question)
            keys.append(mapped_keys)

        recommendation = self.get_recommendation_for_keywords(keys)
        return recommendation


    def find_mapped_keys(self, ker_request_json):
        """
        find top mapped keys from graphqa & docsearch approach and return all top
        predictions
        :param ker_request_json: json input
        :return: mapped_keys : json with updated mapped keys
        """
        enable_kg = True
        enable_doc = True
        recommendation = []
        best_matches = []
        doc_keys = {}
        graphqa_keys = {}
        mapped_keys = {}

        logger.info("Begin mapped_key result=%s", ker_request_json)
        if "hybrid_response" not in ker_request_json:
            ker_request_json[const.HYBRID_RESPONSE] = {}

        ker_request_json[const.HYBRID_RESPONSE][const.HY_RES_STATUS] = \
            const.HY_RES_STATUS_ASKING_QUESTION
        # response of mapped keys
        response_code, graphqa_keys = self.get_graphqa_mapped_keys(ker_request_json)
        logger.debug("graphqa_keys=%s response_code=%d", graphqa_keys, response_code)

        # if response code is one of the below items, it will be same for doc search approach.
        # So if we get these error codes, we can return from here with error code

        failed_cases = any([response_code == cs.ExternalErrorCode.MKG_INVALID_REQUEST,
                 response_code == cs.ExternalErrorCode.MKG_QUERY_PART_NO_NOT_FOUND,
                 response_code == cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING])
        if failed_cases:
            return response_code, graphqa_keys, best_matches, recommendation

        # check if troubleshooting or operation and enable approaches
        keys = list(graphqa_keys.keys())
        enable_doc, enable_kg = self.check_and_enable_approach(self.enable_kg_ts, self.enable_doc_oper, enable_doc,
                                                                     enable_kg, keys)
        if not enable_kg:
            logger.debug("Disabled KG search")
            graphqa_keys = {}

        logger.debug("enable_kg =%d enable_doc=%d", enable_kg, enable_doc)
        response_code_doc = cs.ExternalErrorCode.MKG_SUCCESS
        if (enable_doc) or (len(keys) <= 0):
            logger.debug("Enabled doc search")
            response_code_doc, doc_keys = self.get_docsearch_mapped_keys(ker_request_json)
            logger.debug("doc_keys=%s", doc_keys)

        # TODO Create a function to decide the final response_code
        both_the_response_codes_are_failed = all([response_code != cs.ExternalErrorCode.MKG_SUCCESS,
                                                 response_code_doc != cs.ExternalErrorCode.MKG_SUCCESS])

        final_response_code = cs.ExternalErrorCode.MKG_SUCCESS
        if both_the_response_codes_are_failed:
            final_response_code = cs.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND

        # call new response engine
        if final_response_code is cs.ExternalErrorCode.MKG_SUCCESS:
            mapped_keys, best_matches = self.resp_engine.get_resp_for_mapped_keys(graphqa_keys, doc_keys)
            logger.debug("#####from response engine mapped_key result=%s best_matches=%s", mapped_keys, best_matches)
            logger.debug("from post process mapped_key result=%s", mapped_keys)
            if mapped_keys is None or len(mapped_keys) == 0:
                return cs.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND, mapped_keys, best_matches, recommendation
            if self.enable_recommendations:
                recommendation = self.recommendation_generator(True, ker_request_json[const.QUESTION],
                                                          mapped_keys)
        return final_response_code, mapped_keys, best_matches, recommendation

    def get_normalized_key_name(self, section_name, filtered_dict=None):
        if filtered_dict is None:
            filtered_dict = self.normalized_section_names_kor

        for normalized_section_name, different_section_names in filtered_dict.items():
            if any(section_name.lower() == x.lower() for x in different_section_names):
                return normalized_section_name
        return None

    def get_query_results_from_doc_based(self, request_json):
        """
        calls doc search api for user query and get answer
        :param ker_request_json: input json request
        :return answer : answer from doc approach
        """
        selected_info = request_json[const.QUERY][const.HY_SELECTED_OPTION]
        section_kor = selected_info[cs.ProblemTypes.SECTION]
        logger.debug("user selected section=%s", section_kor)
        # convert korean section name to english . so that down pipeline components will be able to process
        section = self.get_normalized_key_name(section_kor,
                                               self.normalized_section_names_eng)
        selected_info[cs.ProblemTypes.SECTION] = section

        selected_key = selected_info[cs.InfoKnowledge.KEY]
        ker_request_json = request_json[const.QUERY]

        user_question = ker_request_json[const.QUESTION]
        part_no = ker_request_json[cs.IOConstants.PART_NO]
        # matched_result = ker_request_json[const.HY_SELECTED_OPTION][cs.Section.OPERATION.lower()]
        # post request to doc search for doc manual answer results
        logger.debug("doc query result question=%s selected_key=%s", user_question, selected_key)
        selected_key = section_kor + " >> " + selected_key
        post_object = json.dumps(
            {cs.IOConstants.PART_NO: part_no, const.QUESTION: user_question, const.HY_MATCHED_KEY: selected_key})
        responce_doc_results = requests.post(self.url_for_get_doc_retrieval_results, data=post_object,
                                             headers=self.headers)
        logger.debug("1.Query Results from doc based=%s", str(responce_doc_results))
        responce_doc_results = json.loads(responce_doc_results.text)
        logger.debug("2.Query Results from doc based=%s", str(responce_doc_results))
        doc_response = responce_doc_results[const.HY_RESPONSE]
        logger.debug("doc_response from doc based=%s", str(doc_response))
        return doc_response


    def get_query_response_from_doc_based(self, ker_request_json, request_json, section, selected_key):
        # for troubleshooting section, call KG approach even if user selects doc approach
        if section.lower() == cs.Section.TROB.lower():
            ker_request_json[const.HYBRID_RESPONSE][const.HY_RES_CHOSEN_KEY_FROM_USER] = selected_key
            ker_request_json[const.HYBRID_RESPONSE][const.HY_RES_STATUS] = const.HY_RES_STATUS_SATISFIED
            query_response = self.process_request(ker_request_json, cs.ClientType.BNC,
                                                  hybrid_approach=True)
        else:
            # extract actual doc based keys taht has ">>" from user selected key
            # actual_key = self._get_normalized_key_name(selected_key, self.post_process_doc_keys)
            # actual_key = self.post_process_doc_keys[selected_key]
            request_json[const.QUERY][const.HY_SELECTED_OPTION][cs.InfoKnowledge.KEY] = selected_key
            query_response = self.get_query_results_from_doc_based(request_json)
        return query_response

    def _frame_section_hierarchy(self, extracted_info):
        """
        frame section hierarchy for the troubleshooting section partial xml extraction

        Args:
            extracted_info - extracetd info from the retrieval output
        Return:
            section hierarchy - Frmaed section hierarchy for troubleshooting
        """
        main_title = cs.ExtractionConstants.MAIN_TITLE_CHK_BFR_MALFUNCTION
        if cs.ExtractionConstants.STR_FLAG_DIA_SECTION in extracted_info['sub_section']:
            section_title = cs.ExtractionConstants.TITLE_DIA_FAULT
        else:
            section_title = cs.ExtractionConstants.TITLE_TROUBLESHOOTING
        logger.debug("section hierarchy extracted_info: %s",extracted_info)
        topic_title = cs.ExtractionConstants.ENG_TO_KOREAN_SEC_TRANSLATE[extracted_info['sub_section']]
        topic_title = "#".join(topic_title)
        problem = extracted_info['prob_value']
        cause = extracted_info['key_info']

        if problem.lower() == cause.lower():
            if cs.ExtractionConstants.STR_FLAG_DIA_SECTION in extracted_info['sub_section']:
                return "[\""+cs.ExtractionConstants.PROD_STR+"\"]"+"[\""+main_title+"\"]"+"[\""+section_title+"\"]"+"[\""+topic_title+"\"]"
            else:
                return "[\""+cs.ExtractionConstants.PROD_STR+"\"]"+"[\""+main_title+"\"]"+"[\""+section_title+"\"]"+"[\""+topic_title+"\"]"+"[\""+problem+"\"]"
        return "[\""+cs.ExtractionConstants.PROD_STR+"\"]"+"[\""+main_title+"\"]"+"[\""+section_title+"\"]"+"[\""+topic_title+"\"]"+"[\""+problem+"\"]"+"[\""+cause+"\"]"

    def _get_partnumber(self, model_no):
        """
        get the partnumber for the given model number

        Args:
            model_no: model number from user query
        Return:
            partnumber: retrieved partnumber from Db
        """
        resp = self.diag_mgr.get_partnumber(model_no)

        if resp[cs.resp_code] == cs.ResponseCode.KER_INTERNAL_SUCCESS:
            return resp[cs.resp_data]
        return None

    def get_mapped_model_no(self, model_no):
        return self.diag_mgr.get_model_no(model_no, None, None)

    def get_response_from_resp_engine(self, answer, approach, query_response,
                                      section):
        response_code = query_response[cs.resp_code]
        recommendation = []

        if response_code == cs.ExternalErrorCode.MKG_SUCCESS:
            if approach == "kg":
                db_results = query_response[const.ANSWER]
                title = query_response[const.EXTRACTED_INFO][cs.PROP_VALUE]
                section_hierarchy =None
                if section.lower() == "troubleshooting":
                    section_hierarchy = self._frame_section_hierarchy(query_response[const.EXTRACTED_INFO])
                logger.debug("section_hierarchy : %s",section_hierarchy)
                partnumber = query_response[cs.IOConstants.PART_NO]
                answer = self.resp_engine.get_resp_in_html(db_results, section, title, approach, section_hierarchy=section_hierarchy, partnumber=partnumber)
            else:
                answer_dict = query_response["answer"]
                response_dict = list(answer_dict.values())[0]
                logger.debug("response_dict: {}".format(response_dict))
                feature = response_dict["features"]
                logger.debug("feature: {}".format(feature))
                title = feature[0]["feature"]
                logger.debug("title: {}".format(title))
                is_standardized = query_response["standardized"]
                section_hierarchy = query_response["section_hierarchy"]
                logger.debug("section hierarchy in ker : %s", section_hierarchy)
                # ref title = "Results from Doc"
                partnumber = query_response[cs.IOConstants.PART_NO]
                answer = self.resp_engine.get_resp_in_html(answer_dict, section, title, approach, is_standardized, section_hierarchy, partnumber)
            if self.enable_recommendations:
                recommendation = self.recommendation_generator(False, "", title)
        else:
            # if any error , update answer with error description
            answer = cs.ExternalErrorMsgs.ERR_MSGS[response_code][cs.ExternalErrorMsgs.MSG]
        return response_code, answer, recommendation


    def get_query_response(self, request_json):
        """
        calls doc search / KG based api for user query and get answer
        :param request_json: input json request
        :return answer : answer from KG/doc approaches
        """
        answer = ""
        logger.info("request json=%s", request_json)
        selected_info = request_json[const.QUERY][const.HY_SELECTED_OPTION]
        section_kor = selected_info[cs.ProblemTypes.SECTION]
        logger.debug("user selected section=%s", section_kor)
        # convert korean section name to english . so that down pipeline components will be able to process
        section = self.get_normalized_key_name(section_kor,
                                               self.normalized_section_names_eng)
        # check approach...if no approach , by default calling KG approach
        approach = selected_info[const.HY_APPROACH]
        if approach is None or len(approach) == 0:
            approach = "kg"
        selected_key = selected_info[cs.InfoKnowledge.KEY]
        ker_request_json = request_json[const.QUERY]

        logger.debug("selected section=%s approach=%s key=%s", section, approach, selected_key)
        if const.HYBRID_RESPONSE not in ker_request_json:
            ker_request_json[const.HYBRID_RESPONSE] = {}
        query_response = {}
        if approach == "kg":
            selected_info[cs.ProblemTypes.SECTION] = section
            ker_request_json[const.HYBRID_RESPONSE][const.HY_RES_CHOSEN_KEY_FROM_USER] = selected_key
            ker_request_json[const.HYBRID_RESPONSE][const.HY_RES_STATUS] = const.HY_RES_STATUS_SATISFIED
            query_response = self.process_request(ker_request_json, cs.ClientType.BNC, hybrid_approach=True)
        elif approach == "doc":
            query_response = self.get_query_response_from_doc_based(ker_request_json, request_json, section,
                                                                    selected_key)
            # Adding the model number to the request json
            query_response[cs.IOConstants.PART_NO] = request_json[cs.IOConstants.QUERY][cs.IOConstants.PART_NO]

        selected_info[cs.ProblemTypes.SECTION] = section
        logger.debug("Response from KER =%s", query_response)
        response_code, answer, recommendation = self.get_response_from_resp_engine(answer, approach,
                                                                                   query_response,
                                                                                   section)
        # update section name to Korean for sending response
        selected_info[cs.ProblemTypes.SECTION] = section_kor

        # TODO Error handling
        logger.debug("End __get_query_response response_code=%d result=%s", response_code, answer)
        return response_code, answer, recommendation


    def get_section_content_from_doc(self, section, part_no):
        """
        get the manual keys from doc based approach and returns it
        Args:
            section:
            part_no:

        Returns:
            {
                "response_code": 0
                answer:{
                "notes before use":"doc",
                "Sorting laundry":"doc"
                }
            }

        """
        post_object = json.dumps(
            {cs.IOConstants.PART_NO: part_no, "section": section})
        logger.debug("section_content keys request to doc based=%s", str(post_object))
        responce_doc_results = requests.post(self.url_for_get_doc_manual_keys, data=post_object,
                                             headers=self.headers)
        responce_doc_results = json.loads(responce_doc_results.text)
        logger.debug("section_content keys response from doc based=%s", str(responce_doc_results))

        return responce_doc_results


    def get_section_content_answer(self, ker_request_json):
        """
        get manual keys from doc OR KG approach and returns the result
        Args:
            request_json
        Returns:
             {
            "category1_under_chosen_section": {"prob_or_section":"kg", "prob_or_section_2":"kg"},
            "category2_under_chosen_section": {"prob_or_section":"kg", "prob_or_section_2":"kg"}
            }
        """
        answer = {}

        logger.info("__get_section_content_answer request=%s", ker_request_json)
        part_no = ker_request_json.get(cs.IOConstants.PART_NO, None)
        selected_info = ker_request_json[const.HY_SELECTED_OPTION]
        section = selected_info.get(cs.ProblemTypes.SECTION, None)

        if part_no is None or section is None:
            return cs.ExternalErrorCode.MKG_INVALID_REQUEST, answer
        logger.debug("user selected section=%s", section)

        # retrieving l1,l2 keys for troubleshooting from KG and other sections from doc based approach
        if section == const.HY_TROUBLESHOOTING:
            if "hybrid_response" not in ker_request_json:
                ker_request_json[const.HYBRID_RESPONSE] = {}
            # update section and "see section" constants in ker_request_json to process in ker_engine
            ker_request_json[const.HYBRID_RESPONSE][const.HY_RES_STATUS] = \
                const.HY_SEE_SECTION_CONTENTS
            ker_request_json[const.CLASSIFIER_INFO] = {}
            ker_request_json[const.CLASSIFIER_INFO][cs.ProblemTypes.SECTION] = const.HY_TROUBLESHOOTING
            response = self.process_request(ker_request_json, cs.ClientType.BNC, hybrid_approach=True)
            logger.debug("response from Graphqa approach=%s", response)
        else:
            # Call doc based approach for unstructed sections
            response = self.get_section_content_from_doc(section, part_no)
            logger.debug("response from doc approach=%s", response)
        response_code = response[cs.resp_code]
        answer = response[const.ANSWER]
        logger.debug("__get_section_content_answer resp_code=%d answer=%s", response_code, answer)
        return response_code, answer

    def get_resp_for_manual_contents(self):
        """
            form the answer by supporting sections
            Args:
                None
            Returns:
                response_code : int
                answer : dict
        """
        response_code = cs.ExternalErrorCode.MKG_SUCCESS
        sec_keys = [const.HY_TS_SEC, const.HY_OPER_SEC, const.HY_INST_SEC, const.HY_MAIN_SEC]
        sec_values = [const.HY_TROUBLESHOOTING, const.HY_OPERATION, const.HY_INSTALLATION, const.HY_MAINTENANCE]
        # convert lists to dictionary
        answer = dict(zip(sec_keys, sec_values))
        return response_code, answer


    def form_response(self, request_json, request_type, answer, response_code, recommendation, best_matches):
        """
        forms response json from request and answer
        :param request_json : input json request
        :param request_type : str of request type
        :param answer : query answer
        :param best_matches : list of keys sorted
        :return response_json : json response of user query
        """
        logger.info("request_json=%s request_type=%s answer=%s best_matches=%s", str(request_json), request_type, answer, best_matches)
        response_json = copy.deepcopy(request_json)
        logger.debug("response from KER=%s", response_json)
        try:
            # update key
            response_json[const.HY_RESP_TYPE] = response_json.pop(const.HY_REQ_TYPE)

            response_json_query = response_json[const.QUERY]
            # Currently removing extracted_info and part number from outer json. If needed will enable later
            response_json_query.pop(const.HYBRID_RESPONSE, None)
            response_json_query.pop(cs.IOConstants.PART_NO, None)
            response_json_query.pop(const.CLASSIFIER_INFO, None)
            response_json_query.pop(const.SIMILARITY_KEY, None)

            if response_json[const.HY_RESP_TYPE] == const.HY_RES_STATUS_ASKING_QUESTION:
                response_json[const.QUERY][const.HY_BEST_MATCHES] = best_matches

            # TODO: Error codes handling
            response_json[const.QUERY][const.ANSWER] = answer
            response_json[const.QUERY][const.HY_RECOMMENDATION] = recommendation
            response_json[const.QUERY][const.RESP_CODE] = response_code
            response_json[const.QUERY][const.RESP_MSG] \
                = cs.ExternalErrorMsgs.ERR_MSGS[response_code][cs.ExternalErrorMsgs.MSG]
            # update content level
            if response_json[const.HY_RESP_TYPE] == const.HY_SEE_SECTION_CONTENTS:
                section = request_json[const.QUERY][const.HY_SELECTED_OPTION][cs.ProblemTypes.SECTION]
                logger.debug("while adding response, see_section_contents section=%s", section)
                if section == const.HY_TROUBLESHOOTING:
                    response_json[const.QUERY][const.HY_CONTENT_TYPE] = const.HY_CONTENT_2LEVEL
                else:
                    response_json[const.QUERY][const.HY_CONTENT_TYPE] = const.HY_CONTENT_1LEVEL
            # As KER component is updated to return response as json, currently below function call is commented
            logger.debug("Return response from KER=%s", response_json)
        except Exception as e:
            response_code = cs.ExternalErrorCode.MKG_INTERNAL_ERROR
            response_json[const.QUERY][const.RESP_CODE] = response_code
            response_json[const.QUERY][const.RESP_MSG] = cs.ExternalErrorMsgs.ERR_MSGS[response_code][
                cs.ExternalErrorMsgs.MSG]
            logger.exception("Some Error framing the Response KER=%s", str(e))

        return response_json

    def not_satisfied_with_results_response(self, request_json):
        """
        To handle not satisfied with results with MRC-QA
        Args:
            request_json: Incoming request

        Returns:
            the answer from MRC-qa and corresponding response code
        """

        final_response_code = cs.ExternalErrorCode.MKG_SUCCESS
        final_answer = ""
        logger.info("Incoming request_json KER: {}".format(request_json))
        try:
            # Get the following from request_json
            query_part = request_json.get("query", {})
            current_model_no = query_part.get(cs.IOConstants.PART_NO, "")
            user_question = query_part.get("question", "")

            # If the model number is same (Not changing) then don't call the Doc Based API to fetch the passages
            # Existing passages will be used

            # Get the passages from the Doc Search based on the model number and question
            get_new_passages_and_fit_bm25 = self.previous_model_no_to_reload_bm25 != current_model_no
            if get_new_passages_and_fit_bm25:
                # Get the new passages for the current model number
                self.list_of_passages = self.get_passages_from_doc_search(current_model_no)

                # Fit the BM25 model with the new passages
                self.bm25_passage_retriever.fit(self.list_of_passages)

                # Save the current model number to not fit the BM25 model again until unless model number changed
                self.previous_model_no_to_reload_bm25 = current_model_no

            # Get the most_similar from BM25 (Currently top 5)
            top_passages_relevant_to_question = self.bm25_passage_retriever.most_similar(user_question, topk=5)
            logger.debug("Top 5 passages from bm25 =%s", str(top_passages_relevant_to_question))

            # Give to MRC-QA
            # MRC QA takes input only in the form of strings:
            # TODO Check for alternative of calling MRC QA for each passage
            top_passages_relevant_to_question = self._pre_process_input_for_mrc_qa(top_passages_relevant_to_question)

            # Call the MRC-QA Module for fetching the relevant answer
            # Calls BM25 (Passage retrieval) --> Top k=1 relevant passages (Takes time for each new model number)
            answer_from_mrc_qa, confidence_score = self.mrc_qa_module.get_mrc_output(
                paragraph=top_passages_relevant_to_question,
                user_query=user_question)
            logger.debug("mrc qa answer: {}, confidence_score: {}".format(answer_from_mrc_qa, confidence_score))
            if confidence_score < self.mrc_qa_threshold:
                raise MrcQaThresholdException("Confidence of the answer: "
                                              "{} by MRC QA is less "
                                              "than Threshold :{}".format(confidence_score, self.mrc_qa_threshold))

            logger.debug("answer from mrc qa = %s", str(answer_from_mrc_qa))
        except KeyError as ke:
            logger.exception(ke)
            final_response_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
        except MrcQaThresholdException as me:
            logger.exception(me)
            final_response_code = cs.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND
        except Exception as e:
            # TODO Create a utility function to Map Exceptions to External Error Codes, so that  it can be reused
            # Ex: if isinstance(e, NameError) --> final_response_code = cs.ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING
            logger.exception(e)
            final_response_code = cs.ExternalErrorCode.MKG_RESPONSE_GENERATION_ERROR
        else:
            final_answer = answer_from_mrc_qa
            final_response_code = cs.ExternalErrorCode.MKG_SUCCESS

        return final_response_code, final_answer

    def _pre_process_input_for_mrc_qa(self, top_passages_relevant_to_question):
        """
        Preprocess the input as a proper paragraph for mrc_qa
        """
        pre_processed_text = ""
        if isinstance(top_passages_relevant_to_question, list):
            # Add the .(marks the completion of sentence) at the end if it not there for each sentence
            make_sentence_completion = lambda x: x.strip() + "." if x.strip()[-1] == "." else x.strip()
            top_passages_relevant_to_question = [make_sentence_completion(x) for x in top_passages_relevant_to_question]
            # Join them with a space
            pre_processed_text = " ".join(top_passages_relevant_to_question)
        return pre_processed_text

    def get_passages_from_doc_search(self, part_no):
        """
        Get all the text/manual data from doc based (Generally used for MRC_QA)
        Args:
            part_no: The part no for which the text data needs to be extracted

        Returns:
            all the manual data in text relevant to the model number
        """

        # TODO Add response code implementation once available in doc based
        post_object = json.dumps(
            {cs.IOConstants.PART_NO: part_no})
        logger.info("section_content keys request to doc based=%s", str(post_object))
        response_doc_results = requests.post(self.url_for_get_passages, data=post_object,
                                             headers=self.headers)
        doc_search_response = json.loads(response_doc_results.text)["response"]

        return doc_search_response
