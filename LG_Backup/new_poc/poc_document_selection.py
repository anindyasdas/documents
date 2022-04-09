# -*- coding: utf-8 -*-
"""
Created on Mon Apr  4 13:11:10 2022

@author: anindya06.das
"""
import re
from collections import defaultdict
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import json
import  utils as util
#model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
model = SentenceTransformer('paraphrase-mpnet-base-v2')
EMB_BATCH_SIZE=100
emb_file_name='emb_ko_wm_MFL71485465.json'
PART_NO="MFL71485465"
corpus= ["예약 버튼을 눌러 예약 시간을 맞추십시오.(예 현재 오후 1시이며 오후 7시에 세탁을 끝내고 싶을 경우 6시간 설정 (7-1=6)) 섹션.  예약 버튼에 불이 들어오고 '300'가 표시됩니다. 지금부터 세탁을 끝내고 싶을 때까지의 시간(600)이 될 때까지 예약 버튼을 누르세요. 예약 버튼을 한 번 누를 때마다 1시간씩 시간이 늘어납니다.",
 '앱 화면에서 다운로드할 코스를 선택하고 다운로드 버튼을 누르세요 섹션.  한 번에 하나의 코스만 제품에 저장 가능합니다.',
 '예약 설정하기 섹션.  원하는 시간에 세탁을 마치고 싶을 때 사용하세요.',
 '시작/일시정지 버튼을 누르세요 섹션.  예약을 취소할 때는 전원 버튼을 누르세요.',
 '이전설치 및 재설치 한 경우 섹션.  초기 제품 설치 후 제품의 위치를 바꾸거나, 이사 후 재설치한 경우']


def split_value_key_chain(val):
    st = val[2:-2].replace('"]["', "#$#$$")
    st=st.split("#$#$$")
    return st

def tokenizer(doc): 
    """
    This is white space tokenizer that removes 

    Parameters
    ----------
    doc : str text 

    Returns
    -------
    tokens

    """
    token_pattern=r"(?u)\b\w\w+\b"
    token_pattern = re.compile(token_pattern) 
    return token_pattern.findall(doc)

def split_sentences(doc):
    sentences= [sentence.strip() for sentence in re.split(r'(?<=\w[!\?\.])\s', doc)]
    return sentences


def get_vocab(doc, tokenizer):
    """
    

    Parameters
    ----------
    doc : list of documets
    tokenizer : function to tokenize texts

    Returns
    -------
    vocab : list of unique words

    """
    doc= " ".join(doc)
    vocab = list(set(tokenizer(doc)))
    return vocab

def get_document_freq(doc, tokenizer):
    """
    

    Parameters
    ----------
    doc : list of documets
    tokenizer: function to tokenize texts

    Returns
    -------
    dictinray of words to doc frequency

    """
    num_doc=len(doc)
    df_dict=defaultdict()
    for doc_item in doc:
        for word in set(tokenizer(doc_item)):
            if word in df_dict:
                df_dict[word]+=1
            else:
                df_dict[word]=1
                
    df_dict={word:doc_count/num_doc for word, doc_count in df_dict.items()}
    return df_dict

def get_stopwords(doc, tokenizer, max_df=0.85):
    """
    This fucntion extract the stopwords from a given list of documents based on maximum document frequency

    Parameters
    ----------
    doc : list of documents
    tokenizer : method to tokenize text
    max_df : integer value specified the maximum allowed document frequenct
        DESCRIPTION. The default is 0.85.

    Returns
    -------
    stop_words : TYPE
        DESCRIPTION.

    """
    stop_words=[]
    df_dict=get_document_freq(doc, tokenizer)
    for word, doc_freq in df_dict.items():
        if doc_freq > max_df: 
            stop_words.append(word)
    return stop_words
        
def read_stopwords_list(file_name):
    stop_words=[]
    with open(file_name, 'r', encoding='utf-8-sig') as new_file:
        for line in new_file:
            stop_words.append(line.strip())
    return list(set(stop_words))
            
def get_processed_sentences(sentences, tokenizer, stop_words=[]):
    """
    This function takes list of sentences, removes the stopwords and return the processed
    sentences

    Parameters
    ----------
    sentences : list of text

    Returns
    -------
    processed list of text

    """
    processed_sentences=[]
    for sen in sentences:
        processed_sen=" ".join([token for token in tokenizer(sen) if token not in stop_words])
        processed_sentences.append(processed_sen.strip())
    return processed_sentences
       
        
    
def get_inverted_dict(doc, tokenizer, stop_words=[]):
    inverted_dict={}
    for doc_id, doc_item in enumerate(doc):
        sentences=split_sentences(doc_item)
        sentences=get_processed_sentences(sentences, tokenizer, stop_words)
        for sen in sentences:
            if sen not in inverted_dict:
                inverted_dict[sen]={doc_id}
            else:
                inverted_dict[sen].add(doc_id)
    #keys= list(inverted_dict.keys())
    
    return inverted_dict
                
   
def get_embeddings(keys):
    embeddings = [] 
    for i in range(0, len(keys), EMB_BATCH_SIZE):
        print("*******from {} to {} *******".format(i, i + EMB_BATCH_SIZE))
        item = keys[i:i + EMB_BATCH_SIZE]
        id_to_embedding_batch = model.encode(item)
        embeddings.append(id_to_embedding_batch)
        print("*************processed***************")
    emb_mat = np.concatenate(embeddings, axis=0)
    emb_mat = emb_mat / np.linalg.norm(emb_mat, axis=-1)[:, np.newaxis]
    return emb_mat



################## Retrieve Para#########################

def retrieve_passages(key_indices, inverted_dict, doc):
    keys= list(inverted_dict.keys())
    docs=[]
    doc_ids=[]
    for idc in key_indices:
        #print("idc:", idc)
        sentence=keys[idc]
        print("key:" + sentence, file=out_file)
        for doc_id in inverted_dict[sentence]:
            if doc_id not in doc_ids:
                doc_ids.append(doc_id)
                docs.append(doc[doc_id])
    print("########################", file=out_file)
    return docs

def compute_scores(question,tokenizer, emb_mat, stop_words):
    candidate_embeddings = []
    sentences=get_processed_sentences([question], tokenizer, stop_words)
    candidate_embeddings.append(model.encode(sentences))
    candidate_embeddings = np.concatenate(candidate_embeddings, axis=0)
    candidate_embeddings = candidate_embeddings / np.linalg.norm(candidate_embeddings, axis=-1)[:, np.newaxis]

    res = np.matmul(candidate_embeddings, np.transpose(emb_mat)).reshape(-1)
    key_idc = (-res).argsort()
    return key_idc
    #key_score = [res[idc] for idc in key_idc]
##################Load Passages######################
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
                #value_obj = [head + " " + "섹션. "] + util.get_list(value_obj)
                value_obj = util.get_list(value_obj)
                passage = " ".join(value_obj)
                passages.append(passage)
        return passages
    
##########################################################
out_file=open('output.txt', 'w', encoding='utf-8-sig')
stopword_file=".\stopwords.txt"
stop_word_list=read_stopwords_list(stopword_file)

###################Load Passages############################

embedding_list = _load_embedding_file(emb_file_name)
qa_engine = DocBasedQaEngine(embedding_list)

list_of_passages = qa_engine.load_passages()
corpus=list_of_passages +["섬유 유연제가 넘치지 않게 MAX(기준선)a 이하까지 넣으세요. 기준선을 넘을 경우 섬유 유연제가 드럼 안으로 바로 투입될 수 있습니다"]
#####################Compute inverted dict##################################
overall_dict={}
part_no=PART_NO
stop_words= get_stopwords(corpus, tokenizer, max_df=0.85) + stop_word_list
stop_words= list(set(stop_words))
inverted_dict= get_inverted_dict(corpus, tokenizer, stop_words=stop_words)
keys= list(inverted_dict.keys())
key_embeddings= get_embeddings(keys)
overall_dict[part_no]={'inv_dict':inverted_dict, 'inv_key_emb':key_embeddings}
#######################inference inverted dict##################
inverted_dict= overall_dict[part_no]['inv_dict']
emb_mat= overall_dict[part_no]['inv_key_emb']
user_question='섬유 유연제를 얼마나 넣어야 하나요?'
key_indices=compute_scores(user_question,tokenizer, emb_mat, stop_words)
for num, idc in enumerate(key_indices):
    if 'MAX' in keys[idc]:
        print(num)
    

p=retrieve_passages(key_indices[:5], inverted_dict, corpus)
#with open('output.txt', 'w', encoding='utf-8-sig') as out_file:
for num, line in enumerate(p):
    print(str(num) + ":"+ line, file=out_file )

