# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""
import json
import re
import os
import sys
from configparser import ConfigParser
import logging as logger

from .preference import Preference
from .unit_converter import UnitConverter
from .new_unit_converter import NewUnitConverter
from .context_manager import ContextManager
from .value_unit_extractor import ValueUnitExtract
from ..constants import params as cs

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, '..', 'config', 'configuration.ini')


class UnitHandler(object):
    """
       class used to verfiy the context change based on the unit
       from user query
    """

    def __init__(self):
        self.regex_dict = {}
        self.unit_std_dict = {}
        self.spec_unit_data = {}
        self.query_unit = ""
        self.response_unit = ""
        self.value_regex = re.compile(r'((\d+\.\d+)|\d+)', flags=re.IGNORECASE)
        self.value = 0
        self.converted_value = 0
        self._observer = None
        self.fahrenheit = "fahrenheit"
        self.celsius = "celsius"
        self.unit_fahrenheit = "℉"
        self.unit_celsius = "℃"
        self.context_manager = ContextManager()
        self.value_unit_extract = ValueUnitExtract()
        self.unitconv = NewUnitConverter()
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        self.spec_unit_path = os.path.join(current_path, '..',
                                           config_parser.get("spec_unit_db",
                                                             "spec_unit_json"))
        self.unit_regex_fp = os.path.join(current_path, '..',
                                          config_parser.get("unit_regex",
                                                            "unit_regex_json"))
        self.unit_std_fp = os.path.join(current_path, '..',
                                        config_parser.get("unit_standard",
                                                          "unit_standard_json"))

        self._read_regex()
        self._read_unit_std()
        self._read_spec_unit_data()

    def _read_regex(self):
        """
           Read the regex for the spec keys

        Returns
        -------
        None.

        """
        with open(self.unit_regex_fp, 'r', encoding='utf-8') as pf:
            self.regex_dict = json.load(pf)

    def _read_unit_std(self):
        """
           Read the stand units table from json

        Returns
        -------
        None.

        """
        with open(self.unit_std_fp, 'r') as pf:
            self.unit_std_dict = json.load(pf)

    def _read_spec_unit_data(self):
        """
           read the spec unit mapping from json

        Returns
        -------
        None.

        """
        with open(self.spec_unit_path, 'r') as pf:
            self.spec_unit_data = json.load(pf)

    def _get_unit_frm_usr_q(self):
        """
           Identify the units from use query and retrieved 
           knowledge

        Returns
        -------
        None.

        """
        self.query_unit = self._get_unit_from_str(self.user_query)

        if (self.query_unit is not None) and (len(self.query_unit.strip()) > 0):
            self.query_unit = self.query_unit.strip()
            logger.debug("unit in query : %s", self.query_unit)
            tmp_query_unit = self._std_unit(self.query_unit)
            flag = self._validate_unit_spec_key(tmp_query_unit, self.spec_key)

            if flag == False:
                prev_prod = Preference.get_pre_prd()
                self.query_unit = self._std_unit(
                    Preference.get_unit_pref_value(prev_prod))
                flag = self._validate_unit_spec_key(self.query_unit,
                                                    self.spec_key)
                if flag == False:
                    self.query_unit = self.response_unit
            else:
                self.context_manager.update_unit_context(self.query_unit)
                self.query_unit = tmp_query_unit
        else:
            logger.debug("unit not in query")
            prev_prod = Preference.get_pre_prd()
            pref_unit = Preference.get_unit_pref_value(prev_prod)

            if pref_unit is not None:
                self.query_unit = self._std_unit(pref_unit)
                logger.debug("unit frm pref : %s", self.query_unit)
                flag = self._validate_unit_spec_key(self.query_unit,
                                                    self.spec_key)
                if flag == False:
                    self.query_unit = self.response_unit
            else:
                self.query_unit = self.response_unit
                logger.debug("take unit frm resp: %s", self.query_unit)

    def _get_unit_frm_usr_query(self):
        """
           get units from user query

        Returns
        -------
        None.

        """
        self.query_unit = self._get_unit_from_str(self.user_query)

    def _validate_unit_spec_key(self, unit, spec_key):
        """
           cross check the unit with speckey
           Return false if not matched

        Parameters
        ----------
        unit : String
            unit from query.
        spec_key : String
            spec key to get list of units.

        Returns
        -------
        bool
            False - if unit from query and speck units list not matched.
            True - if unit from query and speck units list matched.
        """
        units = self.spec_unit_data[spec_key.lower()]
        if unit in units:
            return True
        else:
            return False

    def _get_unit_from_str(self, user_query):
        """
        get the unit present in query

        Args:
            user_query - query from user
        """
        if self.spec_key is None:
            return None
        regex = self.regex_dict[self.spec_key.lower()]
        logger.debug('unit regex : %s', regex)
        unit_regex = re.compile(regex, flags=re.IGNORECASE)
        unit_tup = unit_regex.search(user_query)
        if unit_tup is not None:
            return unit_tup.groups()[0]
        else:
            return None

    def get_unit_from_query(self, query, spec_key):
        """
        get the units string from user query

        Args:
            query - query from user
            spec_key - spec_key identified from user query
        Return:
            Unit - String:
                   Identified unit
        """
        if spec_key is None:
            return None

        if self._check_spec_key_in_db(spec_key):
            regex = self.regex_dict[spec_key.lower()]
            logger.debug('unit regex : %s', regex)
            unit_regex = re.compile(regex, flags=re.IGNORECASE)
            unit_tup = unit_regex.search(query)
            if unit_tup is not None:
                return unit_tup.groups()[0]
            else:
                return None
        else:
            return None

    def _extract_value_frm_response(self):
        """
          extract value from response

          Returns
          -------
          None.

        """
        final_response = []
        for idx, response in enumerate(self.response):
            response = self.value_unit_extract.extract_value_and_unit(self.spec_key, response)
            logger.debug("conv_reponse : %s", response)
            if response[cs.UnitExtConstants.STATUS] == cs.SUCCESS:
                # standardizing unit to base unit text
                resp_unit = self._std_unit(response[cs.UnitExtConstants.UNITS][0])
                logger.debug("query unit : %s, resp unit: %s", self.query_unit.lower(), resp_unit.lower())
                if self.query_unit.lower() != resp_unit.lower():
                    conv_values = []
                    values = response[cs.UnitExtConstants.VALUE]
                    for value in values:
                        logger.debug("q_unit : %s", self.query_unit)
                        conv_values.append(self._convert_value(value, resp_unit, self.query_unit))
                    final_response.append(
                        self._frame_convert_resp(conv_values, response[cs.UnitExtConstants.TYPE], self.query_unit))

        if len(final_response) > 0:
            return final_response

        return None

    def _frame_convert_resp(self, value, type, unit):
        """
        frma the response from the converted value

        Args:
            value: list of converted value
            type: type whether it is range or single
            unit: converted unit
        """
        if type == cs.UnitExtConstants.SINGLE:
            return str("{:.1f}".format(value[0])) + " " + unit
        elif type == cs.UnitExtConstants.RANGE:
            return str("{:.1f}".format(value[0])) + " - " + str("{:.1f}".format(value[1])) + " " + unit
        elif type == cs.UnitExtConstants.DIMENSION:
            return str("{:.1f}".format(value[0])) + " X " + str("{:.1f}".format(value[1])) + " X " + str(
                "{:.1f}".format(value[2])) + " " + unit

    def _convert_value(self, value, frm_unit, to_unit):
        """
           conver the value to reuqired unit

        Returns
        -------
        Converted value

        """
        converted_value = self.unitconv.convert_value(value, frm_unit, to_unit)
        return converted_value

    def _std_unit(self, unit):
        """
           standadize unit based on unit from json 

        Parameters
        ----------
        unit : String
            unit from user query.

        Returns
        -------
        key : String
            standardized unit.

        """
        keys = self.unit_std_dict.keys()
        for key in keys:
            units = self.unit_std_dict[key]
            if key == self.fahrenheit:
                if (unit == self.unit_fahrenheit) or (unit == self.fahrenheit):
                    return key
            elif key == self.celsius:
                if (unit == self.unit_celsius) or (unit == self.celsius):
                    return key
            elif unit.lower() in units:
                return key

    def _check_spec_key_in_db(self, spec_key):
        """
        check spec key unit conversion is supported or not

        Return:
            True - supported
            False - Unsupported
        """
        keys = self.spec_unit_data.keys()
        logger.debug("keys : %s", keys)
        keys = [key.lower() for key in keys]
        if spec_key.lower() in keys:
            return True
        else:
            return False

    def handle_unit(self, spec_key, user_query, response):
        """
           public method to handle the unit preference

        Parameters
        ----------
        spec_key : String
            speckey from user query.
        user_query : String
            user query.
        response : String
            extracted response from database.

        Returns
        -------
        String
            converted value.
        String
            converted unit.

        """

        logger.debug("response : %s ", response)
        logger.debug("user_query : %s ", response)

        if (spec_key is not None) and (self._check_spec_key_in_db(spec_key.lower())):

            self.spec_key = spec_key.lower()
            self.user_query = user_query
            self.response = response

            if len(response) > 0:
                self._get_unit_frm_usr_q()

                if (self.query_unit is not None) and (len(self.query_unit.strip()) > 0):
                    resp = self._extract_value_frm_response()

                    if resp is not None:
                        return resp, self.query_unit
                    else:
                        return self.response, self.query_unit

                logger.debug("unit not in query")
                return response, None
        elif (spec_key is None) and (len(response) > 0):
            return None, None

        return response, None


if __name__ == "__main__":
    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    Preference.intialize_preference()
    unit_handle = UnitHandler()
    print(unit_handle.handle_unit('Spin speed', 'Tell in rpm', ['1300 rpm']))
    unit_handle.handle_unit('Spin speed', 'Tell in cm', ['1300 rpm'])
    print(unit_handle.handle_unit('width', 'tell in mm', ['45 inch']))
    print(unit_handle.handle_unit('Operating Temperature Range', 'tell in celsius', ['41-95 ℉ (5-35 ℃)']))
    print(unit_handle.handle_unit('Min Operating Temperature Range', 'tell in ℃', ['41 ℉']))
    print(unit_handle.handle_unit('Max Operating Temperature Range', 'tell in ℃', ['95 ℉']))
    print(unit_handle.handle_unit('Water pressure', 'tell in kilopascal', ['20 - 120 psi (138 - 827 kPa)']))
    print(unit_handle.handle_unit('Min Water pressure', 'tell in pascal', ['120.0 psi']))
    print(unit_handle.handle_unit('Spin speed', 'tell in rps', ['950 RPM (±50 rpm)']))
    print(unit_handle.handle_unit('wash capacity', 'tell in liter', ['4.5 cu.ft. / 7.4 cu.ft.']))
    print(unit_handle.handle_unit('dimension', 'tell in mm', ["27'' X 33 1/4'' X 39'' (70cm X 84 cm X 99 cm)"]))
    print(unit_handle.handle_unit('dimension', 'tell in cm', ["29 7/8 x 17 13/18 x 15 13/16 inches"]))
    print(unit_handle.handle_unit('dimension', 'tell in cm', ["23.9 x 13.5 x 19.8 inches (60.6 x 34.4 x 50.3 cm)"]))
    print(unit_handle.handle_unit('dimension', 'tell in meter', ["23.9 x 13.5 x 19.8 inches (60.6 x 34.4 x 50.3 cm)"]))
    print(unit_handle.handle_unit('depth with dooropen', 'tell in inch', ["8.25 inch"]))
