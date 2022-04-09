# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from nltk.corpus import stopwords 
from sentence_transformers import SentenceTransformer
import spacy
import re
import json
import os
import sys
from fuzzywuzzy import fuzz
from components.lg.ParaQA.paraQA import *
nlp=spacy.load("en_core_web_md", disable=["ner", "parser"])
MAX_CAN=60
MAX_OPT=5
device_type='cpu'
#jsonfile_str="jsonfile"
nlp=spacy.load("en_core_web_md", disable=["ner", "parser"])
model = SentenceTransformer('paraphrase-distilroberta-base-v1', device=device_type)
#EMB_FILE_PATH="E:\\work\\Sprint16\\QA\\Embeddings"
current_dir= os.path.dirname(os.path.realpath(__file__))
EMB_FILE_PATH =os.path.join(current_dir, "Embeddings")

stop_words = list(stopwords.words('english')) + \
    list(['what','why','where','when','who','how','whom'])+ list(["please"])+list(["tell"])
stop_words= set(stop_words)-set(["not", "no", "nor"])
BATCH_SIZE=100   
top_percentile=40
th_value=20 # threshould 
 
def tokenize(sen):
    processed= nlp(sen)
    toks=[token.text for token in processed]
    return toks

def process_str_(st, key):
    st=re.sub("\"]\[\"","#$#$$", st[2:-2])
    st=re.sub("hph", "-", st)
    #print(st)
    st=st.split("#$#$$")
    #print(st)
    if st[-1].strip().lower() not in key.lower():
        key= key + " " +  st[-1].strip()
    if len(st)>=3:
        key= " ".join([st[1].strip().capitalize() , '>>', st[2].strip().capitalize() , '>>', key.capitalize()])
    return key
    
    

def check_modelno(modelno):
    modelno_found=False
    with open(os.path.join(EMB_FILE_PATH, "emb.json"), 'r') as emb_json_file:
        embedding_json= json.load(emb_json_file)
    emb_json_keys= list(embedding_json.keys())
    for modelno_chain in emb_json_keys:
        for modelno_json in modelno_chain.split("/"):
            if modelno.startswith(modelno_json):
                modelno_found=True
                return modelno_found, embedding_json[modelno_chain]
    return modelno_found, []

class InteractionModule:
    def __init__(self, embedding_list):

        self.emb_mat=np.array(embedding_list[0])
        self.emb_mat_norm=self.emb_mat/ np.linalg.norm(self.emb_mat, axis=-1)[:, np.newaxis]
        self.keys=embedding_list[1]
        self.norm_keys=embedding_list[2]
        self.values=embedding_list[3]
        self.heads= embedding_list[4]
        self.json_filename=os.path.join(current_dir, "Manual_json", os.path.basename(embedding_list[5]).split("\\")[-1])

        with open(self.json_filename, 'r') as jsonfile:
            self.jsonfile=json.load(jsonfile)
        self.jsonfile_str="self.jsonfile"
        sys.stdout.write("ParaQA loading...(loading might take a few minutes) \n")
        self.load_passages()
        self.para_obj=ParagraphQA(self.passages)
        sys.stdout.write("ParaQA loading completed \n")
        
    def get_jsonfile(self):
        return self.jsonfile
        
    def load_passages(self):
        self.passages=[]
        for head, value in zip(self.heads, self.values):
            value_obj=eval(self.jsonfile_str + value)
            if type(value_obj) == list:
                value_obj =["This section talks about " + head + ". "] + value_obj 
                passage= " ".join(value_obj)
                self.passages.append(passage)
        
    def answer_question(self, question):
        ########Compute Question Embedding#################
        tok_list=[]
        candidate_embeddings=[]
        for token in tokenize(question.lower()):
            if token not in stop_words and token.strip() !="":
                tok_list.append(token)
        ques_processed= " ".join(tok_list)
        candidate_embeddings.append(model.encode([ques_processed]))
        candidate_embeddings= np.concatenate(candidate_embeddings,axis=0)
        candidate_embeddings=candidate_embeddings/ np.linalg.norm(candidate_embeddings, axis=-1)[:, np.newaxis]
        
        res= np.matmul(candidate_embeddings, np.transpose(self.emb_mat_norm)).reshape(-1)
        key_idc= (-res).argsort()[:MAX_CAN]
        key_score= [res[idc] for idc in key_idc]
        del candidate_embeddings

        ################################################
        score=[]    
        for  idc in key_idc:
            #score.append(fuzz.token_sort_ratio(ques_processed,keys[idc]))
            score.append(fuzz.token_set_ratio(ques_processed,self.keys[idc]))
        score= np.asarray(score)
        new_score= score*key_score
        idc_str=(-new_score).argsort()
        new_score=new_score.tolist()

        #max_score = new_score[0]
        max_score = new_score[idc_str[0]]
        th_score = max_score*(1 - top_percentile*0.01)


        ##################################################
        
        ##########Giving Option##########################
        
        self.values_option=[]
        self.keys_option=[]
        self.keys_score=[]

        if max_score <= th_value:
            #No further processing/ no options will be shown
            return
        #sys.stdout.write("MATCHES:\n")
        cnt=0
        for idc in idc_str:
            if new_score[idc] < th_score or  new_score[idc] < th_value or cnt > (MAX_OPT-1):
                break
            key_index= key_idc[idc]
            #self.keys_option.append(self.norm_keys[idc])
            new_str = process_str_(self.values[key_index], self.norm_keys[key_index])
            if new_str not in self.keys_option:
                self.keys_option.append(new_str)
                self.keys_score.append(new_score[idc])
                self.values_option.append(self.values[key_index])
                cnt+=1
            #sys.stdout.write(str(opt_no+1) +". "+ self.norm_keys[idc]+"\n")
            #self.values_option.append(self.jsonfile_str+self.values[idc])
            
        del res
        self.keys_option.append("None of the above")
        self.ques_processed=ques_processed
        #self.key_idc=key_idc
        #sys.stdout.write(str(len(values_option)+1) +". "+ "None of the above \n")
        

    
        
        
    
    
    def paraqa(self, questions):
        """
        

        Parameters
        ----------
        questions : TYPE List
            DESCRIPTION. list -str- questions

        Returns
        -------
        None.

        """
        op_feed=3
        answer=''
        reference=[]
        if op_feed==3:
            ans, refs, rtime, qtime= self.para_obj.get_answer_allen(questions)
            if ans[0]!='':
                answer=ans[0]
                reference=refs[0]
                #sys.stdout.write("answer: " + ans[0] +"\n")
                #sys.stdout.write("reference: " + refs[0] +"\n")
            #else:
                #sys.stdout.write("Sorry unable to answer your query, please contact customer care \n")
        return answer, reference
            
            
        
    
    
    


            

    
                    
                
        
        
        
    


                
    
        




if __name__=="__main__":
    model_no=input("Please enter the model no: ")
    modelno_found, embedding_list =check_modelno(model_no)
    if not modelno_found:
        sys.stdout.write("requested model NOT Supported \n")
    else:
        im_obj=InteractionModule(embedding_list)
        while True:
            question=input("Enter your query: ")
            im_obj.answer_question(question)
        
    
    

