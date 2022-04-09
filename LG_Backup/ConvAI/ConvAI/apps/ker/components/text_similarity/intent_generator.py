# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
 * Copyright(c) 2020 by LG Electronics.
 * Confidential and Proprietary All Rights Reserved.
 *-------------------------------------------------*/
@author: vishwaas@lge.com
"""

# from components.text_similarity import constants
import pandas as pd
import json
import re

import constants


def generate_trob_keys(product = constants.WASHING_MACHINE):
    """
    Gets TroubleShooting Keys Json
    :param product: str
    :return: None
    """

    json_data = {}
    troubleshoot_keys_dict = {}
    json_data['TROUBLESHOOT_KEYS'] = troubleshoot_keys_dict

    troubleshoot_keys_keys = ['HAS_ERROR', 'HAS_NOISE', 'HAS_PROBLEM']
    all_keys = ['ERROR_KEYS','NOISE_KEYS', 'PROBLEM_KEYS']

    file_name = constants.INPUT_FILES[product][constants.TROB]
    data = pd.read_excel(file_name, sheet_name=constants.L1_L2_L3)

    for name1, group1 in data.groupby(['Type']):
        values1 = [s.replace('\n', ' ') for s in list(set(group1['Grouped Key'].values))]
        troubleshoot_keys_dict[troubleshoot_keys_keys[name1]] = values1

        key_type = {}
        for name2, group2 in data.groupby(['Grouped Key']):
            key_type[name2] = [s.replace('\n', ' ') for s in list(set(group2['Info_Extraction_Labels'].values))]

        json_data[all_keys[name1]] = key_type

    with open(constants.TROB_KEYS[product], 'w') as outfile:
        json.dump(json_data, outfile)

def generate_intent(product=constants.WASHING_MACHINE, question_type=constants.SPEC):
    """
    Creates Intent Json
    :param product: str
    :return: None
    """

    file_name = constants.INPUT_FILES[product][question_type]
    output_file = constants.INTENT_FILES[product][question_type]
    if question_type==constants.SPEC:
        __handle_spec(file_name, output_file)
    elif question_type==constants.TROB:
        __handle_trob(file_name, output_file)
    elif question_type==constants.FAQ:
        __handle_faq(file_name, output_file)
    elif question_type==constants.OPERATION:
        __handle_operation(file_name, output_file)

def __handle_faq(file_name, output_file):
    """
    Creates Intent Json for FAQ
    :param product: str
    :return: None
    """
    data_pass = __get_data(file_name, constants.L1_L2_L3)
    intent = {}
    expected_col = 'Text_Similarity_Labels'

    for json_key, group in data_pass.groupby([expected_col]):
        group = group.reset_index()
        json_val = {}
        keys = group.loc[0, 'Key']
        json_val['Intent'] = 'HAS_QUESTION'
        json_val['prob_key'] = 'Question'
        json_val['prob_value'] = keys
        intent[json_key] = json_val

    with open(output_file, 'w') as outfile:
        json.dump(intent, outfile)

def __get_data(file_name, level = constants.L1_L2_L3):
    """
    gets the data
    :param file_name: str
    """
    data = pd.read_excel(file_name, sheet_name= level, engine='openpyxl')
    # data_pass = data.loc[data['Text_Similarity_Accuracy']==1, :]
    data = data.astype(str)
    # data_pass = data.reset_index()

    return data

def __handle_spec(file_name, output_file):
    """
    Creates Intent Json for Specification
    :param product: str
    :return: None
    """
    data_pass = __get_data(file_name)

    response_key = 'Key'
    data_pass[response_key] = data_pass[response_key].apply(lambda x: __preprocess_key(x))
    intent = {}
    for json_key, group in data_pass.groupby([response_key]):
        group = group.reset_index()
        json_val = {}
        json_val['prob_key'] = ""
        json_val['prob_value'] = ""
        json_val['response_key'] = group.loc[0, response_key]
        intent[json_key] = json_val
    with open(output_file, 'w') as outfile:
        json.dump(intent, outfile)

def __handle_operation(file_name, output_file):
    """
    Creates Intent Json for operation
    :param file_name: input file
    :param output_file: output json file
    :return: None
    """
    intent_key = {'control panel feature': 'HAS_CONTROL_PANEL_FEATURE', 'checklist': 'HAS_CHECKLIST',
                  'feature': 'HAS_FEATURE', 'instruction': 'HAS_INSTRUCTION', 'component': 'HAS_COMPONENT'}

    data_pass = __get_data(file_name)
    intent = {}
    key_col = 'Grouped Key'
    expected_col = 'Key'
    type2 = 'Category'
    type3 = 'Type'

    data_pass[expected_col] = data_pass[expected_col].apply(lambda x: __preprocess_key(x))


    for json_key, group in data_pass.groupby([expected_col]):
        json_val = {}
        group = group.reset_index()
        json_val['prob_value'] = group.loc[0, key_col].replace('\n', ' ')
        type_int = group.loc[0, type2].lower()
        json_val['Intent'] = intent_key[type_int]
        json_val['prob_key'] = group.loc[0, type3].lower()
        intent[json_key] = json_val

    with open(output_file, 'w') as outfile:
        json.dump(intent, outfile)

def __handle_trob(file_name, output_file):
    """
    Creates Intent Json for TroubleShooting
    :param product: str
    :return: None
    """
    data_pass = __get_data(file_name)
    intent = {}
    key_col = 'Grouped Key'
    expected_col = 'Key'
    intent_col = 'Intent'
    type2 = 'Type'


    intent_key = {'error messages':('HAS_ERROR_CODE', 'error_code'),
                  'noises':('HAS_NOISE_PROBLEM', 'noise'),
                  'cooling_problem': ('HAS_COOLING_PROBLEM', 'problem'),
                  'ice_problem': ('HAS_ICE_PROBLEM', 'problem'),
                  'wi-fi': ('HAS_WIFI_PROBLEM', 'problem'),
                  'problem': ('HAS_PROBLEM', 'problem')}

    data_pass[expected_col] = data_pass[expected_col].apply(lambda x: __preprocess_key(x))

    for json_key, group in data_pass.groupby([expected_col]):
        json_val = {}
        group = group.reset_index()
        json_val['prob_value'] = group.loc[0, key_col].replace('\n', ' ')
        type_int = group.loc[0, type2].lower()
        json_val['Intent'] = intent_key[type_int][0]
        json_val['prob_key'] = intent_key[type_int][1]
        json_val['query_intent'] = group.loc[0, intent_col]
        intent[json_key] = json_val

    with open(output_file, 'w') as outfile:
        json.dump(intent, outfile)

def __preprocess_key(key):
    keys_pp = key.lower()
    keys_pp = re.sub('\\.$','', keys_pp)
    return keys_pp

# for p in [constants.PRODUCTS[1]]:
#     for t in [constants.SPEC, constants.TROB, constants.FAQ]:
#         generate_intent(p,t)
    # generate_trob_keys(product=p)

generate_intent(constants.WASHING_MACHINE, constants.OPERATION)
# generate_intent(question_type = Constants.FAQ)
# generate_intent(question_type = Constants.FAQ)
# generate_intent(question_type = Constants.FAQ)
# generate_trob_keys()