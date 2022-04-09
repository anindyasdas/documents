"""
-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
-------------------------------------------------
@Author:anusha.kamath@lge.com
"""
import tensorflow_hub as hub
import tensorflow as tf
from . import tokenization, constants


class BertEM:
    """
    Class to load BERT model from Tensorflow hub and APIs to give embeddings
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if BertEM.__instance is None:
            BertEM()
        return BertEM.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if BertEM.__instance is not None:
            raise Exception("BertEM is not instantiable")
        else:
            BertEM.__instance = self
        self.initialize()

    def initialize(self):
        self.module = hub.Module(constants.BertConstants.BERT_MODEL, trainable=constants.BertConstants.TRAINABLE)
        self.tokenizer = self.__create_tokenizer(constants.BertConstants.VOCAB,
                                                 do_lower_case=constants.BertConstants.UNCASED)
        self.sess = tf.Session()
        self.sess.run(tf.global_variables_initializer())
        self.input_ids = tf.placeholder(dtype=tf.int32, shape=[None, None])
        self.input_mask = tf.placeholder(dtype=tf.int32, shape=[None, None])
        self.segment_ids = tf.placeholder(dtype=tf.int32, shape=[None, None])
        self.bert_inputs = dict(input_ids=self.input_ids, input_mask=self.input_mask, segment_ids=self.segment_ids)
        self.bert_outputs = self.module(self.bert_inputs, signature="tokens", as_dict=True)

    def __create_tokenizer(self, vocab_file, do_lower_case=False):
        """
        Creates BERT's full tokenizer object
        Args:
            vocab_file: Path to BERT vocabulary file
            do_lower_case: Boolean to indicate if the BERT model is case sensitive or not

        Returns:
            Full Tokenizer object
        """
        return tokenization.FullTokenizer(vocab_file=vocab_file, do_lower_case=do_lower_case)

    def __convert_sentence(self, sentence, max_seq_len):
        """
        Converts sentence to a set of tokens and inputs necessary to give to the BERT model
        #tokens:       [CLS] the dog is cute . [SEP][PAD][PAD]
        #input_ids:      101 67  56  67  77  89 102  100  100
        #input_mask:     1    1    1  1  1    1   1    0    0
        #segment_ids:    0    0    0  0  0    0   0    0    0
        Args:
            sentence: a string to be tokenized
            max_seq_len: length to which all sequences must be converted

        Returns:
            list of inputs Ids, attention masks, segment IDs
        """
        tokens = ['[CLS]']
        tokens.extend(self.tokenizer.tokenize(sentence))
        if len(tokens) > max_seq_len - 1:
            tokens = tokens[:max_seq_len - 1]
        tokens.append('[SEP]')

        segment_ids = [0] * len(tokens)
        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        input_mask = [1] * len(input_ids)

        # Zero Mask till seq_length
        zero_mask = [0] * (max_seq_len - len(tokens))
        input_ids.extend(zero_mask)
        input_mask.extend(zero_mask)
        segment_ids.extend(zero_mask)
        return input_ids, input_mask, segment_ids

    def convert_sentences_to_features(self, sentences, max_seq_len=32):
        """
        Given a list of strings , pre processes it in the form that is needed to feed the BERT model
        Args:
            sentences: a list of strings
            max_seq_len: length to which all sequences must be converted

        Returns:
            list of inputs Ids, attention masks, segment IDs for all the sentences in the input list
        """
        all_input_ids = []
        all_input_mask = []
        all_segment_ids = []

        for sentence in sentences:
            input_ids, input_mask, segment_ids = self.__convert_sentence(sentence, max_seq_len)
            all_input_ids.append(input_ids)
            all_input_mask.append(input_mask)
            all_segment_ids.append(segment_ids)
        return all_input_ids, all_input_mask, all_segment_ids

    def get_embedding(self, input_ids_vals, input_mask_vals, segment_ids_vals):
        """
        Runs the BERT modelto give the output embedding
        Args:
            input_ids_vals: input ID s to feed the BERT model
            input_mask_vals: input mask s to feed the BERT model
            segment_ids_vals: input segment ID s to feed the BERT model

        Returns:
            BERT embedding for passed inputs
        """
        bert_embedding = self.sess.run(self.bert_outputs, feed_dict={
            self.input_ids: input_ids_vals,
            self.input_mask: input_mask_vals,
            self.segment_ids: segment_ids_vals})
        return bert_embedding


if __name__ == '__main__':
    print("please run ConvAI/classifier_testsuite.py or ConvAI/classifier_trainsuite.py to run the class")
