# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
 * Copyright(c) 2020 by LG Electronics.
 * Confidential and Proprietary All Rights Reserved.
 *-------------------------------------------------*/
@author: vishwaas@lge.com
"""

from . import constants
from .rule_based.info_extraction import InfoExtractionRB

class InfoExtractionFactory:
    # currently rule based model is in use
    RULEBASED_MODEL = 2

    @staticmethod
    def get_info_extraction(model, config=None):
        """
        Gets the info extraction model
        :param model: int - Model to fetch
        :param config: dict - input configuration
        :return: model
        """

        if model == InfoExtractionFactory.RULEBASED_MODEL:
            info_extr = InfoExtractionRB(config)
            return info_extr
        else:
            raise ValueError("Model not found!")
