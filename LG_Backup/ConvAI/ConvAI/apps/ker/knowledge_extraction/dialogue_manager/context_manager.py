import logging as logger
from .preference import Preference

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

class ContextManager(object):

    def __init__(self):
        self.prod_spec_key = 'Product type'

    def get_modelno_context(self):
        """
        get the model no from current context

        return:
            model no
        """
        pref_product = Preference.get_pre_prd()

        if (pref_product is not None) and (len(pref_product.strip()) > 0):
            pref_spec_key = Preference.get_model_pref_value(pref_product)
            return pref_spec_key
        else:
            return None

    def update_modelno_context(self, lmodel_no, prd_type=None):
        """
        check the model no context with preference

        Return:
            Truncated and actual model no
        """

        if prd_type is None:
            prd_type = Preference.get_pre_prd()

        logger.debug("updating the model context : %s prd_type: %s", lmodel_no, prd_type)
        if lmodel_no is not None:
            pref_model_no = Preference.get_model_pref_value(prd_type)
            if lmodel_no != pref_model_no:
                Preference.update_model_pref(lmodel_no, prd_type)
                pref_model_no = Preference.get_model_pref_value(prd_type)
                return pref_model_no
            else:
                return pref_model_no
        # else:
        #     raise Exception("Model no is none")

    def get_spec_key_context(self):
        """
        get the current spec key context

        return:
            get the current spec key
        """
        pref_product = Preference.get_pre_prd()

        if (pref_product is not None) and (len(pref_product.strip()) > 0):
            pref_spec_key = Preference.get_spec_key_pref_value(pref_product)
            return pref_spec_key
        else:
            return None

    def update_spec_key_context(self, spec_key, prd_type):
        """
        check speckey context from user query speckey

        Parameters
        ----------
        spec_key : String
            speckey classified from user query.

        Returns
        -------
        String
            Speck key.

        """
        logger.debug('spec_key prd_type : spec: %s, prd_type : %s', spec_key, prd_type)
        pref_spec_key = Preference.get_spec_key_pref_value(prd_type)

        if spec_key == self.prod_spec_key:
            return pref_spec_key

        if spec_key is not None:
            if ((len(spec_key.strip()) > 0) and
                    (spec_key != pref_spec_key)):
                Preference.update_spec_key_pref(spec_key, prd_type)
                return spec_key.strip()
            else:
                return Preference.get_spec_key_pref_value(prd_type)
        # else:
        #     raise Exception("Spec key is none")

    def get_product_context(self):
        """
        get the product context

        return:
            product context
        """
        pref_product = Preference.get_pre_prd()

        if (pref_product is not None) and (len(pref_product.strip()) > 0):
            prd = Preference.get_product_pref_value(pref_product)
            return prd
        else:
            return None

    def update_product_context(self, main_product, sub_prd):
        """
           check the product context based on preferences

           Args:
               main_product:
                          Type:string
                          Desc:current product
           return:
                  Type:string
                  Desc:product type
        """
        pref_product = Preference.get_pre_prd()
        logger.debug("updating the product context main: %s sub_prd: %s pref_prd:%s", main_product, sub_prd, pref_product)
        if main_product is not None:
            if pref_product != main_product:
                logger.debug("updating main prd : %s",main_product)
                Preference.update_pre_prd(main_product)
            lsub_prd = Preference.get_product_pref_value(main_product)
            if sub_prd is not None:
                if lsub_prd != sub_prd:
                    Preference.update_product_pref(sub_prd, main_product)
                logger.debug("pref_prd :%s %s", main_product, sub_prd)
                return main_product, sub_prd
            else:
                pref_product = Preference.get_pre_prd()
                if len(lsub_prd.strip()) == 0:
                    Preference.update_product_pref(pref_product, pref_product)
                lsub_prd = Preference.get_product_pref_value(pref_product)
                return pref_product, lsub_prd

    def update_unit_context(self, unit):
        """
           Check the unit context with preference

        Parameters
        ----------
        unit : String
            Unit retrieved.

        Returns
        -------
        Updated unit
        """

        logger.debug("update unit context: %s", unit)
        if (unit is not None) and (len(unit) > 0):
            prev_prod = Preference.get_pre_prd()
            pref_unit = Preference.get_unit_pref_value(prev_prod)
            if unit != pref_unit:
                Preference.update_unit_pref(unit, prev_prod)
            return unit

    def get_unit_context(self):
        """
        get the unit context

        return:
            unit from context
        """
        prev_prod = Preference.get_pre_prd()

        if (prev_prod is not None) and (len(prev_prod.strip()) > 0):
            pref_unit = Preference.get_unit_pref_value(prev_prod)
            return pref_unit
        else:
            return None

    def clear_context(self):
        """
        clear the preference
        """
        Preference.reset_preference()

    def get_context(self):
        """
        get the current context
        """
        return Preference.get_preference()
