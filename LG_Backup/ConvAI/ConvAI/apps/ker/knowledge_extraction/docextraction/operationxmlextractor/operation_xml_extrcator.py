# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""

import logging as logger

from constants import params as p
from docextraction.operationxmlextractor.operationextractorutility import OperationExtractorUtility
from docextraction.operationxmlextractor.operationtable_extractor import OperationTableExtractor
from docextraction.operationxmlextractor.operationtable_format_validator import OperationTableValidator
from docextraction.operationxmlextractor.post_processing_operation_data import PostProcessOprData
from docextraction.xml_extractor import XMLExtractor


class OperationXMLExtractor(XMLExtractor):
    """
    Class is used to get the operation section data in the required json format
    This class extends super class XMLExtractor

    @method:get_operation_data(self): get the operation section data in required json format
    """

    def __init__(self, file_path):
        self.oprtableformatvalidator = OperationTableValidator()
        self.operationextractorutility = OperationExtractorUtility(file_path)
        self.oprtableextractor = OperationTableExtractor(file_path)
        super(OperationXMLExtractor, self).__init__(file_path)

    def _extract_from_table(self, table):
        # reference format = self.oprtableformatvalidator.get_format_type(table)
        tbl_format = ""
        return self.oprtableextractor.extract_info_from_table(table, tbl_format)

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
                prereq_children = children.getchildren()
                summary = self._extract_summ_prerequisties(prereq_children, summary)
            if children.tag == p.XMLTags.PARA_TAG:
                if p.DESCRIPTION_KEY not in summary:
                    summary[p.DESCRIPTION_KEY] = []
                summary[p.DESCRIPTION_KEY].append(
                    self._do_preprocessing(self.operationextractorutility.get_value_frm_para(children)))
            if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                summary[p.DESCRIPTION_POINTS] = self.operationextractorutility.extract_from_itemizedlist(children)
        return summary

    def _extract_summ_prerequisties(self, prereq_children, summary):
        """
        extract the content inside the summary tag

        Args:
            prereq_children: prerequisites tag lxml element
            summary:dict need to be filled
        return:
            summary dict
        """
        for p_child in prereq_children:
            if p_child.tag == p.XMLTags.CAUTION_TAG:
                summary[p.XMLTags.PREREQUISITES_TAG][
                    p.XMLTags.CAUTION_TAG] = self.operationextractorutility.extract_from_caution(
                    p_child)
            if p_child.tag == p.XMLTags.WARNING_TAG:
                summary[p.XMLTags.PREREQUISITES_TAG][
                    p.XMLTags.WARNING_TAG] = self.operationextractorutility.extract_from_warning(
                    p_child)
            if p_child.tag == p.XMLTags.PARA_TAG:
                if p.DESCRIPTION_KEY not in summary[p.XMLTags.PREREQUISITES_TAG]:
                    summary[p.XMLTags.PREREQUISITES_TAG][p.DESCRIPTION_KEY] = []
                summary[p.XMLTags.PREREQUISITES_TAG][p.DESCRIPTION_KEY].append(
                    self._do_preprocessing(self.operationextractorutility.get_value_frm_para(p_child)))
            if p_child.tag == p.XMLTags.NOTE_TAG:
                summary[p.XMLTags.PREREQUISITES_TAG][
                    p.XMLTags.NOTE_TAG] = self.operationextractorutility.extract_from_note(
                    p_child)
        return summary

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
                        self.operationextractorutility.get_value_frm_para(children))
                elif children.tag == p.XMLTags.CAUTION_TAG:
                    step_dict[p.XMLTags.CAUTION_TAG] = self.operationextractorutility.extract_from_caution(children)
                elif children.tag == p.XMLTags.NOTE_TAG:
                    step_dict[p.XMLTags.NOTE_TAG] = self.operationextractorutility.extract_from_note(children)
                elif children.tag == p.XMLTags.FIGURE_TAG:
                    step_dict.update(self.operationextractorutility.extract_from_figure(children, self.file_path))
                elif children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                    step_dict[p.DESCRIPTION_POINTS] = self.operationextractorutility.extract_from_itemizedlist(children)
                elif children.tag == p.XMLTags.TABLE_TAG:
                    if p.TABLE_DETAILS not in step_dict:
                        step_dict[p.TABLE_DETAILS] = []
                    step_dict[p.TABLE_DETAILS].append(self._extract_from_table(children))
                elif children.tag == p.XMLTags.VAR_LIST_TAG:
                    step_dict[p.XMLTags.ENTRY_TAG] = self.operationextractorutility.extract_from_variablelist(children)

            procedure.append(step_dict)

        return procedure

    def _extract_from_variablelist_listitem(self, tag):
        extract_json = {}
        all_children = tag.getchildren()
        for children in all_children:
            if children.tag == p.XMLTags.PARA_TAG:
                para_text = self.operationextractorutility.get_value_frm_para(children)
                if p.DESCRIPTION_KEY not in extract_json:
                    extract_json[p.DESCRIPTION_KEY] = []
                extract_json[p.DESCRIPTION_KEY].append(para_text)
            elif children.tag == p.XMLTags.FIGURE_TAG:
                extract_json.update(self.operationextractorutility.extract_from_figure(children, self.file_path))
            elif children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                if p.DESCRIPTION_POINTS not in extract_json:
                    extract_json[p.DESCRIPTION_POINTS] = []
                extract_json[p.DESCRIPTION_POINTS] += self.operationextractorutility.extract_from_itemizedlist(children)

            self._extract_variable_list_child(children, extract_json)
        return extract_json

    def _extract_variable_list_child(self, children, extract_json):
        """
        Extract the childern under the variablist tag

        Args:
            children: childern under the varialbelist
            extract_json: extracted json need to filled
        """
        if children.tag == p.XMLTags.CAUTION_TAG:
            extract_json[p.XMLTags.CAUTION_TAG] = self.operationextractorutility.extract_from_caution(children)
        elif children.tag == p.XMLTags.PROCEDURE_TAG:
            extract_json[p.XMLTags.PROCEDURE_TAG] = self._extract_from_procedure(children)
        elif children.tag == p.XMLTags.TABLE_TAG:
            if p.TABLE_DETAILS not in extract_json:
                extract_json[p.TABLE_DETAILS] = []
            extract_json[p.TABLE_DETAILS].append(self._extract_from_table(children))

    def _extract_from_topic_variablelist(self, tag):
        extract_json = {}
        ele_varlistentries = tag.findall(p.XMLTags.VAR_LIST_ENTRY_TAG)
        for ele_varlistentry in ele_varlistentries:
            all_children = ele_varlistentry.getchildren()
            for children in all_children:
                if children.tag == p.XMLTags.TERM_TAG:
                    key_text = "".join(children.itertext())
                    extract_json[key_text] = {}
                elif children.tag == p.XMLTags.LISTITEM_TAG:
                    extract_json[key_text].update(self._extract_from_variablelist_listitem(children))
                elif children.tag == p.XMLTags.CAUTION_TAG:
                    extract_json[key_text][p.XMLTags.CAUTION_TAG] = self.operationextractorutility.extract_from_caution(
                        children)
        return extract_json

    def _extract_from_simplesect(self, tag):
        """
        extact from the simple section tags

        Args:
            tag : lxml element of the simplesect tag

        Return:
            dict of the simplesection content
        """
        section_dict = {}
        topic_title = ""
        all_childern = tag.getchildren()
        for children in all_childern:
            topic_title, section_dict = self._extract_simplesect_child(children, section_dict, topic_title)
            topic_title, section_dict = self._extract_simplesect_child2(children, section_dict, topic_title)

        return topic_title, section_dict

    def _extract_simplesect_child2(self, children, section_dict, topic_title):
        if children.tag == p.XMLTags.NOTE_TAG:
            if p.XMLTags.NOTE_TAG not in section_dict[topic_title]:
                section_dict[topic_title][p.XMLTags.NOTE_TAG] = self.operationextractorutility.extract_from_note(
                    children)
            else:
                section_dict[topic_title][p.XMLTags.NOTE_TAG].extend(
                    self.operationextractorutility.extract_from_note(children))
        if children.tag == p.XMLTags.TABLE_TAG:
            if p.TABLE_DETAILS not in section_dict[topic_title]:
                section_dict[topic_title][p.TABLE_DETAILS] = []
            section_dict[topic_title][p.TABLE_DETAILS].append(self._extract_from_table(children))
        if children.tag == p.XMLTags.PARA_TAG:
            if p.DESCRIPTION_KEY not in section_dict[topic_title]:
                section_dict[topic_title][p.DESCRIPTION_KEY] = []
            section_dict[topic_title][p.DESCRIPTION_KEY].append(
                self._do_preprocessing(self.operationextractorutility.get_value_frm_para(children)))
        if children.tag == p.XMLTags.PROCEDURE_TAG:
            logger.debug("before procedure : %s", section_dict)
            section_dict[topic_title][p.XMLTags.PROCEDURE_TAG] = self._extract_from_procedure(children)
            logger.debug("proc dict : %s", self._extract_from_procedure(children))
            logger.debug("after procedure : %s", section_dict)
        if children.tag == p.XMLTags.SUMMARY_TAG:
            section_dict[topic_title][p.XMLTags.SUMMARY_TAG] = self._extract_from_summary(children)

        return topic_title, section_dict

    def _extract_simplesect_child(self, children, section_dict, topic_title):
        if children.tag == p.XMLTags.TITLE_TAG:
            topic_title = "".join([text for text in children.itertext() if text != "TM"])
            logger.debug("topic title : %s", topic_title)
            topic_title = self._do_preprocessing(topic_title)
            section_dict[topic_title] = {}
        if children.tag == p.XMLTags.WARNING_TAG:
            previous_tag = p.XMLTags.WARNING_TAG
            section_dict[topic_title][
                p.XMLTags.WARNING_TAG] = self.operationextractorutility.extract_from_warning(children)
        if children.tag == p.XMLTags.CAUTION_TAG:
            section_dict[topic_title][p.XMLTags.CAUTION_TAG] = self.operationextractorutility.extract_from_caution(
                children)
        if children.tag == p.XMLTags.FIGURE_TAG:
            feature_dict = self.operationextractorutility.extract_from_figure(children, self.file_path)
            if feature_dict is not None:
                section_dict[topic_title].update(feature_dict)
        if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
            if p.DESCRIPTION_POINTS not in section_dict[topic_title]:
                section_dict[topic_title][
                    p.DESCRIPTION_POINTS] = self.operationextractorutility.extract_from_itemizedlist(children)
            else:
                section_dict[topic_title][p.DESCRIPTION_POINTS].extend(
                    self.operationextractorutility.extract_from_itemizedlist(children))
        return topic_title, section_dict

    def _extract_from_topic(self, tag):
        """
        extract the content from the topic tag

        Args:
            tag - lxml element of the topic tag
        Return:
            dict - content inside the topic tag
        """
        previous_tag = None
        previous_title = None
        topic_dict = {}
        topic_title = ""
        all_childern = tag.getchildren()
        for children in all_childern:
            try:
                if children.tag == p.XMLTags.VAR_LIST_TAG:
                    topic_dict[topic_title].update(self._extract_from_topic_variablelist(children))
                elif children.tag == p.XMLTags.TITLE_TAG:
                    previous_tag = p.XMLTags.TITLE_TAG
                    topic_title = "".join([text for text in children.itertext() if text != "TM"])
                    logger.debug("topic title : %s", topic_title)
                    topic_title = self._do_preprocessing(topic_title)
                    topic_dict[topic_title] = {}
                elif children.tag == p.XMLTags.CAUTION_TAG:
                    previous_tag = p.XMLTags.CAUTION_TAG
                    topic_dict[topic_title][
                        p.XMLTags.CAUTION_TAG] = self.operationextractorutility.extract_from_caution(children)
                elif children.tag == p.XMLTags.WARNING_TAG:
                    previous_tag = p.XMLTags.WARNING_TAG
                    topic_dict[topic_title][
                        p.XMLTags.WARNING_TAG] = self.operationextractorutility.extract_from_warning(children)
                elif children.tag == p.XMLTags.FIGURE_TAG:
                    previous_tag = p.XMLTags.FIGURE_TAG
                    feature_dict = self.operationextractorutility.extract_from_figure(children, self.file_path)
                    if feature_dict is not None:
                        topic_dict[topic_title].update(feature_dict)
                previous_tag, topic_title, topic_dict = self._extract_topic_child2(children, previous_tag, topic_dict,
                                                                                   topic_title)
                previous_tag, topic_title, topic_dict, previous_title = self._extract_topic_child3(children,
                                                                                                   previous_tag,
                                                                                                   previous_title,
                                                                                                   topic_dict,
                                                                                                   topic_title)
            except Exception as e:
                logger.exception("Exception in extraction : " + str(e))
                logger.error('Error in extracting %s \n Exception: %s', topic_title, e)

        return topic_dict

    def _extract_topic_child2(self, children, previous_tag, topic_dict, topic_title):
        if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
            previous_tag = p.XMLTags.ITEMIZEDLIST_TAG
            if p.DESCRIPTION_POINTS not in topic_dict[topic_title]:
                topic_dict[topic_title][
                    p.DESCRIPTION_POINTS] = self.operationextractorutility.extract_from_itemizedlist(children)
            else:
                topic_dict[topic_title][p.DESCRIPTION_POINTS].extend(
                    self.operationextractorutility.extract_from_itemizedlist(children))
        if children.tag == p.XMLTags.TABLE_TAG:
            logger.debug("topic title :%s", topic_title)
            previous_tag = p.XMLTags.TABLE_TAG
            if p.TABLE_DETAILS not in topic_dict[topic_title]:
                topic_dict[topic_title][p.TABLE_DETAILS] = []
            topic_dict[topic_title][p.TABLE_DETAILS].append(self._extract_from_table(children))
        if children.tag == p.XMLTags.PARA_TAG:
            previous_tag = p.XMLTags.PARA_TAG
            if p.DESCRIPTION_KEY not in topic_dict[topic_title]:
                topic_dict[topic_title][p.DESCRIPTION_KEY] = []
            topic_dict[topic_title][p.DESCRIPTION_KEY].append(
                self._do_preprocessing(self.operationextractorutility.get_value_frm_para(children)))
        if children.tag == p.XMLTags.PROCEDURE_TAG:
            previous_tag = p.XMLTags.PROCEDURE_TAG
            logger.debug("before procedure : %s", topic_dict)
            topic_dict[topic_title][p.XMLTags.PROCEDURE_TAG] = self._extract_from_procedure(children)
            logger.debug("proc dict : %s", self._extract_from_procedure(children))
            logger.debug("after procedure : %s", topic_dict)
        if children.tag == p.XMLTags.VAR_LIST_TAG:
            previous_tag = p.XMLTags.PROCEDURE_TAG

        return previous_tag, topic_title, topic_dict

    def _extract_topic_child3(self, children, previous_tag, previous_title, topic_dict, topic_title):
        """
        extract from summary,note, simplesect tag

        Args:
            children:children lxml element under topic tag
            previous_tag: previously handled lxml element tag
            previous_title: previous tag title
            topic_dict:
            topic_title:
        :return:
        """
        if children.tag == p.XMLTags.SUMMARY_TAG:
            previous_tag = p.XMLTags.SUMMARY_TAG
            topic_dict[topic_title][p.XMLTags.SUMMARY_TAG] = self._extract_from_summary(children)
        if children.tag == p.XMLTags.NOTE_TAG:
            if previous_tag == p.XMLTags.SIMPLESECT_TAG:
                if p.XMLTags.NOTE_TAG not in topic_dict[topic_title][previous_title]:
                    topic_dict[topic_title][previous_title][
                        p.XMLTags.NOTE_TAG] = self.operationextractorutility.extract_from_note(children)
                else:
                    topic_dict[topic_title][previous_title][p.XMLTags.NOTE_TAG].extend(
                        self.operationextractorutility.extract_from_note(children))
            else:
                if p.XMLTags.NOTE_TAG not in topic_dict[topic_title]:
                    topic_dict[topic_title][p.XMLTags.NOTE_TAG] = self.operationextractorutility.extract_from_note(
                        children)
                else:
                    topic_dict[topic_title][p.XMLTags.NOTE_TAG].extend(
                        self.operationextractorutility.extract_from_note(children))
            previous_tag = p.XMLTags.NOTE_TAG
        if children.tag == p.XMLTags.SIMPLESECT_TAG:
            previous_tag = p.XMLTags.SIMPLESECT_TAG
            title, content = self._extract_from_simplesect(children)
            previous_title = title
            topic_dict[topic_title].update(content)

        return previous_tag, topic_title, topic_dict, previous_title

    def _extract_from_chapter(self, tag):
        """
        extract the content inside the chapter tag

        Args:
             tag - lxml object of chapter tag
        Return:
            dict - content inside chapter tag
        """
        final_dict = {}
        main_key = ""
        section_key = ""
        all_children = tag.getchildren()
        for children in all_children:
            if children.tag == p.XMLTags.SECTION_TAG:
                # childern of chapter tag (section tag)
                s_all_children = children.getchildren()
                for s_childern in s_all_children:
                    # title of the section tag
                    logger.debug('child : %s', s_childern.tag)
                    final_dict, section_key = self._extract_chapter_child(final_dict, main_key, s_childern, section_key)
            if children.tag == p.XMLTags.TITLE_TAG:
                main_key = p.ExtractionConstants.SECTION_NAME_TRANSLATE[children.text]
                final_dict[main_key] = {}

        return final_dict, main_key

    def _extract_chapter_child(self, final_dict, main_key, s_childern, section_key):
        if s_childern.tag == p.XMLTags.TITLE_TAG:
            section_key = s_childern.text
            final_dict[main_key][section_key] = {}
        if s_childern.tag == p.XMLTags.TOPIC_TAG:
            final_dict[main_key][section_key].update(self._extract_from_topic(s_childern))
        if s_childern.tag == p.XMLTags.SUMMARY_TAG:
            final_dict[main_key][section_key][p.XMLTags.SUMMARY_TAG] = self._extract_from_summary(
                s_childern)
        return final_dict, section_key

    def _get_section(self, section_title):
        """
        get the parent tag of requied section title

        Args:
            section_title: section title reuqired to identify
        Return:
            key-value pair of the section
        """
        title_list = [title.lower() for title in p.ExtractionConstants.SECTION_NAMING_LIST[section_title]]
        tag_str, tag = self._find_chapters(title_list)
        logger.debug('OPERATION : (%s)', tag_str)
        if tag_str is not p.XMLTags.UNKNOWN_TAG:
            if tag_str == p.XMLTags.TOPIC_TAG:
                key_value_pair, key = self._extract_from_topic(tag)

            elif tag_str == p.XMLTags.CHAPTER_TAG:
                key_value_pair, key = self._extract_from_chapter(tag)

            elif tag_str == p.XMLTags.SECTION_TAG:
                key_value_pair, key = self._extract_from_section(tag)

            entity_dict = {}
            entity_dict[p.ENTITY_PRD_TYPE] = self.get_ent_prd_type(section_title, self.get_product_type())
            key_value_pair.update(entity_dict)
            return key_value_pair, key
        else:
            return None, None

    def get_operation_data(self):
        """
        get the overall json for the operation section

        Return:
            dict - overall content
        """
        self.etree = self.parse_file(self.file_path)
        response_json = {}
        section_data, key = self._get_section(p.OPERATION)
        logger.debug('section_data : %s', section_data)
        if section_data is not None:
            post_process = PostProcessOprData()
            logger.debug("file_path opr : %s", self.file_path)
            framed_dict = {}
            framed_dict[p.PRODUCT_TYPE_KEY] = self.get_product_type()
            model_nos = self.get_buyermodel()
            framed_dict[p.MODELS_KEY] = self._get_regex_model_list(model_nos)
            framed_dict[p.PARTNUMBER] = self.get_partnumber()
            framed_dict[p.COMMON_INFO_KEY] = {}
            framed_dict[p.COMMON_INFO_KEY][p.DATA_KEY] = []
            logger.debug("section_data : %s",section_data)
            framed_dict[p.COMMON_INFO_KEY][p.DATA_KEY].append(post_process.post_process_data(section_data))
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.SUCCESS]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.DATA_KEY] = framed_dict
        else:
            response_json = {}
            ext_error_code = p.ExternalErrorCode.internal_to_ext_err_code[p.ResponseCode.SECTION_NOT_AVAILABLE]
            response_json[p.ExtractionConstants.STATUS_STR] = ext_error_code
            response_json[p.ExtractionConstants.ERR_MG] = p.ExternalErrorMsgs.ERR_MSGS[ext_error_code][
                p.ExternalErrorMsgs.MSG]
        return response_json


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    opr_xml_extract = OperationXMLExtractor(
        r"<path_to_xml>\us_main.book.xml")
    print(opr_xml_extract.get_operation_data())
