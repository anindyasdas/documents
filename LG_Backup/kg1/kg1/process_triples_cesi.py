# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 17:08:49 2021

@author: Anindya
"""
# %%
import csv
import spacy
import json
import os
from stanfordcorenlp import StanfordCoreNLP
nlp=spacy.load("en_core_web_sm")


# %%

class ProcessTriples(object):
    """
    This class processes triple extracted from Manuals to generate file to be processed by cesi clusering
    """
    def __init__(self, c_file, t_file, verbose=True):
        self.cfile = c_file
        self.t_file = t_file
        self.o_file = os.path.abspath(os.path.join(os.path.dirname(self.t_file), 'data_out'))
        self.cnlp = StanfordCoreNLP(self.cfile, memory='8g', quiet =  not verbose)
        self.props = {'annotators': 'kbp,entitylink', 'pipelineLanguage': 'en'}
        self.read_triple_file(self.t_file)
        self.extract_info(self.o_file)
        self.write_to_file()
        
    def read_triple_file(self, f_path):
        """
        This function reads csv file and populates the following:
        id_triples : list of triples in id formats [(entity_id, rel_id, entity_id)...]
        id_to_triple: dictionary {id1:(head1,rel1,tail1),...}
        entity_to_id: mapping from entities to corresponsing id
        rel_to_id: mapping from rel to ids

        Parameters
        ----------
        f_path : string
            path to tab separated file containing the triples extracted from manual.

        Returns
        -------
        None.

        """
        with open(f_path, 'r', encoding='utf8') as f:
            csv_file=csv.reader(f, delimiter="\t")
            self.src = {}
            self.id_triples = []
            self.id_to_triple ={}
            triple_idx = 0 
            self.entity_to_id = {}
            self.id_to_entity = []
            entity_idx = 0
            self.rel_to_id = {}
            self.id_to_rel =[]
            rel_idx = 0
            #with open(data_path, 'w', encoding='utf8') as out_f:
            for line in csv_file:
                head = line[0].strip()
                tail = line[2].strip()
                pred = line[1].strip()
                triple = (head, pred, tail)
                if head not in self.entity_to_id:
                    entity_idx += 1
                    self.entity_to_id[head] = entity_idx
                    self.id_to_entity.append(head)
                if tail not in  self.entity_to_id:
                    entity_idx +=1
                    self.entity_to_id[tail] = entity_idx
                    self.id_to_entity.append(tail)
                if pred not in  self.rel_to_id:
                    rel_idx +=1
                    self.rel_to_id[pred] = rel_idx
                    self.id_to_rel.append(pred)
                if pred.lower() == "talks about":
                    if tail not in self.src:
                        self.src[tail] = [head]
                    else:
                        self.src[tail].append(head)
                triple_idx +=1
                self.id_to_triple[triple_idx] = triple
                self.id_triples.append((self.entity_to_id[head], self.rel_to_id[pred], 
                                        self.entity_to_id[tail]))
                
    def remove_article(self, string_inp):
        """
        

        Parameters
        ----------
        string_inp : string
            incoming string.

        Returns
        -------
        string_out : string
            article removed from the string

        """
        articles=['a', 'an', 'the']
        toks=[]
        for tok in string_inp.split():
            if tok.lower() not in articles:
                toks.append(tok)
        string_out= ' '.join(toks)
                
        return string_out
    
    def entity_link(self, item):
        """
        

        Parameters
        ----------
        item : string
            DESCRIPTION.

        Returns
        -------
        link : string
            the mapped entity from Wikipedia

        """
        annotated = self.cnlp.annotate(item, properties=self.props)
        #print('item:', item)
        try:
            result = json.loads(annotated)
        except:
            return None
        #print(result)
        e_mentions=result['sentences'][0]['entitymentions']
        #print(e_mentions)
        if len(e_mentions)==0:
            link = None
            return link
        else:
            all_links=[]
            for mention in e_mentions:
                #print(mention['text'].lower(), self.remove_article(item).lower())
                #print('mention:', mention)
                try:
                    if mention['text'].lower() == self.remove_article(item).lower():
                        all_links.append(mention['entitylink'])
                except:
                    pass
            if len(all_links)==0:
                link= None
            else:
                link = all_links[0]
        return link
    
    def extract_ontology(self, item, extraction):
        e_mentions=extraction['sentences'][0]['entitymentions']
        for mention in e_mentions:
            #print(mention['text'].lower(), remove_article(item).lower())
            #print('mention:', mention)
            if mention['text'].lower() == self.remove_article(item).lower():
                return mention['ner']
            
            
    def entity_kbp(self, triple):
        """
        ["darth vader", "be bear", "anakin skywalker"]

        Parameters
        ----------
        triple : tuple of strings (head, pred, tail)
            DESCRIPTION.

        Returns
        -------
        List
            KBP information.  [["PERSON", "per:parents", "PERSON"], ["PERSON", "per:parents", "PERSON"]]

        """
        head, pred, tail = triple[0].strip(), triple[1].strip(), triple[2].strip()
        item = " ".join([head, pred, tail])
        #print(item)
        annotated = self.cnlp.annotate(item, properties=self.props)
        #print('item:', item)
        try:
            result = json.loads(annotated)
        except:
            return []
        #print(result)
        kbp=result['sentences'][0]['kbp']
        #print(kbp)
        if len(kbp)==0:
            all_links = []
            return all_links
        else:
            all_links=[]
            for mention in kbp:
                if mention['subject'].lower() == self.remove_article(head).lower() and mention['object'].lower() == self.remove_article(tail).lower():
                    rel= mention['relation']
                    head_ont = self.extract_ontology(mention['subject'], result)
                    tail_ont = self.extract_ontology(mention['object'], result)
                    all_links.append([head_ont, rel, tail_ont])
                    
        return all_links
    
    def lemmatize_string(self, sen):
        doc = nlp(sen)
        lemma_sen = " ".join([token.lemma_ for token in doc])
        return lemma_sen
    
    def extract_info(self, data_path):
        with open(data_path, 'w', encoding='utf8') as out_f:
            #c=0
            for triple_id, triple_value in self.id_to_triple.items():
                if triple_value[0].strip() == '' or triple_value[2].strip() == '':
                    continue
                trip_dict={}
                entity_linking={}
                trip_dict["triple_norm"]=[self.lemmatize_string(item.lower()).strip() for item in triple_value]
                trip_dict["triple"] = list(triple_value)
                #print(triple)
                entity_linking["object"] = self.entity_link(triple_value[2])
                entity_linking["subject"] = self.entity_link(triple_value[0])
                trip_dict["entity_linking"] = entity_linking
                trip_dict["kbp_info"]= self.entity_kbp(triple_value)
                trip_dict["true_link"]={}
                src_sentences = []
                if triple_value[2] in self.src and triple_value[0] in self.src:
                    for item_1 in self.src[triple_value[2]]:
                        if item_1 in self.src[triple_value[0]]:
                            src_sentences.append(item_1)
                if not src_sentences:
                    src_sentences.append(" ".join(triple_value))
                trip_dict["src_sentences"] = src_sentences
                trip_dict["_id"] = int(triple_id)
                
                            
                
                #try:
                #    trip_dict["triple_norm"]=[lemmatize_string(item).strip() for item in triple]
                #except:
                #    print(c, triple)
                #c+=1
                #print(c)
                ##output is stored in JSON Lines file
                json.dump(trip_dict, out_f)
                out_f.write('\n')
                #print(trip_dict, file=out_f)
        return
    
    def write_to_file(self):
        self.eid_file = os.path.abspath(os.path.join(os.path.dirname(self.t_file), 'entity_to_id.txt'))
        with open(self.eid_file, 'w') as doc:
            print(len(self.entity_to_id), file= doc)
            for key, value in self.entity_to_id.items():
                print(key, '\t', value, file=doc)
        
        self.rid_file = os.path.abspath(os.path.join(os.path.dirname(self.t_file), 'rel_to_id.txt'))
        with open(self.rid_file, 'w') as docr:
            print(len(self.rel_to_id), file= docr)
            for keyr, valuer in self.rel_to_id.items():
                print(keyr, '\t', valuer, file=docr)
            
# %%    
    
    
    
    
    
if __name__=="__main__":
    corenlp_path = '/Users/Anindya/Desktop/BackUP/corenlp/stanford-corenlp-4.2.0'
    triple_file = '/Users/Anindya/Desktop/ref_ops_merged.txt'
    
    corenlp_path = input("Enter Core NLP Path")
    triple_file = input("Enter file containing tripes")
    process_triples = ProcessTriples(corenlp_path, triple_file)