"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import logging as logger
import json
import sys
import os

from .constants import params as cs

from ..components.engine.info_engine import InfoEngine
from ..components.classifier.classifier_engine import ClassifierEngine
from ..components.engine import constants

LG_LOGGING_MODULE_OUTPUT_LVL = logger.INFO + 1


class NlpEngineClient(object):
    """
    defines the method to communicate with NLP modules and get the
    json output
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if NlpEngineClient.__instance is None:
            NlpEngineClient()
        return NlpEngineClient.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if NlpEngineClient.__instance is not None:
            logger.error("NlpEngineClient is not instantiable")
            raise Exception("NlpEngineClient is not instantiable")
        else:
            logger.debug("*** NLP Engine client constructor")
            # instance  of info engine module
            self.info_engine = InfoEngine()
            # instance  of classifier module
            self.classify_engine = ClassifierEngine()
            NlpEngineClient.__instance = self
            # use srl,cons parser
            self.use_srl = True
            self.use_cons_parser = True
            # pipeline configuration
            self.pipeline = constants.PIPELINE_1

    def get_classifier_output(self, question):
        """
            This function is used to extract all classifier results for given
            user query

            Args:
                question : str
                           user question
            Returns:
                output : json string
        """
        logger.debug("Begin (%s)" % question)

        # TODO: Supported sections and products need to be checked before calling NLP modules
        # call classifier engine and get all classifier results
        output = self.classify_engine.get_classifier_output(question)

        # log classifier output to lg_logging module
        logger.log(LG_LOGGING_MODULE_OUTPUT_LVL, output)

        output = json.loads(output)
        resp_code = output[cs.resp_code]
        # extract topic,section,problem type & question type
        if resp_code == cs.ResponseCode.SUCCESS:
            output = output[cs.resp_data]
        else:
            logger.error("classifier output error")
            return None, resp_code

        logger.debug("End resp_code=(%d) classifier_output=(%s) " % (resp_code, str(output)))
        return output, resp_code

    def get_similarity_output(self, question, ques_topic, ques_product=constants.WASHING_MACHINE):
        """
            This function is used to extract information from user query
            Args:
                question : str
                           user question
                ques_topic : str
                          topic of the user question
                ques_product:str
                          query about which product
            Returns:
                extracted_knowledge :dict
        """
        logger.debug("get_similarity_output: Begin ques=%s section=%s product=%s" % (question,
                                                                                     ques_topic, ques_product))
        # map section string to info engine constants
        if ques_topic.lower() == cs.SPEC_SECTION.lower():
            ques_topic = constants.SPEC
        elif ques_topic.lower() == cs.TROUBLESHOOTING.lower():
            ques_topic = constants.TROB
        elif ques_topic.lower() == cs.Section.FAQ.lower():
            ques_topic = constants.FAQ
        elif ques_topic == cs.Section.OPERATION:
            ques_topic = constants.OPERATION

        # TODO: Supported sections and products need to be checked before calling NLP modules
        # call info engine and get all info extraction for user query top 3 predictions
        output = self.info_engine.extract(question, question_type=ques_topic,
                                          product=ques_product, pipeline=self.pipeline, top_k=3)
        logger.log(LG_LOGGING_MODULE_OUTPUT_LVL, output)
        logger.debug("output from info_engine=(%s)" % str(output))
        output = json.loads(output)
        resp_code = output[cs.resp_code]
        if resp_code == cs.ResponseCode.SUCCESS:
            # extract similarity_key value from dict
            output = output[cs.resp_data][cs.IOConstants.SIMILARITY_KEY]
        else:
            logger.error("Info Engine output error")
            return None, resp_code

        logger.debug("End output type=(%s) op=(%s)" % (type(output), str(output)))
        return output, resp_code

    def get_answer_from_paraqa(self, paragraph, questions):# pragma: no cover
        """
            This function is used to retrieve answer of factoid question from
            the given paragraph using paraqa model
            Args:
                paragraph : list
                          list of paragraphs
                questions : list
                           list of questions
            Returns:
               output : json string
        """
        # call to info engine paraqa
        output = self.info_engine.extract_answer_para(paragraph, questions)
        logger.debug("paraQA output from info_engine=(%s)" % str(output))
        return output

    def get_answer_from_boolqa(self, paragraph, questions):# pragma: no cover
        """
            This function is used to retrieve answer of bool question from
            the given paragraph using boolqa model
            Args:
                paragraph : list
                          list of paragraphs
                questions : list
                           list of questions
            Returns:
               output : json string
        """
        # call to info engine paraqa
        output = self.info_engine.extract_answer_bool(paragraph, questions)
        logger.debug("paraQA output from info_engine=(%s)" % str(output))
        return output

    def get_srl_cons(self, statement):
        """
            This function is used to get srl,cons parser output of
            given statement
            Args:
                statement : str
                          manual statement
            Returns:
               srl_const_output : json string
        """
        # For storing SRL and Constituency parsers output
        srl_const_output = self.info_engine.extract_srl_cons(statement)
        return srl_const_output
