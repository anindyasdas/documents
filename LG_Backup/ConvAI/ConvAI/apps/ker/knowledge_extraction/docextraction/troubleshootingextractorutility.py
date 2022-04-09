# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""

import logging as logger
import os

import regex as re
from constants import params as p


class TroubleshootingExtractorUtility(object):
    """
    class used to provide the utility methods to extract the basic lxml element

    @method: get_value_frm_para(para) : get text from the para tag
    @method: extract_from_itemizedlist(tag) : extract the itemized list lxml element
    @method: extract_from_figure(tag, file_path) : extract from the figure tag
    @method: extract_from_variablelist(tag): extract from the variablelist tag
    """

    def __init__(self, file_path):
        self.file_path = file_path

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
        text = re.sub('\s{2,}', ' ', text)
        # remove the space around the '-' character
        text = re.sub('\s*-\s*', '-', text)
        # replace the '\n' character
        text = re.sub('\n', '', text)
        text = re.sub('\t', '', text)

        return text

    def get_value_frm_para(self, para):
        """
        parse para element and frame text

        Args:
            para: para element
        Return:
            text
        """
        return self._do_preprocessing("".join(para.itertext()))

    def extract_from_itemizedlist(self, tag):
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
                    list_items[p.DESCRIPTION_KEY].append(self._do_preprocessing(self.get_value_frm_para(children)))
                if children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                    list_items[p.DESCRIPTION_POINTS] = self.extract_from_itemizedlist(children)
                if children.tag == p.XMLTags.FIGURE_TAG:
                    list_items.update(self.extract_from_figure(children, self.file_path))
            details.append(list_items)
        return details

    def extract_from_figure(self, tag, file_path):
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
                feature_dict[p.ExtractionConstants.FIGURE] = self._extract_from_graphic(childern, file_path)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                feature_dict.update(self.extract_from_figure(childern, file_path))

        if len(feature_dict.keys()) > 0:
            return feature_dict
        else:
            return None

    def _get_key_text(self, children, ele_key):
        """
        identify and return the key element to frmae the dict from calloutlist

        Args:
            children: para tag
            ele_key: key tag lxml element
        return:
            key text identified
        """
        key_text = None
        if ele_key is not None:
            key_text = self._do_preprocessing(" ".join(ele_key.itertext()))
        elif ele_key is None:
            ele_emphasis = children.find(p.XMLTags.EMPHASIS_TAG)
            if ele_emphasis is not None:
                key_text = self._do_preprocessing(" ".join(ele_emphasis.itertext()))

        return key_text

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
                para_children = children.getchildren()

                key_text = self._extract_key_txt(children, para_children)
                key_text = self._do_preprocessing(key_text.strip())
                para_text = self._do_preprocessing(self.get_value_frm_para(children))
                logger.debug('ele_key : %s - %s', key_text, para_text)
                if (key_text is not None) and (key_text.strip() == para_text.strip()):
                    feature = self._do_preprocessing(key_text)
                else:
                    ddesc = {}
                    ddesc[p.DESCRIPTION_KEY] = [self._do_preprocessing(para_text)]
                    explanation.append(ddesc)
            elif children.tag == p.XMLTags.ITEMIZEDLIST_TAG:
                explanation = self.extract_from_itemizedlist(children)
            elif children.tag == p.XMLTags.CAUTION_TAG:
                caution = self.extract_from_caution(children)
            elif children.tag == p.XMLTags.NOTE_TAG:
                note = self.extract_from_note(children)

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

    def _extract_key_txt(self, children, para_children):
        key_text = ""
        for child in para_children:
            if child.tag == p.XMLTags.KEY_TAG:
                key_text += self._get_key_text(children, child) + " "
            if child.tag == p.XMLTags.EMPHASIS_TAG:
                key_text += child.text + " "
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

    def _extract_from_graphic(self, tag, file_path):
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
                logger.debug("extracted_path :  %s", self._get_absolute_path(value, file_path))
                file_path = self._get_absolute_path(value, file_path)
                size = os.stat(file_path).st_size
                figure[p.ExtractionConstants.FILE_PATH] = file_path
                figure[p.ExtractionConstants.SIZE] = size
                figure[p.ExtractionConstants.FILE_TYPE] = "png"
                return figure

    def _get_absolute_path(self, img_file_path, file_path):
        """
        get the absolute path of the image refered in XML and change the
        format to PNG

        Args:
             file_path: given XML manual file path
        Return:
            a_path: absolute path of the referred image in XML
        """
        logger.debug("drive 0 : %s", file_path.split(os.path.sep))
        actual_path = file_path.split(os.path.sep)
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

    def extract_from_variablelist(self, tag):
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
                    list_items.append(self._do_preprocessing(self.get_value_frm_para(children)))
                elif children.tag == p.XMLTags.CAUTION_TAG:
                    caution = self.extract_from_caution(children)
                elif children.tag == p.XMLTags.NOTE_TAG:
                    note = self.extract_from_note(children)
            tentry_dict[p.CHECKS] = list_items
            if caution is not None:
                tentry_dict[p.XMLTags.CAUTION_TAG] = caution
            if note is not None:
                tentry_dict[p.XMLTags.NOTE_TAG] = note

            list_entry.append(tentry_dict)

        return list_entry

    def extract_from_caution(self, tag):
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
                caution_list[p.DESCRIPTION_POINTS] += self.extract_from_itemizedlist(childern)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                caution_list.update(self.extract_from_figure(childern))
        return caution_list

    def extract_from_note(self, tag):
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
                logger.debug('nested itemized : %s', self.extract_from_itemizedlist(childern))
                note_details[p.DESCRIPTION_POINTS] += self.extract_from_itemizedlist(childern)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                note_details.update(self.extract_from_figure(childern))

        note_list.append(note_details)

        return note_list

    def extract_from_warning(self, tag):
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
                warning_list[p.DESCRIPTION_POINTS] += self.extract_from_itemizedlist(childern)
            if childern.tag == p.XMLTags.FIGURE_TAG:
                warning_list.update(self.extract_from_figure(childern))

        return warning_list
