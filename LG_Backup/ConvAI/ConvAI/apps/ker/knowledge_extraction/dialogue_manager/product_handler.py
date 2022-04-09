# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk
"""
import os
import sys
import json
import logging as logger
from configparser import ConfigParser

from .product_classifier import ProductClassifier
from .preference import Preference
from ..constants import params as p
from .context_manager import ContextManager

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, '..', 'config', 'configuration.ini')


class ProductHandler(object):

    def __init__(self):
        self.product_db = {}
        self.product_key = 'Products'
        self.model_key = 'model'
        self.context_manager = ContextManager()
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        self.product_db_file = os.path.join(current_path, '..',
                                            config_parser.get("product_pref",
                                                              "product_pref_json"))
        self.classifier = ProductClassifier()
        self._load_prd_db()

    def _write_to_json(self, data):
        """
           write to the json file
           Args:
               data:
                    type:dict
                    desc:json data from html
        """
        with open(self.product_db_file, 'w') as pf:
            json.dump(self.product_db, pf)

    def _remove_prd_from_db(self, value, keys):# pragma: no cover
        """
        Remove the product from product db if no model numbers is allocated
        for specific product name

        Args:
             value: model no
             keys: list of products from product DB
        """
        for key in keys:
            values = self.product_db[key]
            if (values is not None) and (value is not None) and (value in values):
                self.product_db[key] = values.remove(value)
                if len(values) == 0:
                    self.product_db.pop(key)
                    break

    def _remove_value_frm_key(self, value):# pragma: no cover
        """
            Remove the value from existing preference data
            Args:
                value: value to be removed from pref
        """
        if self.product_db is not None:
            keys = self.product_db.keys()
            if keys is not None:
                self._remove_prd_from_db(value, keys)

    def update_db_data(self, update_json):# pragma: no cover
        """
            update the product_db.json with product and corresponding
            model no
            Args:
               update_json:
                           type: dict
                           desc: json from html
            Return:
               return SUCCESS
        """
        product_list = update_json[self.product_key]
        model_list = update_json[self.model_key]
        logger.debug('product : (%s) model: (%s)', product_list, model_list)
        logger.debug('zipped : (%s)', tuple(zip(product_list, model_list)))
        for product, model in zip(product_list, model_list):
            self._remove_value_frm_key(model)
            logger.debug('removed_product_db : %s : %s', product, self.product_db)
            self.product_db[product.lower()] = [model]

        logger.debug('before updated_db : (%s)', self.product_db)
        self._write_to_json(self.product_db)
        self._load_prd_db()
        logger.debug('updated_db : (%s)', self.product_db)
        return p.SUCCESS

    def _load_prd_db(self):# pragma: no cover
        """
           load product details of user from json
        """
        with open(self.product_db_file, 'r') as pf:
            if os.stat(self.product_db_file).st_size > 0:
                self.product_db = json.load(pf)

    def get_prd_db(self):# pragma: no cover
        """
        get the updated product db
        """
        self._load_prd_db()
        return self.product_db

    def delete_product_db(self):# pragma: no cover
        """
        delete the product db json
        Returns:
            updated product db
        """
        self.product_db.clear()
        self._write_to_json(self.product_db)
        logger.debug("deleted product db : %s", self.product_db)
        return self.get_prd_db()

    def _get_class_from_classifier(self, user_query):
        """
           Get the class of product class from query

           Args:
               user_query - Query from user
           return:
                 type:string
                 Desc: product class of query
        """
        return self.classifier.find_class_frm_query(user_query)

    def _get_product_from_db(self, model_no):
        """
           Get product based on model no

           Args:
               model_no:
                      Type:string
                      Desc:model no extracted
           return:
                  Type:string
                  Desc:product type
        """
        products = self.product_db.keys()

        for product in products:
            model_no_list = self.product_db[product]

            if (model_no_list is not None) and (len(model_no_list) > 0):
                for model_no_db in model_no_list:
                    if model_no.lower() == model_no_db.lower():
                        return product
            else:
                continue

        return None

    def _get_product_model_from_db(self, prd_type):
        """
           Get product based on model no

           Args:
               prd_type:
                      Type:string
                      Desc:product type extracted
           return:
                  Type:string
                  Desc:product type
        """
        if prd_type in self.product_db:
            model_no_list = self.product_db[prd_type]
            if (model_no_list is not None) and (len(model_no_list) > 0):
                return model_no_list[0]
            else:
                return None
        else:
            return None

    def handle_product_context(self, query, model_no):
        """
           Handling the context based on product from query or
           take based on model no

           Args:
               query:
                     Type: string
                     Desc: query from user
               model_no:
                       Type:string
                       Desc:model no extracted by model no extractor
           return:
                   Type:string
                   Desc:product type
        """
        cur_prodcut, sub_product = self._get_class_from_classifier(query)
        logger.debug("product : (%s),(%s),(%s),(%s)", query, model_no, cur_prodcut, sub_product)
        # query doesn't contain product type
        if (cur_prodcut is None) and (model_no is not None):  #
            # get product type based on model no from query
            prd_db = self._get_product_from_db(model_no)
            logger.debug("prd frm DB : %s",prd_db)
            if prd_db is None:
                return None, None, model_no, p.DATA_NOT_FOUND
            cur_prodcut, sub_product = self._get_class_from_classifier(prd_db)
            logger.debug("based on db : %s - %s",cur_prodcut, sub_product)
            if (cur_prodcut is not None) and (len(cur_prodcut.strip()) > 0):
                self.context_manager.update_product_context(cur_prodcut, sub_product)
                return cur_prodcut, sub_product, model_no, p.SUCCESS
            return None, None, model_no, p.DATA_NOT_FOUND
        elif (cur_prodcut is None) and (model_no is None):
            cur_prodcut = Preference.get_pre_prd()  # get product type from preference
            if (cur_prodcut is not None) and (len(cur_prodcut) > 0) and \
                    (sub_product is None):
                model_no = Preference.get_model_pref_value(cur_prodcut)
                sub_product = Preference.get_product_pref_value(cur_prodcut)
                return cur_prodcut, sub_product, model_no, p.SUCCESS
            elif (cur_prodcut is not None) and (len(cur_prodcut) > 0) and \
                    (sub_product is not None) and (len(sub_product) > 0):
                self.context_manager.update_product_context(cur_prodcut, sub_product)
                model_no = self._get_product_model_from_db(sub_product)
                return cur_prodcut, sub_product, model_no, p.SUCCESS
            return None, None, None, p.DATA_NOT_FOUND
        elif (cur_prodcut is not None):
            return self._handle_valid_prd(cur_prodcut, sub_product, model_no)

    def _handle_valid_prd(self, cur_prodcut, sub_product, model_no):
        mproduct, sprd = self.context_manager.update_product_context(cur_prodcut, sub_product)
        logger.debug("model frm db : %s sprd=%s",model_no, sprd)
        if (model_no is not None) and (len(model_no.strip()) > 0):
            local_model_no = model_no
        else:
            local_model_no = self._get_product_model_from_db(sprd)
        return mproduct, sprd, local_model_no, p.SUCCESS


if __name__ == '__main__':
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    Preference.intialize_preference()
    product_handler = ProductHandler()

    product_handler.delete_product_db()

    temp = {"Products": ["hall refrigerator"],
            "model": ["LRFDS3007*"]}
    product_handler.update_db_data(temp)
    print(product_handler.get_prd_db())

    print(product_handler.delete_product_db())

    temp = {"Products": ["dinning refrigerator"],
            "model": ["LRFDS3007*"]}
    product_handler.update_db_data(temp)
    print(product_handler.get_prd_db())

    while (True):
        print("Enter Query : ")
        query = input()
        # model no is hot coded since it will be extracted from user query
        print(product_handler.handle_product_context(query, 'LRFDS3007*'))
