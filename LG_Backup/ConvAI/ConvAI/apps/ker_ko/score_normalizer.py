"""
/*-------------------------------------------------
* Copyright(c) 2022-2023 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
from fuzzywuzzy import fuzz

from .knowledge_extraction.constants import params as cs

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class ScoreNormalizer(object):
    """
    defines the method to normalize scores of similarity keys and get the
    output
    """
    __instance = None
    tr_score = 20
    max_score_for_rule_based = 80

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if ScoreNormalizer.__instance is None:
            ScoreNormalizer()
        return ScoreNormalizer.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if ScoreNormalizer.__instance is not None:
            logger.error("ScoreNormalizer is not instantiable")
            raise Exception("ScoreNormalizer is not instantiable")
        else:
            logger.debug("*** ScoreNormalizer constructor")
            # instance for IntentSchema loading
            from .knowledge_extraction.knowledge_retrieval_engine import IntentSchema
            self.intent_schema = IntentSchema.get_instance()
            ScoreNormalizer.__instance = self

    def _normalize_score(self,raw_text, similarity_keys_with_scores_list, product, sub_product_type, question_type, score_flags):
        similarity_key = None
        try:
            logger.debug("ques=%s,keys=%s,product=%s,sub_type=%s,section=%s",raw_text, similarity_keys_with_scores_list,
                        product, sub_product_type, question_type)
            similarity_key = self._apply_fuzzywuzzy_normalization(raw_text, similarity_keys_with_scores_list, product, sub_product_type, question_type, score_flags)
            logger.info("similarity_key in pipeline_1=%s", str(similarity_key))
            return cs.ResponseCode.SUCCESS, similarity_key
        except Exception as e:
            logger.error("Error in normalize_score=%s",str(e))
            return cs.ResponseCode.INTERNAL_ERROR, similarity_key

    def _apply_fuzzywuzzy_normalization(self, user_question, similarity_keys_and_scores, product, sub_product_type,
                                        question_type,score_flags):
        """
        Apply fuzzywuzzy normalization
        """
        section = ""
        use_fuzzy_wuzzy_score = score_flags[0]
        send_l2_keys = score_flags[1]
        logger.debug("user_question: {}, similarity_keys_and_scores: {}, product: {}, question_type: {}, use_fuzzy_wuzzy_score: {}, send_l2_keys: {}".format(
            user_question, similarity_keys_and_scores, product, question_type, use_fuzzy_wuzzy_score, send_l2_keys))
        similarity_key = []
        if question_type.lower() == "OPERATION".lower():
            section = cs.Section.OPERATION
        elif question_type == "TROB":
            section = cs.TROB_SECTION

        if section == cs.Section.OPERATION:
            ScoreNormalizer.tr_score = 20
        if use_fuzzy_wuzzy_score:
            similarity_key = self.__calculate_fuzzy_wuzzy_score(similarity_keys_and_scores, section)
            logger.debug("after adding fuzzy wuzzy score similairty_key=%s", similarity_key)

        # If troubleshooting apply L1 type then apply fuzzywuzzy normalization to L2 Keys
        if send_l2_keys and len(
                list({v['key']: v for v in similarity_key}.values())) == 1 and section == cs.TROB_SECTION:
            similarity_key = self.__get_sub_keys(user_question, similarity_key, product, sub_product_type,
                                             section)
        logger.debug("similairty_key=%s", similarity_key)
        return similarity_key

    def __calculate_fuzzy_wuzzy_score(self, similarity_keys_and_scores, user_question):
        """
            calculate fuzzy wuzzy score for user question and each key
        Args:
            similarity_keys_and_scores: similaryt keys and scores
            user_question: string

        Returns:
            normalized score with fuzzy wuzzy score value
        """
        logger.debug(
            "user_question: {}, similarity_keys_and_scores: {}".format(user_question, similarity_keys_and_scores))
        similarity_key = []
        for index, value in enumerate(similarity_keys_and_scores):
            d = {}
            value = value['key']
            score = value[1]
            each_similarity_key = value[0]
            if score == 100:
                d["key"] = each_similarity_key
                # Instead of giving 100 as the score a max of fuzz token_set_ratio & 80 (
                # max_score_for_rule_based) is given Since the text similarity is 100 % sure, it will be given
                # as 80%, so that the keys from doc based will not be filtered during dynamic threshold and also
                # negative effects of fuzz token_set_ratio is avoided
                # Ex: round(fuzz.token_set_ratio("왜 세탁기에 PE가 뜨죠?", "PE"), 2) = 27
                d["score"] = max(round(fuzz.token_set_ratio(user_question, each_similarity_key), 2),
                                 ScoreNormalizer.max_score_for_rule_based)
                similarity_key.append(d)
            elif score >= ScoreNormalizer.tr_score:
                d["key"] = each_similarity_key
                d["score"] = round((round(value[1], 4)), 2)
                similarity_key.append(d)
        logger.info("user_question: {}, similarity_keys_and_scores: {}".format(user_question, similarity_keys_and_scores))
        return similarity_key

    def __get_sub_keys(self, text, sim_key_list, product, sub_product_type, question_type):
        """
            Fetching L2 keys of given L1 key from trob intent json file and calculate score
        Args:
            text: question
            sim_key_list: similarity keys
            product: type of product of user query relates to
            sub_product_type: sub product type of user query relates to
            question_type: section name of user query relates to

        Returns:
            returns all L2 keys of l1 key with scores
        """
        logger.debug(
            "user_question: {}, sim_key_list: {}, product: {}, sub_product_type: {}, section: {}".format(text, sim_key_list,
                                                product, sub_product_type, question_type))
        sim_key = sim_key_list[0]["key"]
        sim_key_score = sim_key_list[0]["score"]
        new_similarity_key = []
        # get intent json that is already loaded by IntentSchema class
        data = self.intent_schema._load_intent_json_file(question_type, product, sub_product_type)
        l1_key = data[sim_key]["prob_value"]
        top_k_questions = []

        dup_list = []
        for every_key in data:
            if data[every_key]["prob_value"] == l1_key and every_key != l1_key and (every_key not in dup_list):
                top_k_questions.append((every_key, sim_key_score))
                dup_list.append(every_key)
        if len(top_k_questions) < 1:
            return sim_key_list
        for every_key, score in top_k_questions:
            d = {}
            d["key"] = every_key
            d["score"] = score
            new_similarity_key.append(d)

        if len(list({v['key']: v for v in new_similarity_key}.values())) > 0:
            return list({v['key']: v for v in new_similarity_key}.values())
        else:
            return sim_key_list

