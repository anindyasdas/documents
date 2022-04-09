# -------------------------------------------------
# Copyright(c) 2021-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------

# Standard library imports
import json
import os
import warnings

warnings.filterwarnings("ignore")

# Third party imports
import numpy as np
from fuzzywuzzy import fuzz
import importlib

# Local application imports
from apps.ker_ko.document_based.constants import doc_search_model_folder, stop_words, model, top_percentile, th_value, MAX_OPT
from apps.ker_ko.document_based.output_standardizer.jsonparser import JSONParser
import apps.ker_ko.document_based.utils as util

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class DocBasedQaEngine(object):
    def __init__(self, embedding_list):
        self.emb_mat = np.array(embedding_list[0])
        self.emb_mat_norm = self.emb_mat
        self.keys = embedding_list[1]
        self.norm_keys = embedding_list[2]
        self.values = embedding_list[3]
        self.heads = embedding_list[4]
        self.manual_content_dict = {}
        self.json_filename = os.path.join(doc_search_model_folder, "Manual_json",
                                          os.path.basename(embedding_list[5]).split("\\")[-1])
        with open(self.json_filename, 'r', encoding='utf-8-sig') as jsonfile:
            self.jsonfile = json.load(jsonfile)
        self.jsonfile_str = "self.jsonfile"
        self.json_parser = JSONParser()

    def get_jsonfile(self):
        return self.jsonfile

    def load_passages(self):
        passages = []
        for head, value in zip(self.heads, self.values):
            value_obj = eval(self.jsonfile_str + value)
            if type(value_obj) == list:
                value_obj = [head + " " + "섹션. "] + util.get_list(value_obj)
                passage = " ".join(value_obj)
                passages.append(passage)
        return passages

    def manual_view_loader(self):
        """
        This function loads section-wise keys for vieing manuals

        Returns
        -------
        A dictionary containing the manuals keys & values
        {
            "operation":{"key":[], "value":[],
                         "installation":{"key:[], "value":[]
                                         }

        """
        manual_content_dict = {}
        for item in self.values:
            section, section_title, val = util.get_section_headings(item)
            if section not in manual_content_dict:
                manual_content_dict[section] = {"key": [], "value": []}
            if section_title != '' and val != '' and \
                    (section_title not in manual_content_dict[section]["key"]) and \
                    (val not in manual_content_dict[section]["value"]):
                manual_content_dict[section]["key"].append(section_title)
                manual_content_dict[section]["value"].append(val)
        self.manual_content_dict = manual_content_dict

    def answer_question(self, question):
        ########Compute Question Embedding#################
        tok_list = []
        candidate_embeddings = []
        for token in util.tokenize(question):
            if token not in stop_words and token.strip() != "":
                tok_list.append(token)
        ques_processed = " ".join(tok_list)
        candidate_embeddings.append(model.encode([ques_processed]))
        candidate_embeddings = np.concatenate(candidate_embeddings, axis=0)
        candidate_embeddings = candidate_embeddings / np.linalg.norm(candidate_embeddings, axis=-1)[:, np.newaxis]

        res = np.matmul(candidate_embeddings, np.transpose(self.emb_mat_norm)).reshape(-1)
        #Sort all keys in decreasing order of embeddings score(cosine sim) that to be combined subsequently with FuzzyWuzzy Score
        key_idc = (-res).argsort()
        key_score = [res[idc] for idc in key_idc]
        del candidate_embeddings
        ################################################
        score = []
        for idc in key_idc:
            score.append(fuzz.token_set_ratio(ques_processed, self.keys[idc]))
        score = np.asarray(score)
        new_score = score * key_score
        idc_str = (-new_score).argsort()
        new_score = new_score.tolist()
        max_score = new_score[idc_str[0]]
        # print(max_score, top_percentile)
        th_score = max_score * (1 - top_percentile * 0.01)
        ##################################################
        ##########Giving Option##########################
        self.values_option = []
        self.keys_option = []
        self.keys_score = []

        if max_score <= th_value:
            # No further processing/ no options will be shown
            return
        cnt = 0
        d = {}
        d1 = {}
        for idc in idc_str:
            if new_score[idc] < th_score or new_score[idc] < th_value or cnt > (MAX_OPT - 1):
                break
            key_index = key_idc[idc]
            val_fetched = self.values[key_index]
            key_fetched = self.norm_keys[key_index]
            val_fetched, key_fetched = util.handle_description_summary(val_fetched, key_fetched)
            if len(util.split_value_key_chain(val_fetched))<2:
                continue
            new_str = util.process_str_(val_fetched, key_fetched)
            if new_str not in self.keys_option:
                self.keys_option.append(new_str)
                self.keys_score.append(new_score[idc])
                self.values_option.append(val_fetched)
                cnt += 1
                d1[new_str] = round(new_score[idc], 2)
                d[new_str] = fuzz.token_set_ratio(ques_processed, new_str)
        logger.debug("Before score change=%s", d1)
        logger.debug("After score change=%s", d)
        del res
        self.keys_option.append("위의 어느 것도")
        self.ques_processed = ques_processed
        d["위의 어느 것도"] = 0.0
        d = dict(sorted(d.items(), key=lambda item: float(item[1]), reverse=True))
        return d
