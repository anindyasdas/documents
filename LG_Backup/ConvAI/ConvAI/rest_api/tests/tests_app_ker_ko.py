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

    def test_valid_troubleshooting_query_001(self):
        logger.debug("test_valid_troubleshooting_query_001 called")
        query_data = {
                "from": "Butler",
                "to": "KMS",
                "ontology_id": "ker_ko",
                "process": "retrieval",
                "query": {
                    "request_id": 1,
                    "question": "F21ADD 에서 이 IE 를받는 이유는 무엇입니까?",
                    "model_no": "F21ADD",
                    "ker_context": {}
                }
            }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "<b>발생원인</b>\n\n<b>급수 밸브가 잠겨 있나요?</b>\n\n<b>해결방안</b>\n\n세탁기와 연결된 급수 밸브를 여세요. \n\n<b>발생원인</b>\n\n<b>단수되어 있나요?</b>\n\n<b>해결방안</b>\n\n연결된 수도꼭지에 이상이 있으면 해당 수리 업체에 문의하세요. \n\n집 전체가 단수라면 시청이나 군청에 문의하세요. \n\n<b>발생원인</b>\n\n<b>수도꼭지나 급수 호스가 얼어 있나요?</b>\n\n<b>해결방안</b>\n\n수도꼭지를 잠근 후 뜨거운 물수건으로 수도꼭지와 제품 급수 호스 양쪽 연결 부위를 녹이세요. \n\n<b>발생원인</b>\n\n<b>급수 호스가 막혀 있나요?</b>\n\n<b>해결방안</b>\n\n급수구에서 거름망을 꺼내어 이물질을 제거하세요. \n\n<b>발생원인</b>\n\n<b>급수 호스가 꺾여 있나요?</b>\n\n<b>해결방안</b>\n\n급수 호스가 꺾이지 않도록 펴세요. \n\n<b>발생원인</b>\n\n<b>급수 호스가 수도꼭지에 바르게 연결되어 있지 않나요?</b>\n\n<b>해결방안</b>\n\n급수 호스가 수도꼭지에 밀착되도록 다시 조이세요. \n\n",
                "question": "F21ADD 에서 이 IE 를받는 이유는 무엇입니까?",
                "ker_context": {
                    "model_no": "F21ADD",
                    "product": "washing machine",
                    "unit": "",
                    "spec_key": "",
                    "prev_answer": "<b>발생원인</b>\n\n<b>급수 밸브가 잠겨 있나요?</b>\n\n<b>해결방안</b>\n\n세탁기와 연결된 급수 밸브를 여세요. \n\n<b>발생원인</b>\n\n<b>단수되어 있나요?</b>\n\n<b>해결방안</b>\n\n연결된 수도꼭지에 이상이 있으면 해당 수리 업체에 문의하세요. \n\n집 전체가 단수라면 시청이나 군청에 문의하세요. \n\n<b>발생원인</b>\n\n<b>수도꼭지나 급수 호스가 얼어 있나요?</b>\n\n<b>해결방안</b>\n\n수도꼭지를 잠근 후 뜨거운 물수건으로 수도꼭지와 제품 급수 호스 양쪽 연결 부위를 녹이세요. \n\n<b>발생원인</b>\n\n<b>급수 호스가 막혀 있나요?</b>\n\n<b>해결방안</b>\n\n급수구에서 거름망을 꺼내어 이물질을 제거하세요. \n\n<b>발생원인</b>\n\n<b>급수 호스가 꺾여 있나요?</b>\n\n<b>해결방안</b>\n\n급수 호스가 꺾이지 않도록 펴세요. \n\n<b>발생원인</b>\n\n<b>급수 호스가 수도꼭지에 바르게 연결되어 있지 않나요?</b>\n\n<b>해결방안</b>\n\n급수 호스가 수도꼭지에 밀착되도록 다시 조이세요. \n\n",
                    "prev_question": "F21ADD 에서 이 IE 를받는 이유는 무엇입니까?"
                },
                "request_id": 1
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)


    def test_valid_operation_query_002(self):
        logger.debug("test_valid_operation_query_002 called")
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "request_id": 2,
                "question": "섬유유연제 사용에 대한 모든 정보를 알려주세요",
                "model_no": "F21ADD",
                "ker_context": {}
            }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "Find the following information regarding 세제 또는 섬유 유연제 사용하기\n<b>섬유 유연제 넣고 사용하기</b>\n\n<img style=\"display: block;margin: 0 auto;\" src=\"/image_db/washing_machine/MFL71485465/operation/섬유_유연제_넣고_사용하기/victor_korea_softener_201214.png\"/>\n\n섬유 유연제가 넘치지 않게 MAX(기준선)a 이하까지 넣으세요.  기준선을 넘을 경우 섬유 유연제가 드럼 안으로 바로 투입될 수 있습니다 세탁하기 전에 섬유 유연제를 세제통의 정확한 위치에 넣고 후, 세제통을 부드럽게 밀면서 닫으세요.  섬유 유연제가 출렁거리면서 드럼 안으로 바로 투입될 수 있습니다. \n섬유 유연제는 최종 헹굼 시 자동으로 투입됩니다. \n\n",
                "question": "섬유유연제 사용에 대한 모든 정보를 알려주세요",
                "ker_context": {
                    "model_no": "F21ADD",
                    "product": "washing machine",
                    "unit": "",
                    "spec_key": "",
                    "prev_answer": "Find the following information regarding 세제 또는 섬유 유연제 사용하기\n<b>섬유 유연제 넣고 사용하기</b>\n\n<img style=\"display: block;margin: 0 auto;\" src=\"/image_db/washing_machine/MFL71485465/operation/섬유_유연제_넣고_사용하기/victor_korea_softener_201214.png\"/>\n\n섬유 유연제가 넘치지 않게 MAX(기준선)a 이하까지 넣으세요.  기준선을 넘을 경우 섬유 유연제가 드럼 안으로 바로 투입될 수 있습니다 세탁하기 전에 섬유 유연제를 세제통의 정확한 위치에 넣고 후, 세제통을 부드럽게 밀면서 닫으세요.  섬유 유연제가 출렁거리면서 드럼 안으로 바로 투입될 수 있습니다. \n섬유 유연제는 최종 헹굼 시 자동으로 투입됩니다. \n\n",
                    "prev_question": "섬유유연제 사용에 대한 모든 정보를 알려주세요"
                },
                "request_id": 2
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)

    def test_valid_troubleshooting_query_003(self):
        logger.debug("test_valid_troubleshooting_query_003 called")
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "request_id": 3,
                "question": "S5MBC 스타일러 모델에서 에러 코드가 떠요",
                "model_no": "S5MBC",
                "ker_context": {}
            }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "<b>발생원인</b>\n\n<b>필터가 제자리에 조립되어 있나요?</b>\n\n<b>해결방안</b>\n\n필터 없이 제품을 작동시킬경우 발생하는 현상입니다.  필터를 제자리에 조립하세요. \n\n",
                "question": "S5MBC 스타일러 모델에서 에러 코드가 떠요",
                "ker_context": {
                    "model_no": "S5MBC",
                    "product": "styler",
                    "unit": "",
                    "spec_key": "",
                    "prev_answer": "<b>발생원인</b>\n\n<b>필터가 제자리에 조립되어 있나요?</b>\n\n<b>해결방안</b>\n\n필터 없이 제품을 작동시킬경우 발생하는 현상입니다.  필터를 제자리에 조립하세요. \n\n",
                    "prev_question": "S5MBC 스타일러 모델에서 에러 코드가 떠요"
                },
                "request_id": 3
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)

    def test_valid_troubleshooting_query_004(self):
        logger.debug("test_valid_troubleshooting_query_004 called")
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "request_id": 4,
                "question": "와셔 W167J에 LE가 있는 이유는 무엇입니까?",
                "model_no": "W167J",
                "ker_context": {}
            }
        }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "<b>발생원인</b>\n\n<b>많은 양의 세탁물을 넣었나요?</b>\n\n<b>해결방안</b>\n\n세탁물의 양이 너무 많으면 세탁 모터에 많은 힘이 집중되어 드럼이 회전하지 않을 수 있습니다.  세탁물을 조금 빼낸 후 세탁을 다시 시작하세요.  계속해서 표시가 나타나면 전원 플러그를 뺀 후 lg전자 서비스센터에 문의하세요. \n\n",
                "question": "와셔 W167J에 LE가 있는 이유는 무엇입니까?",
                "ker_context": {
                    "model_no": "W167J",
                    "product": "washing machine",
                    "unit": "",
                    "spec_key": "",
                    "prev_answer": "<b>발생원인</b>\n\n<b>많은 양의 세탁물을 넣었나요?</b>\n\n<b>해결방안</b>\n\n세탁물의 양이 너무 많으면 세탁 모터에 많은 힘이 집중되어 드럼이 회전하지 않을 수 있습니다.  세탁물을 조금 빼낸 후 세탁을 다시 시작하세요.  계속해서 표시가 나타나면 전원 플러그를 뺀 후 lg전자 서비스센터에 문의하세요. \n\n",
                    "prev_question": "와셔 W167J에 LE가 있는 이유는 무엇입니까?"
                },
                "request_id": 4
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)

    # Missing query of model_no
    def test_invalid_manual_retrieval_005(self):
        query_data = {
                "from": "Butler",
                "to": "KMS",
                "ontology_id": "ker_ko",
                "process": "retrieval",
                "query": {
                           "request_id": 5,
                           "question": "섬유유연제 사용에 대한 모든 정보를 알려주세요",
                           "model_no": "",
                           "ker_context": {}
                }
        }
        self.invalid_post_and_check(query_data, 200, 9481)

    # # Invalid model no in query
    def test_invalid_manual_retrieval_006(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "request_id": 6,
                "question": "FA1ADD 에서 이 F1 를받는 이유는 무엇입니까?",
                "model_no": "FA1ADD",
                "ker_context": {}
            }
        }
        self.invalid_post_and_check(query_data, 200, 9463)

    # Requested information not found in KG
    def test_invalid_manual_retrieval_007(self):
        query_data = {
            "from": "Butler",
            "to": "KMS",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "request_id": 7,
                "question": "F21ADD 에서 이 F1 를받는 이유는 무엇입니까?",
                "model_no": "F21ADD",
                "ker_context": {}
            }
        }
        self.invalid_post_and_check(query_data, 200, 9464)

    # test case for troubleshooting images retrieval
    def test_valid_troubleshooting_query_008(self):
        logger.debug("test_valid_troubleshooting_query_008 called")
        query_data = {
                "from": "Butler",
                "to": "KMS",
                "ontology_id": "ker_ko",
                "process": "retrieval",
                "query": {
                    "request_id": 8,
                    "question": "경고음으로 결함을 진단하는 방법은 무엇입니까?",
                    "model_no": "F21ADD",
                    "ker_context": {}
                }
            }
        expected_resp_data = {
            "from": "KMS",
            "to": "Butler",
            "ontology_id": "ker_ko",
            "process": "retrieval",
            "query": {
                "response_code": 0,
                "response_message": "Success",
                "answer": "<b>발생원인</b>\n\n<b>문을 닫은 후 전원 버튼을 누르세요. </b>\n\n<b>해결방안</b>\n\nNone\n\n<b>발생원인</b>\n\n<b>전화기를 스마트 진단 로고 (c,d)에 대십시오. </b>\n\n<b>해결방안</b>\n\n전화기의 마이크 부분이 제품을 향하고 있는지 확인하세요. \n\n<img style=\"display: block;margin: 0 auto;\" src=\"/image_db/washing_machine/MFL71485465/troubleshooting/diagnosing_a_fault/smart_diagnosis.png\"/>\n\n<b>발생원인</b>\n\n<b>물온도 버튼을 소리가 날 때까지 길게 누르세요. </b>\n\n<b>해결방안</b>\n\n물온도 버튼을 누르기 전 다른 버튼이나 다이얼을 조작하였다면 전원을 끈 다음 처음부터 다시 시작하세요. 스마트 진단을 위한 데이터 전송 중에는 전화기를 제품에 계속 댄 채 대기하세요.  화면에 데이터 전송을 위한 남은 시간이 표시됩니다. 전송음이 귀에 거슬릴 수 있으나 정확한 고장 진단을 위해 소리가 멈출 때까지 전화기를 떼지 마세요. \n\n<b>발생원인</b>\n\n<b>데이터 전송 완료 후에는 스마트 진단 결과가 애플리케이션에 표시됩니다. </b>\n\n<b>해결방안</b>\n\n데이터 전송이 완료되면 전송 완료 표시와 함께 수 초 후 자동으로 제품의 전원이 꺼집니다. \n\n",
                "question": "경고음으로 결함을 진단하는 방법은 무엇입니까?",
                "ker_context": {
                    "model_no": "F21ADD",
                    "product": "washing machine",
                    "unit": "",
                    "spec_key": "",
                    "prev_answer": "<b>발생원인</b>\n\n<b>문을 닫은 후 전원 버튼을 누르세요. </b>\n\n<b>해결방안</b>\n\nNone\n\n<b>발생원인</b>\n\n<b>전화기를 스마트 진단 로고 (c,d)에 대십시오. </b>\n\n<b>해결방안</b>\n\n전화기의 마이크 부분이 제품을 향하고 있는지 확인하세요. \n\n<img style=\"display: block;margin: 0 auto;\" src=\"/image_db/washing_machine/MFL71485465/troubleshooting/diagnosing_a_fault/smart_diagnosis.png\"/>\n\n<b>발생원인</b>\n\n<b>물온도 버튼을 소리가 날 때까지 길게 누르세요. </b>\n\n<b>해결방안</b>\n\n물온도 버튼을 누르기 전 다른 버튼이나 다이얼을 조작하였다면 전원을 끈 다음 처음부터 다시 시작하세요. 스마트 진단을 위한 데이터 전송 중에는 전화기를 제품에 계속 댄 채 대기하세요.  화면에 데이터 전송을 위한 남은 시간이 표시됩니다. 전송음이 귀에 거슬릴 수 있으나 정확한 고장 진단을 위해 소리가 멈출 때까지 전화기를 떼지 마세요. \n\n<b>발생원인</b>\n\n<b>데이터 전송 완료 후에는 스마트 진단 결과가 애플리케이션에 표시됩니다. </b>\n\n<b>해결방안</b>\n\n데이터 전송이 완료되면 전송 완료 표시와 함께 수 초 후 자동으로 제품의 전원이 꺼집니다. \n\n",
                    "prev_question": "경고음으로 결함을 진단하는 방법은 무엇입니까?"
                },
                "request_id": 8
            }
        }
        self.valid_post_and_check(query_data, expected_resp_data)