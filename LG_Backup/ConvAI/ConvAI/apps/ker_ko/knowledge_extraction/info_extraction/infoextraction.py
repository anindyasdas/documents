# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy
"""
import json
import re
import os
import importlib
from configparser import ConfigParser

from ..constants import params as cs
# KMS Logger
kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

CONFIG_PATH = os.path.join('config', 'configuration.ini')


class InfoExtraction(object):
    """
        class defines API to extract error codes information
    """

    def __init__(self):
        self.regex_dict = {}
        self.error_code_key = "error_codes"
        """
        classifier is used currently to find user problem type
        If info extraction to be used please change to True
        """
        self.use_classifier = True
        self.use_info_extraction = False
        self.use_cons_parser = True
        self.use_srl = True
        try:
            global CONFIG_PATH
            read_config = ConfigParser()
            read_config.read(CONFIG_PATH)
            self.errkeys_json_path = os.path.abspath(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), '..', read_config.get('error_keys', 'error_codes_mapping')))
            logger.debug("URL=(%s)" % self.errkeys_json_path)
            self._read_regex()
        except Exception as e:
            logger.exception("Init exception", e)

    def _read_regex(self):
        """
           read regex for different error codes from json
           Returns:None.
        """
        with open(self.errkeys_json_path, 'r') as pf:
            self.regex_dict = json.load(pf)

    def get_error_code_frm_query(self, query):
        """
           Identify the error code for the user query
           Args:
               query : str
                      Query from user.
           Returns:
               key : Str
                     Error code present in the query.
        """
        error_code = None
        keys = self.regex_dict[self.error_code_key].keys()
        for key in keys:
            error_code_match = re.search(self.regex_dict[self.error_code_key][key], query, re.IGNORECASE)

            if error_code_match is not None:
                error_code = key
                break
        logger.debug("Error code found=(%s)" % error_code)
        return error_code

    def mapintent_with_infoextraction(self, info_dict, problem_type):
        """
            This function is used to map intent with info extraction
            dict response for response_engine

            Args:
                info_dict : dict
                           dict object response of info extraction
                problem_type : str
                           problem type of user query
            Returns:
                dict_resp : dict
        """
        dict_resp = dict()
        prob_key = ""
        mapped_relation = ""
        try:
            generic_prob_val = info_dict[cs.InfoKnowledge.PROB_VAL_GEN]
            specific_prob_val = info_dict[cs.InfoKnowledge.PROB_VAL_SPECI]
            # by default ,we are using classifier output
            # if use_info_extraction is enabled , use info extraction output
            if self.use_info_extraction:
                problem_type = info_dict[cs.PROP_KEY]

            # map the problem type and fill the dictionary with relation
            # prob_key for retrieving knowledge from database
            if problem_type == cs.ProblemTypes.ERROR:
                mapped_relation = cs.HAS_ERROR
                prob_key = cs.ProblemTypes.ERROR_CODE
            elif problem_type == cs.ProblemTypes.NOISE:
                mapped_relation = cs.HAS_NOISE
                prob_key = cs.ProblemTypes.NOISE
            elif problem_type == cs.ProblemTypes.PROBLEM:
                mapped_relation = cs.HAS_PROBLEM
                prob_key = cs.ProblemTypes.PROBLEM
            elif problem_type == cs.ProblemTypes.COOLING_PROBLEM:
                mapped_relation = cs.HAS_COOLING_PROBLEM
                prob_key = cs.ProblemTypes.PROBLEM
            elif problem_type == cs.ProblemTypes.ICE_PROBLEM:
                mapped_relation = cs.HAS_ICE_PROBLEM
                prob_key = cs.ProblemTypes.PROBLEM
            elif problem_type == cs.ProblemTypes.WIFI_PROBLEM:
                mapped_relation = cs.HAS_WIFI_PROBLEM
                prob_key = cs.ProblemTypes.PROBLEM

            dict_resp[cs.INTENT] = mapped_relation
            dict_resp[cs.PROP_KEY] = prob_key
            dict_resp[cs.PROP_VALUE] = generic_prob_val
            dict_resp[cs.InfoKnowledge.PROB_VAL_SPECI] = specific_prob_val

            logger.debug("mapped intent=(%s)" % str(dict_resp))

            return dict_resp
        except KeyError:
            logger.error("Key doesnt exist in trob_keys=%s", str(info_dict))
            return None

    def __get_cons_parser(self, const_output, knowledge_dict):
        """
            parses constituency parser outputs and extract entity,verb

            Args:
                const_output : dict
                knowledge_dict : output to be restored
            Returns:
                knowledge_dict : dict object
        """
        logger.debug("Const wrapper=(%s)", str(const_output))
        entity = const_output[cs.NP]
        verb = const_output[cs.VB]
        if len(entity) > 0:
            entity = [item.lower() for item in entity if len(item.strip()) != 0]
            if len(entity) > 0:
                knowledge_dict[cs.ENTITY] = entity
        if len(verb) > 0:
            verb = [item.lower() for item in verb if len(item.strip()) != 0]
            if len(verb) > 0:
                knowledge_dict[cs.VERB] = verb
        return knowledge_dict

    def __get_srl(self, srl_output, knowledge_dict):
        """
            parses srl outputs and extract cause,purpose,temporal

            Args:
                srl_output : dict
                knowledge_dict : output to be restored
            Returns:
                knowledge_dict : dict object
        """
        reason = []
        purpose = []
        temporal = []
        logger.info("srl_output wrapper=(%s)", str(srl_output))
        # Loop through srl_output and get reason, temporal, purpose
        for key, value in srl_output.items():
            logger.debug("value:(%s)", str(value))
            if cs.CAUSE == key:
                reason = value
                reason = [item.lower() for item in reason if len(item.strip()) != 0]
            elif cs.TMPRL == key:
                temporal = value
                temporal = [item.lower() for item in temporal if len(item.strip()) != 0]
            elif cs.PURPOSE == key:
                purpose = value
                purpose = [item.lower() for item in purpose if len(item.strip()) != 0]

        logger.debug("reas_lem=(%d)pur_len=(%d) temp_len=(%d)" % (len(reason),
                                                                  len(purpose), len(temporal)))
        if len(reason) > 0:
            knowledge_dict[cs.CAUSE] = reason
        if len(purpose) > 0:
            knowledge_dict[cs.PURPOSE] = purpose
        if len(temporal) > 0:
            knowledge_dict[cs.TEMPORAL] = temporal
        return knowledge_dict

    def get_knowledge_from_user_query(self, const_output, srl_output):
        """
            call SRL,constituency parser APIS and get knowledge
            Args:
                const_output : dict
                srl_output : dict
            Returns:
                knowledge_dict : dict object
        """
        knowledge_dict = dict()

        if self.use_cons_parser:
            # get cons parser output
            knowledge_dict = self.__get_cons_parser(const_output, knowledge_dict)

        if self.use_srl:
            # get srl output
            knowledge_dict = self.__get_srl(srl_output, knowledge_dict)

        logger.debug("knowledge_dict=(%s)", str(knowledge_dict))

        # if empty dictionary return none
        if not bool(knowledge_dict) == True:
            return None
        return knowledge_dict

if __name__ == '__main__':
    obj = InfoExtraction()
    assert obj.get_error_code_frm_query("I am getting ie") == 'IE'
    assert obj.get_error_code_frm_query("I am getting ie problem") == 'IE'
    assert obj.get_error_code_frm_query("My product gives motor locked error") == 'LE'
    assert obj.get_error_code_frm_query("My product gives   control lock error") == 'CL'
    assert obj.get_error_code_frm_query("My product gives ezdispense 2 error") == 'E d2'
    assert obj.get_error_code_frm_query("My product gives ed2") == 'E d2'
    assert obj.get_error_code_frm_query("My product gives e d2") == 'E d2'