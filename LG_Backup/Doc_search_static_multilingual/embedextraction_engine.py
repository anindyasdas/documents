# -*- coding: utf-8 -*-
""""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anindya06.das@lge.com
##############################################################################
"""
import numpy as np
from sentence_transformers import SentenceTransformer
import re
import json
import os
import utils.params as cs
import utils.helper as hp

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')


class PrepareEmbedding:
    """
    This is the class for processing obtaining the embeddings of context_keys
    for a given manual
    Output: emb.json file
    format:
        {MODELNOS:[context_key_embedding_list(size: no_context_keys, 768),
                   context_keys_list, normalized_context_keys, value_key_chain,
                   extracted_json_path_referreed by valuekey chain sequence]}
    """

    def __init__(self, filename, json_file_name):
        key_val = open(filename, "r", encoding='utf-8-sig')
        self.json_file_name = json_file_name
        with open(self.json_file_name, 'r') as jsonfile:
            self.jsonfile = json.load(jsonfile)
        self.EMB_FILE_PATH = "./Embeddings_ko"
        self.load_keys_values(key_val)
        self.meta_embedding_json = {}
        self.prepare_embeddings()

    def load_keys_values(self, key_val):
        keys, norm_keys, values, heads, pos = [], [], [], [], None
        for item in key_val:
            item = eval(item)
            if type(item) == list:
                item.sort()
                self.model_no = "/".join(item)
                continue
            item0_l = item[0].lower()
            item2_l = item[2].lower()
            if cs.keywords_map[cs.DESCRIPTION_KEY.lower()] in item0_l:
                pos = re.search(cs.keywords_map[cs.DESCRIPTION_KEY.lower()], item0_l)  # description
            if cs.keywords_map[cs.HAVE_FEATURES.lower()] in item0_l:
                pos = re.search(cs.keywords_map[cs.HAVE_FEATURES.lower()], item0_l)  # feature
            if pos:
                norm_keys.append(item0_l[:pos.start()])
                pos = None
            else:
                norm_keys.append(item0_l)  # norm key contains the num tag
            keys.append(item0_l)  # keys does not contain numtag for duplicates
            values.append(item[1])
            heads.append(item2_l)
        self.keys = keys
        self.norm_keys = norm_keys
        self.values = values
        self.heads = heads

    def prepare_embeddings(self):
        if not os.path.exists(self.EMB_FILE_PATH):
            os.makedirs(self.EMB_FILE_PATH)
        meta_emb_json_file_path = os.path.join(self.EMB_FILE_PATH, "meta_emb.json")

        if os.path.exists(meta_emb_json_file_path):
            with open(meta_emb_json_file_path, 'r', encoding='utf-8-sig') as meta_emb_json_file:
                self.meta_embedding_json = json.load(meta_emb_json_file)
        embeddings = []
        for i in range(0, len(self.keys), cs.EMB_BATCH_SIZE):
            print("*******from {} to {} *******".format(i, i + cs.EMB_BATCH_SIZE))
            item = self.keys[i:i + cs.EMB_BATCH_SIZE]
            id_to_embedding_batch = model.encode(item)
            embeddings.append(id_to_embedding_batch)
            print("*************processed***************")
        self.emb_mat = np.concatenate(embeddings, axis=0)
        self.emb_mat = self.emb_mat / np.linalg.norm(self.emb_mat, axis=-1)[:, np.newaxis]
        json_values = [self.emb_mat.tolist(), self.keys, self.norm_keys, self.values, self.heads, self.json_file_name]
        emb_file_name = "emb_" + os.path.basename(self.json_file_name)
        self.meta_embedding_json[self.model_no] = emb_file_name
        hp.save_file(self.meta_embedding_json, meta_emb_json_file_path, ftype='json', encoding='utf-8-sig')
        hp.save_file(json_values, os.path.join(self.EMB_FILE_PATH, emb_file_name), ftype='json', encoding='utf-8-sig')


if __name__ == "__main__":
    key_val_filename = input("Enter path to the key value file path:")
    json_filename = input("Enter path to the Manual json file path:")
    P_emb_obj = PrepareEmbedding(key_val_filename, json_filename)
