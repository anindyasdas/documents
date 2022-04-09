# -*- coding: utf-8 -*-
"""
Created on Mon May 10 18:51:40 2021

@author: anindya06.das
"""

import logging as logger
import json
import re
from copy import deepcopy


BOOKINFO="bookinfo"
PRODUCTNAME="productname"
CHAPTER="chapter"
TITLE="TITLE"
OPERATION="사용하기"
INSTALLATION="설치하기"
MAINTENANCE="관리하기"
BOOK="book"
BUYERMODEL="buyermodel"
PARTNUMBER="partnumber"


key_words_dict={"Fridge & Freezer":"냉장고 및 냉동고",
"WASHING MACHINE": "세탁기",
"summary":"요약",
"description":"설명",
"procedure":"절차",
"steps":"단계",
"caution":"주의",
"warning":"경고",
"have features":"특징"

}

TABLE_FORMATING=["세탁코스 (최대용량)", "세탁 코스", "최대 세탁 용량", '명칭']
#if top left contains these keywords tables with only one row header will be formatted
#as {main_heading{row_heading:{col_heading:{data}}}} top row and left column are hedings
#main_heading is top_left
#else tables will be formatted as {column_heading:data} only left most row is heading
SIMPLE_REL_LIST=["사용하기", "청소하기", "사용하기 전 알아두기", "세탁 전",
                 "세탁 후", "변경하기", "설정하기", "설치하기", "제거하기", 
                 "연결하기", "분리하기",
                 "해결하기", "관리하기"]

CONJOINED_REL_LIST=["분리/조립하기", "설정/해제하기"]
SPECIAL=["Turning"]
HOWTO=["How to"] #starting with -->how to
RELATION_LIST= CONJOINED_REL_LIST + SIMPLE_REL_LIST + SPECIAL + HOWTO
#RELATION_LIST= SIMPLE_REL_LIST + CONJOINED_REL_LIST +  SPECIAL
#It is necessary to add in this order so that conjoined rels come first in
#the list, because 'locking' or 'locking/unlocking' both relations will match
# to any string starting with 'locking/unlocking', when matching, we are picking 
#the first match, hence it is necessary to keep conjoined relations at the beginning  
MAX_STRING_LEN=80

def process_string(text):
    text=re.sub('#SBOLD#', '', text)
    text=re.sub('#EBOLD#', '', text)
    text=re.sub('#SEMP#', '', text)
    text=re.sub('#EEMP#', '', text)
    text = re.sub('\s*/\s*', '/', text)
    text = re.sub('\s*-\s*', 'hph', text) #replace hyphen by hph
    text = re.sub(':', '', text)
    return text


        

def remove_article(text):
    if text.lower().startswith("the "):
        text= re.sub("the ", "", text, flags=re.I) #IGNORECASE
    if text.lower().startswith("a "):
        text= re.sub("a ", "", text, flags=re.I) #IGNORECASE
    if text.lower().startswith("an "):
        text= re.sub("an ", "", text, flags=re.I) #IGNORECASE
    return text.strip()


        
def extract_entity_from_key(key, match):
    key=re.sub(match, "", key, flags=re.I).strip()
    key=remove_article(key)
    return key

def extract_entity_from_specialkey(key, rel):
    if "on/off" in key.lower():
        match="On/Off"
        key=re.sub(match, "", key, flags=re.I).strip()
        rel = "{} On/{} Off".format(rel,rel)
    elif "on" in key.lower():
        match="On"
        key=re.sub(match, "", key, flags=re.I).strip()
        rel = "{} On".format(rel)
    elif "off" in key.lower():
        match="Off"
        key=re.sub(match, "", key, flags=re.I).strip()
        rel = "{} Off".format(rel)
    key=remove_article(key)
    return key, rel

def extract_entity_from_howto(key, rel):
    #"How to store food, how to sort laundry"
    new_str=re.sub(rel, "", key, flags=re.I).strip().split()
    rel=new_str[0]
    key=remove_article(" ".join(new_str[1:]))
    return key, rel

def disintegrate_combined_keys(match):
    rels= match.split("/")
    return rels


def merge(a, b, path=None):
    "merges b into a"
    #recursive
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key].extend(b[key])
                #a[key]={"variation 1": deepcopy(a[key]), "variation 2": deepcopy(b[key])}
                #Exception handling if keys are same, but values are different
            else:
                #print(a[key], '#########')
                #print(b[key], '#########')
                #print(a[key], "#####", b[key])
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a        

class ProcessJson:
    def __init__(self, filename):
        self.filename= filename
        with open(self.filename, 'r', encoding='utf-8-sig') as jsonfile:
            self.jsonfile=json.load(jsonfile)
        #logger.debug(self.jsonfile)
        
    
    def process_sections(self):
        d={}
        prodname, self.model_nums=self.extract_productname()
        d[prodname]=self.extract_section(OPERATION)
        d[prodname].update(self.extract_section(INSTALLATION))
        #print(d[prodname].keys())
        d[prodname].update(self.extract_section(MAINTENANCE))
        d=self.trim_json(d)
        d=self.remove_special_tags(d)
        
        d=self.process_empty_dict(d)
        d=self.process_notes(d)
        d=self.clean_dict(d)
        d=self.process_relations(d, parent=None)
        d=self.update_model(d)
        d=self.translate_keywords(d)
        
        return d
    
    
    
    
    def update_model(self, dict_item):
        new_dict={BUYERMODEL: self.model_nums}
        #print(dict_item)
        new_dict.update(dict_item)
        return new_dict
        
    def process_variablelist(self, dict_item):
        new_d={}
        if type(dict_item)==dict:
            if "description" in dict_item and len(dict_item["description"])==1:
                key= dict_item["description"][0]
                del dict_item["description"]
                #print('key', key)
                #print(dict_item)
                new_d[key]= self.clean_dict(dict_item)
            else:
                new_d.update(self.clean_dict(dict_item))
            dict_item=new_d
        return dict_item
    
    
    
    
    
    
    
    
    
    def clean_dict(self,d):
        new_d={}
        if type(d)==dict:
            for key, value in d.items():
                if key.split('_')[0]=="variablelist":
                    
                    #new_d.update(self.clean_dict(value))
                    new_d.update(self.process_variablelist(value))
                elif key.split('_')[0]=='step':
                    key_split= key.split('_')
                    if len(key_split) ==1:
                        step_no= key_words_dict["steps"] + " 1"
                    else:
                        step_no= key_words_dict["steps"] + " "+ str(int(key_split[-1]) + 1)
                    if 'steps' not in new_d:
                        new_d['steps'] = {step_no: self.clean_dict(deepcopy(d[key]))}
                    else:
                         new_d['steps'].update({step_no: self.clean_dict(deepcopy(d[key]))})
                    
                            
                elif len(key)>= MAX_STRING_LEN and type(value)==list:
                    new_list= [key]+value
                    if 'description' in new_d:
                        new_d['description']+=new_list
                    else:
                        new_d['description']=new_list
                        
                else:
                    key = re.sub("\.$","", key).strip() #removing the end "." from keys
                    #key = re.sub("-","HYYP", key).strip() #removing the end "." from keys
                    new_d[key]=self.clean_dict(value)
        else:
            new_d=d
        return new_d
                    
                    
                    
    
    def update_dict(self, dict_item, new_d, key, rel, val):
        if key in new_d: #if key is already there in new_dict update dew dict
            if type(new_d[key])==dict:
                #print("BE")
                return_dict={rel: self.process_relations(val, parent=rel)}
                new_d[key].update(return_dict)
            else:
                #print("BK")
                return_dict={"description":deepcopy(new_d[key]), rel: self.process_relations(val, parent=rel)}
                new_d[key] = return_dict  
        else: #if key is not in update dict, first update old dict, then populate new dict
            #print(dict_item)
            if type(dict_item[key])==dict: 
                #print("BO")
                return_dict={rel: self.process_relations(val, parent=rel)} 
                dict_item[key].update(return_dict)
            else:
                #print("BL")
                return_dict={"description":deepcopy(dict_item[key]), rel: self.process_relations(val, parent=rel)}
                dict_item[key] = return_dict
            new_d[key]=deepcopy(dict_item[key])
        return new_d
    
   
    
    def process_relations_cases(self, dict_item, new_d, key, old_key, rel, val, parent, same_level_keys):
        #update same_key
        #print(type(same_level_keys))
        #print(type((dict_item.keys())))
        #print(type(new_d.keys()))
       
        if key == parent:# Matched with parent
            #print("A")
            #for r in rel:
            new_d[rel]=self.process_relations(val, parent=rel)
        elif key in same_level_keys: #key in the same label
            #print("B")
            #for r in rel:
            new_d=self.update_dict(dict_item, new_d, key, rel, val)
        else:
            #print("C", rel)
            #for r in rel
            if key=="":
                return_dict={rel: self.process_relations(val, parent=rel)}
            else:
                #same_level_keys.append(key) #update the keys as new level added
                same_level_keys.append(old_key)
                if old_key not in new_d:
                    return_dict={old_key:{key:{rel: self.process_relations(val, parent=rel)}}}
                else:
                    fetch_dict=deepcopy(new_d[old_key])
                    fetch_dict[key].update({rel: self.process_relations(val, parent=rel)})
                    return_dict={old_key:fetch_dict}
            new_d.update(return_dict)
            #print("C1")
        return new_d
    
    def process_relations(self, dict_item, parent=None):
        new_d={}
        #overall_d={}
        if type(dict_item)==dict:
            same_level_keys= list(dict_item.keys())
            for key, val in dict_item.items():
                old_key=key
                Match_list = [key.lower().endswith(rel.lower()) for rel in RELATION_LIST]
                if True in Match_list:
                    rel =RELATION_LIST[Match_list.index(True)] #First occuing True value
                    #print(key,rel, key.lower().startswith(rel.lower()))
                    #print("********YES*******:", key)
                    
                    key=extract_entity_from_key(key, rel)
                    if rel.lower() in map(str.lower, SPECIAL):
                        #print("######################################")
                        key, rel= extract_entity_from_specialkey(key, rel)
                    if rel.lower() in map(str.lower, HOWTO):
                        #print("######################################")
                        key, rel= extract_entity_from_howto(key, rel)
                    #print("********new key*******:", key)
                    if rel.lower() in map(str.lower, CONJOINED_REL_LIST):
                        rel=disintegrate_combined_keys(rel)
                        #print("********YES*******:", rel)
                    else:
                        rel=[rel]
                    for r in rel:
                        new_d=self.process_relations_cases(dict_item, new_d, key, old_key, r, val, parent, same_level_keys)
                else:
                    if key not in new_d:
                        if key.lower() in map(str.lower, CONJOINED_REL_LIST):
                            rel=disintegrate_combined_keys(key)
                        else:
                            rel=[key]
                        for r in rel:
                            #print("D:", key)
                            new_d[r]=self.process_relations(val, parent=r)
                        #new_d[key]=self.process_relations(val, parent=key)
                
        else:
            new_d=dict_item
                        
        return new_d
    
    def convert_to_list(self, dict_item, key_source, mode='list'):
        """
        if all values of a dict are empty {} combine all the keys to a list return list
        key_source is the main key od the dict i.e {key_source: dict_item}
        Returns
        -------
        None.

        """
        new_d={}
        li=[]
        if mode =='list': 
            for key, val in dict_item.items():
                li.append(key)
            new_d=li
        elif mode =='dict':
            return_dict={}
            for key, val in dict_item.items():
                if len(val)==0:
                    li.append(key)
                else:
                    new_d[key]=val
            if key_source=="have features" and len(li)==1:
                new_d[li[0]]=[]
            else:
                return_dict['description']=li
            
            return_dict.update(new_d)
            new_d=return_dict
            
        return new_d
    
    def collapse_dict(self, dict_item):
        values_list=True
        new_list=[]
        for key, value in dict_item.items():
            if type(value)!= list:
                values_list= False
            new_list.extend(value)
        if values_list:
            dict_item=new_list
        return dict_item
    
    def recursive_collapse(self, dict_item, item_list):
        "collapse the dict"
        if type(dict_item) ==list:
            item_list+=dict_item
            return item_list
        
        for key, value in dict_item.items():
            if key not in RELATION_LIST+['description', 'have feature']:
                item_list+=[key]
                if type(value)==list:
                    item_list+=value 
                else:
                    item_list= self.recursive_collapse(value, item_list)
        return item_list
            
    def process_step(self, dict_item):
        values_list =True
        if type(dict_item)==dict:
            new_list=[]
            for key, value in dict_item.items():
                if type(value)!= list:
                    values_list= False
                if key in ["description", "note"]:
                    #new_list.extend([key])
                    new_list.extend(value)
                elif key  in ["have features"]:
                    continue
                else:
                    if len(key)>40:
                        new_list.extend([key])
                        new_list.extend(value)
                    else:
                        values_list= False
                
                    
            if values_list:
                dict_item=new_list
        return dict_item
                    
                    
                    
                
        
    
    def process_notes(self, dict_item):
        n_d={}
        if type(dict_item)==dict:
            dict_item=self.merge_notes(dict_item)
            for key,value in dict_item.items():
                if type(value)==dict:
                    n_d[key]=self.process_notes(value)
                    if key.split("_")[0]=="step": #collapsing steps to list if step is dict
                        n_d[key]= self.process_step(n_d[key])
                     #   n_d[key]= self.collapse_dict(n_d[key])
                         
                        
                else:
                    n_d[key]= value
        else:
            n_d=dict_item
        return n_d
    
    def merge_notes(self, dict_item):
        all_keys=dict_item.keys()
        #print(all_keys)
        #handle footnote group
        if "footnotegroup" in  all_keys and "footnote" in dict_item["footnotegroup"] :
            if type(dict_item["footnotegroup"]["footnote"]) ==list:
                if "description" in all_keys:
                    dict_item["description"]+=deepcopy(dict_item["footnotegroup"]["footnote"])
                else:
                    dict_item["description"]=deepcopy(dict_item["footnotegroup"]["footnote"])
                del dict_item["footnotegroup"]
            else:
                dict_item.update(deepcopy(dict_item["footnotegroup"]["footnote"]))
                del dict_item["footnotegroup"]
        all_keys=dict_item.keys() #update keys
                
                
        if "note" in all_keys:
            #print("HI")
            keys=[]
            for key in all_keys:
                if key.split("_")[0]=="note": 
                    keys.append(key)
            for key in keys:
                #print(keys)
                if "description" in all_keys and type(dict_item[key])==list:
                        dict_item["description"]+=deepcopy(dict_item[key])
                        del dict_item[key]
                        
                elif "description" not in all_keys  and type(dict_item[key])==list:
                    n_d={"description":deepcopy(dict_item[key])}
                    n_d.update(dict_item)
                    del n_d[key]
                    dict_item = n_d
                else:
                    #If note is a dictionary 
                    dict_item.update(deepcopy(dict_item[key]))
                    del dict_item[key]
        return dict_item
                        
                    
            
    
    def process_empty_dict(self, dict_item, key1=''):
        if type(dict_item)==list:
            return dict_item
        new_d={}
        flag_all_empty=True #flag is set if all keys have empty values
        flag_all_full=True #flag is set if all are full
        for key,val in dict_item.items():
            if len(val)>0:
                flag_all_empty=False #if atlest one has value
            elif len(val)==0:
                flag_all_full= False #at least one empty
            new_d[key]=self.process_empty_dict(val, key)
        if flag_all_empty:
            new_d=self.convert_to_list(new_d, key1)
        elif not(flag_all_full):
            new_d=self.convert_to_list(new_d, key1,  mode='dict')
            
        return new_d
            
            
            
            
    
    
    def process_columns(self, columns):
        new_d={}
        column_processed= False
        for key, value in columns.items():
            if key.split('_')[0]=='entry' and "variablelist" in value:
                new_d.update(value["variablelist"])
                column_processed=True
        return new_d, column_processed
    
    def remove_special_tags(self, new_dict):
        new_d={}
        if type(new_dict)==list:
            return new_dict
        for key,val in new_dict.items():
            key_items= key.split("**")
            if len(key_items)>0:
                key=key_items[-1]
                if key=="":
                    key=key_items[-2]
            key=process_string(key)
            new_d[key]=self.remove_special_tags(val)
        return new_d
    
    def combine_nested_dict_key(self, d, s): 
        for key, value in d.items(): 
            s= s+ " " + key 
            s= self.combine_nested_dict_key(value, s.strip()) 
        return s.strip()
    
   
    
    def process_table_data(self, head, body):
        """
        

        Parameters
        ----------
        head : TYPE dict
            DESCRIPTION. header dict
        body : TYPE dict
            DESCRIPTION. body dict

        Returns
        -------
        new_d : TYPE dict
            DESCRIPTION. formatted tables
            TABLE_FORMATING=["세탁코스 (최대용량)", "세탁 코스"]
            #if top left contains these keywords tables with only one row header will be formatted
            #as {main_heading{row_heading:{col_heading:{data}}}} top row and left column are hedings
            #main_heading is top_left
            #else tables will be formatted as {column_heading:data} only left most row is heading
            

        """
        left_row_is_heading=False
        new_d={}
        t_head_keys= head.keys()
        if len(t_head_keys)==1 and 'row' in t_head_keys: #onlye one row heading
            table_dict={} 
            columns=[]
            for entry, value in head["row"].items():
                des=""
                id1=None
                for k, v in value.items():
                    if k =="@colname":
                        id1= v 
                    else: 
                        des=des + " " +k 
                if id1:
                    table_dict[id1]={"head":des.strip(), "datapoint":{}}
                    columns.append(id1)
                    if des.strip() in TABLE_FORMATING and id1=="1":
                        #print("#########", des)
                        left_row_is_heading=True
                        
            if left_row_is_heading:
                main_heading=table_dict["1"]["head"]
             
                
                for row in body: 
                    for entry, value in body[row].items():
                        id1=None
                        temp_dict={}
                        for k,v in value.items(): 
                            if k=="@colname": 
                                id1 =v
                            elif id1 and k=="figure":
                                fig_key=" ".join(k.split("_"))
                                temp_dict.update(self.process_figure(v, fig_key))
                            elif id1:
                                temp_dict.update({k:deepcopy(v)})
                        if id1=="1":
                            row_heading=self.combine_nested_dict_key(temp_dict, "")
                        else:
                            col_heading=table_dict[id1]["head"]
                            #print("1:", new_d)
                            #print("2:", {main_heading:{row_heading:{col_heading:deepcopy(temp_dict)}}})
                            new_d=merge(new_d, {main_heading:{row_heading:{col_heading:deepcopy(temp_dict)}}})
                            #print("new_d:#######", new_d)
            else:
                for row in body: 
                    for entry, value in body[row].items():
                        id1=None
                        temp_dict={}
                        for k,v in value.items(): 
                            if k=="@colname": 
                                id1 =v 
                            elif id1:
                                temp_dict.update({k:deepcopy(v)})
                        table_dict[id1]["datapoint"].update(temp_dict)  
                #print(table_dict)
                for col, value in table_dict.items():
                    if value["head"]!="": 
                        new_d.update({value["head"]:deepcopy(value["datapoint"])})
        #print("final_d:", new_d)
        return new_d
    
    
    
    
    
                
    
    
    
    
    def process_table(self, dict_item):
        new_d={}
        extract_row=dict_item["tgroup"]["tbody"]
        for row, columns in extract_row.items():
            return_dict, column_processed= self.process_columns(columns)
            new_d.update(return_dict)
        if not column_processed: 
            if 'thead' in dict_item["tgroup"]:
                extract_head=dict_item["tgroup"]["thead"] 
                new_d=self.process_table_data(extract_head, extract_row)
                #print("===newd:", new_d)
            #print("$$$newd:", new_d)
        return new_d
    
    
    
    def process_figure(self, figure, fig_key):
        #print(fig_key)
        new_d={fig_key:{}}
        for key, value in figure.items():
            if key=="graphicgroup":
                figure_path=value["graphic"].split("/")
                img_name= figure_path[-1][:-4]+".png"
                image_path= "./"+figure_path[-3]+"/"+figure_path[-2]+"/"+ img_name
                new_d[fig_key]["graphic"]= [image_path]
                
            if key=="calloutlist":
                new_d[fig_key]["calloutlist"]= deepcopy(value)
        
        return new_d
            

        
    
    def trim_json(self, dict_item):
        new_dict={}
        if type(dict_item)== dict:
            for key, val in dict_item.items():
                if key.split("_")[0] == "table":
                    new_dict.update(self.process_table(val))
                elif key.split("_")[0] =="figure":
                    fig_key=" ".join(key.split("_"))
                    new_dict.update(self.process_figure(val, fig_key))
                else:
                    new_dict[key]=self.trim_json(val)
            dict_item=new_dict 
        return dict_item
        
    def extract_section(self, section_name):
        d={}
        key= "**".join([CHAPTER, TITLE, section_name])
        key= "**"+key
        for key_, value in self.jsonfile[BOOK].items():
            if key_ == key:
                d[key] = deepcopy(value)
                break 
        return d
        
    def extract_productname(self):
        model_nums=[]
        for key, value in self.jsonfile[BOOK].items():
            logger.debug("key %s", key)
            #print(key)
            if key == BOOKINFO:
                prodname= value[PRODUCTNAME]
                models_nums_str=value[BUYERMODEL]
                part_number=value[PARTNUMBER]
                if models_nums_str: #not null
                    model_nums=[re.sub("\*$", "", modelnum.strip()) for modelnum in models_nums_str.split("/")]
                else:
                    model_nums=[part_number]
                break
                    
                
        return prodname, model_nums
    
    
    
    def translate_keywords(self, d):
        new_d={}
        if type(d)!=dict:
            return d
        for key, value in d.items():
            if key in key_words_dict:
                key= key_words_dict[key]
            new_d[key]=deepcopy(self.translate_keywords(value))
            
        return new_d
    
    
    
    def save_file(self, ob, outfile):
        with open(outfile, 'w') as out:
            json.dump(ob, out, indent=6)
            
    
        

        
        
        
        
        
        
        
        
if __name__=="__main__":
    logger.basicConfig(level=logger.DEBUG, format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    filename=input("Enter path to the file")
    Pjson_obj = ProcessJson(filename)
    json_processed= Pjson_obj.process_sections()
    outfile=input("Enter path to the output file")
    Pjson_obj.save_file(json_processed, outfile)