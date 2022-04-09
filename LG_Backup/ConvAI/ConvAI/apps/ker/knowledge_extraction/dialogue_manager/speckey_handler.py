# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""

from .preference import Preference


class SpecKeyHandler(object):
    """
       class used to mantain context based on speckey
    """

    def __init__(self):
        self.prod_spec_key = 'Product type'

    def check_spec_key_context(self, spec_key, prd_type):
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
        pref_spec_key = Preference.get_spec_key_pref_value(prd_type)

        if spec_key == self.prod_spec_key:
            return pref_spec_key

        if ((len(spec_key.strip()) > 0) and
                (spec_key != pref_spec_key)):
            Preference.update_spec_key_pref(spec_key, prd_type)
            return spec_key.strip()
        else:
            return Preference.get_spec_key_pref_value(prd_type)
