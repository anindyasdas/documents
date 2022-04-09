"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: purnanaga.nalluri@lge.com
"""
import logging as logger
from functools import reduce
from ..constants import params
from apps.ker_ko.knowledge_extraction.knowledge.database import DBInterface

logger = logger.getLogger("django")

# status can be one of asking_question, satisfied_with_results, not_satisfied_with_results,


class HybridApproachDialogManager(object):
    def __init__(self):
        # DBInterface instance
        self.db_interface = DBInterface()

    def handle_user_query(self, user_question, nlp_module_info, part_no, client_type, prev_context, hybrid_response):
        """
        handles user query and
        Args:
            user_question: user query
            nlp_module_info: information of classifier and similarity keys
            part_no: part number of the manual for which user is asking query
            client_type: client type
            prev_context: context information about previous successful QA results
            hybrid_response: dictionary object of having ker response

        Returns:
            query_response : KER response
        """
        hybrid_response_status = hybrid_response["status"]
        # Default response_code
        response_code = params.ExternalErrorCode.MKG_SUCCESS

        classifier_info, similarity_info = nlp_module_info

        if not similarity_info:
            response_code = params.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND

        query_response = {}
        if response_code is params.ExternalErrorCode.MKG_SUCCESS:
            try:
                if hybrid_response_status == "asking_question":
                    # Get the top 5 results from text similarity send it back to the user
                    query_response["hybrid_response"] = hybrid_response
                    query_response["hybrid_response"]["mapped_keys"] = {classifier_info["section"] + " >> " + each_tx_sim_match["key"]: each_tx_sim_match["score"]
                                                                        for each_tx_sim_match in similarity_info}
            except Exception as e:
                logger.exception("some exception in handle_user_query", e)
                response_code = params.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND
                query_response["hybrid_response"] = {}
                query_response["hybrid_response"]["mapped_keys"] = {}

        # Code to add the context
        query_response["ker_context"] = prev_context

        # Code to add the model no
        query_response["part_no"] = part_no
        query_response["question"] = user_question

        # Code to Add the response code i.e., http_error_code
        query_response["query_response"] = params.ResponseCode.SUCCESS
        query_response["response_code"] = response_code
        resp_msg = params.ExternalErrorMsgs.ERR_MSGS[response_code][params.ExternalErrorMsgs.MSG]
        query_response["response_message"] = resp_msg

        return query_response

    def get_ts_section_causes(self, product_entity_type, section, part_no):
        """
        Get the TS section causes(l2 keys) for the given model no
        Args:
            product_entity_type : product type
            section: Section from the manual (Troubleshooting/ Operation etc) in Korean
            part_no: part_no from the frontend app

        Returns: response_code : response code in integer
            answer : Query response where in the answer will be in the format as below
            [ "cause1", "cause 2"...]
        """
        logger.debug("input : section: {} part_no: {} ".format(product_entity_type, section, part_no))
        # Default answer when the response
        answer = []
        raw_data_from_db, response_code = self.db_interface.get_ts_section_causes_from_kg(product_entity_type,part_no)
        logger.debug(
            "from db interface : raw_data_from_db: {} response_code: {} ".format(raw_data_from_db, response_code))
        # Map the response code and response msg by mapping external error codes to internal error codes
        if response_code == params.ResponseCode.SUCCESS:
            answer, response_code = self._extract_causes_from_db_results(raw_data_from_db, response_code)
        else:
            response_code = params.ExternalErrorCode.internal_to_ext_err_code[response_code]

        # update error code when list is empty
        if len(answer) == 0:
            response_code = params.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND
        logger.debug("output : response: {} ".format(response_code,answer))
        return response_code,answer

    def _extract_causes_from_db_results(self, raw_data_from_db, response_code):
        answer = []
        # Success and raw_data_from_db is not Empty
        if raw_data_from_db:
            response_code = params.ExternalErrorCode.internal_to_ext_err_code[response_code]
            for result in raw_data_from_db:
                for key, keyvalue in result.items():
                    # check the key and fill the respective dict
                    if key == params.REASON_KEY:
                        answer=keyvalue
        else:
            response_code = params.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND
        return answer, response_code

    def get_section_contents(self, section, part_no):
        """
        Get the section contents like problem type and problems (2 level information)
        Args:
            section: Section from the manual (Troubleshooting/ Operation etc) in Korean
            part_no: Model number from the frontend app

        Returns: Query response where in the answer will be in the format as below
            {
            answer: {
            "category1_under_chosen_section": {"prob_or_section":"kg", "prob_or_section_2":"kg"},
            "category2_under_chosen_section": {"prob_or_section":"kg", "prob_or_section_2":"kg"}
            }
            }
        """
        logger.debug("input : section: {} model_no: {} ".format(section, part_no))
        response = {}
        # Default answer when the response
        answer = {}

        raw_data_from_db, response_code = self.db_interface.get_section_contents_from_kg(section, part_no)
        logger.debug("from db interface : raw_data_from_db: {} response_code: {} ".format(raw_data_from_db, response_code))
        # Map the response code and response msg by mapping external error codes to internal error codes
        if response_code == params.ResponseCode.SUCCESS:
            # Success and raw_data_from_db is not Empty
            if raw_data_from_db:
                answer = self._process_content_from_db(raw_data_from_db, section)
                response[params.IOConstants.RESP_CODE] = params.ExternalErrorCode.internal_to_ext_err_code[response_code]
            else:
                response[params.IOConstants.RESP_CODE] = params.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND
        else:
            response[params.IOConstants.RESP_CODE] = params.ExternalErrorCode.internal_to_ext_err_code[response_code]

        error_msgs_dict = params.ExternalErrorMsgs.ERR_MSGS
        actual_resp_code = response[params.IOConstants.RESP_CODE]
        response[params.IOConstants.RESP_MSG] = error_msgs_dict[actual_resp_code][params.ExternalErrorMsgs.MSG]
        response[params.IOConstants.ANSWER] = answer

        # Fill the other default values
        # Code to add the context
        response[params.IOConstants.KER_CNTXT] = {}
        # Adding model and Question to the response
        response[params.IOConstants.PART_NO] = part_no
        response[params.IOConstants.QUESTION] = ""
        logger.debug("output : response: {} ".format(response))
        return response

    def _process_content_from_db(self, raw_data_from_db, section):
        """Process raw data from DB"""
        final_answer = {}  # {"Error Messages": {"prob_or_section": "kg", "prob_or_section_2": "kg"}}
        if section == params.IOConstants.HY_TROUBLESHOOTING:
            convert_raw_data_to_answer = lambda accumulator_dict, val: accumulator_dict.update(
                {self._get_korean_name(val["problem_type"]): {each_problem: "kg" for each_problem in val["problems"]}}) or accumulator_dict

            final_answer = reduce(convert_raw_data_to_answer, raw_data_from_db, {})
        # {"Operation Sub Section 1": "kg", "Operation Sub Section 2": "kg"}
        elif section == params.IOConstants.HY_OPERATION:
            final_answer = {each_operation_section: "kg" for each_operation_section in raw_data_from_db[0]["sub_sections"]}
        return final_answer

    def _get_korean_name(self, section_name_in_english):
        """To Map with the Korean Name for the english Section names stored in the DB"""
        section_name_in_korean = section_name_in_english

        for korean_name, english_equivalent in params.ExtractionConstants.SECTION_NAME_TRANSLATE.items():
            if english_equivalent == section_name_in_english:
                section_name_in_korean = korean_name
                break
        return section_name_in_korean
