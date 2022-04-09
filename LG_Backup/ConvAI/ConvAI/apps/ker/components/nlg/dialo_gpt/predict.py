"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import logging as logger
import os

import pandas as pd
from transformers import AutoModelWithLMHead, AutoTokenizer
import torch

current_folder = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','..','dataset')) + '/'
MODEL_PATH = current_folder + 'models/nlg/gpt'
OUTPUT_FILE = "results.csv"

class GPTModel(object):
    """
    Interface to Execute dialo gpt model methods
    """
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if GPTModel.__instance is None:
            GPTModel()
        return GPTModel.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if GPTModel.__instance is not None:
            logger.error("GPTModel is not instantiable")
            raise Exception("GPTModel is not instantiable")
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            #__tokenizer.save_pretrained(MODEL_PATH)
            self.model = AutoModelWithLMHead.from_pretrained(MODEL_PATH)
            GPTModel.__instance = self

    def __processing_dataset(self,input_file):
        """
        preprocess the input data like removing extra spaces
        :param input_file: input file path
        :return: list of preprocessed entries
        """
        arr = []
        with open(input_file, "r") as f:
            for line in f:
                out_line = " ".join(line.strip().split(' '))
                arr.append(out_line)
        return arr

    def __get_natural_answer(self, ques, ans):
        """
        Generates natural answer for the given ques and answer

        :param ques: str
        :param ans: str
        :return: output : str
        """
        if isinstance(ans, list):
            ans = ''.join(ans)
        new_user_input_ids = self.tokenizer.encode(ques + self.tokenizer.eos_token, return_tensors='pt')
        new_user_fa_input_ids = self.tokenizer.encode(ans + self.tokenizer.eos_token, return_tensors='pt')
        bot_input_ids = torch.cat([new_user_fa_input_ids, new_user_input_ids], dim=-1)

        # Generate natural answer based on sentence token id and limiting to 200 tokens
        # TODO: should check possible values no_repeat_ngram_size,top_k,top_p,temperature,max_length
        #  for best response generation
        chat_history_ids = self.model.generate(
            bot_input_ids, max_length=200,
            pad_token_id=self.tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
            do_sample=True,
            top_k=100,
            top_p=0.7,
            temperature=0.8
        )
        output = self.tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
        return output

    def predict_nlg_for_single(self, ques, answer):
        """
        calls method to get natural answer for the given ques and answer
        and returns it

        :param ques: str
        :param answer: list
        :return: output : str
        """
        output = self.__get_natural_answer(ques,answer)
        return output

    def predict_nlg_for_file(self , ques_file, ans_file , tgt_file=None):
        """
        calls method to get natural answer for the given file
        and returns it

        Args:
            ques_file: str
                    text file that has questions new line separated
            ans_file: str
                    text file that has answers new line separated
            tgt_file: str
                    text file that has target answers new line separated
        Returns:
             output csv file will be created
        """
        ques = self.__processing_dataset(ques_file)
        ans = self.__processing_dataset(ans_file)
        target = self.__processing_dataset(tgt_file)

        pred_ans = []
        for i in range(len(ques)):
            each_ans = self.__get_natural_answer(ques[i],[ans[i]])
            pred_ans.append(each_ans)

        # writing to csv file with column headers
        df_test_qa = pd.DataFrame(ques,columns = ['Ques'])
        df_test_qa.insert(1,'fa_ans',ans)
        df_test_qa.insert(2,'target',target)
        df_test_qa.insert(3,'pred_ans',pred_ans)
        df_test_qa.to_csv(OUTPUT_FILE,index=False)

if __name__ == "__main__":
    model = GPTModel.get_instance()

    # test for single query
    nlg_answer = model.predict_nlg_for_single("What is the width of my product?",["33 cm"])
    print(nlg_answer)
    nlg_answer = model.predict_nlg_for_single("Let me know the width of my product",["33 cm"])
    print(nlg_answer)
    nlg_answer = model.predict_nlg_for_single("What about the width of my product?",["33 cm"])
    print(nlg_answer)
    nlg_answer = model.predict_nlg_for_single("Could you tell me the width of my appliance?",["33 cm"])
    print(nlg_answer)
    nlg_answer = model.predict_nlg_for_single("Can you tell me the width of my appliance?",["33 cm"])
    print(nlg_answer)
    nlg_answer = model.predict_nlg_for_single("what is the solution?",['The use of hoses designed to limit leaks is not recommended.',
                         'If flow is too low, contact a plumber.', 'Contact a plumber.',
                         'Contact a plumber2.'])
    print(nlg_answer)
