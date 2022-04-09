import argparse
import os
import pandas as pd
import sys
import time
from components.summarizer.summerization_engine import SummarizationEngine
from pandas import ExcelWriter


class SummarizationTester:
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if SummarizationTester.__instance is None:
            SummarizationTester()
        return SummarizationTester.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if SummarizationTester.__instance is not None:
            raise Exception("SummarizationTester is not instantiable")
        else:
            SummarizationTester.__instance = self
        self.initialize()

    def initialize(self):
        """
        function to initialise the NER engine object that gives NER output and argument parser object"""
        self.summarization_engine_obj = SummarizationEngine()
        self.arg_parser = argparse.ArgumentParser()

    def get_data_excel(self, file_path):
        """
        Read data from excel. TBD: Optimised
        @file_path : Input file to be read
        Returns: 
            list of sentences from input file
        """
        df = pd.read_excel(file_path)
        train_x = df['Text'].values.tolist()  # df["Text"].to_list()
        return train_x


if __name__ == "__main__":
    start = time.time()
    tester_obj = SummarizationTester.get_instance()
    tester_obj.arg_parser.add_argument("--run_time_input",
                                       default=True,
                                       help="True if input_data is passed on runtime through keyboard, only a sample at a time")
    tester_obj.arg_parser.add_argument("--input_filepath",
                                       default="manual_inputs.xlsx",
                                       help="Path to input file to feed the model ")
    tester_obj.arg_parser.add_argument("--output_filepath",
                                       default="output.xlsx",
                                       help="Path to output file with predictions from the model ")

    p_args = tester_obj.arg_parser.parse_args()
    if (p_args.run_time_input == False and p_args.input_filepath == None and p_args.output_filepath == None):
        print('Neither data object is passed nor data file path; one of these should be passed');
        sys.exit(0)

    if p_args.run_time_input == True:
        flag = "y"
        while flag == "y":
            eval_text = input("Please enter the tesxt to summarise")
            print(tester_obj.summarization_engine_obj.get_summarized_output(single_input=True, eval_text=eval_text))
            flag = input("Do you want to continue ? (y/n)")
    else:
        if not os.path.exists(p_args.input_filepath):
            print('Input file does not exist');
            sys.exit(0)
        tester_obj.summarization_engine_obj.get_summarized_output(single_input=False, input_file=p_args.input_filepath,
                                                                  output_file=p_args.output_filepath)
        print('Results are written successfully to Excel File.')

    end = time.time() - start
    print('Time taken', end)
