# -*- coding: utf-8 -*-
""""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anindya06.das@lge.com
##############################################################################
"""

import logging as logger
import json
import re
from copy import deepcopy
import os
import utils.image_handling_interface as im_interface
import utils.params as cs
import utils.helper as hp


class DataModelEngine:
    """"Class to process json file extracted from xml, for data modelling and generate
    processed json file as  per data modelling for selected sections"""

    def __init__(self, filename):
        self.filename = filename
        self.folder = os.path.abspath(os.path.join(os.path.dirname(self.filename), '..'))
        self.image_interface = im_interface.ImageHandlingInterface()
        self.section = ""
        with open(self.filename, 'r', encoding='utf-8-sig') as jsonfile:
            self.jsonfile = json.load(jsonfile)

    def process_each_section(self, section):
        d = {}
        d = self.extract_section(section)
        d = self.process_tables_figures(d)
        d = hp.remove_special_tags(d)
        d = self.process_empty_dict(d)
        d = self.clean_dict(d)
        d = self.process_delete_subsections(d, section)
        return d

    def process_sections(self):
        d = {}
        self.prodname, self.model_nums, self.partnumber = self.extract_productname()
        d = self.update_model(d)
        d[self.prodname] = self.process_each_section(cs.S_KO_OPERATION)
        d[self.prodname].update(self.process_each_section(cs.S_KO_INSTALLATION))
        d[self.prodname].update(self.process_each_section(cs.S_KO_MAINTENANCE))
        d[self.prodname].update(self.process_each_section(cs.S_KO_USING_LG_ThinQ))
        d[self.prodname].update(self.process_each_section(cs.S_KO_APPENDIX))
        d[self.prodname].update(self.process_each_section(cs.S_KO_PRODUCT_WARRANTY))
        d[self.prodname].update(self.process_each_section(cs.S_KO_LEARN))
        d[self.prodname].update(self.process_each_section(cs.S_KO_SAFETY_INSTRUCTIONS))
        d[self.prodname].update(self.process_each_section(cs.S_KO_SAFETY_PRECAUTION))
        d = hp.translate_keywords(d)
        return d

    def update_model(self, dict_item):
        """
        This function updates the model no.in the processed json file

        Parameters
        ----------
        dict_item : TYPE dict
            DESCRIPTION.

        Returns
        -------
        new_dict : TYPE dict
            DESCRIPTION.

        """
        new_dict = {cs.XMLTags.BUYERMODEL_TAG: self.model_nums}
        new_dict.update(dict_item)
        return new_dict

    def process_description(self, dict_item):
        """
        This function processes the dictionary containing description. 
        The content inside dictionary is modified as main key of the dictionary itself.
        It returns processed dictionary
        Parameters
        ----------
        dict_item : TYPE dict

        Returns
        -------
        dict_item : TYPE dict

        """
        new_d = {}
        if type(dict_item) == dict:
            if "description" in dict_item and len(dict_item["description"]) == 1:
                key = dict_item["description"][0]
                del dict_item["description"]
                new_d[key] = self.clean_dict(dict_item)
            else:
                new_d.update(self.clean_dict(dict_item))
            dict_item = new_d
        return dict_item

    def process_steps(self, key, d, new_d):
        key_split = key.split('_')
        if len(key_split) == 1:
            step_no = cs.keywords_map["steps"] + " 1"
        else:
            step_no = cs.keywords_map["steps"] + " " + str(int(key_split[-1]) + 1)
        step_value = self.clean_dict(deepcopy(d[key]))
        if type(step_value) == list:
            step_value = " ".join(step_value)
            step_value = {step_value: []}
        if 'steps' not in new_d:
            new_d['steps'] = {step_no: step_value}
        else:
            new_d['steps'].update({step_no: step_value})
        return new_d

    def clean_dict(self, d):
        new_d = {}
        if type(d) != dict:
            return d

        for key, value in d.items():
            if key.split('_')[0] == cs.XMLTags.VAR_LIST_TAG:
                new_d.update(self.process_description(value))
            elif key.split('_')[0] == cs.XMLTags.STEP_TAG:
                new_d = self.process_steps(key, d, new_d)
            #Clean-up remove content with 'para' tag
            elif key.split('_')[0] == cs.XMLTags.PARA_TAG:
                continue
            elif len(key) >= cs.MAX_STRING_LEN and type(value) == list:
                new_list = [key] + value
                if 'description' in new_d:
                    new_d['description'] += new_list
                else:
                    new_d['description'] = new_list
            else:
                key = re.sub("\.$", "", key).strip()  # removing the end "." from keys
                new_d[key] = self.clean_dict(value)
        return new_d

    def convert_to_list(self, dict_item, key_source, mode='list'):
        """
        if all values of a dict are empty {} combine all the keys to a list return list
        key_source is the main key od the dict i.e {key_source: dict_item}
        Returns
        -------
        None.

        """
        new_d = {}
        li = []
        if mode == 'list':
            for key, val in dict_item.items():
                li.append(key)
            if li:
                new_d = li
            else:
                new_d = []

        elif mode == 'dict':
            return_dict = {}
            for key, val in dict_item.items():
                return_dict[key] = self.clean_dict(val)

            return_dict.update(new_d)
            new_d = return_dict

        return new_d

    def process_empty_dict(self, dict_item, key1=''):
        """
        This function recursively processes the dictionary to merge all the keys
        if correspinding values are empty dict
        eg1.
        {abc:{}, bcd:{}, cde:{}}, key1= 123
        output: {123:[abc, bcd, cde]}
        eg2.
        {abc:{}, bcd:{}, cde:[value] }, key1=123
        output: {123:{abc:{}, bcd:{}, cde:{}}}

        Parameters
        ----------
        dict_item : TYPE
            DESCRIPTION.
        key1 : TYPE, optional
            DESCRIPTION. The default is ''.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        if type(dict_item) == list:
            new_d=[]
            for item in dict_item:
                new_d.append(self.process_empty_dict(item))
            return new_d
        if type(dict_item)==str:
            return dict_item
        new_d = {}
        flag_all_empty = True  # flag is set if all keys have empty values
        flag_all_full = True  # flag is set if all are full
        for key, val in dict_item.items():
            if len(val) > 0:
                flag_all_empty = False  # if atlest one has value
            elif len(val) == 0:
                flag_all_full = False  # at least one empty
            new_d[key] = self.process_empty_dict(val, key)
        if flag_all_empty:
            new_d = self.convert_to_list(new_d, key1)
        elif not (flag_all_full):
            new_d = self.convert_to_list(new_d, key1, mode='dict')

        return new_d

    def process_columns(self, columns):
        """
        This function processes the columsn of table which contain variable list

        Parameters
        ----------
        columns : TYPE dict
            DESCRIPTION.

        Returns
        -------
        new_d : TYPE dict
            DESCRIPTION.
        column_processed : BOOL
            DESCRIPTION. Flag is True if variablelist is found else False
        """
        new_d = {}
        column_processed = False
        for key, value in columns.items():
            if key.split('_')[0] == cs.XMLTags.ENTRY_TAG and cs.XMLTags.VAR_LIST_TAG in value:
                new_d.update(value[cs.XMLTags.VAR_LIST_TAG])
                column_processed = True
        return new_d, column_processed

    def delete_subsections(self, new_dict, check_title):
        """This function recursively delete subsections matches with check_title
        Argument: dicttionary, list"""
        new_d = {}
        if type(new_dict) == list:
            return new_dict
        for key, val in new_dict.items():
            if key not in check_title:
                new_d[key] = self.delete_subsections(deepcopy(val), check_title)
        return new_d

    def process_delete_subsections(self, new_dict, section):
        """This function calls delete_subsections if section matches"""
        if section in [cs.S_KO_SAFETY_INSTRUCTIONS, cs.S_KO_SAFETY_PRECAUTION]:
            check_title = ["제품을 사용하기 전에 읽어주세요"]
            new_dict = self.delete_subsections(new_dict, check_title)
        return new_dict

    def merge_header_text(self, header_dict, max_row, max_col):
        """
        This function takes the header as the form of  dictionary, merge mutiple rows
        into a single row 
        Parameters
        ----------
        header_dict : TYPE dict
            DESCRIPTION.
            {(1, 1): '', (1, 2): '소비자 피해 유형', (1, 3): '보상 내역', (1, 4): '보상 내역', (2, 1): '', (2, 2): '소비자 피해 유형', (2, 3): '보증 기간 이내', (2, 4): '보증 기간 경과 후'}
        Returns
        -------
        dict.
        """
        new_header_dict = {}
        for col_num in range(1, max_col + 1):
            des = ""
            for row_num in range(1, max_row + 1):
                current_heading = header_dict[(row_num, col_num)]
                if current_heading not in des:
                    des += " " + current_heading
            new_header_dict[(1, col_num)] = des.strip()
        return new_header_dict
    
    def replicate_rows_cols(self, count_dict):
        morerows=count_dict["morerows"]
        row_number=count_dict["row_number"]
        max_row=count_dict["max_row"]
        max_col=count_dict["max_col"]
        namest=count_dict["namest"]
        nameend=count_dict["nameend"]
        des, header_dict=count_dict["data"]
        for extra_row in range(morerows + 1):  # repeat rows if morerows
            r_no = row_number + extra_row
            if r_no > max_row:
                max_row = r_no
            for col_num in range(namest, nameend + 1):  # repeat columns if column is extended across
                if col_num > max_col:
                    max_col = col_num
                header_dict[(r_no, col_num)] = des
        return header_dict, max_col
    
    def extract_col_properties(self, column_data, header):
        if header:
            des = ""
        else:
            des = {}
        morerows = 0
        fig_count = 0
        for k, v in column_data.items():
            if k == "@colname":
                namest = int(v)
                nameend = int(v)
            elif k == "@namest":
                namest = int(v)
            elif k == "@nameend":
                nameend = int(v)
            elif k == "@morerows":
                morerows = int(v)
            elif isinstance(des, dict) and k == cs.XMLTags.FIGURE_TAG:
                fig_key, fig_count = self.get_fig_key(des, k, fig_count)
                des.update(self.process_figure(v, fig_key))
            elif isinstance(des, dict) and k != cs.XMLTags.FIGURE_TAG:
                des.update({k: deepcopy(v)})
            elif not isinstance(des, dict):
                des = des + " " + k
                des = des.strip()
        return des, namest, nameend, morerows

    def process_table_content(self, head, header=False):
        """
        This function processes table content(header or body) and standardize it by storing inside
        a dictionary, key=(row_no,col_no)
        eg. {(1, 1): '', (1, 2): '소비자 피해 유형', (1, 3): '보상 내역', (1, 4): '보상 내역', (2, 1): '', (2, 2): '소비자 피해 유형', (2, 3): '보증 기간 이내', (2, 4): '보증 기간 경과 후'}
        """
        header_dict = {}
        t_head_rows = head.keys()
        max_row = 0
        max_col = 0
        for row in t_head_rows:
            split_rowkey = row.split("_")
            if len(split_rowkey) == 2:
                row_number = int(split_rowkey[-1]) + 1
            else:
                row_number = 1
            if row_number > max_row:
                max_row = row_number
            for entry, column_data in head[row].items():  # head[row] contains columns for that particular row
                # column_data contains corresponding column
                des, namest, nameend, morerows=self.extract_col_properties(column_data, header)
                count_dict={}
                count_dict["morerows"]=morerows
                count_dict["row_number"]=row_number
                count_dict["max_row"]=max_row
                count_dict["max_col"]=max_col
                count_dict["namest"]=namest
                count_dict["nameend"]=nameend
                count_dict["data"]=[des, header_dict]
                header_dict, max_col=self.replicate_rows_cols(count_dict)
        if header:
            header_dict = self.merge_header_text(header_dict, max_row, max_col)
        header_dict = dict(sorted(header_dict.items(), key=lambda item: item[0]))
        return header_dict
    
    def build_dictkey_from_leftmost_col(self, rd_c1):
        rd_c1_list, flag_extracted = hp.extract_text_keys(rd_c1)
        if not flag_extracted:
            rd_c1_list = ["DUMMY_FOR_ROW"]
        else:
            rd_c1_text = " ".join(rd_c1_list)
            if len(rd_c1_text) < cs.MAX_STRING_LEN:
                rd_c1_list = [rd_c1_text]
        return rd_c1_list, flag_extracted
    
    def populate_col_dict(self, rd_c1, max_head_col, d, head, body, col_dict, flag_extracted):
        for c in range(2, max_head_col + 1):
            h_r1_cc = head[(1, c)]
            temp_dict = {}
            if rd_c1 == body[(d, c)]:
                continue
            for k1, v1 in body[(d, c)].items():  # Refining keys
                if k1 not in cs.SYMBOLS:                        
                    temp_dict.update({k1: deepcopy(v1)})
            col_dict.update({h_r1_cc: temp_dict})
        return col_dict
    
    def populate_row_dict(self, count_dict, row_dict, flag_extracted):
        max_head_col=count_dict["max_head_col"]
        d=count_dict["row"]
        count=count_dict["count"]
        rd_c1, rd_c1_list, head, body=count_dict["data"]
        for k in rd_c1_list:
            col_dict = {}
            if not flag_extracted:  # if no key is extracted from first col, update the col_dict with entries of first row
                col_dict.update(rd_c1)
            col_dict=self.populate_col_dict(rd_c1, max_head_col, d, head, body, col_dict, flag_extracted)
            row_dict, count = self.update_row_dict(count, flag_extracted, k, row_dict, col_dict)
        return row_dict, count
    
    def update_row_dict(self, count, flag_extracted, key, row_dict, col_dict):
        if key not in cs.SYMBOLS:
            count += 1
            if not flag_extracted:
                category = "<num {}>".format(str(count))
            else:
                category=key
            if category in row_dict and type(row_dict[category])==dict:
                data_item = deepcopy(row_dict[category])
                row_dict[category]=[data_item, col_dict]
            elif category in row_dict and type(row_dict[category])==list:
                row_dict[category].append(col_dict)
            else:
                row_dict.update({category: col_dict})
        else:
            row_dict = hp.merge(row_dict, col_dict)
        return row_dict, count
        

        

    def extract_type1_table(self, head, body):
        """
        This function extracts and format from standardize tables, if the table is identified as type I
        type I table has the very first column as header or title apart from the header row
        extracted output has the following format
        {H_R1_C1:{R2_C1:{H_R1_C2:{data}, H_R1_c3:{Data}}, R3_C1:{}}
        R=row, C=col, R1_C1=row1_col1
        H=header row
        R2_C1..... Rn_C1 all acts as header , though does not belong to header row
        if R2_C1 can not be expressed as string key (eg. containing images, list of images)
        then the dict will be {H_R1_C1:{"ct 1":{"item 1":{data R2C1}, H_R1_C2:{data R2C2}, H_R1_c3:{Data R2C3}}, R3_C1:{}}                   
        Parameters
        ----------
        head : TYPE dict
            DESCRIPTION.
        body : TYPE
            DESCRIPTION.dict   
        Returns
        -------
        dict: extracted dict
        """
        extracted_dict = {}
        max_head_col = max(list(head.keys()), key=lambda item: item[1])[1]
        max_body_row = max(list(body.keys()), key=lambda item: item[0])[0]

        row_dict = {}
        count = 0
        for d in range(1, max_body_row + 1):
            rd_c1 = body[(d, 1)]
            rd_c1_list, flag_extracted= self.build_dictkey_from_leftmost_col(rd_c1)
            count_dict={}
            count_dict["max_head_col"]=max_head_col
            count_dict["max_body_row"]=max_body_row
            count_dict["row"]=d
            count_dict["count"]=count
            count_dict["data"]=[rd_c1, rd_c1_list, head, body]
            row_dict, count=self.populate_row_dict(count_dict, row_dict, flag_extracted)

        if head[(1, 1)] != '':
            extracted_dict[head[(1, 1)]] = row_dict
        else:
            extracted_dict = row_dict
        return extracted_dict

    def extract_type2_table(self, head, body):
        """
        This function extracts and format from standardize tables, if the table is identified as type II
        type II table has data under each header column
        {head1:{data}, head2:{data}, head3:{data}}
        Parameters
        ----------
        head : TYPE dict
            DESCRIPTION.
        body : TYPE
            DESCRIPTION.dict
        Returns
        -------
        dict: extracted dict
        """
        extracted_dict = {}
        max_head_col = max(list(head.keys()), key=lambda item: item[1])[1]

        for c in range(1, max_head_col + 1):
            heading = head[(1, c)]
            extracted_dict[heading] = body[(1, c)]

        return extracted_dict

    def standardize_table(self, head, body):
        processed_head = None
        processed_body = None
        if head:
            processed_head = self.process_table_content(head, header=True)
        if body:
            processed_body = self.process_table_content(body)

        return processed_head, processed_body

    def process_table_data_with_head(self, head, body):
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
            process tables that contains both head and body, 
            this function calls standardise tables and then format table data
            based on if it's typeI or type II
        """
        head, body = self.standardize_table(head, body)
        max_body_row = max(list(body.keys()), key=lambda item: item[0])[0]
        if max_body_row > 1:
            t_dict = self.extract_type1_table(head, body)
        else:
            t_dict = self.extract_type2_table(head, body)
        return t_dict

    def process_table_wo_head(self, extract_row):
        new_d = {}
        _, body = self.standardize_table(None, extract_row)
        max_body_row = max(list(body.keys()), key=lambda item: item[0])[0]
        max_body_col = max(list(body.keys()), key=lambda item: item[1])[1]
        for r in range(1, max_body_row + 1):
            for c in range(1, max_body_col + 1):
                col_entry = body[(r, c)]
                category = "<num {}>".format(r)
                new_d = hp.merge(new_d, {category: col_entry})
        return new_d

    def get_fig_key(self, new_d, key, count):
        fig_key = " ".join(key.split("_"))
        if fig_key in new_d:
            count += 1
            fig_key = " ".join([fig_key, str(count)])
        return fig_key, count

    def process_table(self, extract_head, extract_row):
        new_d = {}
        for row, columns in extract_row.items():
            return_dict, column_processed = self.process_columns(columns)
            new_d.update(return_dict)
        # if column_processed flag is false
        if not column_processed:
            if extract_head:
                new_d = self.process_table_data_with_head(extract_head, extract_row)
            else:
                new_d = self.process_table_wo_head(extract_row)
        return new_d

    def process_figure_info(self, image_path):
        image_info = {}
        desc_temp = ""
        image_info["file_path"] = image_path
        image_info["file_type"] = "png"
        image_response = self.image_interface.get_image_information("",
                                                                    "",
                                                                    self.sub_section,
                                                                    self.partnumber, image_info)
        if image_response[cs.resp_code] == cs.ResponseCode.SUCCESS:
            desc_temp += image_response[cs.resp_data][cs.IMAGE_CONTENT][cs.ExtractionConstants.FILE_PATH]
        return desc_temp

    def process_figure(self, figure, fig_key):
        new_d = {fig_key: {}}
        for key, value in figure.items():
            if key == cs.XMLTags.GRAPGHICGRP_TAG:
                figure_path = value[cs.XMLTags.GRAPHIC_TAG].split("/")
                img_name = figure_path[-1][:-4] + ".png"
                image_path = self.folder + os.sep + figure_path[-3] + \
                             os.sep + figure_path[-2] + os.sep + img_name
                self.sub_section=figure_path[-2]
                new_d[fig_key][cs.XMLTags.GRAPHIC_TAG] = [self.process_figure_info(image_path)]

            if key == cs.XMLTags.CALLOUTLIST_TAG:
                new_d[fig_key][cs.XMLTags.CALLOUTLIST_TAG] = deepcopy(value)

        return new_d
    
    def extract_process_table(self, key_split, val, head_copy, new_dict):
        extract_head = None
        extract_row = val[cs.XMLTags.TGROUP_TAG][cs.XMLTags.TBODY_TAG]
        if cs.XMLTags.THEAD_TAG in val[cs.XMLTags.TGROUP_TAG]:
            extract_head = val[cs.XMLTags.TGROUP_TAG][cs.XMLTags.THEAD_TAG]
        if len(key_split) == 1:  # copy extracted head
            head_copy = extract_head
        if len(key_split) == 2 and not extract_head:
            extract_head = head_copy
        new_dict = hp.merge(new_dict, self.process_table(extract_head, extract_row))
        return new_dict, head_copy


    def process_tables_figures(self, dict_item):
        """
        This function calls sub-functions to extract data from table and
        figures
        Parameters
        ----------
        dict_item : TYPE
            DESCRIPTION.
        Returns
        -------
        dict_item : TYPE
            DESCRIPTION.
        """
        new_dict = {}
        head_copy=''
        count = 0
        if type(dict_item) != dict:
            return dict_item
        for key, val in dict_item.items():
            key_split = key.split("_")
            if key_split[0] == cs.XMLTags.TABLE_TAG:
                new_dict, head_copy=self.extract_process_table(key_split, val,
                                                               head_copy, new_dict)
            elif key_split[0] == cs.XMLTags.FIGURE_TAG:
                fig_key, count = self.get_fig_key(new_dict, key, count)
                new_dict.update(self.process_figure(val, fig_key))
            else:
                new_dict[key] = self.process_tables_figures(val)
        dict_item = new_dict
        return dict_item

    def extract_section(self, section_name):
        d = {}
        self.section = cs.Section_map[section_name]
        self.sub_section=""
        for key_, value in self.jsonfile[cs.XMLTags.BOOK_TAG].items():
            section_prod_name = key_.split("**")[-1].split('-')
            if (len(section_prod_name) == 1 and section_name == section_prod_name[0]) \
                    or (len(section_prod_name) == 2 and section_name == section_prod_name[0] and section_prod_name[
                1] in cs.PRODUCTS):
                d[key_] = deepcopy(value)
        return d

    def extract_productname(self):
        model_nums = []
        for key, value in self.jsonfile[cs.XMLTags.BOOK_TAG].items():
            logger.debug("key %s", key)
            if key == cs.XMLTags.BOOKINFO_TAG:
                prodname = value[cs.XMLTags.PRODUCTNAME_TAG]
                models_nums_str = value[cs.XMLTags.BUYERMODEL_TAG]
                part_number = value[cs.XMLTags.PARTNUMBER_TAG]
                if models_nums_str:  # not null
                    model_nums = [re.sub("\*$", "*", modelnum.strip()) for modelnum in models_nums_str.split("/")]
                else:
                    model_nums = [part_number]
                break

        return prodname, model_nums, part_number


if __name__ == "__main__":
    logger.basicConfig(level=logger.DEBUG, format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                                                  "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    filename = input("Enter path to the file")
    Pjson_obj = DataModelEngine(filename)
    json_processed = Pjson_obj.process_sections()
    outfile = input("Enter path to the output file")
    hp.save_file(json_processed, outfile, ftype='json')
