import re
import logging as logger
from fractions import Fraction
import sys
import os

from ..constants import params as cs


class ValueUnitExtract(object):

    def __init__(self):
        self.response_dict = {}
        self.spec_key = None
        self.S_WEIGHT = "weight"
        self.S_WIDTH = "width"
        self.S_DEPTH = "depth"
        self.S_DEPTH_DOOR_OPEN = "depth with dooropen"
        self.S_DEPTH_WITHOUT_DOOR_OPEN = "depth without dooropen"
        self.S_HEIGHT = "height"
        self.S_MAX_OPR_TMP_RANGE = "max operating temperature range"
        self.S_MIN_OPR_TMP_RANGE = "min operating temperature range"
        self.S_MIN_WATER_PRESSURE = "min water pressure"
        self.S_MAX_WATER_PRESSURE = "max water pressure"
        self.S_WATER_PRESSURE = "water pressure"
        self.S_TEMP_RANGE = "temperature range"
        self.SPIN_SPEED = "spin speed"
        self.S_MAX_SPIN_SPEED = "max spin speed"
        self.S_MIN_SPIN_SPEED = "min spin speed"
        self.S_WASH_CAPACITY = "wash capacity"
        self.S_DIMENSION = "dimension"
        self._initialize_response_dict()

    def extract_value_and_unit(self, spec_key, response):
        """
        extract value from unit from the reponse from the db

        Args:
            spec_key: Identified specification key for the query
            response: Response from the DB
        Return:
              response dict framed
        """
        print("spec key convert : ", spec_key.lower())
        self.spec_key = spec_key
        # handle for the weight spec key
        if (self.S_WEIGHT in spec_key.lower()):
            return self._get_weight(response)
        elif (self.S_WIDTH in spec_key.lower()) or \
                (self.S_DEPTH in spec_key.lower()) or \
                (self.S_DEPTH_DOOR_OPEN in spec_key.lower()) or \
                (self.S_DEPTH_WITHOUT_DOOR_OPEN in spec_key.lower()) or \
                (self.S_HEIGHT in spec_key.lower()):
            return self._get_width_depth(response)
        elif (self.S_MAX_OPR_TMP_RANGE in spec_key.lower()) or \
                (self.S_MIN_OPR_TMP_RANGE in spec_key.lower()) or \
                (self.S_MIN_WATER_PRESSURE in spec_key.lower()) or \
                (self.S_MAX_WATER_PRESSURE in spec_key.lower()):
            return self._get_min_max_water_pressure_tmp_range(response)
        elif (self.S_WATER_PRESSURE in spec_key.lower()) or (self.S_TEMP_RANGE in spec_key.lower()):
            return self._get_water_pressure_tmp_range(response)
        elif (self.S_MAX_SPIN_SPEED in spec_key.lower()) or \
                (self.S_MIN_SPIN_SPEED in spec_key.lower()) or \
                (self.SPIN_SPEED in spec_key.lower()):
            return self._get_spin_speed(response)
        elif self.S_WASH_CAPACITY in spec_key.lower():
            return self._get_washer_capacity(response)
        elif self.S_DIMENSION in self.spec_key.lower():
            return self._get_properties_for_dimension(response)
        else:
            return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, None, 0)

    def _get_weight(self, response):
        """
        extract value and unit for the weight spec key

        Args:
            response: response from the db
        Return:
            Response dict
        """
        pattern_identified = re.findall(r"(?P<sub_value>\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs|lb|lbs)", response,
                                        re.IGNORECASE)

        if (pattern_identified is not None) and (len(pattern_identified) > 0):
            value, unit = pattern_identified[0]
            return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, unit, value)

        return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, None, 0)

    def _get_width_depth(self, response):
        """
        extract value and unit from the width,depth height

        Args:
            response: response from the db
        Return:
            Response dict
        """
        pattern_identified = re.findall(
            r"(?P<sub_value>\d+(?:\.\d+)?)\s*(?P<unit>centimeter|cm|mm|millimeter|inch|inches)", response,
            re.IGNORECASE)

        if (pattern_identified is not None) and (len(pattern_identified) > 0):
            value, unit = pattern_identified[0]
            return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, unit, value)

        return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, None, 0)

    def _get_water_pressure_tmp_range(self, response):
        """
        extract the value from the water pressure and temperature range

        Args:
            response: response from the db
        Return:
            response dict framed
        """
        pattern_identified = re.findall(r"(?P<sub_value_min>\d+(?:\.\d+)?)\s*(?P<unit_min>(?:psi|℉))?\s*(?:-|–)\s*"
                                        r"(?P<sub_value_max>\d+(?:\.\d+)?)\s*(?P<unit_max>(?:psi|℉))", response,
                                        re.IGNORECASE)
        if (pattern_identified is not None) and (len(pattern_identified) > 0):
            minvalue, _, maxvalue, unit = pattern_identified[0]
            return self._frame_response_dict(cs.UnitExtConstants.RANGE, self.spec_key, unit, minvalue, maxvalue)

        return self._frame_response_dict(cs.UnitExtConstants.RANGE, self.spec_key, None, 0)

    def _get_min_max_water_pressure_tmp_range(self, response):
        """
        extract value from the min and max of water pressure and temperatur range

        Args:
            response: response from the db
        Return:
            response dict framed
        """
        pattern_identified = re.findall(r"(?P<sub_value_max>\d+(?:\.\d+)?)\s*(?P<unit_max>(?:psi|℉))", response,
                                        re.IGNORECASE)
        if (pattern_identified is not None) and (len(pattern_identified) > 0):
            value, unit = pattern_identified[0]
            return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, unit, value)

        return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, None, 0)

    def _get_spin_speed(self, response):
        """
        extract value from the spin speed response

        Args:
            response: response from the db
        Return:
            response dict framed
        """
        pattern_identified = re.findall(
            r"(?P<sub_value_max>\d+(?:\.\d+)?)\s*"
            r"(?P<unit_max>(?:rotation per hour|rotation per minute|rotation per second|RPM|RPH|RPS))",
            response,
            re.IGNORECASE)
        if (pattern_identified is not None) and (len(pattern_identified) > 0):
            value, unit = pattern_identified[0]
            return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, unit, value)

        return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, None, 0)

    def _get_washer_capacity(self, response):
        """
        extract value from the spin speed response

        Args:
            response: response from the db
        Return:
            response dict framed
        """
        pattern_identified = re.findall(
            r"(?P<sub_value_max>\d+(?:\.\d+)?)\s*"
            r"(?P<unit_max>(?:cu.ft.))",
            response,
            re.IGNORECASE)
        if (pattern_identified is not None) and (len(pattern_identified) > 0):
            value, unit = pattern_identified[0]
            return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, unit, value)

        return self._frame_response_dict(cs.UnitExtConstants.SINGLE, self.spec_key, None, 0)

    def __normalize_subkey(self, unnormalized, mapping_table):
        for unnormalized_ref, normalized in mapping_table:
            if (re.match(unnormalized_ref, unnormalized, re.IGNORECASE)):
                return normalized
        return unnormalized

    # TODO need to complete the dimension extraction
    def _get_properties_for_dimension(self, response):
        generalize_unit = (
            ("cm|cms", "cm"),
            ("\"|''|”|inch|inches|in", "inch"),
        )
        generalize_dim = (
            ("w|width", "width"),
            ("h|height", "height"),
            (r"d(?:,|\s)+door\sopen", "depth_dooropen"),
            ("d|depth", "depth"),
        )

        end_unit_regex_obj = re.search(r"(\bin\b|cm|cms|\"|\'\'|\binches\b|\binch\b)$", response,
                                       flags=re.IGNORECASE)

        if end_unit_regex_obj is not None:
            values = re.findall(r"(?P<sub_value>\d+(?:(?:\.\d+)|\s*\d+/\d+))", response,
                                flags=re.IGNORECASE)
            c_values = []
            unit = self.__normalize_subkey(end_unit_regex_obj.group(), generalize_unit)
            for value in values:
                c_values.append(float(sum(Fraction(s) for s in value.split())))
            return self._frame_response_dict(cs.UnitExtConstants.DIMENSION, self.spec_key, unit, *c_values)
        else:

            c_values = []

            units = re.search(r'(\bin\b|\binch\b|inches|inch|\"|\'{2}|cm|cms)', response, flags=re.IGNORECASE)
            split_resultt = response.split(units.group())
            values = re.findall(r"(?P<sub_value>\d+(?:(?:\.\d+)|\s*\d+/\d+))", split_resultt[0],
                                flags=re.IGNORECASE)
            if len(values) == 3:
                for value in values:
                    c_values.append(float(sum(Fraction(s) for s in value.split())))
                final_resp = self._frame_response_dict(cs.UnitExtConstants.DIMENSION, self.spec_key, units.group(),
                                                       *c_values)
                return final_resp
            else:
                return self._custom_extract_dimension(response, generalize_unit)

    def _custom_extract_dimension(self, response):
        """
        extract the dimension value from the dimension string
        "27'' X 33 1/4'' X 39'' (70cm X 84 cm X 99 cm)"

        Args:
            response: response string
        Return:
            Extracted unit and values
        """
        c_values = []
        generalize_unit = (
            ("cm|cms", "cm"),
            ("\"|''|”|inch|inches|in", "inch"),
        )
        value_all = re.findall(r'(?P<sub_value>\d+(?:(?:\.\d+)?\s*|\s*\d+/\d+))(?P<unit>in|cm|cms|\"|\'\')\s*',
                               response, flags=re.IGNORECASE)
        unit = None
        max_idx = 2
        for id, value in enumerate(value_all):
            if id > max_idx:
                break
            c_values.append(float(sum(Fraction(s) for s in value[0].split())))
            unit = self.__normalize_subkey(value[1], generalize_unit)
        final_resp = self._frame_response_dict(cs.UnitExtConstants.DIMENSION, self.spec_key, unit, *c_values)
        logger.debug("w_dim : %s", final_resp)
        return final_resp

    def _initialize_response_dict(self):
        """
        initialize the response dict
        """
        self.response_dict[cs.UnitExtConstants.VALUE] = []
        self.response_dict[cs.UnitExtConstants.UNITS] = []
        self.response_dict[cs.UnitExtConstants.TYPE] = None
        self.response_dict[cs.UnitExtConstants.SPEC_KEY] = None

    def _frame_response_dict(self, type, spec_key, unit, *values):
        """
        frame the response dict from the converted value and unit

        Args:
            type: type whether it is range or single
            spec_key: spec_key identified from the query
            unit: unit identified
            values: values identified from the response

        Return:
            response dict framed
        """
        self.response_dict[cs.UnitExtConstants.VALUE] = []
        if unit is None:
            self.response_dict[cs.UnitExtConstants.STATUS] = cs.ResponseCode.DATA_NOT_FOUND
        else:
            self.response_dict[cs.UnitExtConstants.STATUS] = cs.ResponseCode.SUCCESS

        logger.debug("value : %s", values)
        logger.debug("unit : %s", unit)

        for value in values:
            self.response_dict[cs.UnitExtConstants.VALUE].append(float(value))
        self.response_dict[cs.UnitExtConstants.UNITS] = [unit]
        self.response_dict[cs.UnitExtConstants.TYPE] = type
        self.response_dict[cs.UnitExtConstants.SPEC_KEY] = spec_key
        logger.debug("resp : %s", self.response_dict)
        return self.response_dict


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    value_extract = ValueUnitExtract()
    print("Final response : ",
          value_extract.extract_value_and_unit("dimension", "27'' X 33 1/4'' X 39'' (70cm X 84 cm X 99 cm)"))
    print("Final response : ", value_extract.extract_value_and_unit("dimension", "29 7/8 x 17 13/18 x 15 13/16 inches"))
    print("Final response : ",
          value_extract.extract_value_and_unit("dimension", "23.9 x 13.5 x 19.8 inches (60.6 x 34.4 x 50.3 cm)"))
