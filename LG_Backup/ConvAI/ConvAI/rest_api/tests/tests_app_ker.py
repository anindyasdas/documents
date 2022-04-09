import json
from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse
from rest_api import views

import logging
import copy

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)


class ManualEngineTestCase(TestCase):
    maxDiff = None
    # templates used for evaluating troubleshooting template responses
    templates = {
        "cause_singular": [
            "This can be the probable cause: ",
            "The cause is: ",
            "This may be the cause: "
        ],
        "sol_singlar": [
            "This is the recommended solution: ",
            "Recommended solution is: ",
            "Here is a quick fix: "
        ]
    }
    causes_templates = templates["cause_singular"]
    solutions_templates = templates["sol_singlar"]

    def _prepare_possible_expected_ts_responses(self, expected_resp_data):
        """
            forms possible combinations of expected troubleshooting json responses
            based on the templates
        """
        expected_resp_list = []
        logger.debug("ManualEngineTestCase.causes_templates : %s",ManualEngineTestCase.causes_templates)
        logger.debug("ManualEngineTestCase.solutions_templatess : %s", ManualEngineTestCase.solutions_templates)
        # forming possible template troubleshooting responses
        for each_cause_temp in ManualEngineTestCase.causes_templates:
            for each_soln_temp in ManualEngineTestCase.solutions_templates:
                expected_resp_copy = copy.deepcopy(expected_resp_data)
                logger.debug("expected_resp_copy : %s",expected_resp_copy)
                template_ans = expected_resp_copy["query"]["answer"]
                logger.debug("*****template_ans****** : %s",template_ans)
                form_resp = template_ans.format(cause_temp=each_cause_temp, solution_temp=each_soln_temp)
                expected_resp_copy["query"]["answer"] = form_resp
                expected_resp_copy["query"]["ker_context"]["prev_answer"] = form_resp
                expected_resp_list.append(copy.deepcopy(expected_resp_copy))
                logger.debug("each====expected_resp_list : %s",expected_resp_list)

        logger.debug(expected_resp_list)
        return expected_resp_list

    def valid_post_and_check_troubleshooting(self, query_data, expected_resp_data):
        req = RequestFactory().post(reverse("rest_api:index"), query_data, content_type='application/json')
        resp = views.IndexView.as_view()(req)
        logger.debug("resp.content : %s",resp.content)
        resp_json = json.loads(resp.content)
        qresp_json = resp_json["query"]
        logger.debug("resp json from ker in test case=(%s)" % qresp_json)
        logger.debug(qresp_json)
        # Check for resp code
        self.assertEqual(resp.status_code, 200)
        logger.debug("status code is success")
        # forms possible combinations of expected troubleshooting json responses
        # based on the templates
        expected_resp_list = self._prepare_possible_expected_ts_responses(expected_resp_data)
        # check json response from KER is present in the expected possible responses
        self.assertIn(resp_json, expected_resp_list)
        # self.assertDictEqual(resp_json, expected_resp_data)

    def valid_post_and_check(self, query_data, expected_resp_data):
        logger.debug("valid_post_and_check : %s , %s",query_data, type(query_data))
        req = RequestFactory().post(reverse("rest_api:index"), query_data, content_type='application/json')
        resp = views.IndexView.as_view()(req)
        logger.debug("valid_post_and_check resp.content : %s", resp.content)
        resp_json = json.loads(resp.content)
        logger.debug("resp json from ker in test case=(%s)" % resp_json)
        logger.debug(resp_json)
        # Check for resp code
        self.assertEqual(resp.status_code, 200)
        logger.debug("status code is success")

        # Comparing req to resp
        # self.assertEqual(resp_json, json.loads(json.dumps(expected_resp_data)))
        self.assertDictEqual(resp_json, expected_resp_data)

    def invalid_post_and_check(self, query_data, expected_resp_code, expected_err_code):
        logger.debug("invalid_post_and_check expected_resp_Code=(%d) expected_err_code=(%d)" %
                     (expected_resp_code, expected_err_code))
        logger.debug("valid_post_and_check : %s , %s",query_data, type(query_data))
        req = RequestFactory().post(reverse("rest_api:index"), query_data, content_type='application/json')
        resp = views.IndexView.as_view()(req)
        logger.debug("**************invalid_post_response : %s",resp.content)
        resp_json = resp.content
        logger.debug(resp_json)
        logger.debug("invalid_post_and_check resp json from ker in test case=(%s)" % resp_json)
        resp_json = json.loads(resp.content)
        err_code = resp_json["query"]["response_code"]
        # Check for resp code
        self.assertEqual(resp.status_code, expected_resp_code)
        self.assertEqual(err_code, expected_err_code)

    def test_valid_specification_query_001(self):
        logger.debug("test_valid_specification_query_001 called")
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker",
            "process": "retrieval",
            "query": {
                "request_id": 1,
                "question": "what is the width of WM4500H*A?",
                "model_no": "WM4500H*A",
                "ker_context": {}
            }
        }
        expected_resp_data = {
                "from": "KMS",
                "to": "Butler",
                "ontology_id": "ker",
                "process": "retrieval",
                "query": {
                    "response_code": 0,
                    "response_message": "Success",
                    "answer": "The width of the washing machine model WM4500H*A is 27.0 inch.",
                    "question": "what is the width of WM4500H*A?",
                    "ker_context": {
                        "model_no": "WM4500H*A",
                        "product": "washing machine",
                        "unit": "",
                        "spec_key": "width",
                        "prev_answer": "The width of the washing machine model WM4500H*A is 27.0 inch.",
                        "prev_question": "what is the width of WM4500H*A?"
                    },
                    "request_id": 1
                }
            }
        self.valid_post_and_check(query_data, expected_resp_data)

    # test case for unit conversion
    def test_valid_specification_query_002(self):
        logger.debug("test_valid_specification_query_002 called")
        query_data = {
           "from":"Butler",
           "to":"KMS",
           "ontology_id":"ker",
           "process":"retrieval",
           "query":{
              "request_id":2,
              "question":"tell me in mm?",
              "model_no":"WM4500H*A",
              "ker_context":{
                 "model_no":"WM4500H*A",
                 "product":"washing machine",
                 "unit":"",
                 "spec_key":"width",
                 "prev_answer":"The width of the washing machine model WM4500H*A is 27.0 inch.",
                 "prev_question":"what is the width of WM4500H*A?"
              }
           }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "The width of the washing machine model WM4500H*A is 685.8 millimeter.",
                "question": "tell me in mm?",
                "ker_context": {
                    "model_no": "WM4500H*A",
                    "product": "washing machine",
                    "unit": "mm",
                    "spec_key": "width",
                    "prev_answer": "The width of the washing machine model WM4500H*A is 685.8 millimeter.",
                    "prev_question": "tell me in mm?"
                },
                "request_id": 2
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)

    def test_valid_troubleshooting_query_001(self):
        logger.debug("test_valid_troubleshooting_query_001 called")
        query_data = {
           "from":"Butler",
           "to":"KMS",
           "ontology_id":"ker",
           "process":"retrieval",
           "query":{
              "request_id":3,
              "question":"How to fix if water inlet hoses are pinched?",
              "model_no":"WM4500H*A",
              "ker_context":{
                 "model_no":"WM4500H*A",
                 "product":"washing machine",
                 "unit":"mm",
                 "spec_key":"width",
                 "prev_answer":"The width of the washing machine model WM4500H*A is 685.8 millimeter.",
                 "prev_question":"tell me in mm?"
              }
           }
        }
        expected_resp_data = {
                                "from": "KMS",
                                "to": "Butler",
                                "ontology_id": "ker",
                                "process": "retrieval",
                                "query": {
                                    "response_code": 0,
                                    "response_message": "Success",
                                    "answer": "<b>{cause_temp}Water inlet hoses are kinked, pinched, or crushed</b>\n\n{solution_temp}Make sure that the hoses are not kinked, pinched or crushed behind or under the washer.  be careful when moving the washer during cleaning or maintenance. \n\n",
                                    "question": "How to fix if water inlet hoses are pinched?",
                                    "ker_context": {
                                        "model_no": "WM4500H*A",
                                        "product": "washing machine",
                                        "unit": "mm",
                                        "spec_key": "width",
                                        "prev_answer": "<b>{cause_temp}Water inlet hoses are kinked, pinched, or crushed</b>\n\n{solution_temp}Make sure that the hoses are not kinked, pinched or crushed behind or under the washer.  be careful when moving the washer during cleaning or maintenance. \n\n",
                                        "prev_question": "How to fix if water inlet hoses are pinched?"
                                    },
                                    "request_id": 3
                                }
                            }
        self.valid_post_and_check_troubleshooting(query_data, expected_resp_data)

    def test_valid_troubleshooting_query_002(self):
        logger.debug("test_valid_troubleshooting_query_002 called")
        query_data = {
                        "from": "Butler",
                        "to": "KMS",
                        "ontology_id": "ker",
                        "process": "retrieval",
                        "query": {
                            "request_id": 4,
                            "question": "Why is my fridge making a gurgling sound?",
                            "model_no": "LRFDS3006*",
                            "ker_context": {
                                    "model_no": "LRFDS3006*",
                                    "product": "refrigerator",
                                    "unit": "",
                                    "spec_key": "net weight",
                                    "prev_answer": "\n\nThe cause is: \nWater inlet hoses are kinked, pinched, or crushed\nRecommended solution is: \nMake sure that the hoses are not kinked, pinched or crushed behind or under the washer. Be careful when moving the washer during cleaning or maintenance.",
                                    "prev_question": "How to fix if water inlet hoses are pinched?"
                            }
                        }
        }
        expected_resp_data = {
                                "from": "KMS",
                                "to": "Butler",
                                "ontology_id": "ker",
                                "process": "retrieval",
                                "query": {
                                    "response_code": 0,
                                    "response_message": "Success",
                                    "answer": "<b>{cause_temp}Refrigerant flowing through the cooling system</b>\n\n{solution_temp}Normal operation\n\n",
                                    "question": "Why is my fridge making a gurgling sound?",
                                    "ker_context": {
                                        "model_no": "LRFDS3006*",
                                        "product": "refrigerator",
                                        "unit": "",
                                        "spec_key": "net weight",
                                        "prev_answer": "<b>{cause_temp}Refrigerant flowing through the cooling system</b>\n\n{solution_temp}Normal operation\n\n",
                                        "prev_question": "Why is my fridge making a gurgling sound?"
                                    },
                                    "request_id": 4
                                }
                            }
        self.valid_post_and_check_troubleshooting(query_data, expected_resp_data)

    def test_valid_operation_query_001(self):
        logger.debug("test_valid_operation_query_001 called")
        query_data = {
                        "from": "Butler",
                        "to": "KMS",
                        "ontology_id": "ker",
                        "process": "retrieval",
                        "query": {
                                   "request_id": 5,
                                   "question": "what is the ice plus feature?",
                                   "model_no": "LRFDS3006*",
                                   "ker_context": {
                                        "model_no": "LRFDS3006*",
                                        "prev_answer": "\n\nThe cause is: \nRefrigerant flowing through the cooling system\nRecommended solution is: \nNormal Operation",
                                        "prev_question": "Why is my fridge making a gurgling sound? ",
                                        "product": "refrigerator",
                                        "spec_key": "net weight",
                                        "unit": ""
                                    }
                        }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "Find the following information regarding Control Panel\n<b>Ice Plus</b>\n\nThis function increases both ice making and freezing capabilities. Press the Ice Plus button to illuminate the icon and activate the function for 24 hours.  The function automatically shuts off after 24 hours.  Stop the function manually by pressing the button once more. \n\n",
                "question": "what is the ice plus feature?",
                "ker_context": {
                    "model_no": "LRFDS3006*",
                    "product": "refrigerator",
                    "unit": "",
                    "spec_key": "net weight",
                    "prev_answer": "Find the following information regarding Control Panel\n<b>Ice Plus</b>\n\nThis function increases both ice making and freezing capabilities. Press the Ice Plus button to illuminate the icon and activate the function for 24 hours.  The function automatically shuts off after 24 hours.  Stop the function manually by pressing the button once more. \n\n",
                    "prev_question": "what is the ice plus feature?"
                },
                "request_id": 5
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)

    def test_valid_operation_query_002(self):
        logger.debug("test_valid_operation_query_002 called")
        query_data = {
           "from":"Butler",
           "to":"KMS",
           "ontology_id":"ker",
           "process":"retrieval",
           "query":{
              "request_id":6,
              "question":"how to turn on sabbath mode?",
              "model_no":"LRFDS3006*",
              "ker_context":{
                 "model_no":"LRFDS3006*",
                 "product":"refrigerator",
                 "unit":"",
                 "spec_key":"net weight",
                 "prev_answer": "Find the following information regarding Control Panel\n<b>Ice Plus</b>\n\nThis function increases both ice making and freezing capabilities. Press the Ice Plus button to illuminate the icon and activate the function for 24 hours.  The function automatically shuts off after 24 hours.  Stop the function manually by pressing the button once more. \n\n",
                 "prev_question":"what is the ice plus feature?"
              }
           }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "Find the following information regarding Sabbath Mode\n<b>Using the Sabbath Mode</b>\n\nSabbath mode is used on the Jewish Sabbath and holidays To turn Sabbath mode on, touch the display to activate it, then press and hold the Freezer and Wi-Fi buttons for 3 seconds until sb appears in the display To turn Sabbath mode off manually, press and hold the Freezer and Wi-Fi buttons for 3 seconds. \n\n",
                "question": "how to turn on sabbath mode?",
                "ker_context": {
                    "model_no": "LRFDS3006*",
                    "product": "refrigerator",
                    "unit": "",
                    "spec_key": "net weight",
                    "prev_answer": "Find the following information regarding Sabbath Mode\n<b>Using the Sabbath Mode</b>\n\nSabbath mode is used on the Jewish Sabbath and holidays To turn Sabbath mode on, touch the display to activate it, then press and hold the Freezer and Wi-Fi buttons for 3 seconds until sb appears in the display To turn Sabbath mode off manually, press and hold the Freezer and Wi-Fi buttons for 3 seconds. \n\n",
                    "prev_question": "how to turn on sabbath mode?"
                },
                "request_id": 6
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)

    def test_valid_operation_query_003(self):
        query_data = {
                        "from": "Butler",
                        "to": "KMS",
                        "ontology_id": "ker",
                        "process": "retrieval",
                        "query": {
                            "request_id": 7,
                            "question": "how to turn off sabbath mode?",
                            "model_no":"LRFDS3006*",
                            "ker_context": {
                                "model_no": "LRFDS3006*",
                                "prev_answer": "Find the following information regarding Sabbath Mode\n<b>Using the Sabbath Mode</b>\n\nSabbath mode is used on the Jewish Sabbath and holidays To turn Sabbath mode on, touch the display to activate it, then press and hold the Freezer and Wi-Fi buttons for 3 seconds until sb appears in the display To turn Sabbath mode off manually, press and hold the Freezer and Wi-Fi buttons for 3 seconds. \n\n",
                                "prev_question": "how to turn on sabbath mode?",
                                "product": "refrigerator",
                                "spec_key": "net weight",
                                "unit": ""
                            }
                        }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "Find the following information regarding Sabbath Mode\n<b>Using the Sabbath Mode</b>\n\nSabbath mode is used on the Jewish Sabbath and holidays To turn Sabbath mode on, touch the display to activate it, then press and hold the Freezer and Wi-Fi buttons for 3 seconds until sb appears in the display To turn Sabbath mode off manually, press and hold the Freezer and Wi-Fi buttons for 3 seconds. \n\n",
                "question": "how to turn off sabbath mode?",
                "ker_context": {
                    "model_no": "LRFDS3006*",
                    "product": "refrigerator",
                    "unit": "",
                    "spec_key": "net weight",
                    "prev_answer": "Find the following information regarding Sabbath Mode\n<b>Using the Sabbath Mode</b>\n\nSabbath mode is used on the Jewish Sabbath and holidays To turn Sabbath mode on, touch the display to activate it, then press and hold the Freezer and Wi-Fi buttons for 3 seconds until sb appears in the display To turn Sabbath mode off manually, press and hold the Freezer and Wi-Fi buttons for 3 seconds. \n\n",
                    "prev_question": "how to turn off sabbath mode?"
                },
                "request_id": 7
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)

    # Missing query of model_no
    def test_invalid_manual_retrieval_001(self):
        query_data = {
                        "from": "Butler",
                        "to": "KMS",
                        "ontology_id": "ker",
                        "process": "retrieval",
                        "query": {
                                   "request_id": 8,
                                   "question": "What is the width?",
                                   "model_no": "",
                                   "ker_context": {}
                        }
        }
        self.invalid_post_and_check(query_data, 200, 9481)
    #
    # # Invalid model no in query
    def test_invalid_manual_retrieval_002(self):
        query_data = {
                    "from": "Butler",
                    "to": "KMS",
                    "ontology_id": "ker",
                    "process": "retrieval",
                    "query": {
                               "request_id": 9,
                               "question": "What is the width?",
                               "model_no": "WM4500H*",
                               "ker_context": {}
                    }
        }
        self.invalid_post_and_check(query_data, 200, 9463)

    # Invalid query, asking spin speed from refrigerator model
    def test_invalid_manual_retrieval_003(self):
        query_data = {
                        "from": "Butler",
                        "to": "KMS",
                        "ontology_id": "ker",
                        "process": "retrieval",
                        "query": {
                                    "request_id": 10,
                                    "question": "What is the spin speed?",
                                    "model_no": "LRFDS3006*",
                                    "ker_context": {
                                        "model_no": "WM4500H*A",
                                        "prev_answer": "68.6",
                                        "prev_question": "What is the width of WM4500H*A?",
                                        "product": "washing machine",
                                        "spec_key": "width",
                                        "unit": "cm"
                                    }
                        }
        }
        self.invalid_post_and_check(query_data, 200, 9464)

    # # invalid request
    def test_invalid_manual_retrieval_004(self):
        logger.debug("executed test_invalid_manual_retrieval_004 called")
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker",
            "process": "retrieval",
            "query": {
                "request_id": 10,
                "question": "",
                "model_no": "LRFDS3006*",
                "ker_context": {
                    "model_no": "WM4500H*A",
                    "prev_answer": "68.6",
                    "prev_question": "What is the width of WM4500H*A?",
                    "product": "washing machine",
                    "spec_key": "width",
                    "unit": "cm"
                }
            }
        }
        self.invalid_post_and_check(query_data, 200, 9481)
    #
    # # KG connection error
    def test_kg_connection_error_005(self):
        logger.debug("executed test_kg_connection_error_005")
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker",
            "process": "retrieval",
            "query": {
                "request_id": 10,
                "question": "what is the net weight?",
                "model_no": "LRFDS3006*",
                "ker_context": {
                    "model_no": "WM4500H*A",
                    "prev_answer": "68.6",
                    "prev_question": "What is the width of WM4500H*A?",
                    "product": "washing machine",
                    "spec_key": "width",
                    "unit": "cm"
                }
            }
        }
        self.invalid_post_and_check(query_data, 200, 9471)
