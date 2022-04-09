"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""

import torch
import spacy
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
import json
from . import constants
from .passageretrival import PassageRetrieval
import pyhocon

# update if you want to use for GPU
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

device = torch.device("cpu")

class BoolQA:
    """
    BoolQA Paser to extract the answer in a paragraph from the question
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if BoolQA.__instance is None:
            BoolQA()
        return BoolQA.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if BoolQA.__instance is not None:
            raise Exception("BoolQA is not instantiable")
        else:
            BoolQA.__instance = self
        self.__initialize()

    def __initialize(self, model_class=AutoModelForSequenceClassification, tokenizer_class=AutoTokenizer):
        """
        Initializes boolqa models and tokenizer
        :param model_class: classification base model
        :param tokenizer_class: type of tokenizer
        :return: None
        """
        # load model and tokenizer
        self.model = model_class.from_pretrained(constants.model_path)
        self.tokenizer = tokenizer_class.from_pretrained(constants.model_path)

        # Copy the model to the GPU.
        self.model.to(device)
        self.nlp = spacy.load(constants.SPACY_MODEL, disable=['ner', 'parser', 'textcat'])
        self.passage_retriever = PassageRetrieval(self.nlp)
        config_file = pyhocon.ConfigFactory.parse_file(constants.CONFIG_FILE)
        self.config = config_file['boolqa']

    def __predict(self, conetxt, question):
        """
        Predicts for 1 context and 1 question
        :param conetxt:  str - paragraph
        :param question: str - question
        :return: yes or no
        """
        encoded_dict = self.tokenizer.encode_plus(
            question,
            conetxt,
            max_length=256,
            pad_to_max_length=True,
            truncation_strategy="longest_first",
            return_tensors='pt')

        input_ids = encoded_dict['input_ids']
        attention_mask = encoded_dict['attention_mask']
        self.model.eval()
        with torch.no_grad():
            preds = self.model(input_ids.to(device), token_type_ids=None,
                               attention_mask=attention_mask.to(device))
        logits = preds[0].detach().cpu().numpy()[0]
        ans = np.argmax(logits)

        if ans == 0:
            return constants.NO
        else:
            return constants.YES

    def get_answer(self, paragraph, questions):
        """
        Gets the answers based for the questions based on paragraphs
        :param paragraph: list of str - list of paragraphs
        :param questions: list of str - list of questions
        :return: answers
        """
        self.passage_retriever.fit(paragraph)
        topk = self.config['topk']
        answers = []
        for i in range(len(questions)):
            passages = self.passage_retriever.most_similar(questions[i], topk=topk)
            whole_para = '\n'.join(passages)
            ans = self.__predict(whole_para, questions[i])
            answers.append(ans)

        return answers


if __name__ == '__main__':

    # ----------------------- how to do inference --------------------------------------

    # question
    q = "does ethanol take more energy make that produces"

    # context
    p = "All biomass goes through at least some of these steps: it \
        needs to be grown, collected, dried, fermented, distilled, \
        and burned. All of these steps require resources and an infrastructure. \
        The total amount of energy input into the process compared to the energy \
        released by burning the resulting ethanol fuel is known as the energy balance \
        (or ``energy returned on energy invested''). Figures compiled in a 2007 report \
        by National Geographic Magazine point to modest results for corn ethanol produced \
        in the US: one unit of fossil-fuel energy is required to create 1.3 energy units \
        from the resulting ethanol. The energy balance for sugarcane ethanol produced in \
        Brazil is more favorable, with one unit of fossil-fuel energy required to create \
        8 from the ethanol. Energy balance estimates are not easily produced, thus numerous \
        such reports have been generated that are contradictory. For instance, a separate survey \
        reports that production of ethanol from sugarcane, which requires a tropical climate to grow \
        productively, returns from 8 to 9 units of energy for each unit expended, as compared to corn, \
        which only returns about 1.34 units of fuel energy for each unit of energy expended. \
        A 2006 University of California Berkeley study, after analyzing six separate studies, \
        concluded that producing ethanol from corn uses much less petroleum than producing gasoline."

    # saved model path
    model_path = 'model_save'

    # Object creation
    clf = BoolQA.get_instance()

    # predicting the ans
    op = clf.get_answer([p], [q])

    # Print the output
    # 0 : No/False
    # 1 : Yes/True
    print(op)
    if op[0] == 0:
        print("No")
    else:
        print("Yes")
