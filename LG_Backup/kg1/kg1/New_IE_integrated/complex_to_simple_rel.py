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
predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz")


discourse_connectives1=['before', 'then', 'till', 'until', 'after', 'once', 'meanwhile',\
                        'meantime', 'because', 'so', 'thus', 'therefore', 'if', 'when', \
                        'but', 'however', 'although', 'and', 'also', 'or', 'unless', 'otherwise', 'except']

discourse_connectives2=['at the same time', 'so that', 'by contrast', 'in contrast', \
                        'on the other hand', 'on the contrary', 'as an alternative',  \
                        'for example', 'for instance', 'in other words']


discourse_connectives= discourse_connectives1 + discourse_connectives2

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




def discourse_rel(clauses):
    '''https://arxiv.org/abs/1905.00270
    The function defines 14 types of relations based on extracted clauses
    for details refer Table 5 of the mentioned paper
    '''
    rel=[]
    
    if len(clauses)==3 and not('' in clauses): #change
        #print('hi')
        if clauses[0].lower() in Precedence:
            rel.append((clauses[2], 'Precedence', clauses[1]))
        elif clauses[0].lower() in Succession:
            rel.append((clauses[2], 'Succession', clauses[1]))
        elif clauses[0].lower() in Synchronous:
            rel.append((clauses[2], 'Synchronous', clauses[1]))
        elif clauses[0].lower() in Reason:
            rel.append((clauses[2], 'Reason', clauses[1]))
        elif clauses[0].lower() in Result:
            rel.append((clauses[2], 'Result', clauses[1]))
        elif clauses[0].lower() in Condition:
            rel.append((clauses[2], 'Condition', clauses[1]))
            rel.append((clauses[1], 'take action', clauses[2]))
        elif clauses[0].lower() in Contrast:
            rel.append((clauses[2], 'Contrast', clauses[1]))
        elif clauses[0].lower() in Concession:
            rel.append((clauses[2], 'Concession', clauses[1]))
        elif clauses[0].lower() in Conjunction:
            rel.append((clauses[2], 'Conjunction', clauses[1]))
        elif clauses[0].lower() in Instantiation:
            rel.append((clauses[2], 'Instantiation', clauses[1]))
        elif clauses[0].lower() in Restatement:
            rel.append((clauses[2], 'Restatement', clauses[1]))
        elif clauses[0].lower() in Alternative:
            rel.append((clauses[2], 'Alternative', clauses[1]))
        elif clauses[0].lower() in Exception_rel:
            rel.append((clauses[2], 'Exception', clauses[1]))
        else:
            rel.append((clauses[2], clauses[0], clauses[1]))
    return rel
        


def extract_multiword_connective(clauses):
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


def clear_puntuation(clauses):
    for i, item in enumerate(clauses):
        #print(item,item.strip(punctuation).strip() )
        clauses[i]= item.strip(punctuation).strip()
    return clauses
    

def pattern_3_process1(tree):
    
    s=[]
    for subtree in tree:
        print('subtree:', subtree)
        if subtree.label() in ['S']:
            for subsubtree in subtree:
                if subsubtree.label() in ['ADVP']:
                    s.append(subtree)
                    return (s)
        else:
            if type(subtree) == nltk.tree.ParentedTree:
                s= pattern_3_process(subtree)
    return (s)


def pattern_3_process(tree, s):
    
    print('the tree:', tree)
    for subtree in tree:
        print('subtree:', subtree)
        if type(subtree) == nltk.tree.ParentedTree:
            if subtree.label() in ['ADVP', 'PP']:
                if tree.label() in ['S']:
                    s.append(tree)
                    return (s)
            else:
                s= pattern_3_process(subtree, s)
    return (s)


def pattern_3(tree):
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
    print('pattern3:')
    s=[]
    print('pattern 3:', tree)
    for pos in tree.treepositions():
        print('pos:',pos, tree[pos])
    clauses=[]
    print('before:', tree)
    s= pattern_3_process(tree, s)
    print('after',tree)
    for pos in tree.treepositions():
        print('pos:',pos, tree[pos])
    print('s:', s, s[0].treeposition())
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
        print('HHHHHHHHHHHHH', s[0].treeposition())
        print(s== tree)
        print(tree)
        del tree[s[0].treeposition()]
        clauses.append(' '.join(tree.leaves()))
    else:
        clauses.append(' '.join(tree.leaves()))
    return (clauses)
        
    
        

def pattern_2(tree):
    '''(S
    (S (NP (PRP I)) (VP (VBP eat) (NP (NN apple))))
    (, ,)
    (S
     (ADVP (RB then))
     (NP (PRP I))
     (VP (VBP go) (S (VP (TO to) (VP (VB swim))))))
    (. .))
    '''
    print('pattern2:')
    s=[]
    clauses=[]
    
    for subtree in tree:
        if subtree.label() in ['S']:
            s.append(subtree)
        elif subtree.label() in ['CC']:
            s.append(subtree)
    
    
    print(len(s), s)
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
        clauses= pattern_3(tree)
        #clauses.append(' '.join(tree.leaves()))
    new_clauses=[]
    if len(clauses) ==3 and clauses[1] in discourse_connectives1:
        new_clauses.append(clauses[1])
        new_clauses.append(clauses[2])
        new_clauses.append(clauses[0])
        clauses=new_clauses
    elif len(clauses) ==2:
        clauses= extract_multiword_connective(clauses)
            
        
    return (clauses)
        
        
        

def traverse_tree(tree, s):
    print("tree:", tree, 'label: ', tree.label(), len(tree))
    if tree.label() in ['SBAR']:
        s.append(tree)
        return (s)
    for subtree in tree:
        if type(subtree) == nltk.tree.ParentedTree:
            traverse_tree(subtree, s)
    return (s)
            

while True:    
    sent=input('>')
    prediction= predictor.predict(sentence=sent)
    sent_tree=nltk.tree.ParentedTree.fromstring(prediction['trees'])
    clauses=[]
    s=[]
    x=traverse_tree(sent_tree,s)
    if len(x)==0:
        clauses=pattern_2(sent_tree)
        
    elif type(x[0])== nltk.tree.ParentedTree:
        Flag = True #change
        new_leaves=[]
        connectives =[]
        leaves_list=x[0].leaves()
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
        del sent_tree[x[0].treeposition()]
        clauses.append(' '.join(sent_tree.leaves()))
        print('clauses:', clauses)
        if len(clauses) ==2:
            clauses= extract_multiword_connective(clauses)
    else:
        clauses.append(' '.join(sent_tree.leaves()))
    
    clauses=clear_puntuation(clauses)

    print(clauses)
    print('relations:', discourse_rel(clauses))
