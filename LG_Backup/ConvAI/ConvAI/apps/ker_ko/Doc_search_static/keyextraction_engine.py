# -*- coding: utf-8 -*-
""""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anindya06.das@lge.com
##############################################################################
"""
import json
import logging as logger
from copy import deepcopy
import utils.params as cs
import utils.helper as hp
import re


class KeyValueExtractionEngine:
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, 'r', encoding='utf-8-sig') as jsonfile:
            self.jsonfile = json.load(jsonfile)

    def extract_triples(self):
        """
        This function extracts the triples by calling submethods and returns
        list of triples
        Returns
        -------
        trips : TYPE
            DESCRIPTION. list of triples
            heading, Relation_that_explains_the_heading, [key chain to reachout to that section]
           eg.('세탁기', '사용하기', ['세탁기', '사용하기'])
           ('알아두면 좋은 정보', '사용하기_전_알아두기', ['세탁기', '사용하기', '알아두면 좋은 정보', '사용하기 전 알아두기'])
        """
        key_track = []
        trips = self.traverse_dict(self.jsonfile, [], deepcopy(key_track))
        return trips

    def traverse_dict(self, new_dict, trips, key_track):
        """
        This function traverse the input dictionary , update the triples and key_track
        Parameters
        ----------
        new_dict : input dictionary to be traversed
        trips : list of triples(tuples of three items)
        key_track : list that track downs the section of the dict to reach out to current section
        Returns
        -------
        trips : TYPE list of triples
        """
        if type(new_dict) == dict:
            for key, value in new_dict.items():
                if key == cs.XMLTags.BUYERMODEL_TAG:
                    self.model_nums = value
                elif key == cs.XMLTags.PARTNUMBER_TAG:
                    self.partnumber= value
                elif key.lower() not in map(str.lower, cs.KO_REL_LIST):
                    key_track.append(key)
                    head = key
                    pred = ''
                    trips = self.get_predicates(value, head.strip(), pred.strip(), trips, deepcopy(key_track),
                                                parent='ent')
                    key_track.pop()
        return trips
    
    def update_pred(self, k, parent, pred, current_key_rel):
        # if current key of the dict is an ent and parent is also an ent, update the relation(new_pred) as 'description'
        if not current_key_rel:
            if parent!='rel':
                new_pred= "특징"
            else:
                new_pred = pred
        else:
        # if current key of the dict is relation, current key is added to existing relation
            if pred == "" :
                new_pred = " ".join(k.split())
            else:
                new_pred = pred.strip() + " " + " ".join(k.split())
        return new_pred
            
    
    def get_predicates_from_dict_items(self, val, head, pred, trips, key_track, parent):
        """
        Submodule to process the predicate for dict key and value items
        """
        for k, v in val.items():
            key_track.append(k)
            if k.lower() not in map(str.lower, cs.KO_REL_LIST):
                current_key_rel=False
                new_pred = self.update_pred(k, parent, pred, current_key_rel)
                trips_val_list = deepcopy(key_track)[:-1]
                trips.append((head.strip(), new_pred, trips_val_list))
                key_track.pop()
                trips = self.traverse_dict(val, trips, deepcopy(key_track))
            else:
                current_key_rel=True
                new_pred = self.update_pred(k, parent, pred, current_key_rel)
                trips = self.get_predicates(v, head.strip(), new_pred.strip(), trips, deepcopy(key_track))
                key_track.pop()
        return key_track, trips

    def get_predicates(self, val, head, pred, trips, key_track, parent='rel'):
        """
       This function processed the predicate or rel either by concatenating with the previous relation or 
       if the current key falls into the KO_REL_LIST list.
        Returns
        -------
        trips : list of triples
        """
        if type(val) == dict and len(val) > 0:  # non_empty dict
            key_track, trips= self.get_predicates_from_dict_items(val, head, pred, trips, key_track, parent)
        elif type(val) == list and len(val) > 0:  # non-empty list
            if pred == '':
                new_pred = cs.keywords_map[cs.DESCRIPTION_KEY.lower()]
            else:
                new_pred = pred
            tail = val
            trips_val_list = deepcopy(key_track) + [tail]
            trips.append((head.strip(), new_pred, trips_val_list[:-1]))

        return trips

    def format_keys_values(self, trips):
        """
        This function receives the triples and returns triples with formatted keys and
        values
        A key: Entity + Predicate
        Predicate= concatenated consecutive relations
        Parameters
        ----------
        trips : TYPE list of triples
            eg. ('알아두면 좋은 정보', '사용하기_전_알아두기', ['세탁기', '사용하기', '알아두면 좋은 정보', '사용하기 전 알아두기'])
    
        Returns
        -------
        new_trips : TYPE list of triples
            DESCRIPTION.
            ('알아두면 좋은 정보 사용하기 전 알아두기', '["세탁기"]["사용하기"]["알아두면 좋은 정보"]["사용하기 전 알아두기"]', '알아두면 좋은 정보')
        """
        new_list = []
        new_trips = []
        for line_no, item in enumerate(trips):
            if line_no == 0:
                new_trips.append(item)
                new_list.append(item)
                continue
            key = " ".join([item[0], item[1]])
            val = '["' + '"]["'.join(item[2]) + '"]'
            in_excluded_list = hp.check_exclude_list(hp.remove_num_item_tags(item[0]))
            # if the head is in excluded list ignore such triple
            # if the value does not contain section information i.e len(item[2])=1
            if in_excluded_list or len(item[2])==1 or re.search('<num(.*?)>', key):
                continue
            new_trips.append((key.strip(), val, item[0].strip()))
        return new_trips

    def add_part_num(self, trips):
        trips.insert(0, [self.partnumber])
        return trips


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG, format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                                                  "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    filename = input("Enter path to the file")
    Trip_obj = KeyValueExtractionEngine(filename)
    trp_processed = Trip_obj.extract_triples()
    trp_processed = hp.remove_duplicates(trp_processed)
    trp_processed = Trip_obj.add_part_num(trp_processed)
    trp_processed = Trip_obj.format_keys_values(trp_processed)
    outfile = input("Enter path to the sentence_key output file")
    hp.save_file(trp_processed, outfile, ftype='txt')
