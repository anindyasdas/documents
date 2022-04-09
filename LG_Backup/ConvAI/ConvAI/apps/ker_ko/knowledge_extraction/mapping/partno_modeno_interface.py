# -*- coding: utf-8 -*-
# -------------------------------------------------
# Copyright(c) 2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------
# @author: anindya06.das@lge.com

# Standard library imports
import os
import logging as logger
import json
import re


class PartnoModelnoMapper:
    """
    Loads the part_no to model_no mapper
    and privdes the API to fetch model_no given a part_no and vice versa
    """
    def __init__(self, MAP_PATH):
        # loading the partno modelno mapping file as a class variable
        with open(os.path.join(MAP_PATH), 'r', encoding='utf-8-sig') as part_model_mapper_file:
            logger.debug("loading the partno modelno mapping file as a object variable")
            self.part_to_model = json.load(part_model_mapper_file)
            self.model_to_part = dict((model,part) for part, model in self.part_to_model.items())

    def get_part_no(self, model_no):
        """
        This method takes model_no as input, returns part_no

        Parameters
        ----------
        model_no : TYPE str
            DESCRIPTION. model_no of selected product

        Returns
        -------
        part_no_found : TYPE bool
            DESCRIPTION. If part_no is found , the flag is True, else False
        part_no : TYPE str
            DESCRIPTION. The field is empty string if part_no is not found

        """
        part_no_found=False
        part_no=''
        model_no_keys=list(self.model_to_part.keys())
        for modelno_chain in model_no_keys:
            for modelno_json in modelno_chain.split("/"):
                modelno_json_pattern = "^" + modelno_json.strip().replace('*', r"[A-Za-z0-9*]{1}") + "$"
                if re.match(modelno_json_pattern, model_no):
                    part_no_found= True
                    part_no=self.model_to_part[modelno_chain]
        return part_no_found, part_no

    def get_model_no(self, part_no):
        """
        This method takes part_no as input, returns model_no

        Parameters
        ----------
        model_no : TYPE str
            DESCRIPTION. model_no of selected product

        Returns
        -------
        part_no_found : TYPE bool
            DESCRIPTION. If part_no is found , the flag is True, else False
        part_no : TYPE str
            DESCRIPTION. The field is empty string if part_no is not found

        """
        model_no_found=False
        model_no=''
        part_no_keys=list(self.part_to_model.keys())
        for part_no_key in part_no_keys:
            if part_no_key==part_no:
                model_no_found=True
                #In case of a match first modelno is selected
                model_no=self.part_to_model[part_no_key].split("/")[0].strip()
        return model_no_found, model_no

     
if __name__=="__main__": 
    logger.basicConfig(level=logger.DEBUG, format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                                                  "funcName)s() %(message)s",datefmt='%Y-%m-%d,%H:%M:%S')
    # MAP_PATH is the path to part_no to model_no mapping dictionary, to be finalized during integration
    MAP_PATH="./partno_modelno_mapper.json"
    pm_mapper=PartnoModelnoMapper(MAP_PATH)
    logger.info("partnum to modelnum : %s", pm_mapper.part_to_model)
    logger.info("modelnum to partnum : %s", pm_mapper.model_to_part)
    print(pm_mapper.part_to_model)
    print(pm_mapper.model_to_part)
    print(pm_mapper.get_part_no('RD20AXD'))
    print(pm_mapper.get_model_no('MFL71831422'))
    