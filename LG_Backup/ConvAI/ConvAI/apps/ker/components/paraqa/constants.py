"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""

import os

current_folder = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','..','dataset')) + '/'

model_name = current_folder+'models/paraqa'+ '/bert-large-uncased-whole-word-masking-finetuned-squad'
SPACY_MODEL = 'en_core_web_sm'
CONFIG_FILE = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))+'/'+'experiments.conf'