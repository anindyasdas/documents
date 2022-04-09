# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import numpy as np
import pandas as pd

from . import constants as ClassifierConstants


class Similarity:
    def __compute_cosine_similarity(self, w1, w2):
        """
        computation of distance between w1 and w2 vectors.
        Args:
             w1: First vector used in computation of cosine similarity
             w2: Second vector used in computation of cosine similarity
        """
        cosine_similarity = np.dot(w1, w2) / (np.linalg.norm(w1) * np.linalg.norm(w2))
        return cosine_similarity

    def compute_top_influence(self, test_sentence, test_vec, train_sentence, train_vec, k=5):
        """
        computation of the top k influencing entries in training for a test sentence
        Args:
            test_sentence : list of testing sentences
            test_vec : vectors for test sentences
            train_sentence : list of training sentences
            train_vec : vectors for train sentences
            k : no of top influencers for each entry
        """
        df = pd.DataFrame(columns=["test sentence", "train sentence", "influence"])
        start = 0
        sentence_id = 0

        for test_row in test_vec:
            feature = []
            for train_row in train_vec:
                feature.append(self.__compute_cosine_similarity(test_row, train_row))
            feature = np.array(feature)
            print(feature.shape)
            indices = (-feature).argsort()[:k]

            i = start
            for x in indices:
                print(x)
                df.loc[i, "test sentence"] = test_sentence[sentence_id]
                df.loc[i, "train sentence"] = train_sentence[x]
                df.loc[i, "influence"] = feature[x]
                i = i + 1
            start = i + 2
            sentence_id = sentence_id + 1
        print("writing debug report")
        df.to_excel(ClassifierConstants.DEBUG_FILE, engine='xlsxwriter')
