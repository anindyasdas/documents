"""
-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------
@author: anusha.kamath@lge.com
"""
import os

current_folder = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','..','dataset')) + '/'

MAX_LENGTH = 45

#The model name is model_name = 'facebook/bart-large-cnn'
MODEL_PATH = current_folder + 'models/summarizer/model/'
TOKENIZER_PATH = current_folder + 'models/summarizer/tokenizer/'
DATA_PATH = current_folder + 'dataset/summarizer/'
