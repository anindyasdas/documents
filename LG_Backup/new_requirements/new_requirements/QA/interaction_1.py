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
MAX_OPT=6
device_type='cpu'
#jsonfile_str="jsonfile"
nlp=spacy.load("en_core_web_md", disable=["ner", "parser"])
model = SentenceTransformer('paraphrase-distilroberta-base-v1', device=device_type)
EMB_FILE_PATH="C:\\Users\\anindya06.das\\Desktop\\process_manual\\SentenceEmb\\Embeddings"

stop_words = list(stopwords.words('english')) + \
    list(['what','why','where','when','who','how','whom'])+ list(["please"])+list(["tell"])
stop_words= set(stop_words)-set(["not", "no", "nor"])
BATCH_SIZE=100   
 
def tokenize(sen):
    processed= nlp(sen)
    toks=[token.text for token in processed]
    return toks

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
        self.keys=embedding_list[1]
        self.norm_keys=embedding_list[2]
        self.values=embedding_list[3]
        self.heads= embedding_list[4]
        self.json_filename=embedding_list[5]
        with open(self.json_filename, 'r') as jsonfile:
            self.jsonfile=json.load(jsonfile)
        self.jsonfile_str="self.jsonfile"
        sys.stdout.write("ParaQA loading...(loading might take a few minutes) \n")
        self.load_passages()
        self.para_obj=ParagraphQA(self.passages)
        sys.stdout.write("ParaQA loading completed \n")
        
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
        
        res= np.matmul(candidate_embeddings, np.transpose(self.emb_mat)).reshape(-1)
        key_idc= (-res).argsort()[:MAX_CAN] 
        del res 
        del candidate_embeddings
        
        ##########Giving Option##########################
        
        values_option=[]
        sys.stdout.write("MATCHES:\n")
        for opt_no, idc in enumerate(key_idc[:MAX_OPT]): 
            sys.stdout.write(str(opt_no+1) +". "+ self.norm_keys[idc]+"\n")
            values_option.append(self.jsonfile_str+self.values[idc])
        sys.stdout.write(str(len(values_option)+1) +". "+ "None of the above \n")
        option_selected=-1
        while option_selected <0:
            option_selected= int(input("Select Options: ")) -1
            if option_selected <len(values_option) and option_selected>=0:
                new_str=json.dumps(eval(values_option[option_selected]), indent=6)
                new_str=re.sub("hph", "-", new_str)
                sys.stdout.write(new_str +"\n")
            elif option_selected==len(values_option):
                op_feed=2
                self.string_matching(op_feed, ques_processed, key_idc)
                return
            else:
                sys.stdout.write("wrong option \n")
                option_selected=-1
        
        op_feed= int(input("1. Problem Solved 2. Problem is still there \n"))
        self.string_matching(op_feed, ques_processed, key_idc)
        
        
        
    def paraqa(self, op_feed, questions):
        """
        

        Parameters
        ----------
        questions : TYPE List
            DESCRIPTION. list -str- questions

        Returns
        -------
        None.

        """
        if op_feed==3:
            ans, refs, rtime, qtime= self.para_obj.get_answer_allen(questions)
            if ans[0]!='':
                sys.stdout.write("answer: " + ans[0] +"\n")
                sys.stdout.write("reference: " + refs[0] +"\n")
            else:
                sys.stdout.write("Sorry unable to answer your query, please contact customer care \n")
            
            
        
    def string_matching(self, op_feed, ques_processed, key_idc):
        if op_feed==2:
            score=[]    
            for  idc in key_idc:
                #score.append(fuzz.token_sort_ratio(ques_processed,keys[idc]))
                score.append(fuzz.token_set_ratio(ques_processed,self.keys[idc]))
            score= np.asarray(score)
            idc_str=(-score).argsort()
            values_option=[]
            sys.stdout.write("Does the following matches your description? \n")
            for opt_no, idc in enumerate(idc_str[:MAX_OPT]):
                key_index= key_idc[idc]
                #sys.stdout.write("#"*100)
                sys.stdout.write(str(opt_no+1) +". " + self.norm_keys[key_index]+"\n")
                values_option.append(self.jsonfile_str+self.values[key_index])
            sys.stdout.write(str(len(values_option)+1) +". "+ "None of the above \n")
                #sys.stdout.write(keys[key_index])
            option_selected=-1
            while option_selected <0:
                option_selected= int(input("Select Options: ")) -1
                if option_selected <len(values_option) and option_selected>=0:
                    new_str=json.dumps(eval(values_option[option_selected]), indent=6)
                    new_str=re.sub("hph", "-", new_str)
                    sys.stdout.write(new_str+"\n")
                elif option_selected==len(values_option):
                    op_feed= input("Want more specific answer ? y:yes , n:no \n")
                    if op_feed.lower() in ["yes", 'y']:
                        op_feed=3
                    self.paraqa(op_feed, [question])
                    return
                else:
                    sys.stdout.write("wrong option\n")
                    option_selected=-1
            op_feed= int(input("1. Problem Solved 2. Problem is still there 3. Need more specific answer\n"))
            self.paraqa(op_feed, [question])
                    
                
        
        
        
    


                
    
        




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
        
    
    

