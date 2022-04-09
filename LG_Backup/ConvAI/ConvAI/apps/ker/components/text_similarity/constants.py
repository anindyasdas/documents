"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas@lge.com
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

ml_model_file_names_1 = ['ExtraTreesClassifier_1.sav', 'RandomForestClassifier_1.sav', 'LogisticRegression_1.sav',
                         'GaussianNB_1.sav']
ml_model_file_names_1 = [ML_MODELS_PATH + s for s in ml_model_file_names_1]

ml_model_file_names_2 = ML_MODELS_PATH + 'RandomForestClassifierr_2.sav'

output_model_file_name_3 = ML_MODELS_PATH + 'XGBClassifier_3.sav'

FILE_PATH = SIMILARITY_DATA_DIR + 'manual_qa_pairs.tsv'

SIAM_BERT_FINETUNED = OUTPUT_DIR + 'siam_bert_finetuned'
SIAM_BERT_MODEL_PATH = OUTPUT_DIR + 'training_nli_custom_siam_model-2020-10-14_11-49-47'
SIAM_BERT_TRAIN_PATH = SIMILARITY_DATA_DIR + 'AllNLI/'
SIAM_BERT_BENCHMARK_PATH = SIMILARITY_DATA_DIR + 'stsbenchmark/'

SIAM_BERT_DATA_STS = SIMILARITY_DATA_DIR + 'stsbenchmark/'
SIAM_BERT_DATA_MRPC = SIMILARITY_DATA_DIR + 'glue_data/MRPC/'
CUSTOM_TROB_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_trob_train.xlsx'
CUSTOM_TROB_SIM_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_trob_sim_train.xlsx'
CUSTOM_SPEC_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_spec_train.xlsx'
CUSTOM_SPEC_TEST_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_spec_test.xlsx'
CUSTOM_SPEC_SIM_TRAIN_DATA = SIMILARITY_DATA_DIR + 'W_R_A_M_V_spec_sim_train.xlsx'

question_list_spec = SIMILARITY_DATA_DIR + 'question_list_spec.json'
question_list_trob = SIMILARITY_DATA_DIR + 'question_list_trob.json'
elmo_emb_size = 1024
elmo_layers = 3
lstm_dim = 200
batch_size = 150
epochs = 15
num_features = 53
context_dim = 300
pos_tags_n = 12
FEATURE_SIZE = 51

trouble_shoot_data = SIMILARITY_DATA_DIR + '/test.tsv'
error_codes_file = SIMILARITY_DATA_DIR + '/error_codes.txt'
technical_words_file = SIMILARITY_DATA_DIR + '/technical_words.txt'

WASHING_MACHINE = 'washing machine'
REFRIGERATOR = 'refrigerator'
AC = 'air conditioner'
VACUUM_CLEANER = 'vacuum cleaner'
MICROWAVE_OVEN = 'microwave oven'
DISH_WASHER = 'dish washer'

PRODUCTS = [WASHING_MACHINE, REFRIGERATOR, AC, VACUUM_CLEANER, MICROWAVE_OVEN, DISH_WASHER]

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
for p in PRODUCTS:
    input_files = {}
    intent_files = {}
    for t in [SPEC, TROB, FAQ, OPERATION]:
        input_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, p + '_' + t + '.xlsx')
        intent_files[t] = os.path.join(SIMILARITY_DATA_DIR, p, p + '_' + t + '_INTENT.json')

    INPUT_FILES[p] = input_files
    INTENT_FILES[p] = intent_files
    TROB_KEYS[p] = os.path.join(SIMILARITY_DATA_DIR, p, p + '_TROB_KEYS.json')

CONFIG_FILE = CURRENT_FOLDER = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + '/' + 'experiments.conf'
