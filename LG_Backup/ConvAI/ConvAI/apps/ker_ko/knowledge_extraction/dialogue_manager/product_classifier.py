# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk
"""
import json
import re
import os
import pandas as pd
from configparser import ConfigParser

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, '..', 'config', 'configuration.ini')


class ProductClassifier(object):

    def __init__(self):
        self.regex_dict = {}
        self.generic_prd_key = "generic_key"
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        self.prd_json_path = os.path.join(current_path, '..',
                                          config_parser.get("product_regex",
                                                            "product_regex_json"))
        self._read_regex()

    def _read_regex(self):
        """
           read regex for different class of
           products from json

        Returns
        -------
        None.

        """
        with open(self.prd_json_path, 'r', encoding="utf-8") as pf:
            self.regex_dict = json.load(pf)

    def find_class_frm_query(self, query):
        """
           Identify the class for the user
           query

        Parameters
        ----------
        query : String
            Query from user.

        Returns
        -------
        key : String
            class of the query.

        """
        main_prd = None
        sub_prd = None
        keys = self.regex_dict[self.generic_prd_key].keys()
        for key in keys:
            main_prd_match = re.search(self.regex_dict[self.generic_prd_key][key], query, re.IGNORECASE)

            if main_prd_match is not None:
                main_prd = key
                break

        if main_prd is not None:
            skeys = self.regex_dict[main_prd].keys()
            for skey in skeys:
                sub_prd_match = re.search(self.regex_dict[main_prd][skey], query, re.IGNORECASE)

                if sub_prd_match is not None:
                    sub_prd = skey
                    break

        return main_prd, sub_prd


    def test_method(self, file_name):
        """
        method to test the different type of question read from excel

        Args:
            file_name: name of the file to read input from
        Return:
            Write the output to the same file in main_product and sub_prd column
        """
        df = pd.read_excel(file_name)
        input_questions = df['Question'].tolist()
        main_prd_list, sub_prd_list = list(), list()

        for question in input_questions:
            main_prd, sub_prd = self.find_class_frm_query(question)
            main_prd_list.append(main_prd)
            sub_prd_list.append(sub_prd)
        df['main product'] = main_prd_list
        df['sub product'] = sub_prd_list
        df.to_excel(file_name, index=False)

if __name__ == '__main__':
    prd_class = ProductClassifier()

    prd_class.test_method("E:\sprint_15\sample_questions.xlsx")

    while (True):
        print("Enter query : ")
        query = input()
        print('Result : ', prd_class.find_class_frm_query(query))
