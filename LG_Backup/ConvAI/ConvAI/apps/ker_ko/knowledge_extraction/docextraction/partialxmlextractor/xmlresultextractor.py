import copy
import logging as logger
import os
import re
from configparser import ConfigParser
from lxml import etree as et

from .troubleshootingextractor import TroubleshootingExtractor
from ...constants import params as p

logger = logger.getLogger("django")

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
print("xml current_path path : ", current_path)
CONFIG_PATH = os.path.abspath(os.path.join(current_path, '..', '..', 'config', 'configuration.ini'))
print("xml config path : ", CONFIG_PATH)


class XMLResultExtractor(object):

    def __init__(self):
        # self.parse_file(file_path)
        logger.debug("xml config path : %s", CONFIG_PATH)
        self.troubleshooting_flag = False
        self.troubleshootingextract = TroubleshootingExtractor()
        regex = r'([\w\s/?\(\),\-.\'‘’~\+&#]*)'
        self.title_regex = re.compile(regex, flags=re.IGNORECASE)
        self.xml_namespace = """<?xml-stylesheet type = "text/xsl" href = "xslt/test.xsl"?>
        <cms xmlns="http://www.crestec.co.jp/cms/element_definitions">"""
        self.xml_close_tag = "</cms>"
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        self.rmv_nw_sp_reg = "[\n\t\s]"
        self.MANUAL_XML_PATH = os.path.join(current_path, '..', '..',
                                            config_parser.get("xml_path_config",
                                                              "manual_xml_path"))

    def _preprocess_text(self, text):
        """
        Preprocessing the text by removing the \n\t\s to compare korean string
        
        Args:
            text - korean text with \n\t\s
        Return:
            text - preprocessed_text after removal of \n\t\s
        """
        text = re.sub(self.rmv_nw_sp_reg, "", text)
        logger.debug("preprocessed_text : %s", text)
        return text.strip()

    def parse_file(self, partnumber):
        """
        parse the file and returns the element tree

        Args:
            file_path: path of the main xml
        Return:
             etree:element tree
        """
        logger.debug("xml filepath partnumber: %s", partnumber)
        self.etree = et.parse(self.MANUAL_XML_PATH + "/" + partnumber + ".xml")
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

    def _find_preface(self, main_title, section_title=None, topic_title=None, sub_topic_title=None):
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
            if self._preprocess_text(title_txt) == self._preprocess_text(main_title.lower()):
                ele_sections = ele_preface.findall(p.XMLTags.SECTION_TAG)
                if section_title is not None:
                    xml_tag, lxml_ele = self._find_in_sections(ele_sections, section_title, topic_title,
                                                               sub_topic_title)

                    if xml_tag is None:
                        return None, None
                    else:
                        return xml_tag, lxml_ele
                else:
                    return p.XMLTags.PREFACE_TAG, ele_preface
        return None, None

    def _find_chapters(self, main_title, section_title=None, topic_title=None, sub_topic_title=None):
        """
        find the given title find from element under chapter

        Args:
            title_list: list of titles
        Return:
            xml element
        """
        ele_chapters = self._get_chapters()
        for ele_chapter in ele_chapters:
            ele_title = ele_chapter.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text.lower()
            logger.debug("chapter title : %s %s", title_txt, title_txt == "고장 신고 전 확인하기")
            logger.debug("title list : %s", main_title)
            title_txt = ele_title.text.lower()
            if self._preprocess_text(title_txt) == self._preprocess_text(main_title.lower()):
                if section_title is not None:
                    ele_sections = ele_chapter.findall(p.XMLTags.SECTION_TAG)
                    xml_tag, lxml_ele = self._find_in_sections(ele_sections, section_title, topic_title,
                                                               sub_topic_title)

                    if xml_tag is None:
                        return None, None
                    else:
                        return xml_tag, lxml_ele
                else:
                    return p.XMLTags.CHAPTER_TAG, ele_chapter
        return None, None

    def _find_appendix(self, main_title, section_title=None, topic_title=None, sub_topic_title=None):
        """
        find the given title find the element under chapter element

        Args:
            title_list: list of titles
        Return:
            xml element
        """
        ele_appendixes = self._get_appendix()
        for ele_appendix in ele_appendixes:
            ele_title = ele_appendix.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text
            if self._preprocess_text(title_txt) == self._preprocess_text(main_title.lower()):
                logger.debug("find in appendix : %s", title_txt)
                if section_title is not None:
                    ele_sections = ele_appendix.findall(p.XMLTags.SECTION_TAG)
                    xml_tag, lxml_ele = self._find_in_sections(ele_sections, section_title, topic_title,
                                                               sub_topic_title)
                    if xml_tag is None:
                        return None, None
                    else:
                        return xml_tag, lxml_ele
                else:
                    return p.XMLTags.APPENDIX_TAG, ele_appendix
        return None, None

    def _find_in_sections(self, ele_sections, section_title, topic_title, sub_topic_title):
        """
        Identify the section xml element based on the given section title , If it is not present in section
        check inside the topic level
        
        Args:
            ele_sections: lxml element:lxml element of the section tag
            section_title: String: title of the section to be identified
            topic_title: String: title of the topic to be identified inside the section
            sub_topic_title: list:  titles of the internal sub topic title
        Return:
            ele_section: lxml element: lxml element of the identified section
            xml_tag: String: identified lxml element tag
        """
        logger.debug("_find_in_sections section_title={0}, topic_title={1}, sub_topic_title={2}".format(section_title,
                                                                                                        topic_title,
                                                                                                        str(sub_topic_title)))
        for ele_section in ele_sections:
            ele_title = ele_section.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text.lower()
            # if title_txt in title_list:
            logger.debug("self._preprocess_text(title_txt.lower()) : %s", self._preprocess_text(title_txt.lower()))
            logger.debug("self._preprocess_text(section_title.lower()) : %s",
                         self._preprocess_text(section_title.lower()))
            if self._preprocess_text(title_txt.lower()) == self._preprocess_text(section_title.lower()):
                if topic_title is not None:
                    xml_tag, lxml_ele = self._find_in_topic(ele_section, topic_title, sub_topic_title)

                    if xml_tag == None:
                        return None, None
                    else:
                        return xml_tag, lxml_ele
                else:
                    return p.XMLTags.SECTION_TAG, ele_section

        return None, None

    def _find_in_topic(self, ele_section, topic_title, sub_topic_title):
        """
        find inside the topic from the given section  lxml element with given topic title
        
        Args:
            ele_section: lxml element : lxml element of the section identified
            topic_title: String : title of the topic to be identifed
            sub_topic_title: list : sub topic title need to identifed with internal content
        Return:
            xml_tag: String: tag of the identifed xml element
            ele_topic: lxml element: identifed topic lxml element
        """
        topic_title = topic_title.split("#")
        logger.debug("_find_in_topic topic_title:%s sub_topic_title=%s", topic_title, sub_topic_title)
        ele_topics = ele_section.findall(p.XMLTags.TOPIC_TAG)
        for ele_topic in ele_topics:
            ele_title = ele_topic.find(p.XMLTags.TITLE_TAG)
            title_txt = ele_title.text.lower()
            logger.debug('_find_in_topic Topic title : (%s)', ele_title.text)
            # if title_txt in title_list:
            topic_title = [self._preprocess_text(title.lower()) for title in topic_title]
            #if self._preprocess_text(title_txt) == self._preprocess_text(topic_title.lower()):
            if self._preprocess_text(title_txt) in topic_title:

                xml_tag, lxml_ele = None, None
                if (sub_topic_title is not None) and ((sub_topic_title[0] in p.XMLTags.INTERNAL_SECTION_TAG) or (
                        sub_topic_title[0] in p.XMLTags.KOREAN_INTERNAL_SECTION_TAG)):
                    xml_tag, lxml_ele = self._find_in_note_caution_summary_warn(ele_topic, sub_topic_title)

                elif sub_topic_title is not None:
                    xml_tag, lxml_ele = self._find_in_internal_content(ele_topic, sub_topic_title)

                if sub_topic_title is None:
                    return p.XMLTags.TOPIC_TAG, ele_topic
                elif xml_tag == None:
                    return None, None
                else:
                    return xml_tag, lxml_ele
        return None, None

    def _find_entry_col_number(self, ele_entry):
        """
        find the column number of the given entry lxml
        
        Args:
            ele_entry: lxml object: lxml object of the entry tag inside the table row
        Return:
            value: String: column number
        """
        ele_attribs = ele_entry.items()
        for attrib, value in ele_attribs:
            if attrib == p.XMLTags.COLNAME_ATTRIB:
                return value

    def _find_in_calloutlist(self, ele_fig, sub_topic_title=None):
        xpath_exp = "//*[normalize-space(text()) = \"" + sub_topic_title[0] + "\"]"
        logger.debug("xpath_exp : %s", xpath_exp)
        found_element = ele_fig.xpath(xpath_exp)

        logger.debug("_find_in_calloutlist : %s", str(found_element))
        if (found_element is not None) and (len(found_element) > 0):
            return True
        return False

    def _find_in_figure(self, ele_topic, sub_topic_title=None):
        """
        find inside the given content in the table from the gien topic tag lxml object
        keep the figure information if immediate child is table  from fig will be useful in case
        of "control panel" section retrieval

        Args:
            ele_topic: lxml obj: lxml object of the topic tag
            sub_topic_title: list : sub topic title with internal content
        Return:
            xml_tag: Content idnetifed xml tag
            tmp_ele_topic: lxml object of the topic tag
        """
        logger.debug("find in table : %s", str(sub_topic_title))
        tmp_ele_topic = copy.deepcopy(ele_topic)
        found_flag = False
        all_children = tmp_ele_topic.getchildren()

        for idx, children in enumerate(all_children):
            if children.tag == p.XMLTags.FIGURE_TAG:
                found_flag = self._find_in_calloutlist(children, sub_topic_title)
            elif children.tag == p.XMLTags.TITLE_TAG:
                continue
            else:
                children.getparent().remove(children)

        if found_flag:
            return p.XMLTags.TOPIC_TAG, tmp_ele_topic

        return None, None

    def _find_in_table_keep_fig(self, ele_topic, sub_topic_title=None):
        """
        find inside the given content in the table from the gien topic tag lxml object
        keep the figure information if immediate child is table  from fig will be useful in case
        of "control panel" section retrieval
        
        Args:
            ele_topic: lxml obj: lxml object of the topic tag
            sub_topic_title: list : sub topic title with internal content
        Return:
            xml_tag: Content idnetifed xml tag
            tmp_ele_topic: lxml object of the topic tag
        """
        logger.debug("_find_in_table_keep_fig find in table : %s", str(sub_topic_title))
        tmp_ele_topic = copy.deepcopy(ele_topic)
        found_flag = False
        all_children = tmp_ele_topic.getchildren()

        for idx, children in enumerate(all_children):
            next_child = None
            if children.tag == p.XMLTags.FIGURE_TAG:
                if (idx + 1) < len(all_children):
                    next_child = all_children[idx + 1]
                # check if the immediate child is table and keep the figure tag
                if (next_child is not None) and (next_child.tag == p.XMLTags.TABLE_TAG):
                    continue
                else:
                    children.getparent().remove(children)
            elif children.tag == p.XMLTags.TABLE_TAG:
                found_flag = self._check_and_eliminate_rows_table(children, sub_topic_title)
            elif (children.tag == p.XMLTags.TITLE_TAG) or (children.tag == p.XMLTags.FOOTNOTE_GROUP_TAG):
                continue
            else:
                children.getparent().remove(children)

        if found_flag:
            return p.XMLTags.TOPIC_TAG, tmp_ele_topic

        return None, None

    def _check_and_eliminate_rows_table(self, ele_table, sub_topic_title=None):
        """
        check the content inside the table rows and remove the row with unwanted content
        
        Args:
            ele_table: lxml obj: lxml elemnt of the table tag
            sub_topic_title: list: sub topic title with internal content
        Return:
            found_flag: bool: True or False
        """
        logger.debug("find in table : %s", str(sub_topic_title))
        found_flag = False
        thead_flag = True

        ele_tgroup = ele_table.find(p.XMLTags.TGROUP_TAG)
        ele_thead = ele_tgroup.find(p.XMLTags.THEAD_TAG)

        if ele_thead is not None:
            ele_rows = ele_thead.findall(p.XMLTags.ROW_TAG)
            found_flag, sub_topic_title = self._fnd_in_thead(ele_rows, found_flag, sub_topic_title)
        else:
            thead_flag = False
            found_flag = True

        logger.debug("found_flag : %s thead_flag:%s", found_flag, thead_flag)
        if ((found_flag) and (len(sub_topic_title) >= 1)) or (not thead_flag):
            logger.debug("finding in row sub_topic_title : %s",sub_topic_title)
            self._eliminate_unwanted_row(ele_tgroup, sub_topic_title)
        elif (found_flag):
            found_flag = True
        else:
            found_flag = False

        return found_flag

    def _find_in_table(self, ele_topic, sub_topic_title=None):
        """
        check insde the table element in the table rows for the internal content.
        
        Args:
            ele_topic: lxml obj: lxml elemnt of the topic tag
            sub_topic_title: list: sub topic title with internal content
        Return:
            xml_tag : String: xml tag of identifed tag
            ele_table: lxml obj: lxml object of the table element
        """
        logger.debug("find in table : %s", str(sub_topic_title))
        tmp_ele_topic = copy.deepcopy(ele_topic)
        ele_tables = tmp_ele_topic.findall(p.XMLTags.TABLE_TAG)
        found_flag = True

        if (ele_tables is not None):
            for ele_table in ele_tables:
                ele_tgroup = ele_table.find(p.XMLTags.TGROUP_TAG)
                ele_thead = ele_tgroup.find(p.XMLTags.THEAD_TAG)
                ele_rows = ele_thead.findall(p.XMLTags.ROW_TAG)

                if ele_thead is not None:
                    found_flag, sub_topic_title = self._fnd_in_thead(ele_rows, found_flag, sub_topic_title)
                if (found_flag) and (len(sub_topic_title) >= 1):
                    logger.debug("finding in row")
                    self._eliminate_unwanted_row(ele_tgroup, sub_topic_title)
                if found_flag:
                    return p.XMLTags.TABLE_TAG, ele_table

        return None, None

    """For reverting back to older implementation
    def _eliminate_unwanted_row(self, ele_tgroup, sub_topic_title):

        check inside the row of the table for the given content and delete the row with
        unwanted content
        
        Args:
            ele_tgroup: lxml obj: lxml object of the tgroup tag of table
            sub_topic_title: sub topic title with internal content to be serached.
        
        ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
        ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
        row_fnd_flag = False
        for ele_row in ele_rows:
            ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
            for ele_entry in ele_entries:
                trow_entry_text = "".join(ele_entry.itertext())
                trow_entry_text = re.sub(self.rmv_nw_sp_reg, "", trow_entry_text)
                sub_topic_entry_text = re.sub(self.rmv_nw_sp_reg, "", sub_topic_title[len(sub_topic_title)-1])
                logger.debug("trow_entry_text : %s",trow_entry_text)
                logger.debug("sub_topic_entry_text : %s",sub_topic_entry_text)
                if sub_topic_entry_text in trow_entry_text:
                    row_fnd_flag = True
                    break
            if row_fnd_flag:
                logger.debug("row_fnd_flag : %s", row_fnd_flag)
                row_fnd_flag = False
                continue
            ele_row.getparent().remove(ele_row)"""

    def _get_col_attrib(self, ele_entry):
        """
        get the colnumber attribute of the entry xml element

        Args:
            ele_entry:lxml object of entry tag
        Return:
            colnumber : int
        """
        attribs = ele_entry.items()
        for attrib, value in attribs:
            if attrib == p.XMLTags.COLNAME_ATTRIB:
                return int(value)

    def _get_merged_cell_cnt(self, ele_entry):
        """
        get the morerows attribute from entry xml tag

        Args:
            ele_entry: lxml obj of entry tag
        Return:
            number of merged cells: int
        """
        mer_cell_cnt = 0
        attribs = ele_entry.items()
        for attrib, value in attribs:
            logger.debug("attrib : %s, %s",attrib, (attrib == p.XMLTags.MOREROWS_ATTRIB))
            if attrib == p.XMLTags.MOREROWS_ATTRIB:
                mer_cell_cnt = value
                break
        return int(mer_cell_cnt)

    def _eliminate_unwanted_row(self, ele_tgroup, sub_topic_titles):
        """
        check inside the row of the table for the given content and delete the row with
        unwanted content

        Args:
            ele_tgroup: lxml obj: lxml object of the tgroup tag of table
            sub_topic_title: sub topic title with internal content to be serached.
        """
        ele_tbody = ele_tgroup.find(p.XMLTags.TBODY_TAG)
        ele_rows = ele_tbody.findall(p.XMLTags.ROW_TAG)
        entry_fnd_flag = False
        previous_merged_cell_entries = []
        prev_merg_cnt = 0
        chk_row_cnt = 0
        mer_cell_cnt = 0

        logger.debug("_eliminate_unwanted_row sub_topic_titles : %s",sub_topic_titles)
        for idx, ele_row in enumerate(ele_rows):
            entry_fnd_flag = False
            prev_merg_cnt = 0
            ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
            for ele_entry in ele_entries:
                trow_entry_text = "".join(ele_entry.itertext())
                trow_entry_text = re.sub(self.rmv_nw_sp_reg, "", trow_entry_text)
                mer_cell_cnt = self._get_merged_cell_cnt(ele_entry)
                logger.debug("ele_row parent : %s",ele_row.get("id"))
                logger.debug("_eliminate_unwanted_row mer_cell_cnt: %s",mer_cell_cnt)

                for sub_topic_title in sub_topic_titles:
                    sub_topic_entry_text = re.sub(self.rmv_nw_sp_reg, "", sub_topic_title)
                    logger.debug("trow_entry_text : %s",trow_entry_text)
                    logger.debug("sub_topic_entry_text : %s in %s",sub_topic_entry_text, (sub_topic_entry_text in trow_entry_text))
                    if sub_topic_entry_text in trow_entry_text:
                        entry_fnd_flag = True
                        logger.debug("Found data in cell")
                        if mer_cell_cnt > 0:
                            if mer_cell_cnt > prev_merg_cnt:
                                logger.debug("mer_cell_cnt: %s prev_merg_cnt: %s",mer_cell_cnt, prev_merg_cnt)
                                prev_merg_cnt = mer_cell_cnt
                            previous_merged_cell_entries.append(ele_entry)

            if prev_merg_cnt > 0:
                chk_row_cnt = prev_merg_cnt
            if not entry_fnd_flag:
                entry_fnd_flag = False
                logger.debug("chk_row_cnt : %s",chk_row_cnt)
                if chk_row_cnt > 0:
                    chk_row_cnt = chk_row_cnt - 1
                elif chk_row_cnt <= 0:
                    chk_row_cnt = 0
                    logger.debug("eliminating the row")
                    ele_row.getparent().remove(ele_row)
                    previous_merged_cell_entries = []


    def _fnd_in_thead(self, ele_rows, found_flag, sub_topic_titles):
        """
        check for the content  inside the thead element of the table
        
        Args:
            ele_rows: lxml element of the tale row
            found_flag: initialized found flags
            sub_topic_titles: sub topic title with internal content to be searched
        Return:
            found_flag : content found flag
        """
        found_flag = False
        for ele_row in ele_rows:
            ele_entries = ele_row.findall(p.XMLTags.ENTRY_TAG)
            for ele_entry in ele_entries:
                thead_text = re.sub(self.rmv_nw_sp_reg, "", "".join(ele_entry.itertext()))
                for idx, sub_topic_title in enumerate(sub_topic_titles):
                    sub_topic_text = re.sub(self.rmv_nw_sp_reg, "", sub_topic_title)
                    logger.debug("thead_text :%s", thead_text)
                    if sub_topic_text in thead_text:
                        found_flag = True
                        sub_topic_titles.pop(idx)
                        # ref found_col_num = self._find_entry_col_number(ele_entry)
                        break
            if found_flag:
                break
        return found_flag, sub_topic_titles

    def _find_in_procedure(self, ele_topic, sub_topic_title=None):
        """
        find procedure lxml object of the procedure tag inside the topic
        
        Args:
            ele_topic:lxml obj of the topic tag
            sub_topic_title: sub topic title with internal text to be searched inside
        Return:
            xml_tag: xml tag of the topic element
            ele_topic: lxml obj of the topic
        """
        logger.debug("find in procedure")
        tmp_ele_topic = copy.deepcopy(ele_topic)
        children = tmp_ele_topic.getchildren()

        for child in children:
            if (child.tag == p.XMLTags.TITLE_TAG) or (child.tag == p.XMLTags.PROCEDURE_TAG):
                continue
            else:
                child.getparent().remove(child)
        children = tmp_ele_topic.getchildren()
        logger.debug("find in procedure :%s", len(children))
        if len(children) > 0:
            return p.XMLTags.TOPIC_TAG, tmp_ele_topic
        return None, None

    def _find_in_note_caution_summary_warn(self, ele_topic, sub_topic_title):
        """
        find inside the extra infor tags like cation, note ... tags.

        Args:
            ele_topic: lxml obj of the topic tag
            sub_topic_title: sub topic title with internal content to be searched
        Return:
            xml_tag: xml tag of the internal content
            lxml_ele: lxml elemnt of the of identifed content
        """
        internal_tag = sub_topic_title[0]
        if internal_tag in p.XMLTags.KOREAN_INTERNAL_SECTION_TAG:
            internal_tag = p.ExtractionConstants.SECTION_NAME_TRANSLATE[internal_tag]

        if internal_tag == p.XMLTags.PROCEDURE_TAG:

            if len(sub_topic_title) > 1:
                xml_tag, lxml_ele = self._find_in_procedure(ele_topic, sub_topic_title[1:])
            else:
                xml_tag, lxml_ele = self._find_in_procedure(ele_topic)
            if xml_tag is not None:
                return xml_tag, lxml_ele

        ele_extra_info = ele_topic.find(internal_tag)
        if ele_extra_info is not None:
            return internal_tag, ele_extra_info

        return None, None

    def _find_in_internal_content(self, ele_topic, sub_topic_title):
        """
        find inside the troubleshooting cause, simplesection, variablelist, table
        
        Args:
            ele_topic: lxml elemnt of the topic element
            sub_topic_title: sub topic title with internal content to be searched
        Return:
            xml_tag: xml tag of the identified element
            lxml_ele: lxml obj of the identifed element
        """
        logger.debug("_find_in_internal_content sub_topic_title : %s", sub_topic_title)

        xml_tag, lxml_ele = None, None

        if self.troubleshooting_flag:
            xml_tag, lxml_ele = self.troubleshootingextract.extract_trob_prob_cause(ele_topic, sub_topic_title)

        if lxml_ele is None:
            xml_tag, lxml_ele = self._find_in_simplesect(ele_topic, sub_topic_title)

        if lxml_ele is None:
            xml_tag, lxml_ele = self._find_in_variablelist(ele_topic, sub_topic_title[0])

            logger.debug("find in note : %s", xml_tag)
            if xml_tag is None:
                xml_tag, lxml_ele = self._find_in_table_keep_fig(ele_topic, sub_topic_title)
            if xml_tag is None:
                xml_tag, lxml_ele = self._find_in_figure(ele_topic, sub_topic_title)
        return xml_tag, lxml_ele

    def _remove_icon_text(self, ele_title):
        """
        remove the text related to the icon from title text

        Args:
            ele_title: title lxml element
        Return:
            title text with icon removed
        """
        title_txt = "".join(ele_title.itertext())
        ele_icon = ele_title.find(p.XMLTags.ICON_TAG)
        logger.debug("_remove_icon_text title_txt : %s",title_txt)
        if ele_icon is not None:
            icon_txt = ele_icon.text
            logger.debug("_remove_icon_text icon_txt : %s",icon_txt)
            for icon_char in icon_txt:
                logger.debug("_remove_icon_text icon_char : %s",icon_char)
                title_txt = title_txt.replace(icon_char, "")
        return title_txt.strip()

    def _find_in_simplesect(self, ele_topic, sub_topic_title):
        logger.debug("sub_topic_title : %s", sub_topic_title)
        ele_simplesects = ele_topic.findall(p.XMLTags.SIMPLESECT_TAG)
        for ele_simplesect in ele_simplesects:
            ele_title = ele_simplesect.find(p.XMLTags.TITLE_TAG)
            title_txt = self._remove_icon_text(ele_title)
            title_txt = title_txt.lower()
            logger.debug('Topic title : (%s)', ele_title.text)
            # if title_txt in title_list:
            if title_txt == sub_topic_title[0].lower():
                if len(sub_topic_title[1:]) >= 1:
                    if (sub_topic_title is not None) and ((sub_topic_title[1] in p.XMLTags.INTERNAL_SECTION_TAG) or (
                            sub_topic_title[1] in p.XMLTags.KOREAN_INTERNAL_SECTION_TAG)):
                        xml_tag, lxml_ele = self._find_in_note_caution_summary_warn(ele_simplesect, sub_topic_title[1:])

                    elif sub_topic_title is not None:
                        xml_tag, lxml_ele = self._find_in_internal_content(ele_simplesect, sub_topic_title[1:])

                    if xml_tag == None:
                        continue
                    else:
                        return xml_tag, lxml_ele
                else:
                    return p.XMLTags.SIMPLESECT_TAG, ele_simplesect
        return None, None

    def _find_in_variablelist(self, ele_topic, term_topic):
        logger.debug("_find_in_variablelist term_topic : %s", term_topic)
        temp_ele_topic = copy.deepcopy(ele_topic)
        ele_variablelists = temp_ele_topic.findall(p.XMLTags.VAR_LIST_TAG)
        found_flag = False
        for ele_variablelist in ele_variablelists:
            ele_variablelistentries = ele_variablelist.findall(p.XMLTags.VAR_LIST_ENTRY_TAG)
            for ele_variablelistentry in ele_variablelistentries:
                ele_term = ele_variablelistentry.find(p.XMLTags.TERM_TAG)
                term_title = "".join(ele_term.itertext())

                if term_title == term_topic:
                    found_flag = True
                else:
                    ele_variablelistentry.getparent().remove(ele_variablelistentry)
            if found_flag:
                return p.XMLTags.VAR_LIST_TAG, ele_variablelist
        return None, None

    def _extract_xml(self, partnumber, main_title, section_title=None, topic_title=None, sub_topic_title=None):

        logger.debug(
            "main_title={0}, section_title={1}, topic_title={2}, sub_topic_title={3}".format(main_title, section_title,
                                                                                             topic_title,
                                                                                             sub_topic_title))
        self.parse_file(partnumber)

        if main_title in p.ExtractionConstants.SECTION_NAMING_LIST[p.TROB_SECTION]:
            self.troubleshooting_flag = True

        tag, lxml_ele = self._find_preface(main_title, section_title, topic_title, sub_topic_title)

        if lxml_ele is None:
            tag, lxml_ele = self._find_chapters(main_title, section_title, topic_title, sub_topic_title)
            if lxml_ele is None:
                tag, lxml_ele = self._find_appendix(main_title, section_title, topic_title, sub_topic_title)

        logger.debug("element : %s", lxml_ele)
        if lxml_ele is not None:
            return str(et.tostring(lxml_ele, pretty_print=True, encoding="utf-8").decode("utf-8"))
        return None

    def getpartialxml(self, partnumber, section_hierarchy):
        try:
            logger.debug("getpartialxml :%s", section_hierarchy)
            title_result = self.get_titles(section_hierarchy)
            logger.debug("title_result :%s", title_result)
            main_title, section_title, topic_title, sub_topic_title = None, None, None, None
            if len(title_result) == 1:
                main_title = title_result[0]
            elif len(title_result) == 2:
                main_title, section_title = title_result[0], title_result[1]
            elif len(title_result) == 3:
                main_title, section_title, topic_title = title_result[0], title_result[1], title_result[2]
            else:
                main_title, section_title, topic_title, sub_topic_title = title_result[0], title_result[1], \
                                                                          title_result[2], title_result[3:]
            xml = self._extract_xml(partnumber, main_title, section_title, topic_title, sub_topic_title)
            logger.debug("partial xml : %s", xml)
            return xml
        except Exception as e:
            logger.exception("Exception in getting partial xml : %s", e)
            return None

    def addnamespacetoxml(self, partialxml):
        return self.xml_namespace + partialxml + self.xml_close_tag

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

    def _pre_process_section_hierarchy(self, section_hierarchy):
        section_hierarchy = re.sub('<num(.*?)>[a-z]', "", section_hierarchy)
        section_hierarchy = re.sub('<num(.*?)>', "", section_hierarchy)
        section_hierarchy = re.sub('figure', "", section_hierarchy)
        section_hierarchy = re.sub('calloutlist', "", section_hierarchy)
        section_hierarchy = re.sub('ct\s*[0-9]\s*[a-z]', "", section_hierarchy)
        section_hierarchy = re.sub('ct\s*[0-9]\s*', "", section_hierarchy)
        section_hierarchy = re.sub('item\s*[0-9]', "", section_hierarchy)
        section_hierarchy = re.sub('orderedlist', "", section_hierarchy)
        section_hierarchy = re.sub('<item(.*?)>', "", section_hierarchy).strip()
        return section_hierarchy

    def get_titles(self, sec_ti_hierarchy):
        logger.debug("Before preprocessing section hierarchy : %s", sec_ti_hierarchy)
        sec_ti_hierarchy = self._pre_process_section_hierarchy(sec_ti_hierarchy)
        logger.debug("After preprocessing section hierarchy : %s", sec_ti_hierarchy)
        title_regex_result = self.title_regex.findall(sec_ti_hierarchy)
        title_regex_result = [title for title in title_regex_result if len(title.strip()) > 0]
        title_regex_result = title_regex_result[1:]
        """append_no_of_none = 0
        if len(title_regex_result) < 3:
            append_no_of_none = 4 - len(title_regex_result)

        for idx in range(append_no_of_none):
            title_regex_result.append(None)"""
        return title_regex_result


if __name__ == "__main__":
    xmlextractor = XMLResultExtractor(
        r"E:\manuals\korean_manuals\older_manual\korean_manual\xml\[MFL71485465]3814_[CW_FL]Victor2_WO_for_Korea_R1\overall.xml")
    print(xmlextractor.extract_xml("LG ThinQ 사용하기", "LG ThinQ 앱으로 제품 작동하기", "LG ThinQ 기능 안내", "세탁/건조 코스(원격제어, 다운로드코스)"))
