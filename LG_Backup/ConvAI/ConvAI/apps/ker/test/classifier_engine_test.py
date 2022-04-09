from components.classifier.classifier_engine import ClassifierEngine
import unittest


class ClassifierTest(unittest.TestCase):
    """
    Interface for testing all the functionality of the classifier
    """
    def test_all(self):
        self.__test_case_1()
        self.__test_case_2()
        self.__test_case_3()

    def __test_case_1(self):
        """
        Test single input
        """
        cs = ClassifierEngine()
        result = cs.get_classifier_output("What are the causes of  PE error ?")
        print(result)  # Troubleshooting
        result = cs.get_classifier_output("What about the gas specifications for my washer?")
        print(result)  # Specification
        result = cs.get_classifier_output("Describe  Door in door")
        print(result)  # Operation

    def __test_case_2(self):
        """
        File based output for a specific type of classifier defined in purpose
        """
        cs = ClassifierEngine(all_models=False, purpose="Topic")
        cs.evaluate_on_file()

    def __test_case_3(self):
        """
        File based output for all the classifiers
        """
        cs = ClassifierEngine(all_models=True)
        cs.evaluate_on_file()

    def __test_case_4(self):
        """
        Function to train the KER classifier based on purpose
        """
        cs = ClassifierEngine(num_lable=3, evaluate=False, all_models=False, purpose="Topic")
        cs.train()


if __name__ == '__main__':
    unittest.main()
