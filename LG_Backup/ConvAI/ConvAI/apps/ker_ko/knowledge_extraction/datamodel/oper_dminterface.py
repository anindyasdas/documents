"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: purnanaga.nalluri@lge.com
"""
import logging as logger
import re
from . import dm_utils as utils
from . import image_handling_interface as im_interface
from ..constants import params as cs


class Operation(object):
    """
    Data Modeling class for Operation section
    Defines the methods to create dict object for entities and relationship
    """

    def __init__(self):
        # These variables are shared across all the functions
        self.product_type = ""
        self.main_section = cs.XMLTags.OPERATION_TAG
        self.model_no_list = []
        self.sub_section = ""
        self.part_no = ""
        self.ent_prd_type = None
        # For handling images
        self.image_interface = im_interface.ImageHandlingInterface()

    def make_triplets(self, operation_section_dictionary):
        """
        Main method to create triplets for operation section

        Args:
            operation_section_dictionary: Extracted information in JSON/Dictionary format from Doc Extraction module

        Returns:
            List of triplets created from operation section
        """

        logger.debug("Inside the make triplets with the input : {}".format(operation_section_dictionary))
        triplets_list = []
        try:

            # To handle the status of extraction
            if operation_section_dictionary is None:
                logger.debug("Triplet dictionary is None\n")
                return None
            elif operation_section_dictionary[cs.ExtractionConstants.STATUS_STR] \
                    == cs.ExternalErrorCode.MKG_SECTION_NOT_AVAILABLE:
                logger.debug("Triplet dictionary has no Section\n")
                return None
            elif operation_section_dictionary[
                cs.ExtractionConstants.STATUS_STR] == cs.ExternalErrorCode.MKG_FORMAT_NOT_SUPPORTED:
                logger.debug("Triplet dictionary format is not supported\n")
                return None
            elif operation_section_dictionary[cs.ExtractionConstants.STATUS_STR] == cs.ExternalErrorCode.MKG_SUCCESS:
                logger.debug("Triplet dictionary format is supported\n")
                operation_section_dictionary = operation_section_dictionary[cs.ExtractionConstants.DATA_KEY]

            # Getting the product type
            self.product_type = self._get_product_type(operation_section_dictionary)

            # Get the part number
            self.part_no = operation_section_dictionary[cs.PARTNUMBER]
            # Get the model No List
            model_no_list = operation_section_dictionary[cs.MODELS]
            self.model_no_list = model_no_list

            # Get the individual sections dictionary to give to make triplets internal function

            # Loop through all the available sections
            for each_section in operation_section_dictionary[cs.COMMON_INFO_KEY][cs.DATA_KEY]:
                ent_prd_type_from_xml = each_section[cs.ENTITY_PRD_TYPE]
                self.ent_prd_type = ent_prd_type_from_xml
                sections_dictionary = each_section[cs.ExtractionConstants.OPERATION_KEY]

                # Call the internal make triplets function to create triplets for sub-sections
                triplets_list_temp = self._make_triplets_internal(model_no_list, sections_dictionary)
                triplets_list = triplets_list + triplets_list_temp

            # Create the triplets for Model and its type
            # create triplet for product type and model for each model and part number
            for model in model_no_list:
                product_type_triplet = self._make_triplet_for_product_type(model)
                logger.debug("Each model triplet from operation:" + str(product_type_triplet))
                triplets_list.append(product_type_triplet)

                part_number_triplet = self._make_triplet_for_part_number(model)
                logger.debug("Each part number triplet from operation:" + str(part_number_triplet))
                triplets_list.append(part_number_triplet)
        except Exception as e:
            logger.exception("Operation : Error in make_triplets " + str(e))

        logger.debug("Inside make triplets : output : {}".format(str(triplets_list)))

        return triplets_list

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
        # Convert the product_type to lower case
        product_type = product_type.lower()
        # Get the generic product names for population
        generic_product_name = cs.get_generic_product_name(product_type)
        # Assign the generic_product_name to product_type if None
        if generic_product_name is not None:
            product_type = generic_product_name

        logger.debug("Operation : get_product_type : output : {}".format(str(product_type)))

        return product_type

    def _get_ent_prd_type(self, section, prd_type):
        """
        Map the internal section title to generic entity product type or map based on product type

        Args:
            section: internal section title like(washer, dryer etc.,)
            prd_type: product type from manual
        Return:
             Entity prd type
        """
        section = section.lower()
        if (section in cs.GenericProductNameMapping.INTERNAL_SEC) and \
                (section in cs.GenericProductNameMapping.INT_SEC_MAP.keys()):
            return section
        else:
            for prd in cs.GenericProductNameMapping.INT_SEC_MAP.keys():
                if prd_type in cs.GenericProductNameMapping.INT_SEC_MAP[prd]:
                    return prd

    def _create_operation_triplets(self, operation_domain, operation_relation, operation_range,
                                   operation_range_info,
                                   operation_domain_props=None):
        """
        Function to create triplets for operation sections and its sub-sections
        Ex: (Model)-[:HAS_OPERATION_SECTION]->(OperationSection)
        (OperationSection)-[:HAS_SUB_SECTION]->(OperationSection)
        Args:
            operation_domain: The domain node for the Operation Section / Sub-Sections
            operation_relation: For Operation it is HAS_OPERATION_SECTION / HAS_SUB_SECTION
            operation_range: The end node or the left node
            operation_range_info: Information about the operation_range, if it has more info this same function is called recursively
            operation_domain_props: The properties for Domain

        Returns:
            list of triplets for Operations Sections and sub sections
        """
        triplets_list_local = []
        # This is used as a sub-section info while creating path to the images
        self.sub_section = operation_range

        domain_type_for_current_sub_section = None
        domain_type_for_current_sub_section = self._get_range_type_for_generic_key(
            operation_relation)

        # Check for the Range makers in operation_range like Desc and Description points to make desc
        range_desc = self._get_description_for_sections(operation_range_info)

        # Property to hold range properties
        range_props_local = {}

        # Handling Summary Tags
        range_props_local, triplets_list_local = self._create_triplets_for_summary_section(
            domain_type_for_current_sub_section, operation_range, operation_range_info, range_desc, range_props_local,
            triplets_list_local)

        # Remove all the used tags as above
        operation_range_info_copy = operation_range_info.copy()
        operation_range_info_copy.pop(cs.DESCRIPTION_POINTS, None)
        operation_range_info_copy.pop(cs.DESCRIPTION, None)
        operation_range_info_copy.pop(cs.XMLTags.SUMMARY_TAG, None)

        # The domain type for procedure relation will be the range type of the generic key
        for each_sub_section, each_sub_section_info in operation_range_info_copy.items():
            each_sub_section = re.sub(r"\s\s+", ' ', each_sub_section)
            rdf_relation_mapping_key = cs.get_operation_mapping_key_relation(each_sub_section)

            triplets_list_local = self.__get_local_triplet_list(domain_type_for_current_sub_section,
                                                                [each_sub_section, each_sub_section_info],
                                                                operation_range,
                                                                range_props_local, rdf_relation_mapping_key,
                                                                triplets_list_local)
        # Finally Call this Function to create triplets
        domain_relation_range = (operation_domain, operation_relation, operation_range)
        # Get the Domain type for HAS_SUB_SECTION relation
        temp_domain_type = None
        if operation_domain == self.current_operation_section and operation_relation == cs.HAS_SUB_SECTION:
            temp_domain_type = cs.OPERATION_SECTION_NODE
        elif operation_domain != self.current_operation_section and operation_relation == cs.HAS_SUB_SECTION:
            temp_domain_type = cs.OPERATION_SUB_SECTION_NODE

        local_temp_triplet = self._refer_schema_create_triplet(domain_relation_range,
                                                               domain_props=operation_domain_props,
                                                               range_props=range_props_local,
                                                               domain_type=temp_domain_type)

        triplets_list_local.append(local_temp_triplet)

        return triplets_list_local

    def __get_local_triplet_list(self, domain_type_for_current_sub_section, each_sub_section_info_list,
                                 operation_range, range_props_local, rdf_relation_mapping_key, triplets_list_local):
        """
        creates a local list of triplets based on subcategory and relation
        Args:
            domain_type_for_current_sub_section: domain type of the sub section
            each_sub_section: chosen sub section
            each_sub_section_info:chosen sub section information
            operation_range: range of the section
            range_props_local:
            rdf_relation_mapping_key: relation identified
            triplets_list_local: list of triplets identified

        Returns:
                list of triplets
        """
        each_sub_section, each_sub_section_info = each_sub_section_info_list[0], each_sub_section_info_list[1]
        if rdf_relation_mapping_key == cs.HAS_PROCEDURE:
            procedure_steps_list = each_sub_section_info
            procedure_triplets = self._create_triplets_for_procedure(procedure_domain=operation_range,
                                                                     procedure_steps=procedure_steps_list,
                                                                     procedure_domain_props=range_props_local,
                                                                     procedure_domain_type=domain_type_for_current_sub_section)

            # Add the procedure triplets to the usage triplets
            triplets_list_local = triplets_list_local + procedure_triplets
        elif rdf_relation_mapping_key == cs.HAS_NOTE:
            note_steps_list = each_sub_section_info
            note_triplets = self._create_triplets_for_note(note_domain=operation_range,
                                                           note_steps=note_steps_list,
                                                           note_domain_props=range_props_local,
                                                           note_domain_type=domain_type_for_current_sub_section)

            # Add the note triplets to the usage triplets
            triplets_list_local = triplets_list_local + note_triplets
        elif rdf_relation_mapping_key == cs.HAS_CAUTION:
            caution_steps_list = each_sub_section_info
            caution_triplets = self._create_triplets_for_caution(caution_domain=operation_range,
                                                                 caution_steps=caution_steps_list,
                                                                 caution_domain_props=range_props_local,
                                                                 caution_domain_type=domain_type_for_current_sub_section)
            # Add the caution triplets to the usage triplets
            triplets_list_local = triplets_list_local + caution_triplets
        elif rdf_relation_mapping_key == cs.HAS_WARNING:
            warning_steps_list = each_sub_section_info
            warning_triplets = self._create_triplets_for_warning(warning_domain=operation_range,
                                                                 warning_steps=warning_steps_list,
                                                                 warning_domain_props=range_props_local,
                                                                 warning_domain_type=domain_type_for_current_sub_section)
            # Add the warning triplets to the usage triplets
            triplets_list_local = triplets_list_local + warning_triplets
        elif rdf_relation_mapping_key == cs.HAS_IMAGE:
            image_content = each_sub_section_info
            image_triplets = self._create_triplets_for_image(image_domain=operation_range,
                                                             image_content=image_content,
                                                             image_domain_props=range_props_local,
                                                             image_domain_type=domain_type_for_current_sub_section,
                                                             image_sub_section=self.sub_section)
            # Add the caution triplets to the usage triplets
            triplets_list_local = triplets_list_local + image_triplets
        elif rdf_relation_mapping_key == cs.HAS_FEATURE:
            features_list = each_sub_section_info
            features_triplets = self._create_triplets_for_features(features_domain=operation_range,
                                                                   features_list=features_list,
                                                                   features_domain_props=range_props_local,
                                                                   features_domain_type=domain_type_for_current_sub_section)
            # Add the caution triplets to the usage triplets
            triplets_list_local = triplets_list_local + features_triplets
        elif each_sub_section == cs.TABLE_DETAILS:
            table_details_list = each_sub_section_info
            table_details_triplets = self._create_triplets_for_tabular_data(table_domain=operation_range,
                                                                            table_list=table_details_list,
                                                                            table_domain_props=range_props_local,
                                                                            table_domain_type=domain_type_for_current_sub_section)
            triplets_list_local = triplets_list_local + table_details_triplets
        else:
            sub_sec_triplets = self._create_operation_triplets(operation_domain=operation_range,
                                                               operation_relation=cs.HAS_SUB_SECTION,
                                                               operation_range=each_sub_section,
                                                               operation_range_info=each_sub_section_info,
                                                               operation_domain_props=range_props_local)
            triplets_list_local = triplets_list_local + sub_sec_triplets
        return triplets_list_local

    def _create_triplets_for_summary_section(self, domain_type_for_current_sub_section, operation_range,
                                             operation_range_info, range_desc, range_props_local, triplets_list_local):
        """
        Create triplets for summary section under Operation Sections
        """
        if cs.XMLTags.SUMMARY_TAG in operation_range_info:
            desc_in_summary = self._get_description_for_sections(operation_range_info[cs.XMLTags.SUMMARY_TAG])
            if range_desc is None or len(range_desc) == 0:
                range_desc = desc_in_summary
            else:
                range_desc += "\n" + desc_in_summary

            if cs.XMLTags.PREREQUISITES_TAG in operation_range_info[cs.XMLTags.SUMMARY_TAG]:
                triplets_list_local = self._create_triplets_for_prerequisites_section(
                    domain_type_for_current_sub_section, operation_range, operation_range_info, range_props_local,
                    triplets_list_local)

        # Update the Range Properties with descriptions
        if range_desc is not None:
            range_props_local[cs.DESC_KEY] = range_desc

        return range_props_local, triplets_list_local

    def _create_triplets_for_prerequisites_section(self, domain_type_for_current_sub_section, operation_range,
                                                   operation_range_info, range_props_local, triplets_list_local):
        """
        Create triplets for prerequisites section under summary Sections
        """
        if cs.NOTE in operation_range_info[cs.XMLTags.SUMMARY_TAG][cs.XMLTags.PREREQUISITES_TAG]:
            note_steps_list = operation_range_info[cs.XMLTags.SUMMARY_TAG][cs.XMLTags.PREREQUISITES_TAG][
                cs.NOTE]
            note_triplets = self._create_triplets_for_note(note_domain=operation_range,
                                                           note_steps=note_steps_list,
                                                           note_domain_props=range_props_local,
                                                           note_domain_type=domain_type_for_current_sub_section)

            # Add the note triplets to the usage triplets
            triplets_list_local = triplets_list_local + note_triplets
        if cs.CAUTION in operation_range_info[cs.XMLTags.SUMMARY_TAG][cs.XMLTags.PREREQUISITES_TAG]:
            caution_steps_list = operation_range_info[cs.XMLTags.SUMMARY_TAG][cs.XMLTags.PREREQUISITES_TAG][
                cs.CAUTION]
            caution_triplets = self._create_triplets_for_caution(caution_domain=operation_range,
                                                                 caution_steps=caution_steps_list,
                                                                 caution_domain_props=range_props_local,
                                                                 caution_domain_type=domain_type_for_current_sub_section)
            # Add the caution triplets to the usage triplets
            triplets_list_local = triplets_list_local + caution_triplets
        if cs.XMLTags.WARNING_TAG in operation_range_info[cs.XMLTags.SUMMARY_TAG][cs.XMLTags.PREREQUISITES_TAG]:
            warning_steps_list = operation_range_info[cs.XMLTags.SUMMARY_TAG][cs.XMLTags.PREREQUISITES_TAG][
                cs.XMLTags.WARNING_TAG]
            warning_triplets = self._create_triplets_for_warning(warning_domain=operation_range,
                                                                 warning_steps=warning_steps_list,
                                                                 warning_domain_props=range_props_local,
                                                                 warning_domain_type=domain_type_for_current_sub_section)
            # Add the warning triplets to the usage triplets
            triplets_list_local = triplets_list_local + warning_triplets
        return triplets_list_local

    def _get_description_for_sections(self, section_info):
        """
        Utility function to combine the descriptions list into a single description
        """
        desc_temp = ""
        if cs.DESCRIPTION in section_info:
            if len(section_info[cs.DESCRIPTION]) == 1:
                desc_str = section_info[cs.DESCRIPTION][0]
            else:
                desc_str = ". ".join([x.strip(".") for x in section_info[cs.DESCRIPTION]])
            desc_temp += desc_str.strip(".")+"."

        if cs.DESCRIPTION_POINTS in section_info:
            desc_temp = self._handle_description_point(desc_temp, section_info)
        if desc_temp is not None and len(desc_temp) > 0:
            desc_temp = desc_temp.strip()
        return desc_temp

    def _handle_description_point(self, desc_temp, section_info):
        """
        handling the description point inside the section

        Args:
            desc_temp: previously framed description string
            section_info: description point dictionary
        Return:
            desc_temp: framed string from description point
        """
        for each_desc_points in section_info[cs.DESCRIPTION_POINTS]:
            for key, value in each_desc_points.items():
                if key == cs.DESCRIPTION:
                    desc_str = ". ".join(
                        [x if len(each_desc_points[cs.DESCRIPTION]) == 1 else x.strip(".") for x in each_desc_points[cs.DESCRIPTION]])
                    desc_temp += desc_str.strip(".") + "."
                elif key == cs.DESCRIPTION_POINTS:
                    desc_temp += self._get_description_for_sections({key: value})
                elif key == cs.ExtractionConstants.FIGURE:  # handling the image under the description points
                    desc_temp = self._get_image_info_under_desc(desc_temp, value)
        return desc_temp

    def _get_image_info_under_desc(self, desc_temp, image_info):
        """
        frame the image information from the extracted json inside the description point

        Args:
            desc_temp: description string framed previously
            image_info: image details extracted under the figure tag

        Return:
            description details with image detail added
        """
        # framing the file path based section,sub_section,partnumber information
        image_response = self.image_interface.get_image_information(self.product_type,
                                                                    self.main_section,
                                                                    self.sub_section,
                                                                    self.part_no, image_info)
        if image_response[cs.resp_code] == cs.ResponseCode.SUCCESS:
            # merging the image detail with the text in a description
            desc_temp += "<img>{\\\"img_path\\\": \\\"" \
                         + image_response[cs.resp_data][cs.IMAGE_CONTENT][cs.ExtractionConstants.FILE_PATH] \
                         + "\\\", \\\"file_size\\\":" + str(image_info["size"]) \
                         + ",\\\"type\\\": \\\"" + image_info["file_type"] + "\\\"}</img>"
        return desc_temp

    def _get_image_content_under_desc(self, section_info):
        """
        Get the image info under sections
        """
        image_content = None
        if cs.DESCRIPTION_POINTS in section_info:
            for each_desc_point in section_info[cs.DESCRIPTION_POINTS]:
                if cs.XMLTags.FIGURE_TAG in each_desc_point:
                    return each_desc_point[cs.XMLTags.FIGURE_TAG]
        return image_content

    def _make_triplets_internal(self, model_no_list, sections_dictionary):
        """
        Internal function called by make_triplets to create triplets individually for all the sections

        Args:
            model_no_list: list of model numbers for which the operation sections content is common
            sections_dictionary: operation sections content

        Returns:
            list of consolidated triplets from different operation sections passed to this function
        """
        triplets_list_local = []

        logger.debug(
            "Operation : inside _make_triplets_internal with model_no : {} and sec_dict {}".format(str(model_no_list),
                                                                                                   str(
                                                                                                       sections_dictionary)))

        # Loop through the section_dictionary

        # Call a function with the generic relation
        for each_model in model_no_list:
            for each_section, each_section_info in sections_dictionary.items():
                # This variable is used for distinguishing the Domain type for HAS_SUB_SECTION relation
                self.current_operation_section = each_section
                triplets_list_temp = self._create_operation_triplets(operation_domain=each_model,
                                                                     operation_relation=cs.HAS_OPERATION_SECTION,
                                                                     operation_range=each_section,
                                                                     operation_range_info=each_section_info)
                triplets_list_local = triplets_list_local + triplets_list_temp
        return triplets_list_local

    def _get_description_for_entry(self, info_to_get_desc):
        """
        Utility function to get the information under the entry node in extracted JSON
        """
        desc_under_entry = ""

        for each_sub_entry in info_to_get_desc[cs.ENTRY]:
            desc_under_entry += each_sub_entry[cs.STEP] + "\n"
            desc_under_entry += each_sub_entry[cs.CHECKS]

        return desc_under_entry


    def _get_table_details_under_procedure(self, table_details):
        """
        get the table details under the step in procedure

        Args:
            table_details: dict of table details under the procedure step

        Return:
            string famed from table details
        """
        row_str = ""
        for table_detail in table_details:
            for row_detail in table_detail[cs.ENTRIES]:
                for key, value in row_detail.items():
                    row_str += key + ":" +self._get_description_for_sections(value)+","
                row_str = row_str.rstrip(",")
                row_str += "\n"

        return row_str


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
            range_desc = ""
            range_desc = self._get_description_for_sections(every_step)
            # If there is 'entry' node (Get description from entry node)
            if cs.ENTRY in every_step:
                range_desc += self._get_description_for_entry(every_step)
            procedure_range_props[cs.DESC_KEY] = range_desc

            if cs.TABLE_DETAILS in every_step:
                logger.debug("table details : %s",every_step[cs.TABLE_DETAILS])
                procedure_range_props[cs.DESC_KEY] += self._get_table_details_under_procedure(every_step[cs.TABLE_DETAILS])

            procedure_step_triplet = self._refer_schema_create_triplet((procedure_domain, procedure_generic_key,
                                                                        every_step[cs.STEP]),
                                                                       range_props=procedure_range_props,
                                                                       domain_props=procedure_domain_props,
                                                                       domain_type=procedure_domain_type)

            triplets_list_local.append(procedure_step_triplet)
            images_under_procedure_steps = []
            if cs.ExtractionConstants.FIGURE in every_step:
                images_under_procedure_steps.append(every_step[cs.ExtractionConstants.FIGURE])

            # To Handle Images
            for every_image_content in images_under_procedure_steps:
                image_content = every_image_content
                image_triplets = self._create_triplets_for_image(image_domain=every_step[cs.STEP],
                                                                 image_content=image_content,
                                                                 image_domain_props=procedure_range_props,
                                                                 image_domain_type=cs.PROCEDURE_NODE,
                                                                 image_sub_section=self.sub_section)
                # Add the caution triplets to the usage triplets
                triplets_list_local = triplets_list_local + image_triplets

            # Handle Notes
            # The domain type for note will be the range type of the generic key
            if cs.NOTE in every_step:
                note_steps_list = every_step[cs.NOTE]
                note_triplets = self._create_triplets_for_note(note_domain=every_step[cs.STEP],
                                                               note_steps=note_steps_list,
                                                               note_domain_props=procedure_range_props,
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

    def _make_triplet_for_product_type(self, model_no):
        """
        Function to create triplets for the model number and its product type
        E.g. (Model:LRFDS3006*)-[TypeOf]-(Product:refrigerator)

        Args:
            model_no: The model number from the manual (current manual)

        Returns:
            Triplet for the model and its product type
        """
        # product_type: The generic product type E.g. refrigerator
        product_type = self.product_type
        product_type_key = cs.PRODUCT

        # create triplet for product type and model
        product_triplet = self._refer_schema_create_triplet(
            (model_no, product_type_key, product_type))

        return product_triplet

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

            # Add the part number property to all the relations except for HAS_PART_NUMBER & REL_TYPE_OF
            if relation_name != cs.HAS_PART_NUMBER and relation_name != cs.REL_TYPE_OF:
                if relation_props is not None:
                    relation_props[cs.PART_NUMBER_PROP] = self.part_no
                elif relation_props is None:
                    relation_props = {cs.PART_NUMBER_PROP: self.part_no}
                # Add the ent_prd_type property for Washer or Dryer types
                relation_props[cs.ENTITY_PRD_TYPE] = self.ent_prd_type

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
            caution_desc = self._get_description_for_sections(every_caution)
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

    def _create_triplets_for_note(self, note_domain, note_steps, note_domain_props, note_domain_type):
        """
        Function to create triplets for notes
        Args:
            note_domain: Domain node for note
            note_steps: The list of Notes
            note_domain_props: The domain properties if any for note relation
            note_domain_type: The domain type for this note relation as note supports multiple domain types
            as per RDF

        Returns:
            List of note triplets for corresponding domain
        """
        triplets_list_local = []

        note_generic_key = cs.HAS_NOTE
        # Note will have 'Description points' i.e., list of 'Description' which can have 'figure' also
        for each_note_step in note_steps:
            actual_note_info = each_note_step[cs.DESCRIPTION_POINTS]
            for every_note in actual_note_info:
                note_desc = self._get_description_for_sections(every_note)
                note_step_triplet = self._refer_schema_create_triplet((note_domain, note_generic_key, note_desc),
                                                                      domain_props=note_domain_props,
                                                                      domain_type=note_domain_type)

                triplets_list_local.append(note_step_triplet)

                # If the note contains image
                if cs.ExtractionConstants.FIGURE in every_note:
                    image_content = every_note[cs.ExtractionConstants.FIGURE]
                    note_img_triplet = self._create_triplets_for_image(note_desc, image_content, None, cs.VALUE_NODE,
                                                                       self.sub_section)

                    triplets_list_local = triplets_list_local + note_img_triplet

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
            warning_desc = self._get_description_for_sections(every_warning)
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

    def _create_triplets_for_features(self, features_domain, features_list, features_domain_props,
                                      features_domain_type):
        triplets_list_local = []
        feature_generic_key = cs.HAS_FEATURE
        feature_range_props = None
        for every_feature in features_list:
            feature_desc = ""
            if cs.EXPLANATION in every_feature:
                for every_explanation in every_feature[cs.EXPLANATION]:
                    temp_desc_full = self._get_description_for_sections(every_explanation)
                    if temp_desc_full is not None:
                        feature_desc += temp_desc_full
                feature_range_props = {cs.DESC_KEY: feature_desc}
            feature_step_triplet = self._refer_schema_create_triplet(
                (features_domain, feature_generic_key, every_feature[cs.FEATURE]),
                domain_props=features_domain_props,
                domain_type=features_domain_type, range_props=feature_range_props)

            triplets_list_local.append(feature_step_triplet)
            # Handle Notes
            # The domain type for note will be the range type of the generic key
            triplets_list_local = self.__handle_extra_info(every_feature, feature_range_props, triplets_list_local)
        return triplets_list_local

    def __handle_extra_info(self, every_feature, feature_range_props, triplets_list_local):
        """
        function to handle extra information

        Args:
            every_feature: explaination in a feature list
            feature_range_props: dictionary of features
            triplets_list_local: list of triplets already made in direct info

        Returns:
            return triplets with extra info triplets attached
        """
        if cs.NOTE in every_feature:
            note_steps_list = every_feature[cs.NOTE]
            note_triplets = self._create_triplets_for_note(note_domain=every_feature[cs.FEATURE],
                                                           note_steps=note_steps_list,
                                                           note_domain_props=feature_range_props,
                                                           note_domain_type=cs.FEATURE_NODE)

            # Add the caution triplets to the usage triplets
            triplets_list_local = triplets_list_local + note_triplets
        if cs.CAUTION in every_feature:
            caution_steps_list = every_feature[cs.CAUTION]
            caution_triplets = self._create_triplets_for_caution(caution_domain=every_feature[cs.STEP],
                                                                 caution_steps=caution_steps_list,
                                                                 caution_domain_props=feature_range_props,
                                                                 caution_domain_type=cs.FEATURE_NODE)
            # Add the caution triplets to the usage triplets
            triplets_list_local = triplets_list_local + caution_triplets
        if cs.XMLTags.WARNING_TAG in every_feature:
            warning_steps_list = every_feature[cs.XMLTags.WARNING_TAG]
            warning_triplets = self._create_triplets_for_warning(warning_domain=every_feature[cs.STEP],
                                                                 warning_steps=warning_steps_list,
                                                                 warning_domain_props=feature_range_props,
                                                                 warning_domain_type=cs.FEATURE_NODE)
            # Add the caution triplets to the usage triplets
            triplets_list_local = triplets_list_local + warning_triplets
        return triplets_list_local

    def _create_triplets_for_extra_info(self, extra_info_data, extra_info_domain, extra_info_domain_props,
                                        extra_info_domain_type):
        """
        Create triplets for extra info like Note, Caution and Warning
        """
        extra_info_triplet_list = []
        # if cs.CAUTION in
        if cs.NOTE in extra_info_data:
            note_steps_list = extra_info_data[cs.NOTE]
            note_triplets = self._create_triplets_for_note(note_domain=extra_info_domain,
                                                           note_steps=note_steps_list,
                                                           note_domain_props=extra_info_domain_props,
                                                           note_domain_type=extra_info_domain_type)

            # Add the caution triplets to the usage triplets
            extra_info_triplet_list = extra_info_triplet_list + note_triplets

        if cs.CAUTION in extra_info_data:
            caution_steps_list = extra_info_data[cs.CAUTION]
            caution_triplets = self._create_triplets_for_caution(caution_domain=extra_info_domain,
                                                                 caution_steps=caution_steps_list,
                                                                 caution_domain_props=extra_info_domain_props,
                                                                 caution_domain_type=extra_info_domain_type)
            # Add the caution triplets to the usage triplets
            extra_info_triplet_list = extra_info_triplet_list + caution_triplets

        if cs.XMLTags.WARNING_TAG in extra_info_data:
            warning_steps_list = extra_info_data[cs.XMLTags.WARNING_TAG]
            warning_triplets = self._create_triplets_for_warning(warning_domain=extra_info_domain,
                                                                 warning_steps=warning_steps_list,
                                                                 warning_domain_props=extra_info_domain_props,
                                                                 warning_domain_type=extra_info_domain_type)
            # Add the caution triplets to the usage triplets
            extra_info_triplet_list = extra_info_triplet_list + warning_triplets

        return extra_info_triplet_list

    def _create_triplets_for_checklist(self, checklist_data, checklist_domain, checklist_domain_props,
                                       checklist_domain_type):
        """
        Create triplets for checklist
        """
        triplets_list_local = []
        # This for loop runs only once for checklist
        for each_entry in checklist_data[cs.ENTRY]:
            entry_node_name = each_entry[cs.STEP]
            entry_node_desc = " ".join(each_entry[cs.CHECKS])
            entry_node_range_props = {cs.DESC_KEY: entry_node_desc}
            entry_triplet = self._refer_schema_create_triplet(
                (checklist_domain, cs.HAS_SUB_SECTION, entry_node_name), domain_props=checklist_domain_props,
                range_props=entry_node_range_props, domain_type=checklist_domain_type)
            triplets_list_local.append(entry_triplet)

            if any([x in [cs.NOTE,cs.CAUTION,cs.XMLTags.WARNING_TAG] for x in each_entry.keys()]):
                extra_info_triplets = self._create_triplets_for_extra_info(extra_info_data=each_entry,
                                                                           extra_info_domain=entry_node_name,
                                                                           extra_info_domain_props=entry_node_range_props,
                                                                           extra_info_domain_type=cs.OPERATION_SUB_SECTION_NODE)
                triplets_list_local.extend(extra_info_triplets)
            # For Handling images
            if cs.ExtractionConstants.FIGURE in checklist_data:
                image_content = checklist_data[cs.ExtractionConstants.FIGURE]
                # here the subsection will the table_domain i.e.,
                # the Operation Sub Section from where it is coming
                image_triplets = self._create_triplets_for_image(image_domain=entry_node_name,
                                                                 image_content=image_content,
                                                                 image_domain_props=entry_node_range_props,
                                                                 image_domain_type=cs.OPERATION_SUB_SECTION_NODE,
                                                                 image_sub_section=self.sub_section)
                # Add the caution triplets to the usage triplets
                triplets_list_local.extend(image_triplets)
        return triplets_list_local

    def _create_triplets_for_tabular_data(self, table_domain, table_list, table_domain_props, table_domain_type):
        """
        Create triplets for tabular data
        """

        triplets_list_local = []
        for every_table_entry in table_list:
            # 'every_table_entry' is a dictionary of only one key 'entries' as per JSON Format
            for each_row_entry in every_table_entry[cs.ENTRIES]:
                # This is a condition to check if it is a Checklist
                # Check for 'entry' in each_row_entry, if true this means it is a kind of checklist
                if any([x == cs.ENTRY for x in each_row_entry.keys()]):
                    checklist_triplets_list = self._create_triplets_for_checklist(checklist_data=each_row_entry,
                                                                           checklist_domain=table_domain,
                                                                           checklist_domain_type=table_domain_type,
                                                                           checklist_domain_props=table_domain_props)
                    triplets_list_local.extend(checklist_triplets_list)
                else:
                    # TODO Handle images in Tables
                    if cs.ExtractionConstants.FIGURE in str(each_row_entry):
                        continue

                    table_cell_triplets = self._create_triplets_for_table_rows(each_row_entry, table_domain,
                                                                               table_domain_props, table_domain_type)

                    triplets_list_local.append(table_cell_triplets)
        return triplets_list_local

    def _create_triplets_for_table_rows(self, each_row_entry, table_domain, table_domain_props, table_domain_type):
        """
        Create Triplets for Table Rows
        """
        # This is a flag to use the first cell as name
        # the other cells as description
        flag_to_use_first_value_as_name = 0
        desc_for_sub_section_list = []
        name_for_section = ""
        for each_cell in each_row_entry:
            flag_to_use_first_value_as_name += 1
            cell_info = each_row_entry[each_cell]
            # Get the Cell description
            cell_desc = self._get_description_for_sections(cell_info)
            if flag_to_use_first_value_as_name == 1:
                name_for_section = str(each_cell) + ": " + cell_desc.strip(".")
            else:
                desc_for_sub_section_list.append(str(each_cell) + ": " + cell_desc.strip("."))
        desc_for_sub_section = ". ".join(desc_for_sub_section_list)
        range_props_temp = {cs.DESC_KEY: desc_for_sub_section}
        table_cell_triplets = self._refer_schema_create_triplet(
            (table_domain, cs.HAS_SUB_SECTION, name_for_section),
            domain_props=table_domain_props,
            range_props=range_props_temp, domain_type=table_domain_type)
        return table_cell_triplets


if __name__ == '__main__':
    # logger configuration
    # logger.getLogger().setLevel(logger.DEBUG)
    logger.basicConfig(level=logger.INFO,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    obj = Operation()

    # For testing the actual images

    from docextraction.xml_extractor import XMLExtractor

    opr_xml_extract = XMLExtractor.get_section_data(
        r"E:\Manuals\Washing Machine\WM4500H\en-us\xml\book\us_main.book.xml", "Operation")

    # opr_xml_extract.get_operation_data()
    print(opr_xml_extract)
    # New Testing New Formats
    # new_dict = json.load(
    #     open(r"E:\TripletsCheck\operation_with_image\operation.json"))

    triplets = obj.make_triplets(opr_xml_extract)
    print("Triplets = ", triplets)
    # #
    # # # To populate
    # from knowledge.database import DBInterface
    #
    # db_obj = DBInterface()
    # db_obj.create_knowledge(triplets)
