# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""
import json
import os
from configparser import ConfigParser
import logging as logger

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, '..', 'config', 'configuration.ini')


class NewUnitConverter(object):
    """
      class is used to convert value from one unit
      to another
    """

    def __init__(self):
        self.formula_table = {}
        self.VALUE_KEY = 'value'
        self.OPR_KEY = 'operation'
        self.DIV_OPR = 'divide'
        self.MUL_OPR = 'multiply'
        self.SUB_OPR = 'subtract'
        self.ADD_OPR = 'add'
        self.REF_KEY = 'reference'
        self.INV_OP = 'invert_op'
        self.FOR_KEY = 'formula'
        self.unit_references = {}
        self.invert_op = {}
        self.formula = {}
        self.main_units = {}
        self.sub_units = {}
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        self.formula_fp = os.path.join(current_path, '..',
                                       config_parser.get("new_formula",
                                                         "new_formula_json"))
        self.load_formula_table()
        self._get_formula_unit_ref()

    def load_formula_table(self):
        """
        Load the formula from json file

        """
        with open(self.formula_fp, 'r') as pf:
            self.formula_table = json.load(pf)
            logger.debug('formula loaded : %s', self.formula_table)

    def _get_formula_unit_ref(self):
        self.unit_references = self.formula_table[self.REF_KEY]
        self.invert_op = self.formula_table[self.INV_OP]
        self.formula = self.formula_table[self.FOR_KEY]
        self.main_units = self.unit_references.values()
        self.sub_units = self.unit_references.keys()

    def convert_value(self, actual_value, from_unit, to_unit):
        """
        Used to convert the value from from unit to required unit

        Args:
        actual_value : int or float
            value to convert
        from_unit : string
            from unit string
        to_unit : Stirng
            to unit in string

        Returns:
        int or float
            converted value.

        """

        if from_unit == to_unit:
            return actual_value

        if from_unit in self.main_units:
            values = self.formula[from_unit][to_unit][self.VALUE_KEY]
            opr = self.formula[from_unit][to_unit][self.OPR_KEY]
            return self._do_calc(values, opr, actual_value)
        else:
            s_unit = self.unit_references[from_unit]
            values = self.formula[s_unit][from_unit][self.VALUE_KEY]
            opr = self.formula[s_unit][from_unit][self.OPR_KEY]
            int_value = self._do_calc(values, opr, actual_value, True)

            logger.debug('int_unit: %s, s_unit :%s',int_value, s_unit)

            if s_unit != to_unit:
                values = self.formula[s_unit][to_unit][self.VALUE_KEY]
                opr = self.formula[s_unit][to_unit][self.OPR_KEY]
                final_value = self._do_calc(values, opr, int_value)
                logger.debug('final_value: %s, to_unit :%s', final_value, to_unit)
                return final_value
            else:
                return int_value

    def _do_calc(self, con_value, con_opr, actual_value, inv_flag=False):

        if inv_flag:
            step = -1
        else:
            step = 1

        for value, opr in zip(con_value[::step], con_opr[::step]):

            if inv_flag:
                opr = self.invert_op[opr]

            if (opr == self.DIV_OPR):
                actual_value = actual_value / value
            elif (opr == self.MUL_OPR):
                actual_value = actual_value * value
            elif (opr == self.SUB_OPR):
                actual_value = actual_value - value
            elif (opr == self.ADD_OPR):
                actual_value = actual_value + value
        return actual_value

if __name__ == "__main__":
    # logger configuration
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    unit_con = NewUnitConverter()
    print(unit_con.convert_value(20, 'celsius', 'fahrenheit'))