"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anusha.kamath@lge.com,vishwaas.n@lge.com
@modified_by: vanitha.alagarsamy@lge.com
"""
import logging as logger
from nltk.stem import WordNetLemmatizer
from . import constants


class RuleBasedClassifier:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()

    def get_operation_intent(self, question, category):
        """
        This function is used to check ontologies defined for category and query intent of given user query and returns
        the query intent
        Args:
            question: user question
            category: category of sub section

        Returns:
                intent of user query
        """
        logger.debug("__get_intent_of_operation_section start : %s, %s", category, question)
        token_list = [self.lemmatizer.lemmatize(word, pos='v') for word in question.lower().split()]
        token_list = list(set(token_list))
        token_list += [self.lemmatizer.lemmatize(word, pos='n') for word in token_list]
        token_list += question.lower().split()
        token_list = list(set(token_list))
        logger.debug("token_list : %s", token_list)
        for intent_name in constants.KerOperationConstants.OPERATION_CATEGORY_TO_INTENT_MAP[category]:
            if any(word in constants.KerOperationConstants.OPERATION_INTENT_DICT[intent_name] for word in token_list):
                logger.debug("intent : %s", intent_name)
                return intent_name
        return constants.KerOperationConstants.DESCRIPTION  #default intent is description

    @staticmethod
    def map_operation_subsection(section):
        """
        This function is used to categorize the given operation section as
           feature/component/checklist/controlpanel
        Args:
            section: sub section name

        Returns:
            category name of the section

        """
        logger.debug("__get_category_of_query start")
        for key, value in constants.KerOperationConstants.OPERATION_SUB_CATEGORY_MAP.items():
            value = [v.lower() for v in value]
            if section.lower() in value:
                return key
        logger.debug("__get_category_of_query end")
        return None

    def __separate_section_for_component(self, query, section): # pragma: no cover
        """
        Function to resolve the similar keys of component category that are grouped together for classifier module
        Args:
            query: user question
            section: L1 key of the question identified by classifier

        Returns:
            L1 key - more specific
        """
        if section == constants.KerOperationConstants.DRAWER:
            if any(word in query.lower().split() for word in constants.KerOperationConstants.CRISPER_DRAWER_LIST):
                return constants.KerOperationConstants.CRISPER_DRAWER
            elif any(word in query.lower().split() for word in constants.KerOperationConstants.PANTRY_DRAWER_LIST):
                return constants.KerOperationConstants.PANTRY_DRAWER
            elif any(
                    word in query.lower().split() for word in constants.KerOperationConstants.FULL_CONVERT_DRAWER_LIST):
                return constants.KerOperationConstants.FULL_CONVERT_DRAWER
            else:  # To be decided yet
                return constants.KerOperationConstants.DRAWER
        if section == constants.KerOperationConstants.DISPENSER:
            if any(word in query.lower().split() for word in constants.KerOperationConstants.WATER_DISPENSER):
                return constants.KerOperationConstants.WATER_DISPENSER
            else:  # To be decided yet
                return constants.KerOperationConstants.ICE_AND_WATER_DISPENSER
        if section == constants.KerOperationConstants.DOOR_IN_DOOR_INSTAVIEW:
            return self.__separate_door_in_door(query)

        return section

    def __separate_door_in_door(self, query):
        """
        function to separate door in door and instaview
        Args:
            query: user query

        Returns:
            either door in door or insta-view based on query

        """
        if any(word in query.lower().split() for word in constants.KerOperationConstants.INSTAVIEW_LIST):
            return constants.KerOperationConstants.INSTAVIEW
        else:  # To be decided yet
            return constants.KerOperationConstants.DOOR_IN_DOOR

    def section_seperator(self, query, section):
        """
        Function to resolve the similar keys that are grouped together for classifier module
        Args:
            query: user question
            section: L1 key of the question identified by classifier

        Returns:
            L1 key - more specific

        """
        if section == constants.KerOperationConstants.STORING_FOOD_AND_WINE:
            if any(word in query.lower().split() for word in constants.KerOperationConstants.WINE_LIST):
                return constants.KerOperationConstants.STORING_WINE
            else:  # defaults to food if the eatable is not in food or wine list
                return constants.KerOperationConstants.STORING_FOOD
        elif section == constants.KerOperationConstants.CONTROL_PANEL_SECTION:
            if any(word in query.lower().split() for word in constants.KerOperationConstants.CONTROL_PANEL_2):
                return constants.KerOperationConstants.CONTROL_PANEL_2
            elif any(word in query.lower().split() for word in constants.KerOperationConstants.CONTROL_PANEL_1):
                return constants.KerOperationConstants.CONTROL_PANEL_1
            else:  # If it is not identified whether it is from control panel 1 or 2 , 1 is returned by default
                return constants.KerOperationConstants.CONTROL_PANEL_SECTION
        elif section == constants.KerOperationConstants.DRAWER or section == constants.KerOperationConstants.DISPENSER:
            return self.__separate_section_for_component(query, section)
        else:
            return section
