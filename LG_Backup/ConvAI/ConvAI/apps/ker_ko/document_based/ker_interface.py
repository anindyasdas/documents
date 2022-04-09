# -------------------------------------------------
# Copyright(c) 2022-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------

# Standard library imports
import re
import sys
import json
import os
import importlib

# Local application imports
from apps.ker_ko.document_based.constants import EMB_FILE_PATH
from apps.ker_ko.document_based.qa_engine import DocBasedQaEngine
from apps.ker_ko.document_based.utils import json_to_html, get_section_section_title, create_standardize_json
from apps.ker_ko.knowledge_extraction.constants import params as cs


kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)
# commenting out django but might need in future logger = logger.getLogger("django")


class KerInterface(object):
    # Load the meta embedding json file as a class variable
    with open(os.path.join(EMB_FILE_PATH, "meta_emb.json"), 'r', encoding='utf-8-sig') as meta_emb_json_file:
        logger.debug("loading the meta embedding_json file as a class variable")
        meta_embedding_json = json.load(meta_emb_json_file)

    def __init__(self):
        """
        Class for interacting with the external ker module
        """
        logger.debug("init KerInterface")
        self.previous_part_no = ""
        self.ques = ""
        self.section = ""
        self.qa_flag = ""

    # Public functions
    def get_mapped_keys_and_scores(self, user_query, part_no):
        """
        To get the mapped keys and scores closely matching with the user query

        Args:
            user_query: Question from the user to get the mapped keys and scores, Ex: "세제는 어떻게 사용하나요?"
            part_no: part number, Ex: "MFL71485465"

        Returns:
            A standardised dictionary containing the answer, response_code
            
                Ex: {"answer": {'사용하기 >> 세제 넣고 사용하기': 63, '사용하기 >> 세탁기 사용하기': 59, '사용하기 >> 세제 넣고 사용하기 주의': 55,
                          '위의 어느 것도': 0.0}. "response_code"=0, "standardized"=True}
        """ 
        result_dict_section="" 
        result_dict_standardized=0  
        is_retrieval_flag=False
        if part_no == "":
            logger.warning("Part No. is Empty =%s", part_no)
            result_dict_response={} 
            result_dict_response_code= cs.ExternalErrorCode.MKG_QUERY_PART_NO_NOT_FOUND 
            return create_standardize_json(result_dict_response, result_dict_section, result_dict_standardized, result_dict_response_code, is_retrieval_flag)
        if (part_no != self.previous_part_no) or (self.previous_part_no == "" and part_no != ""):
            partno_found, self.embedding_list, response_code = self._check_part_no(part_no)
            logger.info("Part_no_found =%s", partno_found)
            logger.info("Response Code =%s", response_code)
            if not partno_found:
                logger.warning("Requested part NOT Supported =%s",  part_no) 
                result_dict_response={}  
                if response_code!= cs.ExternalErrorCode.MKG_SUCCESS: 
                    result_dict_response_code= response_code 
                else: 
                    result_dict_response_code=cs.ExternalErrorCode.MKG_QUERY_PART_NO_NOT_FOUND 
                return create_standardize_json(result_dict_response, result_dict_section, result_dict_standardized, result_dict_response_code, is_retrieval_flag) 
            else:
                logger.info("Part number changed= %s", part_no) 
                self.previous_part_no = part_no
                self.qa_engine = DocBasedQaEngine(self.embedding_list)
                self.ques = user_query
        self.qa_flag = 'doc'
        result_dict_response= self.qa_engine.answer_question(user_query)
        result_dict_response_code=cs.ExternalErrorCode.MKG_SUCCESS
        return create_standardize_json(result_dict_response, result_dict_section, result_dict_standardized, result_dict_response_code, is_retrieval_flag)

    def view_manual_content(self, section="", part_no=""):
        """
        For getting the sub-sections under a section

        Args:
            section: Main section in the manual Ex: "설치하기"
            part_no: The part number, Ex: "MFL71485465"

        Returns: A list of sub-sections under a given section
            Ex: ['옮길 때 알아두기', '운송용 고정볼트 제거하기', '접지할 때 알아두기', '설치용 부자재 별매품 안내', '호스', '수평 조절하기',
                          '미끄럼 방지 시트 설치하기']
        """
        self.section = section
        if part_no == "":
            logger.warning("send part no")
            return
        if (part_no != self.previous_part_no) or (self.previous_part_no == "" and part_no != ""):
            partno_found, self.embedding_list, _ = self._check_part_no(part_no)
            if not partno_found:
                logger.warning("requested part NOT Supported \n")
                return
            else:
                logger.info("Part number changed")
                self.previous_part_no = part_no
                self.qa_engine = DocBasedQaEngine(self.embedding_list)
                self.qa_engine.manual_view_loader()
        if not self.qa_engine.manual_content_dict:
            self.qa_engine.manual_view_loader()
            logger.debug("section: %s", self.section)
        self.qa_flag = 'manual'
        if self.section in self.qa_engine.manual_content_dict:
            logger.debug(len(self.qa_engine.manual_content_dict))
            logger.debug("keys: %s", self.qa_engine.manual_content_dict[section]["key"])
            return self.qa_engine.manual_content_dict[self.section]["key"]
        else:
            return []

    def get_doc_retrieval_output(self, options="위의 어느 것도", ques="", part_no=""):
        """
        For getting the answer from the json file. Output will be either in the form of feature dictionary or a html

        Args:
            options: the selected option from the mapped keys or from manual content sub-sections
            ques: the current user question
            part_no: part number

        Returns: A nested dictionary with the answer (list of features), response code and the standardization level
        """
        if self.qa_flag == "manual":
            options = options.split(">>")[-1].strip()
            keys_option = self.qa_engine.manual_content_dict[self.section]["key"]
            values_option = self.qa_engine.manual_content_dict[self.section]["value"]
        elif self.qa_flag == "doc":
            keys_option = self.qa_engine.keys_option
            values_option = self.qa_engine.values_option

        try:
            idx = keys_option.index(options)
            val_string = values_option[idx]
            logger.debug("val_string: %s", val_string)
            new_str = self._create_answer(val_string)
        except Exception as e:
            logger.exception(e)
            val_string = ''
            new_str = self._create_answer(val_string)
        return new_str

    # Private functions
    def _check_part_no(self, part_no):
        response_code= cs.ExternalErrorCode.MKG_SUCCESS
        partno_found = False
        embed_file=[]
        emb_json_keys = list(KerInterface.meta_embedding_json.keys())
        for partno_key in emb_json_keys:
            if partno_key == part_no:
                partno_found = True
                emb_file_name=KerInterface.meta_embedding_json[partno_key]  
                try: 
                    embed_file=self._load_embedding_file(emb_file_name)
                except Exception as e:
                    logger.exception(e)
                    embed_file=[]
                    response_code= cs.ExternalErrorCode.MKG_FILE_OPEN_ERROR
                return partno_found, embed_file, response_code
        return partno_found, embed_file, response_code
    
    def _load_embedding_file(self, emb_file_name):
        """
        reads the embedding file, load and return the embedding list containing
        embeddings, keys, normalized keys, values, json file name

        Parameters
        ----------
        emb_file_name : TYPE str
            DESCRIPTION. name of the embedding file

        Returns
        -------
        embedding_list : TYPE list
            DESCRIPTION. list containing the embedding matrix,
            keys, normalized keys, values, heading, json file name

        """
        with open(os.path.join(EMB_FILE_PATH, emb_file_name), 'r', encoding='utf-8-sig') as emb_json_file: 
            embedding_list= json.load(emb_json_file)
        return embedding_list
        

    def _create_answer(self, val):
        is_retrieval=True
        logger.debug(val)
        if val == '':
            json_val = {}
            section = 'Key Not Found'
            section_title = 'Exception'
            features_val, standardized = self.qa_engine.json_parser.standardize_doc_based_json(json_val, section_title,
                                                                                               section)
            features_val[0]["feature"] = section_title
            features_val[1]["feature"] = ''
            response_code = cs.ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND
            new_str = create_standardize_json(features_val, section, standardized, response_code, is_retrieval)
            return new_str
        self.jsonfile = self.qa_engine.jsonfile
        logger.debug("jsonfile %s", self.qa_engine.jsonfile_str)
        logger.debug("val %s", val)
        answer_ret = eval(self.qa_engine.jsonfile_str + val)
        logger.debug("answer_ret %s", answer_ret)
        new_str = json.dumps(answer_ret, indent=6)
        new_str = re.sub("hph", "-", new_str)
        json_val = json.loads(new_str)
        section, section_title = get_section_section_title(val)
        logger.debug("raw json : %s", json_val)
        features_val, standardized = self.qa_engine.json_parser.standardize_doc_based_json(json_val, section_title,
                                                                                           section)
        logger.debug("returned features : %s", features_val)
        if not standardized:
            features_val[0]["feature"] = section_title
            html = '<html><body><h1>' + section_title + '</h1>'
            html = json_to_html(json_val, html, '')
            html += '</body></html>'
            features_val[1]["feature"] = html

        response_code = cs.ExternalErrorCode.MKG_SUCCESS
        standardized_answer = create_standardize_json(features_val, section, standardized, response_code, is_retrieval, val)
        logger.debug("standardized_answer : %s", standardized_answer)
        return standardized_answer
    
    def get_passages(self):
        return self.qa_engine.load_passages()


if __name__ == "__main__":
    driver = KerInterface()
    x = driver.get_mapped_keys_and_scores("세탁기를 사용하기 전에 알아야 할 좋은 점은 무엇인가요", "F215DD")
    print(x)
    x = driver.get_mapped_keys_and_scores("세제는 어떻게 사용하나요?", "F215DD")
    print(x)
    x = driver.get_mapped_keys_and_scores("섬유 유연제 넣고 사용하기", "F246DGD")
    print(x)
    y = list(x.keys())[0]
    z = driver.get_doc_retrieval_output(options=y, ques="섬유 유연제 넣고 사용하기", part_no="MFL71485465")
    u = driver.view_manual_content(section="설치하기", part_no="MFL71485465")
    v = driver.get_doc_retrieval_output(options="설치용 부자재 별매품 안내", ques="", part_no="MFL71485465")
