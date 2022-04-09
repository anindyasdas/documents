"""
-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
-------------------------------------------------
"""
import os
from pathlib import Path

MODEL_PATH = os.path.join(Path(os.path.abspath(os.path.dirname(os.path.realpath(__file__)))).parents[1],
                          'dataset', 'models', 'srl')
MODEL_NAME = 'bert-base-srl-2020.03.24'
MODEL = os.path.join(Path(MODEL_PATH), MODEL_NAME)

# Model can be downloaded from "https://storage.googleapis.com/allennlp-public-models/bert-base-srl-2020.03.24.tar.gz"

# List of auxilary verbs
AUX_LIST = ["am", "are", "be", "been", "being", "can", "could", "is", "was", "were", "has", "do", "would", "should",
            "will", "while"]
