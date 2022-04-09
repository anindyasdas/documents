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
from ..classifier.classifier_engine import ClassifierEngine
from ..text_similarity import base_question_extraction
import numpy as np
import pandas as pd
from ...external.constituency_parser.constituency_parser import ContituencyParserWrapper
from ...external.srl.srl_parser import SRLWrapper


class Pipeline3:
    """
    Constituency Paser to extract Noun Phrases and Verb Phrases
    """
    __instance = None

    @staticmethod
    def get_instance(text_sim, info_extr):
        """ Static access method to get the singleton instance"""
        if Pipeline3.__instance is None:
            Pipeline3(text_sim, info_extr)
        return Pipeline3.__instance

    def __init__(self, text_sim, info_extr):
        """ Virtually private constructor. """
        if Pipeline3.__instance is not None:
            raise Exception("Pipeline1 is not instantiable")
        else:
            Pipeline3.__instance = self
        self.initialize(text_sim, info_extr)

    def initialize(self, text_sim, info_extr):
        """
        Initializes hdf5 file
        :param text_sim: text similarity module
        :param info_extr: info extraction module
        :return: None
        """
        self.text_sim = text_sim
        self.info_extr = info_extr
        try:
            self.lm_file = h5py.File(constants.PIPELINE_3_LM_EMB, "r")
        except:
            with h5py.File(constants.PIPELINE_3_LM_EMB, "w") as f:
                for p in constants.PRODUCTS:
                    for t in [constants.SPEC, constants.TROB, constants.FAQ]:
                        orig = pd.read_excel(constants.INPUT_FILES[p][t], sheet_name='ORIG')
                        orig = orig.applymap(str)
                        self.get_embeddings(p, t, orig, f)

            self.lm_file = h5py.File(constants.PIPELINE_3_LM_EMB, "r")

    def get_embeddings(self, product, question_type, data, lm_file):
        """
        Gets all embeddings of the info extraction, srl, constituency parser outputs and stores in hdf5
        :param data: input dataframe
        :param product: product
        :param question_type: SPEC, TROB, FAQ
        :param lm_file: hdf5 file
        :return: None
        """
        key2 = product + '|' + question_type + '|'
        for name, group in data.groupby([constants.TYPE]):
            key1 = key2 + name
            lm_file.create_dataset(key1, data=self.text_sim.compute_embeddings_single(group.Key.values))

    def extract(self, text, question_type, product, top_k=1, filter_by_cat=True):
        """
        Runs info extraction and synonym matching on the given text
        :param text: str - input text
        :param question_type: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param product: the given product
        :param top_k: top k predictions
        :return: Returns 5 outputs -
        [0] - Text Similarity top k predictions,
        [1] - Category (0 - Error Codes, 1 - Noise, 2 - Cooling Problem, 3 - Ice Problem, 4 - WiFi Problem, 4 - Problem)
        [2] - Info extraction output
        [3] - Constituency parser output  - {NP: str1|str2|str3..., VB:str4|str5|str6...}
        [4] - SRL parser output  - {cause: str1|str2|str3..., temp:str4|str5|str6..., purpose: str7|str8|str9}
        """
        orig = pd.read_excel(constants.INPUT_FILES[product][question_type], sheet_name='ORIG')
        orig = orig.applymap(str)
        info_extr, _ = self.info_extr.extract_info_single(text, question_type, product, self.text_sim)

        query_embeddings = self.text_sim.compute_embeddings_single([info_extr])

        if filter_by_cat:
            if question_type == constants.TROB:
                cs = ClassifierEngine()
                category_str = cs.execute_classifier(text, "Type")
                category = [str(constants.reverse_dict[category_str])]
            else:
                category = ['nan']
        else:
            category = list(set(orig.Type.values))

        question_score = []
        for cat in category:
            orig_cat = orig[orig[constants.TYPE] == cat]
            key1 = product + '|' + question_type + '|' + cat
            arr1 = self.text_sim.model_evaluate_single_util(query_embeddings, self.lm_file[key1])
            values = orig_cat['Value'].values
            question_score.extend([(v, s) for v, s in zip(values, arr1)])
        top_k_questions = heapq.nlargest(top_k, question_score, key=lambda x: x[1])

        return {
            constants.response_code: constants.STATUS_OK,
            constants.response_data:
                {
                    "similarity_key": [q[0] for q in top_k_questions],
                    "prob_key": None,
                    "prob_value_specific": None,
                    "prob_value_general": None,
                    "cons_parser": None,
                    "srl": None
                }
        }
