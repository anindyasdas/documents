"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import json
import os.path
import sys
from configparser import ConfigParser

"""
For local testing/debugging , to get the logs in console,
Root Handler should be set before any call to logging statements.
Otherwise it cannot be set later
"""
# logger configurtion
"""
#Please enable only for local debugging
logger.basicConfig(level=logger.DEBUG,
                   format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                          "funcName)s() %(message)s",
                   datefmt='%Y-%m-%d,%H:%M:%S')
"""
from .knowledge.database import DBInterface
from .constants import params as cs
from .mapping.key_mapper import ProductKeyMapper
from .constants.params import GenericProductNameMapping as products
from .response.response_engine import ResponseEngine
from .info_extraction.subkey_extractor import SubKeysExtractor
from .nlp_engine_client import NlpEngineClient


import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'config', 'configuration.ini'))

logger.debug("CONFIG_PATH=%s", CONFIG_PATH)
# constants to use pipeline
TEXT_SIM = 1
INFO_EXT = 2



class IntentSchema(object):
    """
    defines the method to retrieve intent schema
    """
    spec_intent = {}
    trob_intent = {}
    faq_intent = {}
    oper_intent = {}

    @classmethod
    def load_intentmapping_json(cls, topic):
        """
           get the file path from config and convert
           the schema to dict and parse the schema
        """
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        logger.debug("Config path" + CONFIG_PATH)
        abspath_path = os.path.abspath(os.path.join(os.path.dirname(
            os.path.realpath(__file__))))
        intent_file_path = ""
        if topic == cs.SPEC_SECTION:
            intent_file_path = os.path.join(abspath_path,
                                            config_parser.get("spec_intent",
                                                              "spec_intent_mapping"))
        elif topic == cs.TROB_SECTION:
            intent_file_path = os.path.join(abspath_path,
                                            config_parser.get("trob_intent",
                                                              "trob_intent_mapping"))
        elif topic == cs.Section.FAQ:
            intent_file_path = os.path.join(abspath_path,
                                            config_parser.get("faq_intent",
                                                              "faq_intent_mapping"))
        elif topic == cs.Section.OPERATION:
            intent_file_path = os.path.join(abspath_path,
                                            config_parser.get("oper_intent",
                                                              "oper_intent_mapping"))
        logger.debug("intent json file path:" + intent_file_path)
        # Opening JSON file
        with open(intent_file_path) as f:
            # returns JSON object as a dictionary
            intent_mapping = json.load(f)

        # Closing file
        f.close()
        return intent_mapping

    @classmethod
    def get_intent(cls, question, section=None):
        """
            This function is used to get intent for the template question
            from the defined json
            Args:
                question : str
                           template question from Question_Similarity Module
                section : str
                           Manual section name
            Returns:
                intent : str
                         returns the defined intent of template question
        """
        intent = None
        try:
            if question is None or section is None:
                return intent
            logger.debug("typekey=(%s) key:(%s)" % (type(question), question))
            if section == cs.SPEC_SECTION:
                intent = cls.spec_intent[question]
            elif section == cs.TROB_SECTION:
                intent = cls.trob_intent[question]
            elif section == cs.Section.FAQ:
                intent = cls.faq_intent[question]
            elif section == cs.Section.OPERATION:
                intent = cls.oper_intent[question]
            logger.debug("intent return:(%s)", intent)
            return intent
        except KeyError:
            logger.error("Key doesn't exist!=%s", str(question))
            return None


class KnowledgeRetriever(object):
    """
    defines the method to retrieve knowledge from the database
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if KnowledgeRetriever.__instance is None:
            KnowledgeRetriever()
        return KnowledgeRetriever.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if KnowledgeRetriever.__instance is not None:
            logger.error("KnowledgeRetriever is not instantiable")
            raise Exception("KnowledgeRetriever is not instantiable")
        else:
            # Top 3 predictions from text similarity based on score
            # Retrieva knowledge for max 3 iterations to get answers from database
            # Once we get answers it exits and returns response
            self.max_predictions = 3

            # variables to use info extraction pipeline
            self.use_info_extraction = False
            self.pipeline = TEXT_SIM
            # instance of response engine
            self.resp_engine = ResponseEngine()

            # DBInterface instance
            self.db_interface = DBInterface()

            # Instance to handle product specific mapping
            self.prod_key_mapper = ProductKeyMapper()

            # instance to extract sub key info
            self.subkey_extractor = SubKeysExtractor()

            # instance  of nlp engine client module
            self.nlp_eng_client = NlpEngineClient.get_instance()

            # load spec intent json and store
            IntentSchema.spec_intent = IntentSchema.load_intentmapping_json(
                cs.SPEC_SECTION)
            # load trob intent json and store
            IntentSchema.trob_intent = IntentSchema.load_intentmapping_json(
                cs.TROB_SECTION)
            # load faq intent json and store
            IntentSchema.faq_intent = IntentSchema.load_intentmapping_json(
                cs.Section.FAQ)
            # load operation intent json and store
            IntentSchema.oper_intent = IntentSchema.load_intentmapping_json(
                cs.Section.OPERATION)
            KnowledgeRetriever.__instance = self

    def _validate_dbresult(self, db_results, topic):
        """
        validate the DB result from DAtabase

        Args:
            db_results:DB result frm DAtabaseEngine
            topic: topic of the query
        return:
            True or False based on condition
        """
        res = False
        if db_results is None:
            return False

        if topic == cs.Section.OPERATION:
            if (db_results is not None) and (len(db_results[cs.FEATURE]) > 0) or (len(db_results[cs.DESC_KEY]) > 0):
                res = True
        elif topic == cs.Section.TROB:
            if (db_results is not None) and (len(db_results[cs.REASON_KEY]) > 0) or (len(db_results[cs.SOLUTION_KEY]) > 0):
                res = True
        elif (topic == cs.Section.SPEC) and (len(db_results[cs.VALUE]) > 0):
                res = True
        return res

    def _fill_only_feature(self, db_results):# pragma: no cover
        # if the response has only feature, consider only feature list
        # take the corresponding index image url

        feature_dicts = []
        prev_media_url = None
        cur_media_url = ""

        for idx, feature in enumerate(db_results[cs.FEATURE]):
            feature_dict = dict()
            feature_dict[cs.FEATURE] = feature
            if (idx < len(db_results[cs.MEDIA_URL])) and (db_results[cs.MEDIA_URL][idx] is not None) and \
                    (prev_media_url != cur_media_url):
                feature_dict[cs.MEDIA] = dict()
                cur_media_url = db_results[cs.MEDIA_URL][idx]
                feature_dict[cs.MEDIA][cs.MEDIA_URL] = db_results[cs.MEDIA_URL][idx]
                feature_dict[cs.MEDIA][cs.MEDIA_TYPE] = db_results[cs.MEDIA_TYPE][idx]
                feature_dict[cs.MEDIA][cs.MEDIA_SIZE] = db_results[cs.MEDIA_SIZE][idx]
            feature_dicts.append(feature_dict)

        return feature_dicts

    def __make_unstructured_resp_dict(self, db_results, topic):
        """
            This function is used to form dict response for
            unstructured content

            Args:
                db_results : dict
                           dict object from DBInterface
            Returns:
                feature_dict : dict
        """
        key1, key2 = "", ""
        feature_dicts = []
        prev_media_url = None
        cur_media_url = ""
        if topic == cs.TROB_SECTION:
            key1 = cs.REASON_KEY
            key2 = cs.SOLUTION_KEY
        elif topic == cs.Section.OPERATION:
            key1 = cs.FEATURE
            key2 = cs.DESC_KEY

        if self._validate_dbresult(db_results, topic):
            # if the response has both feature and desc tags, zip both list
            # take the corresponding index image url
            replace_none_with_empty_strings = lambda x: x or ""
            filter_none_features = lambda s: s[0] is not None
            for idx, feature_desc in \
                    enumerate(filter(filter_none_features, zip(db_results[key1], db_results[key2]))):
                feature_dict = dict()
                feature_dict[key1] = replace_none_with_empty_strings(feature_desc[0])
                feature_dict[key2] = replace_none_with_empty_strings(feature_desc[1])
                if (idx < len(db_results[cs.MEDIA_URL])) and (db_results[cs.MEDIA_URL][idx] is not None) and \
                        (prev_media_url != cur_media_url):
                    feature_dict[cs.MEDIA] = dict()
                    cur_media_url = db_results[cs.MEDIA_URL][idx]
                    feature_dict[cs.MEDIA][cs.MEDIA_URL] = db_results[cs.MEDIA_URL][idx]
                    feature_dict[cs.MEDIA][cs.MEDIA_TYPE] = db_results[cs.MEDIA_TYPE][idx]
                    feature_dict[cs.MEDIA][cs.MEDIA_SIZE] = db_results[cs.MEDIA_SIZE][idx]
                feature_dicts.append(feature_dict)
        else:
            # if the response has only feature, consider only feature list
            # take the corresponding index image url
            feature_dicts = self._fill_only_feature(db_results)

        return feature_dicts

    def __make_dict_resp(self, product_type, modelno, topic, db_results, respkey_dict, question_detail):
        """
            This function is used to form dict response for
            response_engine

            Args:
                product_type : str
                         product type of the model
                modelno : str
                          modelno of which answer is to be retrieved
                topic : str
                           manual section
                db_results : dict
                           dict object from DBInterface
                respkey_dict : dict
                           dict object of canonical question
            Returns:
                dict_resp : dict
        """
        logger.debug("product_type={}, modelno={}, topic={}, db_results={}, respkey_dict={}, question_detail={}".format(
            product_type, modelno, topic, db_results, respkey_dict, question_detail
        ))
        dict_resp = dict()
        trob_dict = dict()
        spec_dict = dict()
        oper_dict = dict()

        resp_code = ""
        logger.debug("db_results : %s", db_results)
        logger.debug("question_detail : %s", question_detail)
        try:
            # Make Unstructured response only for Troubleshooting and Operation Sections
            if topic != cs.SPEC_SECTION:
                trob_dict[cs.CAUSES_SOL_KEY] = self.__make_unstructured_resp_dict(db_results, topic)
                flag, question_type = question_detail[0], question_detail[1]
                oper_dict[cs.MODULE_FLAG] = flag
                oper_dict[cs.QUESTION_TYPE] = question_type
                oper_dict[cs.FEATURES] = self.__make_unstructured_resp_dict(db_results, topic)

            spec_dict[cs.VALUE] = db_results[cs.VALUE]
            # response key is shared as dictionary returned from info engine module
            if topic == cs.SPEC_SECTION:
                spec_dict[cs.RESPONSE_KEY] = respkey_dict
            elif topic == cs.Section.OPERATION:
                oper_dict[cs.RESPONSE_KEY] = respkey_dict
            else:
                spec_dict[cs.RESPONSE_KEY] = ""

            # check the empty response
            if len(db_results[cs.VALUE]) == 0 and len(db_results[cs.XMLTags.REASON_TAG]) == 0 \
                    and len(db_results[cs.XMLTags.SOLUTION_TAG]) == 0 and len(db_results[cs.DESC_KEY]) == 0 \
                    and len(db_results[cs.FEATURE]) == 0:
                trob_dict[cs.XMLTags.REASON_TAG] = []
                trob_dict[cs.XMLTags.SOLUTION_TAG] = []
                spec_dict[cs.VALUE] = []
                resp_code = cs.ResponseCode.DATA_NOT_FOUND
            else:
                resp_code = cs.ResponseCode.SUCCESS
        except KeyError as e:
            logger.error("Exception : %s", str(e))
            logger.error("__make_dict_resp=%s", str(db_results))
            resp_code = cs.ResponseCode.DATA_NOT_FOUND
        finally:
            dict_resp[cs.SPECIFICATION_TAG] = spec_dict
            dict_resp[cs.XMLTags.TROUBLESHOOT_TAG] = trob_dict
            dict_resp[cs.XMLTags.OPERATION_TAG] = oper_dict
            dict_resp[cs.MODEL_TR] = modelno
            dict_resp[cs.RS_PRODUCT_TYPE] = product_type
            logger.debug("__make_dict_resp=%s errorcode=%d" % (str(dict_resp), resp_code))
        return dict_resp, resp_code

    def __form_json_resp(self, resp_header, extracted_info=None, query_key_mapping=None,
                         knowledge_dict=None, db_resp=None):
        """
            This function is used to form json response from the classifier,info engine
            outputs and DB results

            Args:
                resp_header : dict has resp_code and resp_msg
                extracted_info : dict of classifier outputs of topic,intent and problem type
                query_key_mapping : Info Extraction output
                knowledge_dict : cons parser,srl output
                db_resp : DB Engine response
            Returns:
                resp : json string
        """
        resp = {}
        key_info = {}
        resp_data = {}

        if resp_header[cs.resp_code] != cs.ResponseCode.SUCCESS and resp_header[
            cs.resp_code] != cs.ResponseCode.DATA_NOT_FOUND:
            resp[cs.resp_code] = resp_header[cs.resp_code]
            resp[cs.error_msg] = resp_header[cs.resp_data]
            return json.dumps(resp)

        # key_info response
        key_info = query_key_mapping[cs.InfoKnowledge.KEY]

        """
        # TODO : Once info extraction is updated will enable below else part
        if self.pipeline == constants.PIPELINE_1:
            key_info = query_key_mapping[cs.InfoKnowledge.KEY]
        else:
            key_info[cs.PROP_VALUE] = query_key_mapping[cs.PROP_VALUE]
            key_info[cs.InfoKnowledge.PROB_VAL_SPECI] = query_key_mapping[cs.InfoKnowledge.PROB_VAL_SPECI]
            cons_parser = {}
            srl = {}
            for key in knowledge_dict.keys():
                if key == cs.ENTITY or key == cs.VERB:
                    cons_parser[key] = knowledge_dict[key]
                elif key == cs.TMPRL or key == cs.CAUSE or key == cs.PURPOSE:
                    srl[key] = knowledge_dict[key]
            key_info[cs.InfoKnowledge.CONS_PARSER] = cons_parser
            key_info[cs.InfoKnowledge.SRL] = srl
        """
        # fill key info in extracted_info response
        extracted_info[cs.RespKeys.KEY_INFO] = key_info
        extracted_info[cs.PROP_VALUE] = query_key_mapping[cs.PROP_VALUE]
        # resp code
        resp[cs.resp_code] = resp_header[cs.resp_code]

        # response_data response
        resp_data[cs.RespKeys.DB_RESP] = db_resp
        resp_data[cs.RespKeys.EXTRACTED_INFO] = extracted_info
        resp[cs.resp_data] = resp_data

        return json.dumps(resp)

    def __extract_classifier_info(self, question, classifier_output=None):
        """
            This function is used to extract all classifier results for given
            user query

            Args:
                question : str
                           user question
                classifier_output : json string
                           classifier output of user query
            Returns:
                resp_code : int
                            response code from classifier
                topic : str
                        section type of user query
                intent : str
                        intent of user query
                problem_type : str
                        problem type of user query
                category_type : str
                        category type of the operation query (checklist / component/ feature/ storage)
        """
        topic = ""
        intent = ""
        problem_type = ""
        question_type = ""
        category_type = ""

        logger.debug("Begin (%s)" % question)

        if classifier_output is None:
            return cs.ResponseCode.DATA_NOT_FOUND, topic, intent, problem_type, category_type
        output = classifier_output

        # log classifier output to lg_logging module
        logger.debug("output :%s", output)

        # extract topic,section,problem type & question type
        topic = output.get(cs.ProblemTypes.SECTION, None)
        intent = output.get(cs.ProblemTypes.INTENT, None)
        problem_type = output.get(cs.ProblemTypes.SUB_SECTION, None)
        question_type = output.get(cs.ProblemTypes.QUES_TYPE, None)
        category_type = output.get(cs.ProblemTypes.CATEGORY, None)

        logger.debug("End resp_code=(%d) topic=(%s) intent=(%s) problem_type=(%s) category_type=(%s)"
                     % (cs.ResponseCode.SUCCESS, topic, intent, problem_type, category_type))
        return cs.ResponseCode.SUCCESS, topic, intent, problem_type, question_type, category_type

    def __extract_canonical_key(self, extracted_knowledge, prediction_index=0):
        """
            This function is used to extract similarity key
            and returns it

            Args:
                extracted_knowledge : dict
                prediction_index : int
            Returns:
                canonical_key : str
                key_mapping : dict
        """
        # get template key of user question
        key_mapping = extracted_knowledge[prediction_index]

        # extract canonical key key
        key = key_mapping[cs.InfoKnowledge.KEY]

        # remove leading/trailing spaces and trailing dot
        canonical_key = key.strip().rstrip('.')
        logger.debug("key_mapping=%s similarity_key=(%s)" % (str(key_mapping), str(canonical_key)))
        return key_mapping, canonical_key

    def __map_to_db_knowledge(self, question, query_basic_info, similarity_output, query_intent, prediction_index):
        """
           This function is used to map classifier,info engine knowledge to
           DB Engine knowledge

           Args:
               question : str
                       user question
               query_basic_info : dict
                              contains query basic info model,product,intent,problem type
               similarity_output : dict
                                     text similarity output from info engine
               query_intent : str
                              query intent of user query
               prediction_index : int
                            index of prediction similarity key
           Returns:
               query_key_mapping : dict
               topic:str
               query_intent : str
               knowledge_dict : dict
               similarity_key : str
        """
        query_key_mapping = {}
        knowledge_dict = None
        similarity_key = ""

        # extract topic , product type all basic info of query from dict
        topic = query_basic_info[cs.XMLTags.TOPIC_TAG]
        problem_type = query_basic_info[cs.RespKeys.PROB_TYPE]
        product = query_basic_info[cs.RS_PRODUCT_TYPE]

        logger.debug("similarity_output=%s topic=%s query_intent=%s problem_type=%s product=%s index=%d" %
                     (similarity_output, topic, query_intent, problem_type, product, prediction_index))

        # if user query belongs to specification section
        if topic == cs.SPEC_SECTION:
            # get canonical key and mapping
            spec_mapping, similarity_key = self.__extract_canonical_key(similarity_output, prediction_index)
            logger.debug("spec_mapping=%s", str(spec_mapping))
            # get prod map key and call again retrieve knowledge
            prod_mapped_key = self.prod_key_mapper.get_product_mapped_key(similarity_key, product)
            if prod_mapped_key is not None:
                similarity_key = prod_mapped_key
            # get relation for the spec key
            query_key_mapping = IntentSchema.get_intent(similarity_key, topic)
            rel_intent = query_key_mapping[cs.INTENT]
            # call sub key extractor to get sub key information for specification
            sub_key = self.subkey_extractor.extract_specification_subkey(question, [similarity_key])
            sub_key = sub_key[0]
            logger.debug("sub_key=%s", str(sub_key))
            # get relation from spec_intent.json and add to similarity key mapping
            spec_mapping[cs.INTENT] = rel_intent
            query_key_mapping = spec_mapping
            logger.debug("spec_mapping=%s", str(spec_mapping))
            query_key_mapping[cs.PROP_VALUE] = sub_key[cs.InfoKnowledge.KEY]
            # update  sub key info to spec mapping
            query_key_mapping.update(sub_key)
            logger.debug("query_key_mapping=%s", str(query_key_mapping))
            query_intent = cs.SOLUTION_KEY
            similarity_key = spec_mapping

        # if user query belongs to troubleshooting section or operation section
        elif topic == cs.TROB_SECTION:
            # text similarity approach, get canonical key and mapping
            ts_mapping, similarity_key = self.__extract_canonical_key(similarity_output, prediction_index)

            # get relation for the question
            query_key_mapping = IntentSchema.get_intent(similarity_key, topic)
            if query_key_mapping is None:
                logger.error("query_key_mapping is none")
            else:
                query_key_mapping[cs.InfoKnowledge.PROB_VAL_SPECI] = similarity_key
            similarity_key = ts_mapping
            #  TODO : Once info extraction is updated will enable below else part
            """
            # text similarity approach
            # if info extraction based approach, find query intent from classifier
            elif self.pipeline == constants.PIPELINE_2:

                # map PROB_KEY,PROB_VALUE with info engine output
                query_key_mapping = self.__mapintent_with_infoextraction(
                    similarity_output, problem_type)

                # SRL,Constituency parser output
                cons_parser = similarity_output[cs.InfoKnowledge.CONS_PARSER]
                srl = similarity_output[cs.InfoKnowledge.SRL]
                knowledge_dict = self.__get_knowledge_from_user_query(cons_parser,
                                                                      srl)
                logger.debug("knowledge_dict result=%s" % str(knowledge_dict))
                similarity_key = similarity_output
            """
            query_intent = cs.CAUSES_SOL_KEY

        # if user query belongs to FAQ section
        elif topic == cs.Section.FAQ:
            # get canonical key and mapping
            faq_mapping, similarity_key = self.__extract_canonical_key(similarity_output, prediction_index)

            # get relation for the question
            query_key_mapping = IntentSchema.get_intent(similarity_key, topic)
            query_intent = cs.SOLUTION_KEY
            topic = cs.TROB_SECTION
            similarity_key = faq_mapping

        return query_key_mapping, topic, query_intent, knowledge_dict, similarity_key

    def __map_intent_and_retrieve_knowledge(self, question, query_basic_info, similarity_output, query_intent):
        """
            This function is used to retry the retrieve knowledge retrieve knowledge for
            max 3 iterations to get answers from database
            Once we get answers it exits and returns response

            Args:
                question : str
                          user question
               query_basic_info : dict
                                contains query basic info model,product,intent,problem type
               similarity_output : list
                                    similarity key results dict
               query_intent : str
                              query intent of user query
            Returns:
                db_results : dict
                query_key_mapping : dict
                topic:str
                query_intent : str
                knowledge_dict : dict
                similarity_key : str
        """
        resp_code = cs.ResponseCode.KER_INTERNAL_FAILED
        db_results = {}
        db_results[cs.resp_code] = resp_code
        db_results[cs.error_msg] = cs.ResponseMsg.MSG_INTERNAL_ERROR
        query_key_mapping = {}
        knowledge_dict = {}
        similarity_key = {}

        # extract topic , product type all basic info of query from dict
        topic = query_basic_info[cs.XMLTags.TOPIC_TAG]
        modelno = query_basic_info[cs.MODEL_TR]
        product = query_basic_info[cs.RS_PRODUCT_TYPE]
        prod_sub_type = product

        # if product is washing machine family , identifying special type washer/dryer
        if product == products.WASHING_MACHINE_GEN_NAME:
            prod_sub_type = self.subkey_extractor.get_kepler_product_type(question)

        for index in range(0, self.max_predictions):
            # map the info engine and classifier knowledge to db knowledge
            query_key_mapping, topic, query_intent, knowledge_dict, similarity_key = self.__map_to_db_knowledge(
                question, query_basic_info, similarity_output, query_intent, index)

            if query_key_mapping is None or not bool(query_key_mapping) == True:
                logger.error("query_key_mapping is none")
                continue

            logger.debug("product sub type=%s", prod_sub_type)
            # add product sub type in key mapping dict for query
            query_key_mapping[cs.PRODUCT_TYPE] = prod_sub_type

            logger.debug("query_key_mapping=(%s) Query classifier result=%s" %
                         (query_key_mapping, query_intent))
            # pass entity , relationship to DBInterface
            db_results, resp_code = self.db_interface.retrieve_knowledge(query_key_mapping, topic,
                                                              modelno, query_intent, knowledge_dict)

            logger.debug("db_results=%s, resp_code=%s",db_results, resp_code)
            if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS:
                # check for valid responses and form db results json response
                if self._validate_dbresult(db_results, topic):
                    logger.debug("SPEC/TROB section got some valid results")
                    break
                else:
                    continue
            else:
                break

        logger.debug("#db_results=%s", db_results)
        return db_results, query_key_mapping, topic, query_intent, knowledge_dict, similarity_key, resp_code

    def __get_para_from_db(self, sub_section, modelno, sub_section_type): # pragma: no cover
        """
            This function is used to form para from graph
            Args:
                sub_section:str
                        sub_section of user query
                modelno : str
                          modelno of which answer is to be retrieved
            Returns:
               paragraph : string
        """
        db_relation = ""
        sub_section_type = sub_section_type.lower()

        # map DB relation with classifier output
        if sub_section_type == cs.ProblemTypes.CONTROL_PANEL:
            db_relation = cs.HAS_CONTROL_PANEL_FEATURE
        elif sub_section_type == cs.FEATURE:
            db_relation = cs.HAS_FEATURE
        elif sub_section_type == cs.CHECKLIST.lower():
            db_relation = cs.HAS_CHECKLIST
        elif sub_section_type == cs.ProblemTypes.COMPONENT:
            db_relation = cs.HAS_COMPONENT

        # call db engine to form paragraph
        paragraph, resp_code = self.db_interface.retrieve_para_from_graph(db_relation, modelno, sub_section)
        return db_relation, paragraph, resp_code

    def __form_resp_para_retrieval(self, output, sub_section, db_relation, sub_section_type):# pragma: no cover
        """
            This function is used to form para from graph and calls boolqa
            to retrieve answer of given question of unstructed query
            Args:
                output : json string
                          output of paraqa answer
                sub_section:str
                        sub_section of user query
                db_relation : dict
                           extracted  info mapped to db knowledge
                sub_section_type:str
                        sub_section type of user query
            Returns:
               retrieve_response : json string
        """
        db_results = {}
        db_results[cs.REASON_KEY] = []
        db_results[cs.SOLUTION_KEY] = []
        db_results[cs.VALUE] = []
        db_results[cs.DESC_KEY] = []
        db_results[cs.FEATURE] = []
        db_results[cs.MEDIA_URL] = []
        db_results[cs.MEDIA_TYPE] = []
        db_results[cs.MEDIA_SIZE] = []

        query_key_mapping = {}
        output = json.loads(output)
        feature = []
        desc = []

        logger.debug("output : %s",output)
        if output[cs.resp_code] == cs.ResponseCode.SUCCESS:
            answer = output[cs.resp_data][cs.ProblemTypes.ANSWERS]
            # TODO list of answers to be supported
            desc.append(answer[0])
            feature.append(sub_section_type)
            db_results[cs.DESC_KEY] = desc
            db_results[cs.FEATURE] = feature
        else:
            logger.error("ParaQA retrieval output error")
            db_results = output
        # form query key mapping
        intent_dict = dict()
        intent_dict[cs.PROP_VALUE] = sub_section
        intent_dict[cs.INTENT] = db_relation
        intent_dict[cs.PROP_KEY] = sub_section_type
        query_key_mapping.update(intent_dict)
        query_key_mapping[cs.InfoKnowledge.KEY] = sub_section_type
        return db_results, query_key_mapping

    def __get_answer_from_boolqa(self, modelno, question, sub_section_type, sub_section):# pragma: no cover
        """
            This function is used to form para from graph and calls boolqa
            to retrieve answer of given question of unstructed query
            Args:
                modelno : str
                          modelno of which answer is to be retrieved
                question : str
                           user question
                sub_section_type:str
                        sub_section type of user query
                sub_section:str
                        sub_section of user query
            Returns:
               retrieve_response : json string
        """
        # call boolQA
        logger.debug("boolQA called")

        # get paragraph for the sub section
        db_relation, paragraph, resp_code = self.__get_para_from_db(sub_section, modelno, sub_section_type)

        logger.debug("paragraph=%s, resp_code=%s",paragraph, resp_code)

        # check if paragraph has text
        if (resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS) and (len(paragraph) > 0):
            # call to info engine boolqa
            output = self.nlp_eng_client.get_answer_from_boolqa([paragraph], [question])
            logger.debug("boolqa output from info_engine=(%s)" % str(output))
            # form resp from boolqa module
            db_results, query_key_mapping = self.__form_resp_para_retrieval(output, sub_section, db_relation,
                                                                            sub_section_type)
        else:
            output = paragraph
            # form resp from para qa module
            db_results, query_key_mapping = self.__form_resp_para_retrieval(output, sub_section, db_relation,
                                                                            sub_section_type)

        return db_results, query_key_mapping, resp_code

    def __get_answer_from_paraqa(self, modelno, question, sub_section_type, sub_section):# pragma: no cover
        """
            This function is used to form para from graph and calls paraqa
            to retrieve answer of given question of unstructed query

            Args:
                modelno : str
                          modelno of which answer is to be retrieved
                question : str
                           user question
                sub_section_type:str
                        sub_section type of user query
                sub_section:str
                        sub_section of user query
            Returns:
               retrieve_response : json string
        """
        # call paraQA
        logger.debug("paraQA called")

        # get paragraph for the sub section
        db_relation, paragraph, resp_code = self.__get_para_from_db(sub_section, modelno, sub_section_type)
        logger.debug("paragraph=%s, resp_code=%s", paragraph, resp_code)
        # check if paragraph has text
        if (resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS) and (len(paragraph) > 0):
            # TODO call nlp engine client
            # call to info engine boolqa
            output = self.nlp_eng_client.get_answer_from_paraqa([paragraph], [question])
            logger.debug("paraQA output from nlp engine client=(%s)" % str(output))

            # form resp from para qa module
            db_results, query_key_mapping = self.__form_resp_para_retrieval(output, sub_section, db_relation,
                                                                            sub_section_type)
        else:
            output = paragraph
            # form resp from para qa module
            db_results, query_key_mapping = self.__form_resp_para_retrieval(output, sub_section, db_relation,
                                                                            sub_section_type)

        return db_results, query_key_mapping, resp_code

    def __get_problem_use_fulltext(self, modelno, intent, question):
        """
            finds related problem of user question using
            full text search
            Args:
                intent : str
                question : str
            Returns:
                problem : str
        """
        logger.debug("__find_problem_use_fulltext intent=%s question=%s", intent, question)
        # get SRL and Constituency parsers output of user question to
        # extract noun phrases and verb phrases
        srl_const_output = self.nlp_eng_client.get_srl_cons(question)

        # load the json string into a json
        srl_const_output = json.loads(srl_const_output)

        logger.debug("srl_const_output :" + str(srl_const_output))

        # Check for response_code
        if srl_const_output[cs.resp_code] != cs.ResponseCode.SUCCESS:
            return None

        # Get the response data as per the new format
        srl_const_output = srl_const_output[cs.resp_data]
        # extract only cons parser output
        const_output = srl_const_output[cs.InfoKnowledge.CONS_PARSER]
        logger.info("Const wrapper=(%s)", str(const_output))

        # extract noun,verb phrases separately
        noun_phrases = list(filter(len, const_output[cs.NP]))
        verb_phrases = list(filter(len, const_output[cs.VB]))
        # append query intent to verb phrases
        # verb_phrases.append(intent)

        # call db engine to get related problem key using full text search

        problem_key, problem_node_type, resp_code = self.db_interface.get_problem_key_from_fulltext(modelno, question,
                                                                                                    verb_phrases,
                                                                                                    noun_phrases)
        logger.debug("problem_key from db engine using full text=%s", problem_key)
        return problem_key, problem_node_type, resp_code

    def __update_relation_based_on_problemtype(self, problem_node_type):
        """
            used to update db relationship with the node type
            Args:
                problem_node_type : str
                                 problem key node type
            Returns:
                updated_relation : str
        """
        if problem_node_type == cs.FEATURE_NODE:
            updated_relation = cs.HAS_CONTROL_PANEL_FEATURE
        else:
            updated_relation = cs.HAS_OPERATION_SECTION
        return updated_relation

    def __get_answer_from_graphqa(self, query_basic_info, question, query_intent, question_type, sub_section_type,
                                  similarity_results):
        """
            This function is used to retrieve answer of given question of
            given model

            Args:
                query_basic_info : dict
                           contains query basic info model,product,intent,problem type
                question : str
                           user question
                query_intent: str
                          intent of the query
                question_type : str
                        type of input question
                sub_section_type: str
                        category of the question (feature/ checklist/ component/ storage)
                similarity_results : list
            Returns:
                db_results : dict
                            database results
                query_key_mapping : dict
                            Extracted information
                topic : str
                        section type
                query_intent : str
                        Question intent
                similarity_key : dict
                        Similarity key of user question
        """
        flag = cs.RetrievalConstant.TEXTSIM_BASED
        db_results = {}
        # extract topic , product type all basic info of query from dict
        topic = query_basic_info[cs.XMLTags.TOPIC_TAG]
        sub_section = query_basic_info[cs.RespKeys.PROB_TYPE]
        product = query_basic_info[cs.RS_PRODUCT_TYPE]
        prod_sub_type = product
        modelno = query_basic_info[cs.MODEL_TR]

        logger.debug("product=%s modelno=%s topic=%s type=%s question_type=%s sub_section=%s similarity_results=%s" % (
            product, modelno, topic, sub_section, question_type, sub_section_type, str(similarity_results)))
        # 1) call DB engine based on Text similarity and Classifier results
        logger.debug("Text Similarity will be called")

        # get canonical key and mapping
        oper_mapping, similarity_key = self.__extract_canonical_key(similarity_results, 0)

        # get relation for the question
        query_key_mapping = IntentSchema.get_intent(similarity_key, topic)
        if query_key_mapping is None:
            logger.error("query_key_mapping is none")
            return db_results, None, topic, query_intent, None, similarity_key, cs.ResponseCode.INTERNAL_ERROR
        else:
            query_key_mapping[cs.InfoKnowledge.PROB_VAL_SPECI] = similarity_key

        # if product is washing machine family , identifying special type washer/dryer
        if product == products.WASHING_MACHINE_GEN_NAME:
            prod_sub_type = self.subkey_extractor.get_kepler_product_type(question)

        # since classifier has 95% accuracy , currently taking L1 key from classifier
        # instead of text similarity
        query_key_mapping[cs.PROP_VALUE] = sub_section
        query_key_mapping[cs.PROP_KEY] = cs.ProblemTypes.DIRECT_INFO
        # add product sub type in key mapping dict for query
        query_key_mapping[cs.PRODUCT_TYPE] = prod_sub_type

        similarity_key = oper_mapping
        if query_intent in [cs.ProblemTypes.EXTRA_WARNING, cs.ProblemTypes.EXTRA_CAUTION,
                            cs.ProblemTypes.EXTRA_NOTE]:
            query_key_mapping[cs.PROP_KEY] = cs.ProblemTypes.EXTRA_INFO

        # TODO: analyze more
        # changing relationship name considering classifier output
        if sub_section_type == cs.ProblemTypes.CONTROL_PANEL:
            query_key_mapping[cs.INTENT] = cs.HAS_CONTROL_PANEL_FEATURE

        logger.debug("query_key_mapping=%s", query_key_mapping)
        # pass entity , relationship, extracted info to DBInterface to get answer
        db_results, resp_code = self.db_interface.retrieve_knowledge(query_key_mapping, topic,
                                                                     modelno, query_intent, None)
        # 2) if db returns empty results, fallback to full text search approach
        if (resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS) and (
                self._validate_dbresult(db_results, topic) is False):
            # call full text based search to find problem statement
            logger.debug("Full Test search will be executed")
            related_problem_key, problem_node_type, resp_code = self.__get_problem_use_fulltext(modelno, query_intent,
                                                                                                question)
            # if full text search results are none, return empty results
            if related_problem_key is None:
                return db_results, query_key_mapping, topic, query_intent, similarity_key, flag, resp_code

            # update db relationship based on full text problem node type
            updated_relation = self.__update_relation_based_on_problemtype(problem_node_type)
            query_key_mapping[cs.INTENT] = updated_relation
            # Flag to use full text search while querying
            query_key_mapping[cs.RetrievalConstant.QUERY_METHOD] = cs.RetrievalConstant.USE_FULL_TEXT_FLAG

            if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS:
                # when db results are none, retrying again to retrieve with problem key that we find
                # using full text search
                query_key_mapping[cs.InfoKnowledge.PROB_VAL_SPECI] = related_problem_key
                db_results, resp_code = self.db_interface.retrieve_knowledge(query_key_mapping, topic,
                                                                             modelno, query_intent, None)

        return db_results, query_key_mapping, topic, query_intent, similarity_key, flag, resp_code

    def __retrieve_operation_section(self, query_basic_info, question, query_intent, question_type, sub_section_type,
                                     similarity_results):
        """
            This function is used to retrieve answer of given question of
            given model

            Args:
                query_basic_info : dict
                           contains query basic info model,product,intent,problem type
                question : str
                           user question
                query_intent: str
                          intent of the query
                question_type : str
                        type of input question
                sub_section_type: str
                        category of the question (feature/ checklist/ component/ storage)
                similarity_results : dict
                        list of similarity keys dict
            Returns:
                db_results : dict
                            database results
                query_key_mapping : dict
                            Extracted information
                topic : str
                        section type
                query_intent : str
                        Question intent
                similarity_key : dict
                        Similarity key of user question
        """
        # extract topic and type all basic info of query from dict
        resp_code = -1
        sub_section = query_basic_info[cs.RespKeys.PROB_TYPE]
        modelno = query_basic_info[cs.MODEL_TR]

        logger.debug("query_basic_info=%s question_type=%s sub_section=%s similarity_results=%s" % (
        str(query_basic_info), question_type,
        sub_section_type, str(similarity_results)))

        # if not able to get query intent,set default to desc
        if query_intent is None:
            query_intent = cs.ProblemTypes.DESCRIPTION

        # 1) retrieve answer from graph based on classifier/text sim info or full text search
        db_results, query_key_mapping, topic, query_intent, similarity_key, flag, resp_code = self.__get_answer_from_graphqa(
            query_basic_info, question, query_intent, question_type, sub_section_type, similarity_results)

        # 2) if db_results not valid then paraQA or BoolQA based on the QuestionTypes
        # falling back to paraQA or BoolQA  approach when graph based qa fails
        if (resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS) and \
                (self._validate_dbresult(db_results, topic) is False):# pragma: no cover
            if question_type == cs.QuestionTypes.FACTOID:
                # invoke call to form para and get answer
                db_results, query_key_mapping, resp_code = self.__get_answer_from_paraqa(modelno, question, sub_section_type,
                                                                              sub_section)
                # add code to push extra info here to the above function
                similarity_key = query_key_mapping
                flag = cs.RetrievalConstant.PARA_QA
            elif question_type == cs.QuestionTypes.BOOL:
                # invoke call to form para and get answer
                db_results, query_key_mapping, resp_code = self.__get_answer_from_boolqa(modelno, question, sub_section_type,
                                                                              sub_section)
                similarity_key = query_key_mapping
                flag = cs.RetrievalConstant.BOOL_QA

        return db_results, query_key_mapping, topic, query_intent, None, similarity_key, flag, resp_code

    def __input_verification(self, modelno, product_type):
        """
            This function is used to validate input args model no
            and product type

            Args:
                modelno : str
                          modelno of which answer is to be retrieved
                product_type : str
                            product type of user question
            Returns:
               resp_code : int
                        response code
               resp_msg : str
                        response message
               product_type : str
                          updated product type of user question
        """
        resp_code = cs.ResponseCode.SUCCESS
        resp_msg = ""

        logger.info("modelno=(%s) product_type=(%s) " % (modelno, product_type))
        if modelno is None:
            logger.error("modelno is none")
            resp_code = cs.ResponseCode.BAD_REQUEST
            resp_msg = cs.ResponseMsg.MSG_INVALID_REQUEST

        # if product type is empty ,call DBEngine and get product type
        if product_type is None or product_type == "":
            product_type, resp_code = self.db_interface.retrieve_product_type(modelno)
            if len(product_type.strip()) <= 0:
                logger.error("product type is none")
                resp_code = cs.ResponseCode.INTERNAL_ERROR
                resp_msg = cs.ResponseMsg.MSG_PRODTYPE_NOT_FOUND
        return resp_code, resp_msg, product_type

    def __make_resp_with_allinfo(self, query_basic_info, db_results, query_key_mapping, similarity_key,
                                 resp_header, knowledge_dict, ques_details):
        """
            function is to form the json response with all info

            Args:
                query_basic_info : dict
                           contains query basic info model,product,intent,problem type
                db_results : dict
                          results fetched from DB
                query_key_mapping : dict
                          Info Extraction output
                similarity_key : dict
                          Info Engine similarity key
                resp_header : dict
                          resp_code and resp_msg
                knowledge_dict : dict
                          cons parser,srl output
            Returns:
                retrieve_response : json string
        """
        flag, question_type, resp_code = ques_details[0], ques_details[1], ques_details[2]
        topic = query_basic_info[cs.XMLTags.TOPIC_TAG]
        product_type = query_basic_info[cs.RS_PRODUCT_TYPE]
        modelno = query_basic_info[cs.MODEL_TR]
        problem_type = query_basic_info[cs.RespKeys.PROB_TYPE]
        query_intent = query_basic_info[cs.RespKeys.INTENT]

        logger.debug("db_results=%s,resp_code=%s",db_results,resp_code)

        if (resp_code == cs.ResponseCode.KER_INTERNAL_FAILED) or (resp_code == cs.ResponseCode.CONNECTION_ERROR) \
                or (resp_code == cs.ResponseCode.CLIENT_ERROR):
            resp_header[cs.resp_code] = db_results[cs.resp_code]
            resp_header[cs.resp_data] = db_results[cs.error_msg]
            dict_resp = {}
        # if db results are empty
        elif not bool(db_results) == True:
            resp_header[cs.resp_code] = cs.ResponseCode.DATA_NOT_FOUND
            resp_header[cs.resp_data] = cs.ResponseMsg.MSG_DATA_NOT_FOUND
            dict_resp = {}
        else:
            question_detail = flag, question_type
            dict_resp, resp_code = self.__make_dict_resp(product_type, modelno, topic, db_results,
                                                         query_key_mapping, question_detail)
            resp_header[cs.resp_code] = resp_code

        extracted_info = dict()
        extracted_info[cs.ProblemTypes.SECTION] = topic.lower()
        extracted_info[cs.RespKeys.INTENT] = query_intent
        extracted_info[cs.ProblemTypes.SUB_SECTION] = problem_type

        query_key_mapping[cs.InfoKnowledge.KEY] = similarity_key[cs.InfoKnowledge.KEY]
        logger.info("similarity_key=(%s) dict_resp=(%s)"
                    " query_key_mapping=(%s)" % (similarity_key,
                                                 dict_resp, query_key_mapping))
        # form json response of all extracted information for the user query
        retrieve_response = self.__form_json_resp(resp_header, extracted_info,
                                                  query_key_mapping, knowledge_dict, dict_resp)
        logger.info("similarity_key=(%s) dict_resp=(%s)"
                    " query_key_mapping=(%s)" % (similarity_key,
                                                 dict_resp, query_key_mapping))
        return retrieve_response

    def retrieve_knowledge(self, question, modelno, product_type, classifier_output, similarity_output):
        """
            This function is used to retrieve answer of given question of
            given model

            Args:
                question : str
                           user question
                modelno : str
                          modelno of which answer is to be retrieved
                product_type : str
                            product type of user question
                classifier_output : json string
                           classifier output of user query
                similarity_output : list
                           list of top 3 similarity keys dict
            Returns:
               retrieve_response : json string
        """
        flag = None
        resp_header = dict()
        logger.info("Input question=(%s) modelno=(%s) product_type=(%s) "
                    "classifier_op=%s similarity_op=%s " % (question, modelno, product_type, str(classifier_output),
                                                            str(similarity_output)))

        resp_code, resp_msg, product_type = self.__input_verification(modelno, product_type)
        if resp_code != cs.ResponseCode.SUCCESS:
            resp_header[cs.resp_code] = resp_code
            resp_header[cs.resp_data] = resp_msg
            retrieve_resp = self.__form_json_resp(resp_header)
            return retrieve_resp

        # call classifier engine and get all classifier results
        resp_code, topic, query_intent, problem_type, question_type, sub_category = self.__extract_classifier_info(question,
                                                                                                     classifier_output)
        if resp_code != cs.ResponseCode.SUCCESS:
            resp_header[cs.resp_code] = cs.ResponseCode.INTERNAL_ERROR
            resp_header[cs.resp_data] = cs.ResponseMsg.MSG_CLASSI_ERROR
            retrieve_resp = self.__form_json_resp(resp_header)
            return retrieve_resp

        # dict which has all basic info of user query
        query_basic_info = dict()
        query_basic_info[cs.XMLTags.TOPIC_TAG] = topic
        query_basic_info[cs.RespKeys.PROB_TYPE] = problem_type
        query_basic_info[cs.RS_PRODUCT_TYPE] = product_type
        query_basic_info[cs.MODEL_TR] = modelno

        # Currently operation QA is supported only for Washing machine & refrigerator
        if (topic == cs.Section.OPERATION) and (product_type == products.REFRIGERATOR_GEN_NAME or product_type == products.WASHING_MACHINE_GEN_NAME):
            logger.debug("Operation question ")
            db_results, query_key_mapping, topic, query_intent, knowledge_dict, similarity_key, flag, resp_code = \
                self.__retrieve_operation_section(query_basic_info, question, query_intent, question_type, sub_category,
                                                  similarity_output)
            # if fails to find similarity key
            if query_key_mapping is None or similarity_key is None:
                resp_header[cs.resp_code] = cs.ResponseCode.INTERNAL_ERROR
                resp_header[cs.resp_data] = cs.ResponseMsg.MSG_SIMIKEY_ERROR
                retrieve_resp = self.__form_json_resp(resp_header)
                return retrieve_resp
        else:
            # section classifier of user query
            # TODO: Classifier for FAQ should be handled
            # if ques_topic == cs.Section.FAQ:
            #     topic = ques_topic

            logger.info("Identified Topic =%s" % topic)

            logger.info("Textsim Pipeline  output=(%s)" % str(similarity_output))
            # map classifier , text sim information to db knowledge and retrieve answers from db
            db_results, query_key_mapping, topic, query_intent, knowledge_dict, similarity_key, resp_code= \
                self.__map_intent_and_retrieve_knowledge(question, query_basic_info, similarity_output, query_intent)

        # update query intent in query_basic_info dictionary
        query_basic_info[cs.RespKeys.INTENT] = query_intent

        # make final response with all extracted info
        ques_details = flag, question_type, resp_code
        retrieve_response = self.__make_resp_with_allinfo(query_basic_info, db_results, query_key_mapping,
                                                          similarity_key, resp_header, knowledge_dict, ques_details)
        logger.debug("retrieve_response : %s ", retrieve_response)
        return retrieve_response

    def retrieve_models(self, product_type=None):
        """
            This function is used to retrieve sorted model nos from
            graph database
            Args:
                product_type:str
                             product type of which models to be retrieved
            Returns:
                response : json string
        """
        response = {}
        # retrieve all models for all products in database
        models, resp_code = self.db_interface.retrieve_model_nos(product_type)
        logger.debug("models list from database=%s" % str(models))
        # if models dict is empty
        if (resp_code == cs.ResponseCode.CLIENT_ERROR) or (resp_code == cs.ResponseCode.CONNECTION_ERROR) or \
            (resp_code == cs.ResponseCode.INTERNAL_ERROR):
            response[cs.resp_code] = resp_code
            response[cs.error_msg] = cs.ResponseMsg.MSG_DATA_NOT_FOUND
        else:
            # check all product list and add empty list if no models found
            # for any product
            product_list = [products.WASHING_MACHINE_GEN_NAME, products.REFRIGERATOR_GEN_NAME,
                            products.AIR_CONDITIONER_GEN_NAME,
                            products.VACUUM_CLEANER_GEN_NAME, products.MICROWAVE_OVEN_GEN_NAME,
                            products.DISH_WASHER_GEN_NAME]
            for product in product_list:
                if product not in models.keys():
                    models[product] = []
            logger.debug("modified models list from database=%s" % str(models))
            response[cs.resp_code] = cs.ResponseCode.KER_INTERNAL_SUCCESS
            response[cs.resp_data] = models
        response = json.dumps(response)
        logger.info("models list response=%s" % response)
        return response


if __name__ == "__main__":# pragma: no cover
    user_query = "Drain pipe is damaged in my washing machine. How to fix?"
    model = "WM4500H*"
    pipeline = "1"
    section = "Troubleshooting"
    product_type = "washing machine"
    classifier_output = {"response_code": 200,
                         "response_data": {"Topic": "Troubleshooting", "Follow_up": False, "Intent": "cause-sol",
                                           "Type": "error"}}

    classifier_output = json.dumps(classifier_output)
    # logger configurtion
    logger.basicConfig(level=logger.INFO,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    # creating instance of tablextractor
    engine = KnowledgeRetriever.get_instance()

    resp = engine.retrieve_knowledge(user_query, model, pipeline,
                                     section, product_type, classifier_output)
    print("Answer from database:", resp)
