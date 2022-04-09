# -*- coding: utf-8 -*-
"""
Created on Fri Apr  1 17:58:02 2022

@author: anindya06.das
"""
import os
import json
import requests
from configparser import ConfigParser
import numpy as np
from bm25_retrieval import PassageRetrieval
from bm25_tokenizers import white_space_tokenizer
import  utils as util
emb_file_name='emb_ko_wm_MFL71485465.json'
user_question='세탁기가 돌아가는 중에 전원을 얼마나 눌러야 하나요?'
def _load_embedding_file(emb_file_name):
        """
        reads the embedding file, load and return the embedding list containing
        embeddings, keys, normalized keys, values, json file name

        Parameters
        ----------
        emb_file_name : TYPE str
            DESCRIPTION. name of the embedding file

        Returns
        -------
        embedding_list : TYPE list
            DESCRIPTION. list containing the embedding matrix,
            keys, normalized keys, values, heading, json file name

        """
        with open(os.path.join(emb_file_name), 'r', encoding='utf-8-sig') as emb_json_file: 
            embedding_list= json.load(emb_json_file)
        return embedding_list

class DocBasedQaEngine(object):
    def __init__(self, embedding_list):
        self.emb_mat = np.array(embedding_list[0])
        self.emb_mat_norm = self.emb_mat
        self.keys = embedding_list[1]
        self.norm_keys = embedding_list[2]
        self.values = embedding_list[3]
        self.heads = embedding_list[4]
        self.manual_content_dict = {}
        self.json_filename = os.path.join("Manual_json",
                                          os.path.basename(embedding_list[5]).split("\\")[-1])
        with open(self.json_filename, 'r', encoding='utf-8-sig') as jsonfile:
            self.jsonfile = json.load(jsonfile)
        self.jsonfile_str = "self.jsonfile"

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
    
embedding_list = _load_embedding_file(emb_file_name)
qa_engine = DocBasedQaEngine(embedding_list)


korean_tokenizer = white_space_tokenizer
bm25_passage_retriever = PassageRetrieval(korean_tokenizer)
list_of_passages = qa_engine.load_passages()
bm25_passage_retriever.fit(list_of_passages)
user_questions=['섬유 유연제를 얼마나 넣어야 하나요?',
                '세탁기가 돌아가는 중에 전원을 얼마나 눌러야 하나요?',
                '예약 버튼을 한 번 누를때 마다 몇 시간씩 늘어나나요?',
                '탈수에 몇 단계가 있습니까?',
                '얼마나 큰 이불을 넣을 수 있나요?'
]

targets=["섬유 유연제가 넘치지 않게 MAX(기준선)a 이하까지 넣으세요. 기준선을 넘을 경우 섬유 유연제가 드럼 안으로 바로 투입될 수 있습니다",
        "제품 동작 중 전원을 끌 때는 1초 이상 누르세요.",
        "지금부터 세탁을 끝내고 싶을 때까지의 시간(600)이 될 때까지 예약 버튼을 누르세요. 예약 버튼을 한 번 누를 때마다 1시간씩 시간이 늘어납니다.",
        "탈수 세기를 5단계(건조맞춤, 강, 중, 약, 섬세)로 나누어 선택할 수 있습니다.",
        "담요 및 이불속 4 kg 이하(크기는 180 X 220 ㎝ 이내일 것)"]
for user_question, target in zip(user_questions, targets):
    top_passages_relevant_to_question = bm25_passage_retriever.most_similar(user_question, topk=350)


    for rank, item in enumerate(top_passages_relevant_to_question):
        if target in item:
            print(rank)
        

        