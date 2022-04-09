"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""

import torch
import spacy
import pandas as pd
from transformers import BertForQuestionAnswering
from transformers import BertTokenizer
from transformers import pipeline
from .passageretrival import PassageRetrieval
import pyhocon
from . import constants

class ParagraphQA:

    """
    ParagraphQA Paser to extract the answer in a paragraph from the question
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if ParagraphQA.__instance is None:
            ParagraphQA()
        return ParagraphQA.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if ParagraphQA.__instance is not None:
            raise Exception("ParagraphQA is not instantiable")
        else:
            ParagraphQA.__instance = self
        self.__initialize()

    def __initialize(self, model_name=constants.model_name, spacy_model=constants.SPACY_MODEL):
        '''
        Initializes QA models
        :param model_name: name of the QA model
        :param spacy_model: name of the spacy model
        :return:
        '''
        config_file = pyhocon.ConfigFactory.parse_file(constants.CONFIG_FILE)
        self.config = config_file['paraqa']

        self.model = BertForQuestionAnswering.from_pretrained(model_name)
        
        self.tokenizer = BertTokenizer.from_pretrained(model_name)

        # for GPU
        # self.nlp_qa = pipeline('question-answering', model=model, 
        # 	tokenizer = tokenizer, device=torch.cuda.current_device())

        # for CPU
        self.nlp_qa = pipeline('question-answering', model=self.model, tokenizer = self.tokenizer)
        
        self.nlp = spacy.load(spacy_model, disable=['ner', 'parser', 'textcat'])
        self.passage_retriever = PassageRetrieval(self.nlp)

    def get_answer(self, paragraph, questions):
        """
        Gets the answers based for the questions based on paragraphs
        :param paragraph: list of str - list of paragraphs
        :param questions: list of str - list of questions
        :return: answers
        """
        self.passage_retriever.fit(paragraph)
        topk = self.config['topk']
        max_answer_len = self.config['max_answer_len']
        answers = []
        for i in range(len(questions)):
            passages = self.passage_retriever.most_similar(questions[i], topk = topk)
            whole_para = '\n'.join(passages)
            res = self.nlp_qa(context=whole_para, question=questions[i], max_answer_len = max_answer_len)
            answers.append(res['answer'])
            
        return answers

