"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
"""

import sklearn
import torch
import spacy
import pandas
from . import constants
from .pipeline_1 import Pipeline1
from .pipeline_2 import Pipeline2
from .pipeline_3 import Pipeline3

from ..text_similarity.similarity_factory import SimilarityFactory
from ..info_extraction.info_extraction_factory import InfoExtractionFactory
from ..classifier.classifier_engine import ClassifierEngine
from ...external.constituency_parser.constituency_parser import ContituencyParserWrapper
from ..paraqa.paraqa import ParagraphQA
from ..boolqa.boolqa import BoolQA
from ...external.srl.srl_parser import SRLWrapper
from .utils import Utils
import pandas as pd
import re
import json
import logging as logger


class InfoEngine:

    def __init__(self):
        self.siam_bert = SimilarityFactory.get_text_sim_model(SimilarityFactory.SIAMESE_BERT_MODEL, None)
        self.info_model = InfoExtractionFactory.get_info_extraction(InfoExtractionFactory.RULEBASED_MODEL, None)
        self.cons_parser = ContituencyParserWrapper.get_instance()
        self.srl_parser = SRLWrapper.get_instance()
        self.para_qa = ParagraphQA.get_instance()
        self.bool_qa = BoolQA.get_instance()

    def info_extraction_orig(self): # pragma: no cover
        """
        Computes info extraction, srl and constituency parser outputs on the key column of the data
        :return: None
        """
        for p in constants.PRODUCTS:
            for t in [constants.TROB]:
                orig = pd.read_excel(constants.INPUT_FILES[p][t], sheet_name='ORIG')
                orig = orig.applymap(str)
                info_extrs = []
                nps = []
                vbs = []
                causes = []
                temps = []
                purposes = []

                for key in orig.Key.values:
                    ie = self.info_model.extract_info_single(key, constants.PIPELINE_2, t, p, self.siam_bert)[0]
                    print(ie)
                    logger.info("Info Extraction =%s", str(ie))
                    info_extrs.append(ie)
                    # info_extrs.append(key)
                    con_output = self.cons_parser.get_phrases(key)
                    logger.info("Constituency Parser =%s", str(con_output))
                    nps.append(con_output[constants.NP])
                    vbs.append(con_output[constants.VB])
                    srl_output = self.srl_parser.get_srl_output_for_ker(key)
                    logger.info("SRL Parser =%s", str(srl_output))
                    causes.append(srl_output[constants.CAUSE])
                    temps.append(srl_output[constants.TEMP])
                    purposes.append(srl_output[constants.PURPOSE])
                orig[constants.INFO_EXTRACTION] = info_extrs
                orig[constants.NP] = nps
                orig[constants.VB] = vbs
                orig[constants.CAUSE] = causes
                orig[constants.TEMP] = temps
                orig[constants.PURPOSE] = purposes

                Utils.append_df_to_excel(constants.INPUT_FILES[p][t], orig, 'ORIG', index=False)

    def extract_answer_para(self, paragraphs, questions):
        """
        Extracts answers for the given questions in the paragrahs
        :param paragraphs: list of str - list of paragraphs
        :param questions: list of str - list of questions
        :return: answers
        """
        answers = self.para_qa.get_answer(paragraphs, questions)

        return json.dumps({
            constants.response_code: constants.STATUS_OK,
            constants.response_data:
                {
                    "answers": answers
                }
        })
        
    def extract_answer_bool(self, paragraphs, questions):
        """
        Extracts answers for the given questions in the paragrahs
        :param paragraphs: list of str - list of paragraphs
        :param questions: list of str - list of questions
        :return: answers
        """
        answers = self.bool_qa.get_answer(paragraphs, questions)

        return json.dumps({
            constants.response_code: constants.STATUS_OK,
            constants.response_data:
                {
                    "answers": answers
                }
        })

    def extract(self, text, question_type, product, pipeline=constants.PIPELINE_2, top_k=1, l1_key=None):
        """
        Runs info extraction and synonym matching on the given text
        :param text: str - input text
        :param question_type: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param product: the given product
        :param pipeline: PIPELINE_1/PIPELINE_2/PIPELINE_3
        :param top_k: top k predictions
        :param l1_key: L1 key to filter
        :return: Returns json output
        """
        pipe = None

        if pipeline == constants.PIPELINE_1:
            pipe = Pipeline1
        elif pipeline == constants.PIPELINE_2:
            pipe = Pipeline2
        elif pipeline == constants.PIPELINE_3:
            pipe = Pipeline3

        return json.dumps(pipe.get_instance(self.siam_bert, self.info_model).extract(text.lower(), question_type,
                                                                                    product, top_k, l1_key))

    def extract_srl_cons(self, cause: str):
        """
        returns constituency and SRL outputs
        :param cause: input text
        :return: dict - constituency and SRL outputs
        """
        const_output = self.cons_parser.get_phrases(cause)
        srl_output = self.srl_parser.get_srl_output_for_ker(cause)

        return json.dumps({
            constants.response_code: constants.STATUS_OK,
            constants.response_data:
                {
                    "cons_parser": {constants.NP: const_output[constants.NP].split('|'),
                                    constants.VB: const_output[constants.VB].split('|')},
                    "srl": {constants.TEMP: srl_output[constants.TEMP].split('|'),
                            constants.CAUSE: srl_output[constants.CAUSE].split('|'),
                            constants.PURPOSE: srl_output[constants.PURPOSE].split('|')}
                }
        })

    def train(self): # pragma: no cover
        """
        Trains the engine - currently only text similarity
        :return:
        """
        self.siam_bert.train_custom()

    def __read_all_questions_and_test(self, product, section, pipe, filter_by_cat, f, sheet_name): # pragma: no cover
        """
            Reads all questions for the mentioned product ,section and pipeline
            Args:
                product:str
                section:str
                pipe:str
            Returns:
                to_write:str
        """
        classifier_engine = ClassifierEngine()
        data = pd.read_excel(constants.INPUT_FILES[product][section], sheet_name=sheet_name, engine='openpyxl')
        outputs1 = []
        for q in data.Questions.values:
            if filter_by_cat:
                classifier_output = json.loads(classifier_engine.get_classifier_output(q))
                top = classifier_output["response_data"]["Type"]
            else:
                top=None
            out = json.loads(self.extract(q, section, product, pipe, top_k=1, l1_key=top))[
                constants.response_data]
            # print(out)
            if pipe != constants.PIPELINE_2:
                outputs1.append(out['similarity_key'][0]['key'])
            else:
                outputs1.append(out['prob_value_specific'])
            print(q)
        data['PIPELINE_1'] = outputs1
        labels1 = data[constants.EXPECTED_QUESTION]
        to_write = pipe + '_' + product + '_' + section + '_' + ': ' + str(self.__get_accuracy(labels1, outputs1))
        print(to_write)
        f.write(to_write)
        f.write('\n')
        logger.info("RUN ON FILE =%s", str(constants.INPUT_FILES[product][section]))
        Utils.append_df_to_excel(constants.INPUT_FILES[product][section], data, sheet_name, index=False)
        return to_write

    def extract_on_file(self, filter_by_cat=True): # pragma: no cover
        """
        Runs info extraction on all files
        :return: None
        """
        with open(constants.logs, 'w') as f:
            for pipe in [constants.PIPELINE_1]:
                for p in [constants.WASHING_MACHINE,constants.REFRIGERATOR]:
                    print("--- extract_on_file for product=", p)
                    for t in [constants.OPERATION]:
                        if t != constants.TROB and pipe == constants.PIPELINE_2:
                            continue
                        print(pipe + '_' + p + '_' + t)
                        # read questions and test,return the output
                        self.__read_all_questions_and_test(p, t, pipe, filter_by_cat, f, sheet_name='L1_L2_L3')

    def test_on_file(self, filter_by_cat=True): # pragma: no cover
        """
        Runs info extraction on all files
        :return: None
        """
        to_writes = []
        with open(constants.logs, 'w') as f:
            for pipe in [constants.PIPELINE_1]:
                for p in [constants.WASHING_MACHINE]:
                    for t in [constants.OPERATION]:
                        if t != constants.TROB and pipe == constants.PIPELINE_2:
                            continue
                        print(pipe + '_' + p + '_' + t)
                        # function call to test the file
                        to_write = self.__read_all_questions_and_test(p, t, pipe, filter_by_cat, f, sheet_name='L1_L2_L3_test')
                        to_writes.append(to_write)
        print(to_writes)

    def __read_file_and_evaluate(self, section, pipe, filter_by_cat, file): # pragma: no cover
        """
            Reads all questions for the mentioned product ,section and pipeline
            ,tests and writes back the result to the same file
            Args:
                section:str
                pipe:str
                file:str
            Returns:
                to_write:str
        """
        product = ""
        col = pipe
        data = pd.read_excel(file, sheet_name='test', engine='openpyxl')
        outputs1 = []
        classifier_engine = ClassifierEngine()
        for q, product in data[['User Question', 'product']].values:
            if filter_by_cat:
                classifier_output = json.loads(classifier_engine.get_classifier_output(q))
                top = classifier_output["response_data"]["Type"]
            else:
                top=None

            out = json.loads(self.extract(q, section, product, pipe, top_k=1, l1_key=top))[
                constants.response_data]
            if pipe != constants.PIPELINE_2:
                outputs1.append(out['similarity_key'][0]['key'])
            else:
                outputs1.append(out['prob_value_specific'])
            print(outputs1[-1])
        data[col] = outputs1
        labels1 = data['Reason/Solution']
        to_write = pipe + '_' + product + '_' + section + '_' + ': ' + str(
            self.__get_accuracy(labels1, outputs1))

        Utils.append_df_to_excel(file, data, 'test', index=False)
        return to_write

    def test_on_test_file(self, filter_by_cat=False): # pragma: no cover
        """
        Tests on the created test data
        :return: None
        """
        to_writes = []
        with open(constants.logs, 'w') as f:
            for pipe in [constants.PIPELINE_1]:
                for t in [constants.SPEC, constants.TROB]:

                    if t == constants.TROB:
                        file = constants.TROB_TEST_DATA
                    else:
                        file = constants.SPEC_TEST_DATA

                    if pipe == constants.PIPELINE_2 and t == constants.SPEC:
                        continue
                    # read questions and test,return the output
                    to_write = self.__read_file_and_evaluate(t, pipe, filter_by_cat, file)
                    to_writes.append(to_write)

        print(to_writes)

    def __get_accuracy(self, labels, pred): # pragma: no cover
        """
        Gets the accuracy of prediction
        :param labels: actual
        :param pred: prediction
        :return: float
        """
        acc = 0
        for q1, q2 in zip(labels, pred):
            q1 = self.__preprocess(q1)
            q2 = self.__preprocess(q2)
            if q1 == q2:
                acc += 1
        return acc / len(labels)

    def __preprocess(self, text):
        """
        Preprocess given text
        :param text: Given text
        :return: proprocessed text
        """
        text = text.lower()
        return ' '.join(re.split("[^\\w_]+", text))
