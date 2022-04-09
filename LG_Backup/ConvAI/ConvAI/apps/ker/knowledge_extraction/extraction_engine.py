"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com
"""
import sys
import json
import logging as logger
import os.path
from datamodel.dminterface import DMInterface
from constants import params as cs
from docextraction.extraction import DocxTableExtractor
from docextraction.tablehandler import TableInfoExtractor
from knowledge.database import DBInterface
from docextraction.xml_extractor import XMLExtractor


class KnowledgeExtractor(object):
    """
    defines the method to extract information from the manual
    """

    def __init__(self):
        pass

    def __extract_from_doc(self, file_path, section_name=cs.SPEC_SECTION):
        """
            Call docextraction module to extract knowledge and populate
            knowledge to database.
            Args:
                file_path: str
                    actal file path from which knowledge will be extracted
                section_name: str
                    actual section  of which knowledge is to be extracted
            Returns:
                cs.SUCCESS - on success
                cs.DATA_NOT_FOUND - if no data is found
                cs.INTERNAL-ERROR - if any internal error
        """
        table_dict = None
        # Extract table from the file
        obj = DocxTableExtractor()
        table_dict = obj.get_all_tables(file_path)

        if table_dict is None:
            return cs.INTERNAL_ERROR

        for key, value in table_dict.items():
            logger.debug(str(key))
            logger.debug(str(value))
            if key == section_name:
                tableinfo_ext = TableInfoExtractor()
                key_value_pair = tableinfo_ext.get_info(section_name, value)

                logger.debug("-----------------DOC KEY VALUE PAIR-----------")
                logger.debug(str(key_value_pair))
                logger.debug("---------------------------------------------")

                # creating instance of DMInterface class
                obj = DMInterface()
                triplets = obj.make_triplets(section_name, key_value_pair)
                logger.debug("----------------TRIPLETS ---------------")
                logger.debug(str(triplets))
                logger.debug("----------------------------------------")

                DBInterface().create_knowledge(triplets)
                return cs.SUCCESS
            else:
                return cs.DATA_NOT_FOUND

    def __extract_from_xml(self, file_path, section_name, verify_triplets_only):
        """
            Call xml_extractor module to extract knowledge and populate
            knowledge to database.
            Args:
                file_path: str
                    actual file path from which knowledge will be extracted
                section_name: str
                    actual section  of which knowledge is to be extracted
            Returns:
                cs.SUCCESS - on success
                cs.DATA_NOT_FOUND - if no data is found
        """

        # creating instance of DMInterface class
        dm_obj = DMInterface()

        xml_extracted_data = XMLExtractor.get_section_data(file_path, section_name)
        logger.info("---------------- XML EXTRACTED DATA ---------------\n")
        logger.info("XML EXTRACTED DATA : \n" + str(xml_extracted_data))
        with open('extracted_json.json', 'w', encoding='utf-8') as f:
            json.dump(xml_extracted_data, f, ensure_ascii=False, indent=4)

        triplets = dm_obj.make_triplets(section_name, xml_extracted_data)
        logger.info("---------------- TRIPLETS ---------------\n")
        logger.info("CREATED TRIPLETS : \n" + str(triplets))
        with open('triplet_json.json', 'w', encoding='utf-8') as f:
            json.dump(triplets, f, ensure_ascii=False, indent=4)

        logger.info("Extracted and triplet json files created, verify before populating\n")

        # If verify_triplets_only option is True, it will not populate the data to the Neo4j DB
        if not verify_triplets_only:
            # instance of DBInterface
            db_obj = DBInterface()
            db_obj.create_knowledge(triplets)

        return cs.SUCCESS

    def extract_knowledge(self, file_path, section_name, verify_triplets_only=False):
        """
            This is main interface for the extraction engine.
            Args:
                file_path: str
                    actual file path from which knowledge will be extracted
                section_name:str
                verify_triplets_only: This is used to verify only triples,
                population will not be done if True
            Returns:
                cs.SUCCESS - on success
                cs.NOT_SUPPORTED - on unsupported formats
        """

        # Check availability of the file
        if os.path.isfile(file_path) is False:
            logger.error("Document not exist")
            return cs.DATA_NOT_FOUND

        logger.debug("Input document:" + str(file_path))
        # if input file is doc or docx, call docextraction
        if (file_path.endswith('.doc') or file_path.endswith('.docx')):
            self.__extract_from_doc(file_path)
        # if input file is xml,call xmlextraction
        elif file_path.endswith('.xml'):
            self.__extract_from_xml(file_path, section_name, verify_triplets_only=verify_triplets_only)
        else:
            return cs.NOT_SUPPORTED
        return cs.SUCCESS

    def extract_knowledge_for_multiple_files(self, file_path, section_name):
        """
        For populating multiple manuals at once for a particular section
        (the file_path should contain path of XML files in lines)
        Args:
            file_path: A text file which contains path of XML files in lines
            section_name: Name of the Section Specification,TROUBLESHOOTING or Operation
        """

        logger.debug("STARTED POPULATING AS MULTIPLE MANUAL MODE:" + str(file_path))

        try:
            with open(file_path, "r", encoding="utf-8") as xml_paths:
                for each_path in xml_paths:
                    each_path = each_path.rstrip()
                    logger.debug("POPULATING: {} for {} Section".format(str(each_path), section_name))
                    self.extract_knowledge(each_path, section_name)
                    logger.debug("POPULATING SUCCESS: {} for {} Section".format(str(each_path), section_name))
        except Exception as e:
            logger.exception("Exception in populating multiple manuals: " + str(e))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--multiple", action="store_true",
                        help="For populating multiple manuals in single shot.")

    parser.add_argument("-v", "--verify", action="store_true",
                        help="This option is just to verify the triplets, population will not be done.")

    parser.add_argument("--xml_file_path",
                        type=str,
                        help="Input XML file(us_main_book.xml) path, "
                             "if -m is is specified give a text file with list of paths", required=True)

    parser.add_argument("--req_section",
                        type=str,
                        help="can be Specification, Troubleshooting or Operation", required=True)

    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    p_args = parser.parse_args()
    file_path = p_args.xml_file_path
    required_section = p_args.req_section

    engine = KnowledgeExtractor()

    verify_only_triples = False
    if p_args.verify:
        verify_only_triples = True

    if p_args.multiple:
        engine.extract_knowledge_for_multiple_files(file_path, required_section)
    else:
        engine.extract_knowledge(file_path, required_section, verify_triplets_only=verify_only_triples)
