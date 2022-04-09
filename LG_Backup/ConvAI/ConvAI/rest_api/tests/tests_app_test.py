import json
from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse
from rest_api import views

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class TestEngineTestCase(TestCase):
    def post_and_check(self, query_data, expected_resp_data):
        req = RequestFactory().post(reverse("rest_api:index"), query_data, content_type='application/json')
        resp = views.IndexView.as_view()(req)

        json_string = resp.content
        logger.debug(json_string)

        # Check for resp code
        self.assertEqual(resp.status_code, 200)

        # Comparing req to resp
        self.assertEqual(json.loads(json_string), json.loads(json.dumps(expected_resp_data)))

    def test_retriever_ont001_case001(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "001",
            "Query": {
                "head": "CocaCola",
                "relation": "harmful"
            }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "001",
            "Query": {
                "head": "CocaCola",
                "relation": "harmful"
            },
            "tail": "Close the door and Restart."
        }
        self.post_and_check(query_data, expected_resp_data)

    def test_retriever_ont002_case001(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "002",
            "Query": {
                "head": "CocaCola",
                "relation": "harmful"
            }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "002",
            "Query": {
                "head": "CocaCola",
                "relation": "harmful"
            },
            "tail": "Diabetes"
        }
        self.post_and_check(query_data, expected_resp_data)

    def test_retriever_ont002_case002(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "002",
            "Query": {
                "head": "CocaCola",
                "relation": "alternative"
            }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "002",
            "Query": {
                "head": "CocaCola",
                "relation": "alternative"
            },
            "tail": "Carbonated Water"
        }
        self.post_and_check(query_data, expected_resp_data)

    def test_retriever_ont003_case001(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "003",
            "product_group_code": "AC",

            "product_code": "CRA",

            "symp_code": "ST000584",
            "Query":
                {"head": "SS000001",
                 "relation": "sub_name"
                 }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "003",
            "product_group_code": "AC",
            "product_code": "CRA",
            "symp_code": "ST000584",
            "Query": {
                "head": "SS000001",
                "relation": "sub_name"
            },
            "tail": "제품 사양 문의"
        }
        self.post_and_check(query_data, expected_resp_data)

    def test_retriever_ont003_case002(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "003",

            "product_group_code": "AC",

            "product_code": "CRA",

            "symp_code": "ST000584",
            "Query":
                {"head": "SS000001",
                 "relation": "operation"
                 }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "003",
            "product_group_code": "AC",
            "product_code": "CRA",
            "symp_code": "ST000584",
            "Query": {
                "head": "SS000001",
                "relation": "operation"
            },
            "tail": "일반접수"
        }
        self.post_and_check(query_data, expected_resp_data)

    def test_retriever_ont004_case001(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "004",
            "product": "styler",
            "Query": {
                "head": "dE",
                "relation": "solution"
            }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "004",
            "product": "styler",
            "Query": {
                "head": "dE",
                "relation": "solution"
            },
            "tail": "close door"
        }
        self.post_and_check(query_data, expected_resp_data)

    def test_retriever_pcc(self):  # TODO : check whether KMS is changed to PCC
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "product": "refrigerator",
            "device_id": "00243ce2-8f20-495d-b88c-054c7375f52f",
            "Query": "error_code"
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "product": "refrigerator",
            "device_id": "00243ce2-8f20-495d-b88c-054c7375f52f",
            "Query": "error_code",
            "Answer": {
                "error_code_1": "dE",
                "error_code_2": "NONE",
                "error_code_3": "NONE"
            }
        }
        self.post_and_check(query_data, expected_resp_data)
