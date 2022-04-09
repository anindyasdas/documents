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
lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(lib_path)
from utility_functions import process_string






class ImparativeToDeclarative:
    """
    class is used to output the declarative sentence for a given imparative sentences
    """
    def __init__(self):
        self.predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz")
        
    def convert_sentence(self, sent):
        '''This function takes sentence as input return declarative sentence
        '''
        #print(sent)
        sen_split=sent.strip().split()
        if sen_split[0].lower() == "never":
            sent= "Do not " + " ".join(sen_split[1:])
            sent=process_string(sent)
        prediction= self.predictor.predict(sentence=sent)
        #print(prediction['trees'])
        try:
            sent_tree=nltk.tree.ParentedTree.fromstring(prediction['trees'])    
        except:
            return sent
        
        new_sent, trip=self.traverse_tree(sent_tree)
        if new_sent.strip()=="":
            new_sent=sent 
        return new_sent, trip
    
    def traverse_tree(self, tree):
        subtrees=[]
        if tree.label() in ['S']:
            for subtree in tree: 
                label = subtree.label() 
                if label in punctuation or label in ['ADVP']: 
                    continue 
                else: 
                    subtrees.append(subtree)
        sent, trip = self.process_subtree(subtrees)
        return sent, trip
    
    def create_new_sent(self, vb, np, pp, mode):
        new_sent= ""
        if vb.strip()!='':
            vb= conjugate(verb=vb,tense="vbn") #pattern.en library for verb conjugation 
        if vb and np:
            new_sent= " ".join([np, mode, 'be', vb, pp])
        return new_sent

    def process_subtree(self, subtrees): 
        new_sent="" 
        check_do=""
        check_not=""
        if len(subtrees) ==1 and subtrees[0].label() in ['VP']: 
            new_subtrees=[] 
            for sub_sub_tree in subtrees[0]: 
                if sub_sub_tree.label()[:2] in ['VB']: 
                    check_do= " ".join(sub_sub_tree.leaves()) 
                elif sub_sub_tree.label() in ['RB']:
                    check_not=" ".join(sub_sub_tree.leaves()) 
                else: 
                    new_subtrees.append(sub_sub_tree)
        
        if check_do.lower() == 'do' and check_not.lower() == 'not' and len(new_subtrees) ==1: 
            vb, np, pp = self.process_phrases_neg(new_subtrees, "", "", "")
            vb, np, pp = process_string(vb), process_string(np), process_string(pp)
            new_sent = self.create_new_sent(vb, np, pp, "should not")
        else:
            vb, np, pp = self.process_positive(subtrees)
            vb, np, pp = process_string(vb), process_string(np), process_string(pp)
            new_sent = self.create_new_sent(vb, np, pp, "should")
        trip = (np, vb, pp)
        
            
            
        return new_sent, trip

    def process_positive(self, subtrees):
        check_vb=""
        check_np=""
        check_pp=""
        check_np1=""
        pp_list=[]
        if len(subtrees) ==1 and subtrees[0].label() in ['VP']: 
            for sub_sub_tree in subtrees[0]: 
                if sub_sub_tree.label()[:2] in ['VB']: 
                    check_vb= " ".join(sub_sub_tree.leaves()) 
                elif sub_sub_tree.label() in ['NP'] and check_np=="":
                    check_np=" ".join(sub_sub_tree.leaves()) 
                elif sub_sub_tree.label() in ['S','VP']:
                    check_np1, check_pp= self.process_pos_pattern_1(sub_sub_tree)
                    break
                else:
                    pp_list.extend(sub_sub_tree.leaves())
        if check_np=="":
            check_np=check_np1
        pp_list.append(check_pp)
        if len(pp_list):#if not empty
            check_pp = " ".join(pp_list)
        
        return check_vb, check_np, check_pp
        

    def process_pos_pattern_1(self, subtree):
        check_np=""
        check_pp=""
        pp_list=[]
        for sub_sub_tree in subtree:
            if sub_sub_tree.label() in ['NP'] and check_np=="": 
                check_np=" ".join(sub_sub_tree.leaves()) 
            else: 
                pp_list.extend(sub_sub_tree.leaves())
        check_pp=" ".join(pp_list)
        
        return check_np, check_pp
        
    

    def process_phrases_neg(self, new_subtrees,main_vb, np, pp): 
        #main_vb, np, pp="", "", ""
        main_vb1=""
        np1=""
        pp_list =[]
        if new_subtrees[0].label() in ['VP', 'S']: 
            for subtree in new_subtrees[0]: 
                if subtree.label() in ['VB']: 
                    main_vb = " ".join(subtree.leaves()) 
                elif subtree.label() in ['NP']: 
                    np =  " ".join(subtree.leaves())
                elif subtree.label() in ['S']:
                    main_vb1, np1, pp = self.process_phrases_neg([subtree],main_vb, np, pp)
                    pp_list.append(pp)
                else:
                    pp_list.extend(subtree.leaves())
        if np=="":
            np=np1
        if main_vb=="":
            main_vb=main_vb1
        
        if len(pp_list):#if not empty
            pp = " ".join(pp_list) 
        return main_vb, np, pp





    








        
    
        


        
        
        




if __name__=="__main__":
    imp_to_dec = ImparativeToDeclarative()
    while True:    
        sent=input('>')
        new_sent, trip= imp_to_dec.convert_sentence(sent)
        print(new_sent)

