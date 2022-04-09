# -*- coding: utf-8 -*-
""""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anindya06.das@lge.com
##############################################################################
"""

from lxml import etree as et
import sys
import os
import re
import logging as logger
import json
import xmltodict
from pprint import pprint as pp
import random
from utils import format_json as fjson

random.seed(10)


class XMLJson:
    """
    class is used to parse the xml and convert into json

    """

    def __init__(self, file_path=None):
        """
        constructor initializing the etree element and regex for
        model number extraction

        Args:
            file_path:xml file absolute path
            It can be optional during executing the test case for model no
            extraction.
        """
        if file_path:
            self.etree = self._parse_file(file_path)
            xml_string = et.tostring(self.etree, pretty_print=True, encoding='utf8')
            base_path = os.path.abspath(os.path.join(os.path.dirname(file_path), '..', '..'))
            output_folder = os.path.join(base_path, 'output_folder')
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            consolidated_xml = os.path.join(output_folder, 'consolidated.xml')
            xml_string = self.process_string(xml_string.decode('utf-8-sig'))
            # logger.debug("xml_string : %s", xml_string)
            with open(consolidated_xml, 'w', encoding='utf-8-sig') as doc:
                doc.write(xml_string)
            self.etree = self._parse_file(consolidated_xml)
            self._unique_tag()
            xml_string = et.tostring(self.etree, pretty_print=True, encoding='utf-8')

            tree_json = xmltodict.parse(xml_string,
                                        xml_attribs=True)
            self.json_file_path = os.path.join(output_folder, 'manual.json')
            with open(self.json_file_path, 'w') as manual_json_file:
                json.dump(tree_json, manual_json_file, indent=6)
        self.file_path = file_path

    def _parse_file(self, file_path):
        """
        parse the file and returns the element tree

        Args:
            file_path: path of the main xml
        Return:
             etree:element tree
        """
        etree = et.parse(file_path)
        return etree

    def _recursive_id_tagger(self, node):
        """xmltodict combines the tags/keys with same name, results in discontinuity,
        this function, redefines tags/keys by combining the tag with its id,thus creating unique tags
        which makes it easier to be processed by xmltodict
        """
        for child in node:
            if 'id' in child.attrib:
                child.tag = child.tag + '_id_' + child.attrib['id']
            else:
                attrib = str(random.randint(1, 100000))
                child.tag = child.tag + '_id_' + attrib
            child = self._recursive_id_tagger(child)
        return node

    def _unique_tag(self):
        """ This function attaches unique ids to each generic tag, thus creating unique keys"""
        self.root = self.etree.getroot()
        self.root = self._recursive_id_tagger(self.root)

    def process_string(self, xml_string):
        xml_string = re.sub('<key id="(.*?)">', '#SBOLD#', xml_string)  # makes bold
        xml_string = re.sub('</key>', '#EBOLD#', xml_string)
        xml_string = re.sub('<emphasis id="(.*?)">', '#SEMP#', xml_string)  # makes bold
        xml_string = re.sub('</emphasis>', '#EEMP#', xml_string)
        xml_string = re.sub('<number id="(.*?)">', '', xml_string)  # remove number
        xml_string = re.sub('</number>', '', xml_string)
        xml_string = re.sub('<icon type=(.*?)</icon>', '', xml_string)
        xml_string = re.sub('<icon id="(.*?)">', '', xml_string)  #remove icon id
        xml_string = re.sub('</icon>', '', xml_string)       
        xml_string = re.sub('<lcd id=(.*?)>', '', xml_string)  # remove number
        xml_string = re.sub('</lcd>', '', xml_string)  # remove number
        xml_string = re.sub('\s{2,}', ' ', xml_string)
        xml_string = re.sub('\s*-\s*', '-', xml_string)
        xml_string = re.sub('\n', '', xml_string)
        xml_string = re.sub('\t', '', xml_string)
        return xml_string


if __name__ == "__main__":
    logger.basicConfig(level=logger.INFO,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    arguments = sys.argv
    XML_object = XMLJson(arguments[1])
    path = XML_object.json_file_path
    mp = fjson.ManualProcess(path)
    json_dict = mp.process_manual()
    path_segmented = os.path.abspath(path).split(os.sep)
    file_name, file_extension = path_segmented[-1].split('.')
    version_number = 'final'
    new_file = file_name + '_' + version_number + '.' + file_extension
    path_segmented[-1] = new_file
    new_file_path = os.path.join(path_segmented[0], os.sep, *path_segmented[1:])
    json.dump(json_dict, open(new_file_path, 'w'), indent=6)
