"""
-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------
@author: anusha.kamath@lge.com
"""
from components.summarizer.bart_model import BARTSummarizer
from components.summarizer.utils import SummarizationUtils

class SummarizationEngine:
    """Engine class to run summarization modules. Supports single and file inputs"""
    def __init__(self):
        self.evaluation_model=BARTSummarizer()

    def get_summarized_output(self, single_input=True, eval_text=None, input_file=None,
                              output_file=None):
        """
        Function to get summarized ouput from the model.
        @Args:
              single_input: Boolean to indicate if the input is str or to be read from file
              eval_text : Evaluation string if single output
              input_file : path to input file if input is file-read
              outut_file: path to output file
        Return:
              Returns summarized text in case of single input
        """
        if single_input:
            #TBD - if input is empty, valid
            return self.evaluation_model.summarize_single_text(text=eval_text)
        else:
            #TBD - check if file exists in the path
            df = SummarizationUtils.read_excel(input_file)
            output_list = []
            for idx in df.index:
                summ_op =self.evaluation_model.summarize_single_text(text =df['inputs'][idx])
                output_list.append(summ_op)
            SummarizationUtils.write_output(output_file, output_list=output_list)

if __name__=='__main__':
    c = SummarizationEngine()
    c.get_summarized_output(single_input=False, input_file ="manual_inputs.xlsx", output_file="output.xlsx")