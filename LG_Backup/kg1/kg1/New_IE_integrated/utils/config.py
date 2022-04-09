# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 14:45:03 2021

@author: Anindya
"""

single_word_connectives = ['before', 'then', 'till', 'until', 'after', 'once', 'meanwhile', 'that',\
                        'meantime', 'because', 'so', 'thus', 'therefore', 'if', 'when', 'while',\
                        'but', 'however', 'although', 'and', 'also', 'or', 'unless', 'otherwise', 'except']

multi_word_connectives = ['at the same time', 'so that', 'by contrast', 'in contrast', \
                        'on the other hand', 'on the contrary', 'as an alternative',  \
                        'for example', 'for instance', 'in other words']

overlap_connectives = ['so']

Precedence=['before', 'then', 'till', 'until']
Succession=['after', 'once']
#Synchronous=['meanwhile', 'meantime', 'at the same time']
Synchronous=['meanwhile', 'meantime', 'at the same time', 'while', 'when']
Reason=['because']
Result=['so', 'thus', 'therefore', 'so that']
Condition=['if']
Contrast=['but', 'however', 'by contrast', 'in contrast', 'on the other hand', 'on the contrary']
Concession=['although']
Conjunction=['and', 'also']
Instantiation=['for example', 'for instance']
Restatement=['in other words']
Alternative=['or', 'unless', 'as an alternative', 'otherwise']
Exception_rel=['except']
