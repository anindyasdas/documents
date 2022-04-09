"""
# -------------------------------------------------
# Copyright(c) 2020-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------
"""
import heapq

import h5py

from . import constants
from ..text_similarity import base_question_extraction
import numpy as np
from ..classifier.classifier_engine import ClassifierEngine
import pandas as pd
import re
from fuzzywuzzy import fuzz
import json

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class Pipeline1:
    """
    Constituency Paser to extract Noun Phrases and Verb Phrases
    """
    __instance = None
    max_score = 100

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
                # dryer,styler
                for p in [constants.DRYER, constants.STYLER]:
                    for t in [constants.TROB, constants.OPERATION]:
                        is_supported = self.__check_supported_sections(t, p)
                        if not is_supported:
                            continue
                        json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,p,
                                                                                         pipeline=constants.PIPELINE_1)
                        self.json_data_pt[p + '|' + t] = json_data
                        orig = pd.read_excel(constants.INPUT_FILES[p][t], sheet_name='L1_L2_L3', engine='openpyxl')
                        orig = orig.applymap(str)
                        category = self.__get_category(orig, t)
                        # subtype add
                        self.category_cache[p + '|' + t] = category
                        for k, v in json_data.items():
                            embeddings = text_sim.compute_embeddings_single(v)
                            # subtype
                            f.create_dataset(p + '|' + t + '|' + k, data=embeddings)
                # washing machine
                for p in [constants.WASHING_MACHINE]:
                    for subtype in [constants.WasherSubProductTypes.FRONT_LOADER, constants.WasherSubProductTypes.KEPLER]:
                        for t in [constants.TROB, constants.OPERATION]:
                            is_supported = self.__check_supported_sections(t, p)
                            if not is_supported:
                                continue
                            json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,subtype,
                                                                                             pipeline=constants.PIPELINE_1)
                            self.json_data_pt[p + '|' + subtype + '|'+ t] = json_data
                            orig = pd.read_excel(constants.INPUT_FILES[p][subtype][t], sheet_name='L1_L2_L3', engine='openpyxl')
                            orig = orig.applymap(str)
                            category = self.__get_category(orig, t)
                            # subtype add
                            self.category_cache[p + '|' + subtype + '|' + t] = category
                            for k, v in json_data.items():
                                embeddings = text_sim.compute_embeddings_single(v)
                                # subtype
                                f.create_dataset(p + '|' + subtype + '|' + t + '|' + k, data=embeddings)
                # washing machine
                for p in [constants.WASHING_MACHINE]:
                    for subtype in [constants.WasherSubProductTypes.TOP_LOADER, constants.WasherSubProductTypes.MINI_WASHER]:
                        for t in [constants.TROB]:
                            is_supported = self.__check_supported_sections(t, p)
                            if not is_supported:
                                continue
                            json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,subtype,
                                                                                             pipeline=constants.PIPELINE_1)
                            self.json_data_pt[p + '|' + subtype + '|'+ t] = json_data
                            orig = pd.read_excel(constants.INPUT_FILES[p][subtype][t], sheet_name='L1_L2_L3', engine='openpyxl')
                            orig = orig.applymap(str)
                            category = self.__get_category(orig, t)
                            # subtype add
                            self.category_cache[p + '|' + subtype + '|' + t] = category
                            for k, v in json_data.items():
                                embeddings = text_sim.compute_embeddings_single(v)
                                # subtype
                                f.create_dataset(p + '|' + subtype + '|' + t + '|' + k, data=embeddings)

                # refrigerator
                for p in [constants.REFRIGERATOR]:
                    for subtype in constants.REFRIGERATOR_TYPES:
                        for t in [constants.TROB]:
                            is_supported = self.__check_supported_sections(t, p)
                            if not is_supported:
                                continue
                            json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,subtype,
                                                                                             pipeline=constants.PIPELINE_1)
                            self.json_data_pt[p + '|' + subtype + '|' + t] = json_data
                            orig = pd.read_excel(constants.INPUT_FILES[p][subtype][t], sheet_name='L1_L2_L3', engine='openpyxl')
                            orig = orig.applymap(str)
                            category = self.__get_category(orig, t)
                            # subtype add
                            self.category_cache[p + '|' + subtype + '|'  + t] = category
                            for k, v in json_data.items():
                                embeddings = text_sim.compute_embeddings_single(v)
                                # subtype
                                f.create_dataset(p + '|' + subtype + '|' + t + '|' + k, data=embeddings)

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
            if p in constants.OP_SUPPORTED_PRODUCTS:
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
        #
        for p in [constants.WASHING_MACHINE]:
            for subtype in [constants.WasherSubProductTypes.FRONT_LOADER, constants.WasherSubProductTypes.KEPLER]:
                for t in [constants.TROB, constants.OPERATION]:
                    is_supported = self.__check_supported_sections(t, p)
                    if not is_supported:
                        continue
                    json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,subtype,
                                                                                     pipeline=constants.PIPELINE_1)
                    self.json_data_pt[p + '|' + subtype+ '|' + t] = json_data
                    orig = pd.read_excel(constants.INPUT_FILES[p][subtype][t], sheet_name='L1_L2_L3', engine='openpyxl')
                    orig = orig.applymap(str)
                    if t == constants.OPERATION:
                        category = list(set(map(self.pre_process_key, list(set(orig['Grouped Key'].values)))))
                    else:
                        if 'Type' in orig.columns:
                            category = list(set(map(self.pre_process_key, list(set(orig['Type'].values)))))
                        else:
                            category = ['nan']
                    self.category_cache[p + '|' + subtype+ '|' + t] = category

        for p in [constants.WASHING_MACHINE]:
            for subtype in [constants.WasherSubProductTypes.TOP_LOADER, constants.WasherSubProductTypes.MINI_WASHER]:
                for t in [constants.TROB]:
                    is_supported = self.__check_supported_sections(t, p)
                    if not is_supported:
                        continue
                    json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,subtype,
                                                                                     pipeline=constants.PIPELINE_1)
                    self.json_data_pt[p + '|' + subtype+ '|' + t] = json_data
                    orig = pd.read_excel(constants.INPUT_FILES[p][subtype][t], sheet_name='L1_L2_L3', engine='openpyxl')
                    orig = orig.applymap(str)
                    if t == constants.OPERATION:
                        category = list(set(map(self.pre_process_key, list(set(orig['Grouped Key'].values)))))
                    else:
                        if 'Type' in orig.columns:
                            category = list(set(map(self.pre_process_key, list(set(orig['Type'].values)))))
                        else:
                            category = ['nan']
                    self.category_cache[p + '|' + subtype+ '|' + t] = category
        #
        for p in [constants.STYLER, constants.DRYER]:
            for t in [constants.TROB, constants.OPERATION]:
                is_supported = self.__check_supported_sections(t, p)
                if not is_supported:
                    continue
                json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p,p,
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
        #
        for p in [constants.REFRIGERATOR]:
            for subtype in constants.REFRIGERATOR_TYPES:
                for t in [constants.TROB]:
                    is_supported = self.__check_supported_sections(t, p)
                    if not is_supported:
                        continue
                    json_data = base_question_extraction.generate_question_list_json(info_extr, text_sim, t, p, subtype,
                                                                                     pipeline=constants.PIPELINE_1)
                    self.json_data_pt[p + '|' + subtype + '|' + t] = json_data
                    orig = pd.read_excel(constants.INPUT_FILES[p][subtype][t], sheet_name='L1_L2_L3', engine='openpyxl')
                    orig = orig.applymap(str)
                    if t == constants.OPERATION:
                        category = list(set(map(self.pre_process_key, list(set(orig['Grouped Key'].values)))))
                    else:
                        if 'Type' in orig.columns:
                            category = list(set(map(self.pre_process_key, list(set(orig['Type'].values)))))
                        else:
                            category = ['nan']
                    self.category_cache[p + '|' + subtype + '|' + t] = category

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

    def extract(self, text, question_type, product, sub_product_type,top_k=1, l1_key=None,is_train=False):
        """
        Runs info extraction and synonym matching on the given text
        :param text: str - input text
        :param question_type: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param product: the given product
        :param top_k: top k predictions
        :param l1_key: L1 key to filter during inference
        :return: Returns json output with similairty key
        """
        raw_text = text
        product = self.__update_product_type(product)
        check = self.__check_supported_sections(question_type, product)
        if text in constants.error_syns:
            text = constants.error_word
        if not check:
            return {
                constants.response_code: constants.STATUS_UNSUPPORTED_QUERY,
                constants.response_data:
                    {
                        "similarity_key": None
                    }
            }
        # if product has sub type , then add sub type
        if product != sub_product_type:
            json_data = self.json_data_pt[product + '|' + sub_product_type + '|' + question_type]
        else:
            json_data = self.json_data_pt[product + '|' + question_type]

        info_extr, _ = self.info_extr.extract_info_single(text, constants.PIPELINE_1, question_type, product,
                                                          self.text_sim)

        # adding query details
        query_details = l1_key, product, question_type, sub_product_type
        similarity_keys_with_scores_list = self.__get_topk_questions(info_extr, json_data, query_details, text, top_k)

        similarity_key = self.__get_similarity_key(similarity_keys_with_scores_list)
        logger.debug("similarity_key in pipeline_1=%s", str(similarity_key))
        return {
            constants.response_code: constants.STATUS_OK,
            constants.response_data:
                {
                    constants.SIMILARITY_KEY: similarity_key
                }
        }

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

    def __get_similarity_key_from_rules(self, product, category, section, question):
        """
        check keys in rules and return similarity key
        :param product: the given product
        :param category: L1 key to filter during inference
        :param section: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param question: user query
        :return: Returns string of similairty key
        """
        logger.info("l1_key:%s product=%s section=%s question=%s", category, product, section, question)
        if section == constants.TROB:
            return self._get_similarity_key_trob_from_rules(category, product)

        if section == constants.OPERATION:
            return self._get_similarity_key_oper_from_rules(category, product, question)
        return None

    def _get_similarity_key_trob_from_rules(self, category, product):
        filt_dict = constants.ts_keys.get(category, None)
        if filt_dict is not None:
            logger.debug("TROB filtered dictionary=%s", str(filt_dict))
            for k in filt_dict:
                for v in filt_dict[k]:
                    if product in v:
                        return k
        return None

    def _get_similarity_key_oper_from_rules(self, category, product, question):
        filt_dict = constants.oper_keys.get(category, None)
        if filt_dict is not None:
            logger.debug("Oper filtered dictionary=%s", str(filt_dict))
            for k in filt_dict:
                for v in filt_dict[k]:
                    # TODO: currently added only one rule for anti-wrinkle. filtering will be improved when added \
                    #  more rules
                    if (product in v) and ("구김" in question or "주름" in question):
                        return k
        return None

    def __get_topk_questions(self, info_extr, json_data, query_details, text, top_k):
        """
        Runs text similarity  and get topk canonical keys matching on the given text
        :param info_extr: info extraction module
        :param json_data: json embeddings
        :param query_details: L1 key,prodyct,section to filter during inference
        :param text: str - input text
        :param top_k: top k predictions
        :return: Returns json output with similairty key
        """
        to_return = None
        l1_key, product, question_type,sub_prod_type = query_details[0], query_details[1], query_details[2],query_details[3]
        logger.debug("l1_key:%s product=%s sub_prod_type=%s section=%s", l1_key, product, sub_prod_type, question_type)
        # check rule based approach and return similarity key
        to_return = self.__get_similarity_key_from_rules(product, l1_key, question_type, text)
        logger.info("similarity key from rule based=%s", to_return)
        if to_return is None:
            to_return = self.__get_in_json(json_data, info_extr)
            logger.debug("similarity key from from get in json =%s", to_return)
            if to_return is not None:
                return [(to_return, Pipeline1.max_score)]

        if to_return is None:
            query_embeddings = self.text_sim.compute_embeddings_single([info_extr])
            l1_key = self.__process_l1_key(json_data, l1_key)
            category = self.extract_category(l1_key, product, sub_prod_type, question_type, text)
            flag = False
            question_score = []
            for cat in category:
                for k, v in json_data.items():
                    if k.endswith(cat):
                        if product != sub_prod_type:
                            sentence_embeddings = self.lm_file[product + '|' + sub_prod_type + '|' + question_type + '|' + k]
                        else:
                            sentence_embeddings = self.lm_file[product + '|' + question_type + '|' + k]
                        arr1 = self.text_sim.model_evaluate_single_util(query_embeddings, sentence_embeddings)
                        m = k[:k.rindex('|')]
                        question_score.append((m, np.max(arr1)))
                if flag:
                    break

            if constants.fuzzy_logic:
                fuzz_score, question_score = self.__get_fuzz_score(question_score, text)
                question_score = {(a[0], a[1] * b, b) for a, b in zip(question_score, fuzz_score)}
            top_k_questions = heapq.nlargest(top_k, question_score, key=lambda x: x[1])
            logger.debug("Before score changes=%s", str(top_k_questions))
            top_k_questions=[(item[0], item[2]) for item in top_k_questions]
            top_k_questions=sorted(top_k_questions, key = lambda x: x[1], reverse=True)
            logger.debug("After score changes=%s", str(top_k_questions))
            return top_k_questions
        else:
            to_return = [(to_return, fuzz.token_set_ratio(to_return, text))]
        logger.info("Output from get_topk_keys=%s", str(to_return))
        return to_return

    def __get_fuzz_score(self, question_score, text):
        if constants.top_select_from_cosin:
            question_score = heapq.nlargest(constants.top_k_text_sim_threshold, question_score, key=lambda x: x[1])
        fuzz_score = []
        key_names = [q[0] for q in question_score]
        for idc in key_names:
            fuzz_score.append(fuzz.token_set_ratio(text, idc))
        return fuzz_score, question_score

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

    def extract_category(self, l1_key, product, sub_prod_type, question_type, text):
        """
        extract category of given question
        :param l1_key: str - category
        :param product: product type
        :param question_type: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param text:question
        :return: category
        """
        if product == sub_prod_type:
            if l1_key:
                category = [self.pre_process_key(l1_key)]
            else:
                category = self.category_cache[product + '|' + question_type]
        else:
            if l1_key:
                category = [self.pre_process_key(l1_key)]
            else:
                category = self.category_cache[product + '|' + sub_prod_type + '|' +  question_type]
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
        new_key = self.__delta_category_map(new_key) 
        new_key = re.sub(r'\s+', ' ', new_key)
        new_key = re.sub(r'\.$', '', new_key)
        return new_key

    def __delta_category_map(self, l_key):
        """
        Syncs the keys given by classifier and the dataset incase there is a mismatch in TS.
        This map is just a temporary set-up and will be taken care without the mapping soon.
        :param l_key: Type key in the json
        :return: preprocessed key
        """
        if l_key == "error":
            l_key = "error messages"
        elif l_key == "noise":
            l_key = "noises"
        elif l_key == "wifi problem":
            l_key = "wi-fi"
        return l_key
