"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import os


class FunctionConstants:
    # constants to use and mute some functionalities
    PRINT_SUMMARY = True
    PLOT_GRAPHS = True
    LABEL_ENCODE_DATASET = True
    DEBUG_REPORT = False
    GET_ACCURACY_REPORT = True
    USE_WEIGHTS = False


class PathConstants:
    # general paths for input/ output / model files
    current_folder = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'dataset')) + '/'
    MODEL_PATH = current_folder + 'models/classifier'
    DATA_PATH = current_folder + 'dataset/classifier/'

    # dataset paths
    TRAIN_DATA = current_folder + 'dataset/classifier/W_R_A_M_V_trob_train.xlsx'
    TEST_DATA = current_folder + 'dataset/classifier/washing machine_OPERATION.xlsx'
    DEBUG_FILE = MODEL_PATH + '/debug_results.xlsx'
    RESULTS_FILE = MODEL_PATH + '/results.csv'


class TrainingConstants:
    # constants used for training the model
    EPOCHS = 50
    BATCH_SIZE = 50
    KFOLD_TRAINING = False
    HIDDEN_LSTM_UNITS = 128
    N_FOLDS = 10


class BertConstants:
    # Bert configs related constants
    MAX_LENGTH = 32
    BERT_URL = 'https://tfhub.dev/google/bert_uncased_L-12_H-768_A-12/1'
    BERT_MODEL = PathConstants.current_folder + 'models/bert'
    VOCAB = BERT_MODEL + '/assets/vocab.txt'
    UNCASED = True
    TRAINABLE = False


class GenericModelConstants:
    GENERIC_MODEL = PathConstants.MODEL_PATH + '/generic_model.h5'


# Constants below this point are KER specific constants.
# Hence can be ignored when classifier is used for some other use.
class KerModelConstants:
    # constants related to KER classifiers
    CURRENT_MODEL = "Topic"
    # Model checkpoints paths and name
    TOPIC_DATA_LSTM = PathConstants.MODEL_PATH + '/topic_data.h5'
    INTENT_DATA_LSTM = PathConstants.MODEL_PATH + '/intent_data.h5'
    TYPE_DATA_LSTM = PathConstants.MODEL_PATH + '/type_data.h5'
    FOLLOW_UP_DATA_LSTM = PathConstants.MODEL_PATH + '/follow_up_data.h5'
    SECTION_DATA_LSTM = PathConstants.MODEL_PATH + '/section_data.h5'
    SAVE_MODEL_LSTM = PathConstants.MODEL_PATH + '/ker_model.h5'


class KerStringConstants:
    # Constant strings
    TOPIC = "section"
    INTENT = "intent"
    TYPE = "sub_section"
    FOLLOW_UP = "follow_up"
    SECTION = "Section"
    CATEGORY = "category"
    INFO_EXTRACTION = 'INFO_EXTRACTION'
    CLASS = "question_type"


class KerMappingDictionary:
    # Mapping dictionarires
    TOPIC_DICT = {0: "Specification", 1: "Troubleshooting", 2: "Operation", 3: "Installation"}
    INTENT_DICT = {0: "cause-sol", 1: "reason", 2: "solution"}
    TYPE_DICT = {0: "error", 1: "noise", 2: "cooling problem", 3: "ice problem", 4: "wifi problem", 5: "problem"}
    INFO_DICT = {0: "error_code", 1: "noise", 2: "problem"}
    SECTION_DICT = {0: "Before Use",
                    1: "Control Panel",
                    2: "Sabbath Mode",
                    3: "Dispenser",
                    4: "Ice Compartment",
                    5: "Automatic Icemaker",
                    6: "Humidity Controlled Crispers",
                    7: "Glide'N'Serve",
                    8: "Refrigerator Shelves",
                    9: "Door-in-Door and Instaview",
                    10: "Door Bins",
                    11: "Durabase",
                    12: "Auto lift Device",
                    13: "Automatic Opening Door",
                    14: "Drawers",
                    15: "Dairy Bin",
                    16: "Ice Tray",
                    17: "Storage Racks",
                    18: "Storing Food and Wine",
                    19: "Temperature Controller",
                    20: "In-Door Ice Bin",
                    21: "Adding Cleaning Products",
                    22: "Using the Washer",
                    23: "Dry Cycles",
                    24: "Sorting Laundry",
                    25: "Loading the Washer",
                    26: "Options and Extra Functions",
                    27: "Special Care Features",
                    28: "Wash Cycles",
                    29: "Using the Manual Dispense Function",
                    31: "Cycle Modifiers"
                    }
    CLASS_DICT = {0: 'factoid', 1: 'description', 2: 'list', 3: 'bool'}
    FOLLOW_UP_DICT = {0: False, 1: True}
    MODEL_DICT_MAPPING = {KerStringConstants.TOPIC: TOPIC_DICT, KerStringConstants.INTENT: INTENT_DICT,
                          KerStringConstants.TYPE: TYPE_DICT, KerStringConstants.SECTION: SECTION_DICT,
                          KerStringConstants.CLASS: CLASS_DICT,
                          KerStringConstants.FOLLOW_UP: FOLLOW_UP_DICT}
    MODEL_CK_MAPPING = {KerStringConstants.TOPIC: KerModelConstants.TOPIC_DATA_LSTM,
                        KerStringConstants.INTENT: KerModelConstants.INTENT_DATA_LSTM,
                        KerStringConstants.TYPE: KerModelConstants.TYPE_DATA_LSTM,
                        KerStringConstants.SECTION: KerModelConstants.SECTION_DATA_LSTM,
                        KerStringConstants.FOLLOW_UP: KerModelConstants.FOLLOW_UP_DATA_LSTM}


class KerOperationConstants:
    # operation section constants
    # operation section sub-sections
    CHECKLIST = "checklist"
    CONTROL_PANEL = "control panel"
    COMPONENT = "component"
    USAGE = "usage"
    FEATURE = "feature"
    STORING = "storage"

    # operation section intents
    DESCRIPTION = "desc"
    DETACH = "detach"
    ATTACH = "attach"
    CONTAIN = "contain"
    TURN_OFF = "turn_off"
    TURN_ON = "turn_on"
    EXTRA_WARNING = "warning"
    EXTRA_CAUTION = "caution"
    EXTRA_NOTE = "note"
    DEFAULT_INTENT = "default intent"

    # Combined categories
    STORING_FOOD_AND_WINE = "Storing Food and Wine"
    CONTROL_PANEL_SECTION = "Control Panel"
    DRAWER = "Drawers"
    DISPENSER = "Dispenser"
    DOOR_IN_DOOR_INSTAVIEW = "Door-in-Door and Instaview"

    # Separated sections
    CONTROL_PANEL_1 = "Control Panel 1"
    CONTROL_PANEL_2 = "Control Panel 2"
    FULL_CONVERT_DRAWER = "Full Convert Drawer"
    CRISPER_DRAWER = "Crisper Drawer"
    PANTRY_DRAWER = "Pantry Drawer"
    WATER_DISPENSER = "Water Dispenser"
    ICE_AND_WATER_DISPENSER = "Ice and Water Dispenser"
    STORING_FOOD = "Storing Food"
    STORING_WINE = "Storing Wine"
    DOOR_IN_DOOR = "Door-in-Door"
    INSTAVIEW = "Instaview"

    OPERATION_SEPARATED_SECTIONS = [CONTROL_PANEL_1,
                                    CONTROL_PANEL_2,
                                    FULL_CONVERT_DRAWER,
                                    CRISPER_DRAWER,
                                    PANTRY_DRAWER,
                                    WATER_DISPENSER,
                                    ICE_AND_WATER_DISPENSER,
                                    STORING_FOOD,
                                    STORING_WINE,
                                    DOOR_IN_DOOR,
                                    INSTAVIEW]

    # Mapping dictionaries for operation section
    OPERATION_INTENT_DICT = {
        DESCRIPTION: ['describe', 'tell', 'what', 'description', 'define', 'show',
                      'functionalities', 'feature', 'features', 'steps', 'step'],
        ATTACH: ['attach', 'fix', 'assemble'],
        DETACH: ['detach', 'remove', 'dismantle'],
        USAGE: ['use', 'usage','access', 'operate'],
        CONTAIN: ['contain'],
        TURN_OFF: ['turn off', 'switch off', 'off', 'switching off', 'turning off'],
        TURN_ON: ['turn on', 'switch on', 'switching on', 'turning on', 'on'],
        EXTRA_WARNING: ['warning', 'warn', 'notify', 'alert', 'forewarn', 'warn',
                        'notice'],
        EXTRA_CAUTION: ['caution', 'attention', 'aware'],
        EXTRA_NOTE: ['note', 'more', 'additional', 'add', 'extra info'],
        DEFAULT_INTENT: None
    }

    OPERATION_SUB_CATEGORY_MAP = {COMPONENT: ["Ice and Water Dispenser", "Ice Compartment", "Automatic Icemaker",
                                              "Humidity Controlled Crispers", "Glide'N'Serve", "Refrigerator Shelves",
                                              "Door-in-Door and instaview", "Door Bins", "Durabase", "Dispenser",
                                              "Ice Compartment", "Water Dispenser", "Pantry Drawer", "Crisper Drawer",
                                              "Automatic Icemaker", "Refrigerator Shelves", "Auto lift Device",
                                              "Drawers",
                                              "Dairy Bin", "Ice Tray", "Storage Racks", "Temperature Controller",
                                              "In-Door Ice Bin", "Full Convert Drawer", "Door-in-Door", "Instaview",
                                              ],
                                  CHECKLIST: ["Checklist", "Before use"],
                                  CONTROL_PANEL: ["Control panel", "Control Panel 1", "Control Panel 2"],
                                  FEATURE: ["Sabbath", "Sabbath Mode", "Adding Cleaning Products",
                                            "Dry Cycles", "Sorting Laundry",
                                            "Options and Extra Functions", "Special Care Features",
                                            "Wash Cycles", "Cycle Modifiers"],
                                  USAGE: ["Cleaning the Dispenser", "Automatic Opening Door", "Using the Washer",
                                          "Loading the Washer", "Using the Manual Dispense Function"],
                                  STORING: ["Storing Food", "Storing Food and Wine"]
                                  }

    # dictionary  for all the allowed intents for each category listed based on preference
    OPERATION_CATEGORY_TO_INTENT_MAP = {
        CHECKLIST: [EXTRA_WARNING, EXTRA_CAUTION, EXTRA_NOTE, DESCRIPTION],
        CONTROL_PANEL: [USAGE, DESCRIPTION, EXTRA_WARNING, EXTRA_CAUTION, EXTRA_NOTE],
        COMPONENT: [ATTACH, DETACH, USAGE, CONTAIN, DESCRIPTION, EXTRA_WARNING, EXTRA_CAUTION, EXTRA_NOTE],
        USAGE: [DESCRIPTION, USAGE, EXTRA_WARNING, EXTRA_CAUTION, EXTRA_NOTE],
        FEATURE: [TURN_ON, TURN_OFF, DESCRIPTION, EXTRA_WARNING, EXTRA_CAUTION, EXTRA_NOTE],
        STORING: [EXTRA_WARNING, EXTRA_CAUTION, EXTRA_NOTE, DESCRIPTION]}

    FOOD_LIST = {"food", "butter", "margarine", "cheese", "milk", "egg", "fruit",
                 "leafy vegetable", "vegetables with skin", "pepper",
                 "carrot", "fish"}

    WINE_LIST = {"wine", "non-vintage champagne", "sparkling wines", "cava ", "asti", "prosecco",
                 "sekt", "vintage champagne", "light white", "rose wine", "muscat", "rosé", "riesling", "pinot grigio",
                 "sauvignon blanc", "semillon", "full-bodied white wine", "light red wine",
                 "chardonnay", "viognier", "white burgundy", "chablis", "pinot noir", "beaujolais ",
                 "barbera ", "grenache", "medium-bodied red wine", "full-bodied red wine", "aged reds",
                 "zinfandel ", "chianti", "red burgundy", "cabernet sauvignon", "merlot", "malbec ",
                 "shiraz", "syrah", "bordeaux", "vintage port", "tawny port", "sweet white wine"}

    CONTROL_PANEL_1_LIST = {'control panel 1', 'control panel one'}
    CONTROL_PANEL_2_LIST = {'control panel 2', 'freezer', 'control panel two', 'inside the freezer'}
    FULL_CONVERT_DRAWER_LIST = {"full convert drawer", "full convert"}
    CRISPER_DRAWER_LIST = {"crisper drawer", "crisper", "crisp"}
    PANTRY_DRAWER_LIST = {"pantry drawer", "pantry"}
    WATER_DISPENSER_LIST = {'water dispenser', 'water'}
    ICE_AND_WATER_DISPENSER_LIST = {'ice dispenser', 'ice', 'ice and water'}
    INSTAVIEW_LIST = {"instaview"}
    DOOR_IN_DOOR_LIST = {"door-in-door"}
