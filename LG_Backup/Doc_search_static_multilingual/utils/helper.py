# -*- coding: utf-8 -*-
""""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anindya06.das@lge.com
##############################################################################
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))))
import re
import params as cs
from copy import deepcopy
import json

def process_string(text):
    text=re.sub('#SBOLD#', '', text)
    text=re.sub('#EBOLD#', '', text)
    text=re.sub('#SEMP#', '', text)
    text=re.sub('#EEMP#', '', text)
    text = re.sub('\s*/\s*', '/', text)
    text = re.sub(':', '', text)
    if text in cs.KEY_CORRECTION:
        text= cs.KEY_CORRECTION[text]
    return text

def merge(a, b, path=None):
    "merges dictionary b into dictionary a"
    #recursive
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key].extend(b[key])
                #Exception handling if keys are same, but values are different
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def translate_keywords(d):
    new_d=d  
    if type(d)==list:
        new_d=[]
        for item in d:
            new_d.append(translate_keywords(item)) 
    elif type(d)==dict:
        new_d={}
        for key, value in d.items():
            if key in cs.keywords_map:
                key= cs.keywords_map[key]
            new_d[key]=deepcopy(translate_keywords(value))    
    return new_d

def combine_nested_dict_key(d, s):
    for key, value in d.items(): 
        s= s+ " " + key 
        s= combine_nested_dict_key(value, s.strip()) 
    return s.strip()

def extract_text_keys(t_d):
    text_keys=[]
    for key, value in t_d.items():
        try:
            row_heading= combine_nested_dict_key(value, key)
        except:
            return [], False
        #if not value and key not in cs.SYMBOLS:
        text_keys.append(row_heading)
    return text_keys, True

def remove_special_tags(new_dict):
    """
    remove the special tags
    eg. **topic**TITLE**전원 플러그나 전원선을 다룰 때 tag to be converted to
    전원 플러그나 전원선을 다룰 때

    Parameters
    ----------
    new_dict : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.
    """
    new_d = {}
    if type(new_dict) == list:
        new_d=[]
        for item in new_dict:
            new_d.append(remove_special_tags(item))     
        return new_d
    if type(new_dict)==str:
        return process_string(new_dict)
    for key, val in new_dict.items():
        key_items = key.split("**")
        if len(key_items) > 0:
            key = key_items[-1]
            if key == "":
                key = key_items[-2]
        key = process_string(key)
        new_d[key] = remove_special_tags(val)
    return new_d

def remove_num_item_tags(item):
    """
    <num>, <item> tags are added during data modelling to make identical keys extracted from tables
    distinguishable, during processing such tags are removed

    Parameters
    ----------
    item : TYPE string
        
    Returns
    -------
    item : string

    """
    item=re.sub('<num(.*?)>', "", item) 
    item = re.sub(r'[^\w\s]', '', item)
    item=re.sub('<item(.*?)>', "", item).strip()
    return item

def check_exclude_list(item):
    """
    This function checks if item in excluded list 
    Parameters
    ----------
    item : TYPE
        DESCRIPTION.

    Returns
    -------
    in_excluded_list : TYPE
        DESCRIPTION.
    """
    in_excluded_list= False 
    if (item in cs.EXCLUDE_KEY_LIST or len(item)<=1) or \
    (len(item.split())<=3 and item.split()[0] in cs.EXCLUDE_KEY_LIST): 
        in_excluded_list= True 
    return in_excluded_list
    
def remove_duplicates(trips):
    new_trips=[]
    for item in trips:
        if item not in new_trips:
            new_trips.append(item)
    return new_trips

def save_file(ob, outfile, ftype='json', encoding=''):
    if ftype=='json' and encoding=='': 
        with open(outfile, 'w') as out: 
            json.dump(ob, out, indent=6)
    if ftype=='json' and encoding=='utf-8-sig': 
        with open(outfile, 'w', encoding='utf-8-sig') as out: 
            json.dump(ob, out)
    if ftype=='txt': 
        with open(outfile, 'w',  encoding='utf-8-sig') as out: 
            for item in ob: 
                out.write(str(item)+'\n')