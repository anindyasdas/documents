# -*- coding: utf-8 -*-
"""
 *
 * Copyright (c) 2018 LG Electronics Inc.
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
import json
import os
from configparser import ConfigParser
from rdflib import Graph
import logging as logger

CONFIG_PATH = (os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..'
                 , 'config', 'configuration.ini')))

class RDFParser:
    """
    Package_dependencies:
    Install the following packages before run this parser
    # pip install rdflib        ---> BSD License
    # pip install rdflib-jsonld ---> BSD License

    This class is used to parse the RDF schema in turtle format

    @method - get_schema_for_key - get schema details for specific key
    @method - get_whole_schema - get the converted schema
    """

    def __init__(self):
        self.schema_file_path = ""
        self.converted_dict = {}
        self._parse_schema()

    def _load_file(self):
        """
        load the schema file and returns the file
        @return - file object of schema file
        """
        schema_file = open(self.schema_file_path)
        return schema_file

    def _convert_schema_to_dict(self, json_ld):
        """
        convert the JSON_LD schema format to dict object
        @return - dict of the schema
        """
        schema_dict = json.loads(json_ld)
        return schema_dict

    def _extract_proper_txt(self, text):
        """
        remove the character @ if string starts with it
        or get the string from url after # character

        @param - text - input string
        @return - extracted string
        """
        if text.startswith("@"):
            return text[1:]
        elif text.startswith("http://"):
            return text[text.index("#") + 1:]
        else:
            return text

    def _parse_dict(self, dict):
        """
        remove the unwanted character or extract proper text from uri
        and maintain key value pair properly

        @param - dict with values or keys with uri or @ character
        @return - converted dict object
        """
        temp_dict = {}
        for key in dict.keys():
            temp_dict[self._extract_proper_txt(key)] = self._extract_proper_txt(dict[key])
        return temp_dict

    def _parse_list(self, schema_list):
        """
        remove the unwanted character or extract proper text from uri
        and maintain key value pair properly or if the list have

        @param - list with values or list of dict
        @return - converted list object
        """
        temp_list = []
        for value in schema_list:
            if type(value) is dict:
                temp_list.append(self._parse_dict(value))
            else:
                temp_list.append(self._extract_proper_txt(value))
        return temp_list

    def _parse_rdf_dict(self, schema_dict):
        """
        parse the schema in dict format
        @dict - dict object of the schema
        """
        keys = schema_dict.keys()
        last_main_key = ""
        for key in keys:
            if key == "@id":
                last_main_key = self._extract_proper_txt(schema_dict[key])
                self.converted_dict[last_main_key] = {}
            else:
                ldict = self.converted_dict[last_main_key]
                if isinstance(schema_dict[key], list):
                    ldict[self._extract_proper_txt(key)] = self._parse_list(schema_dict[key])

    def _get_file_path_frm_config(self):
        """
        get the file path mentioned in config file
        and filled it in  schema_file_path
        """
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        abspath_path = os.path.abspath(os.path.join(os.path.dirname(
                                                    os.path.realpath(__file__)), '..', '..'))
        self.schema_file_path = os.path.join(abspath_path,
                                             config_parser.get("rdf_schema_file", "file_path"))


    def _convert_ttl_to_json_ld(self):
        """
        convert the ttl file to JSON_LD format
        :return:json string of schema
        """
        self._get_file_path_frm_config()
        schema_str = Graph().parse(self.schema_file_path, format='turtle')\
                            .serialize(format='json-ld').decode("utf8")
        return schema_str

    def _parse_schema(self):
        """
        get the file path from config and convert
        the schema to dict and parse the schema
        """
        schema_dict_list = self._convert_schema_to_dict(self._convert_ttl_to_json_ld())
        for dict in schema_dict_list:
            self._parse_rdf_dict(dict)
        logger.debug(str(self.converted_dict))

    def get_schema_for_key(self, key):
        """
        get the schema for the specific key

        @return - schema detail for the key
        """
        return self.converted_dict[key]

    def get_whole_schema(self):
        """
        get the whole schema as dict object

        @return - schema as dict object
        """
        return self.converted_dict


if __name__ == "__main__":
    logger.basicConfig(filename="newfile.log",
                       filemode='a',
                       format='%(asctime)s %(message)s')

    rdfparser = RDFParser()
    # added sample code to show how to use api
    print(str(rdfparser.get_schema_for_key("Spin_speed")))
