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
from .operationextractorutility import OperationExtractorUtility


class OperationTableExtractor(object):
    """
    class used to extract the different table format from the operation section

    @method: extract_info_from_table(table, type): extract table based on format type
    @class: Format1TableExtractor : used to extract the format1 type of table
    @class: TableWithTheadExtractor: used to extract the table with header detail
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.operationxml_extract_utility = OperationExtractorUtility(file_path)

    def extract_info_from_table(self, table, type):
        """
        extract details from the table tag

        Args:
            table:lxml element of table tag
            type: format type of table
        return:
            extracted table detail dict
        """
        tablewiththeadextract = self.TableWithTheadExtractor(self.operationxml_extract_utility, self.file_path)
        return tablewiththeadextract.extract_from_table(table)
        # For reference if type == "format_1":
        #     format1extractor = self.Format1TableExtractor(self.operationxml_extract_utility, self.file_path)
        #     return format1extractor.extract_format_1_table(table)
        # else:
        #     tablewiththeadextract = self.TableWithTheadExtractor(self.operationxml_extract_utility, self.file_path)
        #     return tablewiththeadextract.extract_from_table(table)

    class Format1TableExtractor(object):

        """
        class used to extract the format1 type of table

        @method: extract_format_1_table(table): extract detail from the table tag
        """

        def __init__(self, operationxml_extract_utility, file_path):
            self.operationxml_extract_utility = operationxml_extract_utility
            self.file_path = file_path

        def _get_col_attrib(self, tag):
            """
            get the colname attribute of entry tag

            Args:
                tag:lxml element of entry tag
            return:
                colname attribute value
            """
            attrib = tag.items()
            for attrib, value in attrib:
                if attrib == p.XMLTags.COLNAME_ATTRIB:
                    return value
            return None

        def _get_format_1_thead(self, tag):
            """
            extract the thead in dict key-value pair

            Args:
                tag:thead tag lxml element
            return:
                dict of thead detail
            """
            row = tag.find(p.XMLTags.ROW_TAG)
            ele_entries = row.findall(p.XMLTags.ENTRY_TAG)
            detaildict = {}
            key = None
            for ele_entry in ele_entries:
                ele_para = ele_entry.find(p.XMLTags.PARA_TAG)
                para_text = self.operationxml_extract_utility.get_value_frm_para(ele_para)
                col_number = self._get_col_attrib(ele_entry)

                if col_number == "1":
                    detaildict[para_text] = {}
                    key = para_text
                    logger.debug("_get_format_1_thead key : %s", key)
                else:
                    logger.debug("_get_format_1_thead : %s - %s", key, para_text)
                    if (key is not None) and (p.DESCRIPTION_KEY not in detaildict[key]):
                        detaildict[key][p.DESCRIPTION_KEY] = []
                    detaildict[key][p.DESCRIPTION_KEY].append(para_text)

            logger.debug("header dict : %s", detaildict)
            return detaildict

        def _extract_format_1_tbody_entry(self, ele_entry, frame_key, lentry_dict):
            col_attrib = self._get_col_attrib(ele_entry)
            entry_dict = lentry_dict
            key = frame_key
            for idx, child in enumerate(ele_entry.getchildren()):
                if (col_attrib == "1") and (child.tag == p.XMLTags.PARA_TAG):
                    key = self.operationxml_extract_utility.get_value_frm_para(child)
                    logger.debug("_extract_format_1_tbody_entry key : %s", key)
                    entry_dict[key] = {}
                elif child.tag == p.XMLTags.PARA_TAG:
                    if p.DESCRIPTION_KEY not in entry_dict[key]:
                        entry_dict[key][p.DESCRIPTION_KEY] = []
                    entry_dict[key][p.DESCRIPTION_KEY].append(
                        self.operationxml_extract_utility.get_value_frm_para(child))
                elif child.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                    entry_dict[key][p.DESCRIPTION_POINTS] = self.operationxml_extract_utility.extract_from_itemizedlist(
                        child)
            return key, entry_dict

        def _extract_format_1_tbody(self, ele_tbody):
            """
            extract from the table tbody tag

            Args:
                ele_tbody:lxml element of tbody tag
            Return:
                list of extracted detail
            """
            entry_list = []

            for row in ele_tbody.findall(p.XMLTags.ROW_TAG):
                ele_entries = row.findall(p.XMLTags.ENTRY_TAG)
                previous_key = None
                entry_dict = {}
                for ele_entry in ele_entries:
                    key, entry_dict = self._extract_format_1_tbody_entry(ele_entry, previous_key, entry_dict)
                    if not entry_dict[key]:
                        previous_key = key
                entry_list.append(entry_dict)
            logger.debug("_extract_format_1_tbody : %s", entry_list)
            return entry_list

        def extract_format_1_table(self, table):
            """
            extract details from the table tag

            Args:
                table:lxml element of table
            return:
                extracted detail dict
            """
            table_dict = {}
            list_entry = []
            ele_tgroup = table.find(p.XMLTags.TGROUP_TAG)

            children = ele_tgroup.getchildren()

            for child in children:

                if child.tag == p.XMLTags.THEAD_TAG:
                    list_entry.append(self._get_format_1_thead(child))
                if child.tag == p.XMLTags.TBODY_TAG:
                    entry_list = self._extract_format_1_tbody(child)
                    list_entry += entry_list

            table_dict[p.ENTRIES] = list_entry
            return table_dict

    class TableWithTheadExtractor(object):
        """
        class used to extract the table with header details

        @method:extract_from_table(table): used to extract the details from the table
        """

        def __init__(self, operationxml_extract_utility, file_path):
            self.operationxml_extract_utility = operationxml_extract_utility
            self.file_path = file_path

        def _find_all_paras(self, ele_thead_entry):
            thead_str= ""
            ele_paras = ele_thead_entry.findall(p.XMLTags.PARA_TAG)

            for ele_para in ele_paras:
                thead_str += self.operationxml_extract_utility.get_value_frm_para(ele_para)

            return thead_str.strip()

        def _extract_thead_details(self, tag):
            """
            extract the content from the thead tag

            Args:
                tag - lxml element of thead tag
            """
            thead_dict = {}
            col_number = ""
            row = tag.find(p.XMLTags.ROW_TAG)
            ele_entries = row.findall(p.XMLTags.ENTRY_TAG)
            for ele_entry in ele_entries:
                for attrib, value in ele_entry.items():
                    if attrib == p.XMLTags.COLNAME_ATTRIB:
                        col_number = value
                        break
                thead_dict[col_number] = self._find_all_paras(ele_entry)
            logger.debug("thead_dict : %s %s", thead_dict, not thead_dict)
            if not thead_dict:
                return None
            else:
                return thead_dict

        def _get_entry_col_number(self, tag):
            """
            col name attrib value of the entry tag

            Args:
                tag: entry tag lxml element
            return:
                col_name attribute
            """
            for attrib, value in tag.items():
                if attrib == p.XMLTags.COLNAME_ATTRIB:
                    return value
            return -1

        def _extract_frm_entry(self, entry_tag, col_number, internal_key, entry_dict):
            details = entry_dict
            logger.debug('details : %s', details)
            key = p.ENTRY if internal_key is None else internal_key
            entry_children = entry_tag.getchildren()
            for child in entry_children:
                if child.tag == p.XMLTags.PARA_TAG:
                    if col_number == "1":
                        key = self.operationxml_extract_utility.get_value_frm_para(child)
                        details[key] = {}
                    else:
                        if p.DESCRIPTION_KEY not in details[key]:
                            details[key][p.DESCRIPTION_KEY] = []
                        details[key][p.DESCRIPTION_KEY].append(
                            self.operationxml_extract_utility.get_value_frm_para(child))
                if child.tag == p.XMLTags.FIGURE_TAG:
                    details[key].update(self.operationxml_extract_utility.extract_from_figure(child, self.file_path))
            return details, key

        def extract_from_table(self, tag):
            """
            extract content from the table tag

            Args:
                tag - lxml element of the table tag
            Return:
                 dict - content inside as dict format
            """
            thead_detail = {}
            table_dict = {}
            list_entry = []
            pre_row_dict = None
            temp_dict = None
            ele_tgroup = tag.find(p.XMLTags.TGROUP_TAG)
            all_children = ele_tgroup.getchildren()
            for children in all_children:
                if children.tag == p.XMLTags.THEAD_TAG:
                    thead_detail = self._extract_thead_details(children)
                    logger.debug("thead_detail : %s", thead_detail)
                if children.tag == p.XMLTags.TBODY_TAG:
                    ele_rows = children.findall(p.XMLTags.ROW_TAG)
                    for ele_row in ele_rows:
                        ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
                        # frame key-value pair for one row
                        temp_dict = self._extract_entry_in_table(ele_entries, thead_detail)

                        logger.debug("pre_row_dict : %s temp_dict : %s merged_cell : %s", pre_row_dict, temp_dict,
                                     self._check_for_merged_cell(temp_dict, pre_row_dict))

                        if self._check_for_merged_cell(temp_dict, pre_row_dict):
                            temp_dict = self._fill_merged_col_details(temp_dict, pre_row_dict)
                        pre_row_dict = temp_dict
                        if len(temp_dict) > 0:
                            list_entry.append(temp_dict)

                    table_dict[p.ENTRIES] = list_entry
            return table_dict

        def _check_for_merged_cell(self, cur_row, previous_row):

            """
            check for the merged cell based on the previous and current row

            Args:
                cur_row: current row detail filled dict
                previous_row: previous row dict
            return:
                True: if merged column found
                False: If not merged
            """
            if previous_row is None:
                return True
            cur_row_keys = set(cur_row.keys())
            pre_row_keys = set(previous_row.keys())
            logger.debug("cur_row_keys : %s pre_row_keys: %s", cur_row_keys, pre_row_keys)
            diff = list(pre_row_keys - cur_row_keys)
            logger.debug("diff : %s", diff)
            if len(diff) > 0:
                return True

            return False

        def _fill_merged_col_details(self, framed_dict, pre_row_dict):
            """
            fill the merged column detail in a row

            Args:
                framed_dict: framed dict for current row
                pre_row_dict: previous row dict
            return:
                filled dict
            """

            if pre_row_dict is None:
                return framed_dict

            pre_row_keys = set(pre_row_dict.keys())
            framed_dict_col = set(framed_dict.keys())
            missed_columns = list(pre_row_keys - framed_dict_col)

            logger.debug("pre_row_keys : %s , framed_dict_col: %s ", pre_row_keys, framed_dict_col)
            logger.debug("missed_columns : %s", missed_columns)

            for col in missed_columns:
                missed_detail = pre_row_dict[col]
                framed_dict[col] = missed_detail

            return framed_dict

        def _extract_entry_in_table(self, ele_entries, thead_detail):
            """
            extract from the entries inside the rows in table

            Args:
                ele_entries: list of entries inside the row
                temp_dict: dict to be filled
                thead_detail: thead detail of table
            return:
                temp_dict: details filled dict
            """
            temp_dict = {}
            for ele_entry in ele_entries:
                col_number = None
                ele_attribs = ele_entry.items()
                for attrib, value in ele_attribs:
                    if attrib == p.XMLTags.COLNAME_ATTRIB:
                        col_number = value
                entry_all_childern = ele_entry.getchildren()
                temp_dict = self._extract_table_entry_childern(col_number, entry_all_childern, temp_dict, thead_detail)
            return temp_dict

        def _extract_table_entry_childern(self, col_number, entry_all_childern, temp_dict, thead_detail):
            """
            extract the childern inside the entry tag

            Args:
                col_number: col number of entry tag
                entry_all_childern: list if childern under entry tag
                temp_dict: dict to be filled
                thead_detail: thead dict of the table
            return:
                temp_dict: details filled dict
            """

            if len(entry_all_childern) == 0:
                if thead_detail[col_number] not in temp_dict:
                    temp_dict[thead_detail[col_number]] = {}
                if p.DESCRIPTION_KEY not in temp_dict[thead_detail[col_number]]:
                    temp_dict[thead_detail[col_number]][p.DESCRIPTION_KEY] = []
                return temp_dict

            for entry_children in entry_all_childern:
                if entry_children.tag == p.XMLTags.VAR_LIST_TAG:
                    logger.debug("opr list entry : %s",
                                 self.operationxml_extract_utility.extract_from_variablelist(entry_children))
                    # list_entry.append(self._extract_from_variablelist(entry_children))
                    if not thead_detail:
                        temp_dict[p.XMLTags.ENTRY_TAG] = \
                            self.operationxml_extract_utility.extract_from_variablelist(entry_children)
                    else:
                        if thead_detail[col_number] not in temp_dict:
                            temp_dict[thead_detail[col_number]] = {}
                        if p.XMLTags.ENTRY_TAG not in temp_dict[thead_detail[col_number]]:
                            temp_dict[thead_detail[col_number]][p.XMLTags.ENTRY_TAG] = []
                        temp_dict[thead_detail[col_number]][p.XMLTags.ENTRY_TAG].extend(
                                self.operationxml_extract_utility.extract_from_variablelist(
                                entry_children))
                elif entry_children.tag == p.XMLTags.PARA_TAG:
                    logger.debug("para_tag : %s", self.operationxml_extract_utility.get_value_frm_para(entry_children))
                    if not thead_detail:
                        temp_dict[p.DESCRIPTION_KEY] = self.operationxml_extract_utility._do_preprocessing(
                            self.operationxml_extract_utility.get_value_frm_para(entry_children))
                    else:
                        if thead_detail[col_number] not in temp_dict:
                            temp_dict[thead_detail[col_number]] = {}
                        if p.DESCRIPTION_KEY not in temp_dict[thead_detail[col_number]]:
                            temp_dict[thead_detail[col_number]][p.DESCRIPTION_KEY] = []
                        temp_dict[thead_detail[col_number]][p.DESCRIPTION_KEY].append(
                            self.operationxml_extract_utility._do_preprocessing(
                                self.operationxml_extract_utility.get_value_frm_para(entry_children)))
                elif entry_children.tag == p.XMLTags.FIGURE_TAG:
                    if not thead_detail:
                        temp_dict.update(
                            self.operationxml_extract_utility.extract_from_figure(entry_children, self.file_path))
                    else:
                        if thead_detail[col_number] not in temp_dict:
                            temp_dict[thead_detail[col_number]] = {}
                        temp_dict[thead_detail[col_number]].update(
                            self.operationxml_extract_utility.extract_from_figure(entry_children, self.file_path))
                elif entry_children.tag == p.XMLTags.ITEMIZEDLIST_TAG or entry_children.tag == p.XMLTags.ORDEREDLIST_TAG:
                    logger.debug("itemized list : %s", self.operationxml_extract_utility.extract_from_itemizedlist(entry_children))
                    if not thead_detail:
                        temp_dict[p.DESCRIPTION_POINTS] = \
                            self.operationxml_extract_utility.extract_from_itemizedlist(entry_children)
                    else:
                        if thead_detail[col_number] not in temp_dict:
                            temp_dict[thead_detail[col_number]] = {}
                        if p.DESCRIPTION_POINTS not in temp_dict[thead_detail[col_number]]:
                            temp_dict[thead_detail[col_number]][p.DESCRIPTION_POINTS] =[]
                        temp_dict[thead_detail[col_number]][p.DESCRIPTION_POINTS].extend(
                                self.operationxml_extract_utility.extract_from_itemizedlist(entry_children))
                elif entry_children.tag == p.XMLTags.NOTE_TAG:
                    if not thead_detail:
                        temp_dict[p.NOTE]=self.operationxml_extract_utility.extract_from_note(entry_children)
                    else:
                        if thead_detail[col_number] not in temp_dict:
                            temp_dict[thead_detail[col_number]] = {}
                        if p.NOTE not in temp_dict[thead_detail[col_number]]:
                            temp_dict[thead_detail[col_number]][p.NOTE] = []
                        temp_dict[thead_detail[col_number]][p.NOTE] = self.operationxml_extract_utility.extract_from_note(entry_children)

            return temp_dict
