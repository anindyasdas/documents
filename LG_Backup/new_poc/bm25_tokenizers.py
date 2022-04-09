"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""


class TextObject:
    def __init__(self, text):
        self.val = text

    @property
    def lemma_(self):
        return self.val


def white_space_tokenizer(text):
    list_obj = []
    for item in text.split(" "):
        list_obj.append(TextObject(item))
    return list_obj


# TODO: Other Tokenizer To Experiment
'''
from soylemma import Lemmatizer
from soynlp.tokenizer import LTokenizer

lemmatizer = Lemmatizer()
tokenizer = LTokenizer()

class TextObject:
    def __init__(self, text):
        self.val = text

    @property
    def lemma_(self):
        n_val = lemmatizer.lemmatize(self.val)
        if n_val:
            return n_val[0][0]
        else:
            return self.val


def ko_tokenizer(text):
    list_obj = []
    for item in tokenizer.tokenize(text):
        list_obj.append(TextObject(item))
    return list_obj
'''
