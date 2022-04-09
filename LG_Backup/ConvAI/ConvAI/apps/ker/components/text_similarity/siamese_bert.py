"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas@lge.com
"""

import scipy
import pandas as pd
from . import constants

from torch.utils.data import DataLoader
import math
import re
from sentence_transformers import SentencesDataset, SentenceTransformer
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from sentence_transformers.readers import *
from datetime import datetime
import sys
import numpy as np
from sentence_transformers import models, losses
from .base_similarity_model import BaseSimilarityModel
from . import base_question_extraction

from . import utils
import heapq
from collections import defaultdict
from ..engine.utils import Utils as engine_utils
import logging as logger


class SiameseBERT(BaseSimilarityModel):

    def __init__(self, config):
        super().__init__(config, 'siamese_bert')

        self.model = SentenceTransformer(constants.SIAM_BERT_FINETUNED)

        # self.pool = self.model.start_multi_process_pool(encode_batch_size=64) used for multi processing
        self.prod_type_emb = {}

    def compute_embeddings(self, question_list):
        """
        Generates embeddings with and without stop word removal and combined them for the question list
        :param question_list: embeddings
        :return: stacked embeddings
        """
        sentence_embeddings = self.model.encode(question_list)
        question_list_sw = self.__get_question_list_sw(question_list)
        sentence_embeddings_sw = self.model.encode(question_list_sw)
        return np.stack([sentence_embeddings, sentence_embeddings_sw], axis=0)

    def compute_embeddings_single(self, question_list):
        """
        Gets the sentence embeddings of a given question list
        :param question_list: list of str - given question list
        :return:embeddins
        """
        sentence_embeddings = self.model.encode(question_list)
        # sentence_embeddings = self.model.encode_multi_process(question_list, self.pool) used for multi processing
        return sentence_embeddings

    def compute_embeddings_single_by_word(self, words, info_extr):
        """
        Gets the embeddings based on word of a given question list
        :param question_list: list of str - given question list
        :return:embeddings
        """
        weighted_emb = 0
        weight_sum = 0
        for word in words:
            emb = self.compute_embeddings_single([word])[0]
            weight = info_extr.get_idf_score(word)
            weighted_emb += emb * weight
            weight_sum += weight
        if weight_sum != 0:
            return weighted_emb / weight_sum
        else:
            return weighted_emb

    def __get_question_list_sw(self, question_list):
        """
        get the list of questions with stop words
        :param question_list:list of questions with stop words
        :return list of questions
        """
        return [self.__remove_stop_words(q) for q in question_list]

    def train(self):
        """
        Trains the model on NLP data
        :return: None
        """
        # Use BERT for mapping tokens to embeddings

        # You can specify any huggingface/transformers pre-trained model here, for example, bert-base-uncased, roberta-base, xlm-roberta-base
        model_name = sys.argv[1] if len(sys.argv) > 1 else 'bert-base-uncased'

        # Read the dataset
        batch_size = 16
        nli_reader = NLIDataReader(constants.SIAM_BERT_TRAIN_PATH)

        sts_reader = STSDataReader(constants.SIAM_BERT_BENCHMARK_PATH, score_col_idx=4, s1_col_idx=5, s2_col_idx=6)

        train_num_labels = nli_reader.get_num_labels()
        model_save_path = constants.OUTPUT_DIR + '/training_nli_' + model_name.replace("/",
                                                                                       "-") + '-' + datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S")

        word_embedding_model = models.Transformer('bert-base-uncased')

        # Apply mean pooling to get one fixed sized sentence vector
        pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension(),
                                       pooling_mode_mean_tokens=True,
                                       pooling_mode_cls_token=False,
                                       pooling_mode_max_tokens=False)

        model = SentenceTransformer(modules=[word_embedding_model, pooling_model])

        train_data = SentencesDataset(nli_reader.get_examples('train.gz'), model=model)
        train_dataloader = DataLoader(train_data, shuffle=True, batch_size=batch_size)

        train_loss = losses.SoftmaxLoss(model=model,
                                        sentence_embedding_dimension=model.get_sentence_embedding_dimension(),
                                        num_labels=train_num_labels)

        dev_data = SentencesDataset(examples=sts_reader.get_examples('sts-dev.csv'), model=model)
        dev_dataloader = DataLoader(dev_data, shuffle=False, batch_size=batch_size)
        evaluator = EmbeddingSimilarityEvaluator(dev_dataloader)

        num_epochs = 1

        warmup_steps = math.ceil(len(train_dataloader) * num_epochs / batch_size * 0.1)  # 10% of train data for warm-up

        # Train the model
        model.fit(train_objectives=[(train_dataloader, train_loss)],
                  evaluator=evaluator,
                  epochs=num_epochs,
                  evaluation_steps=1000,
                  warmup_steps=warmup_steps,
                  output_path=model_save_path
                  )

    def train_custom(self):
        """
        Trains the model on custom data
        :return: None
        """

        trob_data = self.get_custom_sim_data(constants.CUSTOM_TROB_TRAIN_DATA, constants.CUSTOM_TROB_SIM_TRAIN_DATA)
        spec_data = self.get_custom_sim_data(constants.CUSTOM_SPEC_TRAIN_DATA, constants.CUSTOM_SPEC_SIM_TRAIN_DATA)
        train_data = pd.concat([trob_data, spec_data], axis=0)
        input_examples = []
        model = SentenceTransformer('bert-base-nli-mean-tokens')
        for i in range(train_data.shape[0]):
            ie = InputExample(guid=str(i), texts=[train_data.iloc[i, 0], train_data.iloc[i, 1]],
                              label=train_data.iloc[i, 2])
            input_examples.append(ie)
        train_dataset = SentencesDataset(input_examples, model)
        train_dataloader = DataLoader(train_dataset, shuffle=True, batch_size=16)
        train_loss = losses.CosineSimilarityLoss(model=model)
        train_batch_size = 16
        num_epochs = 1
        warmup_steps = math.ceil(len(train_data) * num_epochs / train_batch_size * 0.1)  # 10% of train data for warm-up
        model_save_path = constants.OUTPUT_DIR + '/training_nli_' + 'custom_siam_model' + '-' + datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S")
        evaluator = EmbeddingSimilarityEvaluator(train_dataloader)

        model.fit(train_objectives=[(train_dataloader, train_loss)],
                  evaluator=evaluator,
                  epochs=num_epochs,
                  evaluation_steps=1000,
                  warmup_steps=warmup_steps,
                  output_path=model_save_path)

    def get_custom_sim_data(self, input_file, output_file):
        """
        Gets the data in the required form for text similarity
        :param input_file: raw input data
        :param output_file: input data formatted for text similarity
        :return:excel file required for text similarity
        """
        data = pd.read_excel(input_file)
        train_data = {'question_1': [], 'question_2': [], 'label': []}

        for k1, v1 in data.groupby(['product']):
            for k2, v2 in v1.groupby(['Reason/Solution']):
                question_1, question_2 = self.get_pos_pairs(v2)
                train_data['question_1'].extend(question_1)
                train_data['question_2'].extend(question_2)
                train_data['label'].extend([1.0] * len(question_1))
                neg_ques = self.get_neg_pairs(v1, k2, len(question_1))
                train_data['question_1'].extend(neg_ques)
                train_data['question_2'].extend(question_1)
                train_data['label'].extend([0.0] * len(question_1))
                if len(train_data['question_1']) < len(train_data['question_2']):
                    train_data['question_2'] = train_data['question_2'][: len(train_data['question_1'])]
                    train_data['label'] = train_data['label'][: len(train_data['question_1'])]
                elif len(train_data['question_2']) < len(train_data['question_1']):
                    train_data['question_1'] = train_data['question_1'][: len(train_data['question_2'])]
                    train_data['label'] = train_data['label'][: len(train_data['question_2'])]

        sim_data = pd.DataFrame(train_data)
        sim_data.to_excel(output_file, sheet_name='Sheet1', index=False)
        return sim_data

    def get_pos_pairs(self, val):
        """
        Gets positive pairs from question list
        :param val: grouped data on key
        :return: positive key
        """
        questions = val['User Question'].values
        question_1 = []
        question_2 = []

        for i in range(val.shape[0]):
            for j in range(i + 1, val.shape[0]):
                question_1.append(questions[i])
                question_2.append(questions[j])
        return question_1, question_2

    def get_neg_pairs(self, data, key, c):
        """
        Gets negative pairs from question list
        :param data: grouped data on key
        :param key: grouped data on key
        :param c: cut off on negative samples
        :return: questions for negative samples
        """
        filtered = data.loc[data['Reason/Solution'] != key]
        questions = filtered['User Question'].values
        questions = np.random.permutation(questions)
        return questions[: c]

    def train_continue(self):
        """
        Method to continue training on other data
        :return: None
        """
        model_name = 'bert-base-nli-mean-tokens'
        train_batch_size = 16
        num_epochs = 4
        model_save_path = constants.OUTPUT_DIR + '/training_nli_' + model_name + '-' + datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S")
        sts_reader = STSBenchmarkDataReader(constants.SIAM_BERT_BENCHMARK_PATH, normalize_scores=True)
        model = SentenceTransformer(model_name)

        # Convert the dataset to a DataLoader ready for training
        train_data = SentencesDataset(sts_reader.get_examples('sts-train.csv'), model)
        train_dataloader = DataLoader(train_data, shuffle=True, batch_size=train_batch_size)
        train_loss = losses.CosineSimilarityLoss(model=model)

        dev_data = SentencesDataset(examples=sts_reader.get_examples('sts-dev.csv'), model=model)
        dev_dataloader = DataLoader(dev_data, shuffle=False, batch_size=train_batch_size)
        evaluator = EmbeddingSimilarityEvaluator(dev_dataloader)

        warmup_steps = math.ceil(len(train_data) * num_epochs / train_batch_size * 0.1)  # 10% of train data for warm-up

        model.fit(train_objectives=[(train_dataloader, train_loss)],
                  evaluator=evaluator,
                  epochs=num_epochs,
                  evaluation_steps=1000,
                  warmup_steps=warmup_steps,
                  output_path=model_save_path)

    def test(self, test_data=constants.SIAM_BERT_DATA_STS):
        """
        Tests the model on STS data
        :return: None
        """
        evaluator =""
        model_name = constants.SIAM_BERT_MODEL_PATH
        model = SentenceTransformer(model_name)
        if test_data == constants.SIAM_BERT_DATA_STS:
            sts_reader = STSDataReader(constants.SIAM_BERT_BENCHMARK_PATH, score_col_idx=4, s1_col_idx=5, s2_col_idx=6)
            test_data = SentencesDataset(examples=sts_reader.get_examples("sts-test.csv"), model=model)
            test_dataloader = DataLoader(test_data, shuffle=False, batch_size=2)
            evaluator = EmbeddingSimilarityEvaluator(test_dataloader)
        elif constants.SIAM_BERT_DATA_MRPC:
            sts_reader = STSDataReader(constants.SIAM_BERT_BENCHMARK_PATH, max_score=1, delimiter='|', score_col_idx=0,
                                       s1_col_idx=2, s2_col_idx=3)
            test_data = SentencesDataset(examples=sts_reader.get_examples("dev.csv"), model=model)
            test_dataloader = DataLoader(test_data, shuffle=False, batch_size=2)
            evaluator = BinaryEmbeddingSimilarityEvaluator(test_dataloader)

        score = model.evaluate(evaluator) * 100
        print('score', score)

    def __get_info_extr_emb(self, question_type, product):
        """
        Gets info extraction and embedding based on question type
        :param question_type: SPEC or TROB
        :param product: product type
        :return: Info extraction object and embedding
        """
        if question_type == constants.SPEC:
            config = self.config_spec
        else:
            config = self.config_trob
        info_extr = InfoExtraction_RB(config)
        json_data = base_question_extraction.generate_question_list_json(info_extr, self, question_type, product)
        question_dict = defaultdict(list)

        for k, v in json_data.items():
            embeddings = self.compute_embeddings_single(v)
            question_dict[k] = embeddings
        return info_extr, question_dict, json_data

    def model_evaluate_single(self, test_question, question_list=None, question_type=constants.SPEC, top_k=1,
                              product=constants.WASHING_MACHINE):
        """
        Evaluates the model on a single test question
        :param test_question: str- question
        :param question_list: list of str - new question list, if None takes the default question list
        :param question_type: SPEC or TROB
        :param top_k: int
        :param product: str - WASHING_MACHINE or REFRIGERATOR
        :return: str - most similar question
        """

        if question_list is None:
            key = (product, question_type)
            if key in self.prod_type_emb:
                info_extr, question_dict, json_data = self.prod_type_emb[key]
            else:
                info_extr, question_dict, json_data = self.__get_info_extr_emb(question_type, product)
                self.prod_type_emb[key] = (info_extr, question_dict, json_data)
            test_question, t = info_extr.extract_info_single(test_question, question_type, product, self)
            if question_type == constants.TROB:
                ec_base_ques = self.__get_base_ques(test_question, json_data)
                if ec_base_ques is not None:
                    return [ec_base_ques] * top_k
        else:
            question_dict = {}
            for q in question_list:
                embedding = self.compute_embeddings_single([q])[0]
                question_dict[q] = [embedding]
        question_score = []
        queries = [test_question]
        query_embeddings = self.model.encode(queries)
        for k, v in question_dict.items():
            arr1 = self.model_evaluate_single_util(query_embeddings, v)
            question_score.append((k, np.max(arr1)))

        if top_k == 1:
            top_question = max(question_score, key=lambda x: x[1])
            return [top_question[0]]

        top_k_questions = heapq.nlargest(top_k, question_score, key=lambda x: x[1])
        return [q[0] for q in top_k_questions]

    def __get_base_ques(self, test_question, question_dict):
        """
        Gets the base question if the extracted question from info extraction is directly available in the json.
        This avoids text similarity module
        :param test_question: str - info extracted test question
        :param question_dict: json dictionary
        :return:base question
        """
        for k, v in question_dict.items():
            for v1 in v:
                if v1 == test_question:
                    return k

        return None

    def model_evaluate_single_util(self, query_embeddings, sentence_embeddings):
        """
        Utility to get the most similar question
        :param test_question: str- question
        :param sentence_embeddings: embeddings for the question list
        :return: str - most similar question
        """
        for query_embedding in query_embeddings:
            distances = scipy.spatial.distance.cdist([query_embedding], sentence_embeddings, "cosine")[0]

            results = zip(range(len(distances)), distances)
            # if scores:
            score_arr = []
            for idx, distance in results:
                score_arr.append(1 - distance)
            return score_arr

    def __remove_stop_words(self, sent):
        """
        Removes stop words and alpha numeric characters
        :param sent: str - sentence
        :return: stop words removes sentence
        """
        sent = sent.lower()
        sent = re.sub(r"[^A-Za-z0-9^,!.\/'+-=?]", " ", sent)

        sent = re.sub(r"\s{2,}", " ", sent)

        text = word_tokenize(sent)
        text_without_stop = []
        for w in text:
            if w not in stop_words:
                text_without_stop.append(w)

        return ' '.join(text_without_stop)

    def model_evaluate_bulk(self, test_question_list, question_list=None, question_type=constants.SPEC, top_k=1,
                            product=constants.WASHING_MACHINE):
        """
        Evaluates the model on a a bulk of test question
        :param top_k: int
        :param test_question_list: list of str- question
        :param question_list: list of str - new question list, if None takes the default question list
        :param question_type: SPEC or TROB
        :param product: str - WASHING_MACHINE or REFRIGERATOR
        :return: str - most similar question
        """
        predicted_question_list = []
        for i, test_question in enumerate(test_question_list):
            pred_questions = self.model_evaluate_single(test_question, question_list, question_type=question_type,
                                                        top_k=top_k, product=product)

            predicted_question_list.append(pred_questions)
            print(i)
        return predicted_question_list

    def model_evaluate_file(self, question_type=constants.SPEC, top_k=1, product=constants.WASHING_MACHINE):
        """
        Evaluate the model on a given file
        :param question_type: SPEC or TROB
        :param product: str - WASHING_MACHINE or REFRIGERATOR
        :return: None
        """
        inputfile = constants.INPUT_FILES[product][question_type]

        data = pd.read_excel(inputfile, sheet_name=constants.L1_L2_L3)
        predicted_question_list = self.model_evaluate_bulk(data.Questions.values, question_type=question_type,
                                                           top_k=top_k, product=product)
        predicted_question_list = np.array(predicted_question_list)
        data = pd.read_excel(inputfile, sheet_name=constants.L1_L2_L3)
        for i in range(top_k):
            data['top_{}'.format(i)] = predicted_question_list[:, i]
        self.__get_accuracy(data, top_k)

        utils.append_df_to_excel(inputfile, data, constants.L1_L2_L3, index=False)

    def __get_accuracy(self, data, top_k):
        """
        Gets the accuracy of the prediction
        :param data: dataframe
        :param top_k: int
        :return: None
        """
        accuracy = []
        for i in range(data.shape[0]):
            row_acc = False
            for j in range(top_k):
                row_acc = row_acc or (data['top_{}'.format(j)][i] == data[constants.EXPECTED_QUESTION][i])
            accuracy.append(int(row_acc))

        print('Accuracy: {}'.format(np.mean(accuracy)))
        data['accuracy'] = accuracy


if __name__ == '__main__':
    siam_bert = SiameseBERT(None)
    siam_bert.model_evaluate_file()
