import logging as logger
import os
import copy

from constants import params as p
from docextraction.xml_extractor import XMLExtractor
from docextraction.post_processing_operation_data import PostProcessOprData


class OperationXMLExtractor(XMLExtractor):
    """
    Class is used to get the operation section data in the required json format
    This class extends super class XMLExtractor

    @method:get_operation_data(self): get the operation section data in required json format
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

    def _extract_from_caution_itemizedlist(self, tag):
        """
        extract the text from the itemizedlist tag and frame the list

        Args:
            tag - lxml element of itemizedlist tag
        Return:
            Items inside as List
        """
        details = []
        ele_listitems = tag.findall(p.XMLTags.LISTITEM_TAG)
        for ele_listitem in ele_listitems:
            all_children = ele_listitem.getchildren()
            list_items = {}
            for children in all_children:
                if children.tag == p.XMLTags.PARA_TAG:
                    if p.DESCRIPTION_KEY not in list_items:
                        list_items[p.DESCRIPTION_KEY] = []
                    list_items[p.DESCRIPTION_KEY].append(self._do_preprocessing(self._get_value_frm_para(children)))
                if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                    list_items[p.DESCRIPTION_POINTS] = self._extract_from_itemizedlist(children)
                if children.tag == p.XMLTags.FIGURE_TAG:
                    list_items.update(self._extract_from_figure(children))
            details.append(list_items)
        return details

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

    def _extract_from_caution(self, tag):
        """
        extract content from the caution tag

        Args:
            tag - lxml element of caution tag
        Return:
            items inside the caution tag as List
        """
        caution_list = {}
        all_childern = tag.getchildren()

        for childern in all_childern:
            if childern.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                if p.DESCRIPTION_KEY not in caution_list:
                    caution_list[p.DESCRIPTION_POINTS] = []
                caution_list[p.DESCRIPTION_POINTS] += self._extract_from_caution_itemizedlist(childern)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                caution_list.update(self._extract_from_figure(childern))
        return caution_list

    def _extract_from_warning(self, tag):
        """
        extract content from the warning tag

        Args:
            tag - lxml element of warning tag
        Return:
            items inside the warning tag as List
        """
        warning_list = {}
        all_childern = tag.getchildren()

        for childern in all_childern:
            if childern.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                if p.DESCRIPTION_POINTS not in warning_list:
                    warning_list[p.DESCRIPTION_POINTS] = []
                warning_list[p.DESCRIPTION_POINTS] += self._extract_from_caution_itemizedlist(childern)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                warning_list.update(self._extract_from_figure(childern))

        return warning_list

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

        note_details = {}
        for childern in all_childern:
            if childern.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                if p.DESCRIPTION_POINTS not in note_list:
                    note_details[p.DESCRIPTION_POINTS] = []
                note_details[p.DESCRIPTION_POINTS] += self._extract_from_caution_itemizedlist(childern)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                note_details.update(self._extract_from_figure(childern))

        note_list.append(note_details)

        return note_list


    def _get_value_from_callout_listitem(self, tag):
        """
        get content from the listitem tag inside calloutlist tag

        Args:
             tag - lxml object of calloutlist tag
        Return:
            dict of items inside the listitem list
        """
        feature_dict = {}
        feature = None
        explanation = []
        caution = None
        note = None
        all_childern = tag.getchildren()

        for children in all_childern:

            if children.tag == p.XMLTags.PARA_TAG:
                ele_key = children.find(p.XMLTags.KEY_TAG)

                key_text = self._get_key_text(children, ele_key)
                para_text = self._do_preprocessing(self._get_value_frm_para(children))
                logger.debug('ele_key : %s - %s', key_text, para_text)
                if (key_text is not None) and (key_text.strip() == para_text.strip()):
                    feature = self._do_preprocessing(key_text)
                else:
                    explanation.append(self._do_preprocessing(para_text))
            elif children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                explanation = self._extract_from_itemizedlist(children)
            elif children.tag == p.XMLTags.CAUTION_TAG:
                caution = self._extract_from_caution(children)
            elif children.tag == p.XMLTags.NOTE_TAG:
                note = self._extract_from_note(children)

        if feature is not None:
            feature_dict[p.FEATURE] = feature
            feature_dict[p.EXPLANATION] = explanation
        else:
            feature_dict[p.FEATURE] = explanation[0]
            feature_dict[p.EXPLANATION] = []

        if caution is not None:
            feature_dict[p.CAUTION] = caution
        if note is not None:
            feature_dict[p.NOTE] = note

        return feature_dict

    def _get_key_text(self, children, ele_key):
        key_text = None
        if ele_key is not None:
            key_text = self._do_preprocessing("".join(ele_key.itertext()))
        elif ele_key is None:
            ele_emphasis = children.find(p.XMLTags.EMPHASIS_TAG)
            if ele_emphasis is not None:
                key_text = self._do_preprocessing("".join(ele_emphasis.itertext()))

        return key_text

    def _extract_from_calloutlist(self, tag):
        """
        extract content from the calloutlist tag

        Args:
            tag - calloutlist lxml object
        Return:
            list - content under calloutlist tag
        """
        list_item = []
        ele_listitems = tag.findall(p.XMLTags.LISTITEM_TAG)
        for ele_listitem in ele_listitems:
            list_item.append(self._get_value_from_callout_listitem(ele_listitem))

        return list_item

    def _get_absolute_path(self, img_file_path):
        """
        get the absolute path of the image refered in XML and change the
        format to PNG

        Args:
             file_path: given XML manual file path
        Return:
            a_path: absolute path of the referred image in XML
        """
        logger.debug("drive 0 : %s", self.file_path.split(os.path.sep))
        actual_path = self.file_path.split(os.path.sep)
        rel_path = img_file_path.split('/')
        img_name = rel_path[-1]
        img_names = img_name.split(".")
        img_name = img_names[0] + ".png"
        rel_path[-1] = img_name
        bk_dir_cnt = rel_path.count('..')
        actual_path = actual_path[:-1]
        actual_path = actual_path[:-bk_dir_cnt]
        rel_path = rel_path[bk_dir_cnt:]
        ch_path = actual_path[1:] + rel_path
        # logger.debug("drive : %s", actual_path[0])
        logger.debug("drive : %s", actual_path)
        a_path = actual_path[0] + os.path.sep + os.path.join(*ch_path)
        return a_path

    def _extract_from_graphic(self, tag):
        """
        extract the figure path from the XML

        Args:
            tag - xml element of graphic
        :return:
        """
        figure = {}
        ele_graphic = tag.find(p.XMLTags.GRAPHIC_TAG)
        attrib = ele_graphic.items()
        for attrib, value in attrib:
            if attrib == p.XMLTags.FILEREF_ATTRIB:
                logger.debug("extracted_path :  %s", self._get_absolute_path(value))
                file_path = self._get_absolute_path(value)
                size = os.stat(file_path).st_size
                figure[p.ExtractionConstants.FILE_PATH] = file_path
                figure[p.ExtractionConstants.SIZE] = size
                figure[p.ExtractionConstants.FILE_TYPE] = "png"
                return figure

    def _extract_from_figure(self, tag):
        """
        extract from the figure tag

        Args:
            tag - lxml object of figure tag
        Return:
            dict - content in dict format
        """
        feature_dict = {}
        all_childern = tag.getchildren()
        logger.debug("fig child : %s", all_childern)
        for childern in all_childern:
            if childern.tag == p.XMLTags.CALLOUTLIST_TAG:
                feature_dict[p.FEATURES] = self._extract_from_calloutlist(childern)
            if childern.tag == p.XMLTags.GRAPGHICGRP_TAG:
                feature_dict[p.ExtractionConstants.FIGURE] = self._extract_from_graphic(childern)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                feature_dict.update(self._extract_from_figure(childern))

        if len(feature_dict.keys()) > 0:
            return feature_dict
        else:
            return None

    def _extract_from_variablelist(self, tag):
        """
        extract the content from the variablelist tag

        Args:
            tag - lxml object of the variablelist tag
        Return:
            list - inside content in list format
        """
        list_entry = []
        caution = None
        note = None
        entry_dict = dict()
        ele_varlistentries = tag.findall(p.XMLTags.VAR_LIST_ENTRY_TAG)

        for ele_varlistentry in ele_varlistentries:
            ele_term = ele_varlistentry.find(p.XMLTags.TERM_TAG)
            key_text = "".join(ele_term.itertext())
            tentry_dict = entry_dict.copy()
            tentry_dict[p.STEP] = self._do_preprocessing(key_text)
            ele_listitem = ele_varlistentry.find(p.XMLTags.LISTITEM_TAG)
            list_items = []
            for children in ele_listitem.getchildren():
                if children.tag == p.XMLTags.PARA_TAG:
                    list_items.append(self._do_preprocessing(self._get_value_frm_para(children)))
                elif children.tag == p.XMLTags.CAUTION_TAG:
                    caution = self._extract_from_caution(children)
                elif children.tag == p.XMLTags.NOTE_TAG:
                    note = self._extract_from_note(children)
            tentry_dict[p.CHECKS] = list_items
            if caution is not None:
                tentry_dict[p.XMLTags.CAUTION_TAG] = caution
            if note is not None:
                tentry_dict[p.XMLTags.NOTE_TAG] = note

            list_entry.append(tentry_dict)

        return list_entry

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
            thead_dict[col_number] = self._get_value_frm_para(ele_entry.find(p.XMLTags.PARA_TAG))
        logger.debug("thead_dict : %s %s", thead_dict, not thead_dict)
        if not thead_dict:
            return None
        else:
            return thead_dict

    def _get_entry_col_number(self, tag):
        for attrib, value in tag.items():
            if attrib == p.XMLTags.COLNAME_ATTRIB:
                return value
        return -1

    def _extract_frm_entry(self, entry_tag, col_number, internal_key, entry_dict):
        details = entry_dict
        logger.debug('details : %s',details)
        key = p.ENTRY if internal_key is None else internal_key
        entry_children = entry_tag.getchildren()
        for child in entry_children:
            if child.tag == p.XMLTags.PARA_TAG:
                if col_number == "1":
                    key = self._get_value_frm_para(child)
                    details[key] = {}
                else:
                    if p.DESCRIPTION_KEY not in details[key]:
                        details[key][p.DESCRIPTION_KEY] = []
                    details[key][p.DESCRIPTION_KEY].append(self._get_value_frm_para(child))
            if child.tag == p.XMLTags.FIGURE_TAG:
                details[key].update(self._extract_from_figure(child))
        return details, key

    def _extract_from_table(self, tag):
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
                    temp_dict = {}
                    temp_dict = self._extract_entry_in_table(ele_entries, temp_dict, thead_detail)

                    if len(temp_dict) > 0:
                        list_entry.append(temp_dict)

                table_dict[p.ENTRIES] = list_entry
        return table_dict

    def _extract_entry_in_table(self, ele_entries, temp_dict, thead_detail):
        """
        extract from the entries inside the rows in table

        Args:
            ele_entries: list of entries inside the row
            temp_dict: dict to be filled
            thead_detail: thead detail of table
        return:
            temp_dict: details filled dict
        """
        for ele_entry in ele_entries:
            col_number = None
            ele_attribs = ele_entry.items()
            for attrib, value in ele_attribs:
                if attrib == p.XMLTags.COLNAME_ATTRIB:
                    col_number = value
            entry_all_childern = ele_entry.getchildren()
            temp_dict = self._extract_table_childern(col_number, entry_all_childern, temp_dict, thead_detail)
        return temp_dict

    def _extract_table_childern(self, col_number, entry_all_childern, temp_dict, thead_detail):
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
        for entry_children in entry_all_childern:
            if entry_children.tag == p.XMLTags.VAR_LIST_TAG:
                logger.debug("opr list entry : %s", self._extract_from_variablelist(entry_children))
                # list_entry.append(self._extract_from_variablelist(entry_children))
                temp_dict[p.XMLTags.ENTRY_TAG] = self._extract_from_variablelist(entry_children)
            if entry_children.tag == p.XMLTags.PARA_TAG:
                logger.debug("para_tag : %s", self._get_value_frm_para(entry_children))
                if not thead_detail:
                    temp_dict[p.DESCRIPTION_KEY] = self._do_preprocessing(
                    self._get_value_frm_para(entry_children))
                else:
                    temp_dict[thead_detail[col_number]] = self._do_preprocessing(
                        self._get_value_frm_para(entry_children))
            if entry_children.tag == p.XMLTags.FIGURE_TAG:
                temp_dict.update(self._extract_from_figure(entry_children))
        return temp_dict

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
                summary[p.DESCRIPTION_KEY].append(self._do_preprocessing(self._get_value_frm_para(children)))
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
                summary[p.XMLTags.PREREQUISITES_TAG][p.XMLTags.CAUTION_TAG] = self._extract_from_caution(
                    p_child)
            if p_child.tag == p.XMLTags.WARNING_TAG:
                summary[p.XMLTags.PREREQUISITES_TAG][p.XMLTags.WARNING_TAG] = self._extract_from_warning(
                    p_child)
            if p_child.tag == p.XMLTags.PARA_TAG:
                if p.DESCRIPTION_KEY not in summary[p.XMLTags.PREREQUISITES_TAG]:
                    summary[p.XMLTags.PREREQUISITES_TAG][p.DESCRIPTION_KEY] = []
                summary[p.XMLTags.PREREQUISITES_TAG][p.DESCRIPTION_KEY].append(
                    self._do_preprocessing(self._get_value_frm_para(p_child)))
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
                    step_dict[p.XMLTags.STEP_TAG] = self._do_preprocessing(self._get_value_frm_para(children))
                if children.tag == p.XMLTags.CAUTION_TAG:
                    step_dict[p.XMLTags.CAUTION_TAG] = self._extract_from_caution(children)
                if children.tag == p.XMLTags.NOTE_TAG:
                    step_dict[p.XMLTags.NOTE_TAG] = self._extract_from_note(children)
                if children.tag == p.XMLTags.FIGURE_TAG:
                    step_dict.update(self._extract_from_figure(children))

            procedure.append(step_dict)

        return procedure

    def _extract_from_variablelist_listitem(self, tag):
        extract_json = {}
        all_children = tag.getchildren()
        for children in all_children:
            if children.tag == p.XMLTags.PARA_TAG:
                para_text = self._get_value_frm_para(children)
                if p.DESCRIPTION_KEY not in extract_json:
                    extract_json[p.DESCRIPTION_KEY] = []
                extract_json[p.DESCRIPTION_KEY].append(para_text)
            if children.tag == p.XMLTags.FIGURE_TAG:
                extract_json.update(self._extract_from_figure(children))
            if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                if p.DESCRIPTION_KEY not in extract_json:
                    extract_json[p.DESCRIPTION_KEY] = []
                extract_json[p.DESCRIPTION_KEY] += self._extract_from_itemizedlist(children)
            if children.tag == p.XMLTags.CAUTION_TAG:
                extract_json[p.XMLTags.CAUTION_TAG] = self._extract_from_caution(children)
        return extract_json

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
                    extract_json[key_text][p.XMLTags.CAUTION_TAG] = self._extract_from_caution(children)
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
                section_dict[topic_title][p.XMLTags.NOTE_TAG] = self._extract_from_note(children)
            else:
                section_dict[topic_title][p.XMLTags.NOTE_TAG].extend(self._extract_from_note(children))
        if children.tag == p.XMLTags.TABLE_TAG:
            section_dict[topic_title].update(self._extract_from_table(children))
        if children.tag == p.XMLTags.PARA_TAG:
            if p.DESCRIPTION_KEY not in section_dict[topic_title]:
                section_dict[topic_title][p.DESCRIPTION_KEY] = []
            section_dict[topic_title][p.DESCRIPTION_KEY].append(
                self._do_preprocessing(self._get_value_frm_para(children)))
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
            topic_title = children.text
            section_dict[topic_title] = {}
        if children.tag == p.XMLTags.CAUTION_TAG:
            section_dict[topic_title][p.XMLTags.CAUTION_TAG] = self._extract_from_caution(children)
        if children.tag == p.XMLTags.FIGURE_TAG:
            feature_dict = self._extract_from_figure(children)
            if feature_dict is not None:
                section_dict[topic_title].update(feature_dict)
        if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
            if p.DESCRIPTION_KEY not in section_dict[topic_title]:
                section_dict[topic_title][p.DESCRIPTION_KEY] = self._extract_from_itemizedlist(children)
            else:
                section_dict[topic_title][p.DESCRIPTION_KEY].extend(self._extract_from_itemizedlist(children))
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
            if children.tag == p.XMLTags.VAR_LIST_TAG:
                topic_dict[topic_title].update(self._extract_from_topic_variablelist(children))
            if children.tag == p.XMLTags.TITLE_TAG:
                previous_tag = p.XMLTags.TITLE_TAG
                topic_title = "".join([text for text in children.itertext() if text != "TM"])
                logger.debug("topic title : %s",topic_title)
                topic_title = self._do_preprocessing(topic_title)
                topic_dict[topic_title] = {}
            if children.tag == p.XMLTags.CAUTION_TAG:
                previous_tag = p.XMLTags.CAUTION_TAG
                topic_dict[topic_title][p.XMLTags.CAUTION_TAG] = self._extract_from_caution(children)
            if children.tag == p.XMLTags.WARNING_TAG:
                previous_tag = p.XMLTags.WARNING_TAG
                topic_dict[topic_title][p.XMLTags.WARNING_TAG] = self._extract_from_warning(children)
            if children.tag == p.XMLTags.FIGURE_TAG:
                previous_tag = p.XMLTags.FIGURE_TAG
                feature_dict = self._extract_from_figure(children)
                if feature_dict is not None:
                    topic_dict[topic_title].update(feature_dict)
            previous_tag, topic_title, topic_dict = self._extract_topic_child2(children, previous_tag, topic_dict,
                                                                               topic_title)
            previous_tag, topic_title, topic_dict, previous_title = self._extract_topic_child3(children, previous_tag,
                                                                                               previous_title,
                                                                                               topic_dict, topic_title)
        return topic_dict

    def _extract_topic_child2(self, children, previous_tag, topic_dict, topic_title):
        if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
            previous_tag = p.XMLTags.ITEMIZEDLIST_TAG
            if p.DESCRIPTION_KEY not in topic_dict[topic_title]:
                topic_dict[topic_title][p.DESCRIPTION_KEY] = self._extract_from_itemizedlist(children)
            else:
                topic_dict[topic_title][p.DESCRIPTION_KEY].extend(self._extract_from_itemizedlist(children))
        if children.tag == p.XMLTags.TABLE_TAG:
            logger.debug("topic title :%s", topic_title)
            previous_tag = p.XMLTags.TABLE_TAG
            topic_dict[topic_title].update(self._extract_from_table(children))
        if children.tag == p.XMLTags.PARA_TAG:
            previous_tag = p.XMLTags.PARA_TAG
            if p.DESCRIPTION_KEY not in topic_dict[topic_title]:
                topic_dict[topic_title][p.DESCRIPTION_KEY] = []
            topic_dict[topic_title][p.DESCRIPTION_KEY].append(
                self._do_preprocessing(self._get_value_frm_para(children)))
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
                    topic_dict[topic_title][previous_title][p.XMLTags.NOTE_TAG] = self._extract_from_note(children)
                else:
                    topic_dict[topic_title][previous_title][p.XMLTags.NOTE_TAG].extend(
                        self._extract_from_note(children))
            else:
                if p.XMLTags.NOTE_TAG not in topic_dict[topic_title]:
                    topic_dict[topic_title][p.XMLTags.NOTE_TAG] = self._extract_from_note(children)
                else:
                    topic_dict[topic_title][p.XMLTags.NOTE_TAG].extend(self._extract_from_note(children))
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
                main_key = children.text
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
                return key_value_pair, key
            elif tag_str == p.XMLTags.CHAPTER_TAG:
                key_value_pair, key = self._extract_from_chapter(tag)
                return key_value_pair, key
            elif tag_str == p.XMLTags.SECTION_TAG:
                key_value_pair, key = self._extract_from_section(tag)
                return key_value_pair, key
        else:
            return None, None

    def get_operation_data(self):
        """
        get the overall json for the operation section

        Return:
            dict - overall content
        """
        response_json = {}
        section_data, key = self._get_section(p.OPERATION)
        logger.debug('section_data : %s',section_data)
        if section_data is not None:
            post_process =  PostProcessOprData()
            logger.debug("file_path opr : %s", self.file_path)
            framed_dict = {}
            framed_dict[p.PRODUCT_TYPE_KEY] = self.get_product_type()
            model_nos = self.get_buyermodel()
            framed_dict[p.MODELS_KEY] = self._get_regex_model_list(model_nos)
            framed_dict[p.PARTNUMBER] = self.get_partnumber()
            framed_dict[p.COMMON_INFO_KEY] = {}
            framed_dict[p.COMMON_INFO_KEY][p.DATA_KEY] = []
            framed_dict[p.COMMON_INFO_KEY][p.DATA_KEY].append(post_process.post_process_data(section_data))
            response_json[p.ExtractionConstants.STATUS_STR] = p.ExtractionConstants.SUCCESS
            response_json[p.ExtractionConstants.DATA_KEY] = framed_dict
        else:
            response_json[p.ExtractionConstants.STATUS_STR] = p.ExtractionConstants.NO_SECTION
            response_json[p.ExtractionConstants.ERR_MG] = p.ExtractionConstants.NO_SECTION_MSG

        return response_json


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    opr_xml_extract = OperationXMLExtractor(
        r"<path_to_xml>\us_main.book.xml")
    print(opr_xml_extract.get_operation_data())
