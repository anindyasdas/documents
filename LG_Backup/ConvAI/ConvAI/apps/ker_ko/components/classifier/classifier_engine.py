# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: purnanaga.nalluri@lge.com
"""
import json
import os
import numpy as np
import tensorflow as tf
from tensorflow.contrib import predictor
from configparser import ConfigParser
from pathlib import Path
import requests
import re
from . import constants as cs, modeling as modeling, run_classifier as run_classifier, \
    tokenization as tokenization
from .run_classifier import model_fn_builder as model_fn_builder
from .utils import Utils as utils
from .rule_based_classifier import RuleBasedClassifier
import pandas as pd
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

flags = tf.flags
FLAGS = flags.FLAGS


def serving_input_fn():
    """
    Input function when the model is Served as a Saved model (pb file)
    """
    label_ids = tf.placeholder(tf.int32, [None], name=cs.KerKoStringConstants.LABEL_IDS)
    input_ids = tf.placeholder(tf.int32, [None, FLAGS.max_seq_length], name=cs.KerKoStringConstants.INPUT_IDS)
    input_mask = tf.placeholder(tf.int32, [None, FLAGS.max_seq_length], name=cs.KerKoStringConstants.INPUT_MASK)
    segment_ids = tf.placeholder(tf.int32, [None, FLAGS.max_seq_length], name=cs.KerKoStringConstants.SEGMENT_IDS)
    input_fn = tf.estimator.export.build_raw_serving_input_receiver_fn({
        cs.KerKoStringConstants.LABEL_IDS: label_ids,
        cs.KerKoStringConstants.INPUT_IDS: input_ids,
        cs.KerKoStringConstants.INPUT_MASK: input_mask,
        cs.KerKoStringConstants.SEGMENT_IDS: segment_ids,
    })()
    return input_fn


class ClassifierEngine(object):
    """
    Interface to Execute all kinds of classifiers
    """
    
    def __init__(self):
        self.bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)
        self.is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2
        self.rule_based_classifier = RuleBasedClassifier.get_instance()

        # Instance of BERT tokenizer
        self.tokenizer = tokenization.FullTokenizer(
            vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)
        # MECAB URL configuration
        read_config = ConfigParser()

        read_config.read(cs.ClassifierConstants.CONFIG_PATH)
        logger.debug("URL=(%s)" % read_config.get('mecab_config', 'mecab_url'))
        self.mecab_url = read_config.get('mecab_config', 'mecab_url')

        # Data processors for different classifiers
        self.processors = {
            cs.ClassifierConstants.TASK_TOPIC: run_classifier.TopicProcessor,
            cs.ClassifierConstants.TASK_TYPE: run_classifier.TypeProcessor,
            cs.ClassifierConstants.TASK_SECTION: run_classifier.SectionProcessor,
            cs.ClassifierConstants.TASK_WM_SECTION: run_classifier.SectionProcessor,
            cs.ClassifierConstants.TASK_KEPLER_SECTION: run_classifier.SectionProcessor,
            cs.ClassifierConstants.TASK_DRYER_SECTION: run_classifier.SectionProcessor,
            cs.ClassifierConstants.TASK_STYLER_SECTION: run_classifier.SectionProcessor
        }
        if cs.ClassifierConstants.IS_TRAIN:
            self.topic_estimator = self._get_estimator(processor=run_classifier.TopicProcessor())
            self.type_estimator = self._get_estimator(processor=run_classifier.TypeProcessor())
            self.section_estimator = self._get_estimator(processor=run_classifier.SectionProcessor())
            self.section_wm_estimator = self._get_estimator(processor=run_classifier.SectionProcessor(),
                                                            product=cs.ClassifierConstants.PRD_WM )
            self.section_kepler_estimator = self._get_estimator(processor=run_classifier.SectionProcessor(),
                                                                product=cs.ClassifierConstants.PRD_KEPLER)
            self.section_dryer_estimator = self._get_estimator(processor=run_classifier.SectionProcessor(),
                                                               product=cs.ClassifierConstants.PRD_DRYER)
            self.section_styler_estimator = self._get_estimator(processor=run_classifier.SectionProcessor(),
                                                                product=cs.ClassifierConstants.PRD_STYLER)

            self.topic_predictor = self._get_predictor(cs.PathConstants.TOPIC_EXPT_DIR)
            self.type_predictor = self._get_predictor(cs.PathConstants.TYPE_EXPT_DIR)
            self.section_predictor = self._get_predictor(cs.PathConstants.SECTION_EXPT_DIR)
            self.section_wm_predictor = self._get_predictor(cs.PathConstants.SECTION_WM_EXPT_DIR)
            self.section_kepler_predictor = self._get_predictor(cs.PathConstants.SECTION_KEPLER_EXPT_DIR)
            self.section_dryer_predictor = self._get_predictor(cs.PathConstants.SECTION_DRYER_EXPT_DIR)
            self.section_styler_predictor = self._get_predictor(cs.PathConstants.SECTION_STYLER_EXPT_DIR)
        else:
            self.topic_predictor = predictor.from_saved_model(cs.PathConstants.TOPIC_DIR)
            self.type_predictor = predictor.from_saved_model(cs.PathConstants.TYPE_DIR)
            self.section_predictor = predictor.from_saved_model(cs.PathConstants.SECTION_DIR)
            self.section_wm_predictor = predictor.from_saved_model(cs.PathConstants.SECTION_WM_DIR)
            self.section_kepler_predictor = predictor.from_saved_model(cs.PathConstants.SECTION_KEPLER_DIR)
            self.section_dryer_predictor = predictor.from_saved_model(cs.PathConstants.SECTION_DRYER_DIR)
            self.section_styler_predictor = predictor.from_saved_model(cs.PathConstants.SECTION_STYLER_DIR)

        # Required flags for training and evaluation
        flags.mark_flag_as_required("data_dir")
        flags.mark_flag_as_required("task_name")
        flags.mark_flag_as_required("vocab_file")
        flags.mark_flag_as_required("bert_config_file")
        flags.mark_flag_as_required("output_dir")

    def _get_predictor(self, export_dir):
        """
        Predictor API to provide methods to test the model
        Args:
            export_dir: directory path from which the predictor needs to be loaded ex. TOPIC_EXPT_DIR

        Returns:
            predictor object correspond to the saved model
        """
        subdir = [x for x in Path(export_dir).iterdir() if x.is_dir() and 'temp' not in str(x)]
        latest = str(sorted(subdir)[-1])
        return predictor.from_saved_model(latest)

    def _get_estimator(self, processor=None,product=None):
        """
        Estimator API to provide methods to test the model
        Args:
            processor: Data processor class for which the estimator needs to be built ex. TopicProcessor

        Returns:
            Estimator object correspond to the model and input portions of the TensorFlow graph
        """
        label_list = processor.get_labels(product)
        output_dir_temp = None
        if isinstance(processor, run_classifier.TopicProcessor):
            output_dir_temp = cs.PathConstants.TOPIC_DIR
        elif isinstance(processor, run_classifier.TypeProcessor):
            output_dir_temp = cs.PathConstants.TYPE_DIR
        elif isinstance(processor, run_classifier.SectionProcessor):
            if product == cs.ClassifierConstants.PRD_WM:
                output_dir_temp = cs.PathConstants.SECTION_WM_DIR
            elif product == cs.ClassifierConstants.PRD_KEPLER:
                output_dir_temp = cs.PathConstants.SECTION_KEPLER_DIR
            elif product == cs.ClassifierConstants.PRD_DRYER:
                output_dir_temp = cs.PathConstants.SECTION_DRYER_DIR
            elif product == cs.ClassifierConstants.PRD_STYLER:
                output_dir_temp = cs.PathConstants.SECTION_STYLER_DIR
            else:
                output_dir_temp = cs.PathConstants.SECTION_DIR

        run_config = tf.contrib.tpu.RunConfig(
            cluster=None,
            master=FLAGS.master,
            model_dir=output_dir_temp,
            save_checkpoints_steps=FLAGS.save_checkpoints_steps,
            tpu_config=tf.contrib.tpu.TPUConfig(
                iterations_per_loop=FLAGS.iterations_per_loop,
                num_shards=FLAGS.num_tpu_cores,
                per_host_input_for_training=self.is_per_host))

        model_fn = model_fn_builder(
            bert_config=self.bert_config,
            num_labels=len(label_list),
            init_checkpoint=FLAGS.init_checkpoint,
            learning_rate=FLAGS.learning_rate,
            num_train_steps=None,
            num_warmup_steps=None,
            use_tpu=FLAGS.use_tpu,
            use_one_hot_embeddings=FLAGS.use_tpu)

        estimator = tf.contrib.tpu.TPUEstimator(
            use_tpu=FLAGS.use_tpu,
            model_fn=model_fn,
            config=run_config,
            train_batch_size=FLAGS.train_batch_size,
            eval_batch_size=FLAGS.eval_batch_size,
            predict_batch_size=FLAGS.predict_batch_size)
        
        estimator._export_to_tpu = False
        # Save the pb file in the tmp folder, only if the folder is not empty
        if isinstance(processor, run_classifier.TopicProcessor):
            output_dir_temp = cs.PathConstants.TOPIC_EXPT_DIR
            os.makedirs(output_dir_temp, exist_ok=True)
            if len(os.listdir(output_dir_temp)) == 0:
                estimator.export_saved_model(output_dir_temp, serving_input_fn)
        elif isinstance(processor, run_classifier.TypeProcessor):
            output_dir_temp = cs.PathConstants.TYPE_EXPT_DIR
            os.makedirs(output_dir_temp, exist_ok=True)
            if len(os.listdir(output_dir_temp)) == 0:
                estimator.export_saved_model(output_dir_temp, serving_input_fn)
        elif isinstance(processor, run_classifier.SectionProcessor):
            if product == cs.ClassifierConstants.PRD_WM:
                output_dir_temp = cs.PathConstants.SECTION_WM_EXPT_DIR
            elif product == cs.ClassifierConstants.PRD_KEPLER:
                output_dir_temp = cs.PathConstants.SECTION_KEPLER_EXPT_DIR
            elif product == cs.ClassifierConstants.PRD_DRYER:
                output_dir_temp = cs.PathConstants.SECTION_DRYER_EXPT_DIR
            elif product == cs.ClassifierConstants.PRD_STYLER:
                output_dir_temp = cs.PathConstants.SECTION_STYLER_EXPT_DIR
            else:
                output_dir_temp = cs.PathConstants.SECTION_EXPT_DIR
            os.makedirs(output_dir_temp, exist_ok=True)
            if len(os.listdir(output_dir_temp)) == 0:
                estimator.export_saved_model(output_dir_temp, serving_input_fn)
        return estimator

    def train(self): # pragma: no cover
        """
        Function to train the model on CPU with default parameters / flags
        """
        FLAGS.do_train = True
        FLAGS.do_eval = True
        FLAGS.max_seq_length = 256
        FLAGS.train_batch_size = 50
        FLAGS.learning_rate = 2e-5
        FLAGS.num_train_epochs = 3
        tf.app.run(run_classifier.main)

    def predict(self):
        """
        Function to do file predict on with the test data in Data in Dataset directory
        """
        FLAGS.do_predict = True
        FLAGS.max_seq_length = 256
        FLAGS.train_batch_size = 8
        FLAGS.learning_rate = 2e-5
        FLAGS.num_train_epochs = 3
        tf.app.run(run_classifier.main)

    def evaluate(self): # pragma: no cover
        """
        Function to do file evaluate on with the test data in Data in Dataset directory
        """
        FLAGS.do_eval = True
        FLAGS.max_seq_length = 256
        FLAGS.train_batch_size = 8
        FLAGS.learning_rate = 2e-5
        FLAGS.num_train_epochs = 3
        tf.app.run(run_classifier.main)
    
    def get_input_features(self, sentence):
        tokenizer = self.tokenizer
        mecab_text = ''
        text_a = sentence
        text_a = re.sub(r"(\[_]|\[=]|\[\s]|\[])", "", text_a)
        text_url = self.mecab_url + text_a
        mecab_result = requests.get(text_url)
        t_json = json.loads(mecab_result.text)[cs.ClassifierConstants.SENTENCES]
        rep_t = run_classifier.get_morphs(t_json)
        for token in rep_t:
            mecab_text = mecab_text + ' ' + token

        token_a = tokenizer.tokenize(mecab_text)
        tokens = []
        segments_ids = []
        tokens.append("[CLS]")
        segment_ids = []
        segment_ids.append(0)
        for token in token_a:
            tokens.append(token)
            segment_ids.append(0)
        tokens.append('[SEP]')
        segment_ids.append(0)
        input_ids = tokenizer.convert_tokens_to_ids(tokens)
        input_mask = [1] * len(input_ids)
        max_seq_length = 128
        while len(input_ids) < max_seq_length:
            input_ids.append(0)
            input_mask.append(0)
            segment_ids.append(0)
        label_id = [0]

        # print((input_ids),(input_mask),(segment_ids),(label_id))

        return {"input_ids":[input_ids], "input_mask":[input_mask], "segment_ids":[segment_ids], "label_ids":label_id}
    
    def get_classifier_output(self, sentence, product=None):
        """
        Function to get the overall classifier output
        Args:
            sentence: String to be tested
            product: Product type - washing machine, kepler, dryer, styler, refrigerator

        Returns:
            The classifier output in json format
        """

        try:
            topic_classifier_output = self._get_each_classifier_output(sentence, task_name=cs.ClassifierConstants.TASK_TOPIC)

            if topic_classifier_output not in cs.KerKoMappingDictionary.TOPIC_LABELS:
                # If the topic is not one of Specification, Troubleshooting or Operation then throw exception
                return json.dumps({cs.ResponseConstants.response_code: cs.ResponseConstants.STATUS_UNSUPPORTED_QUERY})
            elif topic_classifier_output == cs.KerKoMappingDictionary.TOPIC_LABELS[1]:
                # If the topic identified is Operation go through the below process
                # Involves the call for
                # 1. 'section classifier'
                # 2. 'rule based classifier - section separator'
                # 3. 'section intent classifier'
                # 4. 'question class classifier'
                return self.__classification_for_operation_section(sentence, topic_classifier_output, product)
            else:
                # If the topic identified is Troubleshooting go through the below process
                # Involves the call for
                # 1. 'type classifier'
                # 2. 'query intent classifier'
                return self.__classification_for_troubleshooting_section(sentence, topic_classifier_output)
        except Exception as e:
            logger.exception("Classifier : Error in predict_single_example " + str(e))
            return json.dumps({cs.ResponseConstants.response_code: cs.ResponseConstants.STATUS_UNSUPPORTED_QUERY})
    
    def _resolve_diagnosis(self, query, query_type):
        beep_words = cs.KerKoStringConstants.BEEP_WORDS
        thinkq_words = cs.KerKoStringConstants.THINQ_WORDS
        for word in beep_words:
            check = re.search(word, query)
            if check:
                return cs.KerKoStringConstants.DIAG_BEEP
        for word in thinkq_words:
            check = re.search(word, query)
            if check:
                return cs.KerKoStringConstants.DIAG_THINQ
        # Added default case for diagnosis
        check = re.search(cs.KerKoStringConstants.DIAGNOSIS, query)
        if check:
            return cs.KerKoStringConstants.DIAG_BEEP
        return query_type

    def __classification_for_troubleshooting_section(self, eval_text, topic_classifier_output):
        """
        If the topic identified is Troubleshooting go through the below pipeline
        Involves the call for
        1. 'sub section classifier'
        Args:
            eval_text: user query
            topic_classifier_output: Topic classifier output i.e Troubleshooting

        Returns:
            The classifier output in json format

        """
        # Call the Sub section classifier to identify sub section with which the user query is asked
        # One of reason , solution, cause and solution
        type_classifier_output = self._resolve_diagnosis(eval_text, None)
        if not type_classifier_output:
            type_classifier_output = self._get_each_classifier_output(eval_text,
                                                                      task_name=cs.ClassifierConstants.TASK_TYPE)
        if (type_classifier_output not in cs.KerKoMappingDictionary.TYPE_LABELS) and \
                (type_classifier_output != cs.KerKoStringConstants.DIAG_BEEP) and \
                (type_classifier_output != cs.KerKoStringConstants.DIAG_THINQ):
            # if the sub section identified is not among the list of sub section specified and Beep and Thinq
            return json.dumps({cs.ResponseConstants.response_code: cs.ResponseConstants.STATUS_UNSUPPORTED_QUERY})
        return json.dumps({
            cs.ResponseConstants.response_code: cs.ResponseConstants.STATUS_OK,
            cs.ResponseConstants.response_data:
                {
                    cs.KerKoStringConstants.TOPIC: topic_classifier_output,
                    cs.KerKoStringConstants.FOLLOW_UP: None,
                    cs.KerKoStringConstants.INTENT: "cause-sol",
                    cs.KerKoStringConstants.TYPE: type_classifier_output,
                    cs.KerKoStringConstants.CLASS: None,
                    cs.KerKoStringConstants.CATEGORY: None
                }
        })

    def __classification_for_operation_section(self, eval_text, topic_classifier_output, product=None):
        """
        If the topic identified is Operation go through the below pipeline
        Involves the call for
        1. 'section classifier'
        2. 'section intent classifier'
        Args:
            eval_text: user query
            topic_classifier_output: Topic classifier output i.e Operation

        Returns:
            The classifier output in json format

        """
        # Call the section classifier to get the L1 key of the query asked
        section_classifier_output = self._get_each_classifier_output(eval_text,
                                                                  task_name=cs.ClassifierConstants.TASK_SECTION, product=product)
        if product == cs.ClassifierConstants.PRD_KEPLER:
            section_classifier_output = self.rule_based_classifier.map_kepler_operation_subsection(eval_text, section_classifier_output)
        # To categorize the section into one of feature//controlpanel
        sub_section = self.rule_based_classifier.map_operation_subsection(section_classifier_output)
        if sub_section not in cs.KerKoOperationConstants.OPERATION_SUB_CATEGORY_MAP.keys():
            # if the section intent identified is not among the list of sub sections specified
            return json.dumps({cs.ResponseConstants.response_code: cs.ResponseConstants.STATUS_UNSUPPORTED_QUERY})

        # Rule based classifier for identification of the query section intent
        section_intent_classifier_output = self.rule_based_classifier.get_operation_intent(eval_text)
        if section_intent_classifier_output not in cs.KerKoOperationConstants.OPERATION_INTENT_DICT.keys():
            # if the section intent identified is not among the list of intents specified
            return json.dumps({cs.ResponseConstants.response_code: cs.ResponseConstants.STATUS_UNSUPPORTED_QUERY})
        else:
            return json.dumps({
                cs.ResponseConstants.response_code: cs.ResponseConstants.STATUS_OK,
                cs.ResponseConstants.response_data:
                    {
                        cs.KerKoStringConstants.TOPIC: topic_classifier_output,
                        cs.KerKoStringConstants.FOLLOW_UP: None,
                        cs.KerKoStringConstants.INTENT: section_intent_classifier_output,
                        cs.KerKoStringConstants.TYPE: section_classifier_output,
                        cs.KerKoStringConstants.CLASS: None,
                        cs.KerKoStringConstants.CATEGORY: sub_section
                    }
            })

    def _get_each_classifier_output(self, sentence, task_name, product=None):
        """
        Get the output for each classifier
        Args:
            sentence: A single training/test example for simple sequence classification.
            task_name: Name of the task ex. Topic, type etc.,

        Returns:
            Label of each classifier output
        """
        if task_name == cs.ClassifierConstants.TASK_SECTION:
            if product == cs.ClassifierConstants.PRD_WM:
                labels = cs.KerKoMappingDictionary.LABELS_TO_TASK_NAME_MAP[cs.ClassifierConstants.TASK_WM_SECTION]
            elif product == cs.ClassifierConstants.PRD_KEPLER:
                labels = cs.KerKoMappingDictionary.LABELS_TO_TASK_NAME_MAP[cs.ClassifierConstants.TASK_KEPLER_SECTION]
            elif product == cs.ClassifierConstants.PRD_DRYER:
                labels = cs.KerKoMappingDictionary.LABELS_TO_TASK_NAME_MAP[cs.ClassifierConstants.TASK_DRYER_SECTION]
            elif product == cs.ClassifierConstants.PRD_STYLER:
                labels = cs.KerKoMappingDictionary.LABELS_TO_TASK_NAME_MAP[cs.ClassifierConstants.TASK_STYLER_SECTION]
            else:
                labels = cs.KerKoMappingDictionary.LABELS_TO_TASK_NAME_MAP[cs.ClassifierConstants.TASK_SECTION]
        else:
            labels = cs.KerKoMappingDictionary.LABELS_TO_TASK_NAME_MAP[task_name]
        processor = self.processors[task_name]()
        label_list = processor.get_labels()
        estimator = None
        if isinstance(processor, run_classifier.TopicProcessor):
            predictor = self.topic_predictor
        elif isinstance(processor, run_classifier.TypeProcessor):
            predictor = self.type_predictor
        elif isinstance(processor, run_classifier.SectionProcessor):
            if product == cs.ClassifierConstants.PRD_WM:
                predictor = self.section_wm_predictor
            elif product == cs.ClassifierConstants.PRD_KEPLER:
                predictor = self.section_kepler_predictor
            elif product == cs.ClassifierConstants.PRD_DRYER:
                predictor = self.section_dryer_predictor
            elif product == cs.ClassifierConstants.PRD_STYLER:
                predictor = self.section_styler_predictor
            else:
                predictor = self.section_predictor
        final_fe_dict = self.get_input_features(sentence)
        predictions = predictor(final_fe_dict)['probabilities'][0]
        # print(predictions)
        classifier_output = labels[np.argmax(predictions)]

        return classifier_output

    def evaluate_all_classifier_on_file(self, filename): # pragma: no cover
        data = utils.read_input(filename)
        result_col_names = [cs.KerKoStringConstants.TOPIC,
                            cs.KerKoStringConstants.FOLLOW_UP,
                            cs.KerKoStringConstants.INTENT,
                            cs.KerKoStringConstants.TYPE,
                            cs.KerKoStringConstants.CLASS,
                            cs.KerKoStringConstants.CATEGORY]
        results_df = pd.DataFrame(columns=result_col_names)
        input_data = data[cs.KerKoStringConstants.USER_QUESTION]
        product_data = data[cs.KerKoStringConstants.PRODUCT]

        for idx, query in enumerate(input_data):
            op_json = self.get_classifier_output(query,product=product_data[idx])
            op_json = json.loads(op_json)
            print(op_json)
            if op_json[cs.ResponseConstants.response_code] == cs.ResponseConstants.STATUS_OK:
                op_json = op_json[cs.ResponseConstants.response_data]
                results_df.loc[idx, cs.KerKoStringConstants.TOPIC] = op_json[
                    cs.KerKoStringConstants.TOPIC]
                results_df.loc[idx, cs.KerKoStringConstants.FOLLOW_UP] = op_json[
                    cs.KerKoStringConstants.FOLLOW_UP]
                results_df.loc[idx, cs.KerKoStringConstants.INTENT] = op_json[
                    cs.KerKoStringConstants.INTENT]
                results_df.loc[idx, cs.KerKoStringConstants.TYPE] = op_json[
                    cs.KerKoStringConstants.TYPE]
                results_df.loc[idx, cs.KerKoStringConstants.CLASS] = op_json[
                    cs.KerKoStringConstants.CLASS]
                results_df.loc[idx, cs.KerKoStringConstants.CATEGORY] = op_json[
                    cs.KerKoStringConstants.CATEGORY]
            else:
                results_df.loc[idx, cs.KerKoStringConstants.TOPIC] = None
                results_df.loc[idx, cs.KerKoStringConstants.FOLLOW_UP] = None
                results_df.loc[idx, cs.KerKoStringConstants.INTENT] = None
                results_df.loc[idx, cs.KerKoStringConstants.TYPE] = None
                results_df.loc[idx, cs.KerKoStringConstants.CLASS] = None
                results_df.loc[idx, cs.KerKoStringConstants.CATEGORY] = None

        data = pd.concat([data, results_df], axis=1)
        print("writing to :", "results_new.xlsx")
        utils.write_file(data, save_path=cs.PathConstants.RESULTS_FILE)


if __name__ == "__main__": # pragma: no cover
    import timeit
    ce = ClassifierEngine()

    start = timeit.default_timer()
    print(ce.get_classifier_output("무엇이 문제 CL로 이어질 수 있습니까?"))
    
    stop = timeit.default_timer()
    print('Time: ', stop - start)
    
    start = timeit.default_timer()
    print(ce.get_classifier_output("무엇이 문제 CL로 이어질 수 있습니까?"))
    
    stop = timeit.default_timer()
    print('Time: ', stop - start)
    #ce.train()
    #ce.evaluate_all_classifier_on_file("test.xlsx")
