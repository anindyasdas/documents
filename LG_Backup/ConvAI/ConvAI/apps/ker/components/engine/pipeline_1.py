"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""
import heapq

import h5py

from . import constants
from ..text_similarity import base_question_extraction
import numpy as np
# will be enabled later
# from ..classifier.classifier_engine import ClassifierEngine
import pandas as pd
import re

import logging as logger

class Pipeline1:
    """
    Constituency Paser to extract Noun Phrases and Verb Phrases
    """
    __instance = None

    @staticmethod
    def get_instance(text_sim, info_extr):
        """ Static access method to get the singleton instance"""
        if Pipeline1.__instance is None:
            Pipeline1(text_sim, info_extr)
        return Pipeline1.__instance

    def __init__(self, text_sim, info_extr):
        """ Virtually private constructor. """
        if Pipeline1.__instance is not None:
            raise Exception("Pipeline1 is not instantiable")
        else:
            Pipeline1.__instance = self
        self.initialize(text_sim, info_extr)

    def initialize(self, text_sim, info_extr):
        """
        Initializes json data and hdf5 file
        :param text_sim: text similarity module
        :param info_extr: info extraction module
        :return: None
        """
        self.text_sim = text_sim
        self.info_extr = info_extr
        self.json_data_pt = {}
        self.category_cache = {}
        try:
            self.question_list_extraction(info_extr, text_sim)
            
        except OSError as err:
            with h5py.File(constants.PIPELINE_1_LM_EMB, "w") as f:
                for p in constants.PRODUCTS:
                    for t in [constants.SPEC, constants.TROB, constants.FAQ, constants.OPERATION]:
                        is_supported = self.__check_supported_sections(t, p)
                        if not is_supported:
                            continue
                        json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,
                                                                                         pipeline=constants.PIPELINE_1)
                        self.json_data_pt[p + '|' + t] = json_data
                        orig = pd.read_excel(constants.INPUT_FILES[p][t], sheet_name='L1_L2_L3', engine='openpyxl')
                        orig = orig.applymap(str)
                        category = self.__get_category(orig, t)

                        self.category_cache[p + '|' + t] = category
                        for k, v in json_data.items():
                            embeddings = text_sim.compute_embeddings_single(v)
                            f.create_dataset(p + '|' + t + '|' + k, data=embeddings)

            self.lm_file = h5py.File(constants.PIPELINE_1_LM_EMB, "r")

    def __get_category(self, orig, t):
        if t == constants.OPERATION:
            category = list(set(map(self.pre_process_key, list(set(orig['Grouped Key'].values)))))
        elif t == constants.TROB:
            category = list(set(map(self.pre_process_key, list(set(orig.Type.values)))))
        else:
            category = ['nan']
        return category

    def __check_supported_sections(self, t, p):
        """
        check sections supported per product type and returns true or false
        """
        if t == constants.OPERATION:
            if p == constants.REFRIGERATOR or p == constants.WASHING_MACHINE:
                return True
            else:
                return False
        return True

    def question_list_extraction(self, info_extr, text_sim):
        """
        read text similarity embeddings and generate question list json
        :param info_extr: output of info extraction
        :param text_sim: output of text similarity
        :return: None
        """
        self.lm_file = h5py.File(constants.PIPELINE_1_LM_EMB, "r")
        for p in constants.PRODUCTS:
            for t in [constants.SPEC, constants.TROB, constants.FAQ, constants.OPERATION]:
                is_supported = self.__check_supported_sections(t, p)
                if not is_supported:
                    continue
                json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,
                                                                                 pipeline=constants.PIPELINE_1)
                self.json_data_pt[p + '|' + t] = json_data
                orig = pd.read_excel(constants.INPUT_FILES[p][t], sheet_name='L1_L2_L3', engine='openpyxl')
                orig = orig.applymap(str)
                if t == constants.OPERATION:
                    category = list(set(map(self.pre_process_key, list(set(orig['Grouped Key'].values)))))
                else:
                    if 'Type' in orig.columns:
                        category = list(set(map(self.pre_process_key, list(set(orig['Type'].values)))))
                    else:
                        category = ['nan']
                self.category_cache[p + '|' + t] = category

    def __update_product_type(self, product):
        """
        check the product type and correct as per info engine constants defined
        """
        if product == 'vc':
            product = constants.VACUUM_CLEANER
        elif product == 'ac':
            product = constants.AC
        elif product == 'dishwasher':
            product = constants.DISH_WASHER
        elif product == 'oven':
            product = constants.MICROWAVE_OVEN
        return product

    def extract(self, text, question_type, product, top_k=1, l1_key=None):
        """
        Runs info extraction and synonym matching on the given text
        :param text: str - input text
        :param question_type: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param product: the given product
        :param top_k: top k predictions
        :param l1_key: L1 key to filter during inference
        :return: Returns json output with similairty key
        """
        product = self.__update_product_type(product)
        check = self.__check_supported_sections(question_type, product)
        if not check:
            return {
                constants.response_code: constants.STATUS_UNSUPPORTED_QUERY,
                constants.response_data:
                    {
                        constants.SIMILARITY_KEY: None
                    }
            }
        json_data = self.json_data_pt[product + '|' + question_type]

        info_extr, _ = self.info_extr.extract_info_single(text, constants.PIPELINE_1, question_type, product,
                                                          self.text_sim)

        to_return = self.__get_topk_questions(info_extr, json_data, l1_key, product, question_type, text, top_k)

        similarity_key = self.__get_similarity_key(to_return)
        logger.debug("similarity_key in pipeline_1=%s", str(similarity_key))
        return {
            constants.response_code: constants.STATUS_OK,
            constants.response_data:
                {
                    constants.SIMILARITY_KEY: similarity_key
                }
        }

    def __get_topk_questions(self, info_extr, json_data, l1_key, product, question_type, text, top_k):
        to_return = self.__get_in_json(json_data, info_extr)
        if to_return is None:
            query_embeddings = self.text_sim.compute_embeddings_single([info_extr])

            l1_key = self.__process_l1_key(json_data, l1_key)
            category = self.extract_category(l1_key, product, question_type, text)

            flag = False
            question_score = []
            for cat in category:
                for k, v in json_data.items():
                    if k.endswith(cat):
                        sentence_embeddings = self.lm_file[product + '|' + question_type + '|' + k]
                        arr1 = self.text_sim.model_evaluate_single_util(query_embeddings, sentence_embeddings)
                        m = k[:k.rindex('|')]
                        question_score.append((m, np.max(arr1)))
                if flag:
                    break

            top_k_questions = heapq.nlargest(top_k, question_score, key=lambda x: x[1])
            to_return = [q[0] for q in top_k_questions]
        else:
            to_return = [to_return] * top_k
        return to_return

    def __process_l1_key(self, json_data, l1_key):
        l1_key_present = False
        if l1_key is not None:
            l1_key = self.pre_process_key(l1_key)
            for k, v in json_data.items():
                if k.endswith(l1_key):
                    l1_key_present = True
                    break
        if not l1_key_present:
            l1_key = None
        return l1_key

    def __get_similarity_key(self, to_return):
        """
        function to return similarity keys
        """
        similarity_key = []
        for index, value in enumerate(to_return):
            d = {}
            d["key"] = value
            similarity_key.append(d)
        return similarity_key

    def extract_category(self, l1_key, product, question_type, text):
        """
        extract category of given question
        :param l1_key: str - category
        :param product: product type
        :param question_type: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param text:question
        :return: category
        """
        if l1_key:
            category = [self.pre_process_key(l1_key)]
        else:
            category = self.category_cache[product + '|' + question_type]
        return category

    def __get_in_json(self, json_data, info_extr):
        """
        Gets the key if the info extracted text is directly present in the json - this avoids calling text similarity
        :param json_data: canonical questions json
        :param info_extr: output of info extraction
        :return: predicted key
        """
        s = -1
        toreturn = None
        for k, v in json_data.items():
            m = k[:k.rindex('|')]
            for v1 in v:
                if v1 == info_extr:
                    return m
            search = re.search('\\b' + m.lower() + '\\b', info_extr)
            if search is not None and len(m) > s:
                s = len(m)
                toreturn = m
        return toreturn

    def pre_process_key(self, key):
        """
        Applies lower and last full stop removal to keys
        :param key: str - key
        :return: preprocessed key
        """
        new_key = key.lower()
        new_key = new_key.strip()
        new_key = re.sub(r'\s+', ' ', new_key)
        new_key = re.sub(r'\.$', '', new_key)
        return new_key
