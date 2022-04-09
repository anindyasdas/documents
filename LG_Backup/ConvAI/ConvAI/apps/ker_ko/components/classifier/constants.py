# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: purnanaga.nalluri@lge.com
"""
import os

class PathConstants:
    # general paths for input/ output / model files
    current_folder = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'dataset')) + '/'
    DATA_PATH = current_folder + 'dataset/'
    MODEL = current_folder + 'models/classifier/korean_bert/'
    OUTPUT_DIR = MODEL + 'output/'
    TYPE_DIR = MODEL + "output/type_output/"
    TOPIC_DIR = MODEL + "output/topic_output/"
    SECTION_DIR = MODEL + "output/section_output/"
    SECTION_WM_DIR = MODEL + "output/section_wm_output/"
    SECTION_KEPLER_DIR = MODEL + "output/section_kepler_output/"
    SECTION_DRYER_DIR = MODEL + "output/section_dryer_output/"
    SECTION_STYLER_DIR = MODEL + "output/section_styler_output/"
    TYPE_EXPT_DIR = MODEL + "output/type_output/tmp"
    TOPIC_EXPT_DIR = MODEL + 'output/topic_output/tmp'
    SECTION_EXPT_DIR = MODEL + "output/section_output/tmp"
    SECTION_WM_EXPT_DIR = MODEL + "output/section_wm_output/tmp"
    SECTION_KEPLER_EXPT_DIR = MODEL + "output/section_kepler_output/tmp"
    SECTION_DRYER_EXPT_DIR = MODEL + "output/section_dryer_output/tmp"
    SECTION_STYLER_EXPT_DIR = MODEL + "output/section_styler_output/tmp"

    # dataset paths
    TRAIN_DATA = DATA_PATH + 'train.xlsx'
    TEST_DATA = DATA_PATH + 'test.xlsx'
    RESULTS_FILE = DATA_PATH + 'results.xlsx'


class BertConstants:
    # Bert configs related constants
    BERT_URL = 'https://tfhub.dev/google/bert_uncased_L-12_H-768_A-12/1'
    VOCAB = PathConstants.MODEL + 'config/vocab.txt'
    CHECKPOINT = PathConstants.MODEL + 'checkpoint/model.ckpt'
    JSON = PathConstants.MODEL + 'config/bert_config.json'


class ClassifierConstants:
    # mecab url from configuration.ini
    CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '..', '..', 'knowledge_extraction','config', 'configuration.ini'))
    IS_TRAIN = False
    TASK_TYPE = 'type'
    TASK_TOPIC = 'topic'
    TASK_SECTION = 'section'
    TASK_WM_SECTION = 'wm_section'
    TASK_KEPLER_SECTION = 'kepler_section'
    TASK_DRYER_SECTION = 'dryer_section'
    TASK_STYLER_SECTION = 'styler_section'
    STR_BATCH_SIZE = 'batch_size'
    POSITION = 'position'
    SENTENCES = 'sentences'
    PRD_DRYER = 'dryer'
    PRD_WM = 'washing machine'
    PRD_REF = 'refrigerator'
    PRD_STYLER = 'styler'
    PRD_KEPLER = 'kepler'

class KerKoStringConstants:
    # Constant strings
    TOPIC = "section"
    INTENT = "intent"
    TYPE = "sub_section"
    FOLLOW_UP = "follow_up"
    CLASS = "question_type"
    CATEGORY = "category"
    USER_QUESTION = 'User Question'
    SUB_CATEGORY = 'Sub category'
    LABEL = 'label'
    PRODUCT = 'Product'
    # features Dictionary keys
    INPUT_IDS = 'input_ids'
    INPUT_MASK = 'input_mask'
    SEGMENT_IDS = 'segment_ids'
    LABEL_IDS = 'label_ids'
    IS_REAL_EXAMPLE ='is_real_example'
    DIAGNOSIS = "진단"
    BEEP_WORDS = ["삐삐", "빵빵", "beep", "신호음", "경고음"]
    THINQ_WORDS = ["LG ThinQ", "ThinQ", "LG Thing Q"]
    DIAG_BEEP = "diag_beep"
    DIAG_THINQ = "diag_thinq"
    CONTROL_PANEL_WORDS = ["코스 선택 버튼","기능조작부","기능 조작부"]
    DRYING_COURSE_WORDS = ["패딩리프레쉬"]
    OPTIONAL_FEATURES_WORDS = ["스팀살균", "스팀 살균"]

class KerKoMappingDictionary:
    TOPIC_LABELS = ["Troubleshooting","Operation"]
    TYPE_LABELS = ["error", "noise", "cooling problem", "wifi problem", "problem","ice problem"]
    SECTION_LABELS = ['세제 또는 섬유 유연제 사용하기', '세탁 코스 및 옵션 사용하기', '알아두면 좋은 정보', '편리한 기능 사용하기', \
                      "기능조작부 사용하기","세탁 코스 사용하기","옵션 기능 사용하기", "건조 코스 사용하기","세탁물 분류하기", \
                      "건조물 분류하기"]
    TOPIC_DIC = {"troubleshooting":0,"operation":1}
    TYPE_DIC = {"error messages" : 0, "noises" : 1, "cooling problem" : 2, "wifi" : 3, "problem" : 4, "ice" : 5}
    SECTION_DIC = {'세제 또는 섬유 유연제 사용하기' : 0, '세탁 코스 및 옵션 사용하기' : 1, '알아두면 좋은 정보' : 2, '편리한 기능 사용하기' : 3, \
                   "기능조작부 사용하기" : 4, "세탁 코스 사용하기" : 5, "옵션 기능 사용하기" : 6, "건조 코스 사용하기" : 7, \
                   "세탁물 분류하기" : 8, "건조물 분류하기" : 9}
    KEPLER_SECTION_LABELS = ['세제 또는 섬유 유연제 사용하기',  '알아두면 좋은 정보',  \
                      "기능조작부 사용하기","세탁 코스 사용하기","옵션 기능 사용하기", "건조 코스 사용하기","세탁물 분류하기", \
                      "건조물 분류하기"]
    KEPLER_SECTION_DIC = {'세제 또는 섬유 유연제 사용하기' : 0, '알아두면 좋은 정보' : 1,  \
                   "기능조작부 사용하기" : 2, "세탁 코스 사용하기" : 3, "옵션 기능 사용하기" : 4, "건조 코스 사용하기" : 5, \
                   "세탁물 분류하기" : 6, "건조물 분류하기" : 7}
    WM_SECTION_LABELS = ['세제 또는 섬유 유연제 사용하기', '세탁 코스 및 옵션 사용하기', '알아두면 좋은 정보', '편리한 기능 사용하기']
    WM_SECTION_DIC = {'세제 또는 섬유 유연제 사용하기' : 0, '세탁 코스 및 옵션 사용하기' : 1, '알아두면 좋은 정보' : 2, '편리한 기능 사용하기' : 3}
    STYLER_SECTION_LABELS = ['시작 전 준비하기', '알아두면 좋은 정보', '옵션 기능 사용하기', '의류 넣기','코스 사용하기']
    STYLER_SECTION_DIC = {'시작 전 준비하기' : 0, '알아두면 좋은 정보' : 1, '옵션 기능 사용하기' : 2, '의류 넣기' : 3, \
                   '코스 사용하기' : 4 }
    DRYER_SECTION_LABELS = ['건조 코스 및 옵션 사용하기','알아두면 좋은 정보','편리한 기능 사용하기']
    DRYER_SECTION_DIC = {'건조 코스 및 옵션 사용하기' : 0, '알아두면 좋은 정보' : 1, '편리한 기능 사용하기' : 2 }
    LABELS_TO_TASK_NAME_MAP = {"topic":TOPIC_LABELS, "type":TYPE_LABELS, "section":SECTION_LABELS , "wm_section": WM_SECTION_LABELS, \
                               "kepler_section":KEPLER_SECTION_LABELS, "dryer_section": DRYER_SECTION_LABELS, "styler_section": STYLER_SECTION_LABELS}

class ResponseConstants:
    response_code = 'response_code'
    response_data = 'response_data'
    STATUS_OK = 200
    STATUS_UNSUPPORTED_QUERY = 201

class KerKoOperationConstants:
    # operation section constants
    # operation section sub-sections
    CONTROL_PANEL = "기능조작부 사용하기"
    FEATURE = "특색"

    OPERATION_SUB_CATEGORY_MAP = {CONTROL_PANEL: ["세탁 코스 및 옵션 사용하기"],
                                  FEATURE: [None]
                                  }

    # operation section intents
    DESCRIPTION = "desc"
    EXTRA_WARNING = "warning"
    EXTRA_CAUTION = "caution"
    EXTRA_NOTE = "note"

    # Mapping dictionaries for operation section
    OPERATION_INTENT_DICT = {
        DESCRIPTION: [None],
        EXTRA_WARNING: ['경고'],
        EXTRA_CAUTION: ['주의'],
        EXTRA_NOTE: ['알아두기']
    }