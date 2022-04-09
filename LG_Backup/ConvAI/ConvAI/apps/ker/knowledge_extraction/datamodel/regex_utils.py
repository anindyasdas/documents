"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com
"""
import re
import logging as logger
from fractions import Fraction
import sys
import os

from constants import params as cs
import datamodel.dm_utils as utils


class RegExUtils(object):

    def __normalize_subkey(self, unnormalized, mapping_table):
        for unnormalized_ref, normalized in mapping_table:
            if (re.match(unnormalized_ref, unnormalized, re.IGNORECASE)):
                return normalized
        return unnormalized

    def get_range_relation_properties(self, key, value):
        """
           Get the range and relationship properties
           Args:
                key : string
                value : string
           Returns:
               tuple : range properties dictionary, relation properties
        """
        logger.info("Normalize input key(%s) value=(%s)" % (key, value))
        key_lower = key.lower()

        range_properties, relation_properties = None, None
        if any((keys in key_lower) for keys in ("dimension", "height", "width", "depth")):
            range_properties, relation_properties = self._get_properties_for_dimension(key, value)

        if "water pressure" in key.lower() or "temperature" in key.lower():
            range_properties, relation_properties = self._get_properties_for_water_pressure_temperature(value)

        if "weight" in key_lower:
            range_properties, relation_properties = self._get_properties_for_weight(value)

        if "capacity" in key_lower:
            range_properties, relation_properties = self._get_properties_for_capacity(key, value)

        if "spin speed" in key_lower:
            range_properties, relation_properties = self._get_properties_for_spin_speed(key_lower, value)

        if "gas requirements" in key_lower:
            range_properties, relation_properties = self._get_properties_for_gas_requirements(value)

        if "power consumption" in key_lower:
            range_properties, relation_properties = self._get_properties_for_power_consumption(value)

        if "battery run time" in key_lower:
            range_properties, relation_properties = self._get_properties_for_battery_runtime(key, value)

        # TODO Normalize/Convert/Check with the properties for the
        return range_properties, relation_properties

    def _get_properties_for_battery_runtime(self, key, value):
        """
        For getting the properties for battery runtime from keys and values

        Returns:
            object: Dictionary of properties
        """
        # Battery run time has only relation properties
        # no_of_batteries - key
        # usage - key
        # mode - value
        key_lower = key.strip().lower()
        battery_runtime_props = {}
        # Get the mode Turbo/Power/Normal
        value_list = re.split(r'(?:in?\s)?\*', value)
        battery_runtime_props['mode'] = value_list[1].lower()
        # Battery Run Time
        if "using two battery" in key_lower:
            battery_runtime_props['no_of_batteries'] = "two"
        elif "using one battery" in key_lower:
            battery_runtime_props['no_of_batteries'] = "one"
        # usage
        key_list = key.split("*")
        # Remove extra spaces if any
        usage = re.sub(' +', ' ', key_list[1].lower())
        # Code for matching the usage
        # with match to one of them
        # power drive nozzle
        # other than the power drive nozzle
        power_drive_nozzle = r"(?P<power_drive_nozzle>(:?using\s+)?with\s+the(?:\s+power\s+drive\s+)?\s*nozzle)"
        other_than_power_drive_nozzle = r"(?P<other_than_power_drive_nozzle>(?:using\s+)?(?:(?:(:?" \
                                        r"(?:nozzles\s+other\s+than\s+the\s+power drive)|(?:without the))" \
                                        r"(\s+nozzle))|(?:with\s+the\s+tool)))"
        usage_tags = re.match(fr"{power_drive_nozzle}?{other_than_power_drive_nozzle}?", usage, re.IGNORECASE)
        if usage_tags.group('power_drive_nozzle') is not None:
            usage = "power drive nozzle"
        elif usage_tags.group('other_than_power_drive_nozzle') is not None:
            usage = "other than the power drive nozzle"
        battery_runtime_props['usage'] = usage
        return None, battery_runtime_props

    def _get_properties_for_power_consumption(self, value):
        """
        For getting the properties for power consumption from values

        Returns:
            object: Dictionary of properties
        """
        generalize_unit = (
            ("W|watt", "Watts"),
        )
        all_tags = re.findall(
            r"(?P<sub_value_min>\d+(?:\.\d+)?)\s+(?P<unit>W)(?:\s\w*\s*\*)?"
            r"(?P<prop_key>(?:Turbo|Power|Normal))?\*?\s*\w*(?:\s\(Maximum|Max?)"
            r"?\s?(?P<sub_value_max>\d+(?:\.\d+)?)?",
            value,
            re.IGNORECASE)
        result = {}
        # Get the relation properties for gas_type
        power_consump_props = None
        for sub_value_min, unit, prop_key, sub_value_max in all_tags:
            for un_normalized, normalized in generalize_unit:
                if (re.match(un_normalized, unit, re.IGNORECASE)):
                    unit = normalized
                break
            result["min"] = (float(sub_value_min), unit)
            if sub_value_max.isdigit():
                result["max"] = (float(sub_value_max), unit)
            else:
                result["max"] = (float(0), unit)
            if prop_key:
                power_consump_props = {}
                power_consump_props['mode'] = prop_key.lower()
        return result, power_consump_props

    def _get_properties_for_gas_requirements(self, value):
        """
        For getting the properties for gas requirements from value

        Returns:
            object: Dictionary of properties
        """
        generalize_unit = (
            ("cm|cms", "cm"),
            ("\"|''|”|inch|in|inches", "inch"),
        )
        all_tags = re.findall(
            r"(?P<prop_key>\w+):\s+(?P<sub_value_min>\d+(?:\.\d+)?)\s*-?\s*\n?"
            r"(?P<sub_value_max>\d+(?:\.\d+)?)-(?P<unit>\w*)",
            value,
            re.IGNORECASE)
        result = {}
        # Get the relation properties for gas_type
        gas_relation_props = {}
        for prop_key, sub_value_min, sub_value_max, unit in all_tags:
            for un_normalized, normalized in generalize_unit:
                if (re.match(un_normalized, unit, re.IGNORECASE)):
                    unit = normalized
                break
            result["min"] = (float(sub_value_min), unit)
            result["max"] = (float(sub_value_max), unit)
            gas_relation_props['gas_type'] = prop_key
        return result, gas_relation_props

    def _get_properties_for_spin_speed(self, key_lower, value):
        """
        For getting the properties for spin speed from key and value

        Returns:
            object: Dictionary of properties
        """
        generalize_unit = (
            (r"rpm(?:\/min)?", "rpm"),
        )
        all_tags = re.findall(r"(?P<sub_value>(?:\d+|\d+(?:[,\d]+\d+)?)(?:\.\d+)?)\s*(?P<unit>rpm(?:\/min)?)\s*"
                              r"(?P<minmax>min|max)?", value, re.IGNORECASE)
        if ("max" in key_lower):  # Take first entry, if we already know it is Max. Example '950 RPM (±50 rpm)'
            all_tags = [(all_tags[0][0], all_tags[0][1], "max")]
        result = {}
        for sub_value, unit, minmax in all_tags:
            for un_normalized, normalized in generalize_unit:
                if (re.match(un_normalized, unit, re.IGNORECASE)):
                    unit = normalized
                    break
            result[minmax] = (int(sub_value.replace(",", "")), unit)
        # TODO Add relation properties if any
        relation_props = None
        return result, relation_props

    def _get_properties_for_capacity(self, key, value):
        """
        For getting the properties for capacity from key and value

        Returns:
            object: Dictionary of properties
        """
        generalize_unit = (
            (r"cu(?:\.|bic)ft(?:s)?", "cubicfeet"),
        )
        generalize_dim = (
            ("Washer", "washer"),
            ("Dryer", "dryer")
        )
        regex_value = r"(?P<sub_value>\d+(?:(?:\.\d+)?\s*|\s*\d+/\d+))"
        regex_unit = r"(?P<unit>cu(?:\.|bic)ft(?:s)?)"
        dim_combined = "(" + "|".join(d1 for d1, d2 in generalize_dim) + ")"
        # Find and process if dimension is present in key like 'Dimensions (Width X Height X Depth)'
        dim_in_keys = re.findall(
            fr"\((?:\s*{dim_combined}\s*/)(?:\s*{dim_combined}\s*)\)", key, re.IGNORECASE)
        if dim_in_keys:
            value_unit = fr"{regex_value}{regex_unit}"
            all_tags = re.findall(value_unit, value, re.IGNORECASE)
            all_tags = [(a, b, c) for (a, b), c in zip(all_tags, dim_in_keys[0])]
        else:
            value_unit_dim = fr"{dim_combined}?\s*{regex_value}\s*{regex_unit}"
            all_tags = re.findall(value_unit_dim, value, re.IGNORECASE)
        result = {}
        for sub_value, unit, dim in all_tags:
            unit = self.__normalize_subkey(unit, generalize_unit)
            dim = self.__normalize_subkey(dim, generalize_dim)
            # result[(dim, "", unit)] = float(sub_value)  # ToDo: be included in generic logic
            # https://stackoverflow.com/questions/1806278/convert-fraction-to-float
            result[dim] = (float(sum(Fraction(s) for s in sub_value.split())), unit)
        # TODO Add relation properties if any
        relation_props = None
        return result, relation_props

    def _get_properties_for_weight(self, value):
        """
        For getting the properties for weight from key and value

        Returns:
            object: Dictionary of properties
        """
        generalize_unit = (
            ("kg|kgs", "kg"),
        )
        all_tags = re.findall(r"(?P<sub_value>\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs)", value, re.IGNORECASE)
        result = {}
        for sub_value, unit in all_tags:
            for un_normalized, normalized in generalize_unit:
                if (re.match(un_normalized, unit, re.IGNORECASE)):
                    unit = normalized
                    break
            result["weight"] = (float(sub_value), unit)
        # TODO Add relation properties if any
        relation_props = None
        return result, relation_props

    def _get_properties_for_water_pressure_temperature(self, value):
        """
        For getting the properties for water pressure and temperature from key and value

        Returns:
            object: Dictionary of properties
        """
        generalize_unit = ()
        all_tags = re.findall(r"(?P<sub_value_min>\d+(?:\.\d+)?)\s*(?P<unit_min>(?:psi|℉))?\s*(?:-|\(.*\s)\s*"
                              r"(?P<sub_value_max>\d+(?:\.\d+)?)\s*(?P<unit_max>(?:psi|℉))", value, re.IGNORECASE)
        result = {}
        for sub_value_min, _, sub_value_max, unit_max in all_tags:
            for un_normalized, normalized in generalize_unit:
                if (re.match(un_normalized, unit_max, re.IGNORECASE)):
                    unit_max = normalized
                    break
            result["min"] = (float(sub_value_min), unit_max)
            result["max"] = (float(sub_value_max), unit_max)
        # TODO Add relation properties if any
        relation_props = None
        return result, relation_props

    def _get_properties_for_dimension(self, key, value):
        """
        For getting the properties for dimensions from key and value

        Returns:
            object: Dictionary of properties
        """
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
        result = {}
        regex_value = r"(?P<sub_value>(?:\d+[\/\d. ]*|\d))"
        regex_unit = r"(?P<unit>in|cm|cms|\"|'')?"
        # r"\((?P<dim>w|width|h|height|d|d[,\w\s]+)\)"
        dim_combined = "(" + "|".join(d1 for d1, d2 in generalize_dim) + ")"
        # Find and process if dimension is present in key like 'Dimensions (Width X Height X Depth)'
        dim_in_keys = re.findall(
            fr"\((?:\s*{dim_combined}\s*X)(?:\s*{dim_combined}\s*X)*(?:\s*{dim_combined}\s*)\)", key, re.IGNORECASE)
        if dim_in_keys:
            value_unit = fr"{regex_value}{regex_unit}"
            all_tags = re.findall(value_unit, value, re.IGNORECASE)
            # Adding the inches or cm if the unit is missing in the first two
            # Ex: 23.9 x 13.5 x 19.8 inches
            # TODO Implement more efficient way for handling units at last
            if not all_tags[0][1]:
                lst_temp = list(all_tags[0])
                lst_temp[1] = all_tags[2][1]
                all_tags[0] = lst_temp
            if not all_tags[1][1]:
                lst_temp = list(all_tags[1])
                lst_temp[1] = all_tags[2][1]
                all_tags[1] = lst_temp
            all_tags = [(a, b, c) for (a, b), c in zip(all_tags, dim_in_keys[0])]
        else:
            value_unit_dim = fr"{regex_value}{regex_unit}\s*\({dim_combined}\)"
            all_tags = re.findall(value_unit_dim, value, re.IGNORECASE)
        for sub_value, unit, dim in all_tags:
            unit = self.__normalize_subkey(unit, generalize_unit)
            dim = self.__normalize_subkey(dim, generalize_dim)
            # result[(dim, "", unit)] = float(sub_value)  # ToDo: be included in generic logic
            # https://stackoverflow.com/questions/1806278/convert-fraction-to-float
            result[dim] = (float(sum(Fraction(s) for s in sub_value.split())), unit)
        # TODO Add relation properties if any
        relation_props = None
        return result, relation_props

    def normalize_range_dictionary(self, norm_value, range_type):
        """
        check schema props and make properties dictionary for domain and range

        Args:
            norm_value : dict
            range_type : str
        Returns:
               prop_dict : dictionary object
        """
        prop_dict = None
        logger.info("Normalize output value=(%s)" % str(norm_value))
        if (range_type.lower() in cs.DIMENSION.lower() or
                range_type.lower() in cs.RANGE.lower() or
                range_type.lower() in cs.CAPACITY.lower() or
                range_type.lower() in cs.NET_WEIGHT.lower()):
            prop_dict = dict()
            props_list = utils.SCHEMA_OBJ.get_schema_for_key(range_type)[cs.PROP]
            logger.info("Props list=(%s)", str(props_list))
            for eachprop in props_list:
                key = str(eachprop[cs.VALUE])
                if key in norm_value:
                    prop_dict[key] = norm_value[key][0]
                    prop_dict[cs.UNIT] = norm_value[key][1]
                else:
                    logger.info("key not exists")
        logger.info("prop_dict=(%s)" % str(prop_dict))
        return prop_dict


if __name__ == "__main__":
    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    obj = RegExUtils()
    # Test Cases for Dimensions
    assert obj.get_range_relation_properties(' Dimensions (Width X Depth X Height)', "10.2 in X 10.6 in X 44.1 in") == (
        {'width': (10.2, 'inch'), 'depth': (10.6, 'inch'), 'height': (44.1, 'inch')}, None)

    assert obj.get_range_relation_properties('Dimensions(cm)', '68.6 cm(W) x 75.6 cm(D) x 98.3 cm(H)') == (
        {'width': (68.6, 'cm'), 'depth': (75.6, 'cm'), 'height': (98.3, 'cm')}, None)

    assert obj.get_range_relation_properties('Dimensions', '27"(W) x 29.0"(D) x 38 11/16"(H) / 52" (D, door open)') == (
        {
            'width': (27.0, 'inch'), 'depth': (29.0, 'inch'), 'height': (38.6875, 'inch'),
            'depth_dooropen': (52.0, 'inch')}, None)
    assert obj.get_range_relation_properties('Dimensions (Width X Height X Depth)', """27'' X 33 1/4'' X 39'' (70
        cm X 84 cm X 99 cm)""") == ({'width': (27.0, 'inch'), 'height': (33.25, 'inch'), 'depth': (39.0, 'inch')}, None)

    # Test cases for Dimensions in Oven manuals
    assert obj.get_range_relation_properties('Dimensions (W x H x D)',
                                             "23.9 x 13.5 x 19.8 inches (60.6 x 34.4 x 50.3 cm)") == (
               {'width': (23.9, 'inch'), 'height': (13.5, 'inch'), 'depth': (19.8, 'inch')}, None)
    assert obj.get_range_relation_properties('Oven Cavity Dimensions (W x H x D)',
                                             "16.7 x 11.3 x 18.0 inches (42.4 x 28.6 x 45.9 cm)") == (
               {'width': (16.7, 'inch'), 'height': (11.3, 'inch'), 'depth': (18.0, 'inch')}, None)
    assert obj.get_range_relation_properties('Dimensions (W x H x D)',
                                             "29 15/16 x 16 7/16 x 16 15/16 inches") == (
               {'width': (29.9375, 'inch'), 'height': (16.4375, 'inch'), 'depth': (16.9375, 'inch')}, None)
    assert obj.get_range_relation_properties('Dimensions (W x H x D)',
                                             "29 15/16 x 16 7/16 x 16 15/16 inches") == (
               {'width': (29.9375, 'inch'), 'height': (16.4375, 'inch'), 'depth': (16.9375, 'inch')}, None)

    # TODO Regex not working check & Data modelling
    # print(obj.get_range_relation_properties("Maximum Depth with Door Open", "55'' (139.6 cm)"))
    # print(obj.get_range_relation_properties("Maximum Height Lid Open", "57 1/4” (145.3 cm)"))

    # Test Cases for Temperature Range
    assert obj.get_range_relation_properties('Operating Temperature Range', "41-95 ℉ (5-35 ℃)") == ({'min': (41.0, '℉'),
                                                                                                     'max': (
                                                                                                         95.0, '℉')},
                                                                                                    None)
    # Test Case for dishwasher (Inlet Water Temperature)
    assert obj.get_range_relation_properties('Inlet Water Temperature',
                                             "120 ℉ (49 ℃) minimum, 149 ℉ (65 ℃) maximum") == (
               {'min': (120.0, '℉'), 'max': (149.0, '℉')}, None)

    # Test Cases for Water Pressure
    assert obj.get_range_relation_properties('Min. / Max. Water Pressure', "20 - 120 psi (138 - 827 kPa)") == (
        {'min': (20.0, 'psi'), 'max': (120.0, 'psi')}, None)

    # Test Cases for Spin Speed
    assert obj.get_range_relation_properties('spin speed', "1,400 rpm/min max") == ({'max': (1400, 'rpm')}, None)
    assert obj.get_range_relation_properties('max. spin speed', '950 RPM (±50 rpm)') == ({'max': (950, 'rpm')}, None)

    # Test Cases for Capacity
    assert obj.get_range_relation_properties('Capacity (Washer/Dryer)', '4.5 cu.ft. / 7.4 cu.ft.') == (
        {'washer': (4.5, 'cubicfeet'), 'dryer': (7.4, 'cubicfeet')}, None)

    # Test Cases for Gas Requirements
    assert obj.get_range_relation_properties('Gas Requirements', 'NG: 4 - \n10.5-inch (10.2 - 26.7 cm) WC') == (
        {'min': (4.0, 'inch'), 'max': (10.5, 'inch')}, {'gas_type': 'NG'})
    assert obj.get_range_relation_properties('Gas Requirements', 'LP: 8 - 13-inch (20.4 - 33.1 cm) WC') == (
        {'min': (8.0, 'inch'), 'max': (13.0, 'inch')}, {'gas_type': 'LP'})

    # Test Cases for Power Consumption
    assert obj.get_range_relation_properties('Power Consumption', '120 W in *Power* Mode') == (
        {'min': (120.0, 'Watts'), 'max': (0.0, 'Watts')}, {'mode': 'power'})
    assert obj.get_range_relation_properties('Power Consumption', '68 W in *Normal* Mode') == (
        {'min': (68.0, 'Watts'), 'max': (0.0, 'Watts')}, {'mode': 'normal'})
    assert obj.get_range_relation_properties('Power Consumption', '370 W in *Turbo* Mode (Maximum 590 W)') == (
        {'min': (370.0, 'Watts'), 'max': (590.0, 'Watts')}, {'mode': 'turbo'})
    assert obj.get_range_relation_properties('Rated Power Consumption', '1600 W (Microwave oven with '
                                                                        'cooktop lamp and ventilation fan)') == (
               {'min': (1600.0, 'Watts'), 'max': (0.0, 'Watts')}, None)

    # Test Cases for Battery Run Time
    assert obj.get_range_relation_properties('Battery Run Time (Using two battery)*Using with the  Power Drive Nozzle',
                                             'Up to 12  minutes in *Turbo* Mode') == (
               None, {'mode': 'turbo', 'no_of_batteries': 'two', 'usage': 'power drive nozzle'})
    assert obj.get_range_relation_properties(' Battery Run Time (Using one battery)*Using with the Nozzle',
                                             'Up to 40 minutes in *Normal* Mode') == (
               None, {'mode': 'normal', 'no_of_batteries': 'one', 'usage': 'power drive nozzle'})
    assert obj.get_range_relation_properties(' Battery Run Time (Using two battery)*Using with the Tool',
                                             'Up to 60  minutes in *Power* Mode') == (
               None, {'mode': 'power', 'no_of_batteries': 'two', 'usage': 'other than the power drive nozzle'})
    assert obj.get_range_relation_properties('Battery Run Time (Using one battery)*Using Nozzles  other than the '
                                             'Power Drive Nozzle',
                                             'Up to 60 minutes in *Normal* Mode') == (
               None, {'mode': 'normal', 'no_of_batteries': 'one', 'usage': 'other than the power drive nozzle'})

    assert obj.get_range_relation_properties('Battery Run Time*with the Nozzle',
                                             'Up to 6 minutes in *Turbo* Mode') == (
               None, {'mode': 'turbo', 'usage': 'power drive nozzle'})
    assert obj.get_range_relation_properties('Battery Run Time*without the Nozzle',
                                             'Up to 9 minutes in *Power* Mode') == (
               None, {'mode': 'power', 'usage': 'other than the power drive nozzle'})