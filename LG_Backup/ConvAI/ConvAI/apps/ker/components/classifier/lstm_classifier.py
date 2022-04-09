"""
--------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
--------------------------------------------------
@Author:anusha.kamath@lge.com
"""
import numpy as np

import tensorflow as tf
import keras
import keras.backend as K

from keras.utils import to_categorical
import logging

from . import constants
from . import classifier_utils as utils


class LstmClassifier:
    """
    Deep learning based classifier with RNN

    Description:
    Sequential model with
    [1] bi-LSTM with n units each
    [2] 1-Dense layer with 64 hidden units
    [3] 1- softmax
    """

    def __init__(self, num_lable=0, evaluate=True, all_models=True, isgeneric=False, hidden_lstm_units=0,
                 purpose="Topic"):
        """
        Args:
            num_lable: number of labels in the classifier
            evaluate: boolean to indicate if the object is to be created for training or evaluation
            all_models: boolean to indicate if the object need to load all the KER classifiers or not
            isgeneric: boolean to indicate if it is a generic classifier or KER classifier
            hidden_lstm_units: Number of hidden units for Bi-LSTM
            purpose: Purpose of KER classifier to be used in Training or Testing
        """
        self.isgeneric = isgeneric
        if evaluate:
            # if the object is created for evaluation purpose
            if evaluate:
                if self.isgeneric:
                    self.__initialize_generic_model()
                else:
                    self.__initialize_ker_model(all_models=all_models, purpose=purpose)
        else:
            # if the object is created for training purpose
            self.graph = tf.Graph()
            self.sess = tf.Session(graph=self.graph)
            self.num_lable = num_lable
            with self.sess.as_default():
                with self.graph.as_default():
                    self.__build_model(hidden_lstm_units)

    def __initialize_ker_model(self, all_models, purpose=None):
        """
        Private function to initialise KER modules
        Args:
            all_models: boolean to indicate if the object need to load all the KER classifiers or one
            purpose: Purpose of KER classifier to be used in Training or Testing
        """
        if all_models:
            self.graph = [tf.Graph(), tf.Graph(), tf.Graph(), tf.Graph(), tf.Graph()]
            self.sess = [tf.Session(graph=gi) for gi in self.graph]
            self.model_list = []
            model_ck_list = [constants.KerModelConstants.TOPIC_DATA_LSTM, constants.KerModelConstants.INTENT_DATA_LSTM,
                             constants.KerModelConstants.TYPE_DATA_LSTM,
                             constants.KerModelConstants.FOLLOW_UP_DATA_LSTM,
                             constants.KerModelConstants.SECTION_DATA_LSTM]

            for i in range(len(model_ck_list)):
                with self.sess[i].as_default():
                    with self.graph[i].as_default():
                        self.model_list.append(tf.keras.models.load_model(model_ck_list[i]))
                        self.model_list[i].compile(loss="categorical_crossentropy", optimizer="adam",
                                                   metrics=['acc'])
        else:
            evaluation_model = constants.KerMappingDictionary.MODEL_CK_MAPPING[purpose]

            self.graph = tf.Graph()
            self.sess = tf.Session(graph=self.graph)
            with self.sess.as_default():
                with self.graph.as_default():
                    self.model = tf.keras.models.load_model(evaluation_model)
                    self.model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=['acc'])

    def __initialize_generic_model(self):
        """
        private function to build the classifier graph
        """
        self.graph = tf.Graph()
        self.sess = tf.Session(graph=self.graph)
        with self.sess.as_default():
            with self.graph.as_default():
                print("Generic model loads")
                self.model = tf.keras.models.load_model(constants.GenericModelConstants.GENERIC_MODEL)
                self.model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=['acc'])

    def __build_model(self, hidden_lstm_units): # pragma: no cover
        """
        function that build the classifier model graph
        Args:
            hidden_lstm_units: Number of hidden units in Bi-LSTM
        """
        self.model = keras.Sequential()
        self.model.add(
            keras.layers.Bidirectional(
                keras.layers.LSTM(input_shape=[None, None, 768], units=hidden_lstm_units, return_sequences=True,
                                  dropout=0.1, recurrent_dropout=0.1)))
        # Best among dropout= 10%, 20% #recurrent_dropout= 10%, 20%
        self.model.add(keras.layers.GlobalMaxPool1D())
        self.model.add(keras.layers.Dense(128, activation=tf.nn.relu))
        self.model.add(keras.layers.Dense(32, activation=tf.nn.relu))
        self.model.add(keras.layers.Dropout(0.2))  # Best among 0%,20%,50% dropout
        self.model.add(keras.layers.Dense(self.num_lable, activation=tf.nn.softmax))
        self.model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=['accuracy'])
        if constants.FunctionConstants.PRINT_SUMMARY:
            self.model.build([None, None, 768])
            self.model.summary()

    def train_model(self, train_features, train_labels, batch_size=100, epochs=50): # pragma: no cover
        """
        function to do training of the classifier model
        Args:
            train_features: Embedding (x) features for the model
            train_labels: Target labels (y)  features for the module
            batch_size: batch size for training
            epochs:No. of epochs for training the module

        Returns:

        some functions that can help in training can be used
        #early_stopping_callback = callbacks.EarlyStopping(monitor="val_loss", patience=10, verbose=1,
                                                          mode="auto", restore_best_weights=True)
        #learning_rate_callback = callbacks.ReduceLROnPlateau(monitor="val_loss", patience=10, verbose=1,
                                                             factor=0.2)

        # Either use Keras callbacks (with desired parameters) and stop training automatically
        # or observe the best epoch from loss accuracy graph and train for so many epochs
        # self.model.fit(train_features, train_labels, validation_split=0.10, epochs=50,
        # verbose=1, callbacks=[early_stopping_callback, learning_rate_callback])

        """
        train_features, train_labels = utils.shuffle_data(train_features, train_labels)
        with self.sess.as_default():
            with self.graph.as_default():
                his = self.model.fit(train_features, train_labels, validation_split=.1, epochs=epochs,
                                     batch_size=batch_size, verbose=1)
                if self.isgeneric:
                    self.model.save(constants.GenericModelConstants.GENERIC_MODEL)
                else:
                    self.model.save(constants.KerModelConstants.SAVE_MODEL_LSTM)
        if constants.FunctionConstants.PLOT_GRAPHS:
            print("Plotting graphs")
            utils.plot_history(his)

    def train_model_with_kfold(self, train_features, train_labels, batch_size=5, epochs=50, fold_n=10): # pragma: no cover
        """
        Model training with k fold validation
        Args:
            train_features: X features for the model
            train_labels: Y labels for the model
            fold_n : Number of folds for validation
        """
        from sklearn.model_selection import StratifiedKFold
        train_features, train_labels = np.array(train_features), np.array(train_labels)
        seed = 7  # Seed value is set to a constant for the reproducabily of results
        fold = 1  # intialization of fold
        cvscores = []
        kfold = StratifiedKFold(n_splits=fold_n, shuffle=True, random_state=seed)
        with self.sess.as_default():
            with self.graph.as_default():
                for train, test in kfold.split(train_features, train_labels):
                    self.model.fit(train_features[train], to_categorical(train_labels[train]), epochs=epochs,
                                   batch_size=batch_size, verbose=1)
                    scores = self.model.evaluate(train_features[test], to_categorical(train_labels[test]),
                                                 verbose=0)
                    self.model.save(constants.KerModelConstants.SAVE_MODEL_LSTM + str(fold))
                    fold = fold + 1
                    cvscores.append(scores[1] * 100)
        k_fold_results = str(np.mean(cvscores)) + "% +/- (" + str(np.std(cvscores)) + ")"
        print(k_fold_results)
        logging.log(logging.INFO, k_fold_results)

    def evaluate_model(self, test_features): # pragma: no cover
        """
        function for multiple entry prediction
        Args:
            test_features: list of inputs for testing the model

        Returns:
            predicted category for a list of inputs

        """
        with self.sess.as_default():
            with self.graph.as_default():
                pred = self.model.predict(test_features)
        return np.argmax(pred, axis=1)

    def __evaluate_with_debug(self, sentences_test, sentences_train, test_features, train_features, wrong_ids): # pragma: no cover
        """
        To be implemented
        function to get the debugging output for failed cases.
        Args:
            sentences_test: test sentences
            sentences_train: train-set sentences
            test_features: embeddings for test set sentences
            train_features: embeddings for train set sentences
            wrong_ids: ids of sentences that are wrongly classified
        """
        if len(wrong_ids) < 1:
            logging.log(logging.INFO, "The model has classified all the rows correctly")
        else:
            from .debugger import Similarity
            debugger = Similarity()
            with self.sess.as_default():
                with self.graph.as_default():
                    train_vec = self.__intemediate_op(train_features)
                    test_vec = self.__intemediate_op(test_features[wrong_ids])
            train_vec = np.squeeze(train_vec, axis=0)
            test_vec = np.squeeze(test_vec, axis=0)
            sentences_test = np.array(sentences_test)[wrong_ids]
            debugger.compute_top_influence(test_sentence=sentences_test, test_vec=test_vec,
                                           train_sentence=sentences_train, train_vec=train_vec, k=5)

    def predict_single(self, test_features, purpose="None"):
        """
        Function to predict for single input
        Args:
            test_features: the input features
            purpose:  the type of classifier (query intent/ query topic)

        Returns:
                Returns classifier output
        """
        if self.isgeneric:
            with self.sess.as_default():
                with self.graph.as_default():
                    pred = self.model.predict(test_features)
            return np.where(pred[0] == np.amax(pred[0]))[0][0]
        else:
            if purpose == constants.KerStringConstants.TOPIC:
                with self.sess[0].as_default():
                    with self.graph[0].as_default():
                        pred = self.model_list[0].predict(test_features)
                return np.where(pred[0] == np.amax(pred[0]))[0][0]
            elif purpose == constants.KerStringConstants.INTENT:
                with self.sess[1].as_default():
                    with self.graph[1].as_default():
                        pred = self.model_list[1].predict(test_features)
                return np.where(pred[0] == np.amax(pred[0]))[0][0]
            elif purpose == constants.KerStringConstants.TYPE:
                with self.sess[2].as_default():
                    with self.graph[2].as_default():
                        pred = self.model_list[2].predict(test_features)
                return np.where(pred[0] == np.amax(pred[0]))[0][0]
            elif purpose == constants.KerStringConstants.FOLLOW_UP:
                with self.sess[3].as_default():
                    with self.graph[3].as_default():
                        pred = self.model_list[3].predict(test_features)
                return np.where(pred[0] == np.amax(pred[0]))[0][0]
            elif purpose == constants.KerStringConstants.SECTION:
                with self.sess[4].as_default():
                    with self.graph[4].as_default():
                        pred = self.model_list[4].predict(test_features)
                return np.where(pred[0] == np.amax(pred[0]))[0][0]

    def __intemediate_op(self, data, n=2): # pragma: no cover
        """
        Private function to get the intermediate output (from any layer) in the Dl model.
        Args:
            data: data to be passed an input
            n: The index number of the layer
        Returns N th layer output from the model
        """
        get_nth_layer_output = K.function([self.model.layers[0].input, K.learning_phase()],
                                          [self.model.layers[n].output])
        nth_layer_output = get_nth_layer_output([data, 1.0])  # Training phase = 1.0 for testing, 0.0 for training
        return nth_layer_output


if __name__ == '__main__': # pragma: no cover
    print("please run ConvAI/classifier_testsuite.py or ConvAI/classifier_trainsuite.py to run the class")
