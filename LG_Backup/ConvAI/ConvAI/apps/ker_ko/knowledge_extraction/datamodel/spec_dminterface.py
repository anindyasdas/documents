"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com
"""
import json
import logging as logger
import re

from .regex_utils import RegExUtils
from ..constants import params as cs
from . import dm_utils as utils


class Specification(object):
    """
    Data Modeling class for Specification section
    Defines the method to create dict object for entities and relationship
    """

    def __init__(self):
        # Create an object for handling RegEx Utility functions
        # Use for fetching the properties for range and relation
        self.regex_utils = RegExUtils()
        self.part_no = None

    def __get_common_key(self, speckey, keyvalue, key_dict):
        """
           finds the common key of given table key from given dictionary
           Args:
                speckey : string
                keyvalue : string
                key_dict : dictionary object
           Returns:
               commonkey:str
               norm_value : dict
        """
        key = ""
        if key_dict is None:
            return None, None
        if "(" in speckey or "*" in speckey:
            # extract main relation Ex in Dimensions (Width X Height X Depth)
            # To extract Battery Run Time from Battery Run Time*with the Nozzle
            key = re.split(r"[\(\*]", speckey)[0].strip()
        else:
            key = speckey
        for commonkey, value in key_dict.items():
            if key.lower() in str(value).lower():
                range_properties, relation_properties = self.regex_utils.get_range_relation_properties(speckey,
                                                                                                       keyvalue)
                return commonkey, range_properties, relation_properties

        return None, None, None

    def __refer_schema_create_triplet(self, domainvalue, generickey, rangevalue,
                                      range_properties, relation_properties=None):
        """
           refer the schema for given key and finds the node type of domain
           range nodes
           Args:
                domainvalue : str
                generickey : str
                rangevalue :str
                range_properties : dict
           Returns:
               domain : Node object
               relation:Relation object
               rangenode:Node object
        """
        domain_prop_dict = None
        range_prop_dict = None

        # refer schema for specified generic key
        schema_dict = utils.SCHEMA_OBJ.get_schema_for_key(generickey)
        logger.debug("generickey=%s", generickey)

        relation_name = schema_dict[cs.LABEL][0][cs.VALUE]

        # getting range node type based on defined schema
        domain_type = schema_dict[cs.DOMAIN][0][cs.ID]

        # getting range node type based on defined schema
        range_type = schema_dict[cs.RANGE][0][cs.ID]

        logger.debug("norm_values = %s, range_type = %s", range_properties, range_type)
        # TODO Check if this normalize_range_dictionary can be handled inside regex_utils.py
        range_prop_dict = self.regex_utils.normalize_range_dictionary(range_properties, range_type)

        logger.debug("domain type=%s rangetype=%s relation=%s" % (domain_type,
                                                                  range_type,
                                                                  relation_name))

        """
           NOTE:
           When same value but difference in case,create new data in database
           To avoid , convert to all lower case and store it.
           20 – 120 psi (138 – 827 kPA)
           20 - 120 psi (138 - 827 kPa)
        """
        rangevalue = rangevalue.strip().lower()
        if range_type.lower() in cs.DIMENSION.lower():
            if "\'" in rangevalue:
                rangevalue = rangevalue.replace("\'", "")
            if "\"" in rangevalue:
                rangevalue = rangevalue.replace("\"", "")

        # creating triplets
        # create  model node
        domain = utils.Node(domain_type, domainvalue, domain_prop_dict)

        # Adding part number
        # Add the part number property to all the relations except for HAS_PART_NUMBER
        if relation_name != cs.HAS_PART_NUMBER and relation_name != cs.REL_TYPE_OF:
            if relation_properties is not None:
                relation_properties[cs.PART_NUMBER_PROP] = self.part_no
            elif relation_properties is None:
                relation_properties = {cs.PART_NUMBER_PROP: self.part_no}
        elif relation_name == cs.HAS_PART_NUMBER:
            # Since we are converting to lower case ans stripping above we
            # want the original part number here
            rangevalue = self.part_no

        # create relation
        relation = utils.Relation(relation_name, relation_properties)

        # create end node
        rangenode = utils.Node(range_type, rangevalue, range_prop_dict)

        return domain, relation, rangenode

    def __make_triplets_foreachmodel(self, modelno, dict_object, triplets_list):
        """
            creates list of triplets(Node,Relation,Node)  for all the input key
            value pairs of input dict
            Args:
                modelno - str
                dict_object - dict
                triplets_list - list to store all triplets
            Returns:
                cs.SUCCESS - on success
                cs.BAD_REQUEST - on bad request data
        """
        try:
            logger.debug("modelno=%s dict_object=%s", modelno, str(dict_object))
            for key, value in dict_object.items():
                # the key is spec - key
                # value is spec - value
                key = key.strip()

                # if the spec-key is a list, use the first if the the length is 1
                if isinstance(value, list) and len(value) == 1:
                    value = value[0]
                    value = value.strip()

                    # Check the values if they contain any numbers (If not skip them)
                    # This Check only for Voltage Requirements
                    if not any(char.isdigit() for char in value) and any(
                            key.lower() in x.lower() for x in cs.TABLE_KEYS[cs.VOLTAGE_REQUIREMENTS]):
                        continue

                    # find generic key of given table key
                    # Get the range node and relationship properties
                    commonkey, range_properties, relation_properties = self.__get_common_key(key, value,
                                                                                             cs.TABLE_KEYS)

                    # commonkey : Relationship name as per RDF
                    # range_node_properties : dictionary of properties
                    logger.info("commonkey= %s , norm_value= %s", commonkey, range_properties)
                    # if new key found, should add as literals
                    # If the common key is None handle as HAS_SPECIFICATION
                    if commonkey is None:
                        logger.info("Particular key=(%s) is not found in \
                                              dictionary", key)
                        commonkey = cs.HAS_SPECIFICATION
                        relation_properties = {cs.RELATION_NAME: key}

                    # refer schema and generate triplet
                    domain, relation, rangenode = self.__refer_schema_create_triplet(
                        modelno, commonkey, value, range_properties, relation_properties)

                    # create each Node_Relation
                    eachtriplet = utils.NodeRelation(domain.__dict__,
                                                     relation.__dict__,
                                                     rangenode.__dict__)

                    logger.debug("Each triplet:" + str(eachtriplet.__dict__))
                    triplets_list.append(eachtriplet.__dict__)

                elif isinstance(value, list) and len(value) > 1:
                    # Code for handling multiple values like (Gas Requirements)
                    # Check the values if they contain any numbers (If not skip them)
                    self.__make_triplets_foreachmodel_for_value_list(key, modelno, triplets_list, value)

            return cs.SUCCESS
        except (KeyError, ValueError, AttributeError) as e:
            logger.error("Error in __make_triplets_foreachmodel" + str(e))
            return cs.BAD_REQUEST

    def __make_triplets_foreachmodel_for_value_list(self, key, modelno, triplets_list, value):
        """
        Create triplets for each model if the values are list
        Args:
            key: the specification key
            modelno: model number
            triplets_list: triplets (list) variable to which the triplets will be appended
            value: the specification value
        """
        for each_value in value:

            if not any(char.isdigit() for char in each_value) and any(
                    key.lower() in x.lower() for x in cs.TABLE_KEYS[cs.VOLTAGE_REQUIREMENTS]):
                continue

            # find generic key of given table key
            commonkey, range_properties, relation_properties = self.__get_common_key(key, each_value,
                                                                                     cs.TABLE_KEYS)

            # commonkey : Relationship name as per RDF
            # norm_value: dictionary of properties

            # if new key found,should add as literals
            if commonkey is None:
                logger.info("Particular key=(%s) is not found in \
                                                  dictionary", key)
                continue

            # Change the values for HAS_BATTERY_RUNTIME and HAS_POWER_CONSUMPTION
            # Remove unnecessary * and multiple spaces (Added during extraction)
            if commonkey == cs.HAS_BATTERY_RUNTIME or commonkey == cs.HAS_POWER_CONSUMPTION:
                each_value = each_value.replace("*", "").strip()
                each_value = re.sub(' +', ' ', each_value)

            # refer schema and generate triplet
            domain, relation, rangenode = self.__refer_schema_create_triplet(
                modelno, commonkey, each_value, range_properties, relation_properties)

            # create each Node_Relation
            eachtriplet = utils.NodeRelation(domain.__dict__,
                                             relation.__dict__,
                                             rangenode.__dict__)

            logger.debug("Each triplet:" + str(eachtriplet.__dict__))
            triplets_list.append(eachtriplet.__dict__)

            # If It is dimension populate only the first
            if commonkey == cs.DIMENSION:
                break

    def __make_triplet_for_producttype(self, modelno, product_type, triplets_list):
        """
            creates triplet(Node,Relation,Node)  for all the product type
            Args:
                modelno - str
                product_type - str
                triplets_list - list to store all triplets
            Returns:
                None
        """
        prodtype_key = "Product type"
        # create triplet for product type and model 
        commonkey, norm_value, relation_properties = self.__get_common_key(prodtype_key, product_type,
                                                                           cs.TABLE_KEYS)
        logger.info("prod_type common ley=(%s) norm_value=(%s)" % (commonkey,
                                                                   norm_value))
        # refer schema and generate triplet
        domain, relation, rangenode = self.__refer_schema_create_triplet(
            modelno, commonkey, product_type, norm_value)

        #  create each Node_Relation
        eachtriplet = utils.NodeRelation(domain.__dict__,
                                         relation.__dict__,
                                         rangenode.__dict__)

        logger.debug("Each triplet:" + str(eachtriplet.__dict__))
        triplets_list.append(eachtriplet.__dict__)

    def make_triplets(self, dict_object, product_type=None):
        """
            creates list of triplets(Node,Relation,Node) for list of input dict
            Args:
                dict_object - dict
                product_type - str
            Returns:
                list of Triplet objects
        """
        # Implementation as per the new JSON Format
        triplets_list = []
        try:
            if dict_object is None:
                return triplets_list
            elif dict_object[cs.ExtractionConstants.STATUS_STR] \
                    == cs.ExternalErrorCode.MKG_SECTION_NOT_AVAILABLE:
                logger.debug("Triplet dictionary has no Section\n")
                return None
            elif dict_object[cs.ExtractionConstants.STATUS_STR] == \
                    cs.ExternalErrorCode.MKG_FORMAT_NOT_SUPPORTED:
                logger.debug("Triplet dictionary format is not supported\n")
                return None
            elif dict_object[cs.ExtractionConstants.STATUS_STR] == \
                    cs.ExternalErrorCode.MKG_SUCCESS:
                logger.debug("Triplet dictionary format is supported\n")
                dict_object = dict_object[cs.ExtractionConstants.DATA_KEY]

            # This is a new temporary dictionary object which contains common_info and unique_info
            new_dict_object = None
            if cs.APPLIANCE in dict_object:
                new_dict_object = dict_object[cs.APPLIANCE]
                product_type = self._get_product_type(new_dict_object)
                self.part_no = dict_object[cs.APPLIANCE][cs.PARTNUMBER]
            if cs.DUMMY_SECTION_KEY in dict_object:
                new_dict_object = dict_object[cs.DUMMY_SECTION_KEY]
                product_type = self._get_product_type(new_dict_object)
                self.part_no = dict_object[cs.DUMMY_SECTION_KEY][cs.PARTNUMBER]

            self._create_triplets_for_common_info(new_dict_object, product_type, triplets_list)

            self._create_triplets_for_unique_info(new_dict_object, product_type, triplets_list)

            # if "Charger Adaptor" in dict_object:
            # TODO Handle the Charger Adaptor

            return triplets_list

        except (KeyError, ValueError, AttributeError) as e:
            logger.error("Error in make_triplets" + str(e))
            return None

    def _create_triplets_for_unique_info(self, unique_info_dict_object, product_type, triplets_list):
        """
        Create unique info triplets
        Args:
            unique_info_dict_object: Unique information from specification dictionary
            product_type: The generic type of the product
            triplets_list: the triplets variable to which the new triplets needs to be appended

        Returns: None
        """
        if unique_info_dict_object is not None and cs.UNIQUE_INFO_KEY in unique_info_dict_object:
            # Create a temp copy of the unique info for editing purposes
            temp_unique_info_data_list = unique_info_dict_object[cs.UNIQUE_INFO_KEY][cs.DATA_KEY]

            for each_unique_info_dict in temp_unique_info_data_list:
                model_no_list = each_unique_info_dict.pop(cs.MODELS)
                spec_key_values_dict = each_unique_info_dict
                # Create the spec_key_values triplets for each model in model_no_list
                for each_model in model_no_list:
                    response = self._make_all_triplets_for_each_model(each_model, product_type,
                                                                      spec_key_values_dict,
                                                                      triplets_list)
                    # if any key value ends with error, continue creating triplets
                    # for other key-value pairs
                    if response == cs.BAD_REQUEST:
                        logger.error("Error in this model input" + str(each_model))
                        continue

    def _create_triplets_for_common_info(self, common_info_dict_object, product_type, triplets_list):
        """
        Create Common info triplets
        Args:
            common_info_dict_object:  Common information from specification dictionary
            product_type: The generic type of the product
            triplets_list: the triplets variable to which the new triplets needs to be appended

        Returns: None

        """
        if common_info_dict_object is not None and cs.COMMON_INFO_KEY in common_info_dict_object:
            # Get the list of model numbers
            model_no_list = common_info_dict_object[cs.MODELS]
            spec_key_values_dict = common_info_dict_object[cs.COMMON_INFO_KEY][cs.DATA_KEY][0]

            # Create the spec_key_values triplets for each model in model_no_list
            for each_model in model_no_list:
                response = self._make_all_triplets_for_each_model(each_model, product_type, spec_key_values_dict,
                                                                  triplets_list)
                # if any key value ends with error, continue creating triplets
                # for other key-value pairs
                if response == cs.BAD_REQUEST:
                    logger.error("Error in this model input" + str(each_model))
                    continue

    def _make_all_triplets_for_each_model(self, each_model, product_type, spec_key_values_dict, triplets_list):

        logger.debug("Model=%s dict_value=%s", each_model, str(spec_key_values_dict))
        ret = self.__make_triplets_foreachmodel(each_model, spec_key_values_dict,
                                                triplets_list)
        # create product type and model triplet
        self.__make_triplet_for_producttype(each_model, product_type,
                                            triplets_list)

        self._make_triplet_for_part_number(each_model, triplets_list)

        return ret

    def _make_triplet_for_part_number(self, model_no, triplets_list):
        """
        Function to create triplets for the model number and its part number type
        E.g. (Model:LRFDS3006*)-[HAS_PART_NUMBER]->(PartNumber:<Some Part Number>)

        Args:
            model_no: The model number from the manual (current manual)
            triplets_list: triplets_list to be appended the new triplets
        """

        part_no = self.part_no
        product_type_key = cs.HAS_PART_NUMBER

        # create triplet for product type and model
        domain, relation, rangenode = self.__refer_schema_create_triplet(
            model_no, product_type_key, part_no, range_properties=None, relation_properties=None)

        #  create each Node_Relation
        eachtriplet = utils.NodeRelation(domain.__dict__,
                                         relation.__dict__,
                                         rangenode.__dict__)

        logger.debug("Each part number triplet:" + str(eachtriplet.__dict__))

        triplets_list.append(eachtriplet.__dict__)

    def _get_product_type(self, new_dict_object):
        # Fetching Product type from dictionary object
        product_type = new_dict_object[cs.PRODUCT_TYPE]
        # Convert the product_type to lower case
        product_type = product_type.lower()
        # Get the generic product names for population
        generic_product_name = cs.get_generic_product_name(product_type)
        # Assign the generic_product_name to product_type if None
        if generic_product_name is not None:
            product_type = generic_product_name
        return product_type


if __name__ == "__main__":
    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    obj = Specification()
    main_dict = dict()

    main_dict = json.load(
        open(r"E:\TripletsCheck\spec\washing_machine_test.json"))

    triplets = obj.make_triplets(main_dict)

    print("In main triplets=", triplets)
