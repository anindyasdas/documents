"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anusha.kamath@lge.com,vishwaas.n@lge.com
@modified_by: vanitha.alagarsamy@lge.com
"""
from . import constants
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class RuleBasedClassifier:
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if RuleBasedClassifier.__instance is None:
            RuleBasedClassifier()
        return RuleBasedClassifier.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if RuleBasedClassifier.__instance is not None:
            raise Exception("RuleBasedClassifier is not instantiable")
        else:
            RuleBasedClassifier.__instance = self

    def get_operation_intent(self, question):
        """
        This function is used to check ontologies defined for category and query intent of given user query and returns
        the query intent
        Args:
            question: user question
            category: category of sub section

        Returns:
                intent of user query
        """
        logger.debug("__get_intent_of_operation_section start : %s",  question)
        token_list = question.split()
        logger.debug("token_list : %s", token_list)
        for key, value in constants.KerKoOperationConstants.OPERATION_INTENT_DICT.items():
            if any(word in value for word in token_list):
                logger.debug("intent : %s", key)
                return key
        return constants.KerKoOperationConstants.DESCRIPTION

    def map_operation_subsection(self, section):
        """
        This function is used to categorize the given operation section as
           feature/component/checklist/controlpanel
        Args:
            section: sub section name

        Returns:
            category name of the section

        """
        logger.info("__get_category_of_query start")
        for key, value in constants.KerKoOperationConstants.OPERATION_SUB_CATEGORY_MAP.items():
            if section in value:
                return key
        logger.info("__get_category_of_query end")
        return constants.KerKoOperationConstants.FEATURE

    def map_kepler_operation_subsection(self, query, sub_section):
        """
        This function is used to validate and correct the given operation Kepler sub_section is
           feature/component/checklist/function controlpanel
        Args:
            section: sub section name

        Returns:
            corrected sub_section

        """
        control_panel_words = constants.KerKoStringConstants.CONTROL_PANEL_WORDS
        drying_course_words = constants.KerKoStringConstants.DRYING_COURSE_WORDS
        optional_features_words = constants.KerKoStringConstants.OPTIONAL_FEATURES_WORDS
        for word in control_panel_words:
            if word in query:
                return constants.KerKoMappingDictionary.KEPLER_SECTION_LABELS[2] # Using the function control panel
        for word in drying_course_words:
            if word in query:
                return constants.KerKoMappingDictionary.KEPLER_SECTION_LABELS[5] # Using the drying course
        for word in optional_features_words:
            if word in query:
                return constants.KerKoMappingDictionary.KEPLER_SECTION_LABELS[4] # Using optional features
        return sub_section
