"""
# -------------------------------------------------
# Copyright(c) 2020-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------
"""
import json
import os.path
import re
from configparser import ConfigParser
import logging as logger

logger = logger.getLogger("django")

# constants common key name for specification section of product manual
SPECIFICATIONS = "Product_specifications"

############ RDF Schema Constants ##############################
# Nodes
MODEL = "Model"
# Relationship
DESCRIPTION = "RelDescription"
VOLTAGE_REQUIREMENTS = "RelVoltage"
DIMENSION = "RelDimension"
NET_WEIGHT = "RelWeight"
MAX_SPIN_SPEED = "RelSpinSpeed"
WATER_PRESSURE = "RelWaterPressure"
TEMPERATURE = "RelTemperature"
CAPACITY = "RelCapacity"
POWER = "RelPower"
PRODUCT = "RelTypeOf"
GAS_REQUIREMENTS = "RelGasRequirements"
HAS_POWER_CONSUMPTION = "RelPowerConsumption"
HAS_BATTERY_RUNTIME = "RelBatteryRunTime"
REQUIRED_CURRENT = "RelCurrent"
HAS_OUTPUT_VOLTAGE = "RelOutput"
HAS_FREQUENCY = "RelFrequency"
HAS_OVEN_CAVITY_DIMENSION = "RelOvenCavityDimension"
HAS_SPECIFICATION = "RelHasSpecification"
REL_TYPE_OF = "TypeOf"

# constants used in schema
DOMAIN = "domain"
RANGE = "range"
LABEL = "label"
VALUE = "value"
ID = "id"
PROP = "prop"
ISSUE_TYPE = "issue_type"
UNIT = "unit"
TOPIC = "Topic"
CLASS = "Class"
FEATURE = 'feature'
VALUE_NODE = "Value"
CHECKLIST_DESC_NODE = "ChecklistDescription"
USAGE_NODE = "Usage"
COMPONENT_NODE = "Component"
DIAGNOSE_FAULT_NODE = "DiagnoseFault"
CONTROL_PANEL_NODE = "ControlPanel"
TABLE_CELL_NODE = "TableCell"
TABLE_ROW_NODE = "TableRow"
PROCEDURE_NODE = "Procedure"
FEATURE_NODE = "Feature"
OPERATION_SECTION_NODE = "OperationSection"
OPERATION_SUB_SECTION_NODE = "OperationSubSection"

SERIAL_NO_PROP = "serial_no"
STEP_NO_PROP = "step_no"
SECTION_NAME_PROP = "section_name"
TURN_ON_PROP = 'turn_on'
TURN_OFF_PROP = 'turn_off'
FEATURE_NAME_PROP = "feature_name"
RELATION_NAME = "relation_name"
HOW_TO_STORE = "how_to_store"
PART_NUMBER_PROP = "part_number"
ENTITY_PRD_TYPE = "entity_prd_type"
PROBLEM_PROP = "problem"
ERR_CODE_PROP = "error_code"
NOISE_PROP = "noise"
SUB_PRODUCT_TYPE = "sub_product_type"
#############################################################
# dict constant lists all possible keys of specification table
TABLE_KEYS = {SPECIFICATIONS: ['Specifications', 'Product Specifications',
                               'Product Specification', 'Specification'],
              MODEL: ['Model', 'Model name', 'Model Name'],
              PRODUCT: ['Product type', 'Type'],
              DESCRIPTION: ['Description', 'Product Description', 'Name'],
              VOLTAGE_REQUIREMENTS: ['Electrical requirements', 'Power supply',
                                     'Rated voltage'],
              DIMENSION: ['Dimensions', 'Dimension', 'Size'],
              NET_WEIGHT: ['Net weight', 'Net Weight', 'Weight'],
              MAX_SPIN_SPEED: ['Max. spin speed', 'Max spin speed', 'Spin speed'],
              WATER_PRESSURE: ['Min. / Max. water pressure',
                               'Max water pressure', 'Max. water pressure',
                               'Guarantee installation water pressure',
                               'Permissible water pressure'],
              TEMPERATURE: ['Temperature range', 'Operating Temperature Range', 'Inlet Water Temperature', 'Temp'],
              CAPACITY: ['Capacity', 'Wash capacity', 'Capacity (Washer/Dryer)', 'Capacity of Oven Cavity'],
              POWER: ['Max.Watt', 'Max. Watt'],
              GAS_REQUIREMENTS: ['Gas Requirements'],
              HAS_POWER_CONSUMPTION: ['Power Consumption', 'Rated Power Consumption'],
              HAS_BATTERY_RUNTIME: ['Battery Run Time'],
              REQUIRED_CURRENT: ['Rated Current'],
              HAS_OUTPUT_VOLTAGE: ['Microwave Output'],
              HAS_FREQUENCY: ['Frequency', 'Freq'],
              HAS_OVEN_CAVITY_DIMENSION: ['Oven Cavity Dimensions', 'oven cavity dimension', 'Cavity Size']
              }

# constants to return codes
SUCCESS = 200
BAD_REQUEST = 400
CLIENT_ERROR = 401
DATA_NOT_FOUND = 404
CONNECTION_ERROR = 501
INTERNAL_ERROR = 500
DATA_NOT_FOUND = 202
NOT_SUPPORTED = 204
resp_code = "response_code"
resp_data = "response_data"
error_msg = "error_msg"
query_stats = "query_stats"

# Constants used for Cypher query
START_NODE = "domain"
END_NODE = "range"
RELATION = "relation"
PROP_KEY = "prob_key"
PROP_VALUE = "prob_value"
NAME = "Name"
TYPE = "type"
SECTION = "section"

# sections in manual
SPEC_SECTION = "Specification"
TROB_SECTION = "Troubleshooting"
TROUBLESHOOTING = "TROUBLESHOOTING"
ERR_MSG = "Error Messages"
EDISP_ERR_MSG = "ezDispense Error Messages"
NOISES = "Noises"
SCREEN = "Screen"
OPERATION = "Operation"
OPERATION_WASHER = "Operation washer"
OPERATION_DRYER = "Operation dryer"
PERFORMANCE = "Performance"
ODOR = "Odor"
EZDISPENSE = "ezDispense"
WIFI = "Wi-Fi"
COOLING = "Cooling"
WATER = "Water"
ICE_AND_WATER = "Ice & Water"
PARTS_AND_FEATURE = "Parts & Features"
FAQ = "FAQ"
ICE = "Ice"
PROBLEM = "Problem"
FUNCTION = "Function"
ETC = "ETC"
CRAFT_ICE = "Craft Ice"
VOICE_ASSIST = "Voice Assistant"
MOP_NOZZLE = "Mop Nozzle"
DIAGNOSING_FAULT = "Diagnosing a fault"
BFR_CALL_FOR_SERVICE = "Before Calling for Service"
REFRIG_FROZEN = "Refrigerated & frozen"
DIAGNOSING_FAULT_THINQ = "Diagnosing faults with LG ThinQ"
DIAGNOSING_FAULT_BEEP = "Diagnosing a fault with a beep"
DIAGNOSING_FAULT_WIFI = "Diagnosing a fault with a WiFi"
KO_DIAGNOSING_FAULT_BEEP = "신호음으로 고장 진단하기"
KO_DIAGNOSING_FAULT_THINQ = "LG ThinQ로 고장 진단하기"
KO_DIAGNOSING_FAULT_WIFI = "Wi-Fi로 고장 진단하기"
PRB_SOLVING = "Problem solving"
WASHER = "Washer"
DRYER = "Dryer"
WASH_DRY_CMN = "Washing machine/dryer common"
WATER_FILTER = "Water Filter"

# keys used in troubleshooting json and for response template
REASON_KEY = "reason"
SOLUTION_KEY = "solution"
CAUSES_SOL_KEY = "cause-sol"
DESC_KEY = "desc"
RESPONSE_KEY = "response_key"
QUERY_INTENT = "query_intent"
CATEGORY = "Category"
SPECIFICATION_TAG = "specification"
MODEL_TR = "model"
RS_PRODUCT_TYPE = "product_type"
RS_SUB_PRODUCT_TYPE = "sub_product_type"
SP_RESPONSE_KEY = "response_key_template"
SP_RESPONSE_KEY_WP = "response_key_template_prd"
TR_CAUSE_SINGULAR = "cause_singular"
TR_CAUSE_PLURAl = "cause_plural"
TR_SOL_SINGULAR = "sol_singlar"
TR_SOL_PLURAL = "sol_plural"
PRODUCT_TYPE_KEY = "Product_type"
SUB_PRD_TYPE_KEY = "Sub_Product_type"
MODELS_KEY = "Models"
DATA_KEY = "Data"
COMMON_INFO_KEY = "common_info"
UNIQUE_INFO_KEY = "unique_info"
DUMMY_SECTION_KEY = "dummy_section"
PARTNUMBER = "partnumber"

# Troubleshooting cause and solution templates
causes_korean_header = "발생원인"
solutions_korean_header = "해결방안"

# Troubleshooting Error messages section constants
HAS_ERROR = "HAS_ERROR_CODE"
HAS_NOISE = "HAS_NOISE_PROBLEM"
HAS_SOLUTION = "HAS_SOLUTION"
HAS_PROBLEM = "HAS_PROBLEM"
HAS_PART_NUMBER = "HAS_PART_NUMBER"
HAS_TROUBLESHOOTING_PROBLEM = "HAS_TROUBLESHOOTING_PROBLEM"
HAS_DIMENSION = "HAS_DIMENSION"
HAS_OVEN_DIMENSION = "HAS_OVEN_CAVITY_DIMENSION"
HAS_GAS_REQUIREMENTS = "HAS_GAS_REQUIREMENTS"
HAS_QUESTION = "HAS_QUESTION"
HAS_ANSWER = "HAS_ANSWER"
# relations used for unstructured operation section
HAS_SECTION_EXTRA_INFO = "HAS_SECTION_CAUTION|HAS_SECTION_NOTE"
HAS_FEATURE_EXTRA_INFO = "HAS_CAUTION|HAS_NOTE"

INTENT = "Intent"
ERROR_KEYS = "ERROR_KEYS"
NOISE_KEYS = "NOISE_KEYS"
PROBLEM_KEYS = "PROBLEM_KEYS"
ERROR_CODE = "error_code"
NOISE = "noise"

# Operation Section constants for mapping with RDF
HAS_CHECKLIST = "HAS_CHECKLIST"
HAS_CONTROL_PANEL_FEATURE = "HAS_CONTROL_PANEL_FEATURE"
HAS_CONTROL_PANEL = "HAS_CONTROL_PANEL"
HAS_FEATURE = "HAS_FEATURE"
HAS_COMPONENT = "HAS_COMPONENT"
STORING_FOOD = "STORING_FOOD"
STORAGE_TIP = "STORAGE_TIP"
HAS_SUB_INSTRUCTION = "HAS_SUB_INSTRUCTION"
HAS_USAGE = "HAS_USAGE"
HAS_MODE = "HAS_MODE"
HAS_SUB_COMPONENT = "HAS_SUB_COMPONENT"
ATTACHING_DETACHING = "ATTACHING_DETACHING"
HAS_PROCEDURE = "HAS_PROCEDURE"
HAS_CAUTION = "HAS_CAUTION"
HAS_NOTE = "HAS_NOTE"
HAS_WARNING = "HAS_WARNING"
HAS_SECTION_CAUTION = "HAS_SECTION_CAUTION"
HAS_SECTION_NOTE = "HAS_SECTION_NOTE"
HAS_IMAGE = "HAS_IMAGE"
HAS_OPERATION_SECTION = "HAS_OPERATION_SECTION"
HAS_SUB_SECTION = "HAS_SUB_SECTION"
HAS_TABLE = "HAS_TABLE"
HAS_TABLE_ROW = "HAS_TABLE_ROW"
HAS_TABLE_CELL = "HAS_TABLE_CELL"

# Constants to Support Operation
CHECKLIST = "Checklist"
CONTROL_PANEL_FEATURE = 'Control Panel Features'
SABBATH_MODE = 'Sabbath Mode'
USING_SABBATH_MODE = 'Using the Sabbath Mode'
DESCRIPTION = "Description"

# Constants for XML output
TABLE_DETAILS = "table_details"
PRODUCT_TYPE = "Product_type"
MODELS = "Models"
DATA = "Data"
APPLIANCE = "Appliance"
ENTRY = "entry"
ENTRIES = "entries"
CHECKS = 'checks'
STEP = 'step'
FEATURES = 'features'
FEATURE = "feature"
EXPLANATION = 'explanations'
CAUTION = 'caution'
NOTE = 'note'
DESCRIPTION_KEY = "Description"
DESCRIPTION_POINTS = "Description points"
MEDIA = "media"
MEDIA_URL = "mediaUrl"
MEDIA_TYPE = "mediaContentType"
MEDIA_SIZE = "mediaFileSize"
MODULE_FLAG = "module_used"
QUESTION_TYPE = "question_type"

# Troubleshooting Error messages section constants for refrigerator
HAS_ICE_PROBLEM = "HAS_ICE_PROBLEM"
HAS_COOLING_PROBLEM = "HAS_COOLING_PROBLEM"
HAS_WIFI_PROBLEM = "HAS_WIFI_PROBLEM"

# RDF property constants to support korean manuals
DIAGNOSE_WITH_LG_THINQ = "DIAGNOSE_WITH_LG_THINQ"
DIAGNOSE_WITH_BEEP = "DIAGNOSE_WITH_BEEP"
DIAGNOSE_WITH_WIFI = "DIAGNOSE_WITH_WIFI"

# properties used for enrich knowledge for node in graph
VERB = "predicate"
ENTITY = "entity"
TEMPORAL = "temporal"
PURPOSE = "purpose"
CAUSE = "cause"

# constants used to get knowledge from SRL,constituency parser outputs
NP = "NP"
VB = "VB"
TMPRL = "temp"
WASHING_MACHINE = "WASHING_MACHINE"
REFRIGERATOR = "REFRIGERATOR"
AC = "AC"
C_REFRIGERATOR = "refrigerator"
C_WASHING_MACHINE = "washing machine"
C_AIR_CONDITIONER = "air conditioner"
C_VACUUM_CLEANER = "vacuum cleaner"
C_MICROWAVE_OVEN = "microwave oven"
WINDOW_PRD = 'WINDOW(INVERTER)'
P_AC = 'PORTABLE AIR CONDITIONER'
AIR_CONDITIONER = 'AIR CONDITIONER'


class UnitExtConstants(object):
    STATUS = "status"
    VALUE = "value"
    UNITS = "units"
    TYPE = "type"
    SPEC_KEY = "spec_key"
    RANGE = "range"
    SINGLE = "single"
    DIMENSION = "dimension"

####XML TAG constants#######################
class XMLTags(object):
    # tags used in xml
    BOOK_TAG = "book"
    UNKNOWN_TAG = "unknown_tag"
    PREFACE_TAG = "preface"
    TITLE_TAG = "title"
    SECTION_TAG = "section"
    CHAPTER_TAG = "chapter"
    APPENDIX_TAG = "appendix"
    BOOKINFO_TAG = "bookinfo"
    BUYERMODEL_TAG = "buyermodel"
    PARTNUMBER_TAG = "partnumber"
    PRODUCTNAME_TAG = "productname"
    SUMMARY_TAG = "summary"
    TOPIC_TAG = "topic"

    SPECIFICATION_TAG = "specification"

    # tags used in the xml table element
    TABLE_TAG = "table"
    TGROUP_TAG = "tgroup"
    TBODY_TAG = "tbody"
    THEAD_TAG = "thead"
    ROW_TAG = "row"
    ENTRY_TAG = "entry"
    PARA_TAG = "para"
    COL_ATTRIB = "cols"
    KEY_TAG = "key"
    COLNAME_ATTRIB = "colname"
    EMPHASIS_TAG = "emphasis"
    SIMPLESECT_TAG = "simplesect"
    VAR_LIST_TAG = "variablelist"
    VAR_LIST_ENTRY_TAG = "varlistentry"
    TERM_TAG = "term"

    # tags used under troubleshooting section
    TROUBLESHOOT_TAG = "troubleshooting"
    TROUBLELIST_ENTRY_TAG = "troublelistentry"
    PROBLEM_TAG = "problem"
    TROUBLELISTITEM_TAG = "troublelistitem"
    REASON_TAG = "reason"
    ITEMIZEDLIST_TAG = "itemizedlist"
    ORDEREDLIST_TAG = "orderedlist"
    LISTITEM_TAG = "listitem"
    SOLUTION_TAG = "solution"
    CAUTION_TAG = "caution"
    NOTE_TAG = "note"
    FIGURE_TAG = "figure"
    CALLOUTLIST_TAG = "calloutlist"
    OPERATION_TAG = "operation"
    PROCEDURE_TAG = "procedure"
    STEP_TAG = "step"
    SUMMARY_TAG = "summary"
    PREREQUISITES_TAG = "prerequisites"
    LANG_ATTRIB = "lang"
    GRAPGHICGRP_TAG = "graphicgroup"
    GRAPHIC_TAG = "graphic"
    FILEREF_ATTRIB = "fileref"
    WARNING_TAG = "warning"
    ICON_TAG = "icon"
    FOOTNOTE_GROUP_TAG = "footnotegroup"
    MOREROWS_ATTRIB = "morerows"

    KOREAN_LANG = "ko"
    INTERNAL_SECTION_TAG = [SUMMARY_TAG, CAUTION_TAG, WARNING_TAG, NOTE_TAG]
    KOREAN_INTERNAL_SECTION_TAG = ["경고", "주의", "절차"]

class ExtractionConstants(object):
    NO_SECTION_MSG = "Requested section not found"
    FRM_NS_MSG = "Content format is not supported for extraction.Create intermediate format for successful verification"
    STATUS_STR = "status"
    ERR_MG = "err_msg"
    DATA_KEY = "data"
    FIGURE = "figure"
    SIZE = "size"
    FILE_TYPE = "file_type"
    FILE_PATH = "file_path"
    FOOD_KEY = 'Food'
    HOW_TO_STORE_KEY = 'How to Store'
    OPERATION_KEY = "OPERATION"
    KEPLER_PRD = "kepler"

    # Section hierarchy framing constants
    MAIN_TITLE_CHK_BFR_MALFUNCTION = "고장 신고 전 확인하기"
    TITLE_DIA_FAULT = "고장 진단하기"
    TITLE_TROUBLESHOOTING = "문제 해결하기"
    PROD_STR = '세탁기'

    STR_FLAG_DIA_SECTION = "diag"

    KEPLER_PRD_NAME_IN_MANUAL = "laundry center"
    INSTALLATION = "installation"
    MAINTANENCE = "maintenance"
    APPENDIX = "appendix"
    USING_LG_THINQ = "lgthinq"
    SAFETY = "safety_instructions"
    WARRANTY = "product_warranty"
    LEARN = "learn"


    SECTION_NAME_TRANSLATE = {
        "고장 신고 전 확인하기": TROUBLESHOOTING,
        "고장 진단하기": DIAGNOSING_FAULT,
        "문제 해결하기": BFR_CALL_FOR_SERVICE,
        "냉장 & 냉동": REFRIG_FROZEN,
        "부품": PARTS_AND_FEATURE,
        "소음": NOISES,
        "와이파이": WIFI,
        "화면": SCREEN,
        "LG ThinQ로 고장 진단하기": KO_DIAGNOSING_FAULT_THINQ,
        "신호음으로 고장 진단하기": KO_DIAGNOSING_FAULT_BEEP,
        "Wi-Fi로 고장 진단하기": KO_DIAGNOSING_FAULT_WIFI,
        "문제 해결": TROUBLESHOOTING,
        "얼음": ICE,
        "사용 관련": OPERATION,
        "사용하기": OPERATION,
        "사용하기 - 세탁기": OPERATION_WASHER,
        "사용하기 - 건조기": OPERATION_DRYER,
        "에러 메시지": ERR_MSG,
        "에러 메세지": ERR_MSG,
        "알림 메시지": ERR_MSG,
        "세탁기": WASHER,
        "건조기": DRYER,
        "세탁기/건조기 공통": WASH_DRY_CMN,
        "정수 필터": WATER_FILTER,
        "빅 아이스": CRAFT_ICE,
        "물": WATER,
        "설치하기": INSTALLATION,
        "관리하기":MAINTANENCE,
        "경고": XMLTags.WARNING_TAG,
        "주의": XMLTags.CAUTION_TAG,
        "절차": XMLTags.PROCEDURE_TAG
    }

    ENG_TO_KOREAN_SEC_TRANSLATE = {"troubleshooting": ["고장 신고 전 확인하기"],
                                   "diag_beep": ["신호음으로 고장 진단하기"],
                                   "diag_thinq": ["LG ThinQ로 고장 진단하기"],
                                   "error": ["에러 메시지"],
                                   "noise": ["사용 관련"],
                                   "problem": ["사용 관련","물","부품"],
                                   "wifi problem": ["와이파이"],
                                   "wi-fi": ["와이파이"],
                                   "ice problem": ["얼음","냉장 & 냉동"],
                                   "cooling problem": ["냉장 & 냉동"]}

    # Different naming used for a section in manuals
    SECTION_NAMING_LIST = {SPEC_SECTION: ['Specifications', 'Product Specifications',
                                          'Product Specification', 'Specification'],
                           TROB_SECTION: ['TROUBLESHOOTING', '고장 신고 전 확인하기', '문제 해결'],
                           FAQ: ['FAQs', 'FAQ', 'Q&A', 'FAQs: Frequently Asked Questions',
                                 'Frequently Asked Questions'],
                           ERR_MSG: ['Error Messages'],
                           EDISP_ERR_MSG: ['ezDispense Error Messages'],
                           NOISES: ['Noises', 'Noise'],
                           OPERATION: ['Operation', 'OPERATION','사용하기','사용 관련','사용하기 - 세탁기','사용하기 - 건조기'],
                           PERFORMANCE: ['Performance'],
                           ODOR: ['Odor', 'Odour'],
                           EZDISPENSE: ['ezDispense'],
                           WIFI: ['Wi-Fi'],
                           COOLING: ['Cooling'],
                           ICE_AND_WATER: ['Ice & Water', 'Ice', 'Ice  & Water'],
                           WATER: ['Water'],
                           PARTS_AND_FEATURE: ['Parts & Features', 'Parts  & Features'],
                           ICE: ['Ice'],
                           PROBLEM: ['Problem'],
                           FUNCTION: ['Function'],
                           ETC: ['ETC'],
                           CRAFT_ICE: ['Craft Ice'],
                           VOICE_ASSIST: ['Voice Assistant'],
                           MAINTANENCE: ['관리하기'],
                           INSTALLATION: ['설치하기'],
                           }

    XSLT_SECTION_NAMING_LIST = {SPEC_SECTION: ['Specifications', 'Product Specifications',
                                          'Product Specification', 'Specification'],
                           "troubleshooting": ['TROUBLESHOOTING', '고장 신고 전 확인하기', '문제 해결'],
                           FAQ: ['FAQs', 'FAQ', 'Q&A', 'FAQs: Frequently Asked Questions',
                                 'Frequently Asked Questions'],
                           ERR_MSG: ['Error Messages'],
                           EDISP_ERR_MSG: ['ezDispense Error Messages'],
                           NOISES: ['Noises', 'Noise'],
                           OPERATION: ['Operation', 'OPERATION','사용하기','사용 관련','사용하기 - 세탁기','사용하기 - 건조기'],
                           PERFORMANCE: ['Performance'],
                           ODOR: ['Odor', 'Odour'],
                           EZDISPENSE: ['ezDispense'],
                           WIFI: ['Wi-Fi'],
                           COOLING: ['Cooling'],
                           ICE_AND_WATER: ['Ice & Water', 'Ice', 'Ice  & Water'],
                           WATER: ['Water'],
                           PARTS_AND_FEATURE: ['Parts & Features', 'Parts  & Features'],
                           ICE: ['Ice'],
                           PROBLEM: ['Problem'],
                           FUNCTION: ['Function'],
                           ETC: ['ETC'],
                           CRAFT_ICE: ['Craft Ice'],
                           VOICE_ASSIST: ['Voice Assistant'],
                           MAINTANENCE: ['관리하기'],
                           INSTALLATION: ['설치하기'],
                           APPENDIX: ['부록'],
                           USING_LG_THINQ: ['LG ThinQ 사용하기'],
                           SAFETY: ['안전을 위해 주의하기'],
                           WARRANTY: ['제품 보증서 보기'],
                           LEARN: ['알아보기']
                           }

    # Text based Koren Error Codes
    ANTI_WRINKLE_ER_CODE = "구김 방지"
    WATER_REPLENISHMENT_ER_CODE = "물 보충"
    DUMPING_WATER_ER_CODE = "물 버림"
    ERROR_CODE_MAPPER = {"dEz": "dE2",
                         "tEz": "tE2",
                         "LEz": "LE2",
                         "[L": "CL",
                         "tEs": "tE5",
                         "[=]~ENd": ANTI_WRINKLE_ER_CODE,
                         "물 보충에 불이 깜빡거려요.": WATER_REPLENISHMENT_ER_CODE,
                         "물 버림에 불이 깜빡거려요.": DUMPING_WATER_ER_CODE,
                         "dE라고 떠요.": "dE",
                         "Nb라고 떠요.": "Nb",
                         "NA라고 떠요.": "NA",
                         "Ns라고 떠요.": "Ns",
                         "1F라고 떠요.": "1F",
                         "vs": "vs, v5, us, u5"}

    # since the tabular content structure is in not supported format skipping this section
    SKIP_SECTION = ["사용하면 안 되는 의류", "건조물 분류하기", "섬유제품 관리 기호 및 설명","건조기 사용 금지 건조물", "정수 필터"]

    @staticmethod
    def map_error_code(error_code):
        for key in ExtractionConstants.ERROR_CODE_MAPPER.keys():
            logger.debug("key check : %s - %s - %s",key,error_code,(key in error_code))
            if key in error_code:
                logger.debug("key : %s - %s",key, error_code.replace(key, ExtractionConstants.ERROR_CODE_MAPPER[key]))
                error_code = error_code.replace(key, ExtractionConstants.ERROR_CODE_MAPPER[key])
        return error_code

    @staticmethod
    def inv_map_error_code(error_code):
        for key, value in ExtractionConstants.ERROR_CODE_MAPPER.items():
            logger.debug("key check : %s - %s - %s",key,error_code, value)
            actual_err_in_manual = value.split(",")
            logger.debug("actual_err_in_manual : %s",actual_err_in_manual)
            len_val = len(actual_err_in_manual)
            logger.debug("no of erro codes : %s", len_val)
            if ((len_val > 1) and (error_code.lower() in value.lower())) or ((len_val == 1) and (error_code.lower() == value.lower())):
                for actual_err in actual_err_in_manual:
                    logger.debug("key : %s - %s",key, error_code.replace(actual_err, key))
                    error_code = error_code.replace(error_code, key)
                break
        return error_code


# Constants and functions for Image Handling
IMAGE_NAME = "image_name"
IMAGE_CONTENT = "image_content"


def get_image_db_path():
    """
    Get the image db path, server ip , port
    """
    config_file_path = (os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..',
                     'config', 'configuration.ini')))
    config_parser = ConfigParser()
    config_parser.read(config_file_path)

    file_path = config_parser.get("image_db", "image_db_path")
    ip_address = config_parser.get("server_config", "ip")
    port_number = config_parser.get("server_config",
                                    "port_number")
    return file_path, ip_address, port_number


####dialogue manager constants##############
class RespKeys(object):
    """
        key constants used for json response
    """
    DB_RESP = "db_resp"
    EXTRACTED_INFO = "extracted_info"
    INTENT = "intent"
    PROB_TYPE = "problem_type"
    KEY_INFO = "key_info"
    SUCCESS = 100
    FAILURE = 101
    UNIT_FAIL_MSG = "Unit conversion not supported"


def load_json():
    """
        get the file path from config and convert
        the schema to dict
    """
    CONFIG_PATH = (os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..',
                     'config', 'configuration.ini')))
    config_parser = ConfigParser()
    config_parser.read(CONFIG_PATH)
    abspath_path = os.path.abspath(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '..', ))
    file_path = os.path.join(abspath_path,
                             config_parser.get("troubleshooting",
                                               "ts_key_mapping"))
    # Opening JSON file
    f = open(file_path, encoding='utf-8')

    # returns JSON object as a dictionary
    content = json.load(f)

    # Closing file
    f.close()
    return content


# schema variable to have all trob keys
trob_section = load_json()


class ProblemTypes(object):
    """
    Constants for problem types
    """
    # TS problems
    ERROR = 'error'
    NOISE = 'noise'
    PROBLEM = 'problem'
    ICE_PROBLEM = 'ice problem'
    COOLING_PROBLEM = 'cooling problem'
    WIFI_PROBLEM = 'wifi problem'
    ERROR_CODE = 'error_code'
    DIAG_BEEP = 'diag_beep'
    DIAG_THINQ = 'diag_thinq'
    # extra sections
    DIRECT_INFO = 'direct'
    EXTRA_INFO = 'extra_info'
    EXTRA_WARNING = 'warning'
    EXTRA_NOTE = 'note'
    EXTRA_CAUTION = 'caution'
    # operation intents
    DESCRIPTION = 'desc'
    USAGE = 'usage'
    COMPONENT = 'component'
    ANSWERS = 'answers'
    FEATURE = 'feature'
    # English: control panel
    CONTROL_PANEL = '기능조작부 사용하기'
    CHECKLIST = 'checklist'

    # key constants used in classifier output dictionary
    SECTION = "section"
    SUB_SECTION = "sub_section"
    CATEGORY = "category"
    FOLLOW_UP = "follow_up"
    INTENT = "intent"
    QUES_TYPE = "question_type"


class QuestionTypes(object):
    """
    Constants for Question types
    """
    FACTOID = 'factoid'
    DESCRIPTIVE = 'description'
    LIST = 'list'
    BOOL = 'bool'


class Section(object):
    """
    section constants used for text similarity module
    """
    SPEC = 'Specification'
    TROB = 'Troubleshooting'
    FAQ = 'FAQ'
    OPERATION = 'Operation'


class ClientType(object):
    HTML = 1
    RCS = 2
    KMS = 3
    BNC = 4  # Butler New client

class InfoKnowledge(object):
    """
        constants used for info engine module to define
        keys used for retrieval od SPEC/TS
    """
    SIMILARITY = "similarity_key"
    CONS_PARSER = "cons_parser"
    SRL = "srl"
    PROB_VAL_SPECI = "prob_value_specific"
    PROB_VAL_GEN = "prob_value_general"
    KEY = "key"
    SIDE = "side"
    WITH_OPEN = "with"
    WITHOUT_OPEN = "without"
    SIDE_STATUS = "side status"
    OPEN_STATUS = "open status"


# KER Input/Output Json key constants
class IOConstants(object):
    HTTP_ERR_CODE = 'http_error_code'
    RESP_CODE = 'response_code'
    RESP_MSG = 'response_message'
    QUESTION = 'question'
    ANSWER = 'answer'
    KER_CNTXT = 'ker_context'
    CLASSIFIER_INFO = 'classifier_info'
    SIMILARITY_KEY = 'similarity_key'
    PREV_QUESTION = 'prev_question'
    PRODUCT = "product"
    SUB_PRODUCT = "sub_product"
    MODEL = 'model'
    MODEL_NO = 'model_no'
    PART_NO = 'part_no'
    SPEC_KEY = 'spec_key'
    UNIT = 'unit'
    PREV_ANSWER = 'prev_answer'
    KER_CONTEXT = 'ker_context'
    EXTRACTED_INFO = 'extracted_info'
    CAUSES_SOL_KEY = "cause-sol"
    REQ_ID = "request_id"
    QUERY = "query"

    # Constants used for Hybrid Approach
    HYBRID_RESPONSE = "hybrid_response"
    HY_RES_MAPPED_KEYS = "mapped_keys"
    HY_RES_SCORE = "score"
    HY_RES_STATUS = "status"
    HY_RES_CHOSEN_KEY_FROM_USER = "chosen_key_from_user"
    HY_RES_STATUS_SUPPORTED_PRODUCT = "supported_products"
    HY_RES_STATUS_ASKING_QUESTION = "asking_question"
    HY_RES_STATUS_SATISFIED = "satisfied_with_results"
    HY_RES_STATUS_NOT_SATISFIED = "not_satisfied_with_results"
    HY_SEE_MANUAL_CONTENTS = 'see_manual_contents'
    HY_SEE_SECTION_CONTENTS = 'see_section_contents'
    HY_REQ_TYPE = 'request_type'
    HY_RESP_TYPE = 'response_type'
    HY_RESPONSE = 'response'
    HY_SELECTED_OPTION = 'selected_option'
    HY_MATCHED_KEY = 'matched_key'
    HY_APPROACH = 'approach'
    HY_RECOMMENDATION = "recommendation"
    HY_BEST_MATCHES = "best_matches"
    HY_CONTENT_TYPE = "content_type"
    HY_CONTENT_2LEVEL = "2level"
    HY_CONTENT_1LEVEL = "1level"
    # constants for section
    HY_OPERATION = '사용하기'
    HY_INSTALLATION = '설치하기'
    HY_MAINTENANCE = '관리하기'
    HY_TROUBLESHOOTING = '문제 해결하기'
    HY_LEARN = '알아보기'
    HY_SAFETY_INSTRUCTIONS = '안전을 위해 주의하기'
    HY_WARRANTY = '제품 보증서 보기'
    HY_APPENDIX = '부록'
    HY_USING_LG_THINQ = 'LG ThinQ 사용하기'
    HY_SAFETY_PRECAUTION ='안전을 위한 주의 사항'
    # constants for section phrases(lengthy)
    """
    HY_TS_SEC = '문제 해결에 대한 도움이 필요하신가요?'
    HY_OPER_SEC = '제품을 어떻게 사용하는지 알고싶으신가요?'
    HY_SPECI_SEC = '제품사양에 대해 알고 싶으신가요?'
    HY_INST_SEC = '제품을 설치하는데에 도움이 필요하신가요?'
    HY_MAIN_SEC = '제품 관리에 대한 정보가 필요하십니까?'
    """
    HY_TS_SEC = '문제해결'
    HY_OPER_SEC = '사용방법'
    HY_SPECI_SEC = '제품사양'
    HY_INST_SEC = '설치방법'
    HY_MAIN_SEC = '제품 관리'

class ResponseCode(object):
    """
        constants used for return response codes
    """
    SUCCESS = 200
    BAD_RESPONSE = 202
    DATA_NOT_FOUND = 404
    CONNECTION_ERROR = 501
    INTERNAL_ERROR = 500
    CLIENT_ERROR = 401
    BAD_REQUEST = 400
    INVALID = 201
    LANG_NOT_SUPPORTED = 455
    INPUT_PARAM_MISSING = 400
    SECTION_NOT_SUPPORTED = 415
    RESPONSE_GEN_ERROR = 420
    FILE_NOT_FOUND = 421
    FILE_OPEN_ERROR = 423
    FILE_FORMAT_NOT_SUPPORTED = 424
    FILE_IS_EMPTY = 425
    SECTION_NOT_AVAILABLE = 426
    FORMAT_NOT_SUPPORTED = 428
    RCS_SEND_PRD_REG = 429
    PART_NO_NOT_SUPP = 430
    #
    KER_INTERNAL_SUCCESS = 200
    KER_INTERNAL_FAILED = -1


class ExternalErrorCode(object):
    # redefined constants
    MKG_SUCCESS = 0

    # Extraction
    MKG_FILE_FORMAT_NOT_SUPPORTED = 9451
    MKG_FILE_NOT_FOUND = 9452
    MKG_FILE_OPEN_ERROR = 9453
    MKG_FILE_IS_EMPTY = 9454
    MKG_PRODUCT_NOT_SUPPORTED = 9456
    MKG_SECTION_NOT_SUPPORTED = 9457
    MKG_SECTION_NOT_AVAILABLE = 9458
    MKG_FORMAT_NOT_SUPPORTED = 9559

    # Retrieval
    MKG_INVALID_REQUEST = 9461
    MKG_QUERY_LANGUAGE_NOT_SUPPORTED = 9462
    MKG_QUERY_PART_NO_NOT_FOUND = 9463
    MKG_QUERY_MATCHING_DATA_NOT_FOUND = 9464
    MKG_INTERNAL_ERROR = 9465

    MKG_KG_CONNECTION_ERROR = 9471
    MKG_INPUT_PARAMETR_MISSING = 9481

    MKG_RESPONSE_GENERATION_ERROR = 9491
    MKG_OTHER_INTERNAL_ERROR = 9499

    internal_to_ext_err_code = {ResponseCode.SUCCESS: MKG_SUCCESS,
                                ResponseCode.BAD_REQUEST: MKG_INVALID_REQUEST,
                                ResponseCode.CONNECTION_ERROR: MKG_KG_CONNECTION_ERROR,
                                ResponseCode.INVALID: MKG_INVALID_REQUEST,
                                ResponseCode.INTERNAL_ERROR: MKG_INTERNAL_ERROR,
                                ResponseCode.LANG_NOT_SUPPORTED: MKG_QUERY_LANGUAGE_NOT_SUPPORTED,
                                ResponseCode.INPUT_PARAM_MISSING: MKG_INPUT_PARAMETR_MISSING,
                                ResponseCode.SECTION_NOT_SUPPORTED: MKG_SECTION_NOT_SUPPORTED,
                                ResponseCode.DATA_NOT_FOUND: MKG_QUERY_MATCHING_DATA_NOT_FOUND,
                                ResponseCode.RESPONSE_GEN_ERROR: MKG_RESPONSE_GENERATION_ERROR,
                                ResponseCode.SECTION_NOT_AVAILABLE: MKG_SECTION_NOT_AVAILABLE,
                                ResponseCode.FORMAT_NOT_SUPPORTED: MKG_FORMAT_NOT_SUPPORTED,
                                ResponseCode.RCS_SEND_PRD_REG: MKG_INVALID_REQUEST,
                                ResponseCode.PART_NO_NOT_SUPP: MKG_QUERY_PART_NO_NOT_FOUND,
                                ResponseCode.CLIENT_ERROR: MKG_KG_CONNECTION_ERROR,
                                ResponseCode.KER_INTERNAL_FAILED: MKG_INTERNAL_ERROR
                                }


class ResponseMsg(object):
    """
        constants used for return response messages
    """
    MSG_SUCCESS = "Success"
    MSG_INVALID_RESULTS = "Invalid results"
    MSG_INVALID_REQUEST = "Input parameter is missing"
    MSG_PRODUCT_NOT_FOUND = "Product type not able to find"
    MSG_SIMIKEY_ERROR = "Error in finding similarity key"
    MSG_CLASSI_ERROR = "Error in Classifier response"
    MSG_DATA_NOT_FOUND = "Data not found"
    MSG_CONNECTION_ERROR = "Connection fails"
    MSG_INTERNAL_ERROR = "Internal error"
    MSG_PART_NO_NOT_FOUND = "Part no not found"
    MSG_PRODTYPE_NOT_FOUND = "Product type not found"
    MSG_POPULATION_STATUS_OK = "Population count match"
    MSG_POPULATION_STATUS_NOT_OK = "Population count doesnt match"


class ExternalErrorMsgs(object):
    # redefined error messages
    MSG = "MSG"
    HTTP_CODE = "HTTP_CODE"
    ERR_MSGS = {
        ExternalErrorCode.MKG_SUCCESS: {MSG: "Success", HTTP_CODE: 200},
        ExternalErrorCode.MKG_FILE_FORMAT_NOT_SUPPORTED: {MSG: "Supplied Input file format not supported.",
                                                          HTTP_CODE: 415},
        ExternalErrorCode.MKG_FILE_NOT_FOUND: {MSG: "Input file not found", HTTP_CODE: 404},
        ExternalErrorCode.MKG_FILE_OPEN_ERROR: {MSG: "Not able to open the file", HTTP_CODE: 404},
        ExternalErrorCode.MKG_FILE_IS_EMPTY: {MSG: "Input file empty", HTTP_CODE: 404},
        ExternalErrorCode.MKG_PRODUCT_NOT_SUPPORTED: {MSG: "Un supported product.", HTTP_CODE: 415},
        ExternalErrorCode.MKG_SECTION_NOT_SUPPORTED: {MSG: "Requested Section is not supported. ", HTTP_CODE: 415},
        ExternalErrorCode.MKG_SECTION_NOT_AVAILABLE: {MSG: "Requested section not found in the manual.",
                                                      HTTP_CODE: 404},
        ExternalErrorCode.MKG_FORMAT_NOT_SUPPORTED: {MSG: "Requested section content format is not suported.",
                                                     HTTP_CODE: 415},
        ExternalErrorCode.MKG_INVALID_REQUEST: {MSG: "Input format not valid", HTTP_CODE: 400},
        ExternalErrorCode.MKG_QUERY_LANGUAGE_NOT_SUPPORTED: {MSG: "Query language is not supported", HTTP_CODE: 415},
        ExternalErrorCode.MKG_QUERY_PART_NO_NOT_FOUND: {MSG: "Requested part no not supported in KG", HTTP_CODE: 415},
        ExternalErrorCode.MKG_QUERY_MATCHING_DATA_NOT_FOUND: {MSG: "죄송합니다.\n문의하신 내용에 대한 답변을 찾지 못했습니다.",
                                                              HTTP_CODE: 404},
        ExternalErrorCode.MKG_INTERNAL_ERROR: {MSG: "Error in retrieving data", HTTP_CODE: 500},
        ExternalErrorCode.MKG_KG_CONNECTION_ERROR: {MSG: "KG server is not connected.", HTTP_CODE: 502},
        ExternalErrorCode.MKG_INPUT_PARAMETR_MISSING: {MSG: "Required input parameter are missing.", HTTP_CODE: 400},
        ExternalErrorCode.MKG_RESPONSE_GENERATION_ERROR: {MSG: "Error while generating the response", HTTP_CODE: 400},
        ExternalErrorCode.MKG_OTHER_INTERNAL_ERROR: {MSG: "Other error case", HTTP_CODE: 500}
    }


class QueryStats(object):
    """
       constants used for query statistics
    """
    TOTAL_NODES = "total_nodes_created"
    TOTAL_RELATIONS = "total_relation_created"
    TOTAL_TRIPLETS = "total_triplets"
    POPU_STATUS = "population_status"


class TroubleshootingMappingRelation(object):
    """
    For getting the relationship from section mapping
    """
    SECTION_MAPPING = {
        HAS_PROBLEM: [PROBLEM, OPERATION, FUNCTION, PERFORMANCE, ODOR, WATER, ICE_AND_WATER, PARTS_AND_FEATURE,
                      ETC, VOICE_ASSIST, MOP_NOZZLE, SCREEN],
        HAS_ERROR: [ERR_MSG, EDISP_ERR_MSG, EZDISPENSE],
        HAS_NOISE: [NOISES],
        HAS_COOLING_PROBLEM: [COOLING, REFRIG_FROZEN],
        HAS_ICE_PROBLEM: [ICE, CRAFT_ICE],
        HAS_WIFI_PROBLEM: [WIFI],
        DIAGNOSE_WITH_LG_THINQ: [DIAGNOSING_FAULT_THINQ, KO_DIAGNOSING_FAULT_THINQ],
        DIAGNOSE_WITH_BEEP: [DIAGNOSING_FAULT_BEEP, KO_DIAGNOSING_FAULT_BEEP],
        DIAGNOSE_WITH_WIFI:[DIAGNOSING_FAULT_WIFI,KO_DIAGNOSING_FAULT_WIFI]
    }


def get_troubleshooting_mapping_key_relation(section):
    mapping_relation = None
    for key, value in TroubleshootingMappingRelation.SECTION_MAPPING.items():
        if section in value:
            mapping_relation = key
            break

    return mapping_relation


class OperationMappingRelationOld(object):
    """
    For getting the relationship from section mapping
    """
    SECTION_MAPPING = {
        HAS_CHECKLIST: ["Before Use", "Checklist"],
        HAS_CONTROL_PANEL: ["Control Panel"],
        HAS_CONTROL_PANEL_FEATURE: ["Control Panel Features"],
        HAS_FEATURE: ["Sabbath Mode"],
        HAS_COMPONENT: ["Ice and Water Dispenser", "Ice Compartment", "Automatic Icemaker",
                        "Humidity Controlled Crispers",
                        "Glide‘N’Serve", "Refrigerator Shelves",
                        "Door-in-Door", "Door Bins",
                        "Durabase", "Full-Convert Drawer", "Crisper Drawers", "Water Dispenser",
                        "Pantry Drawer", "Ice Tray", "Dairy Bin", "Temperature Controller", "InstaView"],
        HAS_USAGE: ["Using the Ice and Water Dispenser",
                    "Using the Measured Fill", "Locking the Ice and Water Dispenser",
                    "Before Using the In-Door Icemaker", "Before Using the Freezer Icemaker",
                    "Turning the Icemaker On/Off", "Normal Sounds You May Hear",
                    "Preparing for Vacation",
                    "Using the Humidity Controlled Crispers",
                    "Using the Glide‘N’Serve", "Using the Folding Shelf",
                    "Using the Durabase", "Using the Full Convert™ Drawer",
                    "Using the Full Convert Drawer",
                    "Using the EasyLift Bin", "Using the Variable Temperature Control",
                    "Before Using the Water Dispenser", "Using the Water Dispenser", "Using the Ice Tray",
                    "Setting the Fridge Temperature", "Setting the Defrosting",
                    "Cleaning the Dispenser", "Cleaning the Dispenser Tray",
                    "Cleaning the Ice and Water Outlet",
                    "Changing the Craft Ice Mode"],
        HAS_SUB_COMPONENT: ["In-Door Ice Bin", "In-Door Icemaker", "Freezer Icemaker (Cubed Ice)",
                            "Freezer Icemaker (Craft Ice)", "Door-in-Door Compartment",
                            "Door-in-Door Bin", "InstaView Door-in-Door",
                            "InstaView Door-in-Door Compartment",
                            "Door-in-Door Case", "Freezer Icemaker"],
        ATTACHING_DETACHING: ["Detaching the In-Door Ice Bin", "Assembling the In-Door Ice Bin",
                              "Removing/Assembling the Humidity Controlled Crispers",
                              "Detaching/Assembling the Glide‘N’Serve",
                              "Detaching/Assembling the Half Width Shelf",
                              "Detaching/Refitting the Door Bin", "Removing the Crisper Drawers",
                              "Assembling the Crisper Drawers", "Detaching/Assembling the Door Bins",
                              "Detaching/Assembling the Door Bin",
                              "Removing/Assembling the Pantry Drawer", "Removing/Assembling the Dairy Bin",
                              "Detaching/Assembling the Shelf", "Detaching/Assembling Door Bins"],
        STORING_FOOD: ["Storing Food"],
        HAS_SUB_INSTRUCTION: ["Freezing", "Packaging"],
        HAS_MODE: ["Freezer Mode", "Refrigerator Mode"]
    }


# TODO Remove the old OperationMappingRelation
class OperationMappingRelation(object):
    """
    For getting the relationship from section mapping
    """
    SECTION_MAPPING = {
        HAS_FEATURE: ["features"],
        HAS_NOTE: ["note"],
        HAS_CAUTION: ["caution"],
        HAS_WARNING: ["warning"],
        HAS_IMAGE: ["figure"],
        HAS_PROCEDURE: ["procedure"]
    }


def get_operation_mapping_key_relation(section):
    mapping_relation = None
    section = re.sub(r"\s\s+", ' ', section)
    for key, value in OperationMappingRelation.SECTION_MAPPING.items():
        if section in value:
            mapping_relation = key
            break

    return mapping_relation


# Generic Names for Product Names (Will be used while population)

class GenericProductNameMapping(object):
    """
    Generic names for Product Names, used while population
    """
    WASHING_MACHINE_GEN_NAME = "washing machine"
    REFRIGERATOR_GEN_NAME = "refrigerator"
    AIR_CONDITIONER_GEN_NAME = "air conditioner"
    VACUUM_CLEANER_GEN_NAME = "vacuum cleaner"
    MICROWAVE_OVEN_GEN_NAME = "microwave oven"
    DISH_WASHER_GEN_NAME = "dish washer"
    DRYER_GEN_NAME = "dryer"
    STYLER_GEN_NAME = "styler"
    TOP_LOADER_GEN_NAME = "top loader"
    MINI_WASHER_GEN_NAME = "mini washer"
    FRONT_LOADER_GEN_NAME = "front loader"
    REF_LARGE_GEN_NAME = "large"
    REF_MEDIUM_GEN_NAME = "medium"
    REF_KIMCHI_GEN_NAME = "kimchi"
    KEPLER_LOADER_GEN_NAME = "kepler"

    # variable used to map the internal section to entity product type prop
    WASHER_SEC_NAME = "washer"
    DRYER_SEC_NAME = "dryer"
    WASH_DRYER_CMN_SEC_NAME = "washing machine/dryer common"

    PRODUCT_NAME_MAPPING = {
        WASHING_MACHINE_GEN_NAME: ["washing machine", "washer", "laundry center"],
        REFRIGERATOR_GEN_NAME: ["refrigerator", "fridge", "REFRIGERATOR", "FRIDGE", "fridge & freezer"],
        AIR_CONDITIONER_GEN_NAME: ["air conditioner", "ac", "AIR CONDITIONER"],
        VACUUM_CLEANER_GEN_NAME: ["vacuum cleaner", "VACUUM CLEANER"],
        MICROWAVE_OVEN_GEN_NAME: ["microwave oven", "MICROWAVE OVEN", "oven", "OVEN"],
        DISH_WASHER_GEN_NAME: ["dish washer", "dishwasher", "DISH WASHER", "Dish Washer"],
        DRYER_GEN_NAME: ["dryer"],
        STYLER_GEN_NAME: ["styler"],
        TOP_LOADER_GEN_NAME: ["toploader", "top loader"],
        MINI_WASHER_GEN_NAME: ["miniwasher", "mini washer"],
        FRONT_LOADER_GEN_NAME: ["front loader", "frontloader"],
        KEPLER_LOADER_GEN_NAME: ["kepler"],
        REF_MEDIUM_GEN_NAME: ["medium", "refrigerator medium"],
        REF_LARGE_GEN_NAME: ["large", "refrigerator large"],
        REF_KIMCHI_GEN_NAME: ["kimchi", "refrigerator kimchi"]
    }

    # used to map the product type to the entity type prodcut type property value
    PRD_TO_ENT_PRD_MAP = { WASHER_SEC_NAME: ["washing machine", "washer", "laundry center"],
                    DRYER_SEC_NAME: ["dryer"],
                    REFRIGERATOR_GEN_NAME: ["refrigerator", "fridge", "fridge & freezer"],
                    AIR_CONDITIONER_GEN_NAME: ["air conditioner", "ac"],
                    VACUUM_CLEANER_GEN_NAME: ["vacuum cleaner"],
                    MICROWAVE_OVEN_GEN_NAME: ["microwave oven", "oven"],
                    DISH_WASHER_GEN_NAME: ["dish washer", "dishwasher"],
                    STYLER_GEN_NAME: ["styler"]
                  }

    # used to check the whether internal section title is in the list
    INT_SEC = ["washer", "dryer", "washing machine/dryer common", "common"]

    # used to map the internal section title to the list of the entity product type
    SEC_TO_ENT_PRD_MAP = {WASHER_SEC_NAME: ["washer"],
                          DRYER_SEC_NAME: ["dryer"],
                          WASH_DRYER_CMN_SEC_NAME: ["washer", "dryer"],
                          DIAGNOSING_FAULT_THINQ: ["washer", "dryer"],
                          KO_DIAGNOSING_FAULT_BEEP: ["washer", "dryer"],
                          DIAGNOSING_FAULT: ["washer", "dryer"]
                          }
    PRD_KEPLER = "kepler"
    # list of model number of Kepler manual
    KEPLER_MODEL = {PRD_KEPLER: ["W16*TN", "W17*T*", "W16*J", "W16*T*", "W16*S", "W17*T*", "W16*TN"]}

def get_generic_product_name(name_from_extraction):
    generic_product_name = None
    for key, value in GenericProductNameMapping.PRODUCT_NAME_MAPPING.items():
        if name_from_extraction.strip().lower() in value:
            generic_product_name = key
            break

    return generic_product_name


resp_msg = {SUCCESS: "SUCCESS",
            BAD_REQUEST: "BAD_REQUEST",
            CLIENT_ERROR: "CLIENT_ERROR",
            DATA_NOT_FOUND: "DATA_NOT_FOUND",
            CONNECTION_ERROR: "CONNECTION_ERROR",
            INTERNAL_ERROR: "INTERNAL_ERROR",
            DATA_NOT_FOUND: "DATA_NOT_FOUND",
            NOT_SUPPORTED: "NOT_SUPPORTED"}


class FoodIdentifier:
    FOOD_LIST = {"food", "butter", "margarine", "cheese", "milk", "egg", "fruit",
                 "leafy vegetable", "vegetables with skin", "pepper",
                 "carrot", "fish"}
    WINE_LIST = {"wine", "non-vintage champagne", "sparkling wines", "cava ", "asti", "prosecco",
                 "sekt", "vintage champagne", "light white", "rose wine", "muscat", "rosé", "riesling", "pinot grigio",
                 "sauvignon blanc", "semillon", "full-bodied white wine", "light red wine",
                 "chardonnay", "viognier", "white burgundy", "chablis", "pinot noir", "beaujolais ",
                 "barbera ", "grenache", "medium-bodied red wine", "full-bodied red wine", "aged reds",
                 "zinfandel ", "chianti", "red burgundy", "cabernet sauvignon", "merlot", "malbec ",
                 "shiraz", "syrah", "bordeaux", "vintage port", "tawny port", "sweet white wine"
                 }


class ControlPanelIdentifier:
    CONTROL_PANEL_1 = {'control panel 1', 'control panel one'}  # TBD
    CONTROL_PANEL_2 = {'control panel 2', 'freezer', 'control panel two', 'inside the freezer'}


class DrawerIdentifier:
    FULL_CONVERT_DRAWER_LIST = {"full convert drawer", "full convert"}
    CRISPER_DRAWER_LIST = {"crisper drawer", "crisper"}
    PANTRY_DRAWER_LIST = {"pantry drawer", "pantry"}


class DispenserIdentifier:
    WATER_DISPENSER = {'water dispenser', 'water'}
    ICE_AND_WATER_DISPENSER = {'ice dispenser', 'ice'}


class RetrievalConstant(object):
    PARA_QA = "para_qa"
    BOOL_QA = "bool_qa"
    TEXTSIM_BASED = "textsim_based"
    FACTOID_TYPE = "factoid"
	# these are used as a flag to do graph retrieval based on text search
    QUERY_METHOD = 'query_method'
    USE_FULL_TEXT_FLAG = 'full_text_search'


# specific product types
class ProductTypes(object):
    DRYER = "건조기"
    WASHING_MACHINE = "세탁기"
    STYLER = "스타일러"
    KEPLER = "케플러"

class CommonProblemConstants(object):
    DEFAULT_PRODUCT = "washing machine"
    DEFAULT_MODEL_NO = "F214DD"
    DEFAULT_PART_NO = "MFL71485465"
    REQUEST_TYPE = "common_problems"
    COMMON_PROBLEM_MAPPING = {
        "washing machine": ["UE 에러", "IE 에러", "OE 에러",
                            "소음 또는 진동이 심해요","세제 투입구 앞으로 물이 흘러 넘쳐요","신호음으로 고장 진단하기"],
        "refrigerator": ["얼음이 제대로 얼지 않는다","냉장고에서 이상한 냄새가 나요",
                         "냉장고에서 이상한 소리가 나요", "냉장고가 잘 얼지 않는다?"],
        "dryer": ["제품이 작동하지 않습니까?","건조 후 확인해야 할게 있나요?","스팀살균이 뭐예요?",
                  "침구털기가 뭐죠?","모터가 멈춘 것 같아요","건조기 문이 잘 안담겨요"],
        "styler": ["제품이 작동하지 않습니까?","어떤 방법으로 의류 냄새를 제거하나요?","스타일러 화면이 깜빡 거려요",
                   "스타일러 어떻게 사용하나요?","아로마 시트 어떻게 넣나요?","스타일러가 작동을 안해요"],
        "kepler": ["제품이 작동하지 않습니까?","건조기 펌프가 잘 작동하지 않는 거 같아요","배수관이 손상되었습니다?",
                   "건조기가 뜨거운 것 같아요 왜 이런거죠?","옷을 어떻게 분류해요?","세탁 후 뭘 확인해야 하나요?"]
    }

class RecommendationConstants(object):
    RECOMMENDATION_MAPPING = {
        "Detergent" : ["세제 또는 섬유 유연제 사용하기","세제 넣고 사용하기"],
        "fabric softener": ["세제 또는 섬유 유연제 사용하기", "섬유 유연제 넣고 사용하기"],
        "Descaler" : ["tcl","tCL","1~2개월 내에 드럼을 청소하지 않았나요?","제품에서 이상한 냄새가 나요", \
                      "건조 시 냄새가 나나요?","사용 중에 제품에서 냄새가 나나요?","제 품을 처음 사용했나요?","드럼 청소", \
                      "통살균 코스를 사용하여 드럼을 청소하세요","제품 관리하기","통살균 사용하기"],
        "LG D-Soil" : ["세제 또는 섬유 유연제 사용하기","세제 넣고 사용하기"]
    }
    RECOMMENDATION_INFO = {
        "Detergent": {"type" : "세제", "info" : "세제가 필요한가요?"},
        "Descaler": { "type": "석회제거제","info": "세탁통을 청소한지 오래되었나요? 세탁통 클리너로 청소해주세요."},
        "LG D-Soil": {"type": "얼룩제거제","info": "옷에 얼룩이 졌나요? 얼룩제거제를 사용해보세요."},
        "fabric softener": {"type": "섬유 유연제","info": "옷에서 냄새가 난다면 섬유유연제를 사용해보세요."}
    }
