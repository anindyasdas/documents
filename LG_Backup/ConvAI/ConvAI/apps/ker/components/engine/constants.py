"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""
import os
import logging

# stored model file path
current_folder = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'dataset')) + '/'
LG_LOGGING_MODULE_OUTPUT_LVL = logging.INFO + 1
LG_LOGGING_MODULE_OUTPUT_NAME = "OUTPUTS"
LG_LOGGING_MODULE_OUTPUT_KEY = "[special_log]"

# product manual sections
SPEC = 'SPEC'
TROB = 'TROB'
FAQ = 'FAQ'
OPERATION = 'OPERATION'

PIPELINE_1 = 'PIPELINE_1'
PIPELINE_2 = 'PIPELINE_2'
PIPELINE_3 = 'PIPELINE_3'
L1_L2_L3 = 'L1_L2_L3'

data_set = current_folder + 'dataset/info_data'
TROB_TEST_DATA = os.path.join(data_set, 'W_R_A_M_V_trob_test.xlsx')
SPEC_TEST_DATA = os.path.join(data_set, 'W_R_A_M_V_spec_test.xlsx')

PIPELINE_1_LM_EMB = current_folder + 'dataset/info_data/PIPELINE_1_LM_EMB.hdf5'
PIPELINE_2_LM_EMB = current_folder + 'dataset/info_data/PIPELINE_2_LM_EMB.hdf5'
PIPELINE_3_LM_EMB = current_folder + 'dataset/info_data/PIPELINE_3_LM_EMB.hdf5'

# products name
WASHING_MACHINE = 'washing machine'
REFRIGERATOR = 'refrigerator'
AC = 'air conditioner'
VACUUM_CLEANER = 'vacuum cleaner'
MICROWAVE_OVEN = 'microwave oven'
DISH_WASHER = 'dish washer'

PRODUCTS = [WASHING_MACHINE, REFRIGERATOR, AC, VACUUM_CLEANER, MICROWAVE_OVEN, DISH_WASHER]
INPUT_FILES = {}
for p in PRODUCTS:
    input_files = {}
    intent_files = {}
    for t in [SPEC, TROB, FAQ, OPERATION]:
        input_files[t] = os.path.join(data_set, p, p + '_' + t + '.xlsx')

    INPUT_FILES[p] = input_files

INFO_EXTRACTION = 'info_extr'
NP = 'NP'
VB = 'VB'
TEMP = 'temp'
PURPOSE = 'purpose'
CAUSE = 'cause'
TYPE = 'Type'
EXPECTED_QUESTION = 'Key'
INFO_LABELS = 'Info_Extraction_Labels'
logs = current_folder + 'dataset/info_data/logs.txt'
reverse_dict = {"error": 0, "noise": 1, "problem": 2, "ice problem": 3,
                "cooling problem": 4}

response_code = 'response_code'
response_data = 'response_data'
STATUS_OK = 200
STATUS_UNSUPPORTED_QUERY = 201
SIMILARITY_KEY = "similarity_key"