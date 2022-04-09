# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
 * Copyright(c) 2020-2022 by LG Electronics.
 * Confidential and Proprietary All Rights Reserved.
 *-------------------------------------------------*/
"""
import errno
import pickle
import json

import pandas as pd
import numpy as np
import heapq
import pyhocon
import os
from . import utils
from . import constants
import re

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class InfoExtractionBase:
    """
    Info Extraction to extract information from a given text
    """

    def __init__(self, name, config=None, evaluate=True):
        self.config = pyhocon.ConfigFactory.parse_file(constants.CONFIG_FILE)[name]
        if config is not None:
            for k, v in config.items():
                self.config[k] = v
        self.config["log_dir"] = self.__mkdirs(os.path.join(self.config["log_root"], name))
        error_id = self.__get_words_from_file(constants.error_codes_file)
        self.error_id_reg = '|'.join(['\\b' + ei + '\\b' for ei in error_id])

        error_id = [ei.lower() for ei in error_id]
        self.error_id_reg = '|'.join(['\\b' + ei + '\\b' for ei in error_id])
        self.exclude_after = self.config['exclude_after']
        self.rem_words = self.config['rem_words']
        self.prod_type_val = {}

        self._get_max_idf_values()
        if evaluate:
            self.info_extract_model = pickle.load(open(constants.model_name, 'rb'))

    def __get_words_from_file(self, file):
        """
        read the file and returns list of words
        :param file: str: input file path
        :return: list of words
        """
        with open(file,encoding="utf8") as f:
            words = f.readlines()
        return [w.strip('\n') for w in words]

    def __mkdirs(self, path):
        """
        Makes a directory if required in path
        :param path: str: path
        :return: path
        """
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        return path

    def extract_info_single(self, text, pipeline=constants.PIPELINE_1, question_type=constants.TROB,
                            product=constants.WASHING_MACHINE, text_sim=None):
        """
        Extracts info from a single text
        :param text: text
        :param pipeline: pipeline to be used text sim or info based
        :param question_type: SPEC or TROB
        :param product: WASHING_MACHINE OR REFRIGERATOR
        :param text_sim: BERT Embedding model to get sentence embeddings
        :return: Return extracted text
        """
        raise ValueError('Child class should implement this method')

    def _preprocess(self, text):
        """
        Preprocess given text
        :param text: Given text
        :return: proprocessed text
        """
        text = str(text).lower().strip().strip(".")
        if "[_]-->end" in text or "[_]" in text:
            text = text.replace("[_]-->end", "구김 방지") #for handling anti wrinkle error code
            text = text.replace("[_]", "구김 방지") #for handling anti wrinkle error code
        text = re.sub('\\bde2\\b', 'dez', text)
        return re.split("[^\\w_]+", text)

    def train(self, path, embedding_model):
        """
        Train the model
        :param path: Train data path
        :param embedding_model: BERT Embedding model
        :return: None
        """
        sentences, target = embedding_model.get_data(path)
        input_ids_vals, input_mask_vals, segment_ids_vals = embedding_model.convert_sentences_to_features(sentences,
                                                                                                          constants.MAX_LENGTH)
        out = embedding_model.get_embedding(input_ids_vals, input_mask_vals, segment_ids_vals)
        train_features = out['pooled_output']
        self.__train_model(train_features, target)

    def __train_model(self, train_features, train_labels):
        """
        Train the model
        :param train_features: BERT features
        :param train_labels: labels
        :return: None
        """
        logger.info("training the model")
        self.info_extract_model.fit(train_features, train_labels)
        pickle.dump(self.info_extract_model, open(constants.model_name, 'wb'))

    def _get_text_substring(self, prep_text_tok, prep_text_rm):
        """
        Get subtring of a text from the start and end words of the stop word removed text
        :param prep_text_tok: preprocessed text
        :param prep_text_rm: preprocessed text with stop words rem
        :return extracted sub text
        """
        i1 = prep_text_tok.index(prep_text_rm[0])

        i2 = len(prep_text_tok) - prep_text_tok[::-1].index(prep_text_rm[-1]) - 1

        return prep_text_tok[i1:i2 + 1]

    def extract_info_file(self, level=constants.L1_L2_L3, product=constants.WASHING_MACHINE):
        """
        extract info from file
        :param level: question level
        :param product: product type
        :return: None
        """
        extracted = []

        df = pd.read_excel(constants.INPUT_FILES[product][constants.TROB], sheet_name=level)
        texts = df["Questions"].to_list()
        targets = df["Info_Extraction_Labels"].to_list()

        for text, target in zip(texts, targets):
            ex = self.extract_info_single(text)
            # print(ex)
            extracted.append(ex)

        extracted = np.array(extracted)

        df['Info_Extraction_Prediction'] = extracted[:, 0]
        df['Type_Prediction'] = extracted[:, 1]
        utils.append_df_to_excel(constants.INPUT_FILES[product][constants.TROB], df, level, index=False)

        # df.to_csv(Constants.trouble_shoot_data, sep='\t', index=False)

    def _exclude(self, text):
        """
        Excludes the text after the occuance of exclude_after words
        text: str- input text
        return: exlcuded text
        """
        words = [w.strip() for w in text.lower().split()]
        j = len(text) - 1
        for ea in self.exclude_after:
            if ea in words:
                ind = words[::-1].index(ea)
                j = len(words) - ind - 1
                break
        output = ' '.join(words[:j]).strip()
        if len(output) == 0:
            return text
        return output

    def extract_info_bulk(self, texts, pipeline=constants.PIPELINE_1, question_type=constants.TROB,
                          product=constants.WASHING_MACHINE, text_sim=None):
        """
        extract info from a list of texts
        :param texts: list of strings
        :param pipeline: pipeline to be used text sim or info based
        :param question_type: SPEC or TROB
        :param product: WASHING_MACHINE OR REFRIGERATOR
        :param text_sim: BERT Embedding model to get sentence embeddings
        :return: extracted list of info
        """
        extracts = []
        for text in texts:
            extracts.append(self.extract_info_single(text, pipeline, question_type, product, text_sim))

        return extracts

    def _get_max_idf_values(self):
        """
        Gets top k of idf values after tfidf
        :param texts: file from which the data has to read - Troubleshoot data
        :return: max idf values
        """
        try:
            self.read_stored_files()
        except:
            trob_data = self.get_data()

            trob_data = pd.concat(trob_data, axis=0)

            preprocessed_texts = [self._preprocess(text) for text in list(trob_data['Questions'].values)]

            wordfreq = self.get_word_frequency(preprocessed_texts)

            word_idf_values = {}
            max_idf = 0
            for token in wordfreq:
                doc_containing_word = 0
                for document in preprocessed_texts:
                    if token in document:
                        doc_containing_word += 1
                idf = np.log(len(preprocessed_texts) / (1 + doc_containing_word))

                if idf > max_idf:
                    max_idf = idf

                word_idf_values[token] = idf

            self.get_word_idf(max_idf, word_idf_values)

            self.word_idf_values_sim = word_idf_values
            self.word_idf_values_info = word_idf_values.copy()

            k1 = self.config['top_idf_ratio_sim']
            k2 = self.config['top_idf_ratio_info']

            self.__update_word_idf_val(self.word_idf_values_sim, k1, trob_data, constants.WORD_IDF_VALUES_FILE_SIM)
            self.__update_word_idf_val(self.word_idf_values_info, k2, trob_data, constants.WORD_IDF_VALUES_FILE_INFO)

    def get_data(self):
        """
        read all products data file and returns
        :param : none
        :return : data : list of data frames
        """
        data = []
        for p in constants.PRODUCTS:
            for qt in [constants.SPEC, constants.TROB, constants.FAQ]:
                trob_data_p = pd.read_excel(constants.INPUT_FILES[p][qt], sheet_name=constants.L1_L2_L3)
                data.append(trob_data_p)
            data.append(trob_data_p)
        return data

    def read_stored_files(self):
        """
        read the idf values of similarity & info pipelines
        :param : none
        :return: none
        """
        with open(constants.WORD_IDF_VALUES_FILE_SIM, 'r') as f:
            word_idf_values = json.load(f)
            self.word_idf_values_sim = word_idf_values
        with open(constants.WORD_IDF_VALUES_FILE_INFO, 'r') as f:
            word_idf_values = json.load(f)
            self.word_idf_values_info = word_idf_values

    def get_word_idf(self, max_idf, word_idf_values):
        """
        calculate word idf score
        :param max_idf : max idf score value
        :param word_idf_values : dict of idf values
        :return none
        """
        for k, v in word_idf_values.items():
            word_idf_values[k] = v / max_idf

    def get_word_frequency(self, preprocessed_texts):
        """
        calculate word frequency for preprocessed text
        :param preprocessed_texts : preprocessed_texts
        :return wordfreq : list of word frequencies
        """
        wordfreq = {}
        for tokens in preprocessed_texts:
            for token in tokens:
                if token not in wordfreq.keys():
                    wordfreq[token] = 1
                else:
                    wordfreq[token] += 1
        return wordfreq

    def __update_word_idf_val(self, word_idf_values, k, trob_data, file):
        """
        update idf values to stop words,synonyms of noise...and writes back to the file
        :param word_idf_values : list of idf values
        :param k : value to qualify idf values
        :param trob_data : list of data
        :param file : input file
        :return none
        """
        min_idf_values = heapq.nsmallest(int(len(word_idf_values) * (1 - k)), word_idf_values, key=word_idf_values.get)
        min_idf_values = set(min_idf_values)

        for key in self.__unique_keys(trob_data):
            if key in min_idf_values:
                min_idf_values.remove(key)

        for key in self.rem_words:
            word_idf_values[key] = 0
            min_idf_values.add(key)

        noises = constants.NOISE
        for n in noises:
            word_idf_values[n] = 0
            min_idf_values.add(n)

        for key in self.exclude_after:
            min_idf_values.add(key)
            word_idf_values[key] = 0

        for key in min_idf_values:
            word_idf_values[key] = 0

        # with open(Constants.MIN_IDF_VALUES_FILE, 'w') as f:
        #     f.writelines("\n".join(min_idf_values))
        with open(file, 'w') as f:
            json.dump(word_idf_values, f)

    def __unique_keys(self, trob_data):
        """
        Gets unique keys from file
        :param trob_data: input data
        :return: list of str
        """
        keys = set()
        for key in trob_data['Key'].values:
            key = key.replace('_', ' ')
            key = key.replace('/', ' ')
            key = key.replace('  ', ' ')
            key = key.strip()
            for k in self._preprocess(key):
                w = k.strip()
                if w not in stop_words:
                    keys.add(w)
                w = self.lemmatizer.lemmatize(w)
                if w not in stop_words:
                    keys.add(w)
        return keys
