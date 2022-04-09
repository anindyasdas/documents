# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk
"""
import json
import logging as logger
import re


import spacy
from spacy_langdetect import LanguageDetector


from .preference import Preference
from .modelno_handler import ModelNoHandler
from .product_handler import ProductHandler
from .unithandler import UnitHandler
from ..constants import params as cs
from ..knowledge_retrieval_engine import KnowledgeRetriever
from ..response.response_engine import ResponseEngine
from .spec_key_classifier import SpecificationKeyIdentifier
from .context_manager import ContextManager
from .product_classifier import ProductClassifier
from .speckeyextractor import SpecKeyExtractor
from ..response.response_builder import ResponseBuilder
from ..constants.params import GenericProductNameMapping
logger = logger.getLogger("django")

class DialogueManager(object):
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if DialogueManager.__instance is None:
            DialogueManager.__instance = DialogueManager()
        return DialogueManager.__instance

    def __init__(self):
        if DialogueManager.__instance is not None:
            logger.error("KerEngine is not instantiable")
            raise Exception("KerEngine is not instantiable")
        else:
            self.part_no = ""
            self.spec_key = ""
            self.product_type = ""
            self.sub_product_type = ""
            self.unit = ""
            self.user_query = ""
            self.use_info = ""
            self.ques_topic = ""
            self.question_level = ""
            self.response = ""
            self.last_valid_response = ""
            self.previous_question = ""
            self.last_valid_dict_response = ""
            self.last_valid_similarity_key = ""
            self.final_response = ""
            self.question_level_3 = "L3"
            self.template_question = ""
            # response string modified for data not found
            # self.data_not_found = "Data not found"
            self.data_not_found = "Mentioned details not able to find"
            self.no_part_no = "Part No not present."
            self.no_model_req = "Model No not present in request."
            self.no_prd_detail = "Product Detail not available"
            self.data_not_available = "Data not available"
            self.invalid_query = "Invalid Query"
            self.issue_in_module = "There is issue in retrieving the detail"
            self.ERROR_CASE = 255
            self.follow_up_question = 256
            self.product_key = 'Products'
            self.model_key = 'model'
            # REference self.modelno_handler = ModelNoHandler()
            self.unit_handler = UnitHandler()
            self.resp_engine = ResponseEngine()
            self.product_handler = ProductHandler()
            self.spec_key_identifer = SpecificationKeyIdentifier()
            self.context_manager = ContextManager()
            self.KNOWLEDGE_RETRIEVER = KnowledgeRetriever.get_instance()
            Preference.intialize_preference()
            # rcs models dict
            self.models_dict = {}
            self.json_builder = None
            self.bot_register = None
            # variable to differentiate whom sent request to KER server bot/html
            # by default html
            self.request_from = cs.ClientType.HTML
            self.register_request_no = 0
            # instance for product classifier
            self.product_classifier = ProductClassifier()
            self.spec_key_extractor = SpecKeyExtractor()
            self.nlp = spacy.load('en')
            self.nlp.add_pipe(LanguageDetector(), name='language_detector', last=True)
            self.resp_builder = ResponseBuilder()
            self.get_product_models()

    def _get_lang_for_user_query(self, user_query):
        """
        get the language of the user query

        Args:
            user_query: Query from user
        return:
            return True if language supported
            return False if language not supported
        """
        doc = self.nlp(user_query)
        lang_details = doc._.language
        logger.debug("identified lang : %s", lang_details)

        if (lang_details['language'] == "en") or (lang_details['language'] == "ko"):
            return True

        return False

    def validate_cntxt_and_fill(self, ker_cntxt):
        """
        validate whether the context from user is proper format or not
        Args:
            ker_cntxt: local context from the request
        """

        if (ker_cntxt is not None) and (len(ker_cntxt.keys()) > 0):
            prd_type = ker_cntxt[cs.IOConstants.PRODUCT]

            if len(prd_type.strip()) > 0:
                Preference.update_pre_prd(prd_type)
                self.context_manager.update_partno_context(ker_cntxt[cs.IOConstants.PART_NO], prd_type)
                self.context_manager.update_spec_key_context(ker_cntxt[cs.IOConstants.SPEC_KEY], prd_type)
                self.context_manager.update_product_context(prd_type, prd_type)
                self.context_manager.update_unit_context(ker_cntxt[cs.IOConstants.UNIT])
                self.last_valid_response = [ker_cntxt[cs.IOConstants.PREV_ANSWER]]
                self.previous_question = ker_cntxt[cs.IOConstants.PREV_QUESTION]
            else:
                self.context_manager.clear_context()
        else:
            self.context_manager.clear_context()

    def _manage_context(self, lpart_no, user_query, classifier_info, similarity_output, ker_cntxt=None):
        """
        Check the context based on the product type,model no in user_query

        Args:
            lmodel_no: model no from ui
            user_query:user question
            ques_topic:Specification or Troubleshooting.
            question_level:L1 ,L2 or L3.
        Return:
            model_no:str
            template_resp : str
            extracted_knowledge : str
            dict_resp : dict
            query_key_mapping : dict
        """
        try:

            if not self._get_lang_for_user_query(user_query):
                # If user query is not in supported language
                logger.debug("Query language not supported")
                # Will be enabled in future if required
                # ker_cntxt = self._get_cur_ker_context()
                # return self.resp_builder.generate_response(cs.ResponseCode.LANG_NOT_SUPPORTED, ker_cntxt, user_query,
                #                                            self.request_from, None)

            dict_resp = {}
            self.user_query = user_query
            self.product_type = None
            template_resp, similarity_key, dict_resp, query_key_mapping = None, None, None, None
            logger.debug("UI lpart_no no : %s", lpart_no)

            self.context_manager.clear_context()
            self.validate_cntxt_and_fill(ker_cntxt)

            self.part_no = self.get_part_no(user_query, lpart_no)

            logger.debug("part_no: %s", self.part_no)

            # get the product type and model no number based on prd type
            self._check_product_context(user_query, self.part_no)

            logger.debug("part_no: %s", self.part_no)
            vpart_no, fresp, temp_ques, _, _, resp_code = self._validate_user_request()

            if resp_code != cs.ResponseCode.SUCCESS:
                ker_cntxt = self._get_cur_ker_context()
                return self.resp_builder.generate_response(cs.ResponseCode.INPUT_PARAM_MISSING, ker_cntxt,
                                                           user_query, self.request_from, self.part_no)

            if (self.part_no is None) or (len(self.part_no.strip()) == 0):
                self.final_response = self.no_part_no
                self.template_question = self.no_part_no

                ker_cntxt = self._get_cur_ker_context()
                return self.resp_builder.generate_response(cs.ResponseCode.INPUT_PARAM_MISSING, ker_cntxt,
                                                           user_query, self.request_from, self.part_no)
            else:
                logger.debug("final mapped_part_no: %s", self.part_no)
                topic = classifier_info[cs.ProblemTypes.SECTION]
                if topic is not None:
                    return self._handle_user_query(user_query, topic, classifier_info, similarity_output)
        except Exception as e:
            logger.exception("Exception in manage context : " + str(e))
            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(cs.ResponseCode.INTERNAL_ERROR, ker_cntxt,
                                                       user_query, self.request_from, self.part_no)

    def _validate_user_request(self):
        """
        validate whether the user request contains the
        :return:
        """
        if (self.part_no is None) or (len(self.part_no.strip()) == 0):
            logger.debug("model no is none")
            # get product type from preference
            self.product_type = Preference.get_pre_prd()
            if (self.product_type is not None) and (len(self.product_type) > 0):
                pref_part_no = Preference.get_partno_pref_value(self.product_type)
                self.part_no = self.get_part_no(None, pref_part_no)
                self.sub_product_type = Preference.get_product_pref_value(self.product_type)
            else:
                logger.debug('Product frm Preference is empty')
                self.final_response = self.invalid_query
                self.template_question = self.invalid_query
                # When preference is empty, start product registration (RCS scenario)
                return None, self.final_response, self.template_question, "", "", cs.ResponseCode.INVALID

        return "", "", "", "", "", cs.ResponseCode.SUCCESS

    def _handle_user_query(self, luser_query, topic, classifie_op, similarity_key):
        if topic == cs.SPEC_SECTION:
            return self._handle_spec_query(luser_query, topic, classifie_op, similarity_key)

        elif (topic.lower() == cs.TROUBLESHOOTING.lower()) or (topic == cs.FAQ) or (
                topic.lower() == cs.OPERATION.lower()):
            return self._handle_trob_query(luser_query, topic, classifie_op, similarity_key)
        else:
            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(cs.ResponseCode.SECTION_NOT_SUPPORTED, ker_cntxt,
                                                       user_query, self.request_from, self.part_no)

    def _handle_trob_query(self, luser_query, topic, classifie_op, similarity_key):

        # finding closely matched model number using the mapper module
        """
        Future reference:
        if self.product_type is not None:
            matched_model_number, prd_type = close_match_model(self.modelno, self.product_type)
            logger.debug("closely matched model number : %s", matched_model_number)
            self.modelno, self.actual_modelno =
            self.modelno_handler.extract_map_model_no(matched_model_number, self.models_dict)
        """

        # handle the troubleshooting related questions
        resp, prd_type, sim_key, dict_resp = self._call_retrieval_engine(luser_query, self.part_no,
                                                                         self.product_type, classifie_op,
                                                                         similarity_key)
        self.product_type = prd_type
        resp_tuple = resp, luser_query, topic, dict_resp, sim_key, self.product_type, self.sub_product_type
        return self._execute_on_resp_code(resp_tuple)

    def _handle_spec_query(self, luser_query, topic, classifie_op, similarity_key): # pragma: no cover
        """
        Handles the context management for the specification related query

        Args:
            luser_query: user query
            topic: classified topic
            classifie_op: output of classifier module

        return:
            model no - model number identified
            template resp - template response
            similarity key: text similarity output
            dict_resp - framed for response engine
            resp code - response code
        """
        # handle the specification questions
        # check specification related keyword in query or not
        if self.spec_key_identifer.check_spec_key_in_query(luser_query):
            # if follow_up == False:
            resp, prd_type, sim_key, dict_resp = self._call_retrieval_engine(luser_query,
                                                                             self.part_no,
                                                                             self.product_type,
                                                                             classifie_op,
                                                                             similarity_key)
            self.product_type = prd_type
            resp_tuple = resp, luser_query, topic, dict_resp, sim_key, prd_type, self.sub_product_type
            return self._execute_on_resp_code(resp_tuple)
        else:
            # if specification key is not there in query consider that as follow up question
            self.part_no, self.last_valid_similarity_key, dict_resp, dummy = self._handle_specification_follow_up_case(
                luser_query, topic, self.product_type, self.sub_product_type)
            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(cs.ResponseCode.SUCCESS, ker_cntxt, luser_query
                                                       , self.request_from, self.part_no,
                                                       topic=topic, dict_resp=dict_resp,
                                                       similarity_key=self.last_valid_similarity_key)

    def _call_retrieval_engine(self, user_query, part_no, prod_type, classifie_op, similarity_key):
        """
        invoke the retrieval engine for te user query

        Args:
            user_query - query from user
            ques_topic - topic classified
            product_type - product type identified from question
            sub_prd_type - sub product type like dinning fridge,kitchen ...
            classifie_op - topic classifier output
        Returns:
            resp -SUCEESS or DATA_NOT_FOUND
            product type- product type identifed from question
            similarity key - text similarity result
            dict resp - frmaed for the response engine
        """
        if (prod_type is not None) and (len(prod_type.strip()) > 0):
            self.context_manager.update_product_context(prod_type, prod_type)
            self.context_manager.update_partno_context(self.part_no)

        resp_code, prod_type, sub_prd = self._get_prd_type(self.part_no)
        json_response = self.KNOWLEDGE_RETRIEVER.retrieve_knowledge(
            user_query,
            self.part_no,
            prod_type, sub_prd, classifie_op, similarity_key)
        # testing json_response = {}
        #
        # with open("sample_json_opr.json", "r") as pf:
        #     json_response = json.load(pf)

        logger.debug('retrieved knowledge: %s', json_response)
        json_response = json.loads(json_response)
        if json_response[cs.resp_code] == cs.SUCCESS:
            # If retrieval gives valid response for question
            product_type, similarity_key, dict_resp = self._parse_json_from_retrieval_engine(json_response)
            return cs.SUCCESS, product_type, similarity_key, dict_resp

        elif json_response[cs.resp_code] == cs.ResponseCode.DATA_NOT_FOUND:
            # If retrieval engine couldn't able to find response
            if self.request_from != cs.ClientType.KMS:
                self._update_context(json_response)
            similarity_key = json_response[cs.resp_data][cs.RespKeys.EXTRACTED_INFO]
            return cs.ResponseCode.DATA_NOT_FOUND, prod_type, similarity_key, cs.ResponseCode.DATA_NOT_FOUND

        elif json_response[cs.resp_code] == cs.ResponseCode.BAD_RESPONSE:  # Data not available case
            similarity_key = json_response[cs.resp_data][cs.RespKeys.EXTRACTED_INFO]
            return cs.ResponseCode.BAD_RESPONSE, prod_type, similarity_key, None

        elif json_response[cs.resp_code] == cs.ResponseCode.INTERNAL_ERROR:
            # Error case with response code other than success and DATA not found case
            return cs.ResponseCode.INTERNAL_ERROR, prod_type, json_response[cs.error_msg], json_response[cs.error_msg]
        else:
            return json_response[cs.resp_code], prod_type, json_response[cs.error_msg], json_response[cs.error_msg]

    def _update_context(self, json_response):
        """
        Update the context management detail

        Args:
            json_response - response from retrieval engine
        """
        prd_type = json_response[cs.resp_data][cs.RespKeys.DB_RESP][cs.RS_PRODUCT_TYPE]
        # testing prd_type = Preference.get_pre_prd()
        # testing model_no = json_response[cs.resp_data][cs.RespKeys.DB_RESP][cs.MODEL_TR]

        if (prd_type is not None) and (len(prd_type.strip()) > 0):
            part_no = self.part_no
            Preference.update_pre_prd(prd_type)

            if part_no is not None:
                self.context_manager.update_partno_context(part_no, prd_type)

        if self.sub_product_type is not None:
            self.context_manager.update_product_context(prd_type, self.sub_product_type)
        else:
            self.context_manager.update_product_context(prd_type, prd_type)

    def _execute_on_resp_code(self, resp_tuple):
        """
        handle the response for the user query based on the response code
        Args:
            user_query - query from user
            ques_topic - topic classified
            product_type - product type identified from question
            sub_prd_type - sub product type like dinning fridge,kitchen ...
        Return:
            model no - model no
            template resp - framed response
            similarity resp - similarity response from retrieval engine
            dict_resp - framed for response engine
        """
        resp_code, user_query, ques_topic, dict_resp, similarity_key, prd_type, sub_prd_type = \
            resp_tuple[0], resp_tuple[1], resp_tuple[2], resp_tuple[3], resp_tuple[4], resp_tuple[5], resp_tuple[6]

        if resp_code == cs.SUCCESS:
            if ques_topic == cs.SPEC_SECTION:
                self.part_no, similarity_key, dict_resp, dummy = self._handle_specification_success_case(
                    user_query, dict_resp,
                    ques_topic, similarity_key,
                    prd_type, sub_prd_type)

                ker_cntxt = self._get_cur_ker_context()
                return self.resp_builder.generate_response(cs.ResponseCode.SUCCESS, ker_cntxt,
                                                           user_query, self.request_from, self.part_no,
                                                           topic=ques_topic, dict_resp=dict_resp,
                                                           similarity_key=similarity_key)

            elif (ques_topic.lower() == cs.TROUBLESHOOTING.lower()) or (ques_topic == cs.FAQ) or (
                    ques_topic.lower() == cs.OPERATION.lower()):
                self.part_no, similarity_key, dict_resp, dummy = self._handle_trob_opr_success_case(
                    user_query, dict_resp, ques_topic, similarity_key, prd_type,
                    sub_prd_type)

                ker_cntxt = self._get_cur_ker_context()
                return self.resp_builder.generate_response(cs.ResponseCode.SUCCESS, ker_cntxt,
                                                           user_query, self.request_from, self.part_no,
                                                           topic=ques_topic, dict_resp=dict_resp,
                                                           similarity_key=similarity_key)

        elif resp_code == self.follow_up_question:
            self.part_no, self.last_valid_similarity_key, dict_resp, dummy = self._handle_specification_follow_up_case(
                user_query, ques_topic, prd_type, sub_prd_type)

            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(cs.ResponseCode.SUCCESS, ker_cntxt,
                                                       user_query, self.request_from, self.part_no,
                                                       topic=ques_topic, dict_resp=dict_resp,
                                                       similarity_key=self.last_valid_similarity_key)

        elif resp_code == cs.ResponseCode.DATA_NOT_FOUND:
            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(cs.ResponseCode.DATA_NOT_FOUND, ker_cntxt,
                                                       user_query, self.request_from, self.part_no,
                                                       topic=ques_topic, dict_resp=dict_resp,
                                                       similarity_key=similarity_key)

        elif resp_code == cs.ResponseCode.BAD_RESPONSE:  # Data not available case
            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(cs.ResponseCode.BAD_RESPONSE, ker_cntxt,
                                                       user_query, self.request_from, self.part_no,
                                                       topic=ques_topic, dict_resp=dict_resp,
                                                       similarity_key=similarity_key)

        elif resp_code == cs.ResponseCode.INTERNAL_ERROR:  # internal error from retrieval engine
            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(cs.ResponseCode.INTERNAL_ERROR, ker_cntxt,
                                                       user_query, self.request_from, self.part_no,
                                                       topic=ques_topic, dict_resp=dict_resp,
                                                       similarity_key=similarity_key)
        else:
            ker_cntxt = self._get_cur_ker_context()
            return self.resp_builder.generate_response(resp_code, ker_cntxt,
                                                       user_query, self.request_from, self.part_no,
                                                       topic=ques_topic, dict_resp=dict_resp,
                                                       similarity_key=similarity_key)

    def _handle_trob_opr_success_case(self, user_query, dict_resp, ques_topic, similarity_key, product_type,
                                      sub_prd_type):
        """
        handle the success case of the troubleshooting question
        Args:
            user_query - query from user
            ques_topic - topic classified
            product_type - product type identified from question
            sub_prd_type - sub product type like dinning fridge,kitchen ...
        Returns:
            model no - model no
            template resp - framed response
            similarity resp - similarity response from retrieval engine
            dict_resp - framed for response engine

        """
        Preference.update_pre_prd(product_type)
        if sub_prd_type is not None:
            self.context_manager.update_product_context(product_type, sub_prd_type)
        else:
            self.context_manager.update_product_context(product_type, product_type)
        self.context_manager.update_partno_context(self.part_no, product_type)
        if sub_prd_type is not None:
            lproduct_type = sub_prd_type
        else:
            lproduct_type = product_type

        template_resp = self._frame_and_make_response(self.part_no, ques_topic, dict_resp, lproduct_type,
                                                      similarity_key)

        self.last_valid_response = [template_resp]
        self.previous_question = user_query
        logger.info(
            "template_resp:{0}, similarity_key:{1}, dict_resp:{2}".format(template_resp, similarity_key, dict_resp))
        return self.part_no, similarity_key, dict_resp, None

    def _handle_specification_success_case(self, user_query, dict_resp, ques_topic, similarity_key, product_type,
                                           sub_prd_type): # pragma: no cover
        """
        handle the response for the questions with the valid specificatin key

        Args:
            user_query - query from user
            ques_topic - topic classified
            product_type - product type identified from question
            sub_prd_type - sub product type like dinning fridge,kitchen ...
        Returns:
            model no - model no
            template resp - framed response
            similarity resp - similarity response from retrieval engine
            dict_resp - framed for response engine
        """
        spec_key = self._get_spec_key_frm_resp(dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.RESPONSE_KEY])
        Preference.update_pre_prd(product_type)
        self.context_manager.update_partno_context(self.part_no, product_type)
        self.context_manager.update_product_context(product_type, product_type)

        if sub_prd_type is not None:
            self.context_manager.update_product_context(product_type, sub_prd_type)

        if len(spec_key.strip()) > 0:
            self._check_spec_key(spec_key, product_type, user_query)
            spec_question_response_list = self._get_value_from_dict(dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE])
            if len(spec_question_response_list) >= 0:
                self.spec_key = self._get_spec_key_frm_resp(dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.RESPONSE_KEY])
                self.last_valid_response = spec_question_response_list
                self.previous_question = user_query
                self.last_valid_dict_response = dict_resp
                self.last_valid_similarity_key = similarity_key

                logger.debug("success case bfr : %s", self.last_valid_response)

                converted_value = self._check_unit_context_from_query(user_query, self.last_valid_response,
                                                                      self.spec_key, self.product_type)
                dict_resp = self.last_valid_dict_response
                if converted_value is not None:
                    # handle valid converted value
                    dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE] = self._fill_specification_value(
                        dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE], converted_value)
                    if self.request_from == cs.ClientType.KMS:
                        self.last_valid_response = converted_value

                logger.debug("success case aft : %s", self.last_valid_response)

                dict_resp = self._make_dict_response(self.part_no, cs.SPEC_SECTION,
                                                     dict_resp, product_type)
                logger.info("similarity_key:{0}, dict_resp:{1}".format(similarity_key, dict_resp))
                return self.part_no, similarity_key, dict_resp, None
            else:
                logger.debug("Invalid spec key from retrieval engine : %s", spec_key)
                return self.part_no, similarity_key, None, None

        logger.debug("Invalid spec key from retrieval engine : %s", spec_key)
        return self.part_no, similarity_key, None, None

    def _fill_specification_value(self, spec_values, converted_value): # pragma: no cover
        """
        fill the converted value in the dictionary

        Args:
            spec_value - actual value from retrieval engine
            converted_value - converted value
        Return:
            dict - filled value in actual response
        """
        for value, cvalue in zip(spec_values, converted_value):
            value['value'] = cvalue
        return spec_values

    def _handle_specification_follow_up_case(self, user_query, ques_topic, product_type, sub_prd_type): # pragma: no cover
        """
        handle the conversation flow like "tell me in mm" question to frame the response and convert
        the response to required unit

        Args:
            user_query - query from user
            ques_topic - topic classified
            product_type - product type identified from question
            sub_prd_type - sub product type like dinning fridge,kitchen ...
        Returns:
            model no - model no
            template resp - framed response
            similarity resp - similarity response from retrieval engine
            dict_resp - framed for response engine
        """
        dict_resp = self.last_valid_dict_response
        spec_key = self._get_spec_key_frm_resp(dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.RESPONSE_KEY])
        Preference.update_pre_prd(product_type)
        self.context_manager.update_modelno_context(self.part_no, product_type)

        if sub_prd_type is not None:
            self.context_manager.update_product_context(product_type, sub_prd_type)
        else:
            self.context_manager.update_product_context(product_type, product_type)

        self.context_manager.update_modelno_context(self.part_no, product_type)
        if len(spec_key.strip()) > 0:
            logger.debug("follow up case : %s", self.last_valid_response)
            self.previous_question = user_query
            self.context_manager.update_spec_key_context(self.spec_key, product_type)
            converted_value = self._check_unit_context_from_query(user_query, self.last_valid_response,
                                                                  self.spec_key, self.product_type)
            if converted_value is not None:
                # handle valid converted value
                dict_resp = self.last_valid_dict_response
                dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE] = self._fill_specification_value(
                    dict_resp[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE], converted_value)
                if self.request_from == cs.ClientType.KMS:
                    self.last_valid_response = converted_value
            else:
                dict_resp = self.last_valid_dict_response

            dict_resp = self._make_dict_response(self.part_no, cs.SPEC_SECTION,
                                                 dict_resp, product_type)
            logger.info("similarity_key:{0}, dict_resp:{1}".format(self.last_valid_similarity_key, dict_resp))
            return self.part_no, self.last_valid_similarity_key, dict_resp, None
        else:
            logger.debug("Invalid spec key from previous response : %s", spec_key)
            return self.part_no, None, None, None

    def _get_value_from_dict(self, values): # pragma: no cover
        """
        get the list of values from the specification response
        Args:
            values - value from specification response for "value" key
        Return:
            List of specification response values
        """
        list_values = []
        for value in values:
            list_values.append(value[cs.VALUE])

        return list_values

    def _get_spec_key_frm_resp(self, resp): # pragma: no cover
        """
        retrieve the specifcation key from the response in dict format
        Args:
            resp - "response_key" value from response
        Return:
            Specification key string
        """
        print("spec reps : ", resp)
        spec_key = ""
        key = resp["key"]

        if (len(key.strip()) > 0):
            spec_key = self.spec_key_extractor.extract_spec_key(resp)
        return spec_key

    def _parse_json_from_retrieval_engine(self, json_data):
        """
        parse the response from the json sent by retrieval engine

        Args:
            json_data - json from the retrieval engine

        Return:
            product_type - produt type extracted frm the response
            similarity_key - text similarity module output
            dict_resp - dict resp framed for response engine

        """
        dict_resp = {}
        product_type = ""
        similarity_key = {}

        product_type = json_data[cs.resp_data][cs.RespKeys.DB_RESP][cs.RS_PRODUCT_TYPE]
        dict_resp[cs.XMLTags.TROUBLESHOOT_TAG] = json_data[cs.resp_data][cs.RespKeys.DB_RESP][
            cs.XMLTags.TROUBLESHOOT_TAG]
        dict_resp[cs.XMLTags.SPECIFICATION_TAG] = json_data[cs.resp_data][cs.RespKeys.DB_RESP][
            cs.XMLTags.SPECIFICATION_TAG]
        dict_resp[cs.XMLTags.OPERATION_TAG] = json_data[cs.resp_data][cs.RespKeys.DB_RESP][cs.XMLTags.OPERATION_TAG]
        similarity_key = json_data[cs.resp_data][cs.RespKeys.EXTRACTED_INFO]

        logger.debug("pr_type : %s", product_type)

        return product_type, similarity_key, dict_resp

    def _frame_and_make_response(self, part_no, ques_topic, dict_resp, product_type, similarity_key):

        template_resp = None

        logger.debug("part_no:{0}, ques_topic:{1}, dict_resp:{2}, product_type:{3}".format(part_no, ques_topic,
                                                                                            dict_resp, product_type))
        # if request from html, create template response using response engine
        if ques_topic == cs.SPEC_SECTION: # pragma: no cover
            resp_dict = self._make_dict_response(part_no, cs.SPEC_SECTION,
                                                 dict_resp, product_type)
            print('resp_dict : ', resp_dict)
            template_resp, resp_code = self.resp_engine.make_response(resp_dict,
                                                           cs.XMLTags.SPECIFICATION_TAG, self.user_query)
        elif (ques_topic.lower() == cs.TROUBLESHOOTING.lower()) or (ques_topic == cs.FAQ):
            resp_dict = self._make_dict_response(part_no, cs.TROUBLESHOOTING,
                                                 dict_resp, product_type)
            template_resp, resp_code = self.resp_engine.make_response(resp_dict,
                                                           cs.XMLTags.TROUBLESHOOT_TAG, self.user_query)
        else:
            resp_dict = self._make_dict_response(part_no, cs.XMLTags.OPERATION_TAG,
                                                 dict_resp, product_type)
            template_resp, resp_code = self.resp_engine.make_response(resp_dict,
                                                           cs.XMLTags.OPERATION_TAG, self.user_query)

        return template_resp

    def _frame_update_product_pref(self, prd_type, model_no):
        """
        Frame the update product preference json format

        Args:
            prd_type:str
                       product type
            model_no:str
                       model no
        Return:framed dict object
        """
        logger.debug('Updating the product alias : %s,%s', prd_type, model_no)
        framed_dict = {self.product_key: [prd_type], self.model_key: [model_no]}
        return framed_dict

    def _check_product_context(self, user_query, part_no):
        """
        check context based on product type
        Args:
            user_query:user query
            model_no:model no extracted
        """
        prd_type, sub_prd, ppart_no, response_code = self.product_handler.handle_product_context(user_query, part_no)

        logger.debug("prd_type:%s, sub_prd:%s, pmodel_no:%s, response_code:%s", prd_type, sub_prd, ppart_no, response_code)

        if response_code == cs.SUCCESS:
            self.product_type = prd_type
            self.sub_product_type = sub_prd
            if ppart_no is not None:
                self.part_no = self.get_part_no(ppart_no, None)
            logger.debug('product_type : %s sub_prd:%s model_no:%s', self.product_type, self.sub_product_type
                         , self.part_no)
        elif (response_code == cs.DATA_NOT_FOUND) and (self.part_no is not None):
            response_code = cs.SUCCESS
            resp_code, product_type, sub_prd = self._get_prd_type(self.part_no)
            logger.debug("prd frm identified frm DB : %s", product_type)
            if product_type is not None:
                self.product_type = product_type
            else:
                response_code = cs.DATA_NOT_FOUND
            self.sub_product_type = sub_prd
        else:
            # testing self.modelno = None
            # testing self.actual_modelno = None
            self.product_type = None
            self.sub_product_type = None
            self.final_response = self.no_prd_detail
            self.template_question = self.no_prd_detail
            logger.error('Product detail not available')
        return response_code

    def _check_spec_key(self, spec_key, prd_type, user_query): # pragma: no cover
        """
        Check context based on spec key
        Args:
           spec_key:specification key from user query
        """
        logger.debug('User query : %s', user_query)
        if self.spec_key_identifer.check_spec_key_in_query(user_query):
            logger.debug('spec key context valid')
            self.spec_key = self.context_manager.update_spec_key_context(spec_key, prd_type)
        else:
            logger.debug('spec key context None')
            self.spec_key = None

    def _check_unit_context_from_query(self, user_query, response, spec_key, prd_type): # pragma: no cover
        """
        check the context based on the unit from user query with preference

        Args:
              user_query : question from user
              response : response from retrieval engine
              spec_key: identified specification key
              prd_type: identified product type
        Return:
             converted value
        """

        # if current user query doesn't have spec key ex: Tell me in mm
        if spec_key is None:
            # get previous spec key from preference(context) for current query product type
            spec_key = Preference.get_spec_key_pref_value(prd_type)

        unit_frm_qry = self.unit_handler.get_unit_from_query(user_query, spec_key)

        # check atleast the query is having some units(like mm,grmas,...)
        if unit_frm_qry is not None:
            result, converted_unit = self.unit_handler.handle_unit(spec_key,
                                                                   user_query,
                                                                   response)

            logger.debug('converted value :(%s)', result)
            return result
        else:
            unit_from_pref = Preference.get_unit_pref_value(prd_type)
            logger.debug("unit from pref : %s", unit_from_pref)
            if unit_from_pref is not None and len(unit_from_pref.strip()) > 0:
                result, converted_unit = self.unit_handler.handle_unit(spec_key,
                                                                       user_query,
                                                                       response)
                logger.debug('converted value :(%s)', result)
                return result

            return None

    def _make_dict_response(self, partno, topic, value, product_type):
        """
            This function is used to form dict response for
            Args:
                partno : str
                          modelno of which answer is to be retrieved
                topic : str
                           manual section
                value : str
                           conerteed value
                product_type : str
                                 product type extracted
            Returns:
                dict_resp : dict
        """

        logger.debug('befor resp : %s , %s, %s', topic, value, (topic == cs.SPEC_SECTION))

        dict_resp = dict()
        spec_dict = dict()
        opr_dict = dict()

        spec_dict[cs.VALUE] = value[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE]

        if topic == cs.SPEC_SECTION: # pragma: no cover
            logger.debug('resp_key : %s',
                         self._get_spec_key_frm_resp(value[cs.XMLTags.SPECIFICATION_TAG][cs.RESPONSE_KEY]))
            spec_dict[cs.RESPONSE_KEY] = self._get_spec_key_frm_resp(
                value[cs.XMLTags.SPECIFICATION_TAG].get(cs.RESPONSE_KEY, {}))
        else:
            spec_dict[cs.RESPONSE_KEY] = ""

        opr_dict[cs.RESPONSE_KEY] = value[cs.XMLTags.OPERATION_TAG].get(cs.RESPONSE_KEY, {})
        opr_dict[cs.FEATURES] = value[cs.XMLTags.OPERATION_TAG][cs.FEATURES]
        opr_dict[cs.MODULE_FLAG] = value[cs.XMLTags.OPERATION_TAG][cs.MODULE_FLAG]
        opr_dict[cs.QUESTION_TYPE] = value[cs.XMLTags.OPERATION_TAG][cs.QUESTION_TYPE]

        dict_resp[cs.XMLTags.SPECIFICATION_TAG] = spec_dict
        dict_resp[cs.XMLTags.TROUBLESHOOT_TAG] = value[cs.XMLTags.TROUBLESHOOT_TAG]
        dict_resp[cs.XMLTags.OPERATION_TAG] = opr_dict
        dict_resp[cs.IOConstants.PART_NO] = partno
        dict_resp[cs.RS_PRODUCT_TYPE] = product_type

        logger.debug('make_response : %s', dict_resp)

        return dict_resp

    def reset_preference(self):
        """
           clear the preferences
        return: SUCCESS
        """
        return Preference.reset_preference()

    def _return_regex_truncated_model_no_bk(self, model_no):
        """
        return the truncated model_no based on regex defined
        regex will give AlphaNumeric+one Alphabet+*

        Args:
            model_no: model no string
        Return:
            truncated model_no
        """
        result = re.match(r'(\w*\d+\w(\w|\*))', model_no).group()
        char = result[-1]
        if char != '*':
            result = result[0:-1] + '*'

        return result

    def _return_regex_truncated_model_no(self, model_no):
        """
        return the truncated model_no based on regex defined
        regex will give AlphaNumeric+one Alphabet+*

        Args:
            model_no: text from query
        Return:
            truncated model_no
        """
        if model_no is None:
            return None

        result = re.findall(r'([a-z]+\d+([a-z]|\*))', model_no, flags=re.IGNORECASE)
        if result is None:
            return None

        for e_modelno, lchar in result:
            if (len(e_modelno.strip()) > 0) and (len(lchar.strip()) > 0):
                if lchar != '*':
                    e_modelno = e_modelno + '*'

                #if len(e_modelno) > 6:
                return e_modelno

    def _return_truncated_model_no(self, model_no):
        """
        To return the truncated model number
        Args:
            model_no: Original Model Number

        Returns:
            Truncated model number
        """
        mo = re.match('.+([0-9])[^0-9]*$', model_no)
        final_model_no = model_no[0:mo.start(1) + 2]

        # Remove the * at last if any
        if final_model_no[-1] == '*':
            final_model_no = final_model_no[0:-1]

        return final_model_no

    def update_product_pref(self, json_data):
        """
        Update the preference using product handler
        Args:
            json_data: data from HTML
        Returns:
            status from product handler
        """
        return self.product_handler.update_db_data(json_data)

    def get_context(self):
        """
        get the latest context
        """
        return Preference.get_preference()

    def get_product_models(self):
        """
        get the model no with product details

        Return: model_dict

         Ex:
            Model dict  = {(washing machine, top loader):[part number1,part number2,...],
                           (washing machine, kepler):[part number1,part number2,...],
                           (washing machine, mini washer):[part number1,part number2,...],
                           (refrigerator, large):[part number1,part number2,...],
                           (refrigerator, medium):[part number1,part number2,...]
                         }
        """
        models_dict = {}
        product_models = self.KNOWLEDGE_RETRIEVER.retrieve_partnos()
        self.models_dict = product_models
        sts = self.models_dict[cs.resp_code]
        if sts == cs.ResponseCode.SUCCESS:
            logger.info("1 get_product_models retrieved_models type =%s", str(type(self.models_dict)))
            models_dict = self.models_dict[cs.resp_data]
            logger.info("2 get_product_models retrieved_models type =%s", str(type(self.models_dict)))
            logger.info("get_product_models retrieved_models type =%s", self.models_dict)
            # reference self.models_dict = models_dict
        return models_dict

    def get_partnumber(self, model_number):
        """
        retrieve part number based on the model number
        Args:
            model_number: model number
        Return:
            part_number: retrieved partnumber
        """
        return self.KNOWLEDGE_RETRIEVER.retrieve_partnumber(model_number)

    def get_thinq_settings(self):
        """
        get the updated thinq settings
        """
        return self.product_handler.get_prd_db()

    def clear_thinq_settings(self):
        """
        clear thinq settings
        """
        return self.product_handler.delete_product_db()

    def _frame_ker_context(self, resp_code, answer):

        logger.debug('Pref before updating : %s', self.context_manager.get_context())
        resp = {}
        resp[cs.IOConstants.KER_CONTEXT] = {}
        resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PART_NO] = ""
        resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PRODUCT] = ""
        resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.UNIT] = ""
        resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.SPEC_KEY] = ""
        resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PREV_ANSWER] = ""
        resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PREV_QUESTION] = ""
        if resp_code == cs.SUCCESS:
            if self.context_manager.get_modelno_context() is not None:
                resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PART_NO] = self.context_manager.get_partno_context()

            if self.context_manager.get_product_context() is not None:
                resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PRODUCT] = self.context_manager.get_product_context()

            if self.context_manager.get_unit_context() is not None:
                resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.UNIT] = self.context_manager.get_unit_context()

            if self.context_manager.get_spec_key_context() is not None:
                resp[cs.IOConstants.KER_CONTEXT][
                    cs.IOConstants.SPEC_KEY] = self.context_manager.get_spec_key_context()

            logger.debug("dialogue : %s %s", answer, self.last_valid_response)

            if len(self.last_valid_response) > 0:
                resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PREV_ANSWER] = self.last_valid_response[0]

            resp[cs.IOConstants.KER_CONTEXT][cs.IOConstants.PREV_QUESTION] = self.previous_question
        return resp

    def _get_cur_ker_context(self):

        logger.debug('Pref before updating : %s', self.context_manager.get_context())
        resp = {}
        resp[cs.IOConstants.PART_NO] = ""
        resp[cs.IOConstants.PRODUCT] = ""
        resp[cs.IOConstants.UNIT] = ""
        resp[cs.IOConstants.SPEC_KEY] = ""
        resp[cs.IOConstants.PREV_ANSWER] = ""

        if self.context_manager.get_partno_context() is not None:
            resp[cs.IOConstants.MODEL_NO] = self.context_manager.get_partno_context()

        if self.context_manager.get_product_context() is not None:
            resp[cs.IOConstants.PRODUCT] = self.context_manager.get_product_context()

        if self.context_manager.get_unit_context() is not None:
            resp[cs.IOConstants.UNIT] = self.context_manager.get_unit_context()

        if self.context_manager.get_spec_key_context() is not None:
            resp[cs.IOConstants.SPEC_KEY] = self.context_manager.get_spec_key_context()

        if len(self.last_valid_response) > 0:
            resp[cs.IOConstants.PREV_ANSWER] = self.last_valid_response[0]

        resp[cs.IOConstants.PREV_QUESTION] = self.previous_question
        return resp

    # For reference def get_model_no(self, question, req_model_no, client_type):
    #     """
    #     get model no from question if not get from context
    #
    #     Args:
    #         question: user_question
    #     Return:
    #         model number:str
    #     """
    #
    #     modelno, actual_modelno = self.modelno_handler.extract_map_model_no(question, self.models_dict)
    #
    #     logger.debug("get_model_no modelno=%s, actual_modelno=%s",modelno, actual_modelno)
    #
    #     if modelno is None:
    #         modelno, actual_modelno = self.modelno_handler.extract_map_model_no(req_model_no, self.models_dict)
    #         if modelno is None:
    #             actual_modelno = self.context_manager.get_modelno_context()
    #             logger.debug("actual_modelno : %s",actual_modelno)
    #             if actual_modelno is not None:
    #                 modelno, actual_modelno = self.modelno_handler.extract_map_model_no(actual_modelno, self.models_dict)
    #
    #     return modelno, actual_modelno


    def _extract_part_no(self, question):
        """
        extract the partnumber from the question

        Args:
            question: user question
        Return:
            partnumber: partnumber identified
        """
        regex = "([A-Z]*\d{6,})"
        partno_regex = re.compile(regex, flags=re.IGNORECASE)
        result = partno_regex.findall(question)
        print("result :", result)
        partnumber = None
        for lpartnumber in result:
            if (len(lpartnumber.strip()) > 0):
                partnumber = lpartnumber.strip()
                break
        return partnumber

    def get_part_no(self, question, req_part_no):
        """
        get partnumber from question if not get from context

        Args:
            question: user_question
            req_part_no : part number present in request json
        Return:
            part number:str
        """
        partnumber = None

        if question is not None:
            partnumber = self._extract_part_no(question)

        # If part number is not there question and present in request json in part_no parameter
        if (partnumber is None) and (req_part_no is not None):
            partnumber = req_part_no
        # If part number is not there question and not present in request json in part_no parameter
        # get from context
        elif (partnumber is None) and (req_part_no is None):
            partnumber = self.context_manager.get_partno_context()

        model_dict = self.models_dict[cs.resp_data]
        for key, partnumber_list in model_dict.items():
            if (partnumber is not None) and (partnumber in partnumber_list):
                return partnumber
        return None

    def validate_model_no_from_context(self):
        """
        validate model no from context

        Return:
            True if valid model no
            False otherwise
        """
        actual_modelno = self.context_manager.get_modelno_context()

        if actual_modelno is not None:
            return True
        return False

    def _get_prd_type(self, part_no):
        """
        get product type based on model number

        Args:
            model_no: str
        Return:
            response_code: int
            prd_type:str
            sub_prd_type:str
        """
        logger.debug("model_no=%s model_dict=%s", part_no, self.models_dict)

        resp_code = self.models_dict[cs.IOConstants.RESP_CODE]

        if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS:
            prd_types = self.models_dict[cs.resp_data].keys()
            logger.debug("prd_types=%s", str(prd_types))
            # reference mapped_modelno, actual_modelno = self.modelno_handler.extract_map_model_no(model_no, self.models_dict)
            # reference model_no = mapped_modelno
            for prd_type in prd_types:
                lpart_nos = self.models_dict[cs.resp_data][prd_type]
                logger.debug("part_no=%s _get_prd_type lmodel_nos=%s", part_no, str(lpart_nos))
                if part_no in lpart_nos:
                    logger.debug("product type from diagmgr=%s", prd_type)
                    return resp_code, prd_type[0], prd_type[1]
        return resp_code, None, None

    def get_product_type(self, part_no, question, ker_context, client_type):

        """
        get product type based on modelno from question or context or from user request

        Args:
            model_no: from user request
            question:user quesry
            ker_context: context
            client type: client type

        Return:
            prd type:str
        """
        logger.debug("get_product_type--- part_no=%s, question=%s, ker_context=%s"
                     ", client_type=%s",part_no, question, ker_context, client_type)
        if client_type == cs.ClientType.KMS:
            self.validate_cntxt_and_fill(ker_context)

        part_no = self.get_part_no(question, part_no)

        if part_no is None:
            part_no = self.context_manager.get_partno_context()
            if part_no is None:
                return None
        logger.debug("get prd for part_no: %s",part_no)
        return self._get_prd_type(part_no)

    def handle_user_query(self, question, classifier_info, similarity_output, part_no, client_type, ker_cntxt=None):
        """
        Handling the user query for context management
        Args:
            question:user_query
            modelno: model_no from UI
            request_from:bot or html
        return:
              Response frmaed,Template question.
        """
        logger.debug('handle_user_query user query:{0},part_no:{1}'.format(question, part_no))
        # updating variable who requested KER server

        self.request_from = client_type

        # if request from chatbot
        if self.request_from == cs.ClientType.KMS:
            json_response = self._manage_context(part_no, question, classifier_info, similarity_output, ker_cntxt)
        else:
            json_response = self._manage_context(part_no, question, classifier_info, similarity_output)

        return json_response


if __name__ == '__main__': # pragma: no cover
    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    dia_manage = DialogueManager()

    while (True):
        print("Enter Query :")
        user_info = input().split(",")
        if user_info[0] == '1':
            print(dia_manage.reset_preference())
        else:
            user_query = user_info[0]
            # testing code model_no = user_info[1]
            # testing code mdl_chn_flag = bool(user_info[2])
            print('Result : ',
                  dia_manage.handle_user_query(user_query, "WM4500H*A", '2',
                                               'Specification', 'washing machine', False, 'L2'))
