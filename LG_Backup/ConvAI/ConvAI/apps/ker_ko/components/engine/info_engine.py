"""
/*-------------------------------------------------
* Copyright(c) 2020-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""

from . import constants
from .pipeline_1 import Pipeline1
from .pipeline_2 import Pipeline2
from .pipeline_3 import Pipeline3
from ..classifier.classifier_engine import ClassifierEngine
from ..text_similarity.similarity_factory import SimilarityFactory
from ..info_extraction.info_extraction_factory import InfoExtractionFactory

from .utils import Utils
import pandas as pd
import re
import json
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class InfoEngine:

    def __init__(self):
        self.siam_bert = SimilarityFactory.get_text_sim_model(SimilarityFactory.SIAMESE_BERT_MODEL, None)
        self.info_model = InfoExtractionFactory.get_info_extraction(InfoExtractionFactory.RULEBASED_MODEL, None)

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
                    logger.debug("Info Extraction =%s", str(ie))
                    info_extrs.append(ie)
                    # info_extrs.append(key)
                    con_output = self.cons_parser.get_phrases(key)
                    logger.debug("Constituency Parser =%s", str(con_output))
                    nps.append(con_output[constants.NP])
                    vbs.append(con_output[constants.VB])
                    srl_output = self.srl_parser.get_srl_output_for_ker(key)
                    logger.debug("SRL Parser =%s", str(srl_output))
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

    def extract_answer_para(self, paragraphs, questions): # pragma: no cover
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

    def extract_answer_bool(self, paragraphs, questions): # pragma: no cover
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

    def extract(self, text, question_type, product, pipeline=constants.PIPELINE_2, top_k=1, l1_key=None, is_train=False):
        """
        Runs info extraction and synonym matching on the given text
        :param text: str - input text
        :param question_type: SPECIFICATION/TROUBLESHOOTING/FAQ
        :param product: the given product
        :param pipeline: PIPELINE_1/PIPELINE_2/PIPELINE_3
        :param top_k: top k predictions
        :param l1_key: L1 key to filter
        :param is_train: boolean true -> training False-> inference
        :return: Returns json output
        """
        pipe = None
        product_type = product[0]
        sub_product_type = product[1]

        if pipeline == constants.PIPELINE_1:
            pipe = Pipeline1
        elif pipeline == constants.PIPELINE_2:
            pipe = Pipeline2
        elif pipeline == constants.PIPELINE_3:
            pipe = Pipeline3


        return json.dumps(pipe.get_instance(self.siam_bert, self.info_model).extract(text.lower(), question_type,
                                                                                     product_type, sub_product_type,top_k, l1_key, is_train))

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

    def train(self):# pragma: no cover
        """
        Trains the engine - currently only text similarity
        :return:
        """
        self.siam_bert.train_custom()

    def __read_all_questions_and_test(self, product, sub_product_type, section, pipe, filter_by_cat, f, sheet_name):# pragma: no cover
        """
            Reads all questions for the mentioned product ,section and pipeline
            Args:
                product:str
                section:str
                pipe:str
            Returns:
                to_write:str
        """
        logger.info("---question_type=%s product=%s subproduct_type=%s",section, product, sub_product_type)
        if product == sub_product_type:
            input_file = constants.INPUT_FILES[product][section]
        elif product != sub_product_type:
            input_file = constants.INPUT_FILES[product][sub_product_type][section]
        logger.debug("input_file=%s", input_file)
        logger.debug("filter_by_cat=%d",filter_by_cat)
        classifier_engine = ClassifierEngine()
        data = pd.read_excel(input_file, sheet_name=sheet_name, engine='openpyxl')
        outputs1 = []
        all_predictions = []
        for q in data.Questions.values:
            if filter_by_cat:
                classifier_output = json.loads(classifier_engine.get_classifier_output(q))
                top = classifier_output["response_data"]["Type"]
            else:
                top=None
            product_type = product,sub_product_type
            out = json.loads(self.extract(q, section, product_type, pipe, top_k=3, l1_key=top,is_train=True))[
                constants.response_data]

            if pipe != constants.PIPELINE_2:
                if len(out['similarity_key']) == 0:
                    outputs1.append("Empty")
                else:
                    outputs1.append(out['similarity_key'][0]['key'][0])
                    all_predictions.append(out)
            else:
                outputs1.append(out['prob_value_specific'])

        data['PIPELINE_1'] = outputs1
        data['ALL_RESULTS'] = all_predictions
        labels1 = data[constants.EXPECTED_QUESTION]
        to_write = pipe + '_' + product + '_' + sub_product_type + '_' + section + '_' + ': ' + str(self.__get_accuracy(labels1, outputs1))
        f.write(to_write)
        f.write('\n')
        logger.info("RUN ON FILE =%s", str(input_file))
        Utils.append_df_to_excel(input_file, data, sheet_name, index=False)
        return to_write

    def extract_on_file(self, filter_by_cat=True):# pragma: no cover
        """
        Runs info extraction on all files
        :return: None
        """
        with open(constants.logs, 'w') as f:
            for pipe in [constants.PIPELINE_1]:
                # product types
                for p in [constants.REFRIGERATOR]:
                    logger.debug("--- extract_on_file for product=%s", p)
                    for t in [constants.TROB]:
                        if t != constants.TROB and pipe == constants.PIPELINE_2:
                            continue
                        logger.debug("%s_%s_%s",pipe, p ,t)
                        # read questions and test,return the output
                        sub_product_type = p
                        self.__read_all_questions_and_test(p, sub_product_type,t, pipe, False, f, sheet_name='L1_L2_L3')

    def extract_on_file_textsim(self, filter_by_cat=True):  # pragma: no cover
        """
        Runs info extraction on all files
        :return: None
        """
        product = constants.REFRIGERATOR
        sub_prod_type = constants.RefrigeratorSubProductTypes.LARGE
        pipe = constants.PIPELINE_1
        with open(constants.logs, 'w') as f:
            logger.debug("--- extract_on_file for product=%s", product)
            for t in [constants.TROB]:
                if t != constants.TROB and pipe == constants.PIPELINE_2:
                    continue
                logger.debug("%s_%s_%s",pipe ,product,t)
                # read questions and test,return the output
                self.__read_all_questions_and_test(product, sub_prod_type, t, pipe, False, f, sheet_name='L1_L2_L3')

    def test_on_file(self, filter_by_cat=True):# pragma: no cover
        """
        Runs info extraction on all files
        :return: None
        """
        to_writes = []
        with open(constants.logs, 'w') as f:
            for pipe in [constants.PIPELINE_1]:
                for p in constants.PRODUCTS[1:2]:
                    for t in [constants.TROB]:
                        if t != constants.TROB and pipe == constants.PIPELINE_2:
                            continue
                        logger.debug("%s_%s_%s", pipe, p, t)
                        # function call to test the file
                        sub_product_type = p
                        to_write = self.__read_all_questions_and_test(p, sub_product_type, t, pipe, filter_by_cat, f,
                                                                      sheet_name='L1_L2_L3_test')
                        to_writes.append(to_write)
        logger.info("%s",to_writes)

    def __read_file_and_evaluate(self, section, pipe, filter_by_cat, file):# pragma: no cover
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
                top = None

            out = json.loads(self.extract(q, section, product, pipe, top_k=1, l1_key=top))[
                constants.response_data]
            if pipe != constants.PIPELINE_2:
                outputs1.append(out['similarity_key'][0]['key'])
            else:
                outputs1.append(out['prob_value_specific'])
            logger.debug("Output=%s",outputs1[-1])
        data[col] = outputs1
        labels1 = data['Reason/Solution']
        to_write = pipe + '_' + product + '_' + section + '_' + ': ' + str(
            self.__get_accuracy(labels1, outputs1))

        Utils.append_df_to_excel(file, data, 'test', index=False)
        return to_write

    def test_on_test_file(self, filter_by_cat=False):# pragma: no cover
        """
        Tests on the created test data
        :return: None
        """
        to_writes = []
        with open(constants.logs, 'w') as f:
            for pipe in [constants.PIPELINE_1]:
                #for t in [constants.SPEC, constants.TROB]:
                for t in [constants.TROB]:
                    if t == constants.TROB:
                        file = constants.TROB_TEST_DATA
                    else:
                        file = constants.SPEC_TEST_DATA

                    if pipe == constants.PIPELINE_2 and t == constants.SPEC:
                        continue
                    # read questions and test,return the output
                    to_write = self.__read_file_and_evaluate(t, pipe, filter_by_cat, file)
                    to_writes.append(to_write)

        logger.info(to_writes)

    def __get_accuracy(self, labels, pred):# pragma: no cover
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