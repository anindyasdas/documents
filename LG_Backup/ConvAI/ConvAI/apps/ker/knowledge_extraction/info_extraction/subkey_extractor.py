"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas.n@lge.com
@modified-by: vanitha.alagarsamy@lge.com
"""
from collections import defaultdict
import re
import logging as logger

from ..constants import params as cs

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class SubKeysExtractor(object):
    """
    defines the method to extract sub keys information for the
    spec keys which has multi hierarchical levels
    """

    # constants for min/max handling
    MINIMUM = {'min': ['min', 'minimum', 'least', 'lowest', 'smallest', 'littlest', 'lower limit']}
    MAXIMUM = {
        'max': ['max', 'maximum', 'greatest', 'highest', 'largest', 'biggest', 'maximal', 'utmost', 'upper limit',
                'most', 'top']}
    RANGE = {'range': [MINIMUM, MAXIMUM]}

    # constants for battery run time
    BAT_ONE = {'one': ['one', '1', 'single', 'a battery', 'sole', 'singular']}
    BAT_TWO = {'two': ['two', '2', 'double', 'dual', 'twin', 'pair', 'couple', 'both']}

    # constants for mode
    TURBO = {'turbo': ['turbo']}
    POWER = {'power': ['power mode', 'mode of power']}
    NORMAL = {'normal': ['normal']}

    # constants for usage in battery run time
    POWER_DRIVE_NOZZLE = {'power drive nozzle': ['Power Drive Nozzle', 'using with the nozzle']}
    NOZZLES_OTHER_POWER_DRIVE = {
        'other than the power drive nozzle': ['Nozzles other than the Power Drive', 'using with the tool']}
    NO_OF_BATTERIES = {'no_of_batteries': [BAT_ONE, BAT_TWO]}
    MODE = {'mode': [TURBO, POWER, NORMAL]}
    USAGE = {'usage': [POWER_DRIVE_NOZZLE, NOZZLES_OTHER_POWER_DRIVE]}

    # constants for dimension
    DEPTH = {'depth': ['depth', 'deep']}
    WIDTH = {'width': ['width', 'breadth', 'wide']}
    HEIGHT = {'height': ['height', 'tall', 'high']}
    DOOR_OPEN = {'dooropen': ["door open"]}
    LID_OPEN = {'lidopen': ["lid open"]}
    WITH = {'with': ['with']}
    WITHOUT = {'without': ['without', 'with out']}  # please tell me the width with door open
    # {'key': 'dimension', 'range': '', 'side': 'width', 'side_status': 'door open/lid open', 'open_status': 'with/with out'}
    SIDE = {'side': [DEPTH, WIDTH, HEIGHT]}
    SIDE_STATUS = {'side status': [DOOR_OPEN, LID_OPEN]}
    OPEN_STATUS = {'open status': [WITHOUT, WITH]}

    # constants for gas requirements
    LPG = {'lpg': ['lpg']}
    NATURAL_GAS = {'natural gas': ['ng', 'natural gas']}
    GAS_TYPE = {'gas_type': [LPG, NATURAL_GAS]}

    similarity_key_val = defaultdict(lambda: [SubKeysExtractor.RANGE])
    similarity_key_val['battery run time'] = [RANGE, NO_OF_BATTERIES, MODE, USAGE]
    similarity_key_val['dimension'] = [RANGE, SIDE, SIDE_STATUS, OPEN_STATUS]
    similarity_key_val['dimensions'] = [RANGE, SIDE, SIDE_STATUS, OPEN_STATUS]
    similarity_key_val['oven cavity dimensions'] = [RANGE, SIDE, SIDE_STATUS, OPEN_STATUS]
    similarity_key_val['power consumption'] = [RANGE, MODE]
    similarity_key_val['gas requirements'] = [RANGE, GAS_TYPE]

    # constants used for check keys
    STR_MODE = 'mode'
    STR_KEY = 'key'
    STR_USAGE = 'usage'

    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if SubKeysExtractor.__instance is None:
            SubKeysExtractor()
        return SubKeysExtractor.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if SubKeysExtractor.__instance is not None:
            logger.error("SubKeysExtractor is not instantiable")
            raise Exception("SubKeysExtractor is not instantiable")
        else:
            SubKeysExtractor.__instance = self

    def extract_specification_subkey(self, user_ques, pred_keys):
        """
            maps similarity key to child keys and return
            dictionary
            Args:
                user_ques: str
                          users question
                pred_keys: str
                           similarity main key mapped to user question
            Returns:
                toreturn_all: dict
                            extracted main key and all sub keys in dict
        """
        toreturn_all = []
        logger.debug("user_ques=%s pred_keys=%s", user_ques, str(pred_keys))
        # main similarity key eg:dimension
        for pk in pred_keys:
            toreturn = {'key': pk}
            # get all child keys  of main key and iterate
            # eg: [RANGE, SIDE, DOOR_OPEN, LID_OPEN]
            for val in self.similarity_key_val[pk]:
                # check all sub keys dictionary and add if
                # sub key present in output dict eg:SIDE
                self.__get_subkey(toreturn, val, user_ques)
            toreturn_all.append(toreturn)
        logger.debug("return value=%s", str(toreturn_all))
        return toreturn_all

    def __get_subkey(self, toreturn, subkey_dict, user_ques):
        """
            Gets the subkeys based on hierarchy
            Args:
                 toreturn: dictionary
                 subkey_dict: subkey dictionary
                 user_ques: str - users question
            Returns:
                 None
        """
        key = list(subkey_dict.keys())[0]
        # get sub key values eg:[DEPTH, WIDTH, HEIGHT]
        values = list(subkey_dict.values())[0]
        toreturn_val = []
        temp_ques = user_ques

        # iterate all values of child key values eg:[DEPTH, WIDTH, HEIGHT]
        for val in values:
            # get all possible values of child key
            # eg: {'depth': ['depth']}
            for k2, v2 in val.items():
                # forming regex to extract child key values and check in user query
                values_reg = '|'.join(['\\b' + v3.lower() + '\\b' for v3 in v2])
                search = re.search(values_reg, temp_ques)
                if search is not None:
                    toreturn_val.append(k2.lower())
                    temp_ques = temp_ques[:search.span()[0]] + temp_ques[search.span()[1]:]

        # add _ separator for every child key if more child keys are found
        toreturn[key] = '_'.join(toreturn_val)

    def get_kepler_product_type(self, query):
        """
            searches given user query is belongs to washer or dryer
            and returns corresponding type
        """
        matched = re.search(cs.GenericProductNameMapping.DRYER_SEC_NAME, query)
        if matched:
            return cs.GenericProductNameMapping.DRYER_SEC_NAME
        else:
            return cs.GenericProductNameMapping.WASHER_SEC_NAME


if __name__ == '__main__':
    subkey_extract = SubKeysExtractor()
    print(subkey_extract.extract_specification_subkey("please tell me the width with door open", ["dimension"]))
    print(subkey_extract.extract_specification_subkey("please tell me the width with out door open", ["dimension"]))
    print(subkey_extract.extract_specification_subkey("please tell me minimum water pressure", ["water pressure"]))
    print(subkey_extract.extract_specification_subkey("please tell me minimum temperature", ["temperature"]))
    print(subkey_extract.extract_specification_subkey("please tell me maximum lpg gas requirements",
                                                      ["gas requirements"]))
    output = subkey_extract.extract_specification_subkey("fetch me min power consumption in power mode",
                                                         ["power consumption"])
    print(output)
    # how much power needed for my cleaner?
    output = subkey_extract.extract_specification_subkey("how much power needed for my cleaner?", ["power consumption"])
    print('1', output)
    output = subkey_extract.extract_specification_subkey("how much power needed for my cleaner in power mode?",
                                                         ["power consumption"])
    print('2', output)
    output = subkey_extract.extract_specification_subkey(
        "By using the power drive nozzle with two batteries, what is the battery runtime?", ["battery run time"])
    print(output)
    output = subkey_extract.extract_specification_subkey(
        "While using a power drive nozzle and two batteries, how much time does my appliance work?",
        ["battery run time"])
    print('3', output)
    assert output[0]['key'] == 'battery run time'
    assert output[0]['no_of_batteries'] == 'two'
    assert output[0]['usage'] == 'power drive nozzle'
    output = subkey_extract.extract_specification_subkey(
        "While using a power drive nozzle and two batteries in power mode, how much time does my appliance work?",
        ["battery run time"])
    print("**", output)
