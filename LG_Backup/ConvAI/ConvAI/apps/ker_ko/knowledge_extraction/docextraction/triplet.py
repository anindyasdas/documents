# -*- coding: utf-8 -*-
"""
 * Copyright (c) 2020 LG Electronics Inc.
 * SPDX-License-Identifier: LicenseRef-LGE-Proprietary
 *
 * This program or software including the accompanying associated documentation
 * (“Software”) is the proprietary software of LG Electronics Inc. and or its
 * licensors, and may only be used, duplicated, modified or distributed pursuant
 * to the terms and conditions of a separate written license agreement between you
 * and LG Electronics Inc. (“Authorized License”). Except as set forth in an
 * Authorized License, LG Electronics Inc. grants no license (express or implied),
 * rights to use, or waiver of any kind with respect to the Software, and LG
 * Electronics Inc. expressly reserves all rights in and to the Software and all
 * intellectual property therein. If you have no Authorized License, then you have
 * no rights to use the Software in any ways, and should immediately notify LG
 * Electronics Inc. and discontinue all use of the Software.

@author: senthil.sk@lge.com
"""


class Triplet:

    """
     Used for framing the triplets
    """
    _head_node, _relationship, _property, _tail_node = "", "", "", ""

    def __init__(self):
        _head_node, _relationship, _property, _tail_node = "", "", "", ""

    def set_head_node(self, node_str):
        """set the head node name string"""
        self._head_node = node_str

    def set_relationship_node(self, node_str):
        """set the relationship node name string"""
        self._relationship = node_str

    def set_relationship_property(self, property_str):
        """set the relationship node property string"""
        self._property = property_str

    def set_tail_node(self, node_str):
        """set the tail node name string"""
        self._tail_node = node_str

    def get_head_node(self):
        """get the head node name string"""
        return self._head_node

    def get_relationship_node(self):
        """get the relationship node name string"""
        return self._relationship

    def get_property(self):
        """get the relationship node property string"""
        return self._property

    def get_tail_node(self):
        """get the tail node name string"""
        return self._tail_node

    def check_triplets(self):
        """Check all the triplet info are filled"""
        node_cnt = 0
        if len(self._head_node) != 0:
            node_cnt = node_cnt + 1

        if len(self._relationship) != 0:
            node_cnt = node_cnt + 1

        if len(self._tail_node) != 0:
            node_cnt = node_cnt + 1

        if node_cnt >= 3:
            return 1
        else:
            return 0

    def __str__(self):
        print("output" + " : " + self._head_node + " : " + self._relationship + " : "
              + self._property + " : " + self._tail_node)
