"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import os
from pathlib import Path
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))

NP = 'NP'
VB = 'VB'
CHILDREN = 'children'

MODEL_PATH = os.path.join(Path(os.path.abspath(os.path.dirname(os.path.realpath(__file__)))).parents[1], 'dataset',
                          'models', 'constituency_parser')
MODEL_NAME = 'elmo-constituency-parser-2020.02.10'
MODEL = os.path.join(Path(MODEL_PATH), MODEL_NAME)

# model can bbe downloaded from
# 'https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz'


AUX_VERBS = {"am", "are", "be", "been", "being", "can", "could", "is", "was", "were", "has", "do",
             "would", "should", "will", "while"}
