"""
/*-------------------------------------------------
* Copyright(c) 2020-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import json
import os.path
from configparser import ConfigParser
import importlib

from .knowledge.database import DBInterface
from .constants import params as cs
from .mapping.key_mapper import ProductKeyMapper
from .constants.params import GenericProductNameMapping
from .response.response_engine import ResponseEngine
from .info_extraction.subkey_extractor import SubKeysExtractor
from ..nlp_engine_client import NlpEngineClient

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'config', 'configuration.ini'))

logger.info("CONFIG_PATH=%s", CONFIG_PATH)
# constants to use pipeline
TEXT_SIM = 1
INFO_EXT = 2

# Supported products for operation section
SUPPORTED_PRODUCTS_OPER = [GenericProductNameMapping.WASHING_MACHINE_GEN_NAME, GenericProductNameMapping.PRD_KEPLER,
                           GenericProductNameMapping.DRYER_GEN_NAME, GenericProductNameMapping.STYLER_GEN_NAME]

SUPPORTED_SUB_PRODUCTS_OPER = [GenericProductNameMapping.DRYER_GEN_NAME,
                               GenericProductNameMapping.STYLER_GEN_NAME,
                               GenericProductNameMapping.PRD_KEPLER,
                               GenericProductNameMapping.FRONT_LOADER_GEN_NAME]

# Supported products for trob section
SUPPORTED_PRODUCTS_TROB = [GenericProductNameMapping.WASHING_MACHINE_GEN_NAME,
                           GenericProductNameMapping.DRYER_GEN_NAME, GenericProductNameMapping.STYLER_GEN_NAME,
                           GenericProductNameMapping.REFRIGERATOR_GEN_NAME]

SUPPORTED_SUB_PRODUCTS_TROB = [GenericProductNameMapping.DRYER_GEN_NAME,
                               GenericProductNameMapping.STYLER_GEN_NAME,
                               GenericProductNameMapping.PRD_KEPLER,
                               GenericProductNameMapping.MINI_WASHER_GEN_NAME,
                               GenericProductNameMapping.FRONT_LOADER_GEN_NAME,
                               GenericProductNameMapping.TOP_LOADER_GEN_NAME,
                               GenericProductNameMapping.REF_LARGE_GEN_NAME,
                               GenericProductNameMapping.REF_MEDIUM_GEN_NAME,
                               GenericProductNameMapping.REF_KIMCHI_GEN_NAME]


class IntentSchema(object):
    """
    defines the method to retrieve intent schema
    """

    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if IntentSchema.__instance is None:
            IntentSchema()
        return IntentSchema.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if IntentSchema.__instance is not None:
            logger.error("IntentSchema is not instantiable")
            raise Exception("IntentSchema is not instantiable")
        else:
            logger.debug("*** IntentSchema constructor")
            self.trob_intent = {}
            self.oper_intent = {}
            IntentSchema.__instance = self

    def _load_intentmapping_json(self, topic, product_type=None, sub_prd_type=None):
        """
           get the file path from config and convert
           the schema to dict and parse the schema
        """
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        logger.info("Config path" + CONFIG_PATH)
        current_file_path = os.path.realpath(__file__)
        parent_directory_1 = os.path.dirname(current_file_path)
        parent_directory_2 = os.path.dirname(parent_directory_1)
        ker_ko_path = os.path.abspath(os.path.join(parent_directory_2))

        # Naming convention followed for the files in /dataset/dataset/info_data
        trob_intent_files_suffix = "_TROB_INTENT.json"
        oper_intent_files_suffix = "_OPERATION_INTENT.json"
        intent_file_suffix = ""
        if topic == cs.TROB_SECTION:
            intent_file_suffix = trob_intent_files_suffix
        elif topic == cs.Section.OPERATION:
            intent_file_suffix = oper_intent_files_suffix

        dataset_folder_path = config_parser.get("intent_files", "intent_files_path")

        # intent_file_path --> "prefix_path" + "product_type" + "intent_file_suffix"
        # prefix_path --> ker_ko_path + dataset_folder_path
        intent_file_path = ""

        if product_type != sub_prd_type:
            json_file_name = str(product_type + "_" + sub_prd_type) + intent_file_suffix
            intent_file_path = os.path.join(ker_ko_path, dataset_folder_path, product_type, sub_prd_type, json_file_name)
        else:
            json_file_name = str(product_type) + intent_file_suffix
            intent_file_path = os.path.join(ker_ko_path, dataset_folder_path, product_type, json_file_name)

        logger.debug("intent json file path:" + intent_file_path)
        # Opening JSON file
        with open(intent_file_path) as f:
            # returns JSON object as a dictionary
            intent_mapping = json.load(f)

        return intent_mapping

    def load_intent(self, topic=None, product_type=None, sub_prd_type=None):
        """
        Loads the intent based on product and sub-product type

        Args:
            topic: topic or section
            product_type: product type of json
            sub_prd_type: sub product type of json
        """
        if topic == cs.TROB_SECTION:
            self.trob_intent[(product_type, sub_prd_type)] = self._load_intentmapping_json(topic, product_type,
                                                                                        sub_prd_type)
        elif topic == cs.Section.OPERATION:
            self.oper_intent[(product_type, sub_prd_type)] = self._load_intentmapping_json(topic, product_type,
                                                                                        sub_prd_type)

    def get_intent(self, question, section=None, product_type=None, sub_prd_type=None):
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
            logger.debug("type =(%s) key:(%s)" % (type(question), question))
            intent_json_file = self._load_intent_json_file(section, product_type, sub_prd_type)
            intent = intent_json_file.get(question, {})
            logger.debug("intent return:(%s)", intent)
            return intent
        except KeyError:
            logger.exception("Key doesn't exist!=%s", str(question))
            return None

    def _load_intent_json_file(self, section, product_type, sub_prd_type):
        intent_json_file = {}
        # For washing machine --> washing_machine
        # logger.debug("IntentSchema.__dict__ :%s",IntentSchema.__dict__)
        if section == cs.TROB_SECTION:
            intent_json_file = self.trob_intent[(product_type, sub_prd_type)]
        elif section == cs.Section.OPERATION:
            intent_json_file = self.oper_intent[(product_type, sub_prd_type)]
        logger.debug("loaded intent json file: {}".format(intent_json_file))
        return intent_json_file


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

            prd_subprd_model_dict, resp_code = self.db_interface.retrieve_part_nos(None)

            # instance for IntentSchema loading
            self.intent_schema = IntentSchema.get_instance()

            for prd_type, sub_prd_type in prd_subprd_model_dict.keys():
                logger.debug("***********************loading intent jsons***********************");
                if (prd_type in SUPPORTED_PRODUCTS_TROB) and (sub_prd_type in SUPPORTED_SUB_PRODUCTS_TROB):
                    logger.debug("-----------------loading trob intent json--------------------------");
                    self.intent_schema.load_intent(cs.TROB_SECTION, prd_type, sub_prd_type)
                if (prd_type in SUPPORTED_PRODUCTS_OPER) and (sub_prd_type in SUPPORTED_SUB_PRODUCTS_OPER):
                    self.intent_schema.load_intent(cs.Section.OPERATION, prd_type, sub_prd_type)
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
            if (db_results is not None) and (len(db_results[cs.REASON_KEY]) > 0) or (
                    len(db_results[cs.SOLUTION_KEY]) > 0):
                res = True
        elif (topic == cs.Section.SPEC) and (len(db_results[cs.VALUE]) > 0):
            res = True
        return res

    def _fill_only_feature(self, db_results):
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
            for idx, feature_desc in \
                    enumerate(zip(db_results[key1], db_results[key2])):
                feature_dict = dict()
                feature_dict[key1] = feature_desc[0]
                descrip = feature_desc[1]
                if descrip is None:
                    descrip = ""
                feature_dict[key2] = descrip
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

    def __make_dict_resp(self, product_type, partno, topic, db_results, respkey_dict, question_detail):
        """
            This function is used to form dict response for
            response_engine

            Args:
                product_type : str
                         product type of the given partno
                partno : str
                          partno of which answer is to be retrieved
                topic : str
                           manual section
                db_results : dict
                           dict object from DBInterface
                respkey_dict : dict
                           dict object of canonical question
            Returns:
                dict_resp : dict
        """
        dict_resp = dict()
        trob_dict = dict()
        spec_dict = dict()
        oper_dict = dict()

        resp_code = ""
        logger.info("db_results : %s", db_results)
        try:
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
            logger.debug("__make_dict_resp=%s", str(db_results))
            logger.exception("Exception : %s", e)
            resp_code = cs.ResponseCode.DATA_NOT_FOUND
        finally:
            dict_resp[cs.SPECIFICATION_TAG] = spec_dict
            dict_resp[cs.XMLTags.TROUBLESHOOT_TAG] = trob_dict
            dict_resp[cs.XMLTags.OPERATION_TAG] = oper_dict
            dict_resp[cs.IOConstants.PART_NO] = partno
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
        key_info = query_key_mapping.get(cs.InfoKnowledge.KEY, "")

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
        extracted_info[cs.PROP_VALUE] = query_key_mapping.get(cs.PROP_VALUE, "")
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

        logger.info("Begin (%s)" % question)

        if classifier_output is None:
            return cs.ResponseCode.DATA_NOT_FOUND, topic, intent, problem_type, category_type
        output = classifier_output

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
        logger.info("Begin __extract_canonical_key extracted_knowledge=(%s) prediction_index=%d", extracted_knowledge,
                     prediction_index)

        # get template key of user question
        key_mapping = extracted_knowledge[prediction_index]

        # extract canonical key key
        key = key_mapping[cs.InfoKnowledge.KEY]

        # remove leading/trailing spaces and trailing dot
        canonical_key = key.strip().rstrip('.')
        canonical_key = canonical_key.lower()
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
                              contains query basic info partno,product,intent,problem type
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
        similarity_key = {}

        # extract topic , product type all basic info of query from dict
        topic = query_basic_info[cs.XMLTags.TOPIC_TAG]
        problem_type = query_basic_info[cs.RespKeys.PROB_TYPE]
        product = query_basic_info[cs.RS_PRODUCT_TYPE]
        sub_prd_type = query_basic_info[cs.RS_SUB_PRODUCT_TYPE]

        logger.info("### similarity_output=%s topic=%s query_intent=%s problem_type=%s product=%s index=%d sub_prd_type=%s"  %
                     (similarity_output, topic, query_intent, problem_type, product, prediction_index, sub_prd_type))

        # if user query belongs to troubleshooting section or operation section
        if topic == cs.TROB_SECTION:
            # text similarity approach, get canonical key and mapping
            ts_mapping, similarity_key = self.__extract_canonical_key(similarity_output, prediction_index)

            # get relation for the question
            # sending the sub product type instead of product because intent json variable maintained
            # based on sub-prd type
            query_key_mapping = self.intent_schema.get_intent(similarity_key, topic, product, sub_prd_type)
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
                                contains query basic info partno,product,intent,problem type
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
        logger.info("calling __map_intent_and_retrieve_knowledge")
        resp_code = cs.ResponseCode.KER_INTERNAL_FAILED
        db_results = {}
        db_results[cs.resp_code] = resp_code
        db_results[cs.error_msg] = cs.ResponseMsg.MSG_INTERNAL_ERROR
        query_key_mapping = {}
        knowledge_dict = {}
        similarity_key = {}

        # extract topic , product type all basic info of query from dict
        topic = query_basic_info[cs.XMLTags.TOPIC_TAG]
        partno = query_basic_info[cs.IOConstants.PART_NO]
        product = query_basic_info[cs.RS_PRODUCT_TYPE]
        sub_prd_type = query_basic_info[cs.RS_SUB_PRODUCT_TYPE]
        prod_sub_type = self._get_entity_prd_type(product, question, sub_prd_type)

        self.max_predictions = len(similarity_output)

        if self.max_predictions == 0:
            response_code = cs.ResponseCode.DATA_NOT_FOUND
            db_results[cs.resp_code] = response_code
            db_results[cs.error_msg] = cs.ResponseMsg.MSG_DATA_NOT_FOUND

        for index in range(0, self.max_predictions):
            # map the info engine and classifier knowledge to db knowledge
            query_key_mapping, topic, query_intent, knowledge_dict, similarity_key = self.__map_to_db_knowledge(
                question, query_basic_info, similarity_output, query_intent, index)

            if (query_key_mapping is None) or (not bool(query_key_mapping) == True):
                logger.error("query_key_mapping is none")
                continue

            logger.debug("product sub type=%s", prod_sub_type)
            # add product sub type in key mapping dict for query
            query_key_mapping[cs.PRODUCT_TYPE] = prod_sub_type

            logger.debug("query_key_mapping=(%s) Query classifier result=%s" %
                         (query_key_mapping, query_intent))
            # pass entity , relationship to DBInterface
            db_results, resp_code = self.db_interface.retrieve_knowledge(query_key_mapping, topic,
                                                                         partno, query_intent, knowledge_dict)

            logger.debug("db_results=%s, resp_code=%s", db_results, resp_code)
            if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS:
                # check for valid responses and form db results json response
                if self._validate_dbresult(db_results, topic):
                    logger.debug("SPEC/TROB section got some valid results")
                    break
                else:
                    continue
            else:
                break

        logger.info("#db_results=%s", db_results)
        return db_results, query_key_mapping, topic, query_intent, knowledge_dict, similarity_key, resp_code

    def _get_entity_prd_type(self, product, question, sub_prd_type):
        """
        get the entity prd_sub type to frame in cypher query

        Args:
            product: product type
            question: user query
            sub_prd_type: sub product type
        Return:
            entity_prd_type: List
            Ex: [washer, dryer] or [washer] or [refrigerator] ...
        """
        prod_sub_type = [product]
        # if product is kepler/washing machine family, identifying special type washer/dryer
        if sub_prd_type == GenericProductNameMapping.PRD_KEPLER or product == GenericProductNameMapping.WASHING_MACHINE_GEN_NAME:
            prod_sub_type = self.subkey_extractor.get_kepler_section_type(question)
        elif (sub_prd_type == GenericProductNameMapping.MINI_WASHER_GEN_NAME) or \
                (sub_prd_type == GenericProductNameMapping.TOP_LOADER_GEN_NAME):
            prod_sub_type = [GenericProductNameMapping.WASHER_SEC_NAME]
        return prod_sub_type

    def __get_problem_use_fulltext(self, partno, intent, question):
        """
            finds related problem of user question using
            full text search
            Args:
                partno : str
                intent : str
                question : str
            Returns:
                problem : str
        """
        logger.info("__find_problem_use_fulltext intent=%s question=%s", intent, question)
        # get SRL and Constituency parsers output of user question to
        # extract noun phrases and verb phrases
        # TODO: Will be enabled once SRL & cons is enabled for Korean
        verb_phrases = []
        noun_phrases = []

        # call db engine to get related problem key using full text search
        problem_key, problem_node_type, resp_code = self.db_interface.get_problem_key_from_fulltext(partno, question,
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
            given partno

            Args:
                query_basic_info : dict
                           contains query basic info partno,product,intent,problem type
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
        sub_prd_type = query_basic_info[cs.RS_SUB_PRODUCT_TYPE]
        prod_sub_type = product
        partno = query_basic_info[cs.IOConstants.PART_NO]

        logger.info("product=%s partno=%s topic=%s type=%s question_type=%s sub_section=%s similarity_results=%s" % (
            product, partno, topic, sub_section, question_type, sub_section_type, str(similarity_results)))
        # 1) call DB engine based on Text similarity and Classifier results
        logger.info("Text Similarity will be called")

        # get canonical key and mapping
        oper_mapping, similarity_key = self.__extract_canonical_key(similarity_results, 0)

        # get relation for the question
        query_key_mapping = self.intent_schema.get_intent(similarity_key, topic, product, sub_prd_type)
        if query_key_mapping is None:
            logger.error("query_key_mapping is none")
            return db_results, None, topic, query_intent, None, similarity_key, cs.ResponseCode.INTERNAL_ERROR

        query_key_mapping[cs.InfoKnowledge.PROB_VAL_SPECI] = similarity_key
        # Reset the QUERY_METHOD (So that for the first time Text similarity will be called)
        query_key_mapping[cs.RetrievalConstant.QUERY_METHOD] = None

        # if product is kepler/washing machine family , identifying special type washer/dryer
        if product == GenericProductNameMapping.PRD_KEPLER or product == GenericProductNameMapping.WASHING_MACHINE_GEN_NAME:
            prod_sub_type = self.subkey_extractor.get_kepler_section_type(question)

        logger.debug("query method is {}".format(query_key_mapping[cs.RetrievalConstant.QUERY_METHOD]))
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
                                                                     partno, query_intent, None)
        # 2) if db returns empty results, fallback to full text search approach
        if (resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS) and (
                self._validate_dbresult(db_results, topic) is False):
            # call full text based search to find problem statement
            logger.info("Full Test search will be executed")
            related_problem_key, problem_node_type, resp_code = self.__get_problem_use_fulltext(partno, query_intent,
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
                                                                             partno, query_intent, None)
                # falling back to paraqa approach when graph based qa fails
                if (resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS) and \
                        (self._validate_dbresult(db_results, topic) == False):
                    logger.error("Could not retrieve answer from database")
                # TODO: Will be enabled once MRC QA is enabled
                """
                # falling back to paraqa approach when graph based qa fails
                if self._validate_dbresult(db_results, topic) == False:
                    db_results, query_key_mapping, resp_code = self.__get_answer_from_paraqa(partno, question, sub_section_type,
                                                                                  sub_section)
                    flag = cs.RetrievalConstant.PARA_QA
                    logger.debug("From ParaQA : %s", db_results)
                    similarity_key = query_key_mapping
                """
        return db_results, query_key_mapping, topic, query_intent, similarity_key, flag, resp_code

    def __retrieve_operation_section(self, query_basic_info, question, query_intent, question_type, sub_section_type,
                                     similarity_results):
        """
            This function is used to retrieve answer of given question of
            given partno

            Args:
                query_basic_info : dict
                           contains query basic info partno,product,intent,problem type
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

        logger.debug("query_basic_info=%s question_type=%s sub_section=%s similarity_results=%s" % (
            str(query_basic_info), question_type,
            sub_section_type, str(similarity_results)))

        # TODO: Question classifier is not enabled for Korean. Will add conditions once the component is enabled
        # if not able to get query intent,set default to desc
        if query_intent is None:
            query_intent = cs.ProblemTypes.DESCRIPTION

        # retrieve answer from graph based on classifier/text sim info
        db_results, query_key_mapping, topic, query_intent, similarity_key, flag, resp_code = self.__get_answer_from_graphqa(
            query_basic_info, question, query_intent, question_type, sub_section_type, similarity_results)

        return db_results, query_key_mapping, topic, query_intent, None, similarity_key, flag, resp_code

    def __make_resp_with_allinfo(self, query_basic_info, db_results, query_key_mapping, similarity_key,
                                 resp_header, knowledge_dict, ques_details):
        """
            function is to form the json response with all info

            Args:
                query_basic_info : dict
                           contains query basic info partno,product,intent,problem type
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
        partno = query_basic_info[cs.IOConstants.PART_NO]
        problem_type = query_basic_info[cs.RespKeys.PROB_TYPE]
        query_intent = query_basic_info[cs.RespKeys.INTENT]

        logger.info("db_results=%s,resp_code=%s", db_results, resp_code)

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
            dict_resp, resp_code = self.__make_dict_resp(product_type, partno, topic, db_results,
                                                         query_key_mapping, question_detail)
            resp_header[cs.resp_code] = resp_code

        extracted_info = dict()
        extracted_info[cs.ProblemTypes.SECTION] = topic.lower()
        extracted_info[cs.RespKeys.INTENT] = query_intent
        extracted_info[cs.ProblemTypes.SUB_SECTION] = problem_type

        query_key_mapping[cs.InfoKnowledge.KEY] = similarity_key.get(cs.InfoKnowledge.KEY, "")
        logger.debug("similarity_key=(%s) dict_resp=(%s)"
                    " query_key_mapping=(%s)" % (similarity_key,
                                                 dict_resp, query_key_mapping))
        # form json response of all extracted information for the user query
        retrieve_response = self.__form_json_resp(resp_header, extracted_info,
                                                  query_key_mapping, knowledge_dict, dict_resp)
        logger.debug("similarity_key=(%s) dict_resp=(%s)"
                    " query_key_mapping=(%s)" % (similarity_key,
                                                 dict_resp, query_key_mapping))
        return retrieve_response

    def retrieve_knowledge(self, question, partno, product_type, sub_prd, classifier_output, similarity_output, modelno=None):
        """
            This function is used to retrieve answer of given question of
            given partno

            Args:
                question : str
                           user question
                partno : str
                          partno of which answer is to be retrieved
                product_type : str
                            product type of user question
                classifier_output : json string
                           classifier output of user query
                similarity_output : list
                           list of top 3 similarity keys dict
                modelno : str
                         modelno for which user looking for answer
            Returns:
               retrieve_response : json string
        """
        flag = None
        resp_header = dict()
        db_results = dict()
        query_key_mapping = dict()
        similarity_key = dict()
        knowledge_dict = dict()
        logger.info("Input question=(%s) partno=(%s) product_type=(%s) "
                    "classifier_op=%s similarity_op=%s modelno=%s" % (question, partno, product_type, str(classifier_output),
                                                            str(similarity_output), modelno))

        # call classifier engine and get all classifier results
        resp_code, topic, query_intent, problem_type, question_type, sub_category = self.__extract_classifier_info(
            question,
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
        query_basic_info[cs.RS_SUB_PRODUCT_TYPE] = sub_prd
        query_basic_info[cs.IOConstants.PART_NO] = partno


        if (topic == cs.Section.OPERATION) and (product_type in SUPPORTED_PRODUCTS_OPER):
            logger.info("Operation question ")
            db_results, query_key_mapping, topic, query_intent, knowledge_dict, similarity_key, flag, resp_code = \
                self.__retrieve_operation_section(query_basic_info, question, query_intent, question_type, sub_category,
                                                  similarity_output)
            # if fails to find similarity key
            if query_key_mapping is None or similarity_key is None:
                resp_header[cs.resp_code] = cs.ResponseCode.INTERNAL_ERROR
                resp_header[cs.resp_data] = cs.ResponseMsg.MSG_SIMIKEY_ERROR
                retrieve_resp = self.__form_json_resp(resp_header)
                return retrieve_resp
        elif (topic == cs.Section.TROB) and (product_type in SUPPORTED_PRODUCTS_TROB):
            logger.debug("Identified Topic =%s" % topic)

            logger.debug("Textsim Pipeline  output=(%s)" % str(similarity_output))
            # map classifier , text sim information to db knowledge and retrieve answers from db
            db_results, query_key_mapping, topic, query_intent, knowledge_dict, similarity_key, resp_code = \
                self.__map_intent_and_retrieve_knowledge(question, query_basic_info, similarity_output, query_intent)
        else:
            resp_code = -1
        # update query intent in query_basic_info dictionary
        query_basic_info[cs.RespKeys.INTENT] = query_intent

        logger.debug("retrieve_knowledge db_results: %s",db_results)
        # make final response with all extracted info
        ques_details = flag, question_type, resp_code
        retrieve_response = self.__make_resp_with_allinfo(query_basic_info, db_results, query_key_mapping,
                                                          similarity_key, resp_header, knowledge_dict, ques_details)
        return retrieve_response

    def retrieve_partnos(self, product_type=None):
        """
            This function is used to retrieve sorted part nos from
            graph database
            Args:
                product_type:str
                             product type of which models to be retrieved
            Returns:
                response : json string

            Ex:
            part nos dict  = {(washing machine, top loader):[part number1,part number2,...],
                           (washing machine, kepler):[part number1,part number2,...],
                           (washing machine, mini washer):[part number1,part number2,...],
                           (refrigerator, large):[part number1,part number2,...],
                           (refrigerator, medium):[part number1,part number2,...]
                         }
        """
        response = {}
        # retrieve all models for all products in database
        prd_subprd_model_dict, resp_code = self.db_interface.retrieve_part_nos(product_type)
        logger.info("models list from database=%s" % str(prd_subprd_model_dict))
        # if models dict is empty
        if (resp_code == cs.ResponseCode.CLIENT_ERROR) or (resp_code == cs.ResponseCode.CONNECTION_ERROR) or \
                (resp_code == cs.ResponseCode.INTERNAL_ERROR):
            response[cs.resp_code] = resp_code
            response[cs.error_msg] = cs.ResponseMsg.MSG_DATA_NOT_FOUND
        else:
            # check all product list and add empty list if no models found
            # for any product
            product_list = [GenericProductNameMapping.WASHING_MACHINE_GEN_NAME, GenericProductNameMapping.PRD_KEPLER,
                           GenericProductNameMapping.DRYER_GEN_NAME, GenericProductNameMapping.STYLER_GEN_NAME,
                           GenericProductNameMapping.REFRIGERATOR_GEN_NAME]
            for product in product_list:
                if not any(product in prd_type for prd_type in prd_subprd_model_dict.keys()):
                    prd_subprd_model_dict[(product, product)] = []
            response[cs.resp_code] = cs.ResponseCode.KER_INTERNAL_SUCCESS
            response[cs.resp_data] = prd_subprd_model_dict
        logger.debug("models list response=%s" % response)
        return response

    def retrieve_partnumber(self, model_number=None):
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
        logger.info("request model no : %s",model_number)
        partnumber, resp_code = self.db_interface.retrieve_partnumber(model_number)
        logger.debug("partnumber from database=%s" % str(partnumber))
        # if models dict is empty
        if (resp_code == cs.ResponseCode.CLIENT_ERROR) or (resp_code == cs.ResponseCode.CONNECTION_ERROR) or \
                (resp_code == cs.ResponseCode.INTERNAL_ERROR):
            response[cs.resp_code] = resp_code
            response[cs.error_msg] = cs.ResponseMsg.MSG_DATA_NOT_FOUND
        else:
            response[cs.resp_code] = resp_code
            response[cs.resp_data] = partnumber
        return response

if __name__ == "__main__":
    user_query = "Drain pipe is damaged in my washing machine. How to fix?"
    partno = "MFL71485465"
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

    resp = engine.retrieve_knowledge(user_query, partno, pipeline,
                                     section, product_type, classifier_output)
    print("Answer from database:", resp)
