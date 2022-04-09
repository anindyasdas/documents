"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import logging as logger
import os
import sys

logger.debug("cur dir : %s",os.getcwd())

from .dialo_gpt.predict import GPTModel

NLG_GPT = "gpt"
NLG_POINTER_GEN = "pointer_gen"

class NlgEngine(object):
    """
    Interface to Execute nlg interfaces
    """
    def __init__(self, nlg_model_type="gpt"):
        """
        method to generate instance of nlg interface based on nlg_model_type

        Args:
             nlg_model_type : str
                        type of the model to be used for NLG
        Returns:
            None
        """
        self.nlg_model = None
        if nlg_model_type == NLG_GPT:
            self.nlg_model = GPTModel.get_instance()
            logger.debug("GPT based NLG model")
        else:
            logger.debug("Pointer gen based NLG model")
            # TODO get instance from pointer gen

    def get_nlg_output(self,question,answer):
        """
        function to generate nlg answer for the given question and answers

        Args:
            question: str
                      user question
            answer: list
                     predicted answer
        Returns:
            output : str
                     natural answer generated from NLG model
        """
        output = ""
        # TODO answer data type based on dict
        logger.debug("question=%s,answer=%s",question,answer)
        output = self.nlg_model.predict_nlg_for_single(question,answer[0])
        return output

    def get_nlg_for_file(self , ques_file, ans_file , tgt_file=None):
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
        # generate natural answer for file input
        self.nlg_model.predict_nlg_for_file(ques_file, ans_file, tgt_file)

if __name__=='__main__':
    nlg_eng = NlgEngine()
    result = nlg_eng.get_nlg_output("what is the width?","33 cm")
    print(result)

    nlg_eng.get_nlg_for_file("data/news_qa_test.ques","data/news_qa_test.ans","data/news_qa_test.tgt")
    print("file inference is completed")