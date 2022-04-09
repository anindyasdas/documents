"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import sys
import os
import logging as logger

from ..constants import params as cs
from .trob_dminterface import TroubleShooting
from .spec_dminterface import Specification
from .oper_dminterface import Operation


class DMInterface(object):
    """
    Data Modeling Engine class
    Defines the method to create triplets for manual sections
    """

    def __init__(self):
        pass

    def make_triplets(self, section, dict_object):
        """
            creates list of triplets(Node,Relation,Node) for list of input dict
            Args:
                section - str
                dict_object - dict
            Returns:
                list of Triplet objects
        """
        triplets_list = []
        try:
            if section == cs.SPEC_SECTION:
                obj = Specification()
            elif section == cs.TROB_SECTION:
                obj = TroubleShooting.get_instance()
            elif section == cs.OPERATION:
                obj = Operation()
            triplets_list = obj.make_triplets(dict_object)
            return triplets_list

        except (KeyError, ValueError, AttributeError) as e:
            logger.error("Error in make_triplets" + str(e))
            return None


if __name__ == "__main__":
    # logger configuration
    logger.basicConfig(level=logger.INFO,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    obj = Specification()
    main_dict = dict()
    test_dict = dict()

    test_dict[
        'Dimensions'] = '27”(W) x 29 .”(D) x 3811/16”(H) / 52” (D, door open)'
    test_dict['Net weight'] = '110'
    test_dict['Product Description'] = 'Front loader'

    main_dict['WM3997H'] = test_dict

    print("Input dict", main_dict)

    section_name = cs.TROUBLESHOOTING  # to extract TROUBLESHOOTING content
    triplets = obj.make_triplets(section_name, main_dict)

    print("In main triplets=", triplets)
