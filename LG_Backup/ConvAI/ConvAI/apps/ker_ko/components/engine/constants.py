"""
/*-------------------------------------------------
* Copyright(c) 2020-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
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

trob_intent_json_path = os.path.join(current_folder, 'dataset', 'info_data', 'intent_jsons')

# products name
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
INPUT_FILES = {}
for p in [DRYER, STYLER]:
    input_files = {}
    for t in [TROB, OPERATION]:
        input_files[t] = os.path.join(data_set, p, p + '_' + t + '.xlsx')
    INPUT_FILES[p] = input_files

# operation section washing machine
# input_files = {}
p = WASHING_MACHINE
subtype_files = {}
for subtype in WASHER_TYPES:
    if subtype in [WasherSubProductTypes.KEPLER,WasherSubProductTypes.FRONT_LOADER]:
        section_list = [TROB,OPERATION]
    else:
        section_list = [TROB]
    input_files = {}
    for t in section_list:
        input_files[t] = os.path.join(data_set, p, subtype,p + '_' + subtype + '_' + t + '.xlsx')
    subtype_files[subtype] = input_files
INPUT_FILES[p] = subtype_files

# refrigerator products
# input_files = {}
p = REFRIGERATOR
subtype_files = {}
for subtype in REFRIGERATOR_TYPES:
    input_files = {}
    for t in [TROB]:
        input_files[t] = os.path.join(data_set, p, subtype, p + '_' + subtype + '_' + t + '.xlsx')
    subtype_files[subtype] = input_files
INPUT_FILES[p] = subtype_files

#print("in engine constants",json.dumps(INPUT_FILES))
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

fuzzy_logic = True
top_select_from_cosin = True
top_k_text_sim_threshold = 20

response_code = 'response_code'
response_data = 'response_data'
SIMILARITY_KEY = 'similarity_key'
STATUS_OK = 200
STATUS_UNSUPPORTED_QUERY = 415

error_syns = ["오류", "에러", "오차", "잘못", "과실", "실책", "그릇된", "틀림", "실"]
error_word = "error"

# similarity keys for pre defined manual problems
ts_keys = {"wifi problem": {"가전제품과 스마트폰을 wi-fi로 연결할 수 없어요": [WASHING_MACHINE, DRYER, REFRIGERATOR]},
                     "noise": {"작동 중 소리가 나요": [STYLER]}}
oper_keys = {"세탁 코스 및 옵션 사용하기": {"구김방지": [WASHING_MACHINE]}}