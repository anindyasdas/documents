"""
-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------
@author: anusha.kamath@lge.com
"""
import os
import pandas as pd
import xlsxwriter

class SummarizationUtils:
    def read_excel(file_name):
        """
        Read from an excel file
        @Args:
            filename: File name to be read
        Returns:
            a dataframe of read file
        """
        df = pd.read_excel(file_name)
        return df

    def write_output(file_name, output_list, sheetname="outputs"):
        """
        Writes output to an excel file
        @Args:
              filename: File name of output file
              output_list: list of outputs
              sheetname: name of the sheet if necessary
        """
        writer_obj = pd.ExcelWriter(file_name, engine='xlsxwriter')
        df = pd.DataFrame(output_list, columns=['Output'])
        df.to_excel(writer_obj, sheet_name=sheetname)
        writer_obj.save()