"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anindya06.das@lge.com
@modified-by: purnanaga.nalluri@lge.com
"""
import os
import pickle as pkl

from apps.ker_ko.knowledge_extraction.constants import params as cs

# For getting the image_folder_path, ip_address & port_number of the ker system
image_folder_path, ip_address, port_number = cs.get_image_db_path()
prefix_path_with_ip_and_port = "http://" + ip_address + ":" + port_number
image_folder_path = os.path.join(prefix_path_with_ip_and_port, image_folder_path)

# Constants for Paths and loading model
model_ckpt = "mpnet_model.pkl"
current_dir = os.path.dirname(os.path.realpath(__file__))
models_folder = os.path.abspath(os.path.join(current_dir, "..", "dataset", "models"))
doc_search_model_folder = os.path.join(models_folder, "doc_search_models")
SEN_MODEL_PATH = os.path.join(doc_search_model_folder,
                              "paraphrase-mpnet-base-v2", model_ckpt)
EMB_FILE_PATH = os.path.join(doc_search_model_folder, "Embeddings")

# for loading 'paraphrase-mpnet-base-v2'
file_name = open(SEN_MODEL_PATH, 'rb')
model = pkl.load(file_name)

# Constants used in utils
REL = ["사용하기", "청소하기", "사용하기 전 알아두기", "세탁 전",
       "세탁 후", "변경하기", "설정하기",
       "분리", "조립하기", "설정", "해제하기",
       "요약", "설명", "절차", "단계", "주의", "경고", "특징",
       "설치하기", "제거하기", "연결하기", "분리하기",
       "해결하기", "관리하기", ""]
HTML_DISCARD_REL = ["사용하기", "청소하기", "변경하기", "설정하기",
                    "분리", "조립하기", "설정", "해제하기",
                    "설명", "절차", "단계",
                    "설치하기", "제거하기", "연결하기", "분리하기",
                    "해결하기", "관리하기"]
KEPLER_SECTION=["사용하기-세탁기", "사용하기-건조기", "관리하기-건조기", "관리하기-세탁기"]

# QA Engine constants
stop_words = list(['누가', '언제', '어디서', '무엇을', '어떻게', '왜'])
MAX_CAN = 60
MAX_OPT = 3
top_percentile = 40
th_value = 20  # threshold
