"""
-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
-------------------------------------------------
@Author:anusha.kamath@lge.com
"""
from nltk import tree
from allennlp.predictors.predictor import Predictor
from nltk import word_tokenize
from nltk.translate.ribes_score import position_of_ngram

import sys

from constants import RuleBasedModelConstants as constants


class RuleBasedNlgModel:
    def __init__(self):
        self.dependency_predictor = Predictor.from_path(constants.DEPENDENCY_MODEL)
        self.constituency_predictor = Predictor.from_path(constants.CONSTITUENCY_MODEL)

    def get_nlg_ans(self, user_query, category, input_answer, light_phrase_list):
        """
        public function to give nlg answer to a given query..
        Args:
            user_query: User input string
            category : type of question ( confirmatory or factoid)
            input_answer: Answer input by user
            light_phrase_list: list of light phrases

        Returns:
            return NLG answer after processing the rules
        """
        if user_query and input_answer:
            if category == 'Yes/No':
                nlg_ans = self.__solve_confirmatory_question(user_query, input_answer, light_phrase_list)
                return nlg_ans
            elif category == 'Factoid':
                nlg_ans = self.__solve_factoid_question(user_query, input_answer)
                return nlg_ans
            else:
                print("The question type is not supported")
                sys.exit()

    ####################confirmatory questions starts##############################################
    def __solve_confirmatory_question(self, user_query, input_answer, light_phrase_list):
        """
        function to solve confirmatory questions . The are the ones of the kind where answer is yes, no.
        Args:
            user_query: User input string
            input_answer: Answer input by user
            light_phrase_list: list of light phrases

        Returns:
            NLG answer for confirmatory question
        """
        # process light phrases
        user_query = self.__process_light_phrase(user_query, light_phrase_list)

        # get constituency and dependency outputs
        constituency_op = self.constituency_predictor.predict(sentence=user_query)
        dependency_op = self.dependency_predictor.predict(sentence=user_query)

        tokens = word_tokenize(user_query)
        vp_list = self.get_vp(constituency_op)
        vp_ngram_idx = position_of_ngram(tuple(vp_list[0].split()), tokens)

        np_list = self.get_np(constituency_op)
        len_np = len(np_list[0].split())
        np_ngram_idx = position_of_ngram(tuple(np_list[0].split()), tokens)

        if input_answer.lower() == "yes":
            nlg_ans = self.__solve_yes(vp_ngram_idx, np_ngram_idx, dependency_op, len_np)
            return nlg_ans
        elif input_answer.lower() == "no":
            nlg_ans = self.__solve_no(vp_ngram_idx, np_ngram_idx, dependency_op, len_np)
            return nlg_ans
        else:
            print("Not supported")
            sys.exit()

    def __solve_yes(self, vp_ngram_idx, np_ngram_idx, dependency_op, len_np):
        """
        function to solve confirmatory question with yes as answer
        Args:
            vp_ngram_idx: index of np ngram
            np_ngram_idx: index of vp ngram
            dependency_op: dependency parser output
            len_np: length of noun phrase

        Returns:
            nlg answer for confirmatory question with yes as answer
        """
        ans = "Yes,"  # Answer begins with yes
        for i in range(np_ngram_idx, len(dependency_op['words'])):
            if i == vp_ngram_idx or i == np_ngram_idx + len_np:  # rule 1
                ans += " " + dependency_op['words'][0].lower()
            if dependency_op['words'][i] == "?":  # rule 2
                ans += "."
                continue
            if dependency_op['words'][i].lower() == "my":  # rule 3
                ans += " your"
                continue
            if dependency_op['words'][i].lower() == "we" or dependency_op['words'][i].lower() == "i":  # rule 4
                ans += " you"
                continue
            ans += " " + dependency_op['words'][i]
        return ans

    def __solve_no(self, vp_ngram_idx, np_ngram_idx, dependency_op, len_np):
        """
        function to solve confirmatory question with no as answer
        Args:
            vp_ngram_idx: index of np ngram
            np_ngram_idx: index of vp ngram
            dependency_op: dependency parser output
            len_np: length of noun phrase

        Returns:
            nlg answer for confirmatory question with no as answer
        """
        ans = "No,"
        for i in range(np_ngram_idx, len(dependency_op['words'])):
            if i == vp_ngram_idx or i == np_ngram_idx + len_np:  # rule 1
                ans += " " + dependency_op['words'][0].lower() + " " + "not"
            if dependency_op['words'][i] == "?":  # rule 2
                ans += "."
                continue
            if dependency_op['words'][i].lower() == "my":  # rule 3
                ans += " your"
                continue
            if dependency_op['words'][i].lower() == "we" or dependency_op['words'][i].lower() == "i":  # rule 4
                ans += " you"
                continue
            ans += " " + dependency_op['words'][i]
        return ans

    ####################confirmatory ends#######################################################
    ####################factoid starts##########################################################

    def __solve_factoid_question(self, user_query, input_factoid_ans):
        """
        function to solve factoid questions.
        Args:
            user_query: User input string
            input_factoid_ans: factoid answer input

        Returns:
                NLG answer for factoid question
        """
        dependency_op = self.dependency_predictor.predict(sentence=user_query)
        aux_ind, aux_word = self.find_aux_index(dependency_op)

        # special case of questions not having a auxiliary verb in it
        if aux_ind == 0:
            nlg_ans = self.__factoid_without_aux(input_factoid_ans, user_query)
            return nlg_ans

        verb_present = self.check_verb_exists(dependency_op)
        if verb_present == 0:
            # approach when there is no verb
            nlg_ans = self.__factoid_with_no_vp(aux_ind, aux_word, dependency_op, input_factoid_ans)
            return nlg_ans
        else:
            # approaches when there is a verb
            approach_id = self.get_approach_id(aux_ind, dependency_op)
            factoid_ans = input_factoid_ans
            if approach_id == 1:
                # when auxiliary verb and verb are together
                nlg_ans = self.__factoid_with_vp_and_aux_together(input_factoid_ans, user_query)
                return nlg_ans
            elif approach_id != 1:
                # when auxiliary verb and verb are not together
                return self.__factoid_with_vp_and_aux_not_together(aux_ind, aux_word, dependency_op, factoid_ans,
                                                                   input_factoid_ans, user_query)

    def __factoid_with_vp_and_aux_not_together(self, aux_ind, aux_word, dependency_op, factoid_ans,
                                               input_factoid_ans, user_query):
        """
        function to solve nlg answer for question when auxiliary verb and verb are not together
        Args:
            aux_ind: index of auxiliary verb
            aux_word: auxiliary verb
            dependency_op: dependency parser output
            factoid_ans: factoid ans
            input_factoid_ans: factoid answer input
            user_query: user question string

        Returns:
                returns the nlg answer for question when auxiliary verb and verb are not together
        """
        ans = ""
        ans, np_idx = self.get_np_idx(ans, aux_ind, dependency_op)
        if np_idx == 0:
            # if there is no noun phrase
            nlg_ans = self.__factoid_with_no_np(input_factoid_ans, user_query)
            return nlg_ans
        else:
            if aux_word != 'did':
                # skip did in ans
                ans += aux_word + " "
            for i in range(np_idx + 1, len(dependency_op['words']) - 1):
                ans += dependency_op['words'][i] + " "
            ans += factoid_ans + "."  # add full stop at end
            return ans

    def __process_light_phrase(self, user_query, light_phrase_list):
        """
        function to process light phrase.
        If light phrase is found -> replace it with does
        Args:
            user_query:
            light_phrase_list:

        Returns:
                user query where light phrase is processed
        """
        for phrase in light_phrase_list:
            n_lp = self.check_light_phrase(user_query, phrase)
            if n_lp >= 0:
                user_query_updated = "Does" + user_query[n_lp + len(phrase):]
                return user_query_updated
        return user_query

    def __factoid_without_aux(self, input_factoid_ans, user_query):
        """
        function to process answer for question which does not have auxiliary verb
        Args:
            input_factoid_ans:  input factoid answer
            user_query: user query string

        Returns:
                nlg answer for question which does not have auxiliary verb
        """
        constituency_parser_op = self.constituency_predictor.predict(sentence=user_query)
        tr = tree.Tree.fromstring(constituency_parser_op['trees'])
        pos_tags = tr.pos()
        nlg_ans = ""
        for i in range(len(pos_tags) - 2):
            # replace wh word with factoid ans -> corner case -> no large context
            if pos_tags[i][0] == '?':
                continue
            if pos_tags[i][1] == 'WP' or pos_tags[i][1] == 'WRB':
                nlg_ans += input_factoid_ans + " "
            else:
                # my -> your
                # we and i -> you
                if pos_tags[i][0].lower() == "my":
                    nlg_ans += " your"
                    continue
                if pos_tags[i][0].lower() == "we" or pos_tags[i][0].lower() == "i":
                    nlg_ans += " you"
                    continue

                nlg_ans += " " + pos_tags[i][0] + " "
        nlg_ans += pos_tags[len(pos_tags) - 2][0] + "."
        return nlg_ans

    def __factoid_with_no_np(self, input_factoid_ans, user_query):
        """
        function to solve questions without noun phrase
        Args:
            input_factoid_ans: input factoid answer to the question
            user_query: user question string

        Returns:
                nlg answer for question without noun phrase
        """
        constituency_parser_op = self.constituency_predictor.predict(sentence=user_query)
        tr = tree.Tree.fromstring(constituency_parser_op['trees'])
        pos_tags = tr.pos()
        nlg_ans = ""
        for i in range(len(pos_tags) - 2):
            if pos_tags[i][0] == '?':
                continue
            if pos_tags[i][1] == 'WP' or pos_tags[i][1] == 'WRB':
                nlg_ans += input_factoid_ans + " "
            else:
                if pos_tags[i][0].lower() == "my":
                    nlg_ans += " your"
                    continue
                if pos_tags[i][0].lower() == "we" or pos_tags[i][0].lower() == "i":
                    nlg_ans += " you"
                    continue

                nlg_ans += " " + pos_tags[i][0] + " "
        nlg_ans += pos_tags[len(pos_tags) - 2][0] + "."
        return nlg_ans

    def __factoid_with_vp_and_aux_together(self, input_factoid_ans, user_query):
        """
        function to solve factoid question answer when aux verb and verb are together
        Args:
            input_factoid_ans: factoid answer input
            user_query: user question string

        Returns:
               factoid question answer when aux verb and verb are together
        """
        constituency_parser_op = self.constituency_predictor.predict(sentence=user_query)
        tr = tree.Tree.fromstring(constituency_parser_op['trees'])
        pos_tags = tr.pos()
        nlg_ans = ""
        for i in range(len(pos_tags) - 2):
            if pos_tags[i][0] == '?':
                continue
            if pos_tags[i][1] == 'WP' or pos_tags[i][1] == 'WRB':
                nlg_ans += input_factoid_ans + " "
            else:
                if pos_tags[i][0].lower() == "my":
                    nlg_ans += " your"
                    continue
                if pos_tags[i][0].lower() == "we" or pos_tags[i][0].lower() == "i":
                    nlg_ans += " you"
                    continue

                nlg_ans += " " + pos_tags[i][0] + " "
        nlg_ans += pos_tags[len(pos_tags) - 2][0] + "."
        return nlg_ans

    def __factoid_with_no_vp(self, aux_ind, aux_word, dependency_op, input_factoid_ans):
        """
        function to solve questions with factoid answers with no verb phrase
        Args:
            aux_ind: index of the auxiliary verb
            aux_word: auxiliary verb
            dependency_op: dependency parser output
            input_factoid_ans: factoid answer input

        Returns:
               nlg question answer when there is no verb phrase
        """
        ans = ""
        factoid_ans = input_factoid_ans
        for i in range(aux_ind + 1, len(dependency_op['words'])):
            if dependency_op['pos'][i] == 'PUNCT':
                continue

            if dependency_op['words'][i].lower() == "my":
                ans += " your"
                continue
            if dependency_op['words'][i].lower() == "we" or dependency_op['words'][i].lower() == "i":
                ans += " you"
                continue

            ans += " " + dependency_op['words'][i] + " "
        ans += aux_word + " "
        ans += factoid_ans + "."
        return ans

    ############################### factoid ends ##################################################
    ############################### supporting functions #########################################
    @staticmethod
    def get_np(cons_parser_op):
        """
        function to return noun phrase
        Args:
            cons_parser_op: constituency parser output

        Returns:
               list of noun phrases
        """
        ans_list = []
        t = tree.Tree.fromstring(cons_parser_op['trees'])
        subtexts = []
        for subtree in t.subtrees():
            if subtree.label() == "NP":
                subtexts.append(' '.join(subtree.leaves()))
                break

        ans_string = ""
        for text in subtexts:
            ans_string += text
        ans_list.append(ans_string)
        return ans_list

    @staticmethod
    def get_vp(cons_parser_op):
        """
        function to return verb phrase
        Args:
            cons_parser_op:constituency parser output

        Returns:
               list of verb phrases
        """
        ans_list = []
        t = tree.Tree.fromstring(cons_parser_op['trees'])

        subtexts = []
        for subtree in t.subtrees():

            if subtree.label() == "VP":
                subtexts.append(' '.join(subtree.leaves()))
                break

        ans_string = ""
        for text in subtexts:
            ans_string += text
        ans_list.append(ans_string)
        return ans_list

    @staticmethod
    def get_np_idx(ans, aux_ind, dependency_op):
        """
        function to get noun phrase index
        Args:
            ans: nlg answer
            aux_ind: index of auxiliary verb
            dependency_op: dependency parser output

        Returns:
            return index of the noun phrase
        """
        np_idx = 0
        for i in range(aux_ind + 1, len(dependency_op['words']) - 1):
            if dependency_op['pos'][i] == 'NOUN' or dependency_op['pos'][i] == 'DET' or dependency_op['pos'][
                i] == 'PROPN' or \
                    dependency_op['pos'][i] == 'PRON' or dependency_op['pos'][i] == 'ADJ':
                ans += dependency_op['words'][i] + " "
                np_idx = i
            else:
                break
        return ans, np_idx

    @staticmethod
    def get_approach_id(aux_ind, dependency_op):
        """
        approach id when verb is present in the question
        Args:
            aux_ind: index of auxiliary verb
            dependency_op: dependency parser output

        Returns:
                approach id of the approach to be used to solev the problem
        """
        approach_id = 0
        if ((dependency_op['pos'][aux_ind + 1] == 'PART') and (dependency_op['pos'][aux_ind + 2] == 'VERB')) or (
                dependency_op['pos'][aux_ind + 1] == 'VERB'):
            approach_id = 1
        return approach_id

    @staticmethod
    def check_verb_exists(dependency_op):
        """
        function to check if there is a verb in the sentence
        Args:
            dependency_op: dependency parser output

        Returns:
                0 if verb i snot present , 1 if present
        """
        verb_present = 0
        for i in range(len(dependency_op['pos'])):
            if dependency_op['pos'][i] == 'VERB':
                verb_present = 1
                break
        return verb_present

    @staticmethod
    def find_aux_index(dependency_op):
        """
        function to find index of auxiliary verb
        Args:
            dependency_op: dependency parser output

        Returns:
            index of auxiliary verb and the auxiliary word
        """
        aux_ind = 0
        aux_word = ""
        for i in range(len(dependency_op['pos'])):
            if dependency_op['pos'][i] == 'AUX':
                aux_ind = i
                aux_word = dependency_op['words'][aux_ind]
                if dependency_op['pos'][aux_ind + 1] == 'PART' or dependency_op['pos'][aux_ind + 1] == 'AUX':
                    aux_ind += 1
                    aux_word += dependency_op['words'][aux_ind]
                    break
                break
        return aux_ind, aux_word

    @staticmethod
    def check_light_phrase(user_query, target):
        """
        function to check if there is light phrase in the sentence
        Args:
            user_query: user input string
            target: a light phrase

        Returns:
                index of the light phrase
        """
        t = 0
        str_len = len(user_query)
        i = 0

        # Iterate from 0 to len - 1
        for i in range(str_len):
            if t == len(target):
                break
            if user_query[i] == target[t]:
                t += 1
            else:
                t = 0

        if t < len(target):
            return -1
        else:
            return i - t


if __name__ == '__main__':
    question = "What is the cost of the pencil"  # user query
    cat = "Factoid"  # category
    ip_ans = "15 rs"  # factoid ans

    iq = "Can I know if"  # list of light phrases  # yes/ no
    obj = RuleBasedNlgModel()
    print(obj.get_nlg_ans(question, cat, ip_ans, iq))
    question = "Is there a way to do this"  # user query
    cat = 'Yes/No'  # category
    ip_ans = "yes"  # factoid ans

    iq = "Can I know if"  # list of light phrases  # yes/ no
    print(obj.get_nlg_ans(question, cat, ip_ans, iq))