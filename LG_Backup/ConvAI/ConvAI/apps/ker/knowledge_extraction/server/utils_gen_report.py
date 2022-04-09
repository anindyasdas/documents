"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com,senthil.sk@lge.com
"""
import csv
import os.path
import pandas
import logging as logger
import copy
import sys
import os
import json
from os.path import splitext as os_spt

REPORT_CSV_FILE = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + \
                  '/report/QA_test_history.csv'

FIELDS = ['User Question', 'Output Question', 'Answer']
TEST_REPORT_FIELDS = ['Question', 'Expected Answer', 'System Answer', 'Extracted Info']
CSV_WRITER = None
FILE_FD = None
SUPPORTED_FORMAT = [".csv", ".xlsx"]


def check_report_exists():
    """
        checks the report file exists or not
        Args:
            None
        Returns:
            True - if exists
            False - if not exists
    """
    if os.path.isfile(REPORT_CSV_FILE):
        logger.debug("File exist")
        return True
    else:
        logger.debug("File not exist")
        return False


def create_report():
    """
        create the csv report file with defined column headers
        Args:
            None
        Returns:
            None
    """
    global REPORT_CSV_FILE
    global FIELDS
    global CSV_WRITER
    global FILE_FD

    FILE_FD = open(REPORT_CSV_FILE, 'a')
    # creating a csv writer object
    CSV_WRITER = csv.DictWriter(FILE_FD, fieldnames=FIELDS)
    CSV_WRITER.writeheader()


def write_entry(user_question, template_ques, answer):
    """
        writes the csf report file with all fields
        Args:
            user_question : str
            template_ques : str
            answer : str
        Returns:
            None
    """
    global FIELDS
    global CSV_WRITER

    try:
        if CSV_WRITER:
            logger.debug("Writing entry ;file has valid writer")
        else:
            logger.debug("Writing entry ;file has no valid writer")

        # writing row
        CSV_WRITER.writerow({FIELDS[0]: user_question, FIELDS[1]: template_ques,
                             FIELDS[2]: answer})
    except Exception as e:
        logger.debug("Write entry:%s" + str(e))


def open_report():
    """
        checks the report file exists and create if not exists
        If exists,open the report file
        Args:
            None
        Returns:
            None
    """
    global CSV_WRITER
    global FILE_FD

    if check_report_exists() == True:
        FILE_FD = open(REPORT_CSV_FILE, 'a')
        # creating a csv writer object
        CSV_WRITER = csv.DictWriter(FILE_FD, fieldnames=FIELDS)
        logger.debug("csv opened")
    else:
        create_report()
        logger.debug("csv created")

    if CSV_WRITER:
        logger.debug("csv file opened")


def close_report():
    """
        close the report file
        Args:
            None
        Returns:
            None
    """
    global FILE_FD
    if FILE_FD:
        logger.debug("report is closing")
        FILE_FD.close()


def testandupdate_report(report_path, obj, input_json, client_type):
    """
        tests the given file and writes back the results in the same file
        Args:
            report_path - path of test file to be tested
            obj - knowledge retriever object to test
            input_json : dict
            client_type : int
                          html/rcs/kms
        Returns:
            None
    """
    questions = []

    try:
        ext = os_spt(report_path)[1]
        if ext == SUPPORTED_FORMAT[0]:
            data_df = pandas.read_csv(report_path, header=[0], encoding="utf-8")
        elif ext == SUPPORTED_FORMAT[1]:
            data_df = pandas.read_excel(report_path, header=[0])
        questions = data_df[TEST_REPORT_FIELDS[0]].tolist()
        logger.debug("question list : %s",questions)
        data_df[TEST_REPORT_FIELDS[2]] = ''
        data_df[TEST_REPORT_FIELDS[3]] = ''
    except Exception as e:
        logger.error("Error:Reading error in csv :" + str(e))
        return

    try:
        logger.debug("Testing for Bulk:") 
        for i in range(len(questions)):
            request = copy.deepcopy(input_json)
            request["question"] = questions[i]
            query_response = obj.process_request(request, client_type)
            # extract specific details from response
            answer, extract_info = query_response["answer"], query_response["extracted_info"]
            data_df.loc[i,TEST_REPORT_FIELDS[2]] = answer
            data_df.loc[i,TEST_REPORT_FIELDS[3]] = json.dumps(extract_info,  ensure_ascii=False)
        if ext == SUPPORTED_FORMAT[0]:
            data_df.to_csv(report_path, index=False, encoding="utf-8")
        elif ext == SUPPORTED_FORMAT[1]:
            data_df.to_excel(report_path, index=False, encoding = "utf-16")
        return
    except Exception as e:
        logger.exception("Error:Updating report in csv : " + str(e))
        return
