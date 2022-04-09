"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""

import torch
import numpy as np
from transformers import BertForSequenceClassification, BertTokenizer
import os
import json

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = torch.device("cpu")

model_path = CURRENT_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..',
                 'dataset')) + '/models/ques_classifier/model_save'


class QuestionClassification:
    """
    ParagraphQA Paser to extract the answer in a paragraph from the question
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if QuestionClassification.__instance is None:
            QuestionClassification()
        return QuestionClassification.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if QuestionClassification.__instance is not None:
            raise Exception("QuestionClassification is not instantiable")
        else:
            QuestionClassification.__instance = self
        self.__initialize()

    def __initialize(self, model_class=BertForSequenceClassification, tokenizer_class=BertTokenizer):
        """
        Initializes the model
        :param model_class: transformer type
        :param tokenizer_class: transformer tokenizer
        """
        # load model and tokenizer
        self.model = model_class.from_pretrained(model_path)
        self.tokenizer = tokenizer_class.from_pretrained(model_path)

        # Copy the model to the GPU.
        self.model.to(device)

    def predict(self, questions):
        """
        Predicts the class for list of questions
        :param questions: list of str
        """
        results = []
        for question in questions:
            encoded_dict = self.tokenizer.encode_plus(
                question,  # Sentence to encode.
                add_special_tokens=True,  # Add '[CLS]' and '[SEP]'
                max_length=64,  # Pad & truncate all sentences.
                pad_to_max_length=True,
                return_attention_mask=True,  # Construct attn. masks.
                return_tensors='pt',  # Return pytorch tensors.
            )
            input_ids = encoded_dict['input_ids']
            attention_mask = encoded_dict['attention_mask']
            self.model.eval()
            with torch.no_grad():
                preds = self.model(input_ids.to(device), token_type_ids=None,
                                   attention_mask=attention_mask.to(device))
            logits = preds[0].detach().cpu().numpy()[0]
            result = np.argmax(logits)
            results.append(result)
        return results


if __name__ == '__main__':
    # ------------------------- how to do inference ----------------------------

    # Saved model path

    # Object creation
    clf = QuestionClassification.get_instance()

    # Question to be classified
    ques = "What is the capital of India?"

    '''
    0 : factoid
    1 : Description
    2 : List
    3 : bool
    '''

    # Predict the class
    op = clf.predict(ques)
    print(op)

    if op == 0:
        print("Factoid Question")
    elif op == 1:
        print("Description/Non-factoid question")
    elif op == 2:
        print("List type question")
    else:
        print("Bool/Yes_No question")
