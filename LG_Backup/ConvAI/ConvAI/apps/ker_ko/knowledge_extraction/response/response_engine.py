"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com
"""
import json
import os
import random
from configparser import ConfigParser

from ..constants import params as cs
# KMS Logger
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

CONFIG_PATH = (os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..',
                 'config', 'configuration.ini')))


class ResponseEngine(object):
    """
    defines the method to generate template responses
    """

    def __init__(self):
        self.response_template = {}
        # Use this variable for running Natural Language response generation or not
        self.use_nlg_for_response = False
        # nlg_eng is used to give a NLG based response
        self.nlg_eng = None
        if self.use_nlg_for_response:
            self.nlg_eng = NlgEngine()
        try:
            # Loading the response template file from config
            config_parser = ConfigParser()
            config_parser.read(CONFIG_PATH)
            logger.info("Config path " + CONFIG_PATH)
            # get ip address,port and image db
            self.image_path, self.ip_address, self.port_number = cs.get_image_db_path()
            abspath_path = os.path.abspath(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), '..', ))
            json_file_path = os.path.join(abspath_path,
                                          config_parser.get("template_response",
                                                            "template_response_mapping"))
            json_file = open(json_file_path, )

            self.response_template = json.load(json_file)

            # Closing file
            json_file.close()

            logger.debug("SchemaLoader, {} success : {}".format(
                "init function", "reading schema file success"))
        except Exception as exe:
            logger.exception(
                "ResponseEngine, {} failed : {}".format("init function",
                                                        "reading template file error : " + str(exe)))

    def make_response(self, results, section, user_question=None):
        """
        Generate template responses for predicted answers.

        Args:
            results: The raw results from the database
            section: The section for which template response should be generated
            user_question: The question that was asked by the user
        Returns:
            template answer for results
        """
        logger.info("results:{0}, section:{1}, user_question={2}".format(results, section, user_question))
        # To create an answer based on the template
        answer = ""
        # if the section is troubleshooting call create template for troubleshooting
        try:
            section = section.lower()
            if section == cs.XMLTags.TROUBLESHOOT_TAG.lower():
                ts_template = self.response_template[cs.XMLTags.TROUBLESHOOT_TAG]
                answer = self._template_answer_troubleshooting(results, ts_template)
            # if the section is specification call create template for specification
            elif section == cs.XMLTags.SPECIFICATION_TAG.lower():
                sp_template = self.response_template[cs.XMLTags.SPECIFICATION_TAG]
                answer = self._template_answer_specification(results, sp_template, user_question)
            elif section == cs.XMLTags.OPERATION_TAG.lower():
                op_template = self.response_template[cs.XMLTags.OPERATION_TAG]
                answer = self._template_answer_operation(results, op_template, user_question)
        except Exception as exe:
            logger.exception("Exception in make resp : %s", exe)
            return answer, cs.ResponseCode.RESPONSE_GEN_ERROR

        # If the answer is blank send Data not available
        if not answer:
            answer = "Data not available"

        return answer, cs.ResponseCode.SUCCESS

    # for future ref def _template_answer_troubleshooting(self, results, ts_template):
    #     """
    #     To create a template response for troubleshooting section
    #     Args:
    #         results: the raw results from the data base
    #         ts_template: he response template for troubleshooting
    #
    #     Returns: Response answer for troubleshooting
    #     """
    #     # If the reasons and solutions are of the same length then call combined method
    #     # Or else call the normal method
    #     ts_results = results[cs.XMLTags.TROUBLESHOOT_TAG]
    #     reasons_temp = ts_results[cs.REASON_KEY]
    #     solutions_temp = ts_results[cs.SOLUTION_KEY]
    #     answer = ""
    #     if isinstance(reasons_temp, list) and isinstance(solutions_temp, list):
    #         if len(reasons_temp) == len(solutions_temp):
    #             answer = self._template_answer_troubleshooting_combined(results, ts_template)
    #         else:
    #             answer_reason = self._template_answer_troubleshooting_internal(results, ts_template, cs.REASON_KEY)
    #             answer_sol = self._template_answer_troubleshooting_internal(results, ts_template, cs.SOLUTION_KEY)
    #             if not answer_reason:
    #                 answer = answer_reason + answer_sol
    #             else:
    #                 answer = answer_reason + "\n\n" + answer_sol
    #     return answer

    def _get_reson_solution(self, result_list):

        reson_list = []
        sol_list = []
        medialist = []

        for res_sol_dict in result_list:
            reson_list.append(res_sol_dict[cs.REASON_KEY])
            sol_list.append(res_sol_dict[cs.SOLUTION_KEY])
            if cs.MEDIA in res_sol_dict:
                medialist.append(res_sol_dict[cs.MEDIA])
            else:
                medialist.append(dict())

        return reson_list, sol_list, medialist

    def _frame_reson_sol(self, reason, sol, media):


        temp_answer = ""
        prev_img_url = ""
        previous_cause = ""

        for idx in range(len(reason)):
            if reason[idx] != previous_cause:
                # Add a causes in korean for template answer
                temp_answer += "<b>" + cs.causes_korean_header + "</b>" + "\n\n"
                temp_answer += "<b>" + reason[idx] + "</b>" + "\n\n"
                # Add a solutions in korean for template answer
                temp_answer += "<b>" + cs.solutions_korean_header + "</b>" + "\n\n"
            temp_answer += sol[idx] + "\n\n"
            if (len(media) > 0) and (len(media[idx].keys()) > 0):
                img_path = media[idx][cs.MEDIA_URL]
                if (prev_img_url != img_path) and (img_path is not None) and (len(img_path) > 0):
                    prev_img_url = img_path
                    temp_answer += self._create_image_uri(media[idx][cs.MEDIA_URL]) + "\n\n"
            previous_cause = reason[idx]
        return temp_answer

    def _frame_trob_html_resp(self, reason, sol, media):
        """
        frame the HTML response for the operation section
        Args:
            results:result from retrieval engine
        return:
            return framed response
        """
        temp_answer = ""
        prev_img_url = ""

        reson_actual_size = len(list(set(reason)))

        if reson_actual_size == 1:
            # Add a causes in korean for template answer
            temp_answer += "<b>" + cs.causes_korean_header + "</b>" + "\n\n"
            temp_answer += "<b>" + reason[0] + "</b>" + "\n\n"
            # Add a solutions in korean template answer
            temp_answer += "<b>" + cs.solutions_korean_header + "</b>" + "\n\n"
            for idx in range(len(sol)):
                temp_answer += sol[idx] + "\n\n"
                if (len(media) > 0) and (len(media[idx].keys()) > 0):
                    img_path = media[idx][cs.MEDIA_URL]
                    if (prev_img_url != img_path) and (img_path is not None) and (len(img_path) > 0):
                        prev_img_url = img_path
                        temp_answer += self._create_image_uri(media[idx][cs.MEDIA_URL]) + "\n\n"

        else:
            temp_answer = self._frame_reson_sol(reason, sol, media)

        return temp_answer

    def _template_answer_troubleshooting(self, results, ts_template):
        """
        To create a template response for troubleshooting section
        Args:
            results: the raw results from the data base
            ts_template: he response template for troubleshooting

        Returns: Response answer for troubleshooting
        """
        # If the reasons and solutions are of the same length then call combined method
        # Or else call the normal method
        ts_results = results[cs.XMLTags.TROUBLESHOOT_TAG]
        cause_sol = ts_results[cs.IOConstants.CAUSES_SOL_KEY]
        reasons_temp, solutions_temp, media_list = self._get_reson_solution(cause_sol)
        answer = ""
        answer = self._frame_trob_html_resp(reasons_temp, solutions_temp, media_list)
        return answer

    def _template_answer_troubleshooting_internal(self, results, template, result_type):
        """
        To create a template response for troubleshooting section
        Args:
            results: the raw results from the data base
            template: The response template for troubleshooting
            result_type: the type of result Ex : reason or solution for troubleshooting

        Returns: Response answer for troubleshooting

        """
        singular_template = []
        plural_template = []
        if result_type == cs.REASON_KEY:
            singular_template = template[cs.TR_CAUSE_SINGULAR]
            plural_template = template[cs.TR_CAUSE_PLURAl]
        elif result_type == cs.SOLUTION_KEY:
            singular_template = template[cs.TR_SOL_SINGULAR]
            plural_template = template[cs.TR_SOL_PLURAL]

        ts_results = results[cs.XMLTags.TROUBLESHOOT_TAG]
        answer = ""
        if ts_results[result_type] is not None and isinstance(ts_results[result_type], list):
            if len(ts_results[result_type]) == 1:
                temp_ans = ''
                temp_ans = random.choice(singular_template)
                temp_ans = temp_ans + '\n' + ts_results[result_type][0]
                answer = answer + '\n' + temp_ans
                answer = answer.strip()

            elif len(ts_results[result_type]) > 1:
                temp_ans = ''
                temp_ans = random.choice(plural_template)
                numbering = 0
                logger.debug("answer : %s", ts_results[result_type])
                temp_ans_list = ""
                for answer_frm_list in ts_results[result_type]:
                    numbering = numbering + 1
                    temp_ans_list += '\n' + str(numbering) + "." + answer_frm_list
                temp_ans = temp_ans + '\n' + temp_ans_list
                answer = answer + '\n' + temp_ans
                answer = answer.strip()

        return answer

    def _template_answer_specification(self, results, template, specification_question=None): # pragma: no cover
        """
        To create a template response for specification section
        Args:
            results: the raw results from data base
            template: the template for specification obtained from
            response_template json

        Returns: Response template answer for specification

        """
        logger.debug('Resp engine : %s', results)
        if cs.RS_PRODUCT_TYPE in results:
            response_key_template = template[cs.SP_RESPONSE_KEY_WP]
        else:
            response_key_template = template[cs.SP_RESPONSE_KEY]

        # To handle new value(answer value) response format (List of dictionaries)
        template_value = self._create_template_value_for_spec(results)

        # if NLG is enabled use nlg or give the template based response
        answer = ""
        if self.use_nlg_for_response:
            answer = self.nlg_eng.get_nlg_output(specification_question, template_value)
        else:
            answer = response_key_template.format(response_key=results[cs.XMLTags.SPECIFICATION_TAG][cs.RESPONSE_KEY],
                                                  model=results[cs.MODEL_TR],
                                                  value=template_value,
                                                  product_type=results.get(cs.RS_PRODUCT_TYPE, ""))
        logger.debug('Framed resp : %s', answer)
        return answer

    def _create_template_value_for_spec(self, results): # pragma: no cover
        """
            To handle new value response format (List of dictionaries) and create a template response value
        Args:
            results: Specification results from retrieval engine

        Returns:
            Template response for value
        """

        template_value = ""
        if results[cs.XMLTags.SPECIFICATION_TAG][cs.RESPONSE_KEY] == 'battery run time':
            value_template_temp_1_battery = '{value} using {usage} and {no_of_batteries} battery'
            value_template_temp_2_battery = '{value} using {usage} and {no_of_batteries} batteries'
            template_value_list = []
            for each_value in results[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE]:
                if each_value['no_of_batteries'] == 'one':
                    template_value_list.append(value_template_temp_1_battery.format(value=each_value[cs.VALUE],
                                                                                    usage=each_value['usage'],
                                                                                    no_of_batteries=each_value[
                                                                                        'no_of_batteries']))
                elif each_value['no_of_batteries'] == 'two':
                    template_value_list.append(value_template_temp_2_battery.format(value=each_value[cs.VALUE],
                                                                                    usage=each_value['usage'],
                                                                                    no_of_batteries=each_value[
                                                                                        'no_of_batteries']))
            template_value = ", ".join(template_value_list)
        else:
            template_value = ", ".join(
                [result[cs.VALUE] for result in results[cs.XMLTags.SPECIFICATION_TAG][cs.VALUE]])
        return template_value

    def _template_answer_troubleshooting_combined(self, results, template):
        """
        Create a template response for troubleshooting section
        reasons and solutions together
        Args:
            results: the raw results from the data base
            template: The response template for troubleshooting
        """
        ts_results = results[cs.XMLTags.TROUBLESHOOT_TAG]
        output = {}
        for x, y in zip(ts_results[cs.REASON_KEY], ts_results[cs.SOLUTION_KEY]):
            if x in output and isinstance(output[x], list):
                output[x].append(y)
            elif x in output and isinstance(output[x], str):
                temp = [output[x], y]
                output[x] = temp
            else:
                output[x] = y

        answer_to_return = ""
        for reason_temp in output:
            temp_reason = random.choice(template[cs.TR_CAUSE_SINGULAR])
            temp_reason = temp_reason + '\n' + reason_temp

            temp_sol = ''
            temp_sol_key = output[reason_temp]
            if isinstance(temp_sol_key, list):
                temp_sol = random.choice(template[cs.TR_SOL_PLURAL])
                numbering = 0
                temp_sol_list = ""
                for solution in temp_sol_key:
                    numbering += 1
                    temp_sol_list += '\n' + str(numbering) + "." + solution
                temp_sol = temp_sol + '\n' + temp_sol_list
            else:
                temp_sol = random.choice(template[cs.TR_SOL_SINGULAR])
                temp_sol = temp_sol + '\n' + temp_sol_key

            answer_to_return += "\n\n" + temp_reason + '\n' + temp_sol
            answer_to_return.strip()

        return answer_to_return

    def _create_image_uri(self, path):
        """
        Frame image path URI with IP and hosting directory
        :param path:
        :return:
        """
        image_uri = "<img style=\"display: block;margin: 0 auto;\" src=\"" + "/" + self.image_path + "/" + path + "\"/>"
        return image_uri

    def _template_answer_operation(self, results, op_template, user_question=None):
        """
        Function to create template response for Operation Section
        Args:
            results: The dictionary of operation information fetched from DB
            op_template: The operation template defined in response_template.json for operation

        Returns:
            template response for operation
        """
        op_template_answer = ""

        try:
            temp_answer = ""
            module_used = results[cs.XMLTags.OPERATION_TAG][cs.MODULE_FLAG]
            question_type = results[cs.XMLTags.OPERATION_TAG][cs.QUESTION_TYPE]

            logger.debug("module_used : %s,question_type : %s op_template=%s", module_used, question_type, op_template)
            op_template = op_template[cs.SP_RESPONSE_KEY]

            if (module_used == cs.RetrievalConstant.PARA_QA) and \
                    (question_type == cs.RetrievalConstant.FACTOID_TYPE) and (self.use_nlg_for_response == True):
                temp_answer = self._template_answer_operation_paraqa_factoid(results, op_template, user_question)
                temp_answer = self.nlg_eng.get_nlg_output(user_question, temp_answer)
                logger.debug("Operation template answer after nlg \n: " + temp_answer)
            else:
                temp_answer = self._frame_html_resp(results)
                logger.debug("Operation template answer \n: " + temp_answer)

            op_template_answer = op_template.format(
                response_key=results[cs.XMLTags.OPERATION_TAG][cs.RESPONSE_KEY][cs.PROP_VALUE])

            op_template_answer = op_template_answer + "\n" + temp_answer

            logger.debug("Operation template answer \n: " + op_template_answer)
        except Exception as e:
            logger.exception('Exception in framing template response for operation' + str(e))

        return op_template_answer

    def _check_fill_image_details_in_desc(self, desc):
        """
        check the embedded image details in description text and frame the HTML image tags

        Ex: In desc the image details will be embedded like
        건조 중 발생하는 진동으로 건조물이 건조 선반에서 떨어질 수 있습니다.
        <img>{\"img_path\": \"dryer/MFL71424392/operation/건조_선반을_사용하여_건조하기/rack_dry_vivace_03.png\"
        , \"file_size\":6,\"type\": \"png\"}</img>

        Args:
            desc: Description string
        Return:
            Description with HTML image tag details
        """
        while True:
            if ("<img>" in desc) and ("</img>" in desc):
                idx = desc.index("<img>")
                # get the start index of <img>
                start = idx + 4
                logger.debug("index of img end : %s",desc.index("</img>"))
                # get the index of the </img> from the desc string
                end_idx = desc.index("</img>") + 5
                # convert the image detail in string format to dict
                img_detail = eval(desc[start + 1:end_idx - 5].strip())
                logger.debug("img_detail : %s", img_detail)
                desc = desc[:idx] +"<b><b>" + self._create_image_uri(img_detail['img_path']) +"<b><b>"+ desc[end_idx + 1:]
                print(desc)
            else:
                break
        return desc

    def _frame_html_resp(self, results):
        """
        frame the HTML response for the operation section
        Args:
            results:result from retrieval engine
        return:
            return framed response
        """
        temp_answer = ""
        prev_img_url = ""
        prev_img_name = ""
        prev_feature = ""
        prev_desc = ""

        op_feature_list = results[cs.XMLTags.OPERATION_TAG][cs.FEATURES]

        for feature in op_feature_list:
            if feature[cs.FEATURE] is not None:

                cur_feature = feature[cs.FEATURE]

                # check whether the previous and current feature text is same or not
                if cur_feature != prev_feature:
                    prev_feature = cur_feature
                    temp_answer += "<b>" + cur_feature + "</b>" + "\n\n"

                temp_answer, prev_img_url, prev_img_name = \
                    self._check_media_details(feature, prev_img_name, prev_img_url, temp_answer)

                desc_dup_condition = [(cs.DESC_KEY in feature),(feature[cs.DESC_KEY] is not None),(prev_desc != feature[cs.DESC_KEY])]
                if all(desc_dup_condition):
                    prev_desc = feature[cs.DESC_KEY]
                    temp_answer += self._check_fill_image_details_in_desc(feature[cs.DESC_KEY]) + "\n\n"
        return temp_answer

    def _check_media_details(self, feature, prev_img_name, prev_img_url, temp_answer):
        """
        check for the current and previous image details are same or not

        Args:
            feature : current feature text
            prev_img_name: previous image name
            prev_img_url: previous image path URL
            temp_answer: template answer framed previously

        Returns:
            prev_img_name: previous image name
            prev_img_url: previous image path URL
            temp_answer: template answer framed previously

        """
        if cs.MEDIA in feature:
            img_path = feature[cs.MEDIA][cs.MEDIA_URL]
            img_name = img_path.split("/")[-1]
            # check whether the previous and current image name is same or not
            if ((prev_img_url != img_path) and (img_path is not None) and (len(img_path) > 0)) and (
                    img_name != prev_img_name):
                prev_img_url = img_path
                prev_img_name = img_name
                temp_answer += self._create_image_uri(img_path) + "\n\n"
        return temp_answer, prev_img_url, prev_img_name

    def _template_answer_operation_paraqa_factoid(self, results, op_template, user_question=None):# pragma: no cover
        """
        Function to create template response for Operation Section
        Args:
            results: The dictionary of operation information fetched from DB
            op_template: The operation template defined in response_template.json for operation

        Returns:
            template response for operation
        """
        op_template_answer = ""
        prev_img_url = ""
        try:
            temp_answer = ""
            module_used = results[cs.XMLTags.OPERATION_TAG][cs.MODULE_FLAG]
            question_type = results[cs.XMLTags.OPERATION_TAG][cs.QUESTION_TYPE]

            logger.debug("module_used : %s,question_type : %s", module_used, question_type)

            op_feature_list = results[cs.XMLTags.OPERATION_TAG][cs.FEATURES]

            for feature in op_feature_list:
                temp_answer += feature[cs.FEATURE]
                if cs.MEDIA in feature:
                    img_path = feature[cs.MEDIA][cs.MEDIA_URL]
                    if (prev_img_url != img_path) and (img_path is not None) and (len(img_path) > 0):
                        prev_img_url = img_path
                        temp_answer += self._create_image_uri(feature[cs.MEDIA][cs.MEDIA_URL]) + "\n\n"

                if (cs.DESC_KEY in feature) and (feature[cs.DESC_KEY] is not None):
                    temp_answer += " " + feature[cs.DESC_KEY]

            logger.debug("Operation template answer before nlg \n: " + temp_answer)
            op_template_answer = temp_answer.strip()

            logger.debug("Operation template answer \n: " + op_template_answer)
        except Exception as e:
            logger.exception('Exception in framing template response for operation' + str(e))

        return op_template_answer


if __name__ == "__main__": # pragma: no cover
    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    # creating instance of response engine
    engine = ResponseEngine()
    test = {
        "model": "WGS2435",
        cs.XMLTags.TROUBLESHOOT_TAG: {
            'reason': ['This is a test reason 1', 'This is a test reason 2', 'This is a test reason 1',
                       'This is a test reason 1'],
            'solution': ['The use of hoses designed to limit leaks is not recommended.',
                         'If flow is too low, contact a plumber.', 'Contact a plumber.',
                         'Contact a plumber2.'],
        },
        cs.XMLTags.SPECIFICATION_TAG: {
            "value": ["30 Volts"],
            "response_key": "voltage"
        }
    }
    # Test Cases for handling new value format (list of dictionaries) Specification
    test_case_for_spec = {
        "model": "WGS2435",
        cs.XMLTags.SPECIFICATION_TAG: {
            "value": [{'key': 'net weight', 'range': '', 'value': 'approximately 5.67 lb (2.57 kg)'}],
            "response_key": "net weight"
        }
    }
    test_case_battery_run_time = {
        "model": "WGS2435",
        cs.XMLTags.SPECIFICATION_TAG: {
            "value": [{'key': 'battery run time', 'range': '', 'no_of_batteries': 'two', 'mode': 'normal',
                       'usage': 'power drive nozzle', 'value': 'up to 80 minutes in normal mode'},
                      {'key': 'battery run time', 'range': '', 'no_of_batteries': 'two', 'mode': 'power',
                       'usage': 'other than the power drive nozzle', 'value': 'up to 60 minutes in power mode'},
                      {'key': 'battery run time', 'range': '', 'no_of_batteries': 'two', 'mode': 'turbo',
                       'usage': 'power drive nozzle', 'value': 'up to 12 minutes in turbo mode'},
                      {'key': 'battery run time', 'range': '', 'no_of_batteries': 'two', 'mode': 'power',
                       'usage': 'power drive nozzle', 'value': 'up to 40 minutes in power mode'},
                      {'key': 'battery run time', 'range': '', 'no_of_batteries': 'two', 'mode': 'normal',
                       'usage': 'other than the power drive nozzle', 'value': 'up to 120 minutes in normal mode'},
                      {'key': 'battery run time', 'range': '', 'no_of_batteries': 'two', 'mode': 'turbo',
                       'usage': 'other than the power drive nozzle', 'value': 'up to 14 minutes in turbo mode'}],
            "response_key": "battery run time"
        }
    }

    # print(engine.make_response(test_case_battery_run_time, cs.XMLTags.SPECIFICATION_TAG))

    test_case_for_operation = {
        "model": "WGS2435",
        "operation": {
            "desc": ["Temp desc 1", "Temp desc 2"],
            "feature": ["Temp feature 1", "Temp feature 2"],
            "response_key": {
                "Intent": "HAS_CHECKLIST",
                "prob_key": "direct/extra_info",
                "prob_value": "before use/sabbath mode/control panel",
                "prob_value_specific": "before use",
                "query_intent": "reason"
            }
        }
    }

    print(engine.make_response(test_case_for_spec, "specification", "What is the net weight of my washing machine?"))
    print(engine.make_response(test_case_battery_run_time, "specification", "What is the battery run time?"))
