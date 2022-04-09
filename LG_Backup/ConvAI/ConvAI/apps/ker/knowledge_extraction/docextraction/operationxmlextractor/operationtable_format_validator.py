# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""

import logging as logger

from lxml import etree as et

from constants import params as p


class OperationTableValidator(object):
    """
    this class used to identify the format type of the given table lxml element

    @method: get_format_type(table) - used to get the format type for given table tag
    """

    class Constants(object):
        INVALID_FORMAT = "invalid_format"
        FORMAT_1 = "format_1"
        FORMAT_2 = "format_2"

    def _get_col_attrib(self, tag):
        """
        Used to get the colname attribute of the entry tag

        Args:
            tag: entry lxml element
        return:
            colname attribute value
        """
        attrib = tag.items()
        for attrib, value in attrib:
            if attrib == p.XMLTags.COLNAME_ATTRIB:
                return value
        return None

    def get_format_type(self, table):
        """
        USed to get the format type of the given table

        Args:
            table: lxml element of the table

        return:
            format string
        """
        thead_dict = {}
        col_number = ""

        try:
            logger.debug("table : %s", et.tostring(table, pretty_print=True))
            tgroup_tag = table.find(p.XMLTags.TGROUP_TAG)
            thead_tag = tgroup_tag.find(p.XMLTags.THEAD_TAG)
            row = thead_tag.find(p.XMLTags.ROW_TAG)
            ele_entries = row.findall(p.XMLTags.ENTRY_TAG)
            for ele_entry in ele_entries:
                ele_para = ele_entry.find(p.XMLTags.PARA_TAG)
                para_text = "".join(ele_para.itertext())
                logger.debug("cyclce table : %s", para_text)
                if (para_text == 'Cycle') and (self._get_col_attrib(ele_entry) == "1"):
                    return self.Constants.FORMAT_1
            return self.Constants.INVALID_FORMAT
        except Exception as e:
            logger.exception("Exception in table format validator : %s", str(e))
            return self.Constants.INVALID_FORMAT
