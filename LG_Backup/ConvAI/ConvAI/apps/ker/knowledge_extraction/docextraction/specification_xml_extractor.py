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
from collections import defaultdict

from constants import params as p
from docextraction.xml_extractor import XMLExtractor
from docextraction.formatvalidator import SpecificationTableValidator


class SpecificationXMLExtractor(XMLExtractor):
    """
    class used to extract specification detail from the table element

    @method: _get_table_key_values: prepare key-value pair
    """
    no_of_cols = 0
    # constants used to identify the key-value pair outside the table
    ELECTRICAL_REQ_STR = "Electrical requirements"
    WATER_PRS_STR = "water pressure"
    PWR_SUPPLY_STR = "Power Supply"
    RATED_PWR_CONSUM_STR = "Rated Power Consumption"
    MICROWAVE_OT_STR = "Microwave Output"
    RATED_CUR_STR = "Rated Current"
    electrical_req_key = None
    evalue = None
    water_pressure_key = None
    wvalue = None
    power_supply_key = None
    power_supply_value = None
    microwave_ot_key = None
    microwave_ot_value = None
    rated_current_key = None
    rated_current_value = None
    rated_pwr_consumption_key = None
    rated_pwr_consumption_value = None

    def _get_section(self, section_title):
        """
        get the parent tag of requied section title

        Args:
            section_title: section title reuqired to identify
        Return:
            key-value pair of the section
        """
        title_list = [title.lower() for title in p.SECTION_NAMING_LIST[section_title]]
        tag_str, tag = self._find_chapters(title_list)
        if tag_str is not p.XMLTags.UNKNOWN_TAG:
            if tag_str == p.XMLTags.TOPIC_TAG:
                key_value_pair, key = self._extract_from_topic(tag)
                return key_value_pair
            elif tag_str == p.XMLTags.APPENDIX_TAG:
                return self._extract_from_appendix(tag)
        return None

    def _get_section_generic(self, section_title):
        """
        get the parent tag of requied section title

        Args:
            section_title: section title reuqired to identify
        Return:
            key-value pair of the section
        """
        title_list = [title.lower() for title in p.ExtractionConstants.SECTION_NAMING_LIST[section_title]]
        tag_str, tag = self._find_chapters(title_list)
        if tag_str is not p.XMLTags.UNKNOWN_TAG:
            if tag_str == p.XMLTags.TOPIC_TAG:
                key_value_pair, key = self._extract_from_topic_generic(tag)
                return key_value_pair
            elif tag_str == p.XMLTags.APPENDIX_TAG:
                return self._extract_from_appendix(tag)

        response_json = {}
        ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.SECTION_NOT_AVAILABLE]
        response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
        response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][p.ExternalErrorMsgs.MSG]
        return response_json

    def _frame_common_info(self, dict, key, value):
        """
        Frame the common_info section in the given dict

        dict - Response dict
        common_info - common info as dict to be under common_info key
        """
        logger.debug("common info : %s, %s", key, value)
        if key is not None:
            if p.COMMON_INFO_KEY not in dict:
                dict[p.COMMON_INFO_KEY] = {}
            if p.DATA_KEY not in dict[p.COMMON_INFO_KEY]:
                dict[p.COMMON_INFO_KEY][p.DATA_KEY] = [0]  # initalizing array with one element
                dict[p.COMMON_INFO_KEY][p.DATA_KEY][0] = {}
                dict[p.COMMON_INFO_KEY][p.DATA_KEY][0][key] = value
            else:
                dict[p.COMMON_INFO_KEY][p.DATA_KEY][0][key] = value

    def _extract_from_topic_generic(self, ele_topic):
        """
        extract the details from topic element

        Args:
            ele_topic: topic element from xml element tree
        Return:
            details as dict
        """
        response_json = {}
        final_json = {}
        framed_json = {}
        json_model_list = []
        key_value_pairs = {}
        simple_sect = False
        spec_valid = SpecificationTableValidator()

        valid_flag = spec_valid.validate_spec_content(ele_topic)

        if valid_flag:

            for child in ele_topic:
                if child.tag == p.XMLTags.TABLE_TAG:
                    json_model_list = self._extract_spec_table(child, framed_json, json_model_list)
                elif child.tag == p.XMLTags.PARA_TAG:
                    self._fill_common_info_in_json(child, framed_json)

                elif child.tag == p.XMLTags.SIMPLESECT_TAG:
                    simple_sect = True
                    json_model_list = self._extract_spec_simple_section(child, final_json, json_model_list)

            if p.COMMON_INFO_KEY in framed_json:
                framed_json[p.MODELS_KEY] = json_model_list

            framed_json[p.PRODUCT_TYPE_KEY] = self.get_product_type()
            framed_json[p.PARTNUMBER] = self.get_partnumber()
            if simple_sect == False:
                final_json[p.DUMMY_SECTION_KEY] = framed_json

            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.SUCCESS]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.DATA_KEY] = final_json
            return response_json, None

        ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.FORMAT_NOT_SUPPORTED]
        response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
        response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][p.ExternalErrorMsgs.MSG]
        return response_json, None

    def _fill_common_info_in_json(self, child, framed_json):
        content = self._get_value_frm_para(child)
        logger.debug('common section : %s', content)
        if (self.PWR_SUPPLY_STR in content) or (self.RATED_PWR_CONSUM_STR in content) or \
                (self.MICROWAVE_OT_STR in content) or (self.RATED_CUR_STR in content) or \
                (self.ELECTRICAL_REQ_STR in content) or (self.WATER_PRS_STR in content):
            content_arr = content.split(":")
            self._frame_common_info(framed_json, content_arr[0].strip(),
                                    [self._do_preprocessing(content_arr[1])])

    def _extract_spec_table(self, child, framed_json, json_model_list):
        model, key_value_pair = self.get_table_key_values_generic(child)
        if model is not None:
            logger.debug('Extracted key-value pairs : %s, %s', model, key_value_pair)
            json_model_list = model
            framed_json[p.UNIQUE_INFO_KEY] = key_value_pair[p.UNIQUE_INFO_KEY]
        else:
            json_model_list = model
            framed_json[p.UNIQUE_INFO_KEY] = key_value_pair[p.UNIQUE_INFO_KEY]
        return json_model_list

    def _extract_spec_simple_section(self, child, final_json, json_model_list):
        title = child.find(p.XMLTags.TITLE_TAG)
        for lchild in child:
            if lchild.tag == p.XMLTags.TABLE_TAG:
                json_model_list, key_value_pair = self.get_custom_table_key_values_generic(lchild)
                logger.debug('generic key value pair : %s', key_value_pair)
                final_json[title.text] = key_value_pair
        return json_model_list

    def _remove_newline_rtn(self, text):
        return text.replace('\n', '')

    def _post_processing_json(self, json_data):
        """
        post processing the framed json for custom json
        """
        final_dict = {}
        col_2_key = "col2"
        col_3_key = "col3"
        keys = json_data.keys()
        new_key = None
        for key in keys:
            new_key = None
            value_list = []
            tvalue_dict = json_data[key]

            logger.debug("tvalue_dict keys : %s", tvalue_dict.keys())
            for lkey in tvalue_dict.keys():
                value_list = []
                for values in tvalue_dict[lkey]:
                    if p.XMLTags.EMPHASIS_TAG in values:
                        new_key = key + "*" + values[p.XMLTags.EMPHASIS_TAG]
                    else:
                        value_list.append(self._remove_newline_rtn(values[p.XMLTags.PARA_TAG]))

                if new_key is not None:
                    final_dict[self._remove_newline_rtn(new_key)] = value_list
                else:
                    final_dict[self._remove_newline_rtn(key)] = value_list

        return final_dict

    def _get_text_frm_para(self, para):
        """
        parse para element and frame text

        Args:
            para: para element
        Return:
            text
        """
        dict = {}
        ele_empahsis = para.find(p.XMLTags.EMPHASIS_TAG)

        if ele_empahsis is not None:
            dict["emphasis"] = ele_empahsis.text
        else:
            ele_key = para.find(p.XMLTags.KEY_TAG)
            if ele_key is not None:
                temp_txt = "".join(ele_key.itertext())
                actual_para = "".join(para.itertext())
                start_idx = actual_para.index(temp_txt)
                end_idx = start_idx + len(temp_txt)
                temp_txt = actual_para[0:(start_idx - 1)] + ' *' + temp_txt + '* ' + actual_para[(end_idx + 1):]
                dict["para"] = self._do_preprocessing(temp_txt)
            else:
                dict["para"] = "".join(para.itertext())
        return dict

    def get_custom_table_key_values_generic(self, table):
        """
        prepare the key-value pair from table element

        Args:
            table: table element
        Return:
            key_value_pair dict
        """
        final_key_value_pair = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY] = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY] = []
        value_list = []
        key_flag = False
        third_col = False
        model_str = "Model"
        model_flag = False
        key = ""
        ele_tgroup = self._get_tgroup(table)

        ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
        ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
        key_value_pair = {}
        col_2_key = "col2"
        col_3_key = "col3"
        col_key = ""
        for row in ele_rows:
            for ele_entry in row.findall(p.XMLTags.ENTRY_TAG):
                ele_items = ele_entry.items()
                for attrib, value in ele_items:
                    if attrib == p.XMLTags.COLNAME_ATTRIB:
                        if value == "1":
                            key_flag = True
                            col_key = ""
                        elif value == "3":
                            key_flag = False
                            col_key = "col3"
                        elif value == "2":
                            col_key = "col2"
                            key_flag = False
                ele_paras = ele_entry.findall(p.XMLTags.PARA_TAG)
                text = ""
                value_list = []

                if len(ele_paras) > 1:
                    if key_flag:
                        for ele_para in ele_paras:
                            text += ' ' + self._do_preprocessing(self._get_value_frm_para(ele_para))
                    else:
                        for ele_para in ele_paras:
                            value_list.append(self._get_text_frm_para(ele_para))
                else:
                    if key_flag:
                        text = self._do_preprocessing(self._get_value_frm_para(ele_paras[0]))
                        if text.strip() == model_str:
                            model_flag = True
                        else:
                            model_flag = False
                    else:
                        value_list.append(self._get_text_frm_para(ele_paras[0]))

                if key_flag:
                    key = text
                else:
                    if model_flag:

                        if p.MODELS_KEY not in key_value_pair:
                            key_value_pair[p.MODELS_KEY] = {}

                        if col_2_key not in key_value_pair[p.MODELS_KEY]:
                            key_value_pair[p.MODELS_KEY][col_2_key] = value_list
                            model_flag = False
                    else:
                        if len(key) > 0:
                            if key not in key_value_pair:
                                key_value_pair[key] = {}

                            if col_key not in key_value_pair[key]:
                                key_value_pair[key][col_key] = []
                                key_value_pair[key][col_key] = value_list
                            else:
                                key_value_pair[key][col_key] = value_list

        final_key_value_pair[p.PRODUCT_TYPE_KEY] = self.get_product_type()
        final_key_value_pair[p.PARTNUMBER] = self.get_partnumber()
        final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY].append(self._post_processing_json(key_value_pair))
        logger.debug('get_table_key_values key_value_pair : %s', key_value_pair)
        return key_value_pair[p.MODELS_KEY], final_key_value_pair

    def _replace_newline_char(self, text):
        """
        replace the newline character with empty character

        Args:
            text - need to replace \n character

        Return:
            Converted string
        """
        return text.replace('\n', "")

    def get_table_key_values_generic(self, table):
        """
        prepare the key-value pair from table element

        Args:
            table: table element
        Return:
            key_value_pair dict
        """
        final_key_value_pair = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY] = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY] = []
        value_list = []
        key_flag = False
        key = ""
        ele_tgroup = self._get_tgroup(table)

        prd_type = self.get_product_type()

        if (prd_type == p.GenericProductNameMapping.REFRIGERATOR_GEN_NAME) or \
                (prd_type == p.GenericProductNameMapping.MICROWAVE_OVEN_GEN_NAME):
            logger.debug('no of cols : %s', self.no_of_cols)
            return self.get_table_key_value_generic(table, ele_tgroup)
        else:

            if self.no_of_cols > 2:
                return self._get_table_details_with_merged_col(ele_tgroup, table)

            ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
            ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
            key_value_pair = {}
            for row in ele_rows:
                for ele_entry in row.findall(p.XMLTags.ENTRY_TAG):
                    ele_items = ele_entry.items()
                    for attrib, value in ele_items:
                        if attrib == p.XMLTags.COLNAME_ATTRIB:
                            if value == "1":
                                key_flag = True
                            else:
                                key_flag = False
                    ele_paras = ele_entry.findall(p.XMLTags.PARA_TAG)
                    text = ""
                    value_list = []
                    if len(ele_paras) > 1:
                        for ele_para in ele_paras:
                            if key_flag:
                                text += self._do_preprocessing(self._get_value_frm_para(ele_para)) + " "
                            else:
                                value_list.append(self._do_preprocessing(self._get_value_frm_para(ele_para)))
                    else:
                        temp_txt = self._do_preprocessing(self._get_value_frm_para(ele_paras[0]))
                        if key_flag:
                            text = temp_txt
                        else:
                            value_list.append(temp_txt)
                    if key_flag:
                        key = text.strip()
                    else:
                        if len(key) > 0:
                            key_value_pair[key] = value_list

            key_value_pair[p.MODELS_KEY] = self._get_regex_model_list(self._get_thead_detail(table))
            key_value_pair[p.PARTNUMBER] = self.get_partnumber()
            final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY].append(key_value_pair)
            logger.debug('get_table_key_values key_value_pair : %s', key_value_pair)
            return key_value_pair[p.MODELS_KEY], final_key_value_pair

    def _get_table_details_with_merged_col(self, ele_tgroup, table):
        """
        extract the details from the table with merged column details

        Args:
             ele_tgroup - lxml element of the tgroup
             table - lxml element of the table tag
        Return:
            dict framed from the table
        """
        final_key_value_pair = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY] = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY] = []

        ele_thead = ele_tgroup.find(p.XMLTags.THEAD_TAG)
        ele_rows = ele_thead.find(p.XMLTags.ROW_TAG)

        for ele_entry in ele_rows.findall(p.XMLTags.ENTRY_TAG):
            key_value_pair = {}
            col_id = ""
            for attrib, value in ele_entry.items():
                if attrib == p.XMLTags.COLNAME_ATTRIB:
                    col_id = value
                    break

            if (col_id != "1"):
                logger.debug("col id : %s %s", col_id, type(col_id))
                logger.debug('model header : %s', self._get_value_frm_para(ele_entry.find(p.XMLTags.PARA_TAG)))
                key_value_pair[p.MODELS_KEY] = self._get_regex_model_list(
                    self._get_value_frm_para(ele_entry.find(p.XMLTags.PARA_TAG)))
                ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
                ele_int_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
                for row in ele_int_rows:
                    lele_entries = []
                    ele_entries = row.findall(p.XMLTags.ENTRY_TAG)

                    if len(ele_entries) >= self.no_of_cols:
                        logger.debug('required entries : %s %s', col_id,
                                     self._get_value_frm_para(ele_entries[int(col_id) - 1].find(p.XMLTags.PARA_TAG)))
                        lele_entries.append(ele_entries[0])
                        lele_entries.append(ele_entries[int(col_id) - 1])
                    else:
                        lele_entries = ele_entries

                    for ele_entry in lele_entries:
                        ele_items = ele_entry.items()
                        for attrib, value in ele_items:
                            if attrib == p.XMLTags.COLNAME_ATTRIB:
                                if value == "1":
                                    key_flag = True
                                else:
                                    key_flag = False
                        ele_paras = ele_entry.findall(p.XMLTags.PARA_TAG)
                        text = ""
                        value_list = []
                        if len(ele_paras) > 1:
                            if key_flag:
                                for ele_para in ele_paras:
                                    text += self._do_preprocessing(self._get_value_frm_para(ele_para)) + " "
                            else:
                                for ele_para in ele_paras:
                                    value_list.append(self._do_preprocessing(self._get_value_frm_para(ele_para)))
                        else:
                            if key_flag:
                                text = self._do_preprocessing(self._get_value_frm_para(ele_paras[0]))
                            else:
                                value_list.append(self._do_preprocessing(self._get_value_frm_para(ele_paras[0])))
                        if key_flag:
                            key = text.strip()
                        else:
                            if len(key) > 0:
                                key_value_pair[key] = value_list
                logger.debug("int key_value_pair : %s", key_value_pair)
                final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY].append(key_value_pair)
        return self._get_thead_detail(table), final_key_value_pair

    def get_table_key_value_generic(self, table, ele_tgroup):
        """
        get key-value pair from table element

        Args:
            table: lxml element of table
            ele_tgroup : lxml element of tgroup tag

        Return:
            key_value pair of table
        """
        final_key_value_pair = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY] = {}
        final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY] = []
        model_list = []
        key_flag = False
        internal_key = None
        header_dict = self._get_thead_detail_multiple_col(table)
        logger.debug('header_dict : %s', header_dict)
        ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
        ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
        for row in ele_rows:
            key_value_pair = {}
            for ele_entry in row.findall(p.XMLTags.ENTRY_TAG):
                ele_items = ele_entry.items()
                for attrib, value in ele_items:
                    if attrib == p.XMLTags.COLNAME_ATTRIB:
                        if value == "1":
                            key_flag = True
                        else:
                            key_flag = False
                            internal_key = value
                            logger.debug('internal key : %s', internal_key)
                value_list = []
                ele_paras = ele_entry.findall(p.XMLTags.PARA_TAG)
                if len(ele_paras) > 1:
                    for ele_para in ele_paras:
                        if key_flag:
                            model_list.extend(self._get_regex_model_list(self._get_value_frm_para(ele_para)))
                            value_list.extend(self._get_regex_model_list(self._get_value_frm_para(ele_para)))
                        else:
                            value_list.append(self._do_preprocessing(self._get_value_frm_para(ele_para)))
                else:
                    if key_flag:
                        model_list.extend(self._get_regex_model_list(self._get_value_frm_para(ele_paras[0])))
                        value_list.extend(self._get_regex_model_list(self._get_value_frm_para(ele_paras[0])))
                    else:
                        value_list.append(self._do_preprocessing(self._get_value_frm_para(ele_paras[0])))

                if key_flag:
                    key_value_pair[p.MODELS_KEY] = [self._return_regex_truncated_model_no(value) for value in
                                                    value_list]
                    logger.debug('ModelNo : %s', key_value_pair)
                else:
                    if len(key_value_pair[p.MODELS_KEY]) > 0:
                        int_key = header_dict[internal_key]
                        key_value_pair[int_key] = value_list
            key_value_pair[p.PARTNUMBER] = self.get_partnumber()
            final_key_value_pair[p.UNIQUE_INFO_KEY][p.DATA_KEY].append(key_value_pair)
        logger.debug('Final key_value_pair : %s', final_key_value_pair)
        return model_list, final_key_value_pair

    def _extract_from_topic(self, ele_topic):
        """
        extract the details from topic element

        Args:
            ele_topic: topic element from xml element tree
        Return:
            details as dict
        """
        framed_json = {}
        key_value_pairs = {}
        for child in ele_topic:
            if child.tag == p.XMLTags.TABLE_TAG:
                model, key_value_pair = self.get_table_key_values(child)
                if model is not None:
                    m_key_value_pair = {}
                    key_value_pairs[self._return_regex_truncated_model_no(model)] = key_value_pair
                    logger.debug('Extracted key-value pairs : %s, %s', model, key_value_pair)
                    model_list = self._get_regex_model_list(model)
                    for model in model_list:
                        m_key_value_pair[model] = key_value_pair
                    return m_key_value_pair, model
                else:
                    logger.debug('Extracted key-value pairs model : %s, %s', model, key_value_pair)
                    return key_value_pair, None
            elif child.tag == p.XMLTags.PARA_TAG:
                content = self._get_value_frm_para(child)
                self._fill_common_values(content)

        return None, None

    def _fill_common_values(self, content):
        if self.ELECTRICAL_REQ_STR in content:
            content_arr = content.split(":")
            self.electrical_req_key = content_arr[0].strip()
            self.evalue = content_arr[1].strip()
        elif self.WATER_PRS_STR in content:
            content_arr = content.split(":")
            self.water_pressure_key = content_arr[0].strip()
            self.wvalue = content_arr[1].strip()
        elif self.PWR_SUPPLY_STR in content:
            content_arr = content.split(":")
            self.power_supply_key = content_arr[0].strip()
            self.power_supply_value = content_arr[1].strip()
        elif self.RATED_PWR_CONSUM_STR in content:
            content_arr = content.split(":")
            self.rated_pwr_consumption_key = content_arr[0].strip()
            self.rated_pwr_consumption_value = content_arr[1].strip()
        elif self.MICROWAVE_OT_STR in content:
            content_arr = content.split(":")
            self.microwave_ot_key = content_arr[0].strip()
            self.microwave_ot_value = content_arr[1].strip()
        elif self.RATED_CUR_STR in content:
            content_arr = content.split(":")
            self.rated_current_key = content_arr[0].strip()
            self.rated_current_value = content_arr[1].strip()

    def _get_tgroup(self, table):
        """
        get the element tgroup from table element

        Args:
            table: table element from xml
        Return:
            tgroup element
        """
        ele_tgroup = table.find(p.XMLTags.TGROUP_TAG)
        items = ele_tgroup.items()
        for attrib, value in items:
            if attrib == p.XMLTags.COL_ATTRIB:
                self.no_of_cols = int(value)
        return ele_tgroup

    def _get_value_frm_para(self, para):
        """
        parse para element and frame text

        Args:
            para: para element
        Return:
            text
        """
        return "".join(para.itertext())

    def _get_thead_detail(self, table):
        """
        get the model name from table header

        Args:
            table:table from xml element tree
        Return:
            model name from table header
        """
        ele_tgroup = self._get_tgroup(table)
        ele_thead = ele_tgroup.find(p.XMLTags.THEAD_TAG)
        if ele_thead is None:
            return None
        ele_row = ele_thead.find(p.XMLTags.ROW_TAG)
        ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
        logger.debug('Entries in THEAD : %s', ele_entries)
        header_str = ""
        for ele_entry in ele_entries:
            logger.debug('Attrib in Entries : %s', ele_entry.attrib)
            col_index = int(ele_entry.attrib[p.XMLTags.COLNAME_ATTRIB])
            if col_index >= 2:
                ele_paras = ele_entry.find(p.XMLTags.PARA_TAG)
                header_str += self._get_value_frm_para(ele_paras) + ","

        if len(header_str) > 0:
            return header_str
        else:
            return None

    def _get_column_attrib(self, ele_items):
        """
        Get the column attribute value of the tag

        Args:
            ele_items - tag element
        """
        for attrib, value in ele_items:
            if attrib == p.XMLTags.COLNAME_ATTRIB:
                return value

    def _get_thead_detail_multiple_col(self, table):
        """
        get the model name from table header

        Args:
            table:table from xml element tree
        Return:
            model name from table header
        """
        thead_dict = {}
        ele_tgroup = self._get_tgroup(table)
        ele_thead = ele_tgroup.find(p.XMLTags.THEAD_TAG)
        if ele_thead is None:
            return None
        ele_row = ele_thead.find(p.XMLTags.ROW_TAG)
        ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
        for ele_entry in ele_entries:
            column_index = self._get_column_attrib(ele_entry.items())
            ele_para = ele_entry.find(p.XMLTags.PARA_TAG)
            thead_dict[column_index] = self._get_value_frm_para(ele_para)

        return thead_dict

    def get_table_key_values(self, table):
        """
        prepare the key-value pair from table element

        Args:
            table: table element
        Return:
            key_value_pair dict
        """
        key_value_pair = {}
        value_list = []
        key_flag = False
        key = ""
        ele_tgroup = self._get_tgroup(table)

        prd_type = self.get_product_type()

        if (prd_type == p.GenericProductNameMapping.REFRIGERATOR_GEN_NAME) or \
                (prd_type == p.GenericProductNameMapping.MICROWAVE_OVEN_GEN_NAME):
            logger.debug('no of cols : %s', self.no_of_cols)
            return self.get_table_key_value(table, ele_tgroup)
        else:
            ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
            ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
            for row in ele_rows:
                for ele_entry in row.findall(p.XMLTags.ENTRY_TAG):
                    ele_items = ele_entry.items()
                    for attrib, value in ele_items:
                        if attrib == p.COLNAME_ATTRIB:
                            if value == "1":
                                key_flag = True
                            else:
                                key_flag = False
                    ele_paras = ele_entry.findall(p.XMLTags.PARA_TAG)
                    text = ""
                    value_list = []
                    if len(ele_paras) > 1:
                        for ele_para in ele_paras:
                            value_list.append(self._get_value_frm_para(ele_para))
                    else:
                        if key_flag:
                            text = self._get_value_frm_para(ele_paras[0])
                        else:
                            value_list.append(self._get_value_frm_para(ele_paras[0]))
                    if key_flag:
                        key = text
                    else:
                        if len(key) > 0:
                            key_value_pair[key] = value_list
            logger.debug('get_table_key_values key_value_pair : %s', key_value_pair)
            return self._get_thead_detail(table), key_value_pair

    def get_table_key_value(self, table, ele_tgroup):
        """
        get key-value pair from table element

        Args:
            table: lxml element of table
            ele_tgroup : lxml element of tgroup tag

        Return:
            key_value pair of table
        """
        mul_model = False
        model_1 = ""
        model_2 = ""
        value_list = []
        key_value_pair = defaultdict(dict)
        key_flag = False
        internal_key = None
        key = ""
        header_dict = self._get_thead_detail_multiple_col(table)
        logger.debug('header_dict : ', header_dict)
        ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
        ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
        for row in ele_rows:
            for ele_entry in row.findall(p.XMLTags.ENTRY_TAG):
                ele_items = ele_entry.items()
                for attrib, value in ele_items:
                    if attrib == p.COLNAME_ATTRIB:
                        if value == "1":
                            key_flag = True
                        else:
                            key_flag = False
                            internal_key = value
                            logger.debug('internal key : %s', internal_key)

                text = ""
                value_list = []
                ele_paras = ele_entry.findall(p.XMLTags.PARA_TAG)
                if len(ele_paras) > 1:
                    if key_flag:
                        mul_model = True
                    else:
                        mul_model = False
                    for ele_para in ele_paras:
                        value_list.append(self._get_value_frm_para(ele_para))
                else:
                    if key_flag:
                        text = self._return_regex_truncated_model_no(self._get_value_frm_para(ele_paras[0]))
                    else:
                        value_list.append(self._get_value_frm_para(ele_paras[0]))

                if key_flag:
                    if mul_model is True:
                        model_1 = self._return_regex_truncated_model_no(value_list[0])
                        model_2 = self._return_regex_truncated_model_no(value_list[1])
                    else:
                        model_1 = text
                    logger.debug('ModelNo : %s', model_1)
                    model_1 = self._return_regex_truncated_model_no(model_1)
                else:
                    if len(model_1) > 0:
                        int_key = header_dict[internal_key]
                        key_value_pair[model_1][int_key] = value_list
                        if mul_model is True:
                            key_value_pair[model_2][int_key] = value_list

            if self.electrical_req_key is not None:
                key_value_pair[model_1][self.electrical_req_key] = [self.evalue.strip()]
            if self.water_pressure_key is not None:
                key_value_pair[model_1][self.water_pressure_key] = [self.wvalue.strip()]
            if self.power_supply_key is not None:
                key_value_pair[model_1][self.power_supply_key] = [self.power_supply_value]
            if self.rated_pwr_consumption_key is not None:
                key_value_pair[model_1][self.rated_pwr_consumption_key] = [self.rated_pwr_consumption_value]
            if self.microwave_ot_key is not None:
                key_value_pair[model_1][self.microwave_ot_key] = [self.microwave_ot_value]
            if self.rated_current_key is not None:
                key_value_pair[model_1][self.rated_current_key] = [self.rated_current_value]

            if mul_model is True:
                if self.electrical_req_key is not None:
                    key_value_pair[model_2][self.electrical_req_key] = [self.evalue.strip()]
                if self.water_pressure_key is not None:
                    key_value_pair[model_2][self.water_pressure_key] = [self.wvalue.strip()]
                if self.power_supply_key is not None:
                    key_value_pair[model_2][self.power_supply_key] = [self.power_supply_value]
                if self.rated_pwr_consumption_key is not None:
                    key_value_pair[model_2][self.rated_pwr_consumption_key] = [self.rated_pwr_consumption_key_value]
                if self.microwave_ot_key is not None:
                    key_value_pair[model_2][self.microwave_ot_key] = [self.microwave_ot_value]
                if self.rated_current_key is not None:
                    key_value_pair[model_2][self.rated_current_key] = [self.rated_current_value]

        logger.debug('Final key_value_pair : %s', dict(key_value_pair))
        return None, dict(key_value_pair)

    def get_spec_detail(self):
        """
        get the specification section in generic json format
        """
        self.etree = self.parse_file(self.file_path)
        return self._get_section_generic(p.SPEC_SECTION)


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    specxml_extract = SpecificationXMLExtractor(r"<path_to_xml>\us_main.book.xml")
    print(specxml_extract.get_spec_detail())
