# -------------------------------------------------
# Copyright(c) 2021-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------

import os
import re

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

def get_list(data):
    """
    This function takes any data type as input and processes it recursively to extract sentences
    contained in dictionary values or list
    Args:
        data: Input data (list, dict, string)
    Returns: A list of strings
    Eg: Input : [{1:["옮길 때 알아두기"], 2:"운송용 고정볼트 제거하기"},
                 {1:["미끄럼 방지 시트 설치하기"], 3:"미끄럼 방지 시트"}, [["알아두기", "운송용"]], "옮길 때"]
    Output: ['옮길 때 알아두기', '운송용 고정볼트 제거하기', '미끄럼 방지 시트 설치하기', '미끄럼 방지 시트','알아두기', '운송용', '옮길 때']
    """
    data_list=[]
    if type(data)==dict:
        for key, value in data.items():
            data_list.extend(get_list(value))
    elif type(data) ==list and len(data)>0 and (type(data[0])==dict or type(data[0])==list):
        for item in data:
            data_list.extend(get_list(item))
    elif type(data)== str:
        data_list.append(data)
    else:
        data_list.extend(data)
    return  data_list

def split_value_key_chain(val):
    st = val[2:-2].replace('"]["', "#$#$$")
    st=st.split("#$#$$")
    return st

def get_section_headings(st):
    """
    This function extract section heading from a input value-key-chain and processes it
    for SEE_MAUNAL CONTENT


    """
    st=split_value_key_chain(st)
    len_st = len(st)
    section = st[1]
    title = ''
    val_key = ''

    if len_st >= 4:
        for i in range(3, len_st):
            if st[i] not in HTML_DISCARD_REL:
                title = st[i]
                val_key = "[\"" + '"]["'.join(st[:i + 1]) + "\"]"
                break

    return section, title, val_key


def process_img_html(img_list, html):
    for d in img_list:
        d = os.path.join(image_folder_path, d)
        html += '<img style="display: block;margin: 0 auto;" src={}><br>'.format(d)
    return html

def json_to_html_process_key_value(key,value,prev_key, html):
    """
    This function is internally being called by the function json_to_html to process
    each key and value of a dictionary object

    """
    if key == "figure":
        img_list = value["graphic"]
        html = process_img_html(img_list, html)
    elif value:
        curr_key = key
        if key in prev_key or key in HTML_DISCARD_REL or re.match('단계 [0-9]*$', key):
            key = ''
        else:
            prev_key = key
        if key in ['note', '주의', '경고']:
            html += '<fieldset><legend>' + key + '</legend>'
            html = json_to_html(value, html, prev_key) + '</fieldset>'
        elif curr_key == '단계':
            html += '<ol>'
            html = json_to_html(value, html, prev_key) + '</ol>'
        else:
            html += '<h2>' + key + '</h2>'
            html = json_to_html(value, html, prev_key)
    else:
        html += '<p>' + '<ul>' + key + '</ul>' + '</p>'
    
    return prev_key, html

    


def json_to_html(d, html, prev_key):
    """
    This function takes html, dictionary and parent key as inputs, converts the dictionary into html
    and appends extracted html from dictionary to input html, to generate fully formatted html

    Parameters
    ----------
    d : TYPE dictionary
        DESCRIPTION. Input dictionary
    html : TYPE string
        DESCRIPTION. containing html
    prev_key : TYPE String
        DESCRIPTION. this is used for internal parent key tracking and helps in removing the duplicate headings while creating html
        

    Returns
    -------
    html : TYPE string
        

    """
    if isinstance(d, list) and d:
        html += '<p>' + '<ul>'
        for item in d:
            html = json_to_html(item, html, prev_key)
        html += '</ul>' + '</p>'
    elif isinstance(d, dict) and d:
        for k, v in d.items():
            prev_key, html=json_to_html_process_key_value(k,v,prev_key, html)
    else:
        html += '<li>' + str(d) + '</li>'

    return html


def tokenize(sen):
    return sen.split(' ')


def handle_description_summary(val, key):
    """
    This function removes 설명  요약 from key, value

    """
    if val[-6:] == '["설명"]':
        val = val[:-6]
        key = re.sub('설명', '', key)
    if val[-6:] == '["요약"]':
        val = val[:-6]
        key = re.sub('요약', '', key)
    return val, key


def get_section_section_title(st):
    """
    Extract the section name and section_title

    """
    st=split_value_key_chain(st)
    section = st[1]
    section_title = st[-1]
    if section_title in REL:
        section_title = st[-2] + " " + section_title
    return section, section_title


def create_standardize_json(feature_val, section, standardized, response_code, is_retrieval, section_hierarchy=None):
    """
    This function creates standardize json from inputs, is_retrieval = True for answer retrieval
    for option/key fetching is_retrieval=False

    """
    if is_retrieval:
        st_json={"answer":{section:{"features":feature_val}}, "response_code":response_code, "standardized":standardized, "section_hierarchy":section_hierarchy}
    else:
        st_json={"answer":feature_val, "response_code":response_code, "standardized":standardized, "section_hierarchy":section_hierarchy}
    return st_json

    
def process_str_(st, key):
    """
    This function accepts the value-key-chain st and key , and processes the key
    to remove duplicate information or add important information or Product information (KEPLER)[
        As Kepler products has sections eg. Operation dedicated to both Dryer and Washing Machine]
    to make keys much more distinctive and informative

    """
    st=split_value_key_chain(st)
    if st[-1].strip() not in key:
        key= key + " " +  st[-1].strip()
    if st[1].strip() in KEPLER_SECTION:
        st1=st[1].strip().split('-')[0]
        prod_component= " ( "+ st[1].strip().split('-')[1] +" )"
    # For Safety Section st[2] is either caution or warning which is appended to form distinctive keys
    elif st[1].strip() in ["안전을 위해 주의하기"] and len(st)> 3:
        st1= st[1]
        prod_component= " ( "+ st[2].strip() +" )"
    else:
        st1=st[1]
        prod_component=''
    if key.strip() in REL and len(st)>=3: 
        key= " ".join([st1.strip() , '>>', st[2].strip()])
    else:
        key= " ".join([st1.strip() , '>>', key.strip()])
    key+=prod_component
    return key
