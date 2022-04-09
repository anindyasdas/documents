# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 18:03:29 2020

@author: Anindya
"""
from textblob import TextBlob
from allennlp.predictors.predictor import Predictor
#import allennlp_models.structured_prediction
import nltk
predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz")
from string import punctuation
import subprocess
import pandas
import io
import tempfile
import json
import re
from utils.dependency_parse_ie import *
from pyopenie import OpenIE5
extractor = OpenIE5('http://localhost:8000')



#relations=['description', 'is_for', ]
discourse_connectives=['if', 'when']

def get_extraction(input_text):
    """ This is python Wrapper to use java based OLLIE .Will take an input file and use ollie to perform verb extration. Returns a json containing all the extraction information.
    input_text - The file name, or text to perform extraction on. 
    
    """
    
        
    to_extract = input_text
    sp = subprocess.Popen(['java', 
                           '-Xmx512m', 
                           '-jar', 
                           'ollie-app-latest.jar', 
                           '--output-format', 
                           'tabbed', 
                           to_extract], 
                           stdout=subprocess.PIPE)
    out = sp.stdout.read().decode('utf-8')
    
    #print('out:', out)
    
    # Using the StringIO method to set 
    # as file object. Now we have an  
    # object file that we will able to 
    # treat just like a file.
    
    data_frame = pandas.read_csv(io.StringIO(out), sep='\t')
    
    #print('data_frame:', data_frame)
    
    
    # Orient the data frame by records
    output = data_frame.to_json(orient = 'records')
    #output1 = data_frame.to_json(orient = 'split')
    #output2 = data_frame.to_json(orient = 'index')
    #print('output:',output)
    #print('output1:',output1)
    #print('output2:',output2)
        
    return output

def split_sentences(text):
    '''This function takes a block of text and tokenizes it into sentences,
    returns a list of sentences, Textblob is considered better than other tokenizers
    '''
    sentences=set()
    blob_object=TextBlob(text)
    for s in blob_object.sentences:
        rs=re.sub(u"(\u2018|\u2019)", "'", s.raw)
        sentences.add(rs)
    return (list(sentences))


def extract_basic_rel(input_data, triple):
    '''This method extracts the designed relations defined by dictionary and store in triple
    format in a tupple and return as list of tuples, 
    Each key of the dictionary is either an entity or a relation
    {Entity1:{Rel1:{Entity12:{Rel11:Entity13}},Rel2:{Entity21:{Rel21:Entity23}} }}
    output: (Entity1, Rel1, Entity12), (Entity12,Rel11,Entity13),
    (Entity1,Rel2,Entity21), (Entity21,Rel21,Entity23)'''
    print('########### Ectracting basic Relations  ########')
    
    for key, values in input_data.items():
        e1=key
        for key1,values1 in values.items():
            rel=key1
            if type(values1)==list:
                if len(values1)>=1:
                    e2=values1
                    triple.append((e1,rel,e2))
            else:
                for key2,values2 in values1.items():
                    e2=key2
                    triple.append((e1,rel,e2))
                triple=extract_basic_rel(values1, triple)
            
                   #triple=extract_basic_rel(values1, triple)
    return (triple)

def traverse_tree(tree, s):
    '''
    This function takes nltk parented tree as input recursively, the subtree with 'SBAR' is returned
    '''
    #print("tree:", tree, 'label: ', tree.label(), len(tree))
    if tree.label() in ['SBAR']:
        s.append(tree)
        return (s)
    for subtree in tree:
        if type(subtree) == nltk.tree.ParentedTree:
            traverse_tree(subtree, s)
    return (s)


def find_clauses(sent):
    '''This function takes sentence as input return clauses, first one is subordinate, secoding one is principle
    if no such break up is possible it returns original sentence
    '''
    print('####### Extracting Clauses ################')
    #print(sent)
    prediction= predictor.predict(sentence=sent)
    #print(prediction['trees'])
    try:
        sent_tree=nltk.tree.ParentedTree.fromstring(prediction['trees'])
    except:
        return (-1)
    clauses=[]
    s=[]
    x=traverse_tree(sent_tree,s)
    if len(x)==0:
        clauses.append(' '.join(sent_tree.leaves()))
        
    elif type(x[0])== nltk.tree.ParentedTree:
        flag=False
        new_leaves=[]
        leaves_list=x[0].leaves()
        for l in leaves_list:
            if l.lower() in discourse_connectives:
                flag= True
            else:
                new_leaves.append(l)
        if flag:
            clauses.append(' '.join(new_leaves))
            del sent_tree[x[0].treeposition()]
        clauses.append(' '.join(sent_tree.leaves()))
    else:
        clauses.append(' '.join(sent_tree.leaves()))
    return (clauses)


def extract_clausal_rel(sentences, triple):
    new_sentences=[] #collection of sentences
    for s in sentences:
        cl= find_clauses(s)
        if cl==-1:
            continue
        elif len(cl)==2:
            cl1=cl[1].lstrip(punctuation).strip() #remove leading punctuation due to clausal break up
            cl1=cl1.replace(' - ','-')
            cl0=cl[0].replace(' - ','-')
            triple.append((cl0, 'Action', cl1))
            new_sentences.extend([cl0, cl1])
        else:
            cl0=cl[0].replace(' - ','-')
            new_sentences.extend([cl0])
    return (triple, new_sentences)


def sentence_level_IE_dep(triple_dict):
    nlp_d  = load_spacy_model()
    for key, value in triple_dict.items():
        if len(value)==0:
            sentToWordInfo = processSpaCy(key, nlp_d)
            triple_dict[key]=IE(sentToWordInfo)
            print('triple_dict[key]:', triple_dict[key])
    return (triple_dict)

def sentence_level_IE(new_sentences):
    '''This function process sends the broken sentences to python wrapper for ollie
    if no relations are returned then sent to dependency parsing 
    '''
    #print('new_sentences:', new_sentences)
    f = tempfile.NamedTemporaryFile(mode = 'w+t') #temporary file creation
    triple_dict={}
    for item in new_sentences:
        triple_dict[item]=[]
        f.write(item+'\n')
    f.seek(0)#put the cursor to the beginning of the file
    
    resp=get_extraction(f.name)
    resp=eval(resp) #string is returned , so converted to list
    #print('response is:', resp)
    for item in resp:
        #print(item)
        key=item['text']
        arg1=item['arg1']
        rel=item['rel']
        arg2=item['arg2']
        confidence= item['confidence']
        if confidence >= 0.62:
            if key in triple_dict:
                triple_dict[key].append((arg1, rel, arg2))
            else:
                print('I di not find choice')
                print(key)
                triple_dict[key]=[(arg1, rel, arg2)]
    #print('triple_dict:', triple_dict)
    #print(new_sentences)
    print('###################################################')
    print(triple_dict)
    print('###################################################')
    triple_dict=sentence_level_IE_dep(triple_dict)
    print(triple_dict)
    print('###################################################')
    #for key1, value1 in triple_dict.items():
     #   triple.extend(value1)
    #print('type(triple):', type(triple))
    #print('triple', triple)
    #triple=list(set(triple))
    return (triple_dict)
    
    #return (triple)
    
    
def sentence_level_IE5(new_sentences):
    '''This function process sends the broken sentences to python wrapper for ollie
    if no relations are returned then sent to dependency parsing 
    '''
    #print('new_sentences:', new_sentences)
    #f = tempfile.NamedTemporaryFile(mode = 'w+t') #temporary file creation
    triple_dict={}
    for sen in new_sentences:
        #print(sen)
        try:
            extractions= extractor.extract(sen)
            if sen not in triple_dict:
                triple_dict[sen]=[]
            t=set()
            for item in extractions:
            #print('ITEM:', item)
                c= item['confidence']
                arg1=item['extraction']['arg1']['text']
                rel=item['extraction']['rel']['text']
                arg2s=item['extraction']['arg2s']
                context=item['extraction']['context']
                if context == None:
                    for arg2_item in arg2s:
                        #print('arg2:', arg2_item['text'])
                        t.add((arg1, rel, arg2_item['text']))
            triple_dict[sen].extend(list(t))
        except:
            pass
        
   
    print('###################################################')
    print(triple_dict)
    print('###################################################')
    #triple_dict=sentence_level_IE_dep(triple_dict)
    print(triple_dict)
    print('###################################################')
    #for key1, value1 in triple_dict.items():
     #   triple.extend(value1)
    #print('type(triple):', type(triple))
    #print('triple', triple)
    #triple=list(set(triple))
    return (triple_dict)

def concept_relations(triple):
    new_triple=[]
    for item in triple:
        if type(item[2])==list:
            text=''
            for i in item[2]:
                text=text + ' ' + i
            text=text.strip()
            sentences= split_sentences(text)
            triple_c=[]
            triple_c, new_sentences =extract_clausal_rel(sentences, triple_c)
            for s in new_sentences:
                new_triple.append((item[2],'talks about', s))
            new_triple=new_triple+triple_c
            triple_dict= sentence_level_IE5(new_sentences)
            for key1, value1 in triple_dict.items():
                for v in value1:
                    new_triple.append((key1, 'talks about', v[0]))
                    new_triple.append((key1, 'talks about', v[2]))
                new_triple.extend(value1)
    triple= triple+ new_triple
    return (triple)
            
    



triple=[]
f=open('ops.json','r',encoding='utf8')
safety_ins= json.load(f)
f.close()
triple=extract_basic_rel(safety_ins,triple)
file= open('OPS_step1.txt', 'w', encoding='utf8')
for item in triple:
    print(item[0],'\t',item[1],'\t',item[2],file=file)      
file.close()
triple= concept_relations(triple)

file= open('OPS_step3.txt', 'w', encoding='utf8')
for item in triple:
    print(item[0],'\t',item[1],'\t',item[2],file=file)      
file.close() 



                
        
