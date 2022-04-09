"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""

from constants import params as p


class SpecificationTableValidator(object):
    """
    class used to validate the xml structure of the specification content
    """

    def _get_value_frm_para(self, para):
        """
        parse para element and frame text

        Args:
            para: para element
        Return:
            text
        """
        return "".join(para.itertext())

    def validate_spec_content(self, tag):
        """
        validate the specification content

        Args:
            tag - lxml element of the specification section topic
        Return:
            True - If content is valid structure
            False - If content is not valid structure
        """
        ele_table = tag.find(p.XMLTags.TABLE_TAG)

        if ele_table is not None:
            col_validation = self._validate_spectablecol(ele_table)
            col_header_validation = self._validate_col_header(ele_table)
            return col_validation & col_header_validation
        else:
            ele_simplesect = tag.find(p.XMLTags.SIMPLESECT_TAG)
            ele_table = ele_simplesect.find(p.XMLTags.TABLE_TAG)
            if ele_table is not None:
                return self._validate_spectablecol(ele_table)
            return False

    def _validate_spectablecol(self, tag):
        """
        validate the number of columns in a specification table

        Args:
            tag - lxml element of the table element

        Return:
            True - If no.of.column >= 2 and <= 4
            False - If the condition is failed
        """
        col_number = 0
        ele_tgroup = tag.find(p.XMLTags.TGROUP_TAG)
        ele_attribs = ele_tgroup.items()
        for attrib, value in ele_attribs:
            if attrib == p.XMLTags.COL_ATTRIB:
                col_number = int(value)
                break
        if (col_number >= 2) and (col_number <= 4):
            return True
        else:
            return False

    def _validate_col_header(self, tag):
        """
        validate the model string as header in first column

        Args:
            tag - lxml element of the table element

        Return:
             True - If model string as header
             False - If condition as fails
        """
        flag = False
        ele_tgroup = tag.find(p.XMLTags.TGROUP_TAG)
        ele_thead = ele_tgroup.find(p.XMLTags.THEAD_TAG)

        if ele_thead is None:
            return self._identify_first_row_header(tag)

        ele_row = ele_thead.find(p.XMLTags.ROW_TAG)
        ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
        header_entry = None
        for ele_entry in ele_entries:
            ele_attribs = ele_entry.items()
            for attrib, value in ele_attribs:
                if attrib == p.XMLTags.COLNAME_ATTRIB:
                    col_number = int(value)
                    if col_number == 1:
                        header_entry = ele_entry
                        break
            if header_entry is not None:
                flag = self._validate_header_entry(header_entry)

        return flag

    def _validate_header_entry(self, header_entry):
        """
        validate the header entry

        Args:
            header_entry: thead lxml element of table
        return:
            flag : True if supported
                   False If not
        """
        MODEL_STR = 'model'
        flag = False
        ele_para = header_entry.find(p.XMLTags.PARA_TAG)
        header_str = self._get_value_frm_para(ele_para)
        if header_str.lower() == MODEL_STR:
            flag = True

        return flag

    def _identify_first_row_header(self, tag):
        """
        validate the model string in first row first column

        Args:
            tag - lxml element of table tag
        Return:
            True - If model string as header
            False - If condition as fails
        """
        MODEL_STR = 'model'
        flag = False
        ele_tgroup = tag.find(p.XMLTags.TGROUP_TAG)
        ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
        ele_row = ele_tbody.find(p.XMLTags.ROW_TAG)
        ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
        header_entry = None
        for ele_entry in ele_entries:
            ele_attribs = ele_entry.items()
            for attrib, value in ele_attribs:
                if attrib == p.XMLTags.COLNAME_ATTRIB:
                    col_number = int(value)
                    if col_number == 1:
                        header_entry = ele_entry
                        break

            if header_entry is not None:
                flag = self._validate_header_entry(header_entry)
                break
        return flag
