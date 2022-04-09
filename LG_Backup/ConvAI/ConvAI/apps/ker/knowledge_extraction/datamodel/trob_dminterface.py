"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com
"""
import json
import sys
import os
import logging as logger
from constants import params as cs
import datamodel.dm_utils as utils

from nlp_engine_client import NlpEngineClient

class TroubleShooting(object):
    """
    Data Modeling class for TroubleShooting section
    Defines the method to create dict object for entities and relationship
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if TroubleShooting.__instance is None:
            TroubleShooting()
        return TroubleShooting.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if TroubleShooting.__instance is not None:
            raise Exception("TroubleShooting is not instantiable")
        else:
            TroubleShooting.__instance = self
            # Info Object for fetching SRL and Constituency parser outputs
            self.nlp_engine_client = NlpEngineClient.get_instance()
            self.use_srl = False
            self.use_cons_parser = False
            self.image_interface = im_interface.ImageHandlingInterface()
            self.main_section = cs.XMLTags.TROUBLESHOOT_TAG

    def __refer_schema_create_triplet(self, domain_relation_range,
                                      knowledge_dict=None, prop_value=None, issue_type_value=None, domain_type=None,
                                      ent_prd_type=None, partnumber=None):
        """
           refer the schema for given key and finds the node type of domain
           range nodes
           Args:
                domain_relation_range: tuple of (domain value, generic key, range value)
                knowledge_dict : dict
                prop_value :str
           Returns:
               domain : Node object
               relation: Relation object
               range: Node object
        """
        domainvalue, generickey, rangevalue = domain_relation_range
        try:
            # refer schema for specified generic key
            schema_dict = utils.SCHEMA_OBJ.get_schema_for_key(generickey)
            logger.debug("generickey=%s", generickey)
            logger.debug("schema_dict=%s", str(schema_dict))

            relation_name = schema_dict[cs.LABEL][0][cs.VALUE]

            # getting range node type based on defined schema
            if domain_type is None:
                domain_type = schema_dict[cs.DOMAIN][0][cs.ID]

            # getting range node type based on defined schema
            range_type = schema_dict[cs.RANGE][0][cs.ID]

            logger.debug("domain type=%s rangetype=%s relation=%s" % (domain_type,
                                                                      range_type,
                                                                      relation_name))

            if (generickey == cs.HAS_ERROR or generickey == cs.HAS_NOISE or
                    generickey == cs.HAS_PROBLEM or generickey == cs.HAS_COOLING_PROBLEM
                    or generickey == cs.HAS_ICE_PROBLEM or generickey == cs.HAS_WIFI_PROBLEM
                    or generickey == cs.HAS_TROUBLESHOOTING_PROBLEM
                    or generickey == cs.DIAGNOSE_WITH_LG_THINQ
                    or generickey == cs.DIAGNOSE_WITH_BEEP
                    or generickey == cs.HAS_PROCEDURE):
                # Create a dictionary for properties for Relation
                relation_prop_dict = dict()

                self._fill_relation_dict(issue_type_value, partnumber, prop_value, relation_prop_dict
                                         , schema_dict, ent_prd_type)

                # create relation
                relation = utils.Relation(relation_name, relation_prop_dict)

                # create  model node
                domain = utils.Node(domain_type, domainvalue, None)

                # create end node
                rangenode = utils.Node(range_type, rangevalue, knowledge_dict)
                logger.debug(
                    "Created triplet:" + "domain : {}, relation : {}, range : {}".format(domain, relation, rangenode))
                return domain, relation, rangenode
            else:
                # This Else is a case for creating FAQ triplets & answer triplets
                # This else is a case for HAS_QUESTION and HAS_ANSWER & HAS_SOLUTION

                # Create a dictionary for properties for Relation
                relation_prop_dict = dict()

                if generickey == cs.HAS_QUESTION:
                    # only FAQ's contain issue type
                    issue_type = schema_dict[cs.ISSUE_TYPE][0][cs.VALUE]
                    # Check for not None
                    # relation_prop_dict = dict()
                    self._fill_relation_dict(issue_type_value=issue_type_value, en_prd_type=ent_prd_type,
                                             relation_prop_dict=relation_prop_dict, schema_dict=schema_dict)
                    # for future ref if issue_type_value is not None:
                    #     relation_prop_dict = dict()
                    #     relation_prop_dict[issue_type] = issue_type_value

                self._fill_relation_dict(partnumber=partnumber, en_prd_type=ent_prd_type,
                                         relation_prop_dict=relation_prop_dict, schema_dict=schema_dict)

                relation = utils.Relation(relation_name, relation_prop_dict)
                # create  model node
                domain = utils.Node(domain_type, domainvalue, knowledge_dict)

                # create end node
                rangenode = utils.Node(range_type, rangevalue, None)

                logger.debug(
                    "Created triplet:" + "domain : {}, relation : {}, range : {}".format(domain, relation, rangenode))
                return domain, relation, rangenode
        except Exception as e:
            logger.exception("Error in __refer_schema_create_triplet" + str(e))

    def _fill_relation_dict(self, issue_type_value=None, partnumber=None, prop_value=None, relation_prop_dict=None
                            , schema_dict=None, en_prd_type=None):
        logger.debug("relation_prop_dict : relation_prop_dict=%s, prop_value=%s",relation_prop_dict,prop_value)
        logger.debug("schema_dict : %s",schema_dict)
        # Check prop_value & issue_type_value not none before adding to relation_prop_dict
        # if prop_value is not None:
        #     prop_key = schema_dict[cs.PROP][0][cs.VALUE]
        #     relation_prop_dict[prop_key] = prop_value

        if issue_type_value is not None:
            issue_type = schema_dict[cs.ISSUE_TYPE][0][cs.VALUE]
            relation_prop_dict[issue_type] = issue_type_value

        if cs.PROP in schema_dict:
            for prop_key in schema_dict[cs.PROP]:
                if (prop_key[cs.VALUE] == cs.ENTITY_PRD_TYPE) and (en_prd_type is not None):
                    relation_prop_dict[cs.ENTITY_PRD_TYPE] = en_prd_type
                elif (prop_key[cs.VALUE] == cs.PART_NUMBER_PROP) and (partnumber is not None):
                    relation_prop_dict[cs.PART_NUMBER_PROP] = partnumber
                elif ((prop_key[cs.VALUE] == cs.PROBLEM_PROP) or (prop_key[cs.VALUE] == cs.ERR_CODE_PROP)
                      or (prop_key[cs.VALUE] == cs.NOISE_PROP)) and (prop_value is not None):
                    relation_prop_dict[prop_key[cs.VALUE]] = prop_value

    def __make_triplets_causesolution(self, model_no_list, section, problem, cause, solution,
                                      triplets_list):
        """
            creates list of triplets(Node,Relation,Node)  for all the input key
            ,value pairs of input dict
            Args:
                model_no_list : list
                          list of model nos
                section : str
                          section of the troubleshooting
                problem : str
                          Error code of each error
                cause : list
                        list of all causes
                solution : list
                        list of all solutions
                triplets_list : list
                                list to store all triplets
            Returns:
                list of Triplet objects
        """
        eachcause = ""
        knowledge_dict = None

        # Get Common key based on the Section
        commonkey = cs.get_troubleshooting_mapping_key_relation(section)

        # find generic key of given error code
        # For specific relationship
        commonkey_new = utils.DMUtils.get_common_key(problem,
                                                     cs.trob_section["TROUBLESHOOT_KEYS"])

        logger.info("Common Key=(%s)" % commonkey)

        # To remove dependency
        # This is if some problem is misclassified in another category
        # Ex: Noises if Classified as Operation (From Manual)
        if commonkey_new is not None and len(commonkey_new) > 0:
            commonkey = commonkey_new

        # Remove the trailing dots (.) from the problem
        problem = problem.strip(".")

        # If no common key is available then the default key is "HAS_PROBLEM"
        if commonkey is None:
            commonkey = cs.HAS_TROUBLESHOOTING_PROBLEM

        # creating all causes triplets
        for eachcause in cause:
            logger.info("Eachcause=(%s)" % eachcause)
            # Remove the trailing dots (.) from the cause
            eachcause = eachcause.strip().strip(".").strip()

            # update_node_with_knowledge
            knowledge_dict = self.__get_knowledge_from_cause(eachcause)
            # Capitalize
            eachcause = eachcause.capitalize()
            # refer schema and generate triplet
            for each_model in model_no_list:
                domain, relation, rangenode = self.__refer_schema_create_triplet(
                    (each_model, commonkey, eachcause), knowledge_dict,
                    problem, issue_type_value=section, ent_prd_type=self.ent_prd_type, partnumber=self.part_no)

                # create each Node_Relation
                eachtriplet = utils.NodeRelation(domain.__dict__,
                                                 relation.__dict__,
                                                 rangenode.__dict__)

                triplets_list.append(eachtriplet.__dict__)

        commonkey = cs.HAS_SOLUTION
        # creating all solutions triplets
        logger.info("Solutions =%s " % solution)
        for eachsolution in solution:
            logger.info("Each Solution=(%s)" % eachsolution)
            # refer schema and generate triplet
            # cause,solution,list of solutions
            eachsolution = eachsolution.capitalize()
            domain, relation, rangenode = self.__refer_schema_create_triplet(
                (eachcause, commonkey, eachsolution), knowledge_dict, ent_prd_type=self.ent_prd_type,
                partnumber=self.part_no)
            # create each Node_Relation
            eachtriplet = utils.NodeRelation(domain.__dict__, relation.__dict__,
                                             rangenode.__dict__)

            logger.info("Each Cause triplet:" + str(eachtriplet.__dict__))
            triplets_list.append(eachtriplet.__dict__)

        logger.debug("Causesoltuions triplets:" + str(triplets_list))
        return triplets_list

    def __get_knowledge_from_cause(self, cause):
        """
            Call SRL,constituency parser APIS and get knowledge
            Args:
                cause : str
            Returns:
                knowledge_dict : dict object
        """
        knowledge_dict = dict()
        srl_const_output = None
        if self.use_cons_parser and self.use_srl:
            # For storing SRL and Constituency parsers output
            srl_const_output = self.nlp_engine_client.get_srl_cons(cause)

            # load the json string into a json
            srl_const_output = json.loads(srl_const_output)

            logger.debug("srl_const_output :" + str(srl_const_output))

            # Check for response_code
            if srl_const_output[cs.resp_code] != cs.SUCCESS:
                return None

            # Get the response data as per the new format
            srl_const_output = srl_const_output[cs.resp_data]

        if self.use_cons_parser:
            # Get the constituency parser output from srl_const_output
            self._get_knowledge_from_constituency_parser(knowledge_dict, srl_const_output)

        if self.use_srl:
            purpose, reason, temporal = self._get_knowledge_from_srl(srl_const_output)

            # Check if the size of the list if it is zero (then don't add to knowledge_dict)
            if len(reason) > 0:
                # To remove duplicates and sort
                reason = sorted(set(reason))
                knowledge_dict[cs.CAUSE] = reason
            if len(purpose) > 0:
                # To remove duplicates and sort
                purpose = sorted(set(purpose))
                knowledge_dict[cs.PURPOSE] = purpose
            if len(temporal) > 0:
                # To remove duplicates and sort
                temporal = sorted(set(temporal))
                knowledge_dict[cs.TEMPORAL] = temporal

        # if empty dictionary return none
        if not bool(knowledge_dict) is True:
            return None
        logger.info("knowledge_dict=(%s)", str(knowledge_dict))
        return knowledge_dict

    def _get_knowledge_from_srl(self, srl_const_output):
        reason = []
        purpose = []
        temporal = []
        # Get the constituency parser output from srl_const_output
        srl_output = srl_const_output[cs.InfoKnowledge.SRL]
        logger.info("srl_output wrapper=(%s)", str(srl_output))
        # Loop through srl_output and get reason, temporal, purpose
        for key, value in srl_output.items():
            logger.info("value:(%s)", str(value))
            if cs.CAUSE == key:
                reason = value
                reason = [item.lower() for item in reason if len(item.strip()) != 0]
            elif cs.TMPRL == key:
                temporal = value
                temporal = [item.lower() for item in temporal if len(item.strip()) != 0]
            elif cs.PURPOSE == key:
                purpose = value
                purpose = [item.lower() for item in purpose if len(item.strip()) != 0]
        logger.info("reas_lem=(%d)pur_len=(%d) temp_len=(%d)" % (len(reason),
                                                                 len(purpose), len(temporal)))
        return purpose, reason, temporal

    def _get_knowledge_from_constituency_parser(self, knowledge_dict, srl_const_output):
        const_output = srl_const_output[cs.InfoKnowledge.CONS_PARSER]
        logger.info("Const wrapper=(%s)", str(const_output))
        entity = const_output[cs.NP]
        verb = const_output[cs.VB]
        if len(entity) > 0:
            entity = [item.lower() for item in entity if len(item.strip()) != 0]
            if len(entity) > 0:
                # To remove duplicates and sort
                entity = sorted(set(entity))
                knowledge_dict[cs.ENTITY] = entity
        if len(verb) > 0:
            verb = [item.lower() for item in verb if len(item.strip()) != 0]
            if len(verb) > 0:
                # To remove duplicates and sort
                verb = sorted(set(verb))
                knowledge_dict[cs.VERB] = verb

    def __make_triplets_for_troubleshooting(self, model_no_list, section, section_info, en_prd_type=None):
        """
            creates list of triplets(Node,Relation,Node)  for all the input key
            ,value pairs of input dict
            Args:
                model_no_list - list
                          list pf model nos from the manual
                list_dict - list
                          list of dict objects
            Returns:
                list of Triplet objects
        """
        try:
            triplets_list = []
            logger.info("model no list =%s, section=%s, section_info=%s ", model_no_list, str(section),
                        str(section_info))

            # If the section info is FAQ or Other sections call the corresponding functions accordingly
            if section == cs.FAQ:
                triplets_list = self.__make_triplets_forfaq(model_no_list, section_info)
            else:
                # Create triplets for Non-FAQ Content
                for each_sub_section in section_info:
                    for each_problem, cause_sol_list in each_sub_section.items():
                        error_code_or_problem = each_problem
                        cause_sol = cause_sol_list[cs.CAUSES_SOL_KEY]
                        for each_item in cause_sol:
                            causes_list = [each_item[cs.REASON_KEY]]
                            solution_list = each_item[cs.SOLUTION_KEY]
                            self.__make_triplets_causesolution(model_no_list, section, error_code_or_problem,
                                                               causes_list, solution_list, triplets_list)
            return triplets_list
        except (KeyError, ValueError, AttributeError) as e:
            logger.exception("Error in __make_triplets_forproblems" + str(e))
            return None

    def __make_triplets_foreachfaq(self, modelno, question, solution,
                                   triplets_list):
        """
            creates list of triplets(Node,Relation,Node)  for all the input key
            ,value pairs of input dict
            Args:
                modelno : str
                          modelno belongs to all error msgs
                question : str
                          Each question in FAQ
                solution : list
                        list of all solutions
                triplets_list : list
                                list to store all triplets
            Returns:
                list of Triplet objects
        """
        try:
            logger.info("__make_triplets_foreachfaq modelno = %s, question = %s, solution = %s",
                        str(modelno), str(question), str(solution))

            commonkey = cs.HAS_QUESTION
            domain, relation, rangenode = self.__refer_schema_create_triplet(
                (modelno, commonkey, question), issue_type_value=cs.FAQ, ent_prd_type=self.ent_prd_type,
                partnumber=self.part_no)
            # create each Node_Relation
            eachtriplet = utils.NodeRelation(domain.__dict__,
                                             relation.__dict__,
                                             rangenode.__dict__)
            triplets_list.append(eachtriplet.__dict__)

            commonkey = cs.HAS_ANSWER
            for eachsolution in solution:
                eachsolution = eachsolution.capitalize()
                domain, relation, rangenode = self.__refer_schema_create_triplet(
                    (question, commonkey, eachsolution), ent_prd_type=self.ent_prd_type, partnumber=self.part_no)
                # create each Node_Relation
                eachtriplet = utils.NodeRelation(domain.__dict__,
                                                 relation.__dict__, rangenode.__dict__)

                logger.debug("Each answer triplet:" + str(eachtriplet.__dict__))
                triplets_list.append(eachtriplet.__dict__)
            return triplets_list
        except (KeyError, ValueError, AttributeError) as e:
            logger.exception("Error in __make_triplets_foreachfaq" + str(e))
            return None

    def __make_triplets_forfaq(self, model_no_list, list_dict):
        """
            creates list of triplets(Node,Relation,Node)  for all the input key
            ,value pairs of input dict
            Args:
                modelno - str
                          modelno of manual
                list_dict - list
                          list of dict objects
            Returns:
                list of Triplet objects
        """
        try:
            triplets_list = []
            list_value = []
            logger.debug("model nos=%s dict_object=%s", model_no_list, str(list_dict))

            for key, value in list_dict.items():
                list_value.clear()
                # parse each answer in a list
                for eachitem in value:

                    list_value.append(eachitem)
                    logger.debug("question=(%s) answer=(%s)" % (key,
                                                                str(list_value)))
                    for eachmodel in model_no_list:
                        self.__make_triplets_foreachfaq(eachmodel, key, list_value,
                                                        triplets_list)

            return triplets_list
        except (KeyError, ValueError, AttributeError) as e:
            logger.exception("Error in __make_triplets_forproblems" + str(e))
            return None

    def __make_triplet_for_producttype(self, modelno, product_type):
        """
            creates triplet(Node,Relation,Node)  for all the product type
            Args:
                modelno - str
                product_type - str
            Returns:
                triplet - dict
        """
        prodtype_key = cs.PRODUCT

        # create triplet for product type and model
        domain, relation, rangenode = self.__refer_schema_create_triplet(
            (modelno, prodtype_key, product_type))

        #  create each Node_Relation
        triplet = utils.NodeRelation(domain.__dict__,
                                     relation.__dict__,
                                     rangenode.__dict__)

        return triplet

    def __make_triplets_for_diagnosing_a_fault(self, models_list, section, section_info):
        """
        Create triplets for the section Diagnosing a fault
        Args:
            models_list: The list of model numbers for which the section is applicable
            section: The section under 'Diagnosing a fault' Ex: Diagnosing faults with LG ThinQ
            and Diagnosing a fault with a beep
            section_info: The information under the section which can include either Description or some procedure

        Returns:
            List of triplets for Diagnosing a fault section
        """
        logger.debug("Inside the __make_triplets_for_diagnosing_a_fault with " + str(section))
        triplets_list_local = []
        try:
            # Get Common key based on the Section
            commonkey = cs.get_troubleshooting_mapping_key_relation(section)

            # if there is a Description take the Description or else the section name will be the description
            diagnose_fault_desc = section
            if cs.DESCRIPTION in section_info:
                diagnose_fault_desc = "".join(section_info[cs.DESCRIPTION])

            # refer schema and generate triplet for Description
            range_prop = {}
            range_prop[cs.DESC_KEY] = diagnose_fault_desc
            for each_model in models_list:
                domain, relation, rangenode = self.__refer_schema_create_triplet(
                    (each_model, commonkey, diagnose_fault_desc), knowledge_dict=range_prop, issue_type_value=section
                     , ent_prd_type=self.ent_prd_type, partnumber=self.part_no)

                # create each Node_Relation
                each_diagnosing_a_fault_triplet = utils.NodeRelation(domain.__dict__,
                                                                     relation.__dict__,
                                                                     rangenode.__dict__)
                triplets_list_local.append(each_diagnosing_a_fault_triplet.__dict__)

            # refer schema and generate triplets for Procedure
            procedure_steps = None
            if cs.XMLTags.PROCEDURE_TAG in section_info:

                procedure_steps = section_info[cs.XMLTags.PROCEDURE_TAG]

                TROB_REL = ""

                if section == cs.DIAGNOSING_FAULT_THINQ:
                    TROB_REL = cs.DIAGNOSE_WITH_LG_THINQ
                elif (section == cs.DIAGNOSING_FAULT_BEEP):
                    TROB_REL = cs.DIAGNOSE_WITH_BEEP

                self.sub_section = cs.DIAGNOSING_FAULT
                domain_type_for_current_sub_section = self._get_range_type_for_generic_key(TROB_REL)
                # pdb.set_trace()
                domain_prop = {}
                logger.debug("diagnose_fault_desc : %s",diagnose_fault_desc)
                if diagnose_fault_desc is not None:
                    domain_prop[cs.DESC_KEY] = diagnose_fault_desc
                ptriplets_list_local = self._create_triplets_for_procedure(section, procedure_steps, domain_prop,
                                                                           domain_type_for_current_sub_section)
                triplets_list_local = triplets_list_local + ptriplets_list_local
                # for future reference procedure_generic_key = cs.HAS_PROCEDURE
                # procedure_domain_type = cs.DIAGNOSE_FAULT_NODE

                # for future reference step_count = 0
                # for every_step in procedure_steps:
                #     step_count = step_count + 1
                #     procedure_relation_props = {cs.STEP_NO_PROP: step_count}
                #     domain, relation, rangenode = self.__refer_schema_create_triplet(
                #         (diagnose_fault_desc, procedure_generic_key,
                #          every_step[cs.STEP]),
                #         prop_value=procedure_relation_props,
                #         domain_type=procedure_domain_type)
                #
                #     procedure_step_triplet = utils.NodeRelation(domain.__dict__,
                #                                                 relation.__dict__,
                #                                                 rangenode.__dict__)
                #     triplets_list_local.append(procedure_step_triplet.__dict__)
                #
                #     # Handle Notes
                #     # The domain type for note will be the range type of the generic key
                #     if cs.NOTE in every_step:
                #         note_steps_list = every_step[cs.NOTE]
                #         note_triplets = self._create_triplets_for_note(note_domain=every_step[cs.STEP],
                #                                                        note_steps=note_steps_list,
                #                                                        note_domain_type=cs.VALUE_NODE)
                #         # Add the caution triplets to the usage triplets
                #         triplets_list_local = triplets_list_local + note_triplets
        except Exception as e:
            logger.exception("Troubleshooting : Error in __make_triplets_for_diagnosing_a_fault " + str(e))

        return triplets_list_local

    def _get_range_type_for_generic_key(self, generic_key_for_sub_section):
        """
        Gives a range type for a given generic key as per the RDF Schema

        Args:
            generic_key_for_sub_section:

        Returns:
            The range type for a specific relation
        """
        rdf_type_value_from_schema = utils.SCHEMA_OBJ.get_schema_for_key(generic_key_for_sub_section)

        range_type = rdf_type_value_from_schema[cs.RANGE][0][cs.ID]

        return range_type

    def _create_triplets_for_procedure(self, procedure_domain, procedure_steps,
                                       procedure_domain_props, procedure_domain_type):
        """
        Create triplets for procedure tags
        """
        triplets_list_local = []

        procedure_generic_key = cs.HAS_PROCEDURE

        step_count = 0
        for every_step in procedure_steps:
            step_count = step_count + 1
            procedure_range_props = {cs.STEP_NO_PROP: step_count}
            range_desc = None
            range_desc = self._get_description_for_sections(every_step)
            if range_desc is not None:
                procedure_range_props[cs.DESC_KEY] = range_desc
            procedure_step_triplet = self._refer_schema_create_triplet((procedure_domain, procedure_generic_key,
                                                                        every_step[cs.STEP]),
                                                                       range_props=procedure_range_props,
                                                                       domain_props=procedure_domain_props,
                                                                       domain_type=procedure_domain_type)

            triplets_list_local.append(procedure_step_triplet)

            # To Handle Images
            if cs.ExtractionConstants.FIGURE in every_step:
                image_content = every_step[cs.ExtractionConstants.FIGURE]
                image_triplets = self._create_triplets_for_image(image_domain=every_step[cs.STEP],
                                                                 image_content=image_content,
                                                                 image_domain_props=procedure_range_props,
                                                                 image_domain_type=cs.PROCEDURE_NODE,
                                                                 image_sub_section=self.sub_section)
                # pdb.set_trace()
                # Add the caution triplets to the usage triplets
                triplets_list_local = triplets_list_local + image_triplets

            # Handle Notes
            # The domain type for note will be the range type of the generic key
            if cs.NOTE in every_step:
                note_steps_list = every_step[cs.NOTE]
                note_triplets = self._create_triplets_for_note(note_domain=every_step[cs.STEP],
                                                               note_steps=note_steps_list,
                                                               note_domain_type=cs.PROCEDURE_NODE)

                # Add the caution triplets to the usage triplets
                triplets_list_local = triplets_list_local + note_triplets

            if cs.CAUTION in every_step:
                caution_steps_list = every_step[cs.CAUTION]
                caution_triplets = self._create_triplets_for_caution(caution_domain=every_step[cs.STEP],
                                                                     caution_steps=caution_steps_list,
                                                                     caution_domain_props=procedure_range_props,
                                                                     caution_domain_type=cs.PROCEDURE_NODE)
                # Add the caution triplets to the usage triplets
                triplets_list_local = triplets_list_local + caution_triplets

            if cs.XMLTags.WARNING_TAG in every_step:
                warning_steps_list = every_step[cs.XMLTags.WARNING_TAG]
                warning_triplets = self._create_triplets_for_warning(warning_domain=every_step[cs.STEP],
                                                                     warning_steps=warning_steps_list,
                                                                     warning_domain_props=procedure_range_props,
                                                                     warning_domain_type=cs.PROCEDURE_NODE)
                # Add the caution triplets to the usage triplets
                triplets_list_local = triplets_list_local + warning_triplets

        return triplets_list_local

    def _create_triplets_for_image(self, image_domain, image_content, image_domain_props, image_domain_type,
                                   image_sub_section):
        """
        Function to create triplets for images
        Args:
            image_domain: Domain node for image
            image_content: A dictionary which contains file_path, size and file_type
            image_domain_props: The domain properties if any for image relation
            image_domain_type: The domain type for this image relation as Image supports multiple domain types
            as per RDF
            image_sub_section: The sub section where the image is coming from, used for creating new relative path
            in image_db

        Returns:
            List of image triplets for corresponding domain
        """
        triplets_list_local = []

        # Call the image handling module to copy the images and getting the relative path
        image_response = self.image_interface.get_image_information(self.product_type, self.main_section,
                                                                    image_sub_section,
                                                                    self.part_no, image_content)

        try:
            if image_response[cs.resp_code] == cs.ResponseCode.SUCCESS:
                logger.info("Image handling success: Image copied and relative path generated.")

                image_name = image_response[cs.resp_data][cs.IMAGE_NAME]
                image_range_props = image_response[cs.resp_data][cs.IMAGE_CONTENT]

                image_generic_key = cs.HAS_IMAGE
                image_step_triplet = self._refer_schema_create_triplet((image_domain, image_generic_key, image_name),
                                                                       domain_props=image_domain_props,
                                                                       domain_type=image_domain_type,
                                                                       range_props=image_range_props)

                triplets_list_local.append(image_step_triplet)

                return triplets_list_local
            elif image_response[cs.resp_code] == cs.ResponseCode.DATA_NOT_FOUND:
                logger.info("Image handling failed : " + str(image_response))
                raise ValueError("Image handling failed : " + str(image_response))
        except Exception as e:
            logger.exception("Operation : Error in _create_triplets_for_image " + str(e))

    def _get_description_for_sections(self, section_info):
        """
        Utility function to combine the descriptions list into a single description
        """
        desc_temp = None
        if cs.DESCRIPTION in section_info:
            desc_temp = " ".join(section_info[cs.DESCRIPTION])

        if cs.DESCRIPTION_POINTS in section_info:
            for each_desc_points in section_info[cs.DESCRIPTION_POINTS]:
                if desc_temp is None:
                    desc_temp = " ".join(each_desc_points[cs.DESCRIPTION])
                else:
                    desc_temp += " ".join(each_desc_points[cs.DESCRIPTION])
        return desc_temp

    def _refer_schema_create_triplet(self, domain_relation_range, domain_props=None,
                                     relation_props=None,
                                     range_props=None, domain_type=None, range_type=None):
        """
        The central method to refer to the RDF Schema and create triplets

        Args:
            domain_relation_range: The tuple containing domain/left node, relationship and range_value
            domain_props: The properties for domain node
            relation_props: The properties for relation node
            range_props: The properties for domain node
            domain_type: The type of domain to be specified explicitly if the Schema has multiple types for the Domain
            range_type: The type of range to be specified explicitly if the Schema has multiple types for the range

        Returns:
            Created triplet in dictionary format one at a time
        """
        domain_value, relationship, range_value = domain_relation_range
        try:
            # generic_key is the proper relationship name after getting from OperationMappingRelation in params
            generic_key = relationship

            schema_dict = utils.SCHEMA_OBJ.get_schema_for_key(generic_key)
            logger.debug("generic key=%s", generic_key)
            logger.debug("schema_dict=%s", str(schema_dict))

            relation_name = schema_dict[cs.LABEL][0][cs.VALUE]

            # getting range node type based on defined schema
            if domain_type is None:
                domain_type = schema_dict[cs.DOMAIN][0][cs.ID]

            # getting range node type based on defined schema
            if range_type is None:
                range_type = schema_dict[cs.RANGE][0][cs.ID]

            if relation_name != cs.HAS_PART_NUMBER and relation_name != cs.REL_TYPE_OF:
                if relation_props is not None:
                    relation_props[cs.PART_NUMBER_PROP] = self.part_no
                    relation_props[cs.ENTITY_PRD_TYPE] = self.ent_prd_type
                elif relation_props is None:
                    relation_props = {cs.PART_NUMBER_PROP: self.part_no, cs.ENTITY_PRD_TYPE: self.ent_prd_type}

            # Check the properties with the RDF Schema
            if relation_props is not None:
                relation_props = self._check_in_schema_for_properties(relation_name, relation_props)
            if domain_props is not None:
                domain_props = self._check_in_schema_for_properties(domain_type, domain_props)
            if range_props is not None:
                range_props = self._check_in_schema_for_properties(range_type, range_props)

            # create relation
            relation = utils.Relation(relation_name, relation_props)

            # create  model node
            domain = utils.Node(domain_type, domain_value, domain_props)

            # create end node
            range_node = utils.Node(range_type, range_value, range_props)

            # Return the triplet in proper dictionary format
            # Create each Node_Relation
            each_triplet = utils.NodeRelation(domain.__dict__, relation.__dict__,
                                              range_node.__dict__)
        except Exception as e:
            logger.exception("Operation : Error in _refer_schema_create_triplet " + str(e))

        return each_triplet.__dict__

    def _create_triplets_for_caution(self, caution_domain, caution_steps, caution_domain_props, caution_domain_type):
        """
        Function to create triplets for cautions

        Args:
            caution_domain: Domain node for Caution
            caution_steps: The list of Cautions
            caution_domain_props: The domain properties if any for caution relation
            caution_domain_type: The domain type for this caution relation as caution supports multiple domain types
            as per RDF

        Returns:
            List of caution triplets
        """
        triplets_list_local = []

        caution_generic_key = cs.HAS_CAUTION

        # Caution will have 'Description points' i.e., list of 'Description' which can have 'figure' also
        caution_steps = caution_steps[cs.DESCRIPTION_POINTS]

        for every_caution in caution_steps:
            caution_desc = every_caution[cs.DESCRIPTION]
            caution_desc = " ".join(caution_desc)
            caution_step_triplet = self._refer_schema_create_triplet(
                (caution_domain, caution_generic_key, caution_desc),
                domain_props=caution_domain_props,
                domain_type=caution_domain_type)
            triplets_list_local.append(caution_step_triplet)

            # If the caution contains image
            if cs.ExtractionConstants.FIGURE in every_caution:
                image_content = every_caution[cs.ExtractionConstants.FIGURE]
                caution_img_triplet = self._create_triplets_for_image(caution_desc, image_content, None, cs.VALUE_NODE,
                                                                      image_sub_section=self.sub_section)

                triplets_list_local = triplets_list_local + caution_img_triplet

        return triplets_list_local

    def _create_triplets_for_warning(self, warning_domain, warning_steps, warning_domain_props, warning_domain_type):
        """
        Function to create triplets for warnings
        Args:
            warning_domain: Domain node for warning
            warning_steps: The list of Notes
            warning_domain_props: The domain properties if any for warning relation
            warning_domain_type: The domain type for this warning relation as warning supports multiple domain types
            as per RDF

        Returns:
            List of warning triplets for corresponding domain
        """
        triplets_list_local = []

        warning_generic_key = cs.HAS_WARNING
        # Warning will have 'Description points' i.e., list of 'Description' which can have 'figure' also
        warning_steps = warning_steps[cs.DESCRIPTION_POINTS]

        for every_warning in warning_steps:
            warning_desc = every_warning[cs.DESCRIPTION]
            warning_desc = " ".join(warning_desc)
            warning_step_triplet = self._refer_schema_create_triplet(
                (warning_domain, warning_generic_key, warning_desc),
                domain_props=warning_domain_props,
                domain_type=warning_domain_type)

            triplets_list_local.append(warning_step_triplet)

            # If the warning contains image
            if cs.ExtractionConstants.FIGURE in every_warning:
                image_content = every_warning[cs.ExtractionConstants.FIGURE]
                warning_img_triplet = self._create_triplets_for_image(warning_desc, image_content, None, cs.VALUE_NODE,
                                                                      self.sub_section)

                triplets_list_local = triplets_list_local + warning_img_triplet

        return triplets_list_local

    def _check_in_schema_for_properties(self, rdf_type, rdf_type_props):
        """
        Function to check the given properties matches with the properties in the RDF schema.
        If there is a mismatch those properties and their values are removed.

        Args:
            rdf_type: The type from the RDF schema or the name of domain / relation / range
            rdf_type_props: Dictionary of properties prepared

        Returns:
            Filtered list of properties which are defined in RDF Schema for corresponding RDF type
        """
        rdf_type_value_from_schema = utils.SCHEMA_OBJ.get_schema_for_key(rdf_type)

        # Code to filter and remove the properties which are not available in the RDF Schema
        if cs.PROP in rdf_type_value_from_schema and rdf_type_props is not None:
            props_from_schema = [temp_dict[cs.VALUE] for temp_dict in rdf_type_value_from_schema[cs.PROP]]
            rdf_type_props = {k: v for k, v in rdf_type_props.items() if k in props_from_schema}

        return rdf_type_props

    def _create_triplets_for_note(self, note_domain, note_steps, note_domain_type):
        """
        Function to create triplets for notes
        Args:
            note_domain: Domain node for note
            note_steps: The list of Notes
            note_domain_type: The domain type for this note relation as note supports multiple domain types
            as per RDF

        Returns:
            List of note triplets for corresponding domain
        """
        triplets_list_local = []

        note_generic_key = cs.HAS_NOTE

        domain, relation, rangenode = None, None, None

        for every_note in note_steps:
            for key, value in every_note.items():
                if key == cs.DESCRIPTION_POINTS:
                    for description_dict in value:
                        domain, relation, rangenode = self.__refer_schema_create_triplet(
                            (note_domain, note_generic_key, (" ".join(description_dict[cs.DESCRIPTION]).strip())),
                            domain_type=note_domain_type, ent_prd_type= self.ent_prd_type, partnumber=self.part_no)
                elif key == cs.DESCRIPTION:
                    domain, relation, rangenode = self.__refer_schema_create_triplet(
                        (note_domain, note_generic_key, (" ".join(value).strip())),
                        domain_type=note_domain_type, ent_prd_type=self.ent_prd_type, partnumber=self.part_no)

                if (domain is not None) and (relation is not None) and (rangenode is not None):

                    note_step_triplet = utils.NodeRelation(domain.__dict__,
                                                           relation.__dict__,
                                                           rangenode.__dict__)

                    triplets_list_local.append(note_step_triplet.__dict__)


        return triplets_list_local

    def make_triplets(self, dict_object, product_type=None):
        """
        creates list of triplets(Node,Relation,Node) for list of input dict
            Args:
                dict_object - dict
                product_type - str, None by default, taken directly from dict_object
            Returns:
                On success - list of Triplet objects
                On Error - None
        """

        # The dict_object contains the status of extraction and the data

        try:
            # To handle the status of extraction
            if dict_object is None:
                logger.debug("Triplet dictionary is None\n")
                return None
            elif dict_object[cs.ExtractionConstants.STATUS_STR] == cs.ExternalErrorCode.MKG_SECTION_NOT_AVAILABLE:
                logger.debug("Triplet dictionary has no Section\n")
                return None
            elif dict_object[cs.ExtractionConstants.STATUS_STR] == cs.ExternalErrorCode.MKG_FORMAT_NOT_SUPPORTED:
                logger.debug("Triplet dictionary format is not supported\n")
                return None
            elif dict_object[cs.ExtractionConstants.STATUS_STR] == cs.ExternalErrorCode.MKG_SUCCESS:
                logger.debug("Triplet dictionary format is supported\n")

            # For handling the actual troubleshooting data
            triplets_list = []
            # new_dict_temp is the actual dictionary file containing the troubleshooting data
            new_dict_temp = dict_object[cs.ExtractionConstants.DATA_KEY][cs.TROUBLESHOOTING]

            self.product_type, self.sub_prd_type = self._get_product_type(new_dict_temp)
            self.part_no = new_dict_temp[cs.PARTNUMBER]

            triplets_list_temp = self._make_triplets_internal(new_dict_temp)
            triplets_list = triplets_list + triplets_list_temp

            return triplets_list

        except (KeyError, ValueError, AttributeError) as e:
            logger.exception("Error in make_triplets" + str(e))
            return None

    def _get_product_type(self, new_dict_object):
        """
        Returns a generic product name for raw names coming from the manual content
        Example: Washing Machine/Washer maps to "washing machine"

        Args:
            new_dict_object: Input dictionary (operation) which contains the product type info

        Returns:
            Generic name for that particular product
        """
        # Fetching Product type from dictionary object
        product_type = new_dict_object[cs.PRODUCT_TYPE]
        sub_prd_type = new_dict_object[cs.SUB_PRD_TYPE_KEY]
        # Convert the product_type to lower case
        product_type = product_type.lower()
        # Get the generic product names for population
        generic_product_name = cs.get_generic_product_name(product_type)
        # Assign the generic_product_name to product_type if None
        if generic_product_name is not None:
            product_type = generic_product_name

        logger.debug("Operation : get_product_type : output : {}".format(str(product_type)))

        return product_type, sub_prd_type

    def _make_triplet_for_part_number(self, model_no):
        """
        Function to create triplets for the model number and its product type
        E.g. (Model:LRFDS3006*)-[TypeOf]-(Product:refrigerator)

        Args:
            model_no: The model number from the manual (current manual)

        Returns:
            Triplet for the model and its product type
        """
        # product_type: The generic product type E.g. refrigerator
        part_no = self.part_no
        product_type_key = cs.HAS_PART_NUMBER

        # create triplet for product type and model
        product_triplet = self._refer_schema_create_triplet(
            (model_no, product_type_key, part_no))

        return product_triplet

    def _make_triplets_internal(self, dict_object):
        """
        Internal function (Utility function) to make triplets will be called by make_triplets
        based on different sub sections
        Args:
            dict_object: dict, troubleshooting main content
        Returns:
            triplets: list
        """
        # Fetching Product type from dictionary object
        product_type = dict_object[cs.PRODUCT_TYPE]
        # Get the generic product names for population
        generic_product_name = cs.get_generic_product_name(product_type.lower())
        # Assign the generic_product_name to product_type if None
        if generic_product_name is not None:
            product_type = generic_product_name
        elif generic_product_name is None:
            logger.debug(f"Product Detail Not Found Please check{product_type}")
            raise ValueError("Product Detail Not Found Please check")

        # List of model numbers
        models_list = dict_object[cs.MODELS]
        # The troubleshooting list of data
        data_list = dict_object[cs.COMMON_INFO_KEY][cs.DATA][0]
        # Final Triplets list to be returned
        triplets_list = []

        # Get the updated Dictionary as per the new sub-sections of troubleshooting
        # TODO Handle the summary tag in a generic way
        # TODO - Handle Drier sections Steam Function & Indicator Messages TroubleshootingMappingRelation
        for sub_section, sub_section_content in data_list.items():
            for section, section_info in sub_section_content.items():
                if section == cs.XMLTags.SUMMARY_TAG:
                    continue
                triplets_list_temp = []
                self.ent_prd_type = self._get_ent_prd_type(sub_section, self.product_type)
                logger.debug("sub_section : %s",sub_section)
                if (sub_section == cs.BFR_CALL_FOR_SERVICE) or \
                        (sub_section.lower() in cs.GenericProductNameMapping.INT_SEC) or \
                        (sub_section == cs.WASH_DRY_CMN):
                    triplets_list_temp = self.__make_triplets_for_troubleshooting(models_list, section, section_info,
                                                                                  self.ent_prd_type)
                elif sub_section == cs.DIAGNOSING_FAULT:
                    triplets_list_temp = self.__make_triplets_for_diagnosing_a_fault(models_list, section, section_info)

                triplets_list = triplets_list + triplets_list_temp

        # create triplet for product type and model for each model
        for model in models_list:
            triplet = self.__make_triplet_for_producttype(model, product_type)
            part_number_triplet = self._make_triplet_for_part_number(model)
            triplets_list.append(triplet.__dict__)
            triplets_list.append(part_number_triplet)

        return triplets_list

    def _get_ent_prd_type(self, section, prd_type):
        """
        map the internal section title to entity product type if the section title is like washer,dryer,common
        else map based on the product type

        Args:
            section: internal section title
            prd_type:
        """
        section = section.lower()
        if (section in cs.GenericProductNameMapping.INT_SEC) or ((section == cs.DIAGNOSING_FAULT.lower())\
                 and self.sub_prd_type == cs.ExtractionConstants.KEPLER_PRD):
            for sec_key in cs.GenericProductNameMapping.SEC_TO_ENT_PRD_MAP.keys():
                if section == sec_key.lower():
                    return [ent_prd_type for ent_prd_type in cs.GenericProductNameMapping.SEC_TO_ENT_PRD_MAP[sec_key]]
        else:
            for prd in cs.GenericProductNameMapping.PRD_TO_ENT_PRD_MAP.keys():
                if prd_type.lower() in cs.GenericProductNameMapping.PRD_TO_ENT_PRD_MAP[prd]:
                    return [prd]


if __name__ == "__main__":
    # logger configuration
    logger.basicConfig(level=logger.INFO,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    obj = TroubleShooting()
    # New Testing New Formats
    new_dict = json.load(
        open(r"E:\TripletsCheck\trob\troubleshooting.json", encoding='utf-8'))
    triplets = obj.make_triplets(new_dict)
    print("In main triplets=", triplets)

    # To populate
    # from knowledge.database import DBInterface
    # db_obj = DBInterface()
    # db_obj.create_knowledge(triplets)
