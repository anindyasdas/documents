"""
/*-------------------------------------------------
* Copyright(c) 2020-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""

import json
import re
import requests
import importlib

from .query import query_utils as query_utils
from ..constants import params as cs
from .graph.neo4j_db import Neo4jDB
from .query.query_constants import QueryConstants
from .query.query_constants import SpecQuery, TrobQuery, OperationQuery, SeeManualContents
from .query.query_utils import QueryEngine

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class DBInterface(object):
    """
    defines the method to form cypher query and insert to graph datavase
    """

    def __init__(self):
        self.db_engine = Neo4jInterface()

    def get_section_contents_from_kg(self, section, part_no,model_no=None):
        data, response_code = self.db_engine.get_section_contents_from_kg(section, part_no, model_no)
        return data, response_code

    def get_ts_section_causes_from_kg(self, product_entity_type, part_no, model_no=None):
        """
            call the neo4j instance to run query and get all the causes
            of given part no for TS section
        """
        data, response_code = self.db_engine.get_ts_section_causes_from_kg(product_entity_type, part_no, model_no)
        return data, response_code

    def create_knowledge(self, triplets): # pragma: no cover
        """
            Creates knowledge on graph database by calling Neo4jInterface
            Args:
                triplets - list of dictionary objects
            Returns:
                response - json string
        """
        response = self.db_engine.create_knowledge(triplets)
        return response

    def retrieve_product_type(self, part_no, model_no=None):
        """
            retrieve product type for the given modelno
            Args:
                modelno : str
            Returns:
                product_type : str
        """
        product_type, resp_code = self.db_engine.get_product_type(part_no, model_no)
        logger.debug("Product type is=%s", product_type)
        return product_type, resp_code

    def retrieve_part_nos(self, product_type):
        """
            retrieve part nos for product type
            Args:
                product_type : str
            Returns:
                part_nos : list
        """
        part_nos, resp_code = self.db_engine.get_part_nos(product_type)
        logger.debug("Product type is=%s" % str(part_nos))
        return part_nos, resp_code

    def retrieve_partnumber(self, model_number):
        """
            retrieve model nos for product type
            Args:
                product_type : str
            Returns:
                models : list
        """
        partnumber, resp_code = self.db_engine.get_partnumber(model_number)
        logger.debug("partnumber is=%s" % str(partnumber))
        return partnumber, resp_code

    def get_problem_key_from_fulltext(self, partno, question, verb_phrases, noun_phrases,modelno=None): # pragma: no cover
        """
            search full text query with the informations of verb phrases
            and noun_phrases
            Args:
                partno : str
                question : str
                verb_phrases : list
                noun_phrases : list
            Returns:
                problem : str
                problem_node_type : str
                status code : int
        """
        return self.db_engine.get_problem_key_from_fulltext(partno, question, verb_phrases, noun_phrases)

    def retrieve_knowledge(self, relation, topic, partno=None,
                           queryintent=cs.CAUSES_SOL_KEY,
                           knowledge_dict=None, entitytype=cs.MODEL,modelno=None):# TODO entity type has to be modified
        """
            retrieves knowledge from graph database by calling Neo4jInterface
            Args:
	            relation - defined relation of template question
                partno - reference entity of which knowledge is to be retrieved
                topic - manual section
                queryintent - query intent type cause/solution/causes+solution
                knowledge_dict - extracted knowledge using srl,const parser
                entitytype - type of entity
            Returns:
                answer : str
        """
        answer, resp_code = self.db_engine.retrieve_knowledge(relation, partno, topic,
                                                              entitytype, queryintent, knowledge_dict)
        logger.debug("answer=%s, resp_code=%s", answer, resp_code)
        logger.debug("DBinterface enitytype=%s intent=%s entity=%s", entitytype,
                     relation, partno)
        return answer, resp_code

    def retrieve_para_from_graph(self, relation, partno, section, entitytype=cs.MODEL): # pragma: no cover
        """
           retrieves knowledge using entity,entity type,relation details
           from database and forms paragraph

           Args:
               relation - dict object of relation
               partno - partno of which manual, knowledge is to be retrieved
               section - manual section
               entitytype - type of entity
           Returns:
               para : str
        """
        logger.debug("relation=%s, entity=%s, section=%s, entitytype=%s", relation, partno, section, entitytype)
        para, resp_code = self.db_engine.retrieve_para_from_graph(relation, partno, section, entitytype)
        logger.debug("para=%s, resp_code=%s", para, resp_code)
        return para, resp_code


class Neo4jInterface(object):
    """
    defines the method to form cypher query and call interface to insert
    data to graph database
    """

    def __init__(self):
        # change search_method to QueryConstants.UNWIND_SEARCH if sub str search is to be performed
        self.search_method = QueryConstants.LIST_SEARCH
        self.graph = Neo4jDB()
        self.query_engine = QueryEngine.get_instance(self.search_method)
        # drop the index if exists and create full text index
        # This is not required and will be enabled in future if needed
        ## self.__prepare_fulltext_index()

    def get_section_contents_from_kg(self, section, part_no, model_no):

        # Form the query
        query_for_troubleshooting = None
        # Call the Neo4j Instance
        if section == cs.IOConstants.HY_TROUBLESHOOTING:
            query_for_troubleshooting = SeeManualContents.FOR_TROUBLESHOOTING
        elif section == cs.IOConstants.HY_OPERATION:
            query_for_troubleshooting = SeeManualContents.FOR_OPERATION
        query_for_troubleshooting = query_for_troubleshooting.format(part_number=part_no)
        logger.debug("framed query : {}".format(query_for_troubleshooting))
        data, response_code = self.graph.run_query(query_for_troubleshooting)

        return data, response_code

    def get_ts_section_causes_from_kg(self, product_entity_type, part_no, model_no):
        """
        call the neo4j instance to run query and get all the causes
        of given model no for TS section
        """
        logger.debug("prod entity type-%s part_no=%s", product_entity_type, part_no)
        # Convert the entity product type to list
        entity_type_list = self.convert_product_type_to_list_of_strings(product_entity_type)
        # Form the query
        match_query = " ".join([TrobQuery.MATCH_PART_NUMBER, TrobQuery.RETRIEVE_ALL_TS_CAUSES])
        query_for_troubleshooting = match_query.format(part_number=part_no, entity_type=entity_type_list)
        logger.debug("framed query : {}".format(query_for_troubleshooting))
        # Call the Neo4j Instance
        data, response_code = self.graph.run_query(query_for_troubleshooting)
        logger.debug("data=%s response_code=%d", data, response_code)
        return data, response_code

    def __prepare_fulltext_index(self): # pragma: no cover
        """
            This function is used to create , drop full text index
            Args: None
            Returns : None
        """
        try:
            # drop full text index if already created
            drop_index = OperationQuery.DROP_FULLTEXT_INDEX
            logger.debug("drop index query=(%s)", drop_index)
            results, resp_code = self.graph.run_query(drop_index)
            logger.debug("drop_contr_query results=%s", str(results))
        except Exception as e:
            logger.exception("Exception in dropping=%s", str(e))

        try:
            # create full text search index
            create_index = OperationQuery.CREATE_FULLTEXT_INDEX
            logger.debug("create_index index query=(%s)", create_index)
            results, resp_code = self.graph.run_query(create_index)
            logger.debug("fulltext results=%s", str(results))
            logger.debug("full text constraint is added")
        except Exception as e:
            logger.exception("Exception in creating=%s", str(e))

    def __form_range_insert_query(self, node_name, node_type, prop_dict): # pragma: no cover
        """
            form range node query

            Args:
                 node_name - Name of the node
                 node_type - type of the node
                 prop_dict - dict of properties
            Returns:
                 query:str
        """
        if (prop_dict == None or str(not prop_dict) == "True"):
            query = """MERGE (b:%s{Name:"%s"})""" % (node_type, node_name)
        else:
            if "\"" in node_name:
                if cs.ENTITY in str(prop_dict):
                    mod_prop = ",".join("%s:%s" % (key, value) for key, value in
                                        prop_dict.items())
                else:
                    mod_prop = ",".join("%s:\'%s\'" % (key, value) for key, value
                                        in prop_dict.items())
                query = "MERGE (b:%s{Name:\'%s\',%s})" % (node_type,
                                                          node_name, mod_prop)
            else:
                if cs.ENTITY in str(prop_dict):
                    mod_prop = ",".join("%s:%s" % (key, value) for key, value in
                                        prop_dict.items())
                else:
                    mod_prop = ",".join("%s:\"%s\"" % (key, value) for key, value
                                        in prop_dict.items())
                query = "MERGE (b:%s{Name:\"%s\",%s})" % (node_type,
                                                          node_name, mod_prop)
            logger.debug("range prop=(%s)" % str(prop_dict))
            logger.debug("mod_prop=(%s)" % str(mod_prop))
        return query

    def __form_domain_insert_query(self, node_name, node_type, prop_dict): # pragma: no cover
        """
            form domain node query

            Args:
                 node_name - Name of the node
                 node_type - type of the node
                 prop_dict - dict of properties
            Returns:
                 query:str
        """
        if (prop_dict == None or str(not prop_dict) == "True"):
            query = """MERGE (a:%s{Name:"%s"})""" % (node_type, node_name)
        else:
            if "\"" in node_name:
                if cs.ENTITY in str(prop_dict):
                    mod_prop = ",".join("%s:%s" % (key, value) for key, value in
                                        prop_dict.items())
                else:
                    mod_prop = ",".join("%s:\'%s\'" % (key, value) for key, value
                                        in prop_dict.items())
                query = "MERGE (a:%s{Name:\'%s\',%s})" % (node_type,
                                                          node_name, mod_prop)
            else:
                if cs.ENTITY in str(prop_dict):
                    mod_prop = ",".join("%s:%s" % (key, value) for key, value in
                                        prop_dict.items())
                else:
                    mod_prop = ",".join("%s:\"%s\"" % (key, value) for key, value
                                        in prop_dict.items())
                query = "MERGE (a:%s{Name:\"%s\",%s})" % (node_type,
                                                          node_name, mod_prop)
        return query

    def __form_insert_cypher_query(self, triplet): # pragma: no cover
        """
           extracts informations from triplet object and forms cypher query
           Args:
                triplet - Triplet object has node1,relation,node2 informations
           Returns:
                 query:str
        """
        query = None
        node_type, node_name, = None, None
        rel_type = None
        prop_dict = None
        node1_query, rel_query, node2_query = "", "", ""

        if triplet == None:
            return query

        # extract domain values
        logger.info("the triplet to form cypher data %s " % str(triplet))
        node_type = triplet[cs.START_NODE][cs.TYPE]
        node_name = triplet[cs.START_NODE][cs.NAME]
        prop_dict = triplet[cs.START_NODE][cs.PROP]

        node1_query = self.__form_domain_insert_query(node_name, node_type, prop_dict)

        # extract relationship information
        rel_type, prop_dict = None, None
        rel_type = triplet[cs.RELATION][cs.TYPE]
        prop_dict = triplet[cs.RELATION][cs.PROP]

        if prop_dict is None:
            rel_query = "MERGE(a)-[r:%s]->(b)" % rel_type
        else:
            mod_prop = ""
            # use to handle the property based on datatype
            for key, value in prop_dict.items():
                if type(value) is list:
                    mod_prop += key + ":" + str(value) + ","
                else:
                    mod_prop += key + ":\"" + value + "\"" + ","
            logger.debug("mod_prop : %s", mod_prop)
            if (len(mod_prop) > 0) and (mod_prop[len(mod_prop) - 1] == ","):
                mod_prop = mod_prop[:-1]
            # for future ref mod_prop = ",".join('%s:%s' % (key, value) for key, value
            #                     in prop_dict.items())
            rel_query = "MERGE(a)-[r:%s{%s}]->(b)" % (
                rel_type, mod_prop)

        # extract range values
        node_type, node_type, prop_dict = None, None, None
        node_type = triplet[cs.END_NODE][cs.TYPE]
        node_name = triplet[cs.END_NODE][cs.NAME]
        prop_dict = triplet[cs.END_NODE][cs.PROP]

        node2_query = self.__form_range_insert_query(node_name, node_type, prop_dict)

        query = node1_query + node2_query + rel_query
        logger.debug("Formed Cypher query" + str(query))
        return query

    def create_knowledge(self, triplets): # pragma: no cover
        """
           extracts node,relationship informations from triplets and insert
           to database

           Args:
                triplets : Class Triplet:List
           Returns:
                response : json string
        """
        response = {}

        try:
            if (triplets == None) or (len(triplets) == 0):
                response[cs.resp_code] = cs.DATA_NOT_FOUND
                response[cs.error_msg] = "Data not available"
                return json.dumps(response)

            # For sending the queries as a list
            query_list = []
            for eachtriplet in triplets:
                query = self.__form_insert_cypher_query(eachtriplet)
                if query is not None:
                    # Store it as a list and send it as a list
                    query_list.append(query)

            response = self.graph.execute(query_list)
            return response
        except Exception as e:
            response = dict()
            logger.exception("create_knowledge from_triplets=%s", e)
            response[cs.resp_code] = cs.INTERNAL_ERROR
            response[cs.error_msg] = str(e)
            return json.dumps(response)

    def __form_query_for_desc(self, entitytype, entity, intent, common_key, specific_problem, prod_type): # pragma: no cover
        """
            forms cypher query to retrieve knowledge from database

            Args:
                entitytype : type of entity
                entity : entity name of which knowledge is to be retrieved
                intent : dict object of relation
                common_key : common problem key of user query
                specific_problem : specific problem key of user query
                prod_type : product type (Eg: washer/dryer)
            Returns:
                query : str
        """
        common_prob_query = ""
        spec_prob_query = ""
        sub_query = ""

        # query to match model number & part number
        model_query = OperationQuery.MATCH_PART_NUMBER % (entitytype, entity)

        # if its description , storing way in KG differs for sub sections
        if intent == cs.HAS_CONTROL_PANEL_FEATURE:
            logger.debug("control panel feature")
            common_prob_query = OperationQuery.MATCH_CNTLPNL_FEATURE
            spec_prob_query = OperationQuery.MATCH_SPECIFIC_CNTLPANEL_FEATURE
        else:
            logger.debug("retrieve other sections")
            match_query = OperationQuery.MATCH_OPER_SECTION % (common_key, specific_problem, prod_type)
            retrieve_desc = OperationQuery.RETRIEVE_SECTION
            retrieve_proced = OperationQuery.RETRIEVE_PROCEDURE % prod_type
            # query to match section and procedure and return all the results
            sub_query = match_query + retrieve_desc + " UNION " + model_query + match_query + retrieve_proced

        # if query is about specific prob statement, replace with specific query constants
        if intent == cs.HAS_CONTROL_PANEL_FEATURE:
            if common_key.lower() != specific_problem.lower():
                sub_query = spec_prob_query % (common_key, specific_problem)
                return_query = OperationQuery.RETRIEVE_CNTLPNL_FEATURE % (prod_type, prod_type)
                sub_query = sub_query + return_query
            else:
                sub_query = common_prob_query % common_key

        query = model_query + sub_query
        logger.debug("__form_query_for_desc query=%s", query)
        return query

    def __verify_inputs_update_relation(self, relation, query_intent):
        """
           check input values, removes lead.trail spaces and
           update query_intent as per defined ontology

           Args:
               relation : dict object of relation
               query_intent : intent of the user query
           Returns:
               rel_prop_key : info type of user query direct/extra
               query_intent : intent of user query
               intent : relation name
               problem : section of problem
               sub_problem : sub section of problem
        """
        # remove leading/trailing spaces and trailing dot
        intent = relation[cs.INTENT]
        rel_prop_key = relation[cs.PROP_KEY].strip().rstrip('.')
        rel_prop_value = relation[cs.PROP_VALUE].strip().rstrip('.')
        sub_problem = relation[cs.InfoKnowledge.PROB_VAL_SPECI].strip().rstrip('.')
        problem = rel_prop_value

        # if query intent is usage,as per category information to be retrieved may differ
        if query_intent == cs.ProblemTypes.USAGE and intent == cs.HAS_FEATURE \
                or intent == cs.HAS_CONTROL_PANEL_FEATURE or \
                intent == cs.HAS_CHECKLIST:
            logger.debug("this intent %s not have usage, converting to desc", intent)
            query_intent = cs.ProblemTypes.DESCRIPTION

        return rel_prop_key, query_intent, intent, problem, sub_problem

    def __form_query_for_extra_info(self, product_info, query_method=None):
        """
            forms cypher query to retrieve knowledge from database

            Args:
                 product_info: A tuple which will have the following info
                                entity : entity name (Model no) of which knowledge is to be retrieved
                                intent : dict object of relation
                                common_key : common problem key of user query (L1 Key)
                                specific_problem : specific problem key of user query (L2 .. Ln)
                                query_intent : intent of the user query
                                prod_type : product type (washer/dryer)
                query_method: If it is 'full_text_search' query will be formed based on full text
                        (will directly map with the node retrieved from full text search)
            Returns:
                query : str
        """
        entity, intent, common_key, specific_problem, query_intent, prod_type = product_info
        logger.debug("prod_type=%s model=%s query_intent=%s intent=%s common_key=%s specific_problem=%s" % (prod_type,
                                                                                                            entity,
                                                                                                            query_intent,
                                                                                                            intent,
                                                                                                            common_key,
                                                                                                            specific_problem))
        query = ""
        # 1) Check if L1 or Ln and get the main_query
        # To assign later
        operation_or_subsection = ""
        it_is_an_operation_sub_section = False
        if query_method is not None and query_method == cs.RetrievalConstant.USE_FULL_TEXT_FLAG:
            query = " ".join([OperationQuery.MATCH_PART_NUMBER, OperationQuery.FULL_TEXT_SEARCH_SECTION])
            operation_or_subsection = OperationQuery.FULL_TEXT_SEARCH_SECTION
        elif common_key == specific_problem:
            query = " ".join([OperationQuery.MATCH_PART_NUMBER, OperationQuery.OPERATION_SECTION])
            operation_or_subsection = OperationQuery.OPERATION_SECTION
        elif common_key != specific_problem:
            query = " ".join([OperationQuery.MATCH_PART_NUMBER, OperationQuery.OPERATION_SUB_SECTION])
            operation_or_subsection = OperationQuery.OPERATION_SUB_SECTION
            it_is_an_operation_sub_section = True

        # 1.1) Add the Image and Return Query to the query
        if it_is_an_operation_sub_section:
            query = " ".join([query, OperationQuery.SUB_SECTION_IMAGE_QUERY, OperationQuery.RETURN_QUERY])
        else:
            query = " ".join([query, OperationQuery.IMAGE_QUERY, OperationQuery.RETURN_QUERY])

        # 2) Check whether to retrieve Procedures and add Procedure Optional Query
        # update intent(db relation name) based on query_intent
        extra_info = "|".join([cs.HAS_NOTE, cs.HAS_CAUTION, cs.HAS_WARNING])
        if query_intent == cs.NOTE:
            extra_info = cs.HAS_NOTE
        elif query_intent == cs.CAUTION:
            extra_info = cs.HAS_CAUTION
        elif query_intent == cs.ProblemTypes.EXTRA_WARNING:
            extra_info = cs.HAS_WARNING
        # Convert the entity product type to list
        entity_type_list = self.convert_product_type_to_list_of_strings(prod_type)

        extra_info_sub_query = OperationQuery.EXTRA_INFO_QUERY.format(
            part_number_query=OperationQuery.MATCH_PART_NUMBER,
            operation_or_subsection=operation_or_subsection,
            extra_info=extra_info, entity_type=entity_type_list)
        query = " ".join([query, OperationQuery.UNION_STRING, extra_info_sub_query])

        # Format the final query with the string variables
        # Variables to be filled: model_number, operation_section, operation_sub_section, entity_type
        query = query.format(model_number=entity, operation_section=common_key, operation_sub_section=specific_problem,
                             entity_type=entity_type_list)

        logger.debug("query inside __form_query_for_extra_info %s ", query)
        return query

    def __form_query_for_direct_info(self, product_info, query_method=None):
        """
            forms cypher query to retrieve knowledge from database

            Args:
                product_info: A tuple which will have the following info
                                entity : entity name (Model no) of which knowledge is to be retrieved
                                intent : dict object of relation
                                common_key : common problem key of user query (L1 Key)
                                specific_problem : specific problem key of user query (L2 .. Ln)
                                query_intent : intent of the user query
                                prod_type : product type (washer/dryer)
                query_method: If it is 'full_text_search' query will be formed based on full text
                        (will directly map with the node retrieved from full text search)
            Returns:
                query : str
        """
        # product info tuple
        # entity : entity name of which knowledge is to be retrieved
        # intent : db relation name
        # common_key : common problem key of user query
        # specific_problem : specific problem key of user query
        # query_intent : intent of the user query
        # prod_type : product type (Eg: washer/dryer)
        entity, intent, common_key, specific_problem, query_intent, prod_type = product_info
        logger.info("prod_type=%s model=%s query_intent=%s intent=%s common_key=%s specific_problem=%s" % (prod_type,
                                                                                                            entity,
                                                                                                            query_intent,
                                                                                                            intent,
                                                                                                            common_key,
                                                                                                            specific_problem))
        query = ""
        # Query Formation
        # 1) Check if L1 or Ln and get the main_query or Full text Search Query type
        # To assign later
        operation_or_subsection = ""
        it_is_an_operation_sub_section = False
        if query_method is not None and query_method == cs.RetrievalConstant.USE_FULL_TEXT_FLAG:
            query = " ".join([OperationQuery.MATCH_PART_NUMBER, OperationQuery.FULL_TEXT_SEARCH_SECTION])
            operation_or_subsection = OperationQuery.FULL_TEXT_SEARCH_SECTION
        elif common_key == specific_problem:
            query = " ".join([OperationQuery.MATCH_PART_NUMBER, OperationQuery.OPERATION_SECTION])
            operation_or_subsection = OperationQuery.OPERATION_SECTION
        elif common_key != specific_problem:
            query = " ".join([OperationQuery.MATCH_PART_NUMBER, OperationQuery.OPERATION_SUB_SECTION])
            operation_or_subsection = OperationQuery.OPERATION_SUB_SECTION
            it_is_an_operation_sub_section = True

        # 1.1) Add the Image and Return Query to the query
        if it_is_an_operation_sub_section:
            query = " ".join([query, OperationQuery.SUB_SECTION_IMAGE_QUERY, OperationQuery.RETURN_QUERY])
        else:
            query = " ".join([query, OperationQuery.IMAGE_QUERY, OperationQuery.RETURN_QUERY])

        # Convert the entity product type to list
        entity_type_list = self.convert_product_type_to_list_of_strings(prod_type)

        # 2) Sub Query to retrieve Procedures and add Procedure Optional Query
        procedure_sub_query = OperationQuery.PROCEDURE_QUERY.format(
            part_number_query=OperationQuery.MATCH_PART_NUMBER,
            operation_or_subsection=operation_or_subsection, entity_type=entity_type_list)
        query = " ".join([query, OperationQuery.UNION_STRING, procedure_sub_query])

        # 3) Sub Query to retrieve Features and add Feature Optional Query
        feature_sub_query = OperationQuery.FEATURE_QUERY.format(part_number_query=OperationQuery.MATCH_PART_NUMBER,
                                                                operation_or_subsection=operation_or_subsection,
                                                                entity_type=entity_type_list)
        query = " ".join([query, OperationQuery.UNION_STRING, feature_sub_query])

        # Add the Sub Section Query (TODO Check this once if required in English)
        sub_sections_query = OperationQuery.SUB_SECTION_QUERY.format(part_number_query=OperationQuery.MATCH_PART_NUMBER,
                                                                     operation_or_subsection=operation_or_subsection,
                                                                     entity_type=entity_type_list)
        query = " ".join([query, OperationQuery.UNION_STRING, sub_sections_query])

        # Format the final query with the string variables
        # Variables to be filled: model_number, operation_section, operation_sub_section, entity_type
        query = query.format(model_number=entity, operation_section=common_key, operation_sub_section=specific_problem,
                             entity_type=entity_type_list)

        logger.debug("__form_query_for_direct_info query=%s", query)
        return query

    def __get_fulltext_cond_query(self, verb_phrases, noun_phrases): # pragma: no cover
        """
            forms full text conditional query with the informations of verb phrases
            and noun_phrases
            Args:
                verb_phrases : list
                noun_phrases : list
            Returns:
                cond_query : str
        """
        entity = None
        verb = None
        cond_query = None

        logger.debug("__get_fulltext_cond_query np=%s vb=%s", str(noun_phrases), str(verb_phrases))
        if len(noun_phrases) > 0:
            # using map to convert each element to string
            # Filter
            temp = list(map(str, filter(len, noun_phrases)))
            # join() used to join with delimiter
            entity = QueryConstants.LOGICAL_OR.join(temp)
            logger.debug(entity)

        if len(verb_phrases) > 0:
            # using map to convert each element to string
            temp = list(map(str, filter(len, verb_phrases)))
            # join() used to join with delimiter
            verb = QueryConstants.LOGICAL_OR.join(temp)
            logger.debug(verb)

        # if both has values, doing AND in cond query
        if entity is not None and verb is not None:
            cond_query = verb + QueryConstants.LOGICAL_AND + entity
        else:
            if entity is not None:
                cond_query = entity
            elif verb is not None:
                cond_query = verb
            else:
                logger.warning("Full text query both(noun phrases,verb phrases) are none")

        logger.debug("cond_query=%s", cond_query)
        return cond_query

    def get_problem_key_from_fulltext(self, modelno, question, verb_phrases, noun_phrases): # pragma: no cover
        """
            search full text query with the informations of verb phrases
            and noun_phrases
            Args:
                modelno : str
                question : str
                verb_phrases : list
                noun_phrases : list
            Returns:
                problem : str
        """
        problem = None
        nodetype = cs.HAS_OPERATION_SECTION
        results = None
        logger.debug("get_problem_key_from_fulltext modelno=%s question:%s np=%s vb=%s", modelno, question,
                     str(noun_phrases), str(verb_phrases))

        # get conditional query for full text search using verb and noun phrases
        cond_query = self.__get_fulltext_cond_query(verb_phrases, noun_phrases)

        resp_code = cs.ResponseCode.KER_INTERNAL_SUCCESS
        length = 0
        if cond_query is not None:
            # execute full text search query with combination of verb & noun
            query = OperationQuery.SEARCH_FULLTEXT_INDEX.format(model_number=modelno, search_query=cond_query)
            logger.debug("search index query=(%s)", query)
            results, resp_code = self.graph.run_query(query)
            logger.debug("search index query =(%s)", query)
            logger.debug("search index query results=(%s)", str(results))
            length = len(results[0]['op_sections'])
            logger.info("Database problem key results len=(%d)", length)
        # if results None,fallback to only verb phrases search
        if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS and length <= 0:
            logger.info("full text search fall back with input question")
            # removing special characters from question
            search_text = ''.join(e for e in question if e.isalnum() or e.isspace())
            query = OperationQuery.SEARCH_FULLTEXT_INDEX.format(model_number=modelno, search_query=search_text)
            logger.debug("search index query=(%s)", query)
            results, resp_code = self.graph.run_query(query)
            logger.debug("search index query results=(%s)", results)
            length = len(results[0]['op_sections'])
            logger.debug("Database results len=(%d)", length)

        if length > 0:
            problem = results[0]['op_sections'][0]
            node_labels = results[0]['op_sections_type']
            if (node_labels is not None) and (len(node_labels) > 0):
                nodetype = node_labels[0]
        logger.debug("full text search result problem=%s nodetype=%s", problem, nodetype)

        return problem, nodetype, resp_code

    def _form_query_for_unstructured_knowledge(self, relation, entity, entitytype, query_intent):
        """
           forms cypher query to retrieve knowledge from database

           Args:
               relation : dict object of relation
               entity : entity name of which knowledge is to be retrieved
               entitytype : type of entity
               query_intent : intent of the user query
           Returns:
               query : str
               querykey :str
        """
        querykey = None
        prod_type = relation[cs.PRODUCT_TYPE]
        # verify inputs and update intent
        info_type, query_intent, intent, common_key, specific_problem = self.__verify_inputs_update_relation(relation,
                                                                                                             query_intent)
        logger.debug("prod_type=%s info_type=%s query_intent=%s intent=%s common_key=%s specific_problem=%s" %
                     (prod_type, info_type, query_intent, intent, common_key, specific_problem))

        query = ""
        # get cypher query which is stored explicitly (ie) direct info
        query_method = relation.get(cs.RetrievalConstant.QUERY_METHOD, None)
        # Product info is a tuple to get all the product information
        product_info = (entity, intent, common_key, specific_problem, query_intent, prod_type)
        if info_type == cs.ProblemTypes.DIRECT_INFO:
            query = self.__form_query_for_direct_info(product_info, query_method=query_method)

        # get cypher query for notes/caution/warning
        elif info_type == cs.ProblemTypes.EXTRA_INFO:
            query = self.__form_query_for_extra_info(product_info, query_method=query_method)
        # TODO Check for an else (Default condition)
        logger.debug("--------formed query:%s", query)
        return query, querykey

    def __retrieve_query_for_spec(self, relation, entitytype, entity): # pragma: no cover
        """
           forms cypher query for specification section to retrieve knowledge
           from database

           Args:
               relation : dict object of relation
               entitytype : type of entity
               entity : entity name of which knowledge is to be retrieved
           Returns:
               query : str
               querykey :str
        """
        logger.debug("model=%s intent=%s " % (entity, relation))
        # copy dictionary and edit the copy
        prop_dict = relation.copy()
        logger.debug("before pop relation=%s" % str(relation))

        # remove key from dict
        prop_dict.pop(cs.InfoKnowledge.KEY)

        # remove intent key from relation dict
        intent = prop_dict.pop(cs.INTENT)

        logger.debug("after pop relation=%s" % str(relation))
        # Get the node result from the graph
        if intent == cs.HAS_DIMENSION or intent == cs.HAS_OVEN_DIMENSION:
            spec_to_retrieve_node = " ".join([SpecQuery.MATCH_MODEL_PART_NUMBERS, SpecQuery.RETRIEVE_NODE])
            query = spec_to_retrieve_node.format(model_number=entity, specification_type=intent)
        else:
            # forming property key value pair by neglecting range
            # the key should not be be Product_type
            mod_prop = ",".join("%s:'%s'" % (key, value) for key, value in
                                prop_dict.items() if len(value.strip()) > 0 and key != cs.RANGE
                                and key != cs.PRODUCT_TYPE_KEY)
            if len(mod_prop.strip()) > 0:
                # Get the node result from the graph
                spec_specific_query = " ".join([SpecQuery.MATCH_MODEL_PART_NUMBERS,
                                                SpecQuery.RETRIEVE_SPECIFIC_PARAM])
                query = spec_specific_query.format(model_number=entity, specification_type=intent,
                                                   specification_property=mod_prop)
            else:
                # Get the specific param from the graph
                # TODO Check if the else is required
                spec_to_retrieve_node = " ".join([SpecQuery.MATCH_MODEL_PART_NUMBERS, SpecQuery.RETRIEVE_NODE])
                query = spec_to_retrieve_node.format(model_number=entity, specification_type=intent)
        querykey = cs.VALUE
        return query, querykey

    def convert_product_type_to_list_of_strings(self, prod_type):
        """
        A utility function used to convert prod_type to list of strings
        used for querying
        """
        prod_type_as_list_of_strings = []
        if isinstance(prod_type, str):
            prod_type_as_list_of_strings.append(str(prod_type))
        elif isinstance(prod_type, list):
            prod_type_as_list_of_strings.extend([str(x) for x in prod_type])

        return prod_type_as_list_of_strings

    def __retrieve_query_for_trob(self, relation, entitytype, entity, queryintent):
        """
           forms cypher query for troubleshooting section to retrieve knowledge
           from database

           Args:
               relation : dict object of relation
               entitytype : type of entity
               entity : entity name of which knowledge is to be retrieved
               queryintent : query intent type cause/solution/causes+solution
           Returns:
               query : str
               querykey :str
        """
        logger.debug("relation dict=%s", relation)
        intent = relation[cs.INTENT]
        # remove leading/trailing spaces and trailing dot
        rel_prop_key = relation[cs.PROP_KEY].strip().rstrip('.')
        rel_prop_value = relation[cs.PROP_VALUE].strip().rstrip('.')
        common_key = rel_prop_value
        specific_problem = relation[cs.InfoKnowledge.PROB_VAL_SPECI].strip().rstrip('.')
        prod_type = relation[cs.PRODUCT_TYPE]

        match_query = ""
        querykey = ""

        # Convert the entity product type to list
        entity_type_list = self.convert_product_type_to_list_of_strings(prod_type)

        if relation[cs.INTENT] == cs.HAS_QUESTION:
            # FAQ retrieval
            faq_query = " ".join([TrobQuery.MATCH_PART_NUMBER, TrobQuery.MATCH_FAQ_NODE])
            match_query = faq_query.format(part_number=entity, faq_question=common_key,
                                           entity_type=entity_type_list)
            match_query = " ".join([match_query, TrobQuery.RETURN_SOLUTION])
        elif intent == cs.DIAGNOSE_WITH_BEEP:
            diagnose_with_beep_query = " ".join([TrobQuery.MATCH_PART_NUMBER, TrobQuery.RETRIEVE_DIAG_BEEP_PROB])
            match_query = diagnose_with_beep_query.format(part_number=entity, entity_type=entity_type_list)
        elif intent == cs.DIAGNOSE_WITH_LG_THINQ:
            diagnose_with_thinq_query = " ".join([TrobQuery.MATCH_PART_NUMBER, TrobQuery.RETRIEVE_DIAG_THINQ])
            match_query = diagnose_with_thinq_query.format(part_number=entity, entity_type=entity_type_list)
        else:
            # check if specific solution/all solutions for problem
            if common_key.lower() != specific_problem.lower():
                specific_cause_query = " ".join([TrobQuery.MATCH_PART_NUMBER, TrobQuery.MATCH_SPECIFIC_CAUSE])
                match_query = specific_cause_query.format(part_number=entity, problem_type=intent,
                                                          property_key=rel_prop_key,
                                                          property_value=common_key,
                                                          specific_cause=specific_problem, entity_type=entity_type_list)
                # intent, cs.HAS_SOLUTION, prod_type, prod_type,rel_prop_key, common_key, specific_problem)
            else:
                specific_problem_query = " ".join(
                    [TrobQuery.MATCH_PART_NUMBER, TrobQuery.MATCH_SPECIFIC_PROBLEM])
                match_query = specific_problem_query.format(part_number=entity, problem_type=intent,
                                                            property_key=rel_prop_key,
                                                            property_value=common_key, entity_type=entity_type_list)
                # intent, cs.HAS_SOLUTION, prod_type, prod_type, rel_prop_key, common_key)
            return_query = TrobQuery.RETURN_CAUSE_SOLUTION
            match_query = " ".join([match_query, return_query])
        querykey = cs.CAUSES_SOL_KEY

        query = match_query
        return query, querykey

    def __form_retrieve_cypher_query(self, relation, entity, topic,
                                     entitytype, queryintent, knowledge_dict=None):
        """
           forms cypher query to retrieve knowledge from database

           Args:
               relation : dict object of relation
               entity : entity name of which knowledge is to be retrieved
               topic : manual section
               entitytype : type of entity
               queryintent : query intent type cause/solution/causes+solution
               knowledge_dict : extracted knowledge using srl,const parser
           Returns:
               query : str
               querykey :str
        """
        query = None
        querykey = None

        # form cypher query based on srl,cons parser
        if topic == cs.TROB_SECTION and knowledge_dict != None:
            query_dict, querykey = self.__form_cypher_query_from_info(relation, entity,
                                                                      topic, entitytype, queryintent, knowledge_dict)
            return query_dict, querykey
        elif topic == cs.TROB_SECTION:
            query, querykey = self.__retrieve_query_for_trob(relation, entitytype, entity, queryintent)
        elif topic == cs.SPEC_SECTION:
            # TODO Remove entitytype
            query, querykey = self.__retrieve_query_for_spec(relation, entitytype, entity)
        elif topic == cs.Section.OPERATION:
            # get cypher query using extracted knowledge for unstructured section
            query, querykey = self._form_query_for_unstructured_knowledge(relation, entity, entitytype, queryintent)

        try:
            param = {'demoData': query}
            res = requests.get('http://neo4jvisdev1:8080/demoData', params=param)
            logger.debug("Send query to Visualization Web : %s", str(res.status_code) + "|" + res.text)

        except Exception as ex:
            logger.exception("error in vis comm : %s", ex)

        logger.debug("retrieve cypher query=%s", query)
        return query, querykey

    def __remove_toomany_condns(self, query): # pragma: no cover
        """
           forms cypher query to retrieve knowledge from database
           Args:
               query : str
           Returns:
               query : str
        """

        if 'where  OR' in query:
            query = query.replace("where  OR", "where")

        if 'where  AND' in query:
            query = query.replace("where  AND", "where")

        logger.debug("query_list:(%s)" % (str(query)))
        return query

    def __form_prioritylevel_query(self, match_query, return_query,
                                   knowledge_dict): # pragma: no cover
        """
           forms priority levels cypher query to retrieve knowledge from
           database

           Args:
               match_query : partial match cypher query
               return_query : partial return cypher query
               knowledge_dict : extracted knowledge using srl,const parser
           Returns:
               query_list : list
        """
        query_list = {}

        logger.debug("Enter match_query=(%s) return_query=(%s)" % (match_query,
                                                                   return_query))
        # get priority based queries
        priority_queries = self.query_engine.get_priority_based_cond_query(
            knowledge_dict)
        for key, cond_query in priority_queries.items():
            query = match_query + cond_query + return_query
            query = self.__remove_toomany_condns(query)
            query_list[key] = query
        logger.debug("Exit query_list=(%s)" % (str(query_list)))
        return query_list

    def __form_cypher_query_from_info(self, relation, entity, topic,
                                      entitytype, queryintent, knowledge_dict=None): # pragma: no cover
        """
           forms cypher query to retrieve knowledge from database

           Args:
               relation : dict object of relation
               entity : entity name of which knowledge is to be retrieved
               topic : manual section
               entitytype : type of entity
               queryintent : query intent type cause/solution/causes+solution
               knowledge_dict : extracted knowledge using srl,const parser
           Returns:
               query_list : list
               querykey :str
        """
        match_query = None
        return_query = None
        querykey = None
        query_list = {}

        logger.info("*** __form_cypher_query_from_info  called(%s)" %
                    str(knowledge_dict))
        if topic == cs.TROB_SECTION:
            intent = relation[cs.INTENT]

            match_query = TrobQuery.MATCH_ALL_CAUSE % (entitytype, entity, intent, cs.HAS_SOLUTION)
            if queryintent == cs.REASON_KEY:
                return_query = TrobQuery.RETURN_CAUSE
                querykey = cs.REASON_KEY
            elif (queryintent == cs.SOLUTION_KEY) or (queryintent == cs.CAUSES_SOL_KEY):
                return_query = TrobQuery.RETURN_CAUSE_SOLUTION
                querykey = cs.CAUSES_SOL_KEY

            # function call to get priority levels queries list
            query_list = self.__form_prioritylevel_query(match_query,
                                                         return_query, knowledge_dict)

        logger.debug("retrieve cypher query=%s", str(query_list))
        return query_list, querykey

    def __get_specific_dimension(self, rel_schema, node_value): # pragma: no cover
        """
            parses py2neo node object cypher query results and get specific
            answer
            Args:
                rel_schema : dict
                        cypher query main key for which fetching results
                node_value : dict
                        retrieved node from KG
            Returns:
               answer : str
        """
        # if query specific about door open,lid open status
        if rel_schema[cs.InfoKnowledge.OPEN_STATUS] == cs.InfoKnowledge.WITH_OPEN:
            spec_prop = rel_schema[cs.InfoKnowledge.SIDE] + "_" + rel_schema[cs.InfoKnowledge.SIDE_STATUS]
            answer = node_value[spec_prop]
            subanswer = node_value[cs.UNIT]
            answer = answer + " " + subanswer

        # if query asking depth without door open,we consider only side ie: depth OR
        # checking for width,height,depth sides
        elif rel_schema[cs.InfoKnowledge.OPEN_STATUS] == cs.InfoKnowledge.WITHOUT_OPEN or \
                len(rel_schema[cs.InfoKnowledge.SIDE].strip()) > 0:
            spec_prop = rel_schema[cs.InfoKnowledge.SIDE]
            answer = node_value[spec_prop]
            subanswer = node_value[cs.UNIT]
            answer = answer + " " + subanswer

        # whole dimension value considered as output
        else:
            answer = node_value[cs.NAME]
        return answer

    def __convert_node_to_dict(self, cypher_record):
        """
            convert neo4j cypher record to python dict

            Args:
                cypher_record : py2neo object
                              cypher query results
            Returns:
                converted_dict : dict
        """
        json_data = re.search(r"{.*}", cypher_record).group(0)
        json_data = re.sub("(\w+):", r'"\1":', json_data)
        json_data = json_data.replace("'", "\"")
        converted_dict = json.loads(json_data)
        return converted_dict

    def __get_specific_value(self, result, rel_schema): # pragma: no cover
        """
           parses py2neo node object cypher query results and get specific
           answer

           Args:
               result : py2neo object
                         cypher query results
               rel_schema : dict
                        cypher query main key for which fetching results
           Returns:
               resp_dict : dictionary
                        cypher query result info in dict
        """
        relationship = None
        node_value = ""
        # copy dictionary and edit the copy
        resp_dict = rel_schema.copy()

        for key, keyvalue in result.items():
            if key == cs.VALUE:
                node_value = str(keyvalue)
            elif key == cs.RELATION:
                relationship = str(keyvalue)

        logger.debug("rel_schema key=(%s)" % str(rel_schema))

        # convert relationship results to dict
        if relationship is not None:
            final_dict = self.__convert_node_to_dict(relationship)
            logger.info("Converted dict from relationship results=(%s)" % str(final_dict))
            # update rel schema dict by query relationship dict
            resp_dict.update(final_dict)

        # remove Intent key from dict
        resp_dict.pop(cs.INTENT)
        logger.debug("updated dict from relationship results=(%s)" % str(resp_dict))

        # convert node val results to dict
        final_dict = self.__convert_node_to_dict(node_value)
        logger.debug("Converted dict from node results=(%s)" % str(final_dict))
        node_value = final_dict
        logger.debug("@Converted dict from node results=(%s)" % str(node_value))

        # if its dimension related query
        if rel_schema[cs.INTENT] == cs.HAS_DIMENSION or rel_schema[cs.INTENT] == cs.HAS_OVEN_DIMENSION:
            answer = self.__get_specific_dimension(rel_schema, node_value)
        else:
            # checking for min/max specific type of query
            if len(rel_schema[cs.RANGE].strip()) > 0:
                answer = node_value[rel_schema[cs.RANGE]]
                subanswer = node_value[cs.UNIT]
                answer = answer + " " + subanswer
            # if spec key is not looking for specific info, return name info of node
            else:
                answer = node_value[cs.NAME]
        logger.debug("###__get_specific_value answer=%s" % (answer))
        resp_dict[cs.VALUE] = answer
        return resp_dict

    def __parse_unstructured_content_results(self, results, topic):
        """
           parses py2neo object cypher query results and returns the answer

           Args:
               results : py2neo object
                         cypher query results
           Returns:
               desc: list
               feature : list
               image_path : list
               image_type : list
               image_size : list
        """
        key1, key2 = "", ""
        mimetype = 'image/'
        feature = []
        desc = []
        image_path = []
        image_type = []
        image_size = []

        # depends on section, keys assigning for parsing results
        if topic == cs.TROB_SECTION:
            key1 = cs.REASON_KEY
            key2 = cs.SOLUTION_KEY
        elif topic == cs.Section.OPERATION:
            key1 = cs.FEATURE
            key2 = cs.DESC_KEY

        for result in results:
            # get the feature,desc,media keys from results and
            # add to the list response
            feature_value = result.get(key1, "")
            desc_value = result.get(key2, "")
            logger.debug("feature_value=%s", feature_value)
            logger.debug("desc_value=%s", desc_value)
            # if desc is list and convert list to str
            if isinstance(desc_value, list):
                desc_value = "".join(desc_value)
            # add line spacing after each sentence
            if feature_value is not None:
                feature_value = feature_value.replace(".", ". ")
                feature.append(feature_value)
            if desc_value is not None:
                desc_value = desc_value.replace(".", ". ")
                desc.append(desc_value)
            image_path.append(result.get(cs.MEDIA_URL, None))
            img_type = result.get(cs.MEDIA_TYPE, None)
            if img_type is not None:
                img_type = mimetype + img_type
            image_type.append(img_type)
            img_size = result.get(cs.MEDIA_SIZE, None)
            if img_size is not None:
                img_size = int(img_size)
            image_size.append(img_size)
        return desc, feature, image_path, image_type, image_size

    def __parse_structured_content_results(self, results, rel_schema): # pragma: no cover
        """
           parses py2neo object cypher query results and returns the answer

           Args:
               results : py2neo object
                         cypher query results
               rel_schema : dict
                         all extracted info of query
           Returns:
               answer : list
        """
        cause = []
        soln = []
        value = []
        for result in results:
            for key, keyvalue in result.items():
                # check the key and fill the respective dict
                if key == cs.REASON_KEY:
                    cause.append(keyvalue)
                elif key == cs.SOLUTION_KEY:
                    soln.append(keyvalue)
                elif key == cs.VALUE:
                    # for specification retrieval , relationship informations to be retrieved
                    # when it has hierarchical level info,so taking both relation & node values
                    answer = self.__get_specific_value(result,
                                                       rel_schema)
                    value.append(answer)
        return cause, soln, value

    def __parse_graph_results(self, topic, results, rel_schema, result_sts):
        """
           parses py2neo object cypher query results and returns the answer

           Args:
               topic : str
                       Spec/trob/Operation section
               results : py2neo object
                         cypher query results
               rel_schema : dict
                         all extracted info of query
               result_sts: int
                        whether result is fetched successfully or not
           Returns:
               answer : list
        """
        query_results = dict()
        cause = []
        soln = []
        value = []
        feature = []
        desc = []
        image_path = []
        image_type = []
        image_size = []

        if (result_sts == cs.ResponseCode.KER_INTERNAL_FAILED) or (result_sts == cs.ResponseCode.CONNECTION_ERROR) \
                or (result_sts == cs.ResponseCode.CLIENT_ERROR):
            query_results[cs.resp_code] = results[cs.resp_code]
            query_results[cs.error_msg] = results[cs.error_msg]

            return query_results

        logger.debug("type=(%s)Answers from database=%s" % (type(results), str(results)))

        query_results[cs.VALUE] = value
        query_results[cs.REASON_KEY] = cause
        query_results[cs.SOLUTION_KEY] = soln
        query_results[cs.DESC_KEY] = desc
        query_results[cs.FEATURE] = feature

        # parse structured section results
        if topic == cs.SPEC_SECTION: # pragma: no cover
            cause, soln, value = self.__parse_structured_content_results \
                (results, rel_schema)
            query_results[cs.VALUE] = value
        elif topic == cs.TROB_SECTION:
            cause, soln, image_path, image_type, image_size = \
                self.__parse_unstructured_content_results(results, topic)
            query_results[cs.REASON_KEY] = soln
            query_results[cs.SOLUTION_KEY] = cause
        # parse unstructured section results
        elif topic == cs.Section.OPERATION:
            desc, feature, image_path, image_type, image_size = \
                self.__parse_unstructured_content_results(results, topic)
            query_results[cs.DESC_KEY] = desc
            query_results[cs.FEATURE] = feature

        query_results[cs.MEDIA_URL] = image_path
        query_results[cs.MEDIA_TYPE] = image_type
        query_results[cs.MEDIA_SIZE] = image_size

        logger.debug("query_results=(%s)" % (str(query_results)))
        return query_results

    def __retrieve_by_knowledge_dict(self, relation, entity, topic, entitytype, queryintent, knowledge_dict): # pragma: no cover
        """
            form cypher query using knowledge_dict(srl,cons parser) and
            retrieves knowledge from database

            Args:
                relation : dict object of relation
                entity : entity name of which knowledge is to be retrieved
                topic : manual section
                entitytype : type of entity
                queryintent : query intent type cause/solution/causes+solution
                knowledge_dict : extracted knowledge using srl,const parser
            Returns:
                query_results : dict
        """
        query_results = None

        # retrieve with prob_key,value of info extraction
        query, querykey = self.__form_retrieve_cypher_query(relation, entity,
                                                            topic, entitytype, queryintent)
        # execute query
        results, resp_code = self.graph.run_query(query)
        length = len(results)
        logger.debug("**Database results len=(%d)", length)

        # if results None,fallback to cons_parser,srl based search
        if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS:
            if length > 0:
                logger.debug("**Database results=(%s)", str(results))
                query_results = self.__parse_graph_results(topic, results, relation, resp_code)
            else:
                # retrieve with knowledge info
                query, querykey = self.__form_retrieve_cypher_query(relation, entity,
                                                                    topic, entitytype, queryintent, knowledge_dict)
                # execute parallel execution of queries
                if type(query) == dict:
                    logger.debug("Calling thread based parallel execution")
                    results = query_utils.query_parallel_execution(self.graph,
                                                                   query)
                # if no results retrieved from KG, return none
                if results is None:
                    return query_results, resp_code
        return query_results, resp_code

    def __form_and_execute_query(self, relation, entity, topic, entitytype, queryintent,
                                 knowledge_dict=None):
        """
            retrieves knowledge using entity,entity type,relation details
            from database

            Args:
                relation : dict object of relation
                entity : entity name of which knowledge is to be retrieved
                topic : manual section
                entitytype : type of entity
                queryintent : query intent type cause/solution/causes+solution
                knowledge_dict : extracted knowledge using srl,const parser
            Returns:
                query_results : dict
        """
        resp_code = cs.ResponseCode.KER_INTERNAL_FAILED
        try:
            query_results = None

            if (relation == None and knowledge_dict == None):
                return None

            # retrieve knowledge using similarity
            if knowledge_dict == None:
                # function to write cypher query to retrieve data
                query, querykey = self.__form_retrieve_cypher_query(relation, entity,
                                                                    topic, entitytype, queryintent, knowledge_dict)

                # execute query
                results, resp_code = self.graph.run_query(query)
                query_results = self.__parse_graph_results(topic, results, relation, resp_code)
            # knowledge dict and prob key,prob value present
            elif knowledge_dict is not None: # pragma: no cover
                query_results, resp_code = self.__retrieve_by_knowledge_dict(relation, entity, topic, entitytype,
                                                                             queryintent,
                                                                             knowledge_dict)
            logger.debug("Answer from database=%s type=%s", query_results, type(query_results))
            return query_results, resp_code
        except Exception as e:
            logger.exception("retrieve_knowledge :%s", e)
            return None, cs.ResponseCode.KER_INTERNAL_FAILED

    def get_product_type(self, part_no, model_no=None):
        """
        retrieve product type for the given part number

        Args:
            part_no : part number of the manuals
            model_no: model number (optional argument)
        Returns:
            product_type : Type of the product
        """
        product_type = None

        # query to get product type of model
        query = QueryConstants.RETRIEVE_PROD_TYPE % (part_no)
        # execute query
        results, resp_code = self.graph.run_query(query)
        for result in results:
            for key, key_value in result.items():
                product_type = key_value
        return product_type, resp_code

    def get_partnumber(self, model_no):
        """
        retrieve the part number based on the model number

        Args:
            model_no: model number from user request
        Return:
            partnuber: retrieved part number
            response_code: response code
        """
        if (model_no is not None) and (len(model_no.strip()) > 0):
            query = QueryConstants.RETRIEVE_PART_NUMBER .format(model_number=model_no)
            logger.debug("query : %s",query)
            results, resp_code = self.graph.run_query(query)
            logger.debug("DB partnum results : %s", results)
            if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS:
                partnumber = results[0][cs.VALUE]
                logger.debug("partnumber from database=(%s)" % str(partnumber))
                return partnumber, resp_code
        return None, None

    def get_part_nos(self, product_type):
        """
        get all part nos ,sub product type for the all product type

        Args:
            product_type : type of product
        Returns:
            part : Dictionary {(product_type,sub_product_type): [list_of_part_nos]}
        """
        part_nos = {}
        sub_product_type_const = cs.SUB_PRD_TYPE_KEY.lower()
        # query to return sorted model no per product type
        if (product_type is None) or (len(product_type) <= 0):
            query = QueryConstants.RETRIEVE_ALL_PART_NOS
        else:
            query = QueryConstants.RETRIEVE_PROD_PART_NOS % (product_type)
        # execute query
        results, resp_code = self.graph.run_query(query)

        if resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS:
            for result in results:
                product_type_val = result[cs.RS_PRODUCT_TYPE]
                sub_product_type_val = result[sub_product_type_const]
                if sub_product_type_val is None:
                     sub_product_type_val = product_type_val
                dict_key = (product_type_val,sub_product_type_val)
                part_nos[dict_key] = result[cs.VALUE]
            logger.debug("models from database=(%s)" % str(part_nos))
        return part_nos, resp_code

    def __convert_recordlist_todict(self, record): # pragma: no cover
        """
        function to convert cypher record to list

        Args:
            record : cypher record
        Returns:
            final_dict : dict
        """
        logger.debug("record : %s", record)
        json_data = re.search(r"({.*})", record).group(0)
        logger.debug("$$ 1. json_data=%s", json_data)
        text = json_data.split(':')[1]

        # if cypher record starts with single quotes
        if text.strip()[0] == '\'':
            logger.debug("single quote starts with : %s", json_data)
            json_data = re.sub(r"((,|{)\s*([a-zA-Z]+(?:_[a-zA-Z]+)*?)):", r'\2"\3":', json_data)
            json_data = json_data.replace("'", "\"")
        # if cypher record starts with double quotes
        elif text.strip()[0] == '\"':
            logger.debug("starts with double quotes")
            json_data = re.sub(r"((,|{)\s*([a-zA-Z]+(?:_[a-zA-Z]+)*?)):", r'\2"\3":', json_data)
        # convert to dict
        final_dict = json.loads(json_data)
        return final_dict

    def __convert_dict_to_para(self, results): # pragma: no cover
        """
        makes paragraph from python dict
        Args:
            results : dict
        Returns:
            para : str
        """
        para = ""
        # iterate all dict and convert to str and make para
        for eachdict in results:
            if eachdict is not None:
                for key, value in eachdict.items():
                    if value is not None:
                        para += str(value) + " "
        logger.debug(para)
        return para

    def __make_para_from_cypher_results(self, results): # pragma: no cover
        """
        makes paragraph from cypher results
        Args:
            results : cypher record
        Returns:
            para : str
        """
        list_dict = []

        # convert each record to dict
        for result in results:
            if result:
                for key, keyvalue in result.items():
                    if keyvalue is None:
                        continue
                    each_dict = self.__convert_recordlist_todict(str(keyvalue))
                    list_dict.append(each_dict)

        # remove duplicates
        res_list = [i for n, i in enumerate(list_dict) if i not in list_dict[n + 1:]]

        # convert para str from python dict
        para = self.__convert_dict_to_para(res_list)
        return para

    def retrieve_para_from_graph(self, relation, entity, topic, entitytype, subtopic=None): # pragma: no cover
        """
           retrieves knowledge using entity,entity type,relation details
           from database and forms paragraph

           Args:
               relation : dict object of relation
               entity : entity name of which knowledge is to be retrieved
               topic : manual section
               entitytype : type of entity
           Returns:
               para : str
        """
        logger.debug("relation=%s entity=%s topic=%s" % (relation, entity, topic))
        # execute query and form para
        if (relation == cs.HAS_CONTROL_PANEL_FEATURE) or (relation == cs.HAS_CONTROL_PANEL):
            query = OperationQuery.RETRIEVE_CNTLPNL_ALL_INFO % (entitytype, entity)
        else:  # for all other sections
            topic = topic.lower()
            query = OperationQuery.RETRIEVE_SECTION_ALL_INFO % (entitytype, entity, topic)
        logger.info("query for para retreival=%s", query)
        # execute query
        results, resp_code = self.graph.run_query(query)
        logger.debug("result for query : %s resp_code=%s", results, resp_code)
        para = results
        if (resp_code == cs.ResponseCode.KER_INTERNAL_SUCCESS) and (results is not None):
            # makes paragraph from cypher results
            para = self.__make_para_from_cypher_results(results)
            logger.debug("result for para : %s", para)

        return para, resp_code


    def retrieve_knowledge(self, relation, entity, topic, entitytype, queryintent,
                           knowledge_dict=None):
        """
           retrieves knowledge using entity,entity type,relation details
           from database
           Args:
               relation : dict object of relation
               entity : entity name of which knowledge is to be retrieved
               topic : manual section
               entitytype : type of entity
               queryintent : query intent type cause/solution/causes+solution
               knowledge_dict : extracted knowledge using srl,const parser
           Returns:
               query_results : dict
        """
        retrieved_knowledge, resp_code = self.__form_and_execute_query(relation, entity, topic,
                                                                       entitytype, queryintent, knowledge_dict)
        logger.debug("retrieved_knowledge=%s, resp_code=%s", retrieved_knowledge, resp_code)
        return retrieved_knowledge, resp_code


if __name__ == "__main__": # pragma: no cover
    # logger configurtion
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    test_knowledge_dict = dict()
    obj = DBInterface()

    models_output = obj.retrieve_model_nos("microwave oven")
    print(models_output)

    # test for get product type
    test_product_type = obj.retrieve_product_type("VAC900A*")
    print(test_product_type)

    relation = {'key': 'battery run time', 'range': '', 'no_of_batteries': 'two', 'mode': '', 'usage': '',
                'Intent': 'HAS_BATTERY_RUNTIME'}
    test_case_output = obj.retrieve_knowledge(relation, "Specification", "VAC900A*",
                                              cs.SOLUTION_KEY, None, cs.MODEL)
    print("1", test_case_output)

    relation = {'key': 'dimension', 'range': '', 'side': 'width', 'side status': '', 'open status': '',
                'Intent': 'HAS_DIMENSION'}
    test_case_output = obj.retrieve_knowledge(relation, "Specification", "VAC900A*",
                                              cs.SOLUTION_KEY,
                                              None, cs.MODEL)
    print("2", test_case_output)

    relation = {'key': 'net weight', 'range': '', 'Intent': 'HAS_WEIGHT'}
    test_case_output = obj.retrieve_knowledge(relation, "Specification", "VAC900A*",
                                              cs.SOLUTION_KEY,
                                              None, cs.MODEL)
    print("3", test_case_output)

    # retrieve knowledge TS L1 questions
    # What could be the cause of the Spraying sound?
    relation = {"Intent": "HAS_NOISE_PROBLEM",
                "prob_key": "noise",
                "prob_value": "Clicking",
                "prob_value_specific": "Clicking",
                "query_intent": "reason"}
    test_case_output = obj.retrieve_knowledge(relation, "TROUBLESHOOTING", "VAC900A*",
                                              cs.CAUSES_SOL_KEY,
                                              test_knowledge_dict, cs.MODEL)
    print("L1 answer:", test_case_output)
    # retrieve knowledge TS L2 questions
    relation = {"Intent": "HAS_ERROR_CODE",
                "prob_key": "error_code",
                "prob_value": "UE",
                "prob_value_specific": "The wash load may be unbalanced If the washer senses that the load is unbalanced",
                "query_intent": "reason"}

    # test based const parser,SRL
    test_knowledge_dict[cs.ENTITY] = ['Inlet hose', 'drain hose']
    test_knowledge_dict[cs.VERB] = ['know', 'frozen', 'resolve']

    test_case_output = obj.retrieve_knowledge(relation, "TROUBLESHOOTING", "WM4500H*",
                                              cs.CAUSES_SOL_KEY, test_knowledge_dict, cs.MODEL)
    print("L2 answer", test_case_output)

    relation = {"Intent": "HAS_CHECKLIST",
                "prob_key": "direct",
                "prob_value": "before use",
                "prob_value_specific": "before use",
                "query_intent": "reason"}
    test_case_output = obj.retrieve_knowledge(relation, "Operation", "LRFDS3006*",
                                              "desc", None, cs.MODEL)
    print("4", test_case_output)

    relation = {"Intent": "HAS_CHECKLIST",
                "prob_key": "direct",
                "prob_value": "before use",
                "prob_value_specific": "clean the refrigerator",
                "query_intent": "reason"}
    test_case_output = obj.retrieve_knowledge(relation, "Operation", "LRFDS3006*",
                                              "desc", None, cs.MODEL)
    print("5", test_case_output)

    relation = {"Intent": "HAS_FEATURE",
                "prob_key": "direct",
                "prob_value": "sabbath mode",
                "prob_value_specific": "sabbath mode",
                "query_intent": "reason"}
    test_case_output = obj.retrieve_knowledge(relation, "Operation", "LRFDS3006*",
                                              "usage", None, cs.MODEL)
    print("6", test_case_output)

    relation = {"Intent": "HAS_CONTROL_PANEL_FEATURE",
                "prob_key": "direct",
                "prob_value": "control panel",
                "prob_value_specific": "fresh air filter",
                "query_intent": "reason"}
    test_case_output = obj.retrieve_knowledge(relation, "Operation", "LRFDS3006*",
                                              "usage", None, cs.MODEL)
    print("7", test_case_output)

    relation = {"Intent": "HAS_FEATURE",
                "prob_key": "direct",
                "prob_value": "sabbath mode",
                "prob_value_specific": "sabbath mode",
                "query_intent": "turn_on"}
    test_case_output = obj.retrieve_knowledge(relation, "Operation", "LRFDS3006*",
                                              "turn_on", None, cs.MODEL)
    print("8", test_case_output)

    # form para for ice compartment
    paragraph = obj.retrieve_para_from_graph("HAS_COMPONENT", "LRFDS3006*", "ice compartment")
    print(paragraph)

    # form para for storing food
    paragraph = obj.retrieve_para_from_graph("STORING_FOOD", "LRFDS3006*", "ice compartment")
    print(paragraph)
    paragraph = obj.retrieve_para_from_graph("HAS_CONTROL_PANEL", "LRFDS3006*", None)
    paragraph = obj.retrieve_para_from_graph("HAS_CONTROL_PANEL", "LTCS20220*", None)
