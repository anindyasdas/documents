"""
/*-------------------------------------------------
* Copyright(c) 2020-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""

import pandas as pd
import math
import json
import os
from . import constants
from . import utils
import re

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

def generate_question_list_json(info_extr, text_sim, question_type=constants.SPEC, product=constants.WASHING_MACHINE,subtype="front loader",pipeline=constants.PIPELINE_1):
    """
    Generates canonical questions for the given product,section(type)
    :param info_extr: Info Extraction model
    :param text_sim: Text similarity model
    :param question_type: SPEC or TROB
    :param product: WASHING_MACHINE OR REFRIGERATOR
    :param pipeline: pipeline to be used text sim or info based
    :return: dictionary of str:str where keys are canonical question and value is a base question
    """
    input_file, output_file = __get_data_type(question_type, product, subtype)
    json_data = __get_json(output_file)
    if len(json_data) == 0:
        data = pd.read_excel(input_file, sheet_name=constants.L1_L2_L3, engine='openpyxl')
        data['Key'] = data['Key'].apply(pre_process_key)
        grouped = data.groupby(['Key'])

        for name, group in grouped:
            error_codes, non_error_codes = get_error_codes(info_extr, group)
            selected = get_base_question(info_extr, group, pipeline, question_type,
                                         product, text_sim,
                                         [error_codes, non_error_codes])

            key_question_extr = info_extr.extract_info_single(name, pipeline, question_type, product, text_sim)[0]

            cat = 'nan'
            if question_type == constants.TROB:
                cat = group.Type.values[0].lower()
            elif question_type == constants.OPERATION:
                cat = group['Grouped Key'].values[0].lower()
            json_data[name + '|' + str(cat)] = [str(key_question_extr)]
            logger.debug("name=%s",name)
            for q in selected:
                json_data[name + '|' + str(cat)].append(str(q))

        with open(output_file, 'w') as outfile:
            # ensure_ascii=False).encode('utf8')
            json.dump(json_data, outfile,ensure_ascii=False)
    return json_data


def get_error_codes(info_extr, group):
    """
    get the error codes for the mentioned group
    :param info_extr: Info Extraction model
    :param group: error codes group name
    :return: list of error codes , non error codes
    """
    error_codes = []
    non_error_codes = []
    for text in group.Questions.values:
        ei = info_extr.is_in_error_id(text)
        if ei is not None:
            error_codes.append(ei)
        else:
            non_error_codes.append(text)
    return error_codes, non_error_codes


def get_base_question(info_extr, group, pipeline, question_type, product, text_sim, codes):
    """
    search and returns base question for the given product,section(type),group and codes
    :param info_extr: Info Extraction model
    :param group: group section
    :param pipeline: pipeline to be used text sim or info based
    :param question_type: SPEC or TROB
    :param product: WASHING_MACHINE OR REFRIGERATOR
    :param text_sim: Text similarity model
    :param codes:list of error codes
    :return: dictionary of str:str where keys are canonical question and value is a base question
    """
    k = 1 / 3
    if len(codes[0]) == 0:
        question_list = list(
            set(info_extr.extract_info_bulk(group.Questions.values, pipeline, question_type, product, text_sim)))
        question_list = [q[0] for q in question_list]
        base_ques_len = math.ceil(len(question_list) * k)
        selected = utils.get_top_questions(question_list, base_ques_len, text_sim)
    else:
        selected = list(set(codes[0]))
        non_error_codes = list(
            set(info_extr.extract_info_bulk(codes[1], pipeline, question_type, product, text_sim)))
        non_error_codes = [q[0] for q in non_error_codes]
        base_ques_len = math.ceil(len(non_error_codes) * k)
        if len(non_error_codes) != 0:
            selected2 = utils.get_top_questions(non_error_codes, base_ques_len, text_sim)
            selected.extend(selected2)
    return selected


def pre_process_key(key):
    """
    Applies lower and last full stop removal to keys
    :param key: str - key
    :return: preprocessed key
    """
    new_key = key.lower()
    new_key = new_key.strip()
    new_key = re.sub(r'\s+', ' ', new_key)
    new_key = re.sub(r'\.$', '', new_key)
    return new_key


def __get_data_type(question_type, product, subproduct_type):
    """
    Gets input and output file path
    :param question_type: SPEC or TROB
    :param product: product type Eg:Washer/Refrigerator
    :return: file names of input and output to generate embeddings
    """
    if product == subproduct_type:
        output_file = os.path.join(constants.SIMILARITY_DATA_DIR, product,
                                   product + '_' + question_type + '_' + constants.L1_L2_L3 + '.json')
        input_file = constants.INPUT_FILES[product][question_type]
    else:
        output_file = os.path.join(constants.SIMILARITY_DATA_DIR, product,subproduct_type,
                                   product + '_' + subproduct_type+ '_' + question_type + '_' + constants.L1_L2_L3 + '.json')
        input_file = constants.INPUT_FILES[product][subproduct_type][question_type]
    print("inputfile=%s outputfile=%s"%(input_file,output_file))
    return input_file, output_file


def __get_json(input_file):
    """
    Gets the json from json file
    :param input_file: json file
    :return: json data
    """
    try:
        json_data = json.load(open(input_file, 'r', encoding='utf-8'))
        return json_data
    except:
        return {}
