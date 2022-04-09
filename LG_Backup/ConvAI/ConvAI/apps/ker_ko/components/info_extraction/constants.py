# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
 * Copyright(c) 2020 by LG Electronics.
 * Confidential and Proprietary All Rights Reserved.
 *-------------------------------------------------*/
@author: vishwaas@lge.com
"""

import os
import sys

current_folder = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'dataset')) + '/'
data_set = current_folder + 'dataset/info_data'
model_path = current_folder + 'models/info_models/'
vocab = current_folder + 'vocab.txt'
model_name = model_path + 'info_extract.sav'
MAX_LENGTH = 16
error_codes_file = data_set + '/error_codes.txt'
technical_words_file = data_set + '/technical_words.txt'
L1_L2_L3 = 'L1_L2_L3'
NOISE = {'noise', 'noises', 'sound', 'sounds'}
SPEC = 'SPEC'
TROB = 'TROB'
FAQ = 'FAQ'
OPERATION = 'OPERATION'

CONFIG_FILE = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + '/' + 'experiments.conf'
ELMO_MODULE = model_path + 'elmo'
INPUT_FILE_SPEC = data_set + '/SpecQA_All_L1_L2.xlsx'
INPUT_FILE_TROB = data_set + '/Troubleshooting_all_L1_L2.xlsx'
ERROR_CODE_TYPE = 0
NOISE_TYPE = 1
PROBLEM_TYPE = 2

WASHING_MACHINE = 'washing machine'
REFRIGERATOR = 'refrigerator'
AC = 'air conditioner'
VACUUM_CLEANER = 'vacuum cleaner'
MICROWAVE_OVEN = 'microwave oven'
DISH_WASHER = 'dish washer'

PRODUCTS = [WASHING_MACHINE, REFRIGERATOR, AC, VACUUM_CLEANER, MICROWAVE_OVEN, DISH_WASHER]

MIN_IDF_VALUES_FILE = data_set + '/min_idf_values.txt'
WORD_IDF_VALUES_FILE_SIM = data_set + '/word_idf_values_sim.json'
WORD_IDF_VALUES_FILE_INFO = data_set + '/word_idf_values_info.json'

INPUT_FILES = {}

PIPELINE_1 = 'PIPELINE_1'
PIPELINE_2 = 'PIPELINE_2'
PIPELINE_3 = 'PIPELINE_3'

for p in PRODUCTS:
    input_files = {}
    intent_files = {}
    for t in [SPEC, TROB, FAQ, OPERATION]:
        input_files[t] = os.path.join(data_set, p, p + '_' + t + '.xlsx')

    INPUT_FILES[p] = input_files
