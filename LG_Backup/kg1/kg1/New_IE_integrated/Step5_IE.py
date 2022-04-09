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
from utils import allen_coref

coref_resolver = allen_coref.AllenCoref()
print("Coref Loaded")

extractor = OpenIE5('http://localhost:8000')



#relations=['description', 'is_for', ]
discourse_connectives1=['before', 'then', 'till', 'until', 'after', 'once', 'meanwhile', \
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
#Condition=['if', 'when']
Condition=['if']
Contrast=['but', 'however', 'by contrast', 'in contrast', 'on the other hand', 'on the contrary']
Concession=['although']
Conjunction=['and', 'also']
Instantiation=['for example', 'for instance']
Restatement=['in other words']
Alternative=['or', 'unless', 'as an alternative', 'otherwise']
Exception_rel=['except']



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
        item = item.replace(' - ','-') #remove leading punctuation due to clausal break up
        clauses[i]= item.strip(punctuation).strip()
        
    return clauses
    

def pattern_3_process1(tree):
    
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
                s= pattern_3_process(subtree)
    return (s)


def pattern_3_process(tree, s):
    
    #print('the tree:', tree)
    for subtree in tree:
        #print('subtree:', subtree)
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
    s=[]
    #print('pattern 3:', tree)
    #for pos in tree.treepositions():
        #print('pos:',pos, tree[pos])
    clauses=[]
    #print('before:', tree)
    s= pattern_3_process(tree, s)
    #print('after',tree)
    #for pos in tree.treepositions():
        #print('pos:',pos, tree[pos])
    #print('s:', s, len(s))
    #print('s[0].treeposition()', s[0].treeposition())
    
    if len(s)==1 and type(s[0])== nltk.tree.ParentedTree: #change
        #print(s[0]==tree)
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
    s=[]
    clauses=[]
    
    for subtree in tree:
        if subtree.label() in ['S']:
            s.append(subtree)
        elif subtree.label() in ['CC']:
            s.append(subtree)
    
        
    
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
        return (-1, -1)
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
    return (clauses, discourse_rel(clauses))
        


def extract_clausal_rel(sentences, triple):
    new_sentences=[] #collection of sentences
    for s in sentences:
        cl , rel= find_clauses(s)
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
        #else:
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
            text='This section talks about ' + item[0].strip() + '.'
            for i in item[2]:
                text=text + ' ' + i
            text=text.strip()
            text = coref_resolver.coreference_resolved(text)
            sentences= split_sentences(text)
            triple_c=[]
            triple_c, new_sentences =extract_clausal_rel(sentences[1:], triple_c)
            print('triple_c:', triple_c)
            print('new sentences:', new_sentences)
            for s in new_sentences:
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



                
        
