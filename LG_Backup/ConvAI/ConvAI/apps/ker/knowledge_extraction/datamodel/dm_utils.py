"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
@modified-by: purnanaga.nalluri@lge.com
"""
import sys
import os
import logging as logger

from datamodel.schema.rdf_schema_parser import RDFParser

# instance for loading RDFSChema
SCHEMA_OBJ = RDFParser()


class DMUtils(object):
    """ Defines common utils method used for datamodeling """

    @classmethod
    def get_common_key(cls, key, key_dict):
        """
           finds the common key of given table key from given dictionary
           Args:
                key : string
                key_dict : dictionary object
           Returns:
               commonkey:str
        """
        if key_dict == None:
            return None
        key = key.strip()
        for common_key, value in key_dict.items():
            if key in value:
                return common_key

        return None

    @classmethod
    def get_map_key(cls, key, key_dict):
        """
           finds the common key of given table key from given dictionary
           Args:
                key : string
                key_dict : dictionary object
           Returns:
               commonkey:str
        """
        if key_dict == None:
            return None
        key = key.strip()
        for commonkey, value in key_dict.items():
            for eachvalue in value:
                if key.lower() == eachvalue.lower():
                    return commonkey

        return None


class Node(object):
    """
    Node class to create dict object for entity using given type and name
    Args:
        type - str
        name - str
        prop_key - str
        prop_value - str
    Returns:
        object
    """

    def __init__(self, type: None, name: None, prop_dict=None):
        self.type = type
        self.Name = name
        self.prop = prop_dict


class Relation(object):
    """
    Relation class to create dict object for relationship
    Args:
        type - str
        prop_dict - dict
    Returns:
        object
    """

    def __init__(self, type: None, prop_dict=None):
        self.type = type
        self.prop = prop_dict


class NodeRelation(object):
    """
    NodeRelation class to create dict object for Nodes and Relation
    Args:
        domain - Node Object
        relation - Relation object
        rangenode - Node Object
    Returns:
        NodeRelation object
    """

    def __init__(self, domain: None, relation: None, rangenode: None):
        self.domain = domain
        self.relation = relation
        self.range = rangenode
