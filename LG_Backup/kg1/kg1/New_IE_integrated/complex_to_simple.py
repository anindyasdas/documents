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
predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz")


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
        clauses.append(' '.join(sent_tree.leaves()))
        
    elif type(x[0])== nltk.tree.ParentedTree:
        clauses.append(' '.join(x[0].leaves()))
        del sent_tree[x[0].treeposition()]
        clauses.append(' '.join(sent_tree.leaves()))
    else:
        clauses.append(' '.join(sent_tree.leaves()))
    print(clauses)
