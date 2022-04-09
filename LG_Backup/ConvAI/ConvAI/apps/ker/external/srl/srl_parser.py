"""
-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
-------------------------------------------------
"""
import logging

from allennlp.predictors.predictor import Predictor
import pandas as pd
from ...components.engine import constants as engine_constants
from . import constants as srl_constants
from ..os_tools import uncompress_tool as tool
import sys


class SRLWrapper:
    """
    Semantic Role Labeller class.
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if SRLWrapper.__instance is None:
            SRLWrapper()
        return SRLWrapper.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if SRLWrapper.__instance is not None:
            raise Exception("Semantic Role Labeller Wrapper is not instantiable")
        else:
            SRLWrapper.__instance = self
        self.__check_model_files()
        self.predictor = Predictor.from_path(srl_constants.MODEL, import_plugins=False)

    def __check_model_files(self):
        """
        check if the model file is present
        """
        check = tool.extract_compressed_files(srl_constants.MODEL_PATH,
                                              srl_constants.MODEL_NAME,
                                              srl_constants.MODEL_NAME)
        if not check:
            logging.error("Model zipped model file does not exist ")
            sys.exit()

    def get_srl_ouput(self, eval_text):
        """
        Output for a single sentence.
        Args:
             eval_text: Sentence to be evaluated.
        Returns: output in the form of list of strings
        """
        pred_dict = self.predictor.predict(sentence=eval_text)
        return self.__post_processor(pred_dict)

    def get_srl_output_for_ker(self, eval_text):
        """
        Output for a single sentence for graph population.
        Args:
             eval_text: Sentence to be evaluated.
        Returns: returns a dictionary of output necessary for graph population
        """
        pred_dict = self.predictor.predict(sentence=eval_text)
        post_processed_op = self.__post_processor(pred_dict)
        to_return = self.__post_processor_for_ker(post_processed_op)
        logging.log(engine_constants.LG_LOGGING_MODULE_OUTPUT_LVL, to_return)
        return to_return

    def __post_processor(self, pred_dict):
        """
        Post process the output and return in the form of dictionary
        Args:
            pred_dict: Output from predicted output.

        Returns:
               verb: semantic roles dictionary
               eg.{'operated': {'B-ARG1':'washer','B-ARGM-MNR':'completely closing the drawer'},
                   'closing':  {'B-ARGM-EXT': '.', 'B-ARG1': 'drawer'}
                  }
        """
        srl_output = {}
        tokens = pred_dict["words"]
        for idx in pred_dict["verbs"]:
            if idx["verb"] not in srl_constants.AUX_LIST:  # Comment this line if auxilary VERB is to be included
                val = self.__extract_tag(tokens, idx["tags"])
                srl_output[idx["verb"]] = val
        return srl_output

    def __post_processor_for_ker(self, pred_dict):
        """
        Post process the output and return in th form of dictionary for graph population
        Args:
            pred_dict: Output from prediction of SRL after post processing.

        Returns:
               verb: semantic roles dictionary
               eg.{'temp': ['completely closing the drawer','when the washer'],
                   'purpose':  ['because of'],
                   'cause':['because of']
                  }
        """
        rdf_op = {}
        rdf_op['temp'] = []
        rdf_op['purpose'] = []
        rdf_op['cause'] = []

        sub_value = pred_dict.values()

        for sub in sub_value:
            if 'B-ARGM-TMP' in sub:
                rdf_op['temp'].append(sub['B-ARGM-TMP'])
            if 'B-ARGM-PRP' in sub:
                rdf_op['purpose'].append(sub['B-ARGM-PRP'])
            if 'B-ARGM-CAU' in sub:
                rdf_op['cause'].append(sub['B-ARGM-CAU'])

        rdf_op['temp'] = '|'.join(rdf_op['temp'])
        rdf_op['purpose'] = '|'.join(rdf_op['purpose'])
        rdf_op['cause'] = '|'.join(rdf_op['cause'])
        return rdf_op

    def __extract_tag(self, words, tags):
        """
        Function to pre process the output for every single verb.
        Args:
          words: list of tokens in the text.
          tags: list of semantic role tags.

        Returns: Dictionary of semantic roles and its values
        """
        srl_op = {}
        role = ""
        value = []
        for word, tag in zip(words, tags):
            if tag == "B-V" or tag == "I-V":  # Ignore VERB semantic role as it is the key of the dict
                continue
            elif tag.startswith("B"):  # Beginning of a semantic role
                if role != "":
                    srl_op[role] = " ".join(value)
                    role = ""
                    value = []
                role = tag
                value.append(word)
            elif tag.startswith("I"):  # Intermediate of a semantic role
                value.append(word)
            elif tag.startswith("O"):  # word not assigned any semantic role
                if role != "":
                    srl_op[role] = " ".join(value)
                role = ""
                value = []
        return srl_op

    def predict_bulk(self, bulk_list):
        """
        Output for a list of sentences.Writes output to a file.
        Args:
             bulk_list: list of sentence to be evaluated.
        Returns: output in the form of list of lists of strings
        """
        bulk_output = []
        for sentence in bulk_list:
            bulk_output.append(self.predict_single(sentence))
        self.__write_file(bulk_list, bulk_output)
        return bulk_output

    def predict_file(self, path):
        input_df = pd.read_excel(path, sheet_name='Sheet1')
        temps = []
        purposes = []
        causes = []
        for t in input_df['Key'].values:
            d = self.get_srl_output_for_ker(t)
            temps.append('|'.join(d['temp']))
            purposes.append('|'.join(d['purpose']))
            causes.append('|'.join(d['cause']))
        input_df['temp'] = temps
        input_df['purpose'] = purposes
        input_df['cause'] = causes
        input_df.to_excel('output.xlsx', sheet_name='Sheet1', index=False)

    def read_file(self, file_name):
        """
        Reads Excel file for input to provide input.
        Args:
             file_name: input file name.
        Returns:
             List of input sentences
        """
        input_df = pd.read_excel(file_name)
        return input_df['Key'].to_list()

    def __write_file(self, eval_list, bulk_output):
        """
        Writes output to a file.
        Args:
             eval_list: list of input sentences
             bulk_output: list of Outputs
        """
        col_names = ['Sentence', 'SRL-output']
        output_df = pd.DataFrame(columns=col_names)

        for idx in range(len(eval_list)):
            output_df.loc[idx, 'Sentence'] = eval_list[idx]
            output_df.loc[idx, 'SRL-output'] = "\n".join([str(x) + ":" + str(y) for (x, y) in bulk_output[idx].items()])
        output_df.to_excel("SRL_output.xlsx")


if __name__ == "__main__":
    srl_object = SRLWrapper.get_instance()
    srl_object.predict_file('output.xlsx')
    '''
    #ans=srl_object.get_srl_output_for_ker("The default dispense amounts setting may need to be charged")
    #print('ans', ans)
    #ans=srl_object.predict_single_graph(eval_text="Why is my washer gives rattling noise when it washes clothes?")
    #print('graph', ans)
    #eval_text=srl_object.read_file("output.xlsx")
    #eval_text=["Water supply faucets are not fully open.","Water inlet hoses are kinked, pinched, or crushed."]
    #ans=srl_object.predict_bulk(eval_text)
    #print (ans)
    '''
