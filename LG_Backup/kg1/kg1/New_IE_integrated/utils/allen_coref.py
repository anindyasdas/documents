# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 11:12:35 2021

@author: Anindya
"""

from allennlp.predictors.predictor import Predictor
import allennlp_models.tagging
import re

class AllenCoref:
    """
    class is used to output the coreference resolved text, for any incoming text
    containing multiple sentences
    """
    def __init__(self):
        self.predictor = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2020.02.27.tar.gz")
        
    def coreference_resolved(self, text):
        """
        Predicted output has the following forms
        
        
        """
        self.predicted = self.predictor.predict(document = text)
        document = self.predicted['document']
        coref_cluster = self.predicted['clusters']
        document_list = self.coref_resolver(document, coref_cluster)
        doc_string = self.process_string(document_list)
        return doc_string

    """
    def coref_resolver(self, document_list, cluster_list):
        for cluster in cluster_list:
             coreferring_noun_phrase_id = cluster[0]
             for proform_id in cluster[1:]:
                document_list[proform_id[0]:proform_id[1] + 1] = document_list[coreferring_noun_phrase_id[0] : coreferring_noun_phrase_id[1] +1]
        return document_list
    """
    
    
    
    def coref_resolver(self, document_list, cluster_list):
        """
        This function relaces the proform with np coref while adjusting the length difference 
        between the items to be replaced and the replacement
        
        """
        cluster_dict = {}
        start_end_dict = {}
        new_doc =[]
        for cluster in cluster_list:
            coreferring_noun_phrase_id = cluster[0]
            for proform_id in cluster[1:]:
                cluster_dict[tuple(proform_id)] = coreferring_noun_phrase_id
                start_end_dict[proform_id[0]] = proform_id[1]
        idx = 0
        while idx < len(document_list):
            if idx in start_end_dict:
                end= start_end_dict[idx]
                key = (idx, end)
                coref_np = cluster_dict[key]
                new_doc.extend(document_list[coref_np[0]:coref_np[1]+1])
                idx = end +1
            else:
                new_doc.append(document_list[idx])
                idx +=1
        return new_doc
    
    def process_string(self, doc_list):
        doc_string = " ".join(doc_list)
        # replacing the multiple in-between spaces with one space
        doc_string = re.sub('\s{2,}', ' ', doc_string)
        # remove the space around the '-' character
        doc_string = re.sub('\s*-\s*', '-', doc_string)
        #remove space before any punctuation
        doc_string = re.sub(r'\s([?.,\'!"](?:\s|$))', r'\1', doc_string)
        #remove spaces after ['"] 
        doc_string = re.sub(r'([\'"])\s', r'\1', doc_string)

        return doc_string
    
    
if __name__ == "__main__":
    coref_module= AllenCoref()
    while True:
        text = input("Enter the text\n")
        
        print("coref resolved: \n", coref_module.coreference_resolved(text))