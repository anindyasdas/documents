# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""

from lxml import etree as et
import sys
import os
import re
import logging as logger
from pathlib import Path
from io import StringIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')))
from constants import params as p


class XMLExtractor:
    """
    class is used to parse the xml and extract the section
    information

    @method -
    get_section(section_title) - return the section information
                                based on required section
    """

    def __init__(self, file_path=None):
        """
        constructor initializing the etree element and regex for
        model number extraction

        Args:
            file_path:xml file absolute path
            It can be optional during executing the test case for model no
            extraction.
        """
        # For reference if file_path:
        #     self.etree = self._parse_file(file_path)
        self.section_needed = ""
        # for future refe regex = r'(\w*\d+\w(\w|\*))'
        model_extract_full = r'[A-Z]+[^,\/\s]+'
        self.model_regex = re.compile(model_extract_full, flags=re.IGNORECASE)
        self.REFRIGERATOR_PRD_TYPE = "REFRIGERATOR"
        self.OVEN_PRD_TYPE = "MICROWAVE OVEN"
        self.file_path = file_path

    def _return_regex_truncated_model_no(self, model_no):
        """
        return the truncated model_no based on regex defined
        regex will give AlphaNumeric+one Alphabet+*

        Args:
            model_no: text from <Buyermodel> tag
        Return:
            truncated model_no
        """
        logger.debug('model_no : %s', model_no.strip())
        result = self.model_regex.match(model_no.strip()).group()
        char = result[-1]
        if char != '*':
            result = result[0:-1] + '*'

        return result

    def _return_truncated_model_no(self, model_no):
        """
        To return the truncated model number
        Args:
            model_no: Original Model Number

        Returns:
            Truncated model number
        """
        mo = re.match('.+([0-9])[^0-9]*$', model_no)
        final_model_no = model_no[0:mo.start(1) + 2]

        # Remove the * at last if any
        if final_model_no[-1] == '*':
            final_model_no = final_model_no[0:-1]

        logger.debug('f_model_no : %s', final_model_no)

        return final_model_no

    def parse_file(self, file_path):
        """
        parse the file and returns the element tree

        Args:
            file_path: path of the main xml
        Return:
             etree:element tree
        """
        self.etree = et.parse(file_path)
        # print(et.tostring(self.etree, pretty_print=True, encoding='unicode'))
        return self.etree

    def _get_prefaces(self):
        """
        find all the prefaces tag

        Return:
            list of prefaces tag element
        """
        ele_prefaces = self.etree.findall(p.XMLTags.PREFACE_TAG)
        return ele_prefaces

    def _get_chapters(self):
        """
        find all chapter element

        Return:
            list of chapter element
        """
        ele_chapters = self.etree.findall(p.XMLTags.CHAPTER_TAG)
        return ele_chapters

    def _get_appendix(self):
        """
        find all appendix element

        Return:
            list of appendix element
        """
        ele_appendix = self.etree.findall(p.XMLTags.APPENDIX_TAG)
        return ele_appendix

    def _check_title_in_list(self, title, title_list):
        """
        check the title is in the title_list

        Args:
            title - to be searched
            title_list - list of title
        Return :
            True - if title is in title_list
            False - if title is not in title_list
        """
        for m_title in title_list:
            # logger.debug('check_title : (%s):(%s):(%s)', title.lower(), m_title.lower(),
            #              (title.lower() in m_title.lower()))
            if title.lower().strip() == m_title.lower().strip():
                return True
        return False

    def _find_preface(self, title_list):
        """
        find the given title from the element under preface element

        Args:
            title_list: list of titles
        Return:
            xml element
        """
        ele_prefaces = self._get_prefaces()
        for ele_preface in ele_prefaces:
            ele_title = ele_preface.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text.lower()
            if title_txt in title_list:
                return self.preface_tag, ele_preface
            else:
                ele_sections = ele_preface.findall(p.XMLTags.SECTION_TAG)
                xml_tag, lxml_ele = self._find_in_sections(ele_sections, title_list)

                if xml_tag == p.XMLTags.UNKNOWN_TAG:
                    continue
                else:
                    return xml_tag, lxml_ele
        return p.XMLTags.UNKNOWN_TAG, None

    def _find_chapters(self, title_list):
        """
        find the given title find from element under chapter

        Args:
            title_list: list of titles
        Return:
            xml element
        """
        ele_chapters = self._get_chapters()
        xml_tags_list = []
        ele_chapter_list = []
        for ele_chapter in ele_chapters:
            ele_title = ele_chapter.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text.lower()
            logger.debug("chapter title : %s %s", title_txt, title_txt == "고장 신고 전 확인하기")
            logger.debug("title list : %s", title_list)
            if title_txt in title_list:
                xml_tags_list.append(p.XMLTags.CHAPTER_TAG)
                ele_chapter_list.append(ele_chapter)
                continue
            else:
                ele_sections = ele_chapter.findall(p.XMLTags.SECTION_TAG)
                xml_tag, lxml_ele = self._find_in_sections(ele_sections, title_list)

                if xml_tag == p.XMLTags.UNKNOWN_TAG:
                    continue
                else:
                    return xml_tag, lxml_ele
        if xml_tags_list:
            return xml_tags_list,ele_chapter_list
        else:
            return p.XMLTags.UNKNOWN_TAG, None

    def _find_appendix(self, title_list):
        """
        find the given title find the element under chapter element

        Args:
            title_list: list of titles
        Return:
            xml element
        """
        ele_appendixes = self._get_appendix()
        xml_tags_list = []
        ele_appendix_list = []
        for ele_appendix in ele_appendixes:
            ele_title = ele_appendix.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text
            if title_txt in title_list:
                xml_tags_list.append(p.XMLTags.APPENDIX_TAG)
                ele_appendix_list.append(ele_appendix)
            else:
                ele_sections = ele_appendix.findall(p.XMLTags.SECTION_TAG)
                xml_tag, lxml_ele = self._find_in_sections(ele_sections, title_list)

                if xml_tag == p.XMLTags.UNKNOWN_TAG:
                    continue
                else:
                    return xml_tag, lxml_ele
        if ele_appendix_list:
            return xml_tags_list,ele_appendix_list
        else:
            return p.XMLTags.UNKNOWN_TAG, None

    def _find_in_sections(self, ele_sections, title_list):

        for ele_section in ele_sections:
            ele_title = ele_section.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text.lower()
            # if title_txt in title_list:
            if self._check_title_in_list(title_txt, title_list):
                return p.XMLTags.SECTION_TAG, ele_section
            else:
                xml_tag, lxml_ele = self._find_in_topic(ele_section, title_list)

                if xml_tag == p.XMLTags.UNKNOWN_TAG:
                    continue
                else:
                    return xml_tag, lxml_ele

        return p.XMLTags.UNKNOWN_TAG, None


    def _find_in_topic(self, ele_section, title_list):
        ele_topics = ele_section.findall(p.XMLTags.TOPIC_TAG)
        for ele_topic in ele_topics:
            ele_title = ele_topic.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text.lower()
            logger.debug('Topic title : (%s)', ele_title.text)
            # if title_txt in title_list:
            if self._check_title_in_list(title_txt, title_list):
                return p.XMLTags.TOPIC_TAG, ele_topic
        return p.XMLTags.UNKNOWN_TAG, None

    def _get_lang_detail(self):
        """
        get the language details from the root element

        Return:
            lang - language of the manual
        """

        if self.etree.getroot() is not None:
            for attrib, value in self.etree.getroot().items():
                if attrib == p.XMLTags.LANG_ATTRIB:
                    logger.debug("lang : %s", value)
                    return value
        return None

    def get_buyermodel(self):
        """
        get the model string from xml element tree
        Return:
            model string
        """
        ele_bookinfo = self.etree.find(p.XMLTags.BOOKINFO_TAG)
        ele_buyermodel = ele_bookinfo.find(p.XMLTags.BUYERMODEL_TAG)
        model_no = ele_buyermodel.text
        if model_no:
            return model_no
        else:
            return "****"

    def get_partnumber(self):
        """
        get the model string from xml element tree
        Return:
            model string
        """
        ele_bookinfo = self.etree.find(p.XMLTags.BOOKINFO_TAG)
        ele_partnumber = ele_bookinfo.find(p.XMLTags.PARTNUMBER_TAG)
        partnumber = ele_partnumber.text
        return partnumber

    def _get_model_list(self):
        """
        get the list of supported model no
        from xml
        """
        model_no_list = []
        model_nos = self.get_buyermodel()
        model_list_bt = model_nos.split('/')
        model_no_list = [self._return_regex_truncated_model_no(model_no) for model_no in model_list_bt]
        return model_no_list

    def _get_regex_model_list(self, model_no_str):
        """
        get the list of supported model no
        from <Buyermodel> tag.

        Truncate model no as Alphanumeric + *

        Return:
            List of truncated model no
        """
        model_no_list = []
        result = self.model_regex.findall(model_no_str)
        for e_modelno in result:
            model_no_list.append(e_modelno)
        return model_no_list

    def get_product_type(self):
        """
        get the product name string from xml element tree

        Return:
            product name string
        """
        sub_prd = None
        ele_bookinfo = self.etree.find(p.XMLTags.BOOKINFO_TAG)
        ele_productname = ele_bookinfo.find(p.XMLTags.PRODUCTNAME_TAG)
        product_name = ele_productname.text

        if (product_name == p.P_AC) or (product_name == p.WINDOW_PRD):
            product_name = p.AIR_CONDITIONER

        if product_name.lower() == p.ExtractionConstants.KEPLER_PRD_NAME_IN_MANUAL:
            sub_prd = p.ExtractionConstants.KEPLER_PRD
            product_name = p.get_generic_product_name(product_name)
        else:
            product_name = p.get_generic_product_name(product_name)
            sub_prd = self._get_sub_prd_type(product_name)

        return product_name, sub_prd


    def _get_sub_prd_type(self, product_name):
        """
        Extract the sub product type from the entity variable

        Return:
            sub_prod_type: String
        """
        folder_names = self.file_path.split(os.path.sep)
        reframed_path = os.path.sep.join(folder_names[0:len(folder_names)-1])
        with open(reframed_path+os.path.sep+"bookinfo.xml","r") as pf:
            xml_string = pf.read()
            xml_string = xml_string.replace("&","")
            xml_string = xml_string.replace(";", "")
            custom_parser = et.XMLParser(dtd_validation=False, resolve_entities=False)
            tree = et.parse(StringIO(xml_string), custom_parser)
            ele_product_type = tree.find(p.XMLTags.PRODUCTNAME_TAG)
            # product.refrigerator_medium_;
            prd_name_entity = "".join(ele_product_type.itertext())
            # refrigerator_medium_
            sub_prod_type = prd_name_entity.split(".")[1]
            # medium
            sub_prod_type = sub_prod_type.replace("_"," ").strip()
            if product_name != sub_prod_type:
                # _medium_
                sub_prod_type = sub_prod_type.replace(product_name, "").strip()
            return sub_prod_type

    def _standadize_topic_title(self, topic_title):
        """
        standardize the topic title

        Args:

        """
        keys = p.ExtractionConstants.SECTION_NAMING_LIST.keys()
        for key in keys:
            topic_list = p.ExtractionConstants.SECTION_NAMING_LIST[key]
            if topic_title in topic_list:
                return key
        return topic_title


    def _do_preprocessing(self, text):
        """
        do preprocessing by removing some unwanted charaters from the given text

        Args:
            text - extracted text
        Return:
            preprocessed string
        """
        text = text.strip()
        # replacing the multiple in-between spaces with one space
        text = re.sub('\s+', ' ', text)
        # remove the space around the '-' character
        text = re.sub('\s*-\s*', '-', text)
        # replace the '\n' character
        text = re.sub('\n', '', text)
        text = re.sub('\t', '', text)

        return text


    def _validate_file_accessing(self, file_path):
        """
        validate whether the file can be opened or not

        Args:
            file_path: input file  path

        Return:
            True If
        """
        try:
            op = open(file_path)
            op.close()
            return p.ResponseCode.SUCCESS
        except FileNotFoundError:
            return p.ResponseCode.FILE_NOT_FOUND
        except OSError:
            return p.ResponseCode.FILE_OPEN_ERROR

    def _validate_file_size(self, file_path):
        """
        validate the file size

        Args:
            file_path - Input file path

        Return:
            True - If file size greater than 0
            False - otherwise
        """
        if Path(file_path).stat().st_size > 0:
            return True

        return False

    def _validate_file_format(self, file_path):
        """
        validate the file path for format

        Args:
            file_path: input file path
        Return:
            True if format supported
            False If not
        """
        actual_path = file_path.split(os.path.sep)
        try:
            logger.debug("file_format : %s %s", actual_path,actual_path[-1].split("."))
            file_format = actual_path[-1].split(".")[-1]
            logger.debug("file_format : %s",file_format)
            if file_format == "xml":
                return True
            return False
        except Exception as e:
            logger.exception("exception validating file format : %s",e)
            return False


    def validate_file(self, file_path):
        """
        validate the file for size ,format, accessibility

        Args:
            file_path - input file path

        Return:
            True,Empty Response dict - If all conditions passed
            False,Response dict with error details - If one condition failed
        """

        response_json = {}

        if not self._validate_file_format(file_path):
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.FILE_FORMAT_NOT_SUPPORTED]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][
                p.ExternalErrorMsgs.MSG]
            return False, response_json

        if self._validate_file_accessing(file_path) == p.ResponseCode.FILE_NOT_FOUND:
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.FILE_NOT_FOUND]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][
                p.ExternalErrorMsgs.MSG]
            return False, response_json
        elif self._validate_file_accessing(file_path) == p.ResponseCode.FILE_OPEN_ERROR:
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.FILE_OPEN_ERROR]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][
                p.ExternalErrorMsgs.MSG]
            return False, response_json

        if not self._validate_file_size(file_path):
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.FILE_IS_EMPTY]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][
                p.ExternalErrorMsgs.MSG]
            return False, response_json
        else:
            return True, response_json


    def get_ent_prd_type(self, section, prd_type):
        """
        map the internal section title to entity product type if the section title is like washer,dryer,common
        else map based on the product type

        Args:
            section: internal section title
            prd_type:
        """
        section = section.lower()
        if section in p.GenericProductNameMapping.INT_SEC:
            for sec_key in p.GenericProductNameMapping.SEC_TO_ENT_PRD_MAP.keys():
                if section == sec_key:
                    return [ent_prd_type for ent_prd_type in p.GenericProductNameMapping.SEC_TO_ENT_PRD_MAP[sec_key]]
        else:
            for prd in p.GenericProductNameMapping.PRD_TO_ENT_PRD_MAP.keys():
                if prd_type.lower() in p.GenericProductNameMapping.PRD_TO_ENT_PRD_MAP[prd]:
                    return [prd]

    @staticmethod
    def get_section(file_path, section_title):
        """
        get the required section instance

        Args:
            section_title: required section
        Return:
            instance of required section class
        """
        if section_title == p.SPEC_SECTION:
            from docextraction.specification_xml_extractor import SpecificationXMLExtractor
            return SpecificationXMLExtractor(file_path)
        elif section_title == p.TROB_SECTION:
            from docextraction.troubleshooting_xml_extractor import TroubleshootingXMLExtractor
            return TroubleshootingXMLExtractor(file_path)
        elif section_title == p.OPERATION:
            from docextraction.operationxmlextractor.operation_xml_extrcator import OperationXMLExtractor
            return OperationXMLExtractor(file_path)

    @staticmethod
    def get_section_data(file_path, section_title):
        """
        get the required section instance

        Args:
            section_title: required section
        Return:
            instance of required section class
        """
        if section_title == p.SPEC_SECTION:
            specification_xml_extractor = XMLExtractor.get_section(file_path, section_title)
            file_vald_flag, resp_json = specification_xml_extractor.validate_file(file_path)

            if file_vald_flag:
                return specification_xml_extractor.get_spec_detail()
            return resp_json
        elif section_title == p.TROB_SECTION:
            troubleshooting_xml_extractor = XMLExtractor.get_section(file_path, section_title)
            file_vald_flag, resp_json = troubleshooting_xml_extractor.validate_file(file_path)

            if file_vald_flag:
                return troubleshooting_xml_extractor.get_troubleshooting_data()
            return resp_json
        elif section_title == p.OPERATION:
            operation_xml_extractor = XMLExtractor.get_section(file_path, section_title)
            file_vald_flag, resp_json = operation_xml_extractor.validate_file(file_path)

            if file_vald_flag:
                return operation_xml_extractor.get_operation_data()
            return resp_json
        else:
            response_json = {}
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.SECTION_NOT_SUPPORTED]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][p.ExternalErrorMsgs.MSG]
            return response_json


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    import argparse
    import json
    parser = argparse.ArgumentParser()

    parser.add_argument("--xml_file_path",
                        type=str,
                        help="Input XML file(us_main_book.xml) path", required=True)

    parser.add_argument("--req_section",
                        type=str,
                        help="can be Specification,TROUBLESHOOTING or Operation", required=True)
    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    p_args = parser.parse_args()
    file_path = p_args.xml_file_path
    reqired_section = p_args.req_section

    xml_extracted_data = XMLExtractor.get_section_data(file_path, reqired_section)
    print("---------------- XML EXTRACTED DATA ---------------\n")
    print("XML EXTRACTED DATA : \n" + str(xml_extracted_data))
    with open('extracted_json.json', 'w', encoding='utf-8') as f:
        json.dump(xml_extracted_data, f, ensure_ascii=False, indent=4)
