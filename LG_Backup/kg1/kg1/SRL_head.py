# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 18:48:27 2021

@author: anindya06.das
"""
#%%
import re
from fuzzywuzzy import fuzz
import numpy as np
from sklearn.metrics import accuracy_score
from nltk.tokenize import word_tokenize 
from nltk.corpus import stopwords 
from allennlp.predictors.predictor import Predictor
import allennlp_models.tagging
predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/structured-prediction-srl-bert.2020.12.15.tar.gz")

stop_words = list(stopwords.words('english')) + list(['what','why','where','when','who','how','whom'])
    
stop_words= set(stop_words)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-distilroberta-base-v1')

######d is dictionary of all entity 3.9million very large##########
import json
file=open("./Desktop/web_dict.json", 'r')
d=json.load(file)

#####Select only those entities present in the question head entity####

f1= open("./Desktop/web_test.txt","r")
f2= open("./Desktop/web_test.txt","r")

n_d={}
for line in f2:
    q,name,head,a=line.strip().split("\t")
    if head not in n_d:
        n_d[head]=d[head]
        
for line in f1:
    q,name,head,a=line.strip().split("\t")
    if head not in n_d:
        n_d[head]=d[head]
    
f1.close()
f2.close()
    
#%% Entity Embedding   
enity_to_id={}
id_to_entity=[]
i=0
for k,v in n_d.items():
    id_to_entity.append(v[0])
    enity_to_id[i]=k
    i+=1

batch_size=100    
embeddings=[]

for i in range(0, len(id_to_entity), batch_size):
    print("*******from {} to {} *******".format(i, i+batch_size))
    item= id_to_entity[i:i + batch_size]
    id_to_embedding_batch= model.encode(item)
    embeddings.append(id_to_embedding_batch)
    print("*************processed***************")
    
emb_mat= np.concatenate(embeddings, axis=0)
#%%

#%%


f2= open("./Desktop/web_test.txt","r")
d_set=[]
for line in f2:
    q,name,head,a=line.strip().split("\t")
    d_set.append((q,name))
        
        
def calculate(model,d_set, emb_mat):

    #%%
    preds=[]
    actuals=[]
    new_dset=[]
    for item in d_set:
        sen=item[0]
        actual=item[1]
        pred=predictor.predict(
            sentence=sen
        )
        
        d_all=[]
        for item in pred['verbs']:
            d_a={}
            d_a['verb']=item['verb']
            des=item['description']
            pos = re.findall("\[.*?\]", des)
            for arg in pos:
                arg=arg[1:-1]
                key, value= arg.split(":")
                d_a[key.strip()]=value.strip()
            d_all.append(d_a)
            
       
        candidates=[]
        candidate_embeddings=[]
        for di in d_all:
            for key in di:
                if key in ['ARG0','ARG1','ARGM-ADV','ARG2']:
                    if di[key] not in ['what','why','where','when','who','how','whom']:
                        candidates.append(di[key])
                        candidate_embeddings.append(model.encode(di[key]))
        
        if len(candidate_embeddings)==0:
            tok_list=[]
            for token in word_tokenize(sen):
                if token not in stop_words:
                    tok_list.append(token)
            new_sen=" ".join(tok_list)
            candidate_embeddings.append(model.encode([new_sen]))
            
                
        #print(candidate_embeddings, sen)
        candidate_embeddings= np.concatenate(candidate_embeddings,axis=0)
        #print(candidate_embeddings)
        candidate_embeddings= candidate_embeddings.reshape(-1,768)
        
        res= np.matmul(candidate_embeddings, np.transpose(emb_mat))
        arg_max_val=np.argmax(res, axis=-1)
        
        max_vals= np.max(res, axis=-1)
        canditate_with_max_val_arg= np.argmax(max_vals,axis=-1)
        
        max_argument =arg_max_val[canditate_with_max_val_arg]
        prediction= id_to_entity[max_argument]
        preds.append(prediction)
        actuals.append(actual)
        new_dset.append((sen, prediction, actual))
    return preds, actuals, new_dset
#%%  

def calculate1(model,d_set, emb_mat):

    #%%
    k=5
    preds=[]
    actuals=[]
    new_dset=[]
    for item in d_set:
        sen=item[0]
        actual=item[1]
        pred=predictor.predict(
            sentence=sen
        )
        print(sen, pred)
        
        d_all=[]
        for item in pred['verbs']:
            d_a={}
            d_a['verb']=item['verb']
            des=item['description']
            pos = re.findall("\[.*?\]", des)
            for arg in pos:
                arg=arg[1:-1]
                key, value= arg.split(":")
                d_a[key.strip()]=value.strip()
            d_all.append(d_a)
        print(d_all)
        candidates=[]
        candidate_embeddings=[]
        for di in d_all:
            for key in di:
                if key in ['ARG0','ARG1','ARGM-ADV','ARG2']:
                    if di[key] not in ['what','why','where','when','who','how','whom'] and di[key] not in stop_words:
                        candidates.append(di[key])
                        candidate_embeddings.append(model.encode(di[key]))
        
        if len(candidate_embeddings)==0:
            tok_list=[]
            for token in word_tokenize(sen):
                if token not in stop_words:
                    tok_list.append(token)
            new_sen=" ".join(tok_list)
            candidate_embeddings.append(model.encode([new_sen]))
            candidates.append(new_sen)
            
                
        #print(candidate_embeddings, sen)
        candidate_embeddings= np.concatenate(candidate_embeddings,axis=0)
        #print(candidate_embeddings)
        candidate_embeddings= candidate_embeddings.reshape(-1,768)
        
        res= np.matmul(candidate_embeddings, np.transpose(emb_mat))
        #print("res:",res.shape, type(res))
        
        #print(res)
        idc= (-res).argsort()[:,:k]
        print(np.argmax(res, axis=-1))
        print("idc:",idc, type(res))
        idc_scored=-1
        max_score=0
        for index in range(len(idc)):
            score=[]
            can_ids= idc[index]
            candidates_selected=[id_to_entity[cid] for cid in can_ids]
            print("candidates_selected:",candidates_selected)
            c=candidates[index]
            print("c:",c)
            for c1 in candidates_selected:
                score.append(fuzz.partial_ratio(c,c1))
            arg_max= score.index(max(score))
            arg_max_can=can_ids[arg_max]
            m_score=max(score)
            if m_score > max_score:
                max_score=m_score
                idc_scored= arg_max_can
            
        
        prediction= id_to_entity[idc_scored]
        preds.append(prediction)
        actuals.append(actual)
        new_dset.append((sen, prediction, actual))
    return preds, actuals, new_dset

global rx
def calculate2(model,d_set, emb_mat):

    #%%
    k=10
    preds=[]
    actuals=[]
    new_dset=[]
    for item in d_set:
        sen=item[0]
        actual=item[1]
        pred=predictor.predict(
            sentence=sen
        )
        #print(sen, pred)
        
        d_all=[]
        for item in pred['verbs']:
            d_a={}
            d_a['verb']=item['verb']
            des=item['description']
            pos = re.findall("\[.*?\]", des)
            for arg in pos:
                arg=arg[1:-1]
                key, value= arg.split(":")
                d_a[key.strip()]=value.strip()
            d_all.append(d_a)
        #print(d_all)
        candidates=[]
        candidate_embeddings=[]
        for di in d_all:
            for key in di:
                if key in ['ARG0','ARG1','ARGM-ADV','ARG2']:
                    if di[key] not in ['what','why','where','when','who','how','whom'] and di[key] not in stop_words:
                        candidates.append(di[key])
                        candidate_embeddings.append(model.encode(di[key]))
        
        if len(candidate_embeddings)==0:
            tok_list=[]
            for token in word_tokenize(sen):
                if token not in stop_words:
                    tok_list.append(token)
            new_sen=" ".join(tok_list)
            candidate_embeddings.append(model.encode([new_sen]))
            candidates.append(new_sen)
            
                
        #print(candidate_embeddings, sen)
        candidate_embeddings= np.concatenate(candidate_embeddings,axis=0)
        #print(candidate_embeddings)
        candidate_embeddings= candidate_embeddings.reshape(-1,768)
        
        res= np.matmul(candidate_embeddings, np.transpose(emb_mat))
        #print("res:",res.shape, type(res))
        
        #print(res)
        #####################
        row, col= res.shape
        idc_ = []
        for o in range(row):
            idc_.append(np.arange(0,col))
        idc_=np.stack(idc_).flatten()
        res=res.flatten()
        list_of_tuples=list(tuple(zip(idc_,res)))
        list_of_tuples.sort(key=lambda x:x[1], reverse=True)
        list_of_tuples=list_of_tuples[:k]
        cand= [id_to_entity[ind[0]] for ind in list_of_tuples]
        ################################
        #idc= (-res).argsort()[:,:k]
        #idc=idc.flatten()
        #cand= [id_to_entity[ind] for ind in idc]
        scores=[]
        for c in cand:
            scores.append(fuzz.partial_ratio(sen, c))
            #scores.append(fuzz.ratio(sen, c))
            #scores.append(fuzz.token_set_ratio(sen, c))
        arg_max= scores.index(max(scores))
        prediction=cand[arg_max]
        
        """
        cand_emb= model.encode(cand)
        cand_emb= cand_emb.reshape(-1,768)
        sen_emb=model.encode([sen])
        sen_emb= sen_emb.reshape(-1,768)
        resf= np.matmul(sen_emb, np.transpose(cand_emb))
        #print(resf)
        arg_idx=np.argmax(resf, axis=-1).item()
        #print(arg_idx)
        """
        preds.append(prediction)
        actuals.append(actual)
        new_dset.append((sen, prediction, actual))
    return preds, actuals, new_dset

preds, actuals, new_dset=calculate2(model, d_set, emb_mat) 

print("Accuracy Score:", accuracy_score(actuals, preds))

matches=open("./Desktop/matches.txt",'w')
unmatched=open("./Desktop/unmatched.txt", "w")
for items in new_dset:
    if items[1]==items[2]:
        print(items[0],"\t",items[1] , "\t", items[2], file=matches)
    else:
        print(items[0],"\t",items[1] , "\t", items[2], file=unmatched)
#%%

pred=predictor.predict(
    sentence="what did the islamic people believe in"
)

d_all=[]
for item in pred['verbs']:
    d_a={}
    d_a['verb']=item['verb']
    des=item['description']
    pos = re.findall("\[.*?\]", des)
    for arg in pos:
        arg=arg[1:-1]
        key, value= arg.split(":")
        d_a[key.strip()]=value.strip()
    d_all.append(d_a)
    
#%%
candidates=[]
candidate_embeddings=[]
for di in d_all:
    for key in di:
        if key in ['ARG0','ARG1','ARGM-ADV', 'ARG2']:
            if di[key] not in ['what','why','where','when','who','how','whom']:
                candidates.append(di[key])
                candidate_embeddings.append(model.encode(di[key]))
candidate_embeddings= np.concatenate(candidate_embeddings,axis=0)
candidate_embeddings= candidate_embeddings.reshape(-1,768)

res= np.matmul(candidate_embeddings, np.transpose(emb_mat))
arg_max_val=np.argmax(res, axis=-1)

max_vals= np.max(res, axis=-1)
canditate_with_max_val_arg= np.argmax(max_vals,axis=-1)

max_argument =arg_max_val[canditate_with_max_val_arg]
prediction= id_to_entity[max_argument]
print(prediction)
                
        
