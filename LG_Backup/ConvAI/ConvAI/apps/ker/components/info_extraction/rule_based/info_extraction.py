# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
 * Copyright(c) 2020 by LG Electronics.
 * Confidential and Proprietary All Rights Reserved.
 *-------------------------------------------------*/
@author: vishwaas@lge.com
"""

from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession

config = ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)

import sys
import os
import re

from nltk.corpus import stopwords
from ..info_extraction_base import InfoExtractionBase
from .. import constants

stop_words = stopwords.words('english')
import numpy as np


class InfoExtractionRB(InfoExtractionBase):
    """
    Info Extraction to extract information from a given text
    """

    def __init__(self, config=None, evaluate=True):
        super(InfoExtractionRB, self).__init__('RULEBASED', config, evaluate)

    def extract_info_single(self, text, pipeline=constants.PIPELINE_1, question_type=constants.TROB,
                            product=constants.WASHING_MACHINE, text_sim=None):
        """
        Extracts info from a single text
        :param text: text
        :return: Return extracted text
        :embedding_model: BERT Embedding model to get sentence embeddings
        """
        prep_text_split = self._preprocess(text)
        prep_text = ' '.join(prep_text_split)
        self.text_sim = text_sim

        if question_type == constants.TROB:
            search = re.search(self.error_id_reg, prep_text)

            if search is not None:
                return (prep_text[search.span()[0]: search.span()[1]], constants.ERROR_CODE_TYPE)

        if pipeline == constants.PIPELINE_1:
            return prep_text, 1

        if pipeline == constants.PIPELINE_2:
            argmax = 1
            word_idf_values = self.word_idf_values_info
            '''
            commenting out this part, since it is reducing the accuracy and increasing the latency
            spans = [prep_text]
            input_ids_vals, input_mask_vals, segment_ids_vals = self.embedding_model.convert_sentences_to_features(spans,
                                                                                                              Constants.MAX_LENGTH)
            out = self.embedding_model.get_embedding(input_ids_vals, input_mask_vals, segment_ids_vals)
            test_features = out['pooled_output']

            bert_preds = self.info_extract_model.predict_proba(test_features)

            argmax = np.argmax(bert_preds[0])
            '''
        else:
            word_idf_values = self.word_idf_values_sim
            argmax = -1

        prep_text_rm = []

        for word in prep_text_split:
            if self.checkSafe(word, word_idf_values):
                prep_text_rm.append(word)

        if len(prep_text_rm) == 0:
            text = prep_text
        else:
            if pipeline == constants.PIPELINE_2:
                text = ' '.join(prep_text_rm)
            else:
                text = ' '.join(self._get_text_substring(prep_text_split, prep_text_rm))

        '''
        commenting out this part, since it is reducing the accuracy and increasing the latency
        if pipeline == Constants.PIPELINE_2:
           if argmax+1 == Constants.NOISE_TYPE:
               ex_noise = self.extract_noise(prep_text_rm)
               if len(ex_noise)==0:
                   return prep_text, Constants.NOISE_TYPE
               else:
                   return ex_noise, Constants.NOISE_TYPE
           return self._exclude(text), Constants.PROBLEM_TYPE
       '''

        return self._exclude(text), argmax

    def checkSafe(self, word, word_idf_values):
        if len(word) == 0:
            return False
        if word in stop_words:
            return False
        if word in word_idf_values and word_idf_values[word] == 0:
            return False

        return True

    def get_idf_score(self, word):
        if word in self.word_idf_values_info:
            return self.word_idf_values_info[word]
        else:
            return 1

    def extract_noise(self, text):
        noises = constants.NOISE
        noiseless_text = []
        noise_word = None
        noise_ind = -1
        for i, t in enumerate(text):
            if t not in noises:
                noiseless_text.append(t)
            else:
                noise_word = t
                noise_ind = i

        noise = list(noises)[0]
        if len(noiseless_text) == 0:
            if noise_word is not None:
                return noise_word
            else:
                return ' '.join(text)
        else:
            if noise_ind > 1:
                return text[noise_ind - 1]
            else:
                if self.text_sim is None:
                    from components.text_similarity.siamese_bert import SiameseBERT
                    self.text_sim = SiameseBERT(None)
                return self.text_sim.model_evaluate_single(noise, noiseless_text)[0]

    def is_in_error_id(self, text):
        """
        checks if the given text is error code
        :param text: str
        :return: boolean
        """
        prep_text = ' '.join(self._preprocess(text))
        search = re.search(self.error_id_reg, prep_text)

        if search is not None:
            return prep_text[search.span()[0]: search.span()[1]]

        return None