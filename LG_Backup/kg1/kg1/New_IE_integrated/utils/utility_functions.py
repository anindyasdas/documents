# -*- coding: utf-8 -*-
"""
Created on Mon Apr  5 17:34:41 2021

@author: anindya06.das
"""
import re

def process_string(s_string):
    
    s_string = re.sub('\s*-\s*', '-', s_string)
    s_string = re.sub('\s*/\s*', '/', s_string)
    s_string = re.sub('\s*\'\s*', '\'', s_string)
    s_string = re.sub('\s*\’\s*', '\'', s_string)
    #s_string = re.sub('\s*\.\s*', '. ', s_string)
    s_string = re.sub('\s*,\s*', ', ', s_string)
    s_string = re.sub('\s*;\s*', '; ', s_string)
    s_string = re.sub('\s{2,}', ' ', s_string)
    
    return s_string.strip()
