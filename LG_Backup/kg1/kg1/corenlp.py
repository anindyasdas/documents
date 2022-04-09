# -*- coding: utf-8 -*-
"""
Created on Thu Feb  4 11:06:29 2021

@author: Anindya


import json
from stanfordcorenlp import StanfordCoreNLP

stanford_core_nlp_path='/Users/Anindya/Desktop/stanford-corenlp-4.2.0'
stanford_core_nlp_path='./stanford-corenlp-4.2.0'
verbose= True
doc='India, officially the Republic of India, is a country in South Asia. It is the second-most populous country, the seventh-largest country by land area, and the most populous democracy in the world.'

nlp = StanfordCoreNLP(stanford_core_nlp_path, memory='8g', quiet =  not verbose)
#declare memory else it takes a lot of time might end up with outof memory error
props = {'annotators': 'coref', 'pipelineLanguage': 'en'}
#for entitylink download additional jar English (KBP) and put inside the path folder containing jar files
#for other anguages as well download the jar file and put inside the path folder eg. stanford-corenlp-4.2.0
props = {'annotators': 'entitylink', 'pipelineLanguage': 'en'}
annotated = nlp.annotate(doc, properties=props)
result = json.loads(annotated)



for item in result['sentences'][0]['entitymentions']:
    print(item['text'], item['entitylink']) #for only ner
    
##eg. output:
'''
India India
Republic of India India
South Southern_United_States
Asia Asia
'''


for item in result['sentences'][0]['tokens']:
    print(item['originalText'],item['entitylink']) #for each tokens
    
'''
India India
, O
officially O
the O
Republic India
of India
India India
, O
is O
a O
country O
in O
South Southern_United_States
Asia Asia
. O
'''

dd={}
for item in y:
    annotated = nlp.annotate(item, properties=props)
    result = json.loads(annotated)
    dd[item]=result['sentences'][0]['entitymentions']
new_dd={}
for keys, values in dd.items():
    
    if len(values)==0:
        new_dd[keys]=None
    else:
        l=[]
        for j in values:
            try:
                l.append(j['entitylink'])
            except:
                pass
        if len(l)==0:
            l= None
        new_dd[keys]=l
"""      
        
import csv
import spacy
import json
from stanfordcorenlp import StanfordCoreNLP
nlp=spacy.load("en_core_web_sm")
f_path = './IntegratedX.txt'
data_path = './data.txt'
stanford_core_nlp_path = './corenlp/stanford-corenlp-4.2.0'
verbose = True
props = {'annotators': 'kbp,entitylink', 'pipelineLanguage': 'en'}
enlp = StanfordCoreNLP(stanford_core_nlp_path, memory='8g', quiet =  not verbose)



def remove_article(s):
    articles=['a', 'an', 'the']
    toks=[]
    for tok in s.split():
        if tok.lower() not in articles:
            toks.append(tok)
    string1= ' '.join(toks)
            
    return string1

def entity_link(item):
    annotated = enlp.annotate(item, properties=props)
    #print('item:', item)
    try:
        result = json.loads(annotated)
    except:
        return None
    #print(result)
    e_mentions=result['sentences'][0]['entitymentions']
    print(e_mentions)
    if len(e_mentions)==0:
        link = None
        return link
    else:
        all_links=[]
        for mention in e_mentions:
            print(mention['text'].lower(), remove_article(item).lower())
            #print('mention:', mention)
            try:
                if mention['text'].lower() == remove_article(item).lower():
                    all_links.append(mention['entitylink'])
            except:
                pass
        if len(all_links)==0:
            link= None
        else:
            link = all_links[0]
    return link

def extract_ontology(item, extraction):
    e_mentions=extraction['sentences'][0]['entitymentions']
    for mention in e_mentions:
        #print(mention['text'].lower(), remove_article(item).lower())
        #print('mention:', mention)
        if mention['text'].lower() == remove_article(item).lower():
            return mention['ner']
    

def entity_kbp(triple):
    head, pred, tail = triple[0].strip(), triple[1].strip(), triple[2].strip()
    item = " ".join([head, pred, tail])
    print(item)
    annotated = enlp.annotate(item, properties=props)
    #print('item:', item)
    try:
        result = json.loads(annotated)
    except:
        return []
    print(result)
    kbp=result['sentences'][0]['kbp']
    print(kbp)
    if len(kbp)==0:
        all_links = []
        return all_links
    else:
        all_links=[]
        for mention in kbp:
            if mention['subject'].lower() == remove_article(head).lower() and mention['object'].lower() == remove_article(tail).lower():
                rel= mention['relation']
                head_ont = extract_ontology(mention['subject'], result)
                tail_ont = extract_ontology(mention['object'], result)
                all_links.append([head_ont, rel, tail_ont])
                
    return all_links





    


def lemmatize_string(sen):
    doc = nlp(sen)
    lemma_sen = " ".join([token.lemma_ for token in doc])
    return lemma_sen



def create_triple():

    with open(f_path, 'r', encoding='utf8') as f:
        x=csv.reader(f, delimiter="\t")
        triples=[]
        triples1=[]
        #with open(data_path, 'w', encoding='utf8') as out_f:
        for line in x:
            triples1.append(line)
            head = line[0].strip()
            tail = line[2].strip()
            pred = line[1].strip()
            trip_dict={}
            #if tail == 'approximately 6 to 8 12-16 oz':
             #   print(head)
            try:
                #print('hi', line)
                head1=eval(head)
            except:
                head1=head
            
            try:
                #print('hi', line)
                tail1=eval(tail)
            except:
                tail1=tail
                #pass
            if type(head1) == list or type(tail1) == list:
                continue
            else:
                #print('JJJJJ')
                triples.append((head, pred, tail))
                #print(type(line[2]))
                #trip_dict["triple_norm"]=[lemmatize_string(item) for item in line]
                #print(trip_dict, file=out_f)
    return triples

def extract_info(triples):
    with open(data_path, 'w', encoding='utf8') as out_f:
        c=0
        for triple in triples:
            if triple[0].strip() == '' or triple[2].strip() == '':
                continue
            trip_dict={}
            entity_linking={}
            trip_dict["triple_norm"]=[lemmatize_string(item.lower()).strip() for item in triple]
            trip_dict["triple"] = list(triple)
            print(triple)
            entity_linking["object"] = entity_link(triple[2])
            entity_linking["subject"] = entity_link(triple[0])
            trip_dict["entity_linking"] = entity_linking
            trip_dict["kbp_info"]= entity_kbp(triple)
            trip_dict["true_link"]={}
            
            #try:
            #    trip_dict["triple_norm"]=[lemmatize_string(item).strip() for item in triple]
            #except:
            #    print(c, triple)
            c+=1
            print(c)
            print(trip_dict, file=out_f)
             
        
        
        

            
        
    
    
