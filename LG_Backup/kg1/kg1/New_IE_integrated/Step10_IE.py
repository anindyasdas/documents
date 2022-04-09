# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 18:03:29 2020

@author: Anindya
"""
from textblob import TextBlob
from allennlp.predictors.predictor import Predictor
#import allennlp_models.structured_prediction
import nltk
#predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz")
from string import punctuation
import subprocess
import pandas
import io
import tempfile
import json
import re
import os
from copy import deepcopy
from nltk.corpus import stopwords
from utils.dependency_parse_ie import *
from pyopenie import OpenIE5
lib_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
print(lib_path)
sys.path.append(lib_path)
from utils import allen_coref, Special_consitituency_extractor_v3, imperative_to_declarative_v1
from utils import complex_to_simple_rel1
#from utils import coreference_engine1
from utils.utility_functions import *

coref_resolver = allen_coref.AllenCoref()
clausal_extractor = complex_to_simple_rel1.ClausalRelExtractor()
print("Coref Loaded")
te = Special_consitituency_extractor_v3.TripleExtractorTO()
it = Special_consitituency_extractor_v3.TripleExtractorIT()
fr = Special_consitituency_extractor_v3.TripleExtractorFOR()
imp_to_dec = imperative_to_declarative_v1.ImperativeToDeclarative()

extractor = OpenIE5('http://localhost:8000')

stop_words = set(stopwords.words('english'))

other_list=['yet', 'first', 'available', 'necessary',  'approximately',
            'initially', 'initial', 'open', 'closed', 'away', 'frequently',
            'use', 'full', 'easy', 'difficult']
stop_words= list(stop_words)+ other_list
#stanford_path=input("Enter StanfordCorenlp Path:\n")
#coref_engine = coreference_engine1.CoreferenceEngine(stanford_path) #Doing so, failing to do so




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
    sentences=list()
    blob_object=TextBlob(text)
    for s in blob_object.sentences:
        rs=re.sub(u"(\u2018|\u2019)", "'", s.raw)
        sentences.append(rs)
    return sentences


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




        






        
    
        


        
        
        



        


def extract_clausal_rel(sentences, simple_sentences, triple):
    new_sentences=[] #collection of sentences
    for s in sentences:
        cl , rel= clausal_extractor.find_clauses(s)
        if cl==-1:
            continue
        elif len(cl)==3 and '' not in [cl[1], cl[2]] :
            for tail in [cl[1], cl[2]]:
                tail=process_string(tail)
                triple.append((s,'talks about', tail))
            triple.extend(rel)
            new_sentences.extend([cl[1], cl[2]])
        elif len(cl)==2 and '' not in [cl[0], cl[1]] :
            for tail in [cl[0], cl[1]]:
                tail=process_string(tail)
                triple.append((s,'talks about', tail))
            new_sentences.extend([cl[0], cl[1]])
        elif len(cl)==1:
            imp_s, tr= imp_to_dec.convert_sentence(s)
            cl1=re.sub('\W+',' ', imp_s).lower()
            cl2=re.sub('\W+',' ', process_string(s)).lower()
            if cl1 != cl2:
                triple.append((s,'paraphrase', imp_s))
            else:
                imp_s=s
                
            if tr[0] !="" and tr[1]!="" and tr[2]!="":
                triple.append((imp_s, 'talks about', tr[0]))
                triple.append((imp_s, 'talks about', tr[2]))
                triple.append(tr)
                
            simple_sentences.extend([imp_s])
    return (triple, simple_sentences, new_sentences)

def extract_clausal_rel1(sentences, triple):
    new_sentences=[] #collection of sentences
    for s in sentences:
        cl , rel= clausal_extractor.find_clauses(s)
        if cl==-1:
            continue
        elif len(cl)==3:
            triple.extend(rel)
            new_sentences.extend([cl[1], cl[2]])
        else:
            new_sentences.extend(cl)
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
                #print('I di not find choice')
                print(key)
                triple_dict[key]=[(arg1, rel, arg2)]
    #print('triple_dict:', triple_dict)
    #print(new_sentences)
    print('###################################################')
    #print(triple_dict)
    print('###################################################')
    #triple_dict=sentence_level_IE_dep(triple_dict)
    #print(triple_dict)
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
    print(' Start server java -Xmx10g -XX:+UseConcMarkSweepGC -jar openie-assembly-5.0-SNAPSHOT.jar -s -b --httpPort 8000')
    print('new_sentences:', new_sentences)
    #f = tempfile.NamedTemporaryFile(mode = 'w+t') #temporary file creation
    triple_dict={}
    for sen in new_sentences:
        sen = process_string(sen)
        print(sen)
        #if True:
        try:
            extractions= extractor.extract(sen)
            #print('extractions:', extractions)
            if sen not in triple_dict:
                triple_dict[sen]=[]
            t=set()
            for item in extractions:
                #print('ITEM:', item)
                c= item['confidence']
                arg1=item['extraction']['arg1']['text'].strip()
                arg1=process_string(arg1)
                rel=item['extraction']['rel']['text'].strip()
                arg2s=item['extraction']['arg2s']
                context=item['extraction']['context']
                if context == None:
                    for arg2_item in arg2s:
                        #print('arg2:', arg2_item['text'])
                        t.add((arg1, rel, process_string(arg2_item['text'].strip())))
            triple_dict[sen].extend(list(t))
        except:
        #else:
            pass
        
   
    print('###################################################')
    print(triple_dict)
    print('###################################################')
    #triple_dict=sentence_level_IE_dep(triple_dict)
    #print(triple_dict)
    #print('###################################################')
    #for key1, value1 in triple_dict.items():
     #   triple.extend(value1)
    #print('type(triple):', type(triple))
    #print('triple', triple)
    #triple=list(set(triple))
    return (triple_dict)



def concept_relations0(triple):
    
    
    new_triple=[]
    for item in triple:
        if type(item[2])==list:
            text='This section talks about ' + item[0].strip() + '.'
            for i in item[2]:
                text=text + ' ' + i
            text=text.strip()
            print("0 text:", item[2])
            print("1 text:", text)
            text = coref_resolver.coreference_resolved(text)
            print("2 coref text:",text)
            sentences= split_sentences(text)
            triple_c=[]
            print("sentences:", sentences)
            print("sentences[1:]", sentences[1:])
            triple_c, new_sentences =extract_clausal_rel(sentences[1:], triple_c)
            print('triple_c:', triple_c)
            print('new sentences:', new_sentences)
            for s in new_sentences:
                if s.strip() != '':
                    new_triple.append((item[2],'talks about', s))
            new_triple=new_triple+triple_c
            triple_dict= sentence_level_IE5(new_sentences)
            #triple_dict= sentence_level_IE(new_sentences)
            for key1, value1 in triple_dict.items():
                for v in value1:
                    new_triple.append((key1, 'talks about', v[0]))
                    new_triple.append((key1, 'talks about', v[2]))
                new_triple.extend(value1)
    triple= triple+ new_triple
    return (triple)



def concept_relations1(triple):
    property_dict = {}
    
    
    new_triple=[]
    for idx in range(len(triple)):
        item = triple[idx]
        if type(item[2])==list:
            text='This section talks about ' + item[0].strip() + '.'
            for i in item[2]:
                text=text + ' ' + i
            text=text.strip()
            print("0 text:", item[2])
            print("1 text:", text)
            #########################
            named_item = ' '.join(item[:-1])
            property_dict[named_item] = item[2]
            new_item = (item[0], item[1], named_item)
            triple[idx] = new_item 
            #f_dict = open('property.json', 'w', encoding ='utf8')
            #json.dump(property_dict, f_dict, indent =6)
            #f_dict.close()
            ####################
            text = coref_resolver.coreference_resolved(text)
            print("2 coref text:",text)
            sentences= split_sentences(text)
            triple_c=[]
            print("sentences:", sentences)
            print("sentences[1:]", sentences[1:])
            triple_c, new_sentences =extract_clausal_rel(sentences[1:], triple_c)
            print('triple_c:', triple_c)
            print('new sentences:', new_sentences)
            for s in new_sentences:
                if s.strip() != '':
                    new_triple.append((new_item[2],'talks about', s))
            new_triple=new_triple+triple_c
            triple_dict= sentence_level_IE5(new_sentences)
            #triple_dict= sentence_level_IE(new_sentences)
            for key1, value1 in triple_dict.items():
                for v in value1:
                    tup_1 = (key1, 'talks about', v[0])
                    tup_2 = (key1, 'talks about', v[2])
                    new_triple.append(tup_1)
                    new_triple.append(tup_2)
                new_triple.extend(value1)
    triple= triple+ new_triple
    f_dict = open('property.json', 'w', encoding ='utf8')
    json.dump(property_dict, f_dict, indent =6)
    f_dict.close()
    return (triple)


def concept_relations(triple):
    property_dict = {}
    sentence_list='sentence_list'
    sl_id=0
    
    
    new_triple=[]
    for idx in range(len(triple)):
        item = triple[idx]
        if type(item[2])==list:
            sl_id+=1
            text='This section talks about ' + item[0].strip() + '.'
            for i in item[2]:
                text=text + ' ' + i
            text=process_string(text.strip())
            print("0 text:", item[2])
            print("1 text:", text)
            #########################
           #named_item = ' '.join(item[:-1])
            named_item = sentence_list + '_' + str(sl_id)
            property_dict[named_item] = item[2]
            new_item = (item[0], item[1], named_item)
            #new_item = (item[0], item[1], item[2])
            triple[idx] = new_item 
            
            ####################
            text = coref_resolver.coreference_resolved(text)
            text = process_string(text)
            print("2 coref text:",text)
            ###################Integrate coref engine doing so, following to do so
            #text = coref_engine.cp_postprocessing(text) 
            text = process_string(text)
            print("2 coref engine text:",text)
            #########################################################
            sentences= split_sentences(text)
            triple_c=[]
            print("sentences:", sentences)
            print("sentences[1:]", sentences[1:])
            new_sentences =[]
            for s in sentences[1:]:         
                if s.strip() != '':
                    beg = s.strip().split()[0].lower()
                    if beg in ['it']:
                        extracted= it.convert_sent(s)
                        new_sentences.append(extracted)
                        new_triple.append((new_item[2],'talks about',extracted))
                    elif beg in ['to']:
                        trip_n= te.extract_triple(s)
                        extracted=s.strip()
                        if trip_n !="":
                            new_triple.append((new_item[2],'talks about',extracted))
                            new_triple.append((extracted, 'talks about', trip_n[0]))
                            new_triple.append((extracted, 'talks about', trip_n[2]))
                            new_triple.append(trip_n)
                    elif beg in ['for']:
                        extracted= fr.convert_sent(s)
                        new_sentences.append(extracted)
                        new_triple.append((new_item[2],'talks about',extracted))
                    else:
                        extracted=s.strip()
                        new_sentences.append(extracted)
                        new_triple.append((new_item[2],'talks about',extracted))
            simple_sentences =[]
            while new_sentences:
                triple_c, simple_sentences, new_sentences =extract_clausal_rel(new_sentences, simple_sentences, triple_c)
                print('triple_c:', triple_c)
                print('new sentences:', new_sentences)
            
            new_triple=new_triple+triple_c
            triple_dict= sentence_level_IE5(simple_sentences)
            #triple_dict= sentence_level_IE(simple_sentences)
            for key1, value1 in triple_dict.items():
                for v in value1:
                    tup_1 = (key1, 'talks about', v[0])
                    tup_2 = (key1, 'talks about', v[2])
                    new_triple.append(tup_1)
                    new_triple.append(tup_2)
                new_triple.extend(value1)
    triple= triple+ new_triple
    f_dict = open('property.json', 'w', encoding ='utf8')
    json.dump(property_dict, f_dict, indent =6)
    f_dict.close()
    new_triple = []
    for item in triple:
        if item not in new_triple and item[0].lower() not in stop_words and item[2].lower() not in stop_words: 
            new_triple.append(item)
    return (new_triple)






    






if __name__=="__main__":
    filename=input("Enter the input file name:")
    outname=input("Enter the output file name:")
    f=open(filename, 'r',encoding='latin1')
    triple=[]
    for line in f:
        triple.append(eval(line.strip()))
    triple= concept_relations(triple)
    file= open(outname, 'w')
    for item in triple:
        print(item[0],'\t',item[1],'\t',item[2],file=file)      
    file.close()
    
                
        
