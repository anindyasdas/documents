import os

current_folder = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', 'dataset')) + '/'

class RuleBasedModelConstants:
    MODEL_PATH = current_folder + 'models/nlg_model/rule_based/'
    DEPENDENCY_MODEL = current_folder + MODEL_PATH + "biaffine-dependency-parser-ptb-2020.04.06.tar.gz"
    CONSTITUENCY_MODEL = current_folder + MODEL_PATH + "elmo-constituency-parser-2020.02.10.tar.gz"
