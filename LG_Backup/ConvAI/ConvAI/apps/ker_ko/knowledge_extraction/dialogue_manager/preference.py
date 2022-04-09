# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk
"""

import json
import os
import logging as logger
from configparser import ConfigParser

from ..constants import params as cs

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, '..', 'config', 'configuration.ini')


class Preference(object):
    pref = {}

    MODEL_PREF_KEY = 'model'
    PARTNO_PREF_KEY = 'part_no'
    PRODUCT_PREF_KEY = 'product'
    UNIT_PREF_KEY = 'unit'
    SPEC_PREF_KEY = 'spec_key'
    PRE_PPRODUCT_KEY = 'pre_product'
    config_parser = ConfigParser()
    config_parser.read(CONFIG_PATH)
    PREF_JSON_FP = os.path.join(current_path, '..',
                                config_parser.get("preference",
                                                  "preference_json"))
    logger.debug('pref path : %s',PREF_JSON_FP)

    def __init__(self):
        pass

    @staticmethod
    def intialize_preference():
        """
        Function to initialize the preferences to JSON file
        """
        with open(Preference.PREF_JSON_FP, 'r', encoding='utf-8') as pf:
            Preference.pref = json.load(pf)

    @staticmethod
    def write_to_json():
        """
        Function to write the preferences to JSON file
        """
        with open(Preference.PREF_JSON_FP, 'w') as pf:
            logger.debug('write_to_pref :%s', Preference.pref)
            json.dump(Preference.pref, pf)

    @staticmethod
    def get_preference():
        """
        get the latest preference

        Return:
            Preference dict
        """
        return Preference.pref

    @staticmethod
    def reset_preference():
        """
           reset the preference
        """
        Preference.pref[Preference.PRE_PPRODUCT_KEY] = ''
        keys = Preference.pref.keys()

        for key in keys:
            if key == Preference.PRE_PPRODUCT_KEY:
                continue
            Preference.pref[key][Preference.PARTNO_PREF_KEY] = ''
            Preference.pref[key][Preference.PRODUCT_PREF_KEY] = ''
            Preference.pref[key][Preference.UNIT_PREF_KEY] = ''
            Preference.pref[key][Preference.SPEC_PREF_KEY] = ''
        Preference.write_to_json()
        return cs.SUCCESS

    @staticmethod
    def update_pre_prd(prd_type):
        """
        Update the previous product type in the pref.json
        Args:
            prd_type: The type of product (Washing machine, Refrigerator etc.,)
        """
        Preference.pref[Preference.PRE_PPRODUCT_KEY] = prd_type
        Preference.write_to_json()

    @staticmethod
    def get_pre_prd():
        """
        Gives the previously stored product information
        Returns:
            previous product information
        """
        return Preference.pref[Preference.PRE_PPRODUCT_KEY]

    @staticmethod
    def update_partno_pref(part_no, prd_type):
        """
           update model no to preference

        Args:
            part_no : String
                part no.
            prd_type: the type of product
        Returns
            None.
        """
        Preference.pref[prd_type][Preference.PARTNO_PREF_KEY] = part_no
        Preference.write_to_json()

    @staticmethod
    def update_model_pref(model, prd_type):
        """
           update model no to preference

        Args:
            model : String
                Model no.
            prd_type: the type of product
        Returns
            None.
        """
        Preference.pref[prd_type][Preference.MODEL_PREF_KEY] = model
        Preference.write_to_json()

    @staticmethod
    def get_partno_pref_value(prd_type):
        """
           get model from preferences based on the product type
        Args:
            prd_type : the type of product
        Returns
        String - model no.
        """
        return Preference.pref[prd_type][Preference.PARTNO_PREF_KEY]

    @staticmethod
    def get_model_pref_value(prd_type):
        """
           get model from preferences based on the product type
        Args:
            prd_type : the type of product
        Returns
        String - model no.
        """
        return Preference.pref[prd_type][Preference.MODEL_PREF_KEY]

    @staticmethod
    def update_product_pref(product, prd_type):
        """
           update product name to preference

        Args:
        product : String
            product name.
        prd_type: the type of product

        Returns
        None.
        """
        Preference.pref[prd_type][Preference.PRODUCT_PREF_KEY] = product
        Preference.write_to_json()

    @staticmethod
    def get_product_pref_value(prd_type):
        """
          get product from user query based on the product type
        Args:
        prd_type: the type of product
        Returns
        -------
        String
            Product.

        """
        return Preference.pref[prd_type][Preference.PRODUCT_PREF_KEY]

    @staticmethod
    def update_unit_pref(unit, prd_type):
        """
          Update unit to preference

        Parameters
        ----------
        unit : String
            unit.
        prd_type: the type of product

        Returns
        -------
        None.

        """
        Preference.pref[prd_type][Preference.UNIT_PREF_KEY] = unit
        Preference.write_to_json()

    @staticmethod
    def get_unit_pref_value(prd_type):
        """
           get unit from preference
        Args:
        prd_type: the type of product
        Returns:
        -------
        String
            unit from preferences.

        """
        return Preference.pref[prd_type][Preference.UNIT_PREF_KEY]

    @staticmethod
    def update_spec_key_pref(unit, prd_type):
        """
           Update spec key to preference

        Parameters
        ----------
        unit : String
            spec key.
        prd_type:
            the type of product
        Returns
        -------
        None.

        """
        Preference.pref[prd_type][Preference.SPEC_PREF_KEY] = unit
        Preference.write_to_json()

    @staticmethod
    def get_spec_key_pref_value(prd_type):
        """
          Get spec key from preference
        Parameters
        ----------
        prd_type:
            the type of product
        Returns
        -------
        String
            Speck key.

        """
        return Preference.pref[prd_type][Preference.SPEC_PREF_KEY]


if __name__ == "__main__":
    Preference.intialize_preference()
    Preference.update_model_pref('WD345', "washing machine")
