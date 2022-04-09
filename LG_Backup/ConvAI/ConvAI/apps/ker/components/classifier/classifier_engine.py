# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anusha.kamath@lge.com
@author: vishwaas@lge.com
"""
import logging
import json
import pandas as pd

from keras.utils import to_categorical

from .embedding_model import BertEM
from .lstm_classifier import LstmClassifier
from .rule_based_classifier import RuleBasedClassifier
from ..engine import constants as engine_constants
from . import constants as classifier_constants
from .question_classifier import QuestionClassification
from . import classifier_utils as utils


class ClassifierEngine(object):
    """
    Interface to Execute all kinds of classifiers
    """

    def __init__(self, num_lable=0, evaluate=True, all_models=True, purpose="Topic",
                 hidden_lstm_units=classifier_constants.TrainingConstants.HIDDEN_LSTM_UNITS):
        """
        Args:
            num_lable: Total number of classes in classifier : Argument necessary only while training
            evaluate: Boolean to indicate if training or testing
            all_models: Boolean to indicate if training or testing is for all KER models or a specific model
            purpose: The type of KER model that has to be trained or tested
            hidden_lstm_units: Number of hidden units for BILSTM in the network
        """
        self.embedding_model = BertEM.get_instance()
        self.lstm_classifier = LstmClassifier(num_lable=num_lable, evaluate=evaluate, all_models=all_models,
                                              hidden_lstm_units=hidden_lstm_units, purpose=purpose)
        self.rule_based_classifier = RuleBasedClassifier()
        self.question_class_classifier = QuestionClassification.get_instance()
        self.purpose = purpose
        self.all_models = all_models

    def get_classifier_output(self, eval_text):
        """
        Single sentence prediction for all the classifier required for KER pipeline in order
        Args:
            eval_text: String to be tested

        Returns:
            The classifier output in json format with execution status
            e.g:
               {"response_code": 200,
               "response_data": {"Topic": "Operation",
                                "Follow_up": false,
                                "Intent": "Description",
                                "Type": "Door Bins",
                                "Class": "factoid"}}
        """
        eval_text = utils.preprocess_input(eval_text)

        # Call the topic classifier to get the topic to which the query belongs
        # One of Specification, Troubleshooting or Operation
        topic_classifier_output = self.__execute_classifier(eval_text, classifier_constants.KerStringConstants.TOPIC)

        if topic_classifier_output not in classifier_constants.KerMappingDictionary.TOPIC_DICT.values():
            # If the topic is not one of Specification, Troubleshooting or Operation then throw exception
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})
        elif topic_classifier_output == classifier_constants.KerMappingDictionary.TOPIC_DICT[0]:
            # If the topic identified is Specification go through the below process
            # Involves the call for :
            # 1. 'follow up classifier'
            return self.__classification_for_specification_section(eval_text, topic_classifier_output)
        elif topic_classifier_output == classifier_constants.KerMappingDictionary.TOPIC_DICT[2]:
            # If the topic identified is Operation go through the below process
            # Involves the call for
            # 1. 'section classifier'
            # 2. 'rule based classifier - section separator'
            # 3. 'section intent classifier'
            # 4. 'question class classifier'
            return self.__classification_for_operation_section(eval_text, topic_classifier_output)
        else:
            # If the topic identified is Troubleshooting go through the below process
            # Involves the call for
            # 1. 'type classifier'
            # 2. 'query intent classifier'
            return self.__classification_for_troubleshooting_section(eval_text, topic_classifier_output)

    def __classification_for_troubleshooting_section(self, eval_text, topic_classifier_output):
        """
        If the topic identified is Troubleshooting go through the below pipeline
        Involves the call for
        1. 'type classifier'
        2. 'query intent classifier'
        Args:
            eval_text: user query
            topic_classifier_output: Topic classifier output i.e Troubleshooting

        Returns:
            The classifier output in json format

        """
        # Call the intent classifier to intent with which the user query is asked
        # One of reason , solution, cause and solution
        intent_classifier_output = self.__execute_classifier(eval_text, classifier_constants.KerStringConstants.INTENT)

        if intent_classifier_output not in classifier_constants.KerMappingDictionary.INTENT_DICT.values():
            # when the intent is not one of reason , solution, cause and solution
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})

        type_classifier_output = self.__execute_classifier(eval_text, classifier_constants.KerStringConstants.TYPE)
        # Call the intent classifier to intent with which the user query is asked
        # One of error message, noises, cooling problem, ice problem, wifi problem, general problem

        if type_classifier_output not in classifier_constants.KerMappingDictionary.TYPE_DICT.values():
            # when the intent is not one of error message, noises, cooling problem, ice problem, wifi problem,
            # general problem
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})

        else:
            return json.dumps({
                engine_constants.response_code: engine_constants.STATUS_OK,
                engine_constants.response_data:
                    {
                        classifier_constants.KerStringConstants.TOPIC: topic_classifier_output,
                        classifier_constants.KerStringConstants.FOLLOW_UP: None,  # TBD for troubleshooting
                        classifier_constants.KerStringConstants.INTENT: intent_classifier_output,
                        classifier_constants.KerStringConstants.TYPE: type_classifier_output,
                        classifier_constants.KerStringConstants.CLASS: None,
                        classifier_constants.KerStringConstants.CATEGORY: None
                    }
            })

    def __classification_for_operation_section(self, eval_text, topic_classifier_output):
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
        section_classifier_output = self.__execute_classifier(eval_text,
                                                              classifier_constants.KerStringConstants.SECTION)

        # Rule based classifier to separate similar categories that could not be separated by a DL classifier
        section_classifier_output = self.rule_based_classifier.section_seperator(eval_text, section_classifier_output)

        if (section_classifier_output not in classifier_constants.KerMappingDictionary.SECTION_DICT.values()) and (
                section_classifier_output not in classifier_constants.KerOperationConstants.OPERATION_SEPARATED_SECTIONS):
            # if the L1 identified is not among the list specified
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})

        # To categorize the section into one of feature/component/checklist/controlpanel
        sub_section = self.rule_based_classifier.map_operation_subsection(section_classifier_output)
        if sub_section not in classifier_constants.KerOperationConstants.OPERATION_SUB_CATEGORY_MAP.keys():
            # if the section intent identified is not among the list of sub sections specified
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})

        # Rule based classifier for identification of the query section intent
        section_intent_classifier_output = self.rule_based_classifier.get_operation_intent(eval_text, sub_section)
        if section_intent_classifier_output not in classifier_constants.KerOperationConstants.OPERATION_INTENT_DICT.keys():
            # if the section intent identified is not among the list of intents specified
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})

        # Call the class classifier to get the question type of the query

        class_classifier_output = self.__execute_classifier(eval_text, classifier_constants.KerStringConstants.CLASS)

        if class_classifier_output not in classifier_constants.KerMappingDictionary.CLASS_DICT.values():
            # if the question class identified is not among the list of question types specified
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})

        else:
            return json.dumps({
                engine_constants.response_code: engine_constants.STATUS_OK,
                engine_constants.response_data:
                    {
                        classifier_constants.KerStringConstants.TOPIC: topic_classifier_output,
                        classifier_constants.KerStringConstants.FOLLOW_UP: None,
                        classifier_constants.KerStringConstants.INTENT: section_intent_classifier_output,
                        classifier_constants.KerStringConstants.TYPE: section_classifier_output,
                        classifier_constants.KerStringConstants.CLASS: class_classifier_output,
                        classifier_constants.KerStringConstants.CATEGORY: sub_section
                    }
            })

    def __classification_for_specification_section(self, eval_text, topic_classifier_output):
        """
        If the topic identified is Specification go through the below pipeline
        Involves the call for :
        1. 'follow up classifier'
        Args:
            eval_text: user query
            topic_classifier_output: Topic classifier output i.e Specification

        Returns:
            The classifier output in json format

        """
        # Call the follow up classifier too understand if the query is freash query or follow up query
        followup_classifier_output = self.__execute_classifier(eval_text,
                                                               classifier_constants.KerStringConstants.FOLLOW_UP)

        if followup_classifier_output not in classifier_constants.KerMappingDictionary.FOLLOW_UP_DICT.values():
            # if the query is not identified as one fresh or follow up question
            return json.dumps({engine_constants.response_code: engine_constants.STATUS_UNSUPPORTED_QUERY})

        else:
            return json.dumps({
                engine_constants.response_code: engine_constants.STATUS_OK,
                engine_constants.response_data:
                    {
                        classifier_constants.KerStringConstants.TOPIC: topic_classifier_output,
                        classifier_constants.KerStringConstants.FOLLOW_UP: followup_classifier_output,
                        classifier_constants.KerStringConstants.INTENT: None,
                        classifier_constants.KerStringConstants.TYPE: None,
                        classifier_constants.KerStringConstants.CLASS: None,
                        classifier_constants.KerStringConstants.CATEGORY: None
                    }
            })

    def __execute_classifier(self, eval_text, purpose):
        """
        Execute the classifier based on the purpose given.
        Args:
             eval_text: String to be tested
             purpose: The name of the classifier #(Intent Classifier, Type classifier, Topic classifier)

        Returns:
                The output category as a string
        """
        reverse_dict = self.get_reverse_dict(purpose)
        to_return = ""
        if reverse_dict is None:
            return to_return  # Exception to be caught by the calling function like in get_classifier_output

        eval_text = [eval_text]

        #  get embedding for the given query
        input_ids_vals, input_mask_vals, segment_ids_vals = self.embedding_model.convert_sentences_to_features(
            eval_text, classifier_constants.BertConstants.MAX_LENGTH)
        out = self.embedding_model.get_embedding(input_ids_vals, input_mask_vals, segment_ids_vals)

        if purpose == classifier_constants.KerStringConstants.CLASS:
            logit = self.question_class_classifier.predict(eval_text)
            logit = logit[0]  # Since batch size of 1 is currently supported
            to_return = reverse_dict[logit]

        else:
            logit = self.lstm_classifier.predict_single(out['sequence_output'], purpose=purpose)
            to_return = reverse_dict[logit]

        logging.log(engine_constants.LG_LOGGING_MODULE_OUTPUT_LVL, to_return)
        return to_return

    @staticmethod
    def get_reverse_dict(purpose):
        """
        Get a dictionary of What each categorical variable means
        Args:
            purpose: The name of the classifier #(Intent Classifier, Purpose classifier)
        Returns:
               A dictionary of mapping Tag to String
        """
        if purpose == classifier_constants.KerStringConstants.TOPIC:
            reverse_dict = classifier_constants.KerMappingDictionary.TOPIC_DICT
            return reverse_dict
        elif purpose == classifier_constants.KerStringConstants.INTENT:
            reverse_dict = classifier_constants.KerMappingDictionary.INTENT_DICT
            return reverse_dict
        elif purpose == classifier_constants.KerStringConstants.INFO_EXTRACTION:
            reverse_dict = classifier_constants.KerMappingDictionary.INFO_DICT
            return reverse_dict
        elif purpose == classifier_constants.KerStringConstants.TYPE:
            reverse_dict = classifier_constants.KerMappingDictionary.TYPE_DICT
            return reverse_dict
        elif purpose == classifier_constants.KerStringConstants.FOLLOW_UP:
            reverse_dict = classifier_constants.KerMappingDictionary.FOLLOW_UP_DICT
            return reverse_dict
        elif purpose == classifier_constants.KerStringConstants.SECTION:
            reverse_dict = classifier_constants.KerMappingDictionary.SECTION_DICT
            return reverse_dict
        elif purpose == classifier_constants.KerStringConstants.CLASS:
            reverse_dict = classifier_constants.KerMappingDictionary.CLASS_DICT
            return reverse_dict
        else:
            logging.log(logging.INFO, "classifier not implemented for this problem")
            return None

    def __get_embedding(self, sentences):
        """
        Read from file and get the required embedding from the embedding model.
        Args:
            sentences: list of sentences for which classifier output is required
        Returns:
            BERT embedding for those sentences
        """
        input_ids_val, input_mask_val, segment_ids_val = self.embedding_model.convert_sentences_to_features(
            sentences, classifier_constants.BertConstants.MAX_LENGTH)
        bert_output = self.embedding_model.get_embedding(input_ids_val, input_mask_val, segment_ids_val)
        features = bert_output['sequence_output']
        return features

    def evaluate_on_file(self, input_file=classifier_constants.PathConstants.TEST_DATA, input_column_name="Text",
                         label_column_name="Label", output_file="output.csv"): # pragma: no cover
        """
        Function to get classifier output for one type (defined in purpose) output with a file input.
        Args:
            input_file : file path of input file
            label_column_name : Name of column where ground truth is present
            output_file : file path of output file
            input_column_name: Name of input column

        Returns:
            writes classifier results to the output file
        """
        data = utils.read_input(input_file)
        if self.all_models:
            result_col_names = [classifier_constants.KerStringConstants.TOPIC,
                                classifier_constants.KerStringConstants.FOLLOW_UP,
                                classifier_constants.KerStringConstants.INTENT,
                                classifier_constants.KerStringConstants.TYPE,
                                classifier_constants.KerStringConstants.CLASS,
                                classifier_constants.KerStringConstants.CATEGORY]
            results_df = pd.DataFrame(columns=result_col_names)
            input_data = data[input_column_name]

            for idx, query in enumerate(input_data):
                op_json = self.get_classifier_output(query)
                op_json = json.loads(op_json)
                print(op_json)
                if op_json["response_code"] == 200:
                    op_json = op_json["response_data"]
                    results_df.loc[idx, classifier_constants.KerStringConstants.TOPIC] = op_json[
                        classifier_constants.KerStringConstants.TOPIC]
                    results_df.loc[idx, classifier_constants.KerStringConstants.FOLLOW_UP] = op_json[
                        classifier_constants.KerStringConstants.FOLLOW_UP]
                    results_df.loc[idx, classifier_constants.KerStringConstants.INTENT] = op_json[
                        classifier_constants.KerStringConstants.INTENT]
                    results_df.loc[idx, classifier_constants.KerStringConstants.TYPE] = op_json[
                        classifier_constants.KerStringConstants.TYPE]
                    results_df.loc[idx, classifier_constants.KerStringConstants.CLASS] = op_json[
                        classifier_constants.KerStringConstants.CLASS]
                    results_df.loc[idx, classifier_constants.KerStringConstants.CATEGORY] = op_json[
                        classifier_constants.KerStringConstants.CATEGORY]
                else:
                    results_df.loc[idx, classifier_constants.KerStringConstants.TOPIC] = None
                    results_df.loc[idx, classifier_constants.KerStringConstants.FOLLOW_UP] = None
                    results_df.loc[idx, classifier_constants.KerStringConstants.INTENT] = None
                    results_df.loc[idx, classifier_constants.KerStringConstants.TYPE] = None
                    results_df.loc[idx, classifier_constants.KerStringConstants.CLASS] = None
                    results_df.loc[idx, classifier_constants.KerStringConstants.CATEGORY] = None

            data = pd.concat([data, results_df], axis=1)
            print("writing to :", output_file)
            utils.write_file(data, save_path=output_file)

        else:
            features, target, num_labels = utils.label_encode_input_data(data, purpose=self.purpose,
                                                                         input_column_name=input_column_name,
                                                                         true_value_col_name=label_column_name)

            test_features = self.__get_embedding(features)
            y_pred = self.lstm_classifier.evaluate_model(test_features=test_features)

            if classifier_constants.FunctionConstants.GET_ACCURACY_REPORT:
                # You can disable this in constants.py if not required
                utils.get_classification_report(target, y_pred, num_labels)
                utils.get_confusion_matric(target, y_pred, num_labels)
            output_dict = classifier_constants.KerMappingDictionary.MODEL_DICT_MAPPING[self.purpose]
            y_pred = list(map(output_dict.get, y_pred, y_pred))
            data["Results"] = y_pred
            utils.write_file(data, save_path=output_file)

    def train(self, batch_size=classifier_constants.TrainingConstants.BATCH_SIZE,
              epochs=classifier_constants.TrainingConstants.EPOCHS,
              input_file=classifier_constants.PathConstants.TRAIN_DATA,
              input_column_name="Text", label_column_name="Label"): # pragma: no cover
        """
        Training pipeline for classifier
        Args:
            batch_size: batch size of the input for training
            epochs: Number of epocchs the model has to be trained on
            input_file: filepath to input file
            input_column_name: The name of the column in which the data is in the input file
            label_column_name: Truth value of the data
        """
        data = utils.read_input(input_file)
        features, target, target_names = utils.label_encode_input_data(data, purpose=self.purpose,
                                                                       input_column_name=input_column_name,
                                                                       true_value_col_name=label_column_name)
        train_features = self.__get_embedding(features)

        if classifier_constants.TrainingConstants.KFOLD_TRAINING:
            self.lstm_classifier.train_model_with_kfold(train_features, target, batch_size=batch_size,
                                                        epochs=epochs,
                                                        fold_n=classifier_constants.TrainingConstants.N_FOLDS)
            # Note that the training time will increase fold_n times
        else:
            self.lstm_classifier.train_model(train_features, to_categorical(target), batch_size=batch_size,
                                             epochs=epochs)


if __name__ == '__main__': # pragma: no cover
    cs = ClassifierEngine()
    result = cs.get_classifier_output("What are the causes of  PE error ?")
    print(result)  # Troubleshooting
    cs = ClassifierEngine()
    result = cs.get_classifier_output("What about the gas specifications for my washer?")
    print(result)  # Specification
