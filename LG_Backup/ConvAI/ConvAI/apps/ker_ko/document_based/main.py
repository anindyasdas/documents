# -------------------------------------------------
# Copyright(c) 2021-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------

from flask import Flask, request
from .ker_interface import KerInterface
from apps.ker_ko.knowledge_extraction.constants import params as cs
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

app = Flask(__name__)
doc_based_search_engine = KerInterface()


@app.route('/get_graph_output', methods=['POST'])
def get_graph_output():
    if request.method == "POST":
        logger.debug("request : %s", request)
        req_json = request.get_json()
        logger.debug("req_json : %s", req_json)
        question = req_json["question"]
        part_no = req_json["part_no"]
        result = doc_based_search_engine.get_mapped_keys_and_scores(question, part_no)
        result_dict = dict()
        result_dict["response"] = result
        return result_dict


@app.route('/get_doc_retrieval_output', methods=['POST'])
def get_doc_retrieval_output():
    if request.method == "POST":
        logger.debug("request : %s", request)
        req_json = request.get_json()
        logger.debug("req_json : %s", req_json)
        matched_key = req_json["matched_key"]
        question = req_json["question"]
        part_no = req_json["part_no"]
        result = doc_based_search_engine.get_doc_retrieval_output(matched_key, question, part_no)
        result_dict = dict()
        result_dict["response"] = result
        return result_dict


@app.route('/get_manual_keys', methods=['POST'])
def get_manual_keys():
    if request.method == "POST":
        logger.debug("request : %s", request)
        req_json = request.get_json()
        logger.debug("req_json : %s", req_json)
        section = req_json["section"]
        part_no = req_json["part_no"]
        results = doc_based_search_engine.view_manual_content(section=section, part_no=part_no)
        result_dict = dict()
        result_dict[cs.IOConstants.RESP_CODE] = cs.ExternalErrorCode.MKG_SUCCESS
        result_dict[cs.IOConstants.ANSWER] = {}
        for result in results:
            result_dict[cs.IOConstants.ANSWER].update({result: "doc"})
        return result_dict
        

@app.route('/get_manual_passages', methods=['POST'])
def get_manual_passages():
    if request.method == "POST":
        logger.debug("request : %s", request)
        req_json = request.get_json()
        logger.debug("req_json : %s", req_json)
        result_dict = dict()
        result= doc_based_search_engine.get_passages()
        result_dict["response"] = result
        return result_dict


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    ip = '0.0.0.0'
    logger.debug("Starting docsearch..........")
    app.run(host=ip, port=8007)
    logger.debug("Starting docsearch started..........")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/