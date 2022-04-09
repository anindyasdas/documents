from ..engine import constants
from ..engine.info_engine import InfoEngine
import unittest
import json
from components.classifier.classifier_engine import ClassifierEngine

class InfoEngineTest(unittest.TestCase):

    def test_all(self):
        info_engine = InfoEngine()
        #info_engine.info_extraction_orig()
        #self.__test_case_1(info_engine)
        # self.__test_case_2(info_engine)
        # self.__test_case_3(info_engine)
        # self.__test_case_4(info_engine)
        # self.__test_case_5(info_engine)
        self.__test_case_6(info_engine)
        # self.__test_case_7(info_engine)
        # self.__test_case_8(info_engine)
        # self.__test_case_9(info_engine)
        # self.__test_case_10(info_engine)
        # self.__test_case_11(info_engine)

    def __test_case_1(self, info_engine):

        output = info_engine.extract('E d4의 원인을 알려주세요 ', question_type=constants.TROB,
                                     product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_1)

        assert json.loads(output)['response_data']['similarity_key'][0]['key'] == 'net weight'.lower()

        #start = time.time()
        # output = info_engine.extract('Even after adding the softener the refill alarm continues to show, why is this?',
        #                              question_type=constants.TROB,
        #                              product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_1)
        #
        # assert json.loads(output)['response_data']['similarity_key'][0]['key'] == 'Refill Alarm continues to display when detergent/ softener is added'.lower()
        #
        # output = info_engine.extract('what is the model name?', question_type=constants.SPEC,
        #                              product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_1)
        #
        # assert json.loads(output)['response_data']['similarity_key'][0]['key'] == 'model'.lower()
        #
        # output = info_engine.extract('Give me instruction to calculate the correct default amount for my detergent',
        #                              question_type=constants.FAQ,
        #                              product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_1)
        #
        # assert json.loads(output)['response_data']['similarity_key'][0]['key'] == 'How do I calculate the correct default amount for my detergent?'.lower()
        #
        # end = time.time()
        # print((end - start) / 3)
        #
        # output = info_engine.extract('what are the causes and solutions of tE?', question_type=constants.TROB,
        #                              product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_2)
        #
        # assert json.loads(output)['response_data']['prob_value_specific'] == 'tE'.lower()
        #
        # start = time.time()
        # output = info_engine.extract('I wrongly filled the detergent compartment what should I do?',
        #                              question_type=constants.TROB,
        #                              product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_2)
        #
        # assert json.loads(output)['response_data']['prob_value_specific'] == 'Detergent compartments clogged from incorrect filling'.lower()
        #
        # output = info_engine.extract('Too much detergent seems to be dispensed, how do I fix this?',
        #                              question_type=constants.TROB,
        #                              product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_2)
        #
        # assert json.loads(output)['response_data'][
        #            'prob_value_specific'] == 'Too much/too little detergent or softener dispensed'.lower()
        #
        # end = time.time()
        # print((end - start) / 3)

    def __test_case_2(self, info_engine):
        output = info_engine.extract('Fetch details about the water pressure', question_type=constants.SPEC,
                                     product=constants.REFRIGERATOR, pipeline=constants.PIPELINE_1)
        assert json.loads(output)['response_data']['similarity_key'][0]['key'] == 'water pressure'.lower()

        output = info_engine.extract('ice fragments are sedimented in delivery chute how to fix it?',
                                     question_type=constants.TROB,
                                     product=constants.REFRIGERATOR, pipeline=constants.PIPELINE_1)
        assert json.loads(output)['response_data']['similarity_key'][0][
                   'key'] == 'The delivery chute is clogged with frost or ice fragments'.lower()

        output = info_engine.extract('ice fragments are sedimented in delivery chute how to fix it?',
                                     question_type=constants.TROB,
                                     product=constants.REFRIGERATOR, pipeline=constants.PIPELINE_2)
        assert json.loads(output)['response_data'][
                   'prob_value_specific'] == 'The delivery chute is clogged with frost or ice fragments'.lower()

        output = info_engine.extract('What temperature settings give best results for my freezer and refrigerator?',
                                     question_type=constants.FAQ,
                                     product=constants.REFRIGERATOR, pipeline=constants.PIPELINE_1)

        assert json.loads(output)['response_data']['similarity_key'][0][
                   'key'] == 'What are the best temperature settings for my refrigerator and freezer?'.lower()

    def __test_case_3(self, info_engine):
        output = info_engine.extract('Loud chatter from AC. What do I do?', question_type=constants.TROB,
                                     product=constants.AC, pipeline=constants.PIPELINE_1)
        assert json.loads(output)['response_data']['similarity_key'][0]['key'] == 'High Pitched Chatter'.lower()

        output = info_engine.extract('Loud chatter from AC. What do I do?', question_type=constants.TROB,
                                     product=constants.AC, pipeline=constants.PIPELINE_2)
        assert json.loads(output)['response_data']['prob_value_specific'] == 'High Pitched Chatter'.lower()

        output = info_engine.extract('Give me instruction to calculate the correct default amount for my detergent',
                                     question_type=constants.FAQ,
                                     product=constants.WASHING_MACHINE, pipeline=constants.PIPELINE_1)

        assert json.loads(output)['response_data']['similarity_key'][0][
                   'key'] == 'How do I calculate the correct default amount for my detergent?'.lower()

    def __test_case_4(self, info_engine):
        output = info_engine.extract('The product is not charging, what can I do?', question_type=constants.TROB,
                                     product=constants.VACUUM_CLEANER, pipeline=constants.PIPELINE_1)
        assert json.loads(output)['response_data']['similarity_key'][0][
                   'key'] == 'The product body does not appear to be charging'.lower()

        output = info_engine.extract('The product is not charging, what can I do?', question_type=constants.TROB,
                                     product=constants.VACUUM_CLEANER, pipeline=constants.PIPELINE_2)
        assert json.loads(output)['response_data'][
                   'prob_value_specific'] == 'The product body does not appear to be charging'.lower()

    def __test_case_5(self, info_engine):
        output = info_engine.extract('why arcing in oven?', question_type=constants.TROB,
                                     product=constants.MICROWAVE_OVEN, pipeline=constants.PIPELINE_1)
        assert json.loads(output)['response_data']['similarity_key'][0]['key'] == 'Arcing or Sparking'.lower()

        output = info_engine.extract('why arcing in oven?', question_type=constants.TROB,
                                     product=constants.MICROWAVE_OVEN, pipeline=constants.PIPELINE_2)
        # assert json.loads(output)['response_data']['prob_value_specific'] == 'Arcing or Sparking'.lower()

        output = info_engine.extract('What makes the dish hot when the oven operates ?', question_type=constants.FAQ,
                                     product=constants.MICROWAVE_OVEN, pipeline=constants.PIPELINE_1)

        assert json.loads(output)['response_data']['similarity_key'][0][
                   'key'] == 'Why does the dish become hot when I microwave food in it?'.lower()

        output = info_engine.extract('By using the power drive nozzle with two batteries, what is the battery runtime?',
                                     question_type=constants.SPEC,
                                     product=constants.VACUUM_CLEANER, pipeline=constants.PIPELINE_1)
        output = json.loads(output)['response_data']['similarity_key'][0]
        assert output['key'] == 'Battery Run Time'.lower()
        assert output['no_of_batteries'] == 'two'.lower()
        assert output['usage'] == 'power drive nozzle'.lower()

    def __test_case_6(self, info_engine):
        '''
        output = info_engine.extract('How can I reconnect to my phone with AC if connection is lost?', question_type=constants.TROB,
                           product = constants.AC, pipeline=constants.PIPELINE_2)
        info_engine.info_extraction_orig()
        info_engine.extract_on_file()
        info_engine.train()
        info_engine.test_on_file()
        '''
        info_engine.extract_on_file_textsim()
        #info_engine.test_on_test_file()

    def __test_case_7(self, info_engine):
        para = ['my name is abc', 'mars comes after earth']
        questions = ['what comes after earth?', 'what is my name?']
        output = info_engine.extract_answer_para(para, questions)
        answers = json.loads(output)['response_data']['answers']
        print(answers)

    def __test_case_8(self, info_engine):

        while True:
            ques = input('enter the question: ')
            question_type = input('enter the type - TROB, SPEC, FAQ or OPERATION: ')
            product = input('enter the product ' + ' or '.join(
                [constants.WASHING_MACHINE, constants.REFRIGERATOR, constants.AC, constants.VACUUM_CLEANER,
                 constants.MICROWAVE_OVEN]) + ': ')
            category = input('enter the l1key: ')
            output = info_engine.extract(ques, question_type=question_type,
                                         product=product, pipeline=constants.PIPELINE_1, top_k=3, l1_key=category)

            print(json.loads(output)['response_data']['similarity_key'])

    def __test_case_9(self, info_engine):
        import pandas as pd

        classifier_engine = ClassifierEngine()

        filename = 'test/dialog_RFG_WS1.xlsx'
        df = pd.read_excel(filename, sheet_name='Sheet1')
        chatin_speech = []
        product = []
        topic_classifier = []
        intent = []
        type_classifier = []
        output_data = []

        for index, row in df.iterrows():
            chatin_speech.append(row['chatin_speech'])
            statement = row['chatin_speech']
            product.append(row['product'])
            prod = row['product']
            ques = statement
            classifier_output = json.loads(classifier_engine.get_classifier_output(ques))
            top = classifier_output["response_data"]["Topic"]
            topic_classifier.append(top)
            intent_val = classifier_output["response_data"]["Intent"]
            intent.append(intent_val)
            type_val = classifier_output["response_data"]["Type"]
            type_classifier.append(type_val)
            print("type_val:", type_val)
            topic = "TROB"
            if top == "Specification":
                topic = "SPEC"
            if top == "Troubleshooting":
                topic = "TROB"
            if top == "Operation" and prod == "refrigerator":
                topic = "OPERATION"
            output = info_engine.extract(ques, question_type=topic, product=prod, pipeline=constants.PIPELINE_1,
                                         top_k=1)
            key_out = json.loads(output)['response_data']['similarity_key'][0]['key']
            output_data.append(key_out)

        dict_id = {'chatin_speech': chatin_speech, 'product': product, 'topic_classifier': topic_classifier,
                   'intent': intent, "type_classifier": type_classifier, "output_data": output_data}
        df = pd.DataFrame(dict_id)
        writer = pd.ExcelWriter("test/text_similarity.xlsx", engine='xlsxwriter')
        df.to_excel(writer, 'Sheet1', index=False)
        writer.save()

    def __test_case_10(self, info_engine):
        classifier_engine = ClassifierEngine()
        output = classifier_engine.get_classifier_output("What is the capital of India?")
        output = json.loads(output)["response_data"]["Class"]
        assert output == 'factoid'

    def __test_case_11(self, info_engine):
        para = ['my name is abc', 'mars comes after earth']
        questions = ['Is my name bcd?', 'does mars come after earth?']
        output = info_engine.extract_answer_bool(para, questions)
        answers = json.loads(output)['response_data']['answers']
        assert answers[0] == 'no'
        assert answers[1] == 'yes'


if __name__ == '__main__':
    unittest.main()