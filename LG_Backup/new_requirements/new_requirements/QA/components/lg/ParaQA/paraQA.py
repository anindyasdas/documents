"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""

#import torch
import time
import spacy
#import pandas as pd
#import numpy as np
import re
#from transformers import BertForQuestionAnswering
#from transformers import BertTokenizer
#from transformers import pipeline
from allennlp.predictors.predictor import Predictor
from components.lg.ParaQA.passageRetrival import PassageRetrieval
import pyhocon
from components.lg.ParaQA import constants

def construct_answer(context_tokens, span):
    """
    This function process tokens
    Input
    -------
    (1) list of token strings
    (2) list of integers containing range of actual answer

    Returns 
    -------
    str

    """
   
    
            
    start_span= span[0]
    end_span=span[1]
    context_len= len(context_tokens)
    #start_sentence_index=0
    #end_sentence_index= len(context_tokens)-1
    while start_span >=0:
        if context_tokens[start_span] in ['!', '.', '?', ').', '].']:
            start_span =start_span+1
            break
        start_span-=1
    while end_span < context_len:
        if context_tokens[end_span] in ['!', '.', '?', ').', '].']:
            break
        end_span+=1
        
    if start_span <0:
        start_span=0
    if end_span >=context_len:
        end_span= context_len-1 
        
    new_context_tokens=[] 
    token_item=''
        
    for item in context_tokens[start_span:end_span+1]:
        if not item.startswith('Ġ'):
            token_item+=item
        else:
            new_context_tokens.append(re.sub('Ġ', '', token_item))
            token_item=item
    new_context_tokens.append(re.sub('Ġ', '', token_item))
        
    sentence = " ".join(new_context_tokens).strip()
    return sentence

class ParagraphQA:

    """
    ParagraphQA Paser to extract the answer in a paragraph from the question
    """
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method to get the singleton instance"""
        if ParagraphQA.__instance is None:
            ParagraphQA()
        return ParagraphQA.__instance

    #def __init__(self):
    def __init__(self, paragraph):
        """ Virtually private constructor. """
        if ParagraphQA.__instance is not None:
            ParagraphQA.__instance = self
            self.paragraph=paragraph
            #raise Exception("ParagraphQA is not instantiable")
        else:
            ParagraphQA.__instance = self
            self.paragraph=paragraph
        self.__initialize()

    def __initialize(self, SPACY_MODEL =constants.SPACY_MODEL):
        '''
        Initializes QA models
        :param model_name: name of the QA model
        :param SPACY_MODEL: name of the spacy model
        :return:
        '''
        config_file = pyhocon.ConfigFactory.parse_file(constants.CONFIG_FILE)
        self.config = config_file['paraqa']

        
        self.nlp = spacy.load(SPACY_MODEL, disable=['ner', 'parser', 'textcat'])
        self.predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/transformer-qa.2021-02-11.tar.gz")
        self.passage_retriever = PassageRetrieval(self.nlp)
        self.passage_retriever.fit(self.paragraph)

    
    def get_answer_allen(self, questions):
        """
        Gets the answers based for the questions based on paragraphs
        :param paragraph: list of str - list of paragraphs
        :param questions: list of str - list of questions
        :return: answers
        """
        #self.passage_retriever.fit(paragraph)
        #print("passage fitted")
        topk = self.config['topk']
        #max_answer_len = self.config['max_answer_len']
        answers = []
        refs=[]
        for i in range(len(questions)):
            #print("fetching passages")
            
            start= time.time()
            passages = self.passage_retriever.most_similar(questions[i], topk = topk)
            #print("passage fetched")
            end=time.time()
            ans=''
            ref=''
            res_instance=''
            #best_span_scores
            score=0
            start1= time.time()
            
            for psg in passages:
                psg = re.sub('hph', '-', psg)
                res= self.predictor.predict(passage=psg,question=questions[i])
                #print(psg)
                #print(res['best_span_scores'])
                #print(res['best_span_str'])
                if res['best_span_scores'] > score and res['best_span_str']!='':
                    score = res['best_span_scores']
                    ans = res['best_span_str']
                    res_instance=res
                    ref=psg
                
            
            
            #whole_para = '\n'.join(passages)
            #res= self.predictor.predict(passage=whole_para, question=questions[0])['best_span_str']
            if ans !='': 
                ans= construct_answer(res_instance['context_tokens'], res_instance['best_span'])
            end1=time.time()
            #print("whole_para: ", whole_para)
            
            #res = self.nlp_qa(context=whole_para, question=questions[i], max_answer_len = max_answer_len)
            
            
            answers.append(ans)
            refs.append(ref)
            
        return answers, refs, end-start, end1-start1

