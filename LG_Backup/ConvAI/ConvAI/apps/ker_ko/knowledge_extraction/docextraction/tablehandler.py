# -*- coding: utf-8 -*-
"""
 * Copyright (c) 2020 LG Electronics Inc.
 * SPDX-License-Identifier: LicenseRef-LGE-Proprietary
 *
 * This program or software including the accompanying associated documentation
 * (“Software”) is the proprietary software of LG Electronics Inc. and or its
 * licensors, and may only be used, duplicated, modified or distributed pursuant
 * to the terms and conditions of a separate written license agreement between you
 * and LG Electronics Inc. (“Authorized License”). Except as set forth in an
 * Authorized License, LG Electronics Inc. grants no license (express or implied),
 * rights to use, or waiver of any kind with respect to the Software, and LG
 * Electronics Inc. expressly reserves all rights in and to the Software and all
 * intellectual property therein. If you have no Authorized License, then you have
 * no rights to use the Software in any ways, and should immediately notify LG
 * Electronics Inc. and discontinue all use of the Software.

@author: senthil.sk@lge.com
"""
from docx import Document
import sys
import os

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')))
from .triplet import Triplet
from .extraction import DocxTableExtractor


class TableInfoExtractor:

    """
       Extracting the key-value pair from the table object
       @method get_info : extract the key-value pair from table obj
    """

    def __init__(self):
        self.triplet_list = []  # used to hold list triplet object
        self.triplet_dict = {}  # used to hold keyvalue pair as dictionary

    def _get_key_column_index(self, table):
        """get cell_index of the key from header row of the table"""
        index = [0]
        cell_0 = table.rows[0].cells[0].text
        for cell_idx in range(len(table.rows[0].cells)):
            if cell_idx != 0:
                cell_val = table.rows[0].cells[cell_idx].text
                if cell_val == cell_0:
                    index.append(cell_idx)
        return index

    def _get_value_column_index(self, table, index_arr):
        """get value_index from the header row"""
        value_index = []
        previous_txt = ""
        list = []
        for cell_idx in range(len(table.rows[0].cells)):
            if cell_idx not in index_arr:
                cur_text = table.rows[0].cells[cell_idx].text
                if cur_text == previous_txt:
                    list.append(cell_idx)
                else:
                    if len(list) != 0:
                        value_index.append(list)
                    list = []
                    list.append(cell_idx)
                previous_txt = cur_text
        if len(list) != 0:
            value_index.append(list)
        return value_index

    def _get_key_str(self, table, cell_idx, value_index):
        """get node name(model name) name from 1st row"""
        for list in value_index:
            if cell_idx in list:
                return table.rows[0].cells[cell_idx].text
        return ""

    def _get_value(self, table, row_idx, cell_idx, value_index):
        """get tail node name from corresponding row_idx"""
        for list in value_index:
            if cell_idx in list:
                return table.rows[row_idx].cells[cell_idx].text
        return ""

    def _get_key_value(self, table, row_idx, index_arr):
        """get relationship name and property from corresponding row
        :param row_idx : row index
        :param index_arr : value column index list
        @return : key and property
        """
        key = table.rows[row_idx].cells[0].text
        property = ""
        for i in index_arr:
            if key != table.rows[row_idx].cells[i].text:
                property += table.rows[row_idx].cells[i].text

        return key, property

    def _get_triplet(self, table):
        """prepare triplet list from the table object
        :param table :table object from the Document
        :@return : list of triplet object
        """
        key_col_index = self._get_key_column_index(table)
        value_index = self._get_value_column_index(table, key_col_index)
        triplet_obj = Triplet()
        for row_idx in range(len(table.rows)):
            if row_idx == 0:
                continue
            for cell_idx in range(len(table.rows[row_idx].cells)):
                if cell_idx in key_col_index:
                    continue
                elif len(self._get_value(table, row_idx, cell_idx, value_index)) != 0:
                    triplet_obj.set_head_node(self._get_key_str(table, cell_idx, value_index))
                    triplet_obj.set_relationShip_node(self._get_key_value(table, row_idx, key_col_index)[0])
                    triplet_obj.set_relationship_property(self._get_key_value(table, row_idx, key_col_index)[1])
                    triplet_obj.set_tail_node(self._get_value(table, row_idx, cell_idx, value_index))
                    if (triplet_obj.check_triplets() == 1) and (triplet_obj is not None):
                        self.triplet_list.append(triplet_obj)
                        triplet_obj = Triplet()
        return self.triplet_list

    def get_info(self, section, table):
        """
           Get the key-value pair using _get_keyvalue_pair_from_table
           :param section : section name of the table
           :param table: table object
           @return : key-value pair
        """
        if section == 'Specification':
            return self._get_keyvalue_pair_from_table(table)

        elif section == 'Troubleshooting':
            return self._get_troubleshooting_info(table)

    def _get_troubleshooting_info(self, table):
        pass

    def _get_specification_info(self, table):
        """prepare key-value pair from the table object
        :param table:table object from the Document
        :@return : list of key value pairs from the table
        """
        key_col_idx = self._get_key_column_index(table)
        value_idx = self._get_value_column_index(table, key_col_idx)

        for row_idx in range(len(table.rows)):
            key = ""
            property = ""

            for cell_idx in range(len(table.rows[row_idx].cells)):
                if cell_idx in key_col_idx:
                    if cell_idx == 0:
                        key = table.rows[row_idx].cells[cell_idx].text
                    else:
                        property = property + table.rows[row_idx].cells[cell_idx].text + " "
                elif (len(self._get_value(table, row_idx, cell_idx, value_idx)) != 0) and (len(key) != 0):
                    if key.strip() == property.strip() or (len(property.strip()) == 0):
                        if key in self.triplet_dict:
                            self.triplet_dict[key] = self.triplet_dict[key] + "," + self._get_value(table, row_idx,
                                                                                                    cell_idx,
                                                                                                    value_idx)
                        else:
                            self.triplet_dict[key] = self._get_value(table, row_idx, cell_idx, value_idx)
                    else:
                        if (key + "{" + property + "}") in self.triplet_dict:
                            self.triplet_dict[key + "{" + property.strip() + "}"] = self.triplet_dict[key + "{" + property + "}"] \
                                                                                    + "," + self._get_value(table, row_idx, cell_idx, value_idx)
                        else:
                            self.triplet_dict[key + "{" + property.strip() + "}"] = self._get_value(table, row_idx,
                                                                                                    cell_idx,
                                                                                                    value_idx)
        return self.triplet_dict

    def _init_triplet_keyvaluepair(self, table, key_col_idx):
        """
        initialize the triplet_dict variable for list of keys
        """
        for cell_idx in range(len(table.rows[0].cells)):
            if cell_idx in key_col_idx:
                continue
            else:
                key = table.rows[0].cells[cell_idx].text.strip()
                if key not in self.triplet_dict:
                    self.triplet_dict[key] = {}

    def _get_dict_for_key(self, key):
        return self.triplet_dict[key]

    def _get_triplet_keyvaluepair(self, table):
        """prepare keyvaluepair list from the table object
        :param table :table object from the Document
        :@return :list of keyvalue pairs for table object
        """
        key_col_idx = self._get_key_column_index(table)
        value_idx = self._get_value_column_index(table, key_col_idx)
        self._init_triplet_keyvaluepair(table, key_col_idx)

        for row_idx in range(len(table.rows)):
            if row_idx == 0:
                continue
            for cell_idx in range(len(table.rows[row_idx].cells)):
                if cell_idx in key_col_idx:
                    continue
                elif len(self._get_value(table, row_idx, cell_idx, value_idx)) != 0:
                    dict = self._get_dict_for_key(self._get_key_str(table, cell_idx, value_idx))
                    key = self._get_key_value(table, row_idx, key_col_idx)[0]
                    property = self._get_key_value(table, row_idx, key_col_idx)[1]
                    value = self._get_value(table, row_idx, cell_idx, value_idx)

                    if (key != property) and (len(property.strip()) > 0):
                        dict[key + "{" + property + "}"] = value
                    else:
                        dict[key] = value

        return self.triplet_dict

    def _get_keyvalue_pair_from_table(self, table):
        """get keyvalue pair from table using _get_triplet_keyvaluepair method
        :param table: docx package table object
        :@return :list of keyvalue pairs for table object
        """
        key_value_pairs = self._get_triplet_keyvaluepair(table)
        return key_value_pairs

    def _get_triplet_from_table(self, table_name, table):
        """get triplet from file
        :param table_name : name of the table
        :param table: docx package table object
        :return : list of triplet objects
        """
        triplet_dict = {}
        triplet_list = self._get_triplet(table)
        triplet_dict[table_name] = triplet_list
        return triplet_dict


if __name__ == "__main__":

    table_info_extract = TableInfoExtractor()

    table_extract = DocxTableExtractor()
    dict = table_extract.get_all_tables(sys.argv[1])
    keys = dict.keys()
    for key in keys:
        key_value_pair = table_info_extract.get_info(key, dict[key])
        print(str(key_value_pair))
