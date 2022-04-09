# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""

import logging as logger
import re

from constants import params as p
from docextraction.xml_extractor import XMLExtractor
from docextraction.troubleshootingextractorutility import TroubleshootingExtractorUtility

class TroubleshootingXMLExtractor(XMLExtractor):
    """
    This class is used to extract the troubleshooting section from the
    XML, this class extends the super class XMLExtractor

    @method:get_troubleshooting_data(self): get the troubleshooting section
                                            data in required json format
    """

    def __init__(self, file_path):
        self.trobextractorutility = TroubleshootingExtractorUtility(file_path)
        super(TroubleshootingXMLExtractor, self).__init__(file_path)

    def _extract_from_caution(self, tag):
        """
        extract content from the caution tag

        Args:
            tag - lxml element of caution tag
        Return:
            items inside the caution tag as List
        """
        caution_list = []
        all_childern = tag.getchildren()

        for childern in all_childern:
            if childern.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                caution_list += self._extract_from_itemizedlist(childern)

        return caution_list

    def _extract_from_note(self, tag):
        """
        extract content from the note tag

        Args:
            tag - lxml element of note tag
        Return:
            items inside the note tag as List
        """
        note_list = []
        all_childern = tag.getchildren()

        for childern in all_childern:
            if childern.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                note_list += self._extract_from_itemizedlist(childern)

        return note_list

    def _get_value_frm_para(self, para):
        """
        parse para element and frame text

        Args:
            para: para element
        Return:
            text
        """
        return "".join(para.itertext())

    def _extract_from_topic(self, ele_topic):
        """
        extract the details from topic element

        Args:
            ele_topic: topic element from xml element tree
        Return:
            details as dict
        """
        key_value_pairs = {}
        for child in ele_topic:
            if child.tag == p.XMLTags.TABLE_TAG:
                trouble_faq_extract = self.TroubleshootingFAQExtractor(self)
                key_value_pairs[
                    self._return_regex_truncated_model_no(
                        self.get_buyermodel())] = trouble_faq_extract.get_table_key_values(
                    child)
                key = self._return_regex_truncated_model_no(self.get_buyermodel())
                return key_value_pairs, key
            elif child.tag == p.XMLTags.TROUBLESHOOT_TAG:
                trouble_shoot_extract = self.TroubleShootingProbCauseExtract(self)
                key_value_pairs[self._return_regex_truncated_model_no(
                    self.get_buyermodel())] = trouble_shoot_extract.get_from_troubleshoot(child)
                key = self._return_regex_truncated_model_no(self.get_buyermodel())
                return key_value_pairs, key

        return None, None

    def _extract_from_appendix(self, ele_appendix):
        """
        preare the key_value pair of <appendix> tag

        Args:
            ele_appendix: <appendix> tag as lxml element
        Return:
            key-value pair as dict
        """
        key_value_pair = {}
        ele_sections = ele_appendix.findall(p.XMLTags.SECTION_TAG)
        section_dict = {}
        for ele_section in ele_sections:
            ele_title = ele_section.find(p.XMLTags.TITLE_TAG)
            section_title = ele_title.text
            ele_topics = ele_section.findall(p.XMLTags.TOPIC_TAG)
            topic_dict = {}
            for ele_topic in ele_topics:
                ele_title = ele_topic.find(p.XMLTags.TITLE_TAG)
                topic_title_txt = ele_title.text
                topic_content, key = self._extract_from_topic(ele_topic)
                if topic_content is not None:
                    topic_dict[topic_title_txt] = topic_content[key]
                else:
                    topic_dict[topic_title_txt] = []
            section_dict[section_title] = topic_dict
        key_value_pair[self._return_regex_truncated_model_no(self.get_buyermodel())] = section_dict
        key = self._return_regex_truncated_model_no(self.get_buyermodel())
        return key_value_pair, key

    def _get_tag_title(self, tag):
        """
        Get the title text of given tag

        Args:
            tag - lxml element of tag

        Return:
            title text
        """
        ele_title = tag.find(p.XMLTags.TITLE_TAG)
        logger.debug('topic title : (%s)', ele_title)
        if ele_title is not None:
            return ele_title.text
        else:
            return "Sub_Section"

    def _extract_from_itemizedlist(self, tag):
        """
        extract the text from the itemizedlist tag and frame the list

        Args:
            tag - lxml element of itemizedlist tag
        Return:
            Items inside as List
        """
        list_items = []
        ele_listitems = tag.findall(p.XMLTags.LISTITEM_TAG)
        for ele_listitem in ele_listitems:
            all_children = ele_listitem.getchildren()
            for children in all_children:
                if children.tag == p.XMLTags.PARA_TAG:
                    list_items.append(self._do_preprocessing(self._get_value_frm_para(children)))
                if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                    list_items += self._extract_from_itemizedlist(children)

        return list_items


    def _extract_from_procedure(self, tag):
        """
        extract the content from the procedure tag

        Args:
            tag:lxml instance of the summary tag

        Return:
             list of steps in procedure
        """
        procedure = []
        steps = tag.findall(p.XMLTags.STEP_TAG)

        for step in steps:
            step_dict = {}
            all_childern = step.getchildren()
            for children in all_childern:
                if children.tag == p.XMLTags.PARA_TAG:
                    step_dict[p.XMLTags.STEP_TAG] = self._do_preprocessing(
                        self.trobextractorutility.get_value_frm_para(children))
                elif children.tag == p.XMLTags.CAUTION_TAG:
                    step_dict[p.XMLTags.CAUTION_TAG] = self.trobextractorutility.extract_from_caution(children)
                elif children.tag == p.XMLTags.NOTE_TAG:
                    step_dict[p.XMLTags.NOTE_TAG] = self.trobextractorutility.extract_from_note(children)
                elif children.tag == p.XMLTags.FIGURE_TAG:
                    step_dict.update(self.trobextractorutility.extract_from_figure(children, self.file_path))
                elif children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                    step_dict[p.DESCRIPTION_POINTS] = self.trobextractorutility.extract_from_itemizedlist(children)
            procedure.append(step_dict)

        return procedure


    # for reference def _extract_from_procedure(self, tag):
    #     """
    #     extract the content from the procedure tag
    #
    #     Args:
    #         tag:lxml instance of the summary tag
    #
    #     Return:
    #          list of steps in procedure
    #     """
    #     procedure = []
    #     steps = tag.findall(p.XMLTags.STEP_TAG)
    #
    #     for step in steps:
    #         step_dict = {}
    #         all_childern = step.getchildren()
    #         for children in all_childern:
    #             if children.tag == p.XMLTags.PARA_TAG:
    #                 step_dict[p.XMLTags.STEP_TAG] = self._do_preprocessing(self._get_value_frm_para(children))
    #             if children.tag == p.XMLTags.CAUTION_TAG:
    #                 step_dict[p.XMLTags.CAUTION_TAG] = self._extract_from_caution(children)
    #             if children.tag == p.XMLTags.NOTE_TAG:
    #                 step_dict[p.XMLTags.NOTE_TAG] = self._extract_from_note(children)
    #         procedure.append(step_dict)
    #
    #     return procedure

    def _extract_from_topic_generic(self, ele_topic):
        """
        extract the details from topic element

        Args:
            ele_topic: topic element from xml element tree
        Return:
            details as dict
        """
        data = {}
        data_list = []
        title = self._get_tag_title(ele_topic)
        for child in ele_topic:
            if child.tag == p.XMLTags.TABLE_TAG:
                trouble_faq_extract = self.TroubleshootingFAQExtractor(self)
                # if len(data.keys()) == 0:
                if len(data) == 0:
                    data = trouble_faq_extract.get_table_key_values(child)
                    logger.debug("FAQ data :%s", data)
                else:
                    if type(data) is dict:
                        data.update(trouble_faq_extract.get_table_key_values(child))
                    elif type(data) is list:
                        data.append(trouble_faq_extract.get_table_key_values(child))

            elif child.tag == p.XMLTags.TROUBLESHOOT_TAG:
                trouble_shoot_extract = self.TroubleShootingProbCauseExtract(self)
                logger.debug("prob_cause data :%s", data)
                # if len(data.keys()) == 0:
                data_list = self._extract_troubleshoot_list(child, data_list, trouble_shoot_extract)

            self._handle_topic_child(child, data)
            # for future reference elif child.tag == p.XMLTags.PROCEDURE_TAG:
            #     data[p.XMLTags.PROCEDURE_TAG] = self._extract_from_procedure(child)
            # elif child.tag == p.XMLTags.PARA_TAG:
            #     if p.DESCRIPTION_KEY not in data:
            #         data[p.DESCRIPTION_KEY] = []
            #     data[p.DESCRIPTION_KEY].append(self._get_value_frm_para(child))
            # elif child.tag == p.XMLTags.ITEMIZEDLIST_TAG:
            #     if p.DESCRIPTION_KEY not in data:
            #         data[p.DESCRIPTION_KEY] = self._extract_from_itemizedlist(child)
            #     else:
            #         data[p.DESCRIPTION_KEY].extend(self._extract_from_itemizedlist(child))
            # else:
            #     continue

        logger.debug("extracted type :%s", data)

        return self._validate_and_send_extract_resp(data, data_list, title)

    def _extract_troubleshoot_list(self, child, data_list, trouble_shoot_extract):
        if len(data_list) == 0:
            data_list = trouble_shoot_extract.get_from_troubleshoot(child)
            logger.debug("troubleshoot data : %s", data_list)
        else:
            data_list = data_list + trouble_shoot_extract.get_from_troubleshoot(child)
        return data_list

    def _validate_and_send_extract_resp(self, data, data_list, title):
        """
        validate and send reponse based on extract response

        Args:
            data: extracted data
            data_list: extracted troubleshoot list item
            title: section title
        return:
            data: extracted data
            title: section title
        """
        if len(data) > 0:
            return data, title
        elif len(data_list) > 0:
            return data_list, title
        else:
            return None, None

    def _handle_topic_child(self, child, data):
        """
        handle child inside the topic tag

        Args:
            child:topic lxml element
            data: dictionary need to be filled
        """
        if child.tag == p.XMLTags.PROCEDURE_TAG:
            data[p.XMLTags.PROCEDURE_TAG] = self._extract_from_procedure(child)
        elif child.tag == p.XMLTags.PARA_TAG:
            if p.DESCRIPTION_KEY not in data:
                data[p.DESCRIPTION_KEY] = []
            data[p.DESCRIPTION_KEY].append(self._get_value_frm_para(child))
        elif child.tag == p.XMLTags.ITEMIZEDLIST_TAG:
            if p.DESCRIPTION_KEY not in data:
                data[p.DESCRIPTION_KEY] = self._extract_from_itemizedlist(child)
            else:
                data[p.DESCRIPTION_KEY].extend(self._extract_from_itemizedlist(child))

    def _extract_from_summary(self, tag):
        """
        extract the content from the summary xml tag

        Args:
            tag : lxml element of the summary tag
        Return:
            content in dict format
        """
        summary = {}
        all_children = tag.getchildren()

        for children in all_children:
            if children.tag == p.XMLTags.PREREQUISITES_TAG:
                summary[p.XMLTags.PREREQUISITES_TAG] = {}
                self._extract_prereqistes_childern(children, summary)
            elif children.tag == p.XMLTags.PARA_TAG:
                if p.DESCRIPTION_KEY not in summary:
                    summary[p.DESCRIPTION_KEY] = []
                summary[p.DESCRIPTION_KEY].append(self._do_preprocessing(self._get_value_frm_para(children)))
        return summary

    def _extract_prereqistes_childern(self, children, summary):
        prereq_children = children.getchildren()
        for p_child in prereq_children:
            if p_child.tag == p.XMLTags.CAUTION_TAG:
                summary[p.XMLTags.PREREQUISITES_TAG][p.XMLTags.CAUTION_TAG] = self._extract_from_caution(
                    p_child)
            elif p_child.tag == p.XMLTags.PARA_TAG:
                if p.DESCRIPTION_KEY not in summary[p.XMLTags.PREREQUISITES_TAG]:
                    summary[p.XMLTags.PREREQUISITES_TAG][p.DESCRIPTION_KEY] = []
                summary[p.XMLTags.PREREQUISITES_TAG][p.DESCRIPTION_KEY].append(
                    self._do_preprocessing(self._get_value_frm_para(p_child)))
            elif p_child.tag == p.XMLTags.NOTE_TAG:
                summary[p.XMLTags.PREREQUISITES_TAG][p.XMLTags.NOTE_TAG] = self._extract_from_note(
                    p_child)

    def _extract_data_from_tag(self, ele_appendix):
        """
        preare the key_value pair of <appendix> tag

        Args:
            ele_appendix: <appendix> tag as lxml element
        Return:
            key-value pair as dict
        """
        response_json = {}
        for ele_appendix_item in ele_appendix:
            ele_title = ele_appendix_item.find(p.XMLTags.TITLE_TAG)
            appendix_title_txt = ele_title.text
            ele_sections = ele_appendix_item.findall(p.XMLTags.SECTION_TAG)
            framed_dict = {}

            if self._get_lang_detail() == p.XMLTags.KOREAN_LANG:
                appendix_title_txt = p.ExtractionConstants.SECTION_NAME_TRANSLATE[appendix_title_txt]

            framed_dict[appendix_title_txt] = {}

            prd_type, sub_prd_type = self.get_product_type()
            framed_dict[appendix_title_txt][p.PRODUCT_TYPE_KEY] = prd_type
            framed_dict[appendix_title_txt][p.SUB_PRD_TYPE_KEY] = sub_prd_type
            model_nos = self.get_buyermodel()
            framed_dict[appendix_title_txt][p.MODELS_KEY] = self._get_regex_model_list(model_nos)
            framed_dict[appendix_title_txt][p.PARTNUMBER] = self.get_partnumber()
            framed_dict[appendix_title_txt][p.COMMON_INFO_KEY] = {}
            framed_dict[appendix_title_txt][p.COMMON_INFO_KEY][p.DATA_KEY] = []
            section_dict = {}

            for ele_section in ele_sections:
                ele_title = ele_section.find(p.XMLTags.TITLE_TAG)
                section_title = ele_title.text

                logger.debug("section name : %s %s", section_title, section_title == "고장 진단하기")

                if self._get_lang_detail() == p.XMLTags.KOREAN_LANG:
                    section_title = p.ExtractionConstants.SECTION_NAME_TRANSLATE[section_title]

                ele_topics = ele_section.findall(p.XMLTags.TOPIC_TAG)
                section_dict[section_title] = {}

                ele_summary = ele_section.find(p.XMLTags.SUMMARY_TAG)
                if ele_summary is not None:
                    section_dict[section_title][p.XMLTags.SUMMARY_TAG] = self._extract_from_summary(ele_summary)

                for ele_topic in ele_topics:
                    title = self._get_tag_title(ele_topic)

                    if title in p.ExtractionConstants.SKIP_SECTION:
                        continue

                    topic_content, topic_key = self._extract_from_topic_generic(ele_topic)
                    if self._get_lang_detail() == p.XMLTags.KOREAN_LANG:
                        topic_key = p.ExtractionConstants.SECTION_NAME_TRANSLATE[topic_key]
                    logger.debug("topic_key : %s", topic_key)
                    if topic_content is not None:
                        section_dict[section_title][topic_key] = topic_content
                        logger.debug("section_dict : %s", section_dict)

            framed_dict[appendix_title_txt][p.COMMON_INFO_KEY][p.DATA_KEY].append(dict(section_dict))

        ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.SUCCESS]
        response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
        response_json[p.ExtractionConstants.DATA_KEY] = framed_dict
        return response_json

    def _extract_from_section(self, ele_section):
        """
        Extrcat from give section tag

        Args:
            ele_section:lxml element of section tag
        """
        for child in ele_section:
            if child.tag == p.XMLTags.TOPIC_TAG:
                return self._extract_from_topic(child)

    def _get_section(self, section_title):
        """
        get the parent tag of requied section title

        Args:
            section_title: section title reuqired to identify
        Return:
            key-value pair of the section
        """
        title_list = [title.lower() for title in p.ExtractionConstants.SECTION_NAMING_LIST[section_title]]
        tag_str, tag = self._find_appendix(title_list)
        logger.debug('FAQ : (%s)', tag_str)
        if tag_str is not p.XMLTags.UNKNOWN_TAG:
            if tag_str == p.XMLTags.TOPIC_TAG:
                key_value_pair, key = self._extract_from_topic(tag)
                return key_value_pair, key
            elif tag_str == p.XMLTags.APPENDIX_TAG:
                key_value_pair, key = self._extract_from_appendix(tag)
                return key_value_pair, key
            elif tag_str == p.XMLTags.SECTION_TAG:
                key_value_pair, key = self._extract_from_section(tag)
                return key_value_pair, key
        else:
            return None, None

    def _frame_json(self, key_value_pair, key):
        """
        Frame final json response for troubleshooting
        problem cause and solution

        Return:
            framed json
        """
        framed_dict = {}

        if key_value_pair is not None:
            prd_type, sub_prd_type = self.get_product_type()
            framed_dict[p.PRODUCT_TYPE_KEY] = prd_type
            framed_dict[p.SUB_PRD_TYPE_KEY] = sub_prd_type
            model_nos = self.get_buyermodel()
            framed_dict[p.MODELS_KEY] = self._get_regex_model_list(model_nos)
            framed_dict[p.DATA_KEY] = key_value_pair[key]
            return framed_dict
        else:
            return None

    def _frame_faq_json(self, key_value_pair, key):
        """
        Frame final json response for troubleshooting
        problem cause and solution

        Return:
            framed json
        """
        framed_dict = {}

        if key_value_pair is not None:
            prd_type, sub_prd_type = self.get_product_type()
            framed_dict[p.PRODUCT_TYPE_KEY] = prd_type
            framed_dict[p.SUB_PRD_TYPE_KEY] = sub_prd_type
            model_nos = self.get_buyermodel()
            framed_dict[p.MODELS_KEY] = self._get_regex_model_list(model_nos)
            framed_dict[p.DATA_KEY] = [key_value_pair[key]]
            return framed_dict
        else:
            return None

    def _find_troubleshooting_section(self):
        """
        find the tag of the troubleshooting section

        Return:
            tag_str - tag_name
            tag - lxml element of tag
        """
        section = p.TROB_SECTION
        tag_str, tag = self._find_preface(p.ExtractionConstants.SECTION_NAMING_LIST[section])
        if tag_str is p.XMLTags.UNKNOWN_TAG:
            tag_str, tag = self._find_chapters(p.ExtractionConstants.SECTION_NAMING_LIST[section])
            logger.debug("troubleshooting : %s", tag_str)
            if tag_str is p.XMLTags.UNKNOWN_TAG:
                tag_str, tag = self._find_appendix(p.ExtractionConstants.SECTION_NAMING_LIST[section])

        return tag_str, tag

    def _frame_trob_json(self, key_value_pair, framed_dict):
        """
        Frame final json for troubleshooting

        Return:
            framed json
        """

        if key_value_pair is not None:
            prd_type, sub_prd_type = self.get_product_type()
            framed_dict[p.PRODUCT_TYPE_KEY] = prd_type
            framed_dict[p.SUB_PRD_TYPE_KEY] = sub_prd_type
            model_nos = self.get_buyermodel()
            framed_dict[p.MODELS_KEY] = self._get_regex_model_list(model_nos)
            framed_dict[p.COMMON_INFO_KEY] = {}
            if p.DATA_KEY not in framed_dict[p.COMMON_INFO_KEY]:
                framed_dict[p.COMMON_INFO_KEY][p.DATA_KEY] = []
                framed_dict[p.COMMON_INFO_KEY][p.DATA_KEY].append(key_value_pair)
            else:
                framed_dict[p.COMMON_INFO_KEY][p.DATA_KEY].append(key_value_pair)

            return framed_dict
        else:
            return None

    def get_troubleshooting_data(self):
        """
        get the overall troubleshhoting data

        Return:
            key-value pair of troubleshooting data
        """
        self.etree = self.parse_file(self.file_path)
        tag_str, tag = self._find_troubleshooting_section()
        if tag_str is not p.XMLTags.UNKNOWN_TAG:
            return self._extract_data_from_tag(tag)
        else:
            response_json = {}
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.SECTION_NOT_AVAILABLE]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][
                p.ExternalErrorMsgs.MSG]
            return response_json

    class TroubleshootingFAQExtractor:

        """
        this class is used to extract troubleshooting FAQ table
        @method:get_table_key_values(table) - prepare key_value_pair from
                                              <table> tag
        """

        def __init__(self, outer_inst):
            self.no_of_cols = 0
            self.outer_cls = outer_inst

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
            col_name = ""
            thead_detail = {}
            ele_tgroup = self._get_tgroup(table)
            ele_thead = ele_tgroup.find(p.XMLTags.THEAD_TAG)
            if ele_thead is None:
                return None
            ele_row = ele_thead.find(p.XMLTags.ROW_TAG)
            ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
            for ele_entry in ele_entries:
                items = ele_entry.items()
                for attrib, value in items:
                    if attrib == p.XMLTags.COLNAME_ATTRIB:
                        col_name = value
                ele_para = ele_entry.find(p.XMLTags.PARA_TAG)
                thead_detail[col_name] = self._get_value_frm_para(ele_para)

            if len(thead_detail.keys()) > 0:
                return thead_detail
            else:
                return None

        def get_custom_table_key_values(self, table):
            key_value_pair = {}
            ele_tgroup = self._get_tgroup(table)
            ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
            thead_detail = self._get_thead_detail(table)

            ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)

            entries = []
            last_value = ""
            for ele_row in ele_rows:
                entry = {}
                ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)

                for ele_entry in ele_entries:
                    items = ele_entry.items()
                    for attrib, value in items:
                        if attrib == p.XMLTags.COLNAME_ATTRIB:
                            col_name = value

                    last_value = self._get_value_frm_para(ele_entry.find(p.XMLTags.PARA_TAG))
                    entry[thead_detail[col_name]] = last_value

                logger.debug("range: %s", range((self.no_of_cols - len(ele_entries)) - 1))

                self._fill_merged_col_details(ele_entries, entry, last_value, thead_detail)

                entries.append(entry)

            key_value_pair['entries'] = entries
            return key_value_pair

        def _fill_merged_col_details(self, ele_entries, entry, last_value, thead_detail):
            remaining_fill = []
            if len(ele_entries) < self.no_of_cols:
                for idx in range(self.no_of_cols - len(ele_entries)):
                    logger.debug("idx : %s", idx)
                    remaining_fill.append(str(len(ele_entries) + (idx + 1)))
            if len(remaining_fill) > 0:
                for col in remaining_fill:
                    entry[thead_detail[col]] = last_value

        def get_table_key_values(self, table):
            """
            prepare the key-value pair from table element

            Args:
                table: table element
            Return:
                key_value_pair dict
            """
            key_value_pair = {}
            key_flag = False
            value_flag = False
            key = ""
            ele_tgroup = self._get_tgroup(table)

            if self.no_of_cols == 2:  # Extract the Q&A from FAQ
                ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
                ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
                for row in ele_rows:
                    for ele_entry in row.findall(p.XMLTags.ENTRY_TAG):
                        ele_paras = ele_entry.findall(p.XMLTags.PARA_TAG)
                        if len(ele_paras) > 0:
                            for ele_para in ele_paras:
                                text = self._get_value_frm_para(ele_para)
                                if (text == "Q:") or (text == "Q"):
                                    key_flag = True
                                    value_flag = False
                                    logger.debug("key text Q identified")
                                elif (text == "A:") or (text == "A"):
                                    value_flag = True
                                    key_flag = False
                                    logger.debug("value text A identified")
                                elif key_flag:
                                    key = self.outer_cls._do_preprocessing(text)
                                    logger.debug("key = %s", key)
                                elif value_flag:
                                    value = self.outer_cls._do_preprocessing(text)
                                    logger.debug("value = %s", value)
                                    if len(key) > 0:
                                        if key not in key_value_pair:
                                            logger.debug('key not present')
                                            key_value_pair[key] = []
                                            key_value_pair[key].append(value)
                                        else:
                                            key_value_pair[key].append(value)
                                    logger.debug('key_value_pair = %s', key_value_pair)
                        else:
                            logger.debug("itemized list entering : %s , %s, %s", key_flag, value_flag, key)
                            ele_itemized_list = ele_entry.find(p.XMLTags.ITEMIZEDLIST_TAG)
                            ele_listitems = ele_itemized_list.findall(p.XMLTags.LISTITEM_TAG)
                            logger.debug("ele_listitem : %s , %s", ele_listitems, len(ele_listitems))
                            for ele_listitem in ele_listitems:
                                ele_para = ele_listitem.find(p.XMLTags.PARA_TAG)
                                text = self.outer_cls._do_preprocessing(self._get_value_frm_para(ele_para))
                                if key_flag:
                                    key += text + ""
                                    logger.debug("key = %s", key)
                                elif value_flag:
                                    logger.debug("key_value_pair : %s", key_value_pair)
                                    if len(key) > 0:
                                        if key not in key_value_pair:
                                            logger.debug('key not present')
                                            key_value_pair[key] = []
                                            key_value_pair[key].append(text)
                                        else:
                                            key_value_pair[key].append(text)

                return key_value_pair
            else:
                return self.get_custom_table_key_values(table)

    class TroubleShootingProbCauseExtract:

        """
        This class is used to iterate the over the troubleshoot tag
        and get the section details

        @method:get_from_troubleshoot(ele_troubleshoot):
                    iterate through the <troubleshoot> tag
                    and get the details as dict
        """

        def __init__(self, outer_inst):
            self.outer_cls = outer_inst
            regex = "((?<![\-])[A-Z]+([0-9]|[A-Z])(?![\-+]))"
            self.error_code_regex = re.compile(regex, flags=re.IGNORECASE)

        def _get_value_frm_para(self, para):
            """
            parse para element and frame text
            Args:
                para: para element
            Return:
                para element and frame text
            """
            return self.outer_cls._do_preprocessing("".join((para.itertext())))

        def _get_all_troublelistentry(self, ele_troubleshoot):
            """
            get all <troublelistentry> child under <troubleshoot> tag
            Args:
                ele_troubleshoot:<troubleshoot> tag as lxml element
            Return:
                all <troublelistentry> as lxml element
            """
            ele_troublellistentries = ele_troubleshoot.findall(p.XMLTags.TROUBLELIST_ENTRY_TAG)
            return ele_troublellistentries

        def _find_error_codes(self, problem_string):
            """
            find the list of error codes in the error code string separated with comma or space

            Args:
                problem_string:error code string
            Return:
                err_code: erro codes separated by comma
            """
            err_code = None
            result = self.error_code_regex.findall(problem_string)
            err_list = [error_codes for error_codes, _ in result]

            if len(err_list) > 0:
                err_code = ",".join(err_list)
            return err_code


        def _get_problem_text(self, ele_troublelistentry):
            """
            get the text from the <problem> under <troublelistentry> tag
            Args:
                ele_troublelistentry:<troublelistentry> tag as lxml element
            Return:
                text from the <problem> under <troublelistentry> tag
            """
            ele_problem = ele_troublelistentry.find(p.XMLTags.PROBLEM_TAG)
            ele_paras = ele_problem.findall(p.XMLTags.PARA_TAG)

            if len(ele_paras) > 1:
                error_code = ""
                error_desc = ""
                for index in range(len(ele_paras)):
                    ele_para = ele_paras[index]
                    if index == 0:
                        error_code = self.outer_cls._do_preprocessing(self._get_value_frm_para(ele_para).strip())
                        logger.debug("before mapped : %s",error_code)
                        error_code = p.ExtractionConstants.map_error_code(error_code)
                        logger.debug("after mapped : %s", error_code)
                    else:
                        error_desc = self.outer_cls._do_preprocessing(self._get_value_frm_para(ele_para).strip())
                error_code = self._find_error_codes(error_code)
                return error_desc, error_code

            error_codes = p.ExtractionConstants.map_error_code(self._get_value_frm_para(ele_paras[0]))
            processed_error_codes = self._find_error_codes(error_codes)

            if processed_error_codes is not None:
                return processed_error_codes, ""
            return error_codes, ""

        def _get_from_reason_tag(self, ele_reason):
            """
            get the text from the <reason> tag
            Args:
                ele_reason: <reason> tag lxml element
            Return:
                text from the <reason> tag
            """
            text = []
            ele_paras = ele_reason.findall(p.XMLTags.PARA_TAG)
            for ele_para in ele_paras:
                text.append(self.outer_cls._do_preprocessing(self._get_value_frm_para(ele_para)))
            return text

        def _get_frm_solution(self, ele_solution):
            """
            get all the string under the <solution>
            Args:
                ele_solution: <solution> tag as lxml element
            Return:
                list of solutions strings
            """
            sol_list = []
            ele_itemizedlist = ele_solution.findall(p.XMLTags.ITEMIZEDLIST_TAG)
            for ele_itemizeditem in ele_itemizedlist:
                ele_listitems = ele_itemizeditem.findall(p.XMLTags.LISTITEM_TAG)
                for ele_listitem in ele_listitems:
                    for child in ele_listitem:
                        sol_list.append(self.outer_cls._do_preprocessing("".join(child.itertext())))
            return sol_list

        def _get_from_troublelistitem(self, ele_troublelistitem):
            """
            prepare solutions under <troublelistitem> tag as a list
            Args:
                ele_troublelistitem:<troublelistitem> as lxml element
            Return:
                solutions as list
            """
            key_value_pairs = []
            ele_reason = ele_troublelistitem.find(p.XMLTags.REASON_TAG)
            if ele_reason is not None:
                reasons = self._get_from_reason_tag(ele_reason)

                for reason in reasons:
                    key_value_pair = {}
                    key_value_pair[p.REASON_KEY] = reason
                    ele_solution = ele_troublelistitem.find(p.XMLTags.SOLUTION_TAG)
                    solution_list = self._get_frm_solution(ele_solution)
                    key_value_pair[p.SOLUTION_KEY] = solution_list
                    key_value_pairs.append(key_value_pair)
            else:
                key_value_pair = {}
                key_value_pair[p.REASON_KEY] = ""
                ele_solution = ele_troublelistitem.find(p.XMLTags.SOLUTION_TAG)
                solution_list = self._get_frm_solution(ele_solution)
                key_value_pair[p.SOLUTION_KEY] = solution_list
                key_value_pairs.append(key_value_pair)
            return key_value_pairs

        def _get_from_troublelistentry(self, ele_troublelistentry):
            """
            prepare reason solution key-value pair from <troublelistentry>
            tag
            Args:
                ele_troublelistentry:<troublelistentry> tag as lxml element
            Return:
                dict - reason-solution
            """
            key_value_pairs = {}
            reason_solution_list = []
            error_desc, error_key = self._get_problem_text(ele_troublelistentry)
            ele_troublelistitems = ele_troublelistentry.findall(p.XMLTags.TROUBLELISTITEM_TAG)
            for ele_troublelistitem in ele_troublelistitems:
                reason_solution_list.extend(self._get_from_troublelistitem(ele_troublelistitem))

            if len(error_key) > 0:
                key_value_pairs[error_key] = {}
                key_value_pairs[error_key][p.DESC_KEY] = error_desc
                key_value_pairs[error_key][p.CAUSES_SOL_KEY] = reason_solution_list
            else:
                key_value_pairs[error_desc] = {}
                key_value_pairs[error_desc][p.CAUSES_SOL_KEY] = reason_solution_list

            return key_value_pairs

        def get_from_troubleshoot(self, ele_troubleshoot):
            """
            prepare troubleshoot reason and solution section wise
            Args:
                ele_troubleshoot: <troubleshooting> tag as lxml element
            Return:
                  dict - troubleshoot section
            """
            troubleshoot_list = []
            ele_troublelistentries = self._get_all_troublelistentry(ele_troubleshoot)
            for ele_troublelistentry in ele_troublelistentries:
                troubleshoot_list.append(self._get_from_troublelistentry(ele_troublelistentry))
            return troubleshoot_list


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    trob_xml_extract = TroubleshootingXMLExtractor(r"<path_to_xml>\us_main.book.xml")
    print(trob_xml_extract.get_troubleshooting_data())
