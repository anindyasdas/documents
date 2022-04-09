"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com,senthil.sk@lge.com
"""
import logging as logger
import os
import os.path
import sys
from configparser import ConfigParser
import copy
import jinja2
import pandas as pd
from flask import Flask, render_template, request, json, send_file, jsonify
from werkzeug.utils import secure_filename
import requests
import lg_logging

# To be moved to __main__ provided there is no other code executed before it.
lg_logging.SpecialHandler.set_default_logging()

from . import utils_gen_report as report
from ..response.json_builder import WidgetConstants
from ..constants import params as cs
from ...ker_engine import KerEngine


CONFIG_PATH = (os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 '..', 'config', 'configuration.ini')))

config_parser = ConfigParser()
config_parser.read(CONFIG_PATH)
port_number = config_parser.get("server_config", "port_number")
hosting_path = config_parser.get("image_db", "image_db_path")

print("2 sys path", sys.path)
UPLOAD_FOLDER = (os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 '..', '..', 'dataset', 'bulk_test_data/')))
app = Flask(__name__, static_folder='image_db')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

TEMPLATE_FOLDER = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/templates/"
my_loader = jinja2.ChoiceLoader([app.jinja_loader, jinja2.FileSystemLoader(TEMPLATE_FOLDER), ])
app.jinja_loader = my_loader

INFO_EXTRACTION = '2'
TEXT_SIMILARITY = '1'
KER_ENGINE = KerEngine.get_instance()
# open test history report
report.open_report()

# constants used for parsing json message from Web UI
QUERY = "question"
MODEL_NO = "model_no"
KER_CNTXT = "ker_context"
REQ_ID = "request_id"
USE_INFO = "use_info"
QUERY_TOPIC = "ques_topic"
QUERY_LEVEL = "question_level"
EMPTY_TEXT = "Dummy"
RESP_QUES = 'Question'
RESP_ANS = 'Answer'
RESPONSE_STR = "Response"
INFOEXTRACT_COMP = "Info Extraction"
TEXTSIMI_COMP = "Text Similarity"
PRODUCT_TYPE = "product_type"
MODEL_CHANGE = "model_change"

# html files path
KER_HTML = "spec_trob.html"
SPEC_HTML = "specification.html"
TS_HTML = "troubleshooting.html"
FAQ_HTML = "faq.html"
UPDATE_PREF_HTML = "updatepref.html"
KER_HYBRID_HTML = "ker_hybrid.html"

# store previous product,current product
CUR_PROD = None
PREV_PROD = None

# models list for all products
MODELS_LIST = {}

INPUT_JSON = {
    "request_id": 1,
    "question": "",
    "model_no": "",
    "ker_context": {},
    "classifier_info": {},
    "similarity_key": []
}

def get_product_models():
    """
        get all the model nos  for all product types
        Args:
            none
        Returns:
            none
    """
    global MODELS_LIST
    # get all models for all products
    MODELS_LIST = KER_ENGINE.get_product_models()
    logger.info("----get_product_models model list=(%s)" % str(MODELS_LIST))


# update models list
get_product_models()

@app.route('/')
def homepage():
    """
        Defines the HTTP REST API to load HTML UI home page
    """
    return "Home Page. Execute url http://<ip>:port/ker_ts to reach QA Test \
            Interface page"


@app.route('/display_updatepref')
def display_updatepref():
    """
        Defines the HTTP REST API to communicate all models
        to send to pref UI page
    """
    global MODELS_LIST

    logger.info("display update pref=(%s)" % str(MODELS_LIST))
    # returning models info back to pref html page
    return render_template(UPDATE_PREF_HTML, models=json.dumps(MODELS_LIST))


# For Updating prefs
@app.route('/update_pref', methods=['POST', 'GET'])
def update_pref():
    """
        Defines the HTTP REST API to communicate back end for update
        preference
    """
    if request.method == 'POST':
        # Send the updated preferences
        try:
            json_obj = request.get_json()
            final_response = ""
            rest_response = KER_ENGINE.update_product_pref(json_obj)
            if rest_response != cs.SUCCESS:
                final_response = "<p>UPDATE FAILED</p>"
            else:
                final_response = "<p>UPDATE SUCCESS</p>"
            return final_response

        except Exception as e:
            logger.exception("Exception in demo" + str(e))


# For Resetting prefs
@app.route('/reset_pref', methods=['POST', 'GET'])
def reset_pref():
    """
        Defines the HTTP REST API to communicate back end to reset
        preferences
    """
    if request.method == 'POST':
        # Send the updated preferences
        try:
            final_response = ""
            rest_response = KER_ENGINE.reset_preference()
            if rest_response != cs.SUCCESS:
                final_response = "<p>RESET FAILED</p>"
            else:
                final_response = "<p>RESET SUCCESS</p>"
            return final_response

        except Exception as e:
            logger.exception("Exception in demo" + str(e))


# For getting the context preferences
@app.route('/get_pref', methods=['POST', 'GET'])
def get_pref():
    """
        Defines the HTTP REST API to communicate back end to get the
        current preferences
    """
    global CUR_PROD, PREV_PROD
    pref_resp = {}
    if request.method == 'POST':
        # Send the updated preferences
        try:
            json_response = dict(KER_ENGINE.get_context())
            logger.debug("json_response : %s ", json_response)
            # pop out and store the previous product info and show it as current context
            CUR_PROD = json_response.pop('pre_product', None)
            print("CUR_PROD", CUR_PROD)
            print("PREV_PROD", PREV_PROD)
            # if current context is empty or none
            if CUR_PROD is None or len(CUR_PROD.strip()) <= 0:
                html_return = "Current Product: {}".format("None")
                return html_return
            if PREV_PROD is None:
                PREV_PROD = CUR_PROD
            print("CUR_PROD", CUR_PROD)
            print("PREV_PROD", PREV_PROD)

            pref_resp[CUR_PROD] = json_response[CUR_PROD]

            gfg = pd.DataFrame(pref_resp)
            html_return = gfg.to_html()
            html_return = html_return.replace("\n", "")
            html_return = html_return + "<br><br>Current Product: {}".format(CUR_PROD)

            if CUR_PROD != PREV_PROD:
                html_return = html_return + "<br><br>Previous Product: {}".format(PREV_PROD)
            # updating cur product to prev product
            PREV_PROD = CUR_PROD
            return html_return

        except Exception as e:
            logger.exception("Exception in demo" + str(e))


@app.route('/ker_updated_thinq', methods=['POST', 'GET'])
def get_updated_thinq_settings():
    """
    get the updated thinq settings
    """
    dict_var = KER_ENGINE.get_thinq_settings()
    prd = []
    model = []
    final_dict = {}
    for key in dict_var.keys():
        prd.append(key)
        model.append(dict_var[key][0])
    final_dict["Product"] = prd
    final_dict["Model"] = model
    gfg = pd.DataFrame(final_dict)
    html_return = gfg.to_html()
    return html_return


@app.route('/ker_clear_thinq', methods=['POST', 'GET'])
def reset_thinq_settings():
    """
    reset thinq settings
    """
    dict_var = KER_ENGINE.clear_thinq_settings()
    prd = []
    model = []
    final_dict = {}
    if dict_var:
        for key in dict_var.keys():
            prd.append(key)
            model.append(dict_var[key][0])
        final_dict["Product"] = prd
        final_dict["Model"] = model
        gfg = pd.DataFrame(final_dict)
        html_return = gfg.to_html()
        return html_return
    else:
        final_dict["Product"] = None
        final_dict["Model"] = None
        html_return = "<p> Clear success </p>"
        return html_return


@app.route('/ker', methods=['POST', 'GET'])
def demo_spec_ts():
    """
    Defines the HTTP REST API to communicate Spec queries from browser to
    python interface.
    It returns the answer in json format to HTML UI page
    """
    try:
        sentence = ""
        if request.method == 'POST':

            question = request.get_data().decode()
            logger.debug("question from html=%s"%str(question))
            input_json = copy.deepcopy(INPUT_JSON)
            input_json["question"] = question
            logger.debug("In html client end point input_json=%s" % str(input_json))
            gfg, gfg_only_sol = get_answer(input_json, cs.ClientType.HTML)

            html_only_sol = gfg_only_sol.to_html(index=False, justify='center'
                                                 , bold_rows=False)
            html_only_sol = html_only_sol.replace("\\n", "<br>")
            html_only_sol = html_only_sol.replace("&lt;", "<")
            html_only_sol = html_only_sol.replace("&gt;", ">")
            html_only_sol = html_only_sol + "<br><br><br><br><br><br><br><br><br><br>"

            html_return = gfg.to_html(index=False, justify='center'
                                      , bold_rows=False)
            html_return = html_return.replace("\\n", "<br>")
            html_return = html_return.replace("&lt;", "<")
            html_return = html_return.replace("&gt;", ">")
            html_return = html_return + "<br><br>"
            logger.debug("html")
            return html_only_sol + html_return

        elif request.method == 'GET':
            return render_template(KER_HTML)

    except Exception as e:
        logger.exception("Exception in demo" + str(e))
        gfg = pd.DataFrame({RESP_QUES: [str(sentence)],
                            RESP_ANS: ['Data not available']})
        html_return = gfg.to_html(index=False, justify='center', bold_rows=False)

        html_return = html_return.replace("\\n", "<br>")
        html_return = html_return + "<br>"
        return html_return


@app.route('/ker_faq', methods=['POST', 'GET'])
def demo_faq():
    """
    Defines the HTTP REST API to communicate FAQ queries from browser to python
    interface.
    It returns the answer in json format to HTML UI page
    """
    try:
        sentence = ""
        if request.method == 'POST':
            question = request.get_data()
            input_json = copy.deepcopy(INPUT_JSON)
            input_json["question"] = question
            gfg, gfg_only_sol = get_answer(input_json, cs.ClientType.HTML)

            html_return = gfg.to_html(index=False, justify='center',
                                      bold_rows=False)
            html_return = html_return.replace("\\n", "<br>")
            html_return = html_return.replace("&lt;", "<")
            html_return = html_return.replace("&gt;", ">")
            return html_return
        elif request.method == 'GET':
            return render_template(FAQ_HTML)

    except Exception as e:
        logger.exception("Exception in demo: " + str(e))
        gfg = pd.DataFrame({RESP_QUES: [str(sentence)],
                            RESP_ANS: ['Data not available']})
        html_return = gfg.to_html(index=False, justify='center', bold_rows=False)
        return html_return


@app.route('/ker_rcs_act', methods=['POST'])
def demo_ker_rcs_act():
    """
    Defines the HTTP REST API to communicate Spec queries from browser to
    python interface.
    It returns the answer in json format to HTML UI page
    """
    try:
        bot_request = request.get_data().decode()
        logger.info("bot_request from flask=%s", bot_request)
        logger.info("bot_request from flask=%s", type(bot_request))
        if WidgetConstants.POSTBACK in str(bot_request):
            req_dict = json.loads(bot_request)
            bot_dict = req_dict.get(WidgetConstants.RESPONSE, None)
            if bot_dict is None:
                bot_request = req_dict[WidgetConstants.REPLY][WidgetConstants.POSTBACK][WidgetConstants.DATA]
            else:
                bot_request = req_dict[WidgetConstants.RESPONSE][WidgetConstants.REPLY][WidgetConstants.POSTBACK][
                    WidgetConstants.DATA]

        logger.info("From flask, bot request:%s" + str(bot_request))
        logger.info("From flask, bot request type:%s" + str(type(bot_request)))

        # form input json with rcs input message
        json_input = copy.deepcopy(INPUT_JSON)
        # To reset the text similarity and classifier_info which may be set by other end points
        json_input['similarity_key'] = None
        json_input['classifier_info'] = None
        json_input["question"] = bot_request
        # call ker_engine to get query response
        query_response = KER_ENGINE.process_request(json_input, cs.ClientType.RCS)
        # extract specific details from response
        bot_response = query_response[cs.IOConstants.ANSWER]
        logger.info("response to bot=%s" % str(bot_response))
        logger.info("type response to bot=%s" % str(type(bot_response)))
        return bot_response
    except Exception as e:
        logger.exception("Exception in demo" + str(e))
        return "Error"


@app.route('/download')
def download_file():
    global DOWNLOAD_FILE
    path = UPLOAD_FOLDER + "/" + DOWNLOAD_FILE
    logger.debug("download_file path: %s" + path)
    return send_file(path, as_attachment=True)


def __validate_file_input(request):
    """
    validate the input file and check its file type.
    """
    resp = jsonify({'status_code': 0})
    request_from = 'html'
    file = ""
    f_name = ""

    if 'file' not in request.files and 'myFile' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp, request_from, file, f_name

    logger.debug("Upload file received. Saving in remote server...")
    if 'file' in request.files:
        file = request.files['file']
        request_from = 'command'
    elif 'myFile' in request.files:
        file = request.files['myFile']
        request_from = 'html'
    f_name = secure_filename(file.filename)
    resp.status_code = 200
    if (f_name == '') or (not allowed_file(f_name)):
        resp = jsonify({'message': 'No file selected for uploading'})
        resp.status_code = 400
    return resp, request_from, file, f_name


@app.route('/file_input', methods=['POST', 'GET'])
def file_input():
    """
    Defines the HTTP REST API to communicate message from browser to python interface.
    It returns the answer in json format to HTML UI page
    """
    file = None
    filename = ""
    request_from = None
    try:
        global DOWNLOAD_FILE
        if request.method == 'POST':
            logger.debug("HTTP flask upload is called")
            resp, request_from, file, filename = __validate_file_input(request)
            if resp.status_code != 200:
                return resp

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            todownload = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            logger.debug("***todownload: %s", todownload)
            # call function to read excel and update QA results
            ret = test_report(todownload)
            if ret == 0:
                if request_from == 'command':
                    message = 'Download the report from server at this path (%s)' % (todownload)
                    resp = jsonify({'message': message})
                    resp.status_code = 200
                    return resp
                elif request_from == 'html':
                    DOWNLOAD_FILE = filename
                    return render_template('ker_file.html', filename=filename)
            else:
                return "Error:Updating error in report"
        elif request.method == 'GET':
            return render_template("ker_file.html")

    except Exception as e:
        logger.error("Exception in upload" + str(e))
        return "Error in Updating results in  report"


@app.route('/ker_kms', methods=['POST', 'GET'])
def demo_kms_ts():
    """
    Defines the HTTP REST API to communicate with the KMS client

    REsponse is in json format
    """
    sentence = ""
    ker_cntxt = ""
    req_id = 0

    try:
        sentence = ""
        if request.method == 'POST':

            json_obj = request.get_json()

            resp_json = get_kms_answer(json_obj, cs.ClientType.KMS)
            return resp_json

        elif request.method == 'GET':
            return render_template(KER_HTML)

    except Exception as e:
        logger.exception("Exception in demo" + str(e))
        resp_json = {}
        resp_json = _frame_response_json(req_id, cs.INTERNAL_ERROR, sentence, cs.resp_msg[cs.INTERNAL_ERROR], ker_cntxt)
        return resp_json


@app.route('/ker_hybrid', methods=['POST', 'GET'])
def ker_engine_for_hybrid_approach():
    """
    The function to handle hybrid_approach request.
    """
    sample_questions = {"0": "", "1": "세탁기를 사용하기 전에 알아야 할 좋은 점은 무엇인가요 F215DD",
               }

    global KER_ENGINE
    global INPUT_JSON

    if request.method == "POST":
        req = request.form
        question = req.get("user_question")
        logger.debug("question from html=%s" % str(question))
        input_json = copy.deepcopy(INPUT_JSON)
        input_json["question"] = question
        logger.debug("In html client end point input_json=%s" % str(input_json))

        ################# RESPONSE FROM GRAPH QA ##########################
        if cs.IOConstants.HYBRID_RESPONSE not in input_json:
            input_json[cs.IOConstants.HYBRID_RESPONSE] = {}
        input_json[cs.IOConstants.HYBRID_RESPONSE][cs.IOConstants.HY_RES_STATUS] = cs.IOConstants.HY_RES_STATUS_ASKING_QUESTION
        logger.info("use_infoflag  from browser=(%d)", cs.ClientType.HTML)
        input_json[cs.IOConstants.SIMILARITY_KEY] = None
        input_json[cs.IOConstants.CLASSIFIER_INFO] = None
        query_response = KER_ENGINE.process_request(input_json, cs.ClientType.HTML, hybrid_approach=True)
        user_question, resp_modelno, hybrid_response = query_response[cs.IOConstants.QUESTION], \
                                                      query_response[cs.IOConstants.MODEL_NO], \
                                                      query_response[cs.IOConstants.HYBRID_RESPONSE]
        INPUT_JSON = input_json
        # Get the list of top results from text similarity
        mapped_keys_and_scores_gqa = hybrid_response[cs.IOConstants.HY_RES_MAPPED_KEYS]
        logger.info("mapped_keys_and_scores from graph qa:" + str(mapped_keys_and_scores_gqa))

        ################# RESPONSE FROM EMBEDDING BASED ###########################

        url_for_get_doc_results = 'http://docsearch:8007/get_graph_output'
        post_object = json.dumps({'question': user_question})
        headers = {'Content-Type': 'application/json'}
        responce_doc_results = requests.post(url_for_get_doc_results, data = post_object,
        headers=headers)
        responce_doc_results = json.loads(responce_doc_results.text)
        mapped_keys_and_scores_ea = responce_doc_results['response']
        if mapped_keys_and_scores_ea is not None:
            mapped_keys_and_scores_ea = dict(sorted(mapped_keys_and_scores_ea.items(), key=lambda item: float(item[1]), reverse=True))
        elif mapped_keys_and_scores_ea is None:
            mapped_keys_and_scores_ea = {}
        logger.info("mapped_keys_and_scores from embedding approach:" + str(mapped_keys_and_scores_ea))

        return render_template(KER_HYBRID_HTML, mapped_keys_and_scores_gqa=mapped_keys_and_scores_gqa,
                               mapped_keys_and_scores_ea=mapped_keys_and_scores_ea,
                               textarea_value=user_question,
                               sample_questions=sample_questions, html_resp=None)
    elif request.method == "GET":
        # Find the enrichment result
        matched_result = request.args.get('matched_result')
        approach = request.args.get('approach') # graph_based or doc_based

        input_json = copy.deepcopy(INPUT_JSON)
        response = ""
        user_question = input_json["question"]
        if matched_result is not None:
            if approach == "graph_based":
                matched_result_for_gqa = matched_result.split(">>")[1].strip()
                input_json[cs.IOConstants.HYBRID_RESPONSE][cs.IOConstants.HY_RES_CHOSEN_KEY_FROM_USER] = matched_result_for_gqa
                input_json[cs.IOConstants.HYBRID_RESPONSE][cs.IOConstants.HY_RES_STATUS] = cs.IOConstants.HY_RES_STATUS_SATISFIED
                response = _get_graph_qa_response(input_json)
            elif approach == "doc_based":
                url_for_get_doc_results = 'http://docsearch:8007/get_doc_retrieval_output'
                headers = {'Content-Type': 'application/json'}
                post_object = json.dumps({'question': user_question, 'matched_key':matched_result})
                responce_doc_results = requests.post(url_for_get_doc_results, data = post_object,
                    headers = headers)
                responce_doc_results = json.loads(responce_doc_results.text)
                response = responce_doc_results['response']

        logger.debug("html_resp=%s" % str(response))
        return render_template(KER_HYBRID_HTML, mapped_keys_and_scores_gqa={},mapped_keys_and_scores_ea={},
                               textarea_value=user_question, sample_questions=sample_questions, html_resp=response)

    return ""


def _get_graph_qa_response(input_json):
    """
    Generate response from graph QA
    """
    logger.debug("In html client end point input_json=%s" % str(input_json))
    gfg, gfg_only_sol = get_answer(input_json, cs.ClientType.HTML, hybrid_approach=True)

    html_only_sol = gfg_only_sol.to_html(index=False, justify='center'
                                         , bold_rows=False)
    html_only_sol = html_only_sol.replace("\\n", "<br>")
    html_only_sol = html_only_sol.replace("&lt;", "<")
    html_only_sol = html_only_sol.replace("&gt;", ">")
    logger.debug("html")
    return html_only_sol

def _frame_response_json(req_id, resp_code, question, answer, ker_cntxt):
    """
    frame the response json for the KMS system

    Args:
        req_id: request id
        resp_code: response code
        question: user question
        answer: answer from KER system
        ker_cntxt: current context
    return:
        framed response json
    """
    resp = {}
    resp["request_id"] = req_id
    resp["response_code"] = resp_code
    resp["response_message"] = cs.ExternalErrorMsgs.ERR_MSGS[resp_code][cs.ExternalErrorMsgs.MSG]
    resp["question"] = question
    resp["answer"] = answer
    resp.update(ker_cntxt)
    return json.dumps(resp)


def get_kms_answer(json_obj, client_type):
    """
    call the KER system to get the response for the user question

    Args:
        json_obj: dict
        client_type: int
    return:
        JSON response from KER system
    """
    global KER_ENGINE
    sentence = json_obj[QUERY]
    req_id = json_obj[REQ_ID]
    # call to ker engine to get rsponse for query
    query_response = KER_ENGINE.process_request(json_obj, client_type)
    # extract specific details to form KMS response
    template_resp, resp_code, ker_cntxt = query_response[cs.IOConstants.ANSWER], \
                                          query_response[cs.IOConstants.RESP_CODE], \
                                          query_response[cs.IOConstants.KER_CONTEXT]
    context_dict = {cs.IOConstants.KER_CONTEXT: ker_cntxt}
    json = _frame_response_json(req_id, resp_code, sentence, template_resp, context_dict)
    return json

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_answer(json_obj, client_type, hybrid_approach=False):
    """
        Returns the answer for the user question
        Args:
            user_question - User question as string
            flag - component to be used for extract info
            modelno - modelno of user query
            ques_topic - topic name of user query
            question_level - question level of user query
        Returns:
            gfg - pandas dataframe object
    """

    global KER_ENGINE

    logger.info("use_infoflag  from browser=(%d)", client_type)

    # call ker_engine to get query response
    query_response = KER_ENGINE.process_request(json_obj, client_type, hybrid_approach)
    # extract specific details from response
    user_question, resp_modelno, template_resp, extracted_info = query_response[cs.IOConstants.QUESTION], \
                                                                 query_response[cs.IOConstants.MODEL_NO], \
                                                                 query_response[cs.IOConstants.ANSWER], \
                                                                 query_response[cs.IOConstants.EXTRACTED_INFO]

    if template_resp is None or len(template_resp) <= 0:
        template_resp = "Data Not Available"
    logger.debug("flask_main template_ques=%s answer=%s",
                 extracted_info, template_resp)

    gfg = pd.DataFrame({RESP_QUES: [user_question],
                        'Model Number': [resp_modelno],
                        'Text Similarity': [extracted_info]})

    gfg_only_response = pd.DataFrame({RESP_QUES: [user_question],
                                      RESPONSE_STR: [template_resp]})

    report.write_entry(user_question, extracted_info, template_resp)
    return gfg, gfg_only_response


def test_report(filepath):
    """
        tests the given test file and writes back the results
        Args:
            filepath - path of test file to be tested
            modelno - modelno of user query
            use_info - component to be used for extract info
            ques_topic - topic name of user query
            question_level - question level of user query
        Returns:
            None
    """
    global KER_ENGINE
    input_json_req = copy.deepcopy(INPUT_JSON)
    # call to create test report
    try:
        report.testandupdate_report(filepath, KER_ENGINE, input_json_req, cs.ClientType.HTML)
        return 0
    except Exception as e:
        return -1

# main function
if __name__ == "__main__":
    ip = '0.0.0.0'
    # call for file testing
    # test_report("test.csv","WM4500H*A","2","Specification","L1")
    # print("************Flask started")
    app.run(host=ip, port=int(port_number))
