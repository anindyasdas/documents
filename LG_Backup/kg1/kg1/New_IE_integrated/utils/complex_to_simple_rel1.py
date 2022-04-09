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
#predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz")
lib_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
print(lib_path)
sys.path.append(lib_path)
from utils import config as cfg

discourse_connectives1= cfg.single_word_connectives

discourse_connectives2= cfg.multi_word_connectives


discourse_connectives= discourse_connectives1 + discourse_connectives2





class ClausalRelExtractor:
    """
    class is used to output the coreference resolved text, for any incoming text
    containing multiple sentences
    """
    def __init__(self):
        self.predictor = Predictor.from_path("elmo-constituency-parser-2020.02.10.tar.gz")
        
    def find_clauses(self, sent):
        '''This function takes sentence as input return clauses, first one is subordinate, secoding one is principle
        if no such break up is possible it returns original sentence
        '''
        print('####### Extracting Clauses ################')
        #print(sent)
        prediction= self.predictor.predict(sentence=sent)
        #print(prediction['trees'])
        try:
            sent_tree=nltk.tree.ParentedTree.fromstring(prediction['trees'])
        except:
            return (-1, -1)
        clauses=[]
        s=[]
        x=self.traverse_tree(sent_tree,s)
        if len(x)==0:
            clauses=self.pattern_2(sent_tree)
        elif type(x[0])== nltk.tree.ParentedTree:
            Flag = True #change
            new_leaves=[]
            connectives =[]
            leaves_list=x[0].leaves()
            #print(leaves_list)
            for l in leaves_list:
                if l.lower() in discourse_connectives1 and Flag: #change
                    connectives.append(l)
                else:
                    new_leaves.append(l)
                    if l not in list(punctuation): #change
                        Flag = False #change
            if len(connectives) > 0:
                clauses.append(' '.join(connectives))
            clauses.append(' '.join(new_leaves))
            if x[0].treeposition():
                del sent_tree[x[0].treeposition()]
                clauses.append(' '.join(sent_tree.leaves()))
            #print('clauses:', clauses)
            
            
            if len(clauses) ==2:
                clauses= self.extract_multiword_connective(clauses)
        else:
            clauses.append(' '.join(sent_tree.leaves()))
        
        
    
        if clauses[0].lower() in cfg.overlap_connectives and len(clauses) ==3:
            multi_word_clauses= []
            multi_word_clauses.append(' '.join(clauses[:-1]))
            multi_word_clauses.append(clauses[2])
            multi_word_clauses= self.extract_multiword_connective(multi_word_clauses)
            if len(multi_word_clauses) ==3:
                clauses = multi_word_clauses
        
        clauses=self.clear_puntuation(clauses)
    
        #print(clauses)
        #print('relations:', self.discourse_rel(clauses))
        return (clauses, self.discourse_rel(clauses))
    
    def traverse_tree(self, tree, s):
        #print("tree:", tree, 'label: ', tree.label(), len(tree))
        if tree.label() in ['SBAR']:
            s.append(tree)
            return (s)
        for subtree in tree:
            if type(subtree) == nltk.tree.ParentedTree:
                self.traverse_tree(subtree, s)
        return (s)
    
    def pattern_2(self, tree):
        '''(S
        (S (NP (PRP I)) (VP (VBP eat) (NP (NN apple))))
        (, ,)
        (S
         (ADVP (RB then))
         (NP (PRP I))
         (VP (VBP go) (S (VP (TO to) (VP (VB swim))))))
        (. .))
        '''
        #print('pattern2:')
        s=[]
        clauses=[]
        
        for subtree in tree:
            if subtree.label() in ['S']:
                s.append(subtree)
            elif subtree.label() in ['CC']:
                s.append(subtree)
        
        
        #print(len(s), s)
        if len(s)==2:
            for i in s:
                leaves_list=i.leaves()
                new_leaves=[]
                connectives=[]
                Flag= True #change
                for l in leaves_list:
                    if l.lower() in discourse_connectives1 and Flag and len(connectives) ==0: #change
                        connectives.append(l)
                    else:
                        new_leaves.append(l)
                        if l not in list(punctuation): #change
                            Flag = False #change
                if len(connectives)>0:
                    clauses.append(' '.join(connectives))
                clauses.append(' '.join(new_leaves))
        elif len(s)==3:
            for item in s:
                clauses.append(' '.join(item.leaves()))
        else:
            clauses= self.pattern_3(tree)
            #clauses.append(' '.join(tree.leaves()))
        new_clauses=[]
        if len(clauses) ==3 and clauses[1] in discourse_connectives1:
            new_clauses.append(clauses[1])
            new_clauses.append(clauses[2])
            new_clauses.append(clauses[0])
            clauses=new_clauses
        elif len(clauses) ==2:
            clauses= self.extract_multiword_connective(clauses)
                
            
        return (clauses)
    
    def extract_multiword_connective(self, clauses):
        new_clauses=[]
        pos= None
        pos1= None
        for c in discourse_connectives2:
            pos= re.search(c, clauses[0].lower())
            pos1= re.search(c, clauses[1].lower())
            if pos:
                connective=clauses[0][pos.span()[0] : pos.span()[1]]
                new_clauses.append(connective)
                new_clauses.append(clauses[0].replace(connective, '').strip())
                new_clauses.append(clauses[1])
                clauses=new_clauses
                break
            elif pos1:
                connective= clauses[1][pos1.span()[0] : pos1.span()[1]]
                new_clauses.append(connective)
                new_clauses.append(clauses[1].replace(connective, '').strip())
                new_clauses.append(clauses[0])
                clauses=new_clauses
                break
        return (clauses)
    
    def clear_puntuation(self, clauses):
        for i, item in enumerate(clauses):
            # replacing the multiple in-between spaces with one space
            item = re.sub('\s{2,}', ' ', item)
            # remove the space around the '-' character
            item = re.sub('\s*-\s*', '-', item)
            #print(item,item.strip(punctuation).strip() )
            clauses[i]= item.strip(punctuation).strip()
        return clauses
    
    def discourse_rel(self, clauses):
        '''https://arxiv.org/abs/1905.00270
        The function defines 14 types of relations based on extracted clauses
        for details refer Table 5 of the mentioned paper
        '''
        rel=[]
        
        if len(clauses)==3 and not('' in clauses): #change
            #print('hi')
            if clauses[0].lower() in cfg.Precedence:
                #rel.append((clauses[2], 'Precedence', clauses[1]))
                #rel.append((clauses[1], 'Succession', clauses[2]))
                rel.append((clauses[2], 'succeded by', clauses[1]))
                rel.append((clauses[1], 'preceded by', clauses[2]))
            elif clauses[0].lower() in cfg.Succession:
                #rel.append((clauses[2], 'Succession', clauses[1]))
                #rel.append((clauses[1], 'Precedence', clauses[2]))
                rel.append((clauses[2], 'preceded by', clauses[1]))
                rel.append((clauses[1], 'succeded by', clauses[2]))
            elif clauses[0].lower() in cfg.Synchronous:
                rel.append((clauses[2], 'Synchronous', clauses[1]))
                rel.append((clauses[1], 'Synchronous', clauses[2]))
            elif clauses[0].lower() in cfg.Reason:
                rel.append((clauses[2], 'Reason', clauses[1]))
                rel.append((clauses[1], 'Result', clauses[2]))
            elif clauses[0].lower() in cfg.Result:
                rel.append((clauses[2], 'Result', clauses[1]))
                rel.append((clauses[1], 'Reason', clauses[2]))
            elif clauses[0].lower() in cfg.Condition:
                rel.append((clauses[2], 'Condition', clauses[1]))
                rel.append((clauses[1], 'Follows', clauses[2]))
            elif clauses[0].lower() in cfg.Contrast:
                rel.append((clauses[2], 'Contrast', clauses[1]))
            elif clauses[0].lower() in cfg.Concession:
                rel.append((clauses[2], 'Concession', clauses[1]))
            elif clauses[0].lower() in cfg.Conjunction:
                rel.append((clauses[2], 'Conjunction', clauses[1]))
                rel.append((clauses[1], 'Conjunction', clauses[2]))
            elif clauses[0].lower() in cfg.Instantiation:
                rel.append((clauses[2], 'Instantiation', clauses[1]))
            elif clauses[0].lower() in cfg.Restatement:
                rel.append((clauses[2], 'Restatement', clauses[1]))
            elif clauses[0].lower() in cfg.Alternative:
                rel.append((clauses[2], 'Alternative', clauses[1]))
                rel.append((clauses[1], 'Alternative', clauses[2]))
            elif clauses[0].lower() in cfg.Exception_rel:
                rel.append((clauses[2], 'Exception', clauses[1]))
            else:
                rel.append((clauses[2], clauses[0], clauses[1]))
        return rel
    
    def pattern_3_process1(self, tree):
    
        s=[]
        for subtree in tree:
            #print('subtree:', subtree)
            if subtree.label() in ['S']:
                for subsubtree in subtree:
                    if subsubtree.label() in ['ADVP']:
                        s.append(subtree)
                        return (s)
            else:
                if type(subtree) == nltk.tree.ParentedTree:
                    s= self.pattern_3_process(subtree)
        return (s)
    
    
    def pattern_3_process(self, tree, s):
    
        #print('the tree:', tree)
        for subtree in tree:
            #print('subtree:', subtree)
            if type(subtree) == nltk.tree.ParentedTree:
                if subtree.label() in ['ADVP', 'PP']:
                    if tree.label() in ['S']:
                        s.append(tree)
                        return (s)
                else:
                    s= self.pattern_3_process(subtree, s)
        return (s)
    
    def pattern_3(self, tree):
        '''
        (S
      (NP (PRP I))
      (VP
        (VBP go)
        (S (VP (TO to) (VP (VB swim))))
        (, ,)
        (S
          (ADVP (RB however))
          (S (NP (PRP I)) (VP (VBP eat) (NP (NN apple))))))
      (. .))
        '''
        #print('pattern3:')
        s=[]
        #print('pattern 3:', tree)
        #for pos in tree.treepositions():
            #print('pos:',pos, tree[pos])
        clauses=[]
        #print('before:', tree)
        s= self.pattern_3_process(tree, s)
        #print('after',tree)
        #for pos in tree.treepositions():
         #   print('pos:',pos, tree[pos])
        #print('s:', s)#, s[0].treeposition())
        if len(s)==1 and type(s[0])== nltk.tree.ParentedTree: #change
            new_leaves=[]
            connectives =[]
            leaves_list=s[0].leaves()
            Flag = True #change
            for l in leaves_list:
                if l.lower() in discourse_connectives1 and Flag:
                    connectives.append(l)
                else:
                    new_leaves.append(l)
                    if l not in list(punctuation): #change
                        Flag = False #change
            if len(connectives) > 0 : 
                clauses.append(' '.join(connectives))
            clauses.append(' '.join(new_leaves))
            #print('HHHHHHHHHHHHH', s[0].treeposition())
            #print(s== tree)
            #print(tree)
            if s[0].treeposition():
                del tree[s[0].treeposition()]
                clauses.append(' '.join(tree.leaves()))
            #del tree[s[0].treeposition()]
            #clauses.append(' '.join(tree.leaves()))
        else:
            clauses.append(' '.join(tree.leaves()))
        return (clauses)

        

    







    








        
    
        


        
        
        




if __name__=="__main__":
    clausal_extractor = ClausalRelExtractor()
    while True:    
        sent=input('>')
        cl , rel= clausal_extractor.find_clauses(sent)
        print(cl)
        print(rel)

