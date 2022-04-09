"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas@lge.com
"""

import pyhocon

from . import constants


class BaseSimilarityModel:
    """
    Read the config file and apply the configurations for
    defined sections spec&trob
    """
    def __init__(self, config, name):
        config_file = pyhocon.ConfigFactory.parse_file(constants.CONFIG_FILE)
        self.config = config_file[name]
        if config is not None:
            for k, v in config.items():
                self.config[k] = v

        self.config_spec = config_file['info_extr_spec']
        self.config_trob = config_file['info_extr_trob']
