# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 19:54:33 2020

@author: Anindya
Breaks only Complex sentences, does not work for compound sentence
Works for Imparative/Declarative but not for 

"""

from allennlp.predictors.predictor import Predictor
import allennlp_models.structured_prediction
import nltk
import re
from string import punctuation
import os
import sys
from pattern.en import conjugate #used for verb conjugation






class TripleExtractor:
    """
    class is used to output the extracted triples from sentences, starts with To
    eg. To assemble the bin, slide the bin in above the desired support and push down.
    """
    def __init__(self):
        self.predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz")
        
    def extract_triple(self, sent):
        '''This function takes sentence as input return declarative sentence
        '''
        #print(sent)
        prediction= self.predictor.predict(sentence=sent)
        #print(prediction['trees'])
        try:
            sent_tree=nltk.tree.ParentedTree.fromstring(prediction['trees'])    
        except:
            return ""
        
        new_sent=self.traverse_tree(sent_tree)
        
        return new_sent
    
   
    




    def create_trip(self, rest, vb, np):
        tail=""
        trip=""
        if rest: 
            tail=" ".join(rest)
        if vb and np and tail: 
            rel = " ".join(['should', 'be', conjugate(vb, tense='vbn'), 'by']) 
            trip=(np, rel, tail) 
        return trip
    
    
    
        
    
    
    def traverse_tree(self, tree):
        rest=[]
        vb,np,rest=self.process_pattern(tree, rest)
        trip=self.create_trip(rest, vb, np)
        return trip
        
    
    
    def process_pattern(self, tree, rest):
        vb= ""
        np=""
        subtrees=[]
        rest1=[]
        for subtree in tree:
            if subtree.label() not in punctuation:
                subtrees.append(subtree)
        if subtrees[0].label() in ['TO'] and len(subtrees)>0:
            #print("hi", subtrees[1:])
            for item in subtrees[2:]:
                if item.label() not in punctuation:
                    rest1.extend(item.leaves())
            #print("restpp:",rest1)
            rest= rest1+rest
            vb, np, rest = self.process_subtree(subtrees[1:],rest)
        elif subtrees[0].label() in ['S', 'VP']:
            for item in subtrees[1:]:
                if item.label() not in punctuation:
                    rest1.extend(item.leaves())
            rest=rest1+rest
            vb,np,rest= self.process_pattern(subtrees[0], rest)
        
        return vb,np,rest
            
            
            
            
                
    def process_subtree(self, subtrees,rest):
        np=""
        vb=""
        rest_1=[]
        sub_sub_trees=[]
        #print("restps:",rest)
        
        for sub_sub_tree in subtrees[0]:
            sub_sub_trees.append(sub_sub_tree)
        
        if len(sub_sub_tree)>0 and sub_sub_trees[0].label() in ['VP']:
            for item in sub_sub_trees[1:]:
                if item.label() not in punctuation:
                    rest_1.extend(item.leaves())
            #print("restpst:",rest_1, sub_sub_trees[1:])
            rest=rest_1+rest
            vb, np, rest= self.process_sub_sub_tree(sub_sub_trees[0], rest)
            
        else:
            for sub_sub_tree in sub_sub_trees:
                if sub_sub_tree.label()[:2] in ['VB']:
                    vb= " ".join(sub_sub_tree.leaves())
                elif sub_sub_tree.label() in ['NP']:
                    np= " ".join(sub_sub_tree.leaves())
                elif sub_sub_tree.label() not in punctuation:
                    rest_1.extend(sub_sub_tree.leaves())
            rest= rest_1+rest
        #print("restpse:",rest)
                    
        return vb, np, rest
    
    def process_sub_sub_tree(self, sub_sub_tree, rest):
        np=""
        vb=""
        #print("rest:",rest)
        rest_1=[]
        for sub_sub_tree in sub_sub_tree:
            if sub_sub_tree.label()[:2] in ['VB']:
                vb= " ".join(sub_sub_tree.leaves())
            elif sub_sub_tree.label() in ['NP']:
                np= " ".join(sub_sub_tree.leaves())
            elif sub_sub_tree.label() not in punctuation:
                rest_1.extend(sub_sub_tree.leaves())
        #print("rest1:",rest_1)
        rest= rest_1+rest
        #print("rest:",rest)
        return vb, np, rest
                
                


    
    




        
    
        


        
        
        




if __name__=="__main__":
    te = TripleExtractor()
    while True:    
        sent=input('>')
        extracted= te.extract_triple(sent)
        print(extracted)

