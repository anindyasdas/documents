# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""
import logging as logger
from constants import params as p

class PostProcessOprData(object):
    """
    this class is used to perform post processing the extracted json ,change the required section content in
    supported format
    """

    post_process_section = {'Storing Food': {'Food Storage Tips':['How to Store Food']}}

    def post_process_data(self, data):
        """
        post process the data extracted from the manual to reframe the content.

        Args:
            data: extracted data from the manual in json format
        return:
            data: reframed section content in json
        """
        reframed_json = {}
        data = data[p.ExtractionConstants.OPERATION_KEY]
        for section in self.post_process_section.keys():
            for internal_section in self.post_process_section[section].keys():
                for topic in self.post_process_section[section][internal_section]:
                    if topic in data[section][internal_section]:
                        reframe_data = self._reframe_section_data(data[section][internal_section][topic], section, topic)
                        data[section][internal_section].pop(topic)
                        data[section][internal_section].update(reframe_data)
        logger.debug('reframed json : %s',data)
        reframed_json[p.ExtractionConstants.OPERATION_KEY] = data
        return reframed_json

    def _reframe_section_data(self, data, section, topic):
        """
        reframe the section content in standar format based on section and topic title.

        Args:
            data: extraced section from the manual
            section: section title content need to reframed
            topic:topic under the section need to reframed
        return:
            reframed the section content json
        """
        if section is 'Storing Food' and topic is 'How to Store Food':
            descriptions = data[p.DESCRIPTION_KEY]
            section_data = {}
            section_data[p.ENTRIES] = []
            for idx, value in enumerate(descriptions):
                entry = {}
                if idx % 2 == 0:
                    entry[p.ExtractionConstants.FOOD_KEY] = value
                    entry[p.ExtractionConstants.HOW_TO_STORE_KEY] = descriptions[idx+1]
                    section_data[p.ENTRIES].append(entry)
                    idx = idx+1

        return section_data
