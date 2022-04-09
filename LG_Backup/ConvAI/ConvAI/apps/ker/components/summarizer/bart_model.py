"""
-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------
@author: anusha.kamath@lge.com
"""
import transformers
import tensorflow as tf
from transformers import BartTokenizer, TFBartForConditionalGeneration
from components.summarizer.utils import SummarizationUtils
from components.summarizer import constants

class BARTSummarizer:
    """
    The BART Model with a language modeling head. Used for summarization.
    """
    def __init__(self):
        """
        Intitializes the pre trained model and tokenizer
        """
        self.tokenizer = BartTokenizer.from_pretrained(constants.TOKENIZER_PATH, local_files_only=True)
        self.summ_model = TFBartForConditionalGeneration.from_pretrained(constants.MODEL_PATH, local_files_only=True)

    def summarize_single_text(self, text):
        """
        Summarization of a single text of data
        @Args:
              text : input string for evaluation
        Returns:
              summary for the input text
        """
        text = str(text.replace('\n', ' ')) #to avoid unwanted '\n' while copying text from pdf manuals
        article_input_ids = self.tokenizer.batch_encode_plus([text], return_tensors='tf',
                                                             max_length=1024,
                                                             truncation=True)['input_ids']
        #TBD- Moving constants to a file
        summary_ids = self.summ_model.generate(article_input_ids, do_sample=True, max_length=45,
                                               top_p=0.90)
        #TBD- Moving constants to a file
        #The constants in the function are reported as the best suited values for our problem
        summary_txt = self.tokenizer.decode(tf.squeeze(summary_ids), skip_special_tokens=True)
        return summary_txt
