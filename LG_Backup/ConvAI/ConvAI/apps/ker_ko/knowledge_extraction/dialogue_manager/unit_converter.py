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


class UnitConverter(object):
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
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        self.formula_fp = os.path.join(current_path, '..',
                                       config_parser.get("formula_table",
                                                         "formula_table_json"))
        self.load_formula_table()

    def load_formula_table(self):
        """
        Load the formula from json file

        """
        with open(self.formula_fp, 'r') as pf:
            self.formula_table = json.load(pf)
            logger.debug('formula loaded : %s', self.formula_table)

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
        conversion_det = self.formula_table[from_unit][to_unit]
        con_value = conversion_det[self.VALUE_KEY]
        con_opr = conversion_det[self.OPR_KEY]

        logger.debug("con_value : %s %s", con_value, con_opr)

        for value, opr in zip(con_value, con_opr):
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

    unit_con = UnitConverter()
    print(unit_con.convert_value(20, 'fahrenheit', 'celsius'))
