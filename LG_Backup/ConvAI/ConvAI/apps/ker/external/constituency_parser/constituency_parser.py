# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
 * Copyright(c) 2020 by LG Electronics.
 * Confidential and Proprietary All Rights Reserved.
 *-------------------------------------------------*/
@author: vishwaas@lge.com
"""
import logging

from allennlp.predictors.predictor import Predictor
import allennlp_models.structured_prediction
import pandas as pd
import time
import sys

from ...components.engine import constants as engine_constants
from . import constants as constituency_parser_constanst
from ..os_tools import uncompress_tool as tool


class ContituencyParserWrapper:
    """
    Constituency Paser to extract Noun Phrases and Verb Phrases
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if ContituencyParserWrapper.__instance is None:
            ContituencyParserWrapper()
        return ContituencyParserWrapper.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if ContituencyParserWrapper.__instance is not None:
            raise Exception("ContituencyParserWrapper is not instantiable")
        else:
            ContituencyParserWrapper.__instance = self
        # check if the model folder is present
        self.__check_model_files()
        self.predictor = Predictor.from_path(constituency_parser_constanst.MODEL)

    def __check_model_files(self):
        """
        check if the model file is present
        """
        check = tool.extract_compressed_files(constituency_parser_constanst.MODEL_PATH,
                                              constituency_parser_constanst.MODEL_NAME,
                                              constituency_parser_constanst.MODEL_NAME)
        if not check:
            logging.error("Model zipped model file does not exist ")
            sys.exit()

    def get_constituency_output(self, sentence):
        """
        Gets the complete output of the constituency parser
        sentence: Input sentence
        returns: the complete output dict of the constituency parser
        """
        sentence_pp = self.pre_process(sentence)
        return self.predictor.predict(sentence=sentence_pp)

    def get_phrases(self, sentence):
        """
        Gets Noun Phrases and Verbs
        sentence: Input sentence
        returns: dict with keys 'NP' and 'VB' for noun phrase and verbs and values having the list of those
        """
        sentence_pp = self.pre_process(sentence)
        prediction = self.get_constituency_output(sentence_pp)
        root = prediction['hierplane_tree']['root']

        np = self.__get_noun_phrases_util(root)
        vb = self.__get_verb_util(root)
        to_return = {'NP': '|'.join(np), 'VB': '|'.join(vb)}
        logging.log(engine_constants.LG_LOGGING_MODULE_OUTPUT_LVL, to_return)
        return to_return

    def __get_noun_phrases_util(self, root):
        """
        Recursively adds the lowest level noun phrases in a bottom up manner
        root: Root node of the tree
        phrases: list to append the noun phrases
        returns: list of noun phrases
        """
        phrases = []
        words = root['word']
        node_type = root['nodeType']

        if constituency_parser_constanst.CHILDREN in root:
            for child in root[constituency_parser_constanst.CHILDREN]:
                phrases.extend(self.__get_noun_phrases_util(child))

        if len(phrases) == 0 and node_type == constituency_parser_constanst.NP:
            words_pp = self.post_process(words)
            if len(words_pp) != 0:
                phrases.append(words_pp)
        return list(set(phrases))

    def __get_verb_util(self, root):
        """
        Recursively adds the verbs in a bottom up manner
        root: Root node of the tree
        phrases: list to append the verbs
        returns: list of verbs
        """
        verbs = []
        if constituency_parser_constanst.CHILDREN in root:
            for child in root[constituency_parser_constanst.CHILDREN]:
                verbs.extend(self.__get_verb_util(child))
        words = root['word']
        node_type = root['nodeType']
        if constituency_parser_constanst.VB in node_type:
            words_pp = self.post_process(words)
            if len(words_pp) != 0 and words_pp not in constituency_parser_constanst.AUX_VERBS:
                verbs.append(self.post_process(words_pp))
        return list(set(verbs))

    def get_phrases_file(self, path):
        """
        Writes the noun and verb phrases for each sentence in the file.
        path: Path of the file
        returns: None
        """
        data = pd.read_excel(path, sheet_name='ORIG')

        questions = data['Key'].values
        phrase_nps = []
        phrase_vps = []
        for question in questions:
            start = time.time()
            phrases = self.get_phrases(question)
            end = time.time()
            print((end - start) / 1000)
            phrase_np = phrases[constituency_parser_constanst.NP]
            phrase_vp = phrases[constituency_parser_constanst.VB]
            phrase_nps.append('|'.join(phrase_np))
            phrase_vps.append('|'.join(phrase_vp))

        data['Noun_Phrases'] = phrase_nps
        data['Verbs'] = phrase_vps

        data.to_excel('output.xlsx', index=False, sheet_name='Sheet1')

    def pre_process(self, text):
        """
        Preprocesses the given text
        text: str - input text
        return preprocessed text
        """
        text_pp = text.replace('/', ' or ')
        text_pp = text_pp.replace('  ', ' ')
        return text_pp

    def post_process(self, text):
        """
        Postprocesses the given text
        text: str - input text
        return postprocessed text
        """
        text = text.split(' ')
        mod_text = []
        for w in text:
            if w.lower() not in constituency_parser_constanst.stop_words:
                mod_text.append(w)
        mod_text = ' '.join(mod_text)
        return mod_text.strip()


if __name__ == '__main__':
    cons = ContituencyParserWrapper.get_instance()
    out = cons.get_phrases(
        'The amount of liquid detergent/ fabric softener in the detergent/ softener reservoir did not decrease.')
    print(out)
