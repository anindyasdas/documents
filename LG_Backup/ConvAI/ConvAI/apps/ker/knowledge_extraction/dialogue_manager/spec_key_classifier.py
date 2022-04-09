# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""
import sys
import os
from configparser import ConfigParser
import logging as logger
import json

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, '..', 'config', 'configuration.ini')

class SpecificationKeyIdentifier(object):
    """
       Used to identify the spec key in user query
    """
    def __init__(self):
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        spec_key_json_path = os.path.join(current_path, '..',
                                       config_parser.get("spec_key",
                                                         "spec_key_json"))
        with open(spec_key_json_path, 'r') as pf:
            self.spec_key = json.load(pf)

    def check_spec_key_in_query(self, query):
        """
        Identify the spec key in user query
        Args:
             query: query from user
        return:
             Boolean - True spec_key present
                         - False Sepc_key not present
        """
        keys = self.spec_key.keys()

        for key in keys:
            for text in self.spec_key[key]:
                if text.lower() in query.lower():
                    return True
        return False

if __name__ == "__main__":
    classifier = SpecificationKeyIdentifier()
    print(classifier.check_spec_key_in_query("What is the width of washing machine?"))