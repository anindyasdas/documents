# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author:senthil.sk@lge.com
"""

import logging as logger
import re

import nltk
import numpy as np

from .preference import Preference
from ..constants import params as cs

class ModelNoHandler(object):

    def __init__(self):
        # future ref regex = r'([a-z]+\d+([a-z]\*|[a-z]|\*)\w*)'
        regex = r'([a-z]+\d+([a-z]\*|[a-z]+|\*|\s*|\d+)[a-z0-9]*)'
        self.model_regex = re.compile(regex, flags=re.IGNORECASE)

    def extract_model_no(self, user_query): # pragma: no cover
        """
        extract model no from user query
        Args:
            user_query: query from usery
        Return:
            Truncated modelno,actual model no
        """
        self.user_query = user_query
        result = self.model_regex.findall(self.user_query)

        for e_modelno, lchar in result:
            logger.debug("e_modelno=%s",e_modelno)
            logger.debug("lchar=%s",lchar)
            #if (len(e_modelno.strip()) > 0) and (len(lchar.strip()) > 0) and (len(e_modelno) > 6):
            #if (len(e_modelno.strip()) > 0) and (len(lchar.strip()) > 0):
            if (len(e_modelno.strip()) > 0):
                return self._return_regex_truncated_model_no(e_modelno), e_modelno

        return None, None

    def _return_regex_truncated_model_no(self, model_no): # pragma: no cover
        """
        return the truncated model_no based on regex defined
        regex will give AlphaNumeric+one Alphabet+*

        Args:
            model_no: text from <Buyermodel> tag
        Return:
            truncated model_no
        """
        if model_no is None:
            return None

        logger.debug('model_no : %s', model_no)
        result = re.findall(r'([a-z]+\d+([a-z]|\*|\s*))', model_no, flags=re.IGNORECASE)
        logger.debug('result : %s', result)
        if result is None:
            return None

        for e_modelno, lchar in result:
            #if (len(e_modelno.strip()) > 0) and (len(lchar.strip()) > 0):
            if (len(e_modelno.strip()) > 0):
                if lchar is not '*':
                    e_modelno = e_modelno.strip() + '*'

                #if len(e_modelno) > 6:
                return e_modelno

        return None

    def _group_model_no_based_length(self, length, models_dict):
        """
        group the model number from the DB based on length of the model number from DB

        Args:
            length: length of the model number in user query
            models_dict: models_dict obtained from the DB
        Return:
            dict of the model number as key in length
        """
        model_with_len_det = {}

        for product in models_dict.keys():
            for model in models_dict[product]:
                key = len(model.strip())
                if key not in model_with_len_det:
                    model_with_len_det[key] = []
                model_with_len_det[key].append(model.strip())
        logger.debug("grouped model no : %s", model_with_len_det)
        return model_with_len_det

    def _get_match_model_no_grp(self, user_model_no, grp_model_dict):
        """
        get the list of model number from the DB dict based on matched model number length from user query

        Args:
            user_model_no: model no from user query
            grp_model_dict: groped model dict
        Return:
            list of the model number based on length of user queried model number
        """
        key = len(user_model_no.strip())

        if key in grp_model_dict:
            return grp_model_dict[len(user_model_no.strip())]
        return None

    def _frame_regex(self, model_list):
        """
        frame the regex by the * char with .*

        Args:
            model_list: list of mapped model from DB
        Return:
            List of regex model
        """
        regex_list = []
        for model in model_list:
            regex_list.append(model.replace("*",".*"))

        return regex_list

    def _get_model_number_based_regex(self, user_model_number, regex_list):
        """
        map the model number from user query to the model in DB

        Args:
            user_model_number:model no from user
            regex_list: list of model number in regex
        Return:
            mapped model no index
        """
        model_number = None
        logger.debug("regex_list : %s",regex_list)
        for idx in range(len(regex_list)):
            model_number = re.search(regex_list[idx], user_model_number)

            if model_number is not None:
                return idx
        return -1

    def _map_user_model_no_based_regex(self, user_model_no, model_dict):
        """
        map the model number from the user query to the model number to DB

        Args:
            user_model_no: model froom user
            model_dict: model_dict got from DB
        Return:
            mapped model number
        """
        grp_model_dict = self._group_model_no_based_length(len(user_model_no.strip()), model_dict)
        logger.debug("grp dict : %s", grp_model_dict)
        grp_model_list = self._get_match_model_no_grp(user_model_no, grp_model_dict)

        # check if user queried model number length matched model no in DB
        if grp_model_list is not None:
            model_regex_list = self._frame_regex(grp_model_list)
            found_model_idx = self._get_model_number_based_regex(user_model_no, model_regex_list)
            logger.debug("fnd model idx : %s",found_model_idx)
            if found_model_idx != -1:
                return grp_model_list[found_model_idx]
        return None

    def _map_usr_model_to_db(self, user_model_no, model_dict): # pragma: no cover
        """
        map the model number from user query to model no in DB based on edit distance

        Args:
            user_model_no: model no from user query
            model_dict: model_dict framed from DB
        Return:
            mapped model number
        """
        grp_model_dict = self._group_model_no_based_length(len(user_model_no.strip()), model_dict)
        logger.debug("grp dict : %s", grp_model_dict)
        grp_model_list = self._get_match_model_no_grp(user_model_no, grp_model_dict)
        logger.debug("grp_model_list : %s", grp_model_list)
        model_edit_distance = []

        # check if user queried model number length matched model no in DB
        if grp_model_list is not None:
            for model in grp_model_list:
                logger.debug("user_model_no:%s, model:%s, edit_dis: %s", user_model_no, model,
                             nltk.edit_distance(user_model_no, model))
                model_edit_distance.append(nltk.edit_distance(user_model_no, model))
            min_idx = np.argmin(model_edit_distance, axis=0)

            if model_edit_distance[min_idx] <= 2:
                return grp_model_list[min_idx]
        return None

    def extract_map_model_no(self, user_query, model_dict):
        """
        extract and map the model number from user query to model in DB

        Args:
            user_query: user query
            model_dict: model dict framed from DB
        Return:
            mapped model number , extracted model number
        """
        logger.debug("user_query=%s, model_dict=%s",user_query, model_dict)
        sts = model_dict[cs.resp_code]
        model_dict = model_dict[cs.resp_data]

        if sts == cs.ResponseCode.KER_INTERNAL_SUCCESS:
            result = self.model_regex.findall(user_query)
            e_modelno = ""
            for e_modelno, lchar in result:
                if (len(e_modelno.strip()) > 0) and (len(lchar.strip()) > 0) and (len(e_modelno) > 6):
                    e_modelno = e_modelno.strip()

            logger.debug("e_modelno = %s, length=%s",e_modelno, len(e_modelno.strip()))
            if len(e_modelno.strip()) == 0:
                return None, None

            logger.debug("model no frm qur : %s", e_modelno)
            logger.debug("model dict : %s", model_dict)
            # for testing return self._map_usr_model_to_db(e_modelno, model_dict)
            mapped_model_no = self._map_user_model_no_based_regex(e_modelno, model_dict)
            logger.debug("mapped_model_no : %s ",mapped_model_no)
            return mapped_model_no, e_modelno
        else:
            return None, None


if __name__ == '__main__': # pragma: no cover
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    # for testing Preference.intialize_preference()
    # for testing user_query = "My vacuum cleaner VAC900A gives me a hot air, Why so?"
    model_dict = {
        "washing machine": ["WM4500H*A", "WKEX200H*A", "WKGX201H*A", "WM9500H*A", "WT7100C*", "WT7150C*", "WT7150*",
                            "WT7005C*"],
        "refrigerator": ["LRFDS2503*", "LRFXS2503*", "LRFCS2503*"],
        "oven": ["LSEL6337*", "LSEL6335*"],
        "dishwasher": ["LDFN343**"]
    }
    model = ModelNoHandler()
    while (True):
        print("Enter query : ")
        query = input()
        print("mapped model no : %s",model.extract_map_model_no(query, model_dict))
    # print(model.extract_model_no(user_query))
