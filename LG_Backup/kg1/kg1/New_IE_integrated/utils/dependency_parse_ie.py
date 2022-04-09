# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 13:17:06 2020

@author: Anindya
"""

import os
import time
import spacy
import pprint
from spacy.symbols import ORTH # value 65 , orthgraphy orth is simply an integer indicates the index of the occurrence of the word kept in spacy used for tokenizer exception
from spacy.util import *
from spacy.tokenizer import Tokenizer
import sys
import glob

def custom_sentence_segmentation(doc):
    doc_len = len(doc)
    for index, token in enumerate(doc):
        if(index > 0 and index < doc_len and doc[index-1].text not in ['.','?','!',';'] and not(doc[index-1].text.endswith('.'))):
            doc[index].sent_start = False
    return doc

def collapse_prepositions(sentToWordInfo):
    for sno in sentToWordInfo.keys():
        indexToWordInfo = sentToWordInfo[sno]
        for wno in indexToWordInfo.keys():
            if(wno == 0):
                continue
            wordInfo = indexToWordInfo[wno]
            parent = wordInfo[5][0]
            if(parent == 0):
                continue
            parent_dep = wordInfo[2][parent]
            if(parent_dep == 'pobj'):
                new_parent = indexToWordInfo[parent][5][0]
                new_parent_dep = 'nmod:'+indexToWordInfo[parent][0].lower()
                del wordInfo[2][parent]
                del indexToWordInfo[parent][3][wno]
                wordInfo[2][new_parent] = new_parent_dep
                indexToWordInfo[new_parent][3][wno] = new_parent_dep
                
def process_conjunctions(sentToWordInfo):
    for sno in sentToWordInfo.keys():
        indexToWordInfo = sentToWordInfo[sno]
        for wno in indexToWordInfo.keys():
            if(wno == 0):
                continue
            wordInfo = indexToWordInfo[wno]
            parent = list(wordInfo[2].keys())[0]
            if(parent == 0):
                continue
            parent_dep = wordInfo[2][parent]
            if(parent_dep == 'conj'):
                new_parent = list(indexToWordInfo[parent][2].keys())[0]
                new_dr = indexToWordInfo[parent][2][new_parent]
                while (new_dr == 'conj'):
                    prev_new_parent = new_parent
                    new_parent = list(indexToWordInfo[new_parent][2].keys())[0]
                    new_dr = indexToWordInfo[prev_new_parent][2][new_parent]
                del wordInfo[2][parent]
                del indexToWordInfo[parent][3][wno]
                wordInfo[2][new_parent] = new_dr
                indexToWordInfo[new_parent][3][wno] = new_dr

def get_head_index(indexToWordInfo, si, ei):
    for wno in range(si, ei+1):
        #print ('\twno='+str(wno)+'\t' + str(indexToWordInfo[wno]))
        if(indexToWordInfo[wno][5][0] < si or indexToWordInfo[wno][5][0] > ei):
            return wno
    return ei

def processSpaCy(paragraph, nlp_d):
    doc = nlp_d(paragraph) #.decode('unicode-escape'))
    #bio_ner_doc_protein = nlp_d_ner_protein(paragraph)
    #bio_ner_doc_disease = nlp_d_ner_disease(paragraph)
    doc_tokens = []
    #doc_protein_tokens = []
    #for token in doc:
    #    doc_tokens.append(token.text)
    #for token in bio_ner_doc_protein:
    #    doc_protein_tokens.append(token.text)
    #print(doc_tokens)
    #print(doc_protein_tokens)

    sentToWordInfo = {}
    token_index_to_sno_wno = {}
    num_words_in_prev_sents = 0
    sno = 0
    for sent in doc.sents:
        indexToWordInfo = {}
        root_wordInfo = ('_ROOT_', '_ROOT_', {}, {}, 'O', [], 'O', 'O', '_ROOT_')
        indexToWordInfo[0] = root_wordInfo
        num_words_in_curr_sent = 0
        for token in sent:
            num_words_in_curr_sent = num_words_in_curr_sent + 1
            wno = token.i + 1 - num_words_in_prev_sents
            token_index_to_sno_wno[token.i] = (sno, wno)
            word = token.text #.encode('ascii',errors='ignore')
            pos_tag = token.tag_
            parent_dict = {}
            child_dict = {}
            ner_tag = token.ent_type_
            if(ner_tag.startswith('PER')):
                ner_tag = 'PERSON'
            elif(ner_tag.startswith('ORG')):
                ner_tag = 'ORGANIZATION'
            elif(ner_tag.startswith('LOC')):
                ner_tag = 'LOCATION'

            basic_parent = []
            
            parent_index = 0
            parent_dep = 'root'
            if(token.head.i != token.i):
                parent_index = token.head.i + 1 - num_words_in_prev_sents
                parent_dep = token.dep_
            else:
                indexToWordInfo[0][3][wno] = 'root'
            parent_dict[parent_index] = parent_dep
            basic_parent.append(parent_index)
            
            for child in token.children:
                child_index = child.i + 1 - num_words_in_prev_sents
                child_dict[child_index] = child.dep_

            #bio_ner_tag_protein = 'O'

            # Bio NER Protein
            #for ent in bio_ner_doc_protein.ents:

                #if (ent.start_char <= token.idx) and (token.idx + len(token.text) <= ent.end_char):
                    #bio_ner_tag_protein = ent.label_

            #bio_ner_tag_disease = 'O'
            # Bio NER Disease
            #for ent in bio_ner_doc_disease.ents:
                #if (ent.start_char <= token.idx) and (token.idx + len(token.text) <= ent.end_char):
                    #bio_ner_tag_disease = ent.label_
            
            # General POS tag (coarse)
            pos_tag_coarse = token.pos_

            wordInfo = (word, pos_tag, parent_dict, child_dict, ner_tag,  basic_parent, pos_tag_coarse)
            indexToWordInfo[wno] = wordInfo
        num_words_in_prev_sents = num_words_in_prev_sents + num_words_in_curr_sent
        sentToWordInfo[sno] = indexToWordInfo
        sno = sno + 1
    
    #collapse_prepositions(sentToWordInfo)
    process_conjunctions(sentToWordInfo)
    return sentToWordInfo

def load_spacy_model():
    #it loads spacy model and adds exceptions
    additional_tokenizer_exceptions = {}
    f = open('./utils/single_tokens.txt')
    for line in f:
        parts = line.strip().split('\t')
        additional_tokenizer_exceptions[parts[0]] = [{ORTH: parts[0]}]
    f.close()
    nlp_d = spacy.load('en_core_web_md')
    #nlp_d_ner_protein = spacy.load('en_ner_jnlp_dba_md')
    #nlp_d_ner_disease = spacy.load('en_ner_bc5cdr_md')
    #how to tokenize 'gonna' [{65: 'gon', 73: 'go', 67: 'going'}, {65: 'na', 73: 'to', 67: 'to'}] tokenizer exception
    
    new_tokenizer_exceptions = update_exc(nlp_d.Defaults.tokenizer_exceptions, additional_tokenizer_exceptions) #used t update the exception
    prefix_re = compile_prefix_regex(nlp_d.Defaults.prefixes)
    suffix_re = compile_suffix_regex(nlp_d.Defaults.suffixes)
    #infix_re = compile_infix_regex(nlp_d.Defaults.infixes)
    #infix_re = re.compile(r'[\,\?\:\;\‘\’\`\“\”\"\'~]')
    infix_re = re.compile(r'[\,\?\:\;\'\"\~]')
    
    new_tokenizer = Tokenizer(nlp_d.vocab, new_tokenizer_exceptions, prefix_search=prefix_re.search, suffix_search=suffix_re.search, infix_finditer=infix_re.finditer,token_match=None)
    nlp_d.tokenizer = new_tokenizer
    #new_tokenizer = Tokenizer(nlp_d_ner_protein.vocab, new_tokenizer_exceptions, prefix_search=prefix_re.search, suffix_search=suffix_re.search, infix_finditer=infix_re.finditer,token_match=None)
    #nlp_d_ner_protein.tokenizer = new_tokenizer
    #new_tokenizer = Tokenizer(nlp_d_ner_disease.vocab, new_tokenizer_exceptions, prefix_search=prefix_re.search, suffix_search=suffix_re.search, infix_finditer=infix_re.finditer,token_match=None)
    #nlp_d_ner_disease.tokenizer = new_tokenizer

    nlp_d.add_pipe(custom_sentence_segmentation, before='parser') #add custom sentence segmentation to the pipeline
    #nlp_d_ner_protein.add_pipe(custom_sentence_segmentation, before='ner')
    #nlp_d_ner_disease.add_pipe(custom_sentence_segmentation, before='ner')


    # new_tokenizer = Tokenizer(nlp_d.vocab, new_tokenizer_exceptions, prefix_search=prefix_re.search, suffix_search=suffix_re.search, infix_finditer=infix_re.finditer,token_match=None)
    # nlp_d.tokenizer = new_tokenizer
    # nlp_d_ner_protein.tokenizer = new_tokenizer
    # nlp_d_ner_disease.tokenizer = new_tokenizer
    return nlp_d

def get_sentence(indexToWordInfo):
    words = []
    for wno in range(1, len(indexToWordInfo)):
        words.append(indexToWordInfo[wno][0])
    return ' '.join(words)


##########################################################
###########################################################
#####################################################
####################################################
##################################################
    

check_list=['pobj', 'ccomp', 'pcomp', 'dobj', 'mark', 'advmod','punct', 'cc']
def explore(dp, key, key2, mode=None):
    nodes=[key2]
    to_explore=[key2]
    while to_explore:
        node= to_explore.pop(-1)
        to_explore.extend([item for item in dp[key][node][3]])
        if mode:
            nodes.extend([item for item in dp[key][node][3] if dp[key][node][3][item].lower() not in [ 'mark', 'intj']])
        else:
            nodes.extend([item for item in dp[key][node][3] if dp[key][node][3][item].lower() not in ['nsubj',  'mark', 'intj']])
    nodes.sort()
    string_1= ' '.join(map(lambda k:dp[key][k][0], nodes))
    head= nodes.pop(-1)
    return(string_1)

def do_process_(dp,key,key2):
    trip=[]
    trip_a=[]
    trip_d=[]
    trip_p=[]
    trip_c=[]
    head= None
    rel=dp[key][key2][0]
    #print('hi:', dp[key])
    #print('rel:', rel)
    if 'neg' in dp[key][key2][3].values():
        rel= 'not' + ' ' + rel #handle negation
    for key3, value3 in dp[key][key2][3].items():
        mark=0
        if value3 in ['nsubj', 'nsubjpass']:
            if head == None:
                head=explore(dp, key, key3, 'subj')
            #print('h1:', head)
        elif value3 in ['advcl','prep','xcomp']:
            rel1=rel
            key4=key3
            #print(value3)
            #print(dp[key][key4])
            #print('not_okay:', [(key_,value_) for key_, value_ in dp[key][key4][3].items()])
            #while not(len(dp[key][key4][3]) ==1 and [(key_,value_) for key_, value_ in dp[key][key4][3].items()][0][1] in ['pobj', 'ccomp']):
            #print('hhhhhhhhhhhhhhhhhhhhhhhhhh')
            try:
                check= [(key_,value_) for key_, value_ in dp[key][key4][3].items()][0][1]
                #print([(key_,value_) for key_, value_ in dp[key][key4][3].items()])
                #print('kkkk:',check, key4)
                check_ind= check in check_list
            except:
                check_ind= True
            while not(check_ind):
                #print('okay:', [(key5,value5) for key5, value5 in dp[key][key4][3].items()])
                #print('hhh:', dp[key][key4])
                if dp[key][key4][1]=='VB':
                    mark==1
                    break
                #print('old_rel:',rel1)
                #rel1 = rel1 + ' ' + dp[key][key4][0]
                #print('new_rel:',rel1)
                #print('old_rel:',rel1)
                rel1 = rel1 + ' ' + dp[key][key4][0]
                #print('new_rel:',rel1)
                key4 = [(key5,value5) for key5, value5 in dp[key][key4][3].items()][0][0]
                #print('old_rel:',rel1)
                #rel1 = rel1 + ' ' + dp[key][key4][0]
                #print('new_rel:',rel1)
                
                try:
                    #print('hello')
                    check= [(key_,value_) for key_, value_ in dp[key][key4][3].items()][0][1]
                    check_ind= check in check_list
                except:
                    check_ind= True
            if 'mark' in dp[key][key4][3].values():
                mark=1
            pred=[]
            if mark==0:
                rel1 = rel1 + ' ' + dp[key][key4][0]
                #print('hex rel1:', rel1)
                for key_1, value_1 in  dp[key][key4][3].items():
                    if value_1 in ['pobj', 'ccomp', 'pcomp', 'dobj', 'advmod']:
                        pred.append(explore(dp, key, key_1))
            else:
                head=explore(dp, key, key4)
                #print(head)
                pred=[]
            
            #for key_1, value_1 in  dp[key][key4][3].items():
             #   if value_1 in ['pobj', 'ccomp', 'pcomp']:
              #      pred.append(explore(dp, key, key_1))
            for p in pred:
                trip_p.append((rel1, p))
        elif value3 in ['attr']:
            pred=explore(dp, key, key3)
            trip_a.append((rel,pred))
        elif value3 in ['dobj']:
            pred=explore(dp, key, key3)
            trip_d.append((rel,pred))
        elif value3 in ['pobj']:
            pred=explore(dp, key, key3)
            trip_c.append((rel,pred))
    #print(trip_a)
    #print(trip_p)
    #print(trip_c)
    if head != None:
        for r2, p2 in trip_p:
            trip.append((head, r2, p2))
        for r3, p3 in trip_c:
            trip.append((head, r3, p3))
        for r4, p4 in trip_d:
            trip.append((head, r4, p4))  
    for r1,p1 in trip_a:
        if head != None:
            trip.append((head, r1, p1))
        for r2, p2 in trip_p:
            trip.append((p1,r2,p2))
        for r3, p3 in trip_c:
            trip.append((p1,r3, p3))
        
    return (trip)
##################################################################
    #############################################
    ##############################
    
def rec_rec(head, rel1, trip_p, dp,key, key4, mark):
    trip_p1=[]
    pred=[]
    if dp[key][key4][1]=='VB':
        head=explore(dp, key, key4)
        #print(head)
        pred=[]
        return (trip_p, head)
    rel1 = rel1 + ' ' + dp[key][key4][0]
    if len(dp[key][key4][3]) > 0:
        check= [(key_,value_) for key_, value_ in dp[key][key4][3].items()]
        for k_1, v_1 in check:
            prev_rel=rel1
            if v_1 not in check_list:
                rec_rec(head, rel1, trip_p, dp,key, k_1, mark)
            rel1=prev_rel
            if 'mark' in dp[key][key4][3].values():
                mark=1
            pred=[]
            if mark==0:
                #print('hex rel1:', rel1)
                for key_1, value_1 in  dp[key][key4][3].items():
                    if value_1 in ['pobj', 'ccomp', 'pcomp', 'dobj', 'advmod']:
                        pred.append(explore(dp, key, key_1))
            else:
                head=explore(dp, key, key4)
                #print(head)
                pred=[]
    for p in pred:
        trip_p1.append((rel1, p))
    #print(trip_p)
    trip_p.extend(trip_p1)
    return (trip_p, head)
    

      
    



def do_process(dp,key,key2):
    trip=[]
    trip_a=[]
    trip_d=[]
    trip_p=[]
    trip_c=[]
    head= None
    rel=dp[key][key2][0]
    #print('hi:', dp[key])
    #print('rel:', rel)
    if 'neg' in dp[key][key2][3].values():
        rel= 'not' + ' ' + rel #handle negation
    for key3, value3 in dp[key][key2][3].items():
        mark=0
        if value3 in ['nsubj', 'nsubjpass']:
            if head == None:
                head=explore(dp, key, key3, 'subj')
            #print('h1:', head)
        elif value3 in ['advcl','prep','xcomp']:
            rel1=rel
            key4=key3
            #print(value3)
            
            trip_p, head = rec_rec(head, rel1, trip_p, dp,key, key4, mark)
        elif value3 in ['attr']:
            pred=explore(dp, key, key3)
            trip_a.append((rel,pred))
        elif value3 in ['dobj']:
            pred=explore(dp, key, key3)
            trip_d.append((rel,pred))
        elif value3 in ['pobj']:
            pred=explore(dp, key, key3)
            trip_c.append((rel,pred))
    #print(trip_a)
    #print(trip_p)
    #print(trip_c)
    if head != None:
        for r2, p2 in trip_p:
            trip.append((head, r2, p2))
        for r3, p3 in trip_c:
            trip.append((head, r3, p3))
        for r4, p4 in trip_d:
            trip.append((head, r4, p4))  
    for r1,p1 in trip_a:
        if head != None:
            trip.append((head, r1, p1))
        for r2, p2 in trip_p:
            trip.append((p1,r2,p2))
        for r3, p3 in trip_c:
            trip.append((p1,r3, p3))
    for r1,p1 in trip_d:
        #print(p1)
        for r2, p2 in trip_p:
            #print('hi')
            trip.append((p1,'be '+ r2,p2))
        for r3, p3 in trip_c:
            trip.append((p1,'be ' +r3, p3))
            
    return (trip)
##################################################################
    #############################################
    ##############################


def IE(dp):
    total_trip=[]
    for key in dp:
        for key2 in dp[key]:
            if dp[key][key2][1][:2]=='VB':
                process=False
                for key6, value6 in dp[key][key2][3].items():
                    if value6 in ['nsubj', 'nsubjpass']:
                        process= True
                    if  dp[key][key2][1]=='VB' and len(dp[key][key2][3])>=2 :
                        process= True
                if process:
                    trip= do_process(dp,key,key2)
                    total_trip.extend(trip)
    return (total_trip)


