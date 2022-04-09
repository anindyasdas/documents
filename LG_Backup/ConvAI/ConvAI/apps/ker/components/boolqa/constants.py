"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""

import os

CURRENT_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','..','dataset')) + '/'

model_path = CURRENT_FOLDER + '/models/boolqa/model_save'
SPACY_MODEL = 'en_core_web_sm'
CONFIG_FILE = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))+'/'+'experiments.conf'
NO = 'no'
YES = 'yes'
