"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""
import h5py

from . import constants
import pandas as pd
import numpy as np
import heapq
from scipy.spatial.distance import cosine
from ..classifier.classifier_engine import ClassifierEngine
import re


class Pipeline2:
    """
    Constituency Paser to extract Noun Phrases and Verb Phrases
    """
    __instance = None

    @staticmethod
    def get_instance(text_sim, info_extr):
        """ Static access method to get the singleton instance"""
        if Pipeline2.__instance is None:
            Pipeline2(text_sim, info_extr)
        return Pipeline2.__instance

    def __init__(self, text_sim, info_extr):
        """ Virtually private constructor. """
        if Pipeline2.__instance is not None:
            raise Exception("Pipeline2 is not instantiable")
        else:
            Pipeline2.__instance = self
        self.initialize(text_sim, info_extr)

    def initialize(self, text_sim, info_extr, use_srl=False):
        """
        Initializes hdf5 file
        :param text_sim: text similarity module
        :param info_extr: info extraction module
        :return: None
        """
        self.text_sim = text_sim
        self.info_extr = info_extr
        if use_srl:
            self.cons_parser = ContituencyParserWrapper.get_instance()
            self.srl_parser = SRLWrapper.get_instance()
        self.orig_cache = {}

        try:
            self.lm_file = h5py.File(constants.PIPELINE_2_LM_EMB, "r")
            for p in constants.PRODUCTS:
                for t in [constants.TROB]:
                    orig = pd.read_excel(constants.INPUT_FILES[p][t], sheet_name='ORIG')
                    orig = orig.applymap(str)
                    orig = orig.apply(lambda x: self.__preprocess_key(x))
                    self.orig_cache[p + '|' + t] = orig
        except:
            with h5py.File(constants.PIPELINE_2_LM_EMB, "w") as f:
                for p in constants.PRODUCTS:
                    for t in [constants.TROB]:
                        orig = pd.read_excel(constants.INPUT_FILES[p][t], sheet_name='ORIG')
                        orig = orig.applymap(str)
                        orig = orig.apply(lambda x: self.__preprocess_key(x))
                        self.orig_cache[p + '|' + t] = orig
                        self.get_embeddings(orig, p, t, f, weighted=True)

        self.lm_file = h5py.File(constants.PIPELINE_2_LM_EMB, "r")

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
        orig = self.orig_cache[product + '|' + question_type]
        category = list(map(lambda x: x.lower(), list(set(orig.Type.values))))

        info_extr, is_l1 = self.info_extr.extract_info_single(text, constants.PIPELINE_2, question_type, product,
                                                              self.text_sim)
        print('info_extr', info_extr)
        import time
        start = time.time()
        const_output = self.cons_parser.get_phrases(text)
        srl_output = self.srl_parser.get_srl_output_for_ker(text)
        end = time.time()
        print(end - start)

        test_data = pd.DataFrame()
        test_data[constants.INFO_EXTRACTION] = [info_extr]
        test_data[constants.NP] = [const_output[constants.NP]]
        test_data[constants.VB] = [const_output[constants.VB]]
        test_data[constants.TEMP] = [srl_output[constants.TEMP]]
        test_data[constants.CAUSE] = [srl_output[constants.CAUSE]]
        test_data[constants.PURPOSE] = [srl_output[constants.PURPOSE]]

        category_str = 'problem'
        if filter_by_cat:
            if question_type == constants.TROB:
                cs = ClassifierEngine()
                category_str = cs.execute_classifier(text, "Type")
                category = [category_str]
            else:
                category = ['nan']

        question_score = []

        test_data[constants.TYPE] = ['test']
        test_dict = {}

        self.get_embeddings(test_data, product, question_type, test_dict, True)

        key2 = product + '|' + question_type + '|' + 'test'
        key2 = key2.lower()

        for cat in category:
            orig_cat = orig[orig[constants.TYPE] == cat]
            scores = np.zeros([orig_cat.shape[0], 3])
            key1 = product + '|' + question_type + '|' + cat
            key1 = key1.lower()
            self.get_info_extraction_scores(test_dict, key1, key2, scores)
            self.get_constituency_scores(test_dict, key1, key2, scores)
            self.get_srl_scores(test_dict, key1, key2, scores)

            scores = [(a * b * c) for a, b, c in zip(scores[:, 0], scores[:, 1], scores[:, 2])]
            values = orig_cat['Value'].values
            grouped_key = orig_cat['Grouped Key'].values
            question_score.extend([(v, g, s) for v, g, s in zip(values, grouped_key, scores)])

        top_k_questions = heapq.nsmallest(top_k, question_score, key=lambda x: x[2])

        return {
            constants.response_code: constants.STATUS_OK,
            constants.response_data:
                {
                    "similarity_key": None,
                    "prob_key": category_str,  # from whom we have to take classifier/info extraction
                    "prob_value_specific": top_k_questions[0][0].replace('\n', ' '),
                    "prob_value_general": top_k_questions[0][1].replace('\n', ' '),
                    "cons_parser": {constants.NP: const_output[constants.NP].split('|'),
                                    constants.VB: const_output[constants.VB].split('|')},
                    "srl": {constants.TEMP: srl_output[constants.TEMP].split('|'),
                            constants.CAUSE: srl_output[constants.CAUSE].split('|'),
                            constants.PURPOSE: srl_output[constants.PURPOSE].split('|')}
                }
        }

    def get_embeddings(self, data, product, question_type, lm_dict, weighted):
        """
        Gets all embeddings of the info extraction, srl, constituency parser outputs and stores in hdf5
        :param data: input dataframe
        :param product: product
        :param question_type: SPEC, TROB, FAQ
        :param lm_dict: dict or hdf5 file
        :return: None
        """
        key2 = product + '|' + question_type + '|'
        for name, group in data.groupby([constants.TYPE]):
            key1 = key2 + name + '|'
            self.__handle_single_get_emb(group, key1, constants.INFO_EXTRACTION, lm_dict, weighted)

            self.__handle_multi_get_emb(group, key1, constants.NP, lm_dict, weighted)
            self.__handle_multi_get_emb(group, key1, constants.VB, lm_dict, weighted)
            self.__handle_multi_get_emb(group, key1, constants.TEMP, lm_dict, weighted)
            self.__handle_multi_get_emb(group, key1, constants.PURPOSE, lm_dict, weighted)
            self.__handle_multi_get_emb(group, key1, constants.CAUSE, lm_dict, weighted)

    def get_single_embs(self, values, weighted):
        """
        Gets the embeddings on info extraction
        :param values: list of str
        :param weighted:boolean
        :return: embeddings
        """
        embs = np.zeros(shape=[len(values), 768])
        for i, val in enumerate(values):
            if val == 'nan':
                embs[i] = np.zeros([768])
            else:
                if weighted:
                    embs[i] = self.text_sim.compute_embeddings_single_by_word(val, self.info_extr)
                else:
                    embs[i] = self.text_sim.compute_embeddings_single([val])[0]
        return embs

    def __handle_single_get_emb(self, data, key1, col, lm_dict, weighted):
        """
        Gets the embeddings on info extraction
        :param data: dataframe
        :param col: column
        :param lm_dict: dictionary or hdf5 file
        :param weighted:boolean
        :return: embeddings
        """
        key = key1 + col
        key = key.lower()
        if key not in lm_dict:
            emb = self.get_single_embs(data[col].values, False)
            if type(lm_dict) == dict:
                lm_dict[key] = emb
            else:
                lm_dict.create_dataset(key, data=emb)

    def __handle_multi_get_emb(self, data, key1, col, lm_dict, weighted):
        """
        Gets the embeddings on srl or constituency parser outputs
        :param data: dataframe
        :param col: column
        :param lm_dict: dictionary or hdf5 file
        :param weighted:boolean
        :return: embeddings
        """

        key = key1 + col
        key = key.lower()
        if key not in lm_dict:
            val = data[col].values
            emb_tot = np.zeros([len(val), 768])
            for i, row in enumerate(val):
                row_vals = row.split('|')
                emb = self.get_single_embs([row_vals], weighted=True)[0]
                emb_tot[i] = emb
            if type(lm_dict) == dict:
                lm_dict[key] = emb_tot
            else:
                lm_dict.create_dataset(key, data=emb_tot)

    def get_cosine_scores(self, orig_embs, test_emb):
        """
        Gets cosine scores
        :param orig_embs: list of embeddings
        :param test_emb: test embedding
        :return: scores
        """
        scores = []
        for emb in orig_embs:
            c = cosine(emb, test_emb)
            if not np.isnan(c):
                scores.append(c)
            else:
                scores.append(1)
        return scores

    def get_cosine_scores_group(self, emb1, emb2):
        """
        Gets cosine scores on srl and constituency parser outputs
        :param emb1: embedding 1
        :param emb2: embedding 2
        :return: scores
        """
        s = 0

        for e1, e2 in zip(emb1, emb2):
            c = cosine(e1, e2)
            if not np.isnan(c):
                s += c
            else:
                s += 1
        return s / emb1.shape[0]

    def get_mean_emb(self, embs):
        """
        calculate the mean of given embeddings and returns
        :param embs: embedding
        :return: mean
        """
        sum_emb = np.zeros(shape=[embs.shape[1]])
        cnt = 0
        for emb in embs:
            if np.sum(emb, axis=0) != 0:
                sum_emb += emb
                cnt += 1
        if cnt == 0:
            return 0
        return sum_emb / cnt

    def max_conv_score(self, emb1, emb2):
        """
        computes convolution (without reversal) on list of embedding 1 and embedding 2
        :param emb1: list of embedding 1
        :param emb2: list of embedding 2
        :return: score
        """
        mean_emb_1 = self.get_mean_emb(emb1)
        mean_emb_2 = self.get_mean_emb(emb2)
        cos = cosine(mean_emb_1, mean_emb_2)
        if not np.isnan(cos):
            return cos
        return 1

    def get_cosine_scores_conv(self, orig_embs, test_emb):
        """
        computes convolution (without reversal) on list of embedding 1 and embedding 2
        :param orig_embs: list of embedding 1
        :param test_emb: list of embedding 2
        :return: scores
        """
        scores = []

        for emb in orig_embs:
            scores.append(self.max_conv_score(emb, test_emb))

        return scores

    def get_info_extraction_scores(self, test_dict, key1, key2, scores):
        """
        Computes info extraction scores
        :param test_dict: dict or hdf5 file
        :param key1: str key
        :param scores: scres array
        :return:
        """
        key1 = key1 + '|' + constants.INFO_EXTRACTION
        key2 = key2 + '|' + constants.INFO_EXTRACTION
        scores[:, 0] = self.get_cosine_scores(self.lm_file[key1], test_dict[key2][0])

    def get_constituency_scores(self, test_dict, key1, key2, scores):
        """
        Computes constituency parser scores
        :param test_dict: dict or hdf5 file
        :param key1: str key
        :param scores: scres array
        :return:
        """
        key_1 = key1 + '|' + constants.NP.lower()
        key_2 = key2 + '|' + constants.NP.lower()
        scores1 = self.get_cosine_scores(self.lm_file[key_1], test_dict[key_2][0])
        key_1 = key1 + '|' + constants.VB.lower()
        key_2 = key2 + '|' + constants.VB.lower()
        scores2 = self.get_cosine_scores(self.lm_file[key_1], test_dict[key_2][0])
        scores[:, 1] = [(a * b) ** (1 / 2) for a, b in zip(scores1, scores2)]

    def get_srl_scores(self, test_dict, key1, key2, scores):
        """
        Computes srl scores
        :param test_dict: dict or hdf5 file
        :param key1: str key
        :param scores: scres array
        :return:
        """
        key_1 = key1 + '|' + constants.TEMP.lower()
        key_2 = key2 + '|' + constants.TEMP.lower()
        scores1 = self.get_cosine_scores(self.lm_file[key_1], test_dict[key_2][0])
        key_1 = key1 + '|' + constants.CAUSE.lower()
        key_2 = key2 + '|' + constants.CAUSE.lower()
        scores2 = self.get_cosine_scores(self.lm_file[key_1], test_dict[key_2][0])
        key_1 = key1 + '|' + constants.PURPOSE.lower()
        key_2 = key2 + '|' + constants.PURPOSE.lower()
        scores3 = self.get_cosine_scores(self.lm_file[key_1], test_dict[key_2][0])
        scores[:, 2] = [(a * b * c) ** (1 / 3) for a, b, c in zip(scores1, scores2, scores3)]

    def __preprocess_key(self, keys):
        """
        preprocess the keys
        :param keys: product manual problem keys
        :return: preprocesed keys
        """
        keys_pp = [key.lower() for key in keys]
        keys_pp = [re.sub('\\.$', '', key) for key in keys_pp]
        return keys_pp