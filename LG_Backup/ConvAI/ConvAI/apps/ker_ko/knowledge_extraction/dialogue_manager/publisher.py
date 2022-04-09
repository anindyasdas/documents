# -*- coding: utf-8 -*-
"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""


class Publisher(object):
    
    def __init__():
        self.observers = []
    
    def add(self, observer):
        
        if observer not in self.observers:
            self.observers.append(observer)
        else:
            print('Failed to add observer')
    
    def remove(self, observer):
        try:
            self.observers.remove(observer)
        except ValueError:
            print('Failed to remove')
            
    def notify(self):
        [observer.notify for observer in self.observers]