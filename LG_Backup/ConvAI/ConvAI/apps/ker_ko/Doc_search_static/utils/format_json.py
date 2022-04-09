# -*- coding: utf-8 -*-
""""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anindya06.das@lge.com
##############################################################################
"""

import json
import os
import sys
import logging as logger
from copy import deepcopy

sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))))
import config as cfg


class ManualProcess:
    def __init__(self, file_path):
        self.uid = 0
        self.file_path = file_path
        with open(self.file_path, 'r') as jsonfile:
            self.manual_dict = json.load(jsonfile)

    def get_dict(self):
        return self.manual_dict

    def process_manual(self):
        manual = self.get_dict()
        new_d = self.process_properties(deepcopy(manual))
        json_dict = self.traverse_dict(deepcopy(new_d))
        json_dict = self.process_itemizedlist(deepcopy(json_dict))
        json_dict = self.process_bold(deepcopy(json_dict))
        json_dict = self.process_final(deepcopy(json_dict))
        return json_dict

    def process_properties(self, man_json):
        """
        This function removes the property tags
        """
        if type(man_json) == dict:
            for k in list(man_json):
                if k[0] == "@" and k not in [cfg.FILEREF, cfg.COLNAME, cfg.NAMEST, cfg.NAMEEND, cfg.MOREROWS]:
                #if k[0] == "@" and k not in [cfg.FILEREF, cfg.COLNAME]:
                    del man_json[k]
                else:
                    man_json[k] = self.process_properties(man_json[k])
        elif type(man_json) == list:
            v_list = []
            for item in man_json:
                v_list.append(self.process_properties(item))
            man_json = v_list

        return man_json
    

    def process_para(self, json_dict):
        text = json_dict[cfg.TEXT]
        return text, {}

    def process_title(self, json_dict):
        """
        if key is preface value is passed
        pass the entire dict
        """

        key = [k for k in json_dict.keys() if cfg.TITLE in k][0]

        text = json_dict[key][cfg.TEXT]
        del json_dict[key]
        return text, json_dict

    def process_varlist(self, json_dict):
        new_d = {}
        for key, value in json_dict.items():
            if key.split('_')[0] == cfg.TERM:
                new_key = value[cfg.TEXT]
            else:
                new_d[key] = self.traverse_dict(value)

        return new_key, new_d

    def process_listitem(self, json_dict, new_dict):
        json_dict = self.traverse_dict(json_dict)
        for key_l, value_l in json_dict.items():
            new_dict[key_l] = value_l
        return new_dict

    def traverse_dict(self, json_dict):
        """
        This fucntion processes the json dict, with keys preface, chapter, section, topic,
        para
        Parameters
        ----------
        json_dict : dict
            DESCRIPTION.
        Returns
        -------
        dict
            DESCRIPTION.
        """
        if type(json_dict) == dict:
            n_d = {}
            for k, v in json_dict.items():
                n_d=self.process_dict_keys(k, v, n_d)
            return n_d
        else:
            return json_dict
        
    def process_dict_keys(self, k, v, n_d): 
        """This function receives key, valu and the dict, processes the key and value
        based on type of the key (preface, chapter, section, topic,para"""
        key_item = k.split('_')[0]  # key part without the id
        if key_item in cfg.PROCESS_TITLE_LIST:
            key, json_dict1 = self.process_title(v)
            key = '**'+ key_item + '**' +'TITLE' + '**' + key
            n_d[key] = self.traverse_dict(json_dict1)
        elif key_item in cfg.PROCESS_PARA_LIST and v: #not empty
            key, json_dict1 = self.process_para(v)
            n_d[key] = json_dict1
        elif key_item in cfg.PROCESS_LISTITEM_LIST and type(v) == dict:
            n_d = self.process_listitem(v, n_d)
        elif key_item in cfg.GRAPHIC and type(v) == dict:
            n_d[k] = deepcopy(v[cfg.FILEREF])
        elif key_item in cfg.PROCESS_VARLISTENTRY:
            key, json_dict1 = self.process_varlist(deepcopy(v))
            n_d[key] = self.traverse_dict(json_dict1)
        elif key_item not in cfg.PROCESS_COLSPEC_LIST:
            n_d[k] = self.traverse_dict(v)
        return n_d

    def populate_dict(self, j_dict, new_dict):
        if type(j_dict) == dict:
            for new_key, new_value in j_dict.items():
                new_dict[new_key] = new_value
        return new_dict

    
    def process_itemizedlist_index(self, idxs, keys, json_dict):
        txt_key=''
        for idx in idxs:
            if (idx - 1) >= 0 and (keys[idx-1] in json_dict) and not json_dict[keys[idx-1]]:  # if previous key exists and corresponding value
                new_dict = {}
                new_dict = self.populate_dict(json_dict[keys[idx - 1]], new_dict)
                new_dict = self.populate_dict(json_dict[keys[idx]], new_dict)
                json_dict[keys[idx - 1]] = new_dict
                del json_dict[keys[idx]]
                txt_key= keys[idx - 1]
            elif txt_key !='':
                new_dict = {}
                new_dict = self.populate_dict(json_dict[keys[idx]], new_dict)
                json_dict[txt_key].update(new_dict)
                del json_dict[keys[idx]]
        return json_dict

    def process_itemizedlist(self, json_dict):
        """
        This method handles itemized keys,within a dictionary if one key is itemized key , the previous key is a text, then the value
        corresponding to itemized key becomes the value with the text as key
        """
        n_d = {}
        if type(json_dict) == dict:
            keys = list(json_dict.keys())
            idxs = [indx for indx, key in enumerate(keys) if key.split('_')[0] == "itemizedlist"]
            if idxs :  # if keys with "itemizedlist found"
                json_dict = self.process_itemizedlist_index(idxs, keys, json_dict)

            for k, v in json_dict.items():
                if k.split('_')[0] in cfg.PROCESS_ITEMIZEDLIST_LIST and type(v) == dict:
                    v = self.process_itemizedlist(v)
                    n_d = self.populate_dict(v, n_d)
                else:
                    n_d[k] = self.process_itemizedlist(v)
            return n_d
        else:
            return json_dict

    def check_bold(self, string):
        if (string[:7] == "#SBOLD#" and string[-7:] == "#EBOLD#") or (
                string[:6] == "#SEMP#" and string[-6:] == "#EEMP#"):
            return True
        else:
            return False

    def process_bold_heading(self, idxs, keys, json_dict):
        for idx_idx in range(len(idxs)):
            new_dict = {}

            heading_idx = idxs[idx_idx]
            for txt_idx in range(heading_idx + 1, len(keys)):
                for key, value in json_dict[keys[heading_idx]].items():
                    new_dict[key] = value
                if self.check_bold(keys[txt_idx]):
                    break
                else:
                    new_dict[keys[txt_idx]] = deepcopy(json_dict[keys[txt_idx]])
                    json_dict[keys[heading_idx]] = new_dict
                    del json_dict[keys[txt_idx]]
        return json_dict

    def process_bold(self, json_dict):
        n_d = {}
        if type(json_dict) == dict:
            keys = list(json_dict.keys())
            idxs = [indx for indx, key in enumerate(keys) if self.check_bold(key)]
            json_dict = self.process_bold_heading(idxs, keys, json_dict)

            for k, v in json_dict.items():
                n_d[k] = self.process_bold(v)
            return n_d
        else:
            return json_dict

    def process_final(self, json_dict):
        uid = 0
        n_d = {}
        if type(json_dict) == dict:
            for key, value in json_dict.items():
                key_segmented = key.split('_id_')
                if key_segmented[0] in n_d:
                    uid += 1
                    new_key = key_segmented[0] + '_' + str(uid)
                else:
                    new_key = key_segmented[0]
                n_d[new_key] = self.process_final(value)
            return n_d
        else:
            return json_dict


if __name__ == "__main__":
    logger.basicConfig(level=logger.INFO,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    path = input("Enter path to the book.main.xml file:")
    mp = ManualProcess(path)
    json_dict = mp.process_manual()
    path_segmented = os.path.abspath(path).split(os.sep)
    file_name, file_extension = path_segmented[-1].split('.')
    version_number = 'final'
    new_file = file_name + '_' + version_number + '.' + file_extension
    path_segmented[-1] = new_file
    new_file_path = os.path.join(path_segmented[0], os.sep, *path_segmented[1:])
    json.dump(json_dict, open(new_file_path, 'w'), indent=6)
