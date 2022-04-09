"""
/*-------------------------------------------------
* Copyright(c) 2020-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""

import os

CURRENT_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'dataset')) + '/'

TASK = 'MRPC'
SIMILARITY_DATA_DIR = CURRENT_FOLDER + 'dataset/info_data/'
BERT_MODEL = 'uncased_L-12_H-768_A-12'
BERT_MODEL_HUB = 'https://tfhub.dev/google/bert_' + BERT_MODEL + '/1'

TRAIN_CSV = SIMILARITY_DATA_DIR + 'QQP/train.tsv'
TEST_CSV = SIMILARITY_DATA_DIR + 'QQP/test.tsv'
DEV_CSV = SIMILARITY_DATA_DIR + 'QQP/dev.tsv'

CACHE_PATH = SIMILARITY_DATA_DIR + 'siam_emb.hdf5'
QUESTION_DATA_LIST = SIMILARITY_DATA_DIR + 'question_list.csv'
OUTPUT_DIR = CURRENT_FOLDER + 'models/similarity_models/'
BERT_MODEL_DIR = OUTPUT_DIR + '/bert_model'
TASK_DATA_DIR = SIMILARITY_DATA_DIR + 'glue_data/' + TASK
FILE_PRED_PATH = OUTPUT_DIR + "/manual_eval_results.csv"
MODEL_PATH = OUTPUT_DIR + 'siamese_model/siamese_model.max.ckpt'
ML_MODELS_PATH = OUTPUT_DIR + 'ml_models/'
TRAIN_PP = SIMILARITY_DATA_DIR + 'QQP/train_pp.tsv'
TEST_PP = SIMILARITY_DATA_DIR + 'QQP/test_pp.tsv'

FILE_PATH = SIMILARITY_DATA_DIR + 'manual_qa_pairs.tsv'

SIAM_BERT_MODEL_PATH = OUTPUT_DIR + 'training_nli_custom_siam_model-2020-10-14_11-49-47'
SIAM_BERT_MULTILINGUAL_MODEL_PATH = OUTPUT_DIR + 'stsb-xlm-r-multilingual'
SIAM_BERT_TRAIN_PATH = SIMILARITY_DATA_DIR+'AllNLI/'
SIAM_BERT_BENCHMARK_PATH = SIMILARITY_DATA_DIR+'stsbenchmark/'

SIAM_BERT_DATA_STS = SIMILARITY_DATA_DIR + 'stsbenchmark/'
SIAM_BERT_DATA_MRPC = SIMILARITY_DATA_DIR + 'glue_data/MRPC/'
CUSTOM_TROB_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_trob_train.xlsx'
CUSTOM_TROB_SIM_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_trob_sim_train.xlsx'
CUSTOM_SPEC_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_spec_train.xlsx'
CUSTOM_SPEC_TEST_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_spec_test.xlsx'
CUSTOM_SPEC_SIM_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_spec_sim_train.xlsx'

trouble_shoot_data = SIMILARITY_DATA_DIR + '/test.tsv'
error_codes_file = SIMILARITY_DATA_DIR + '/error_codes.txt'
technical_words_file = SIMILARITY_DATA_DIR + '/technical_words.txt'

WASHING_MACHINE = 'washing machine'
REFRIGERATOR = 'refrigerator'
AC = 'air conditioner'
VACUUM_CLEANER = 'vacuum cleaner'
MICROWAVE_OVEN = 'microwave oven'
DISH_WASHER = 'dish washer'
DRYER = 'dryer'
STYLER = 'styler'

class WasherSubProductTypes(object):
    """
        key constants used for washing machine product sub types
    """
    KEPLER = 'kepler'
    FRONT_LOADER = 'front loader'
    TOP_LOADER = 'top loader'
    MINI_WASHER = 'mini washer'

class RefrigeratorSubProductTypes(object):
    """
        key constants used for washing machine product sub types
    """
    LARGE = 'large'
    MEDIUM = 'medium'
    KIMCHI = 'kimchi'

OP_SUPPORTED_PRODUCTS = [WASHING_MACHINE, DRYER, STYLER]

# defining sub product types
WASHER_TYPES = [WasherSubProductTypes.KEPLER,WasherSubProductTypes.TOP_LOADER,
                WasherSubProductTypes.FRONT_LOADER,WasherSubProductTypes.MINI_WASHER]
REFRIGERATOR_TYPES = [RefrigeratorSubProductTypes.LARGE, RefrigeratorSubProductTypes.MEDIUM,
                      RefrigeratorSubProductTypes.KIMCHI]

PRODUCTS = [WASHING_MACHINE, DRYER, STYLER, REFRIGERATOR]

reverse_dict = {"error": 0, "noises": 1, "cooling_problem": 2, "ice_problem": 3,
                "wi-fi": 4, "problem": 5}

EXPECTED_QUESTION = 'Text_Similarity_Labels'
SPEC = 'SPEC'
TROB = 'TROB'
FAQ = 'FAQ'
OPERATION = 'OPERATION'

L1_L2_L3 = 'L1_L2_L3'

PIPELINE_1 = 'PIPELINE_1'
PIPELINE_2 = 'PIPELINE_2'
PIPELINE_3 = 'PIPELINE_3'

CANONICAL_QUESTION_PRUN = 18

INPUT_FILES = {}
INTENT_FILES = {}
TROB_KEYS = {}

for p in [STYLER,DRYER]:
    input_files = {}
    intent_files = {}
    for t in [TROB,OPERATION]:
        input_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, p + '_' + t + '.xlsx')
        intent_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, p + '_' + t + '_INTENT.json')

    INPUT_FILES[p] = input_files
    INTENT_FILES[p] = intent_files


p = WASHING_MACHINE
subtype_files = {}
subtype_intentfiles = {}
for subtype in WASHER_TYPES:
    if subtype in [WasherSubProductTypes.KEPLER, WasherSubProductTypes.FRONT_LOADER]:
        section_list = [TROB, OPERATION]
    else:
        section_list = [TROB]
    input_files = {}
    intent_files = {}
    for t in section_list:
        input_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, subtype, p + '_' + subtype + '_' + t + '.xlsx')
        intent_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, subtype, p + '_' + subtype + '_' + t + '_INTENT.json')
    subtype_files[subtype] = input_files
    subtype_intentfiles[subtype] = intent_files
INPUT_FILES[p] = subtype_files
INTENT_FILES[p] = subtype_intentfiles

p = REFRIGERATOR
subtype_files = {}
subtype_intentfiles = {}
for subtype in REFRIGERATOR_TYPES:
    input_files = {}
    intent_files = {}
    for t in section_list:
        input_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, subtype, p + '_' + subtype + '_' + t + '.xlsx')
        intent_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, subtype, p + '_' + subtype + '_' + t + '_INTENT.json')
    subtype_files[subtype] = input_files
    subtype_intentfiles[subtype] = intent_files
INPUT_FILES[p] = subtype_files
INTENT_FILES[p] = subtype_intentfiles


CONFIG_FILE = CURRENT_FOLDER = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + '/' + 'experiments.conf'
