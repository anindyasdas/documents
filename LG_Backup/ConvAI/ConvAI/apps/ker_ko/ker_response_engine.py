"""
# -------------------------------------------------
# Copyright(c) 2021-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------
"""
import json
import os

import requests
from configparser import ConfigParser

from .knowledge_extraction.constants import params as cs
from .knowledge_extraction.docextraction.partialxmlextractor.xmlresultextractor import XMLResultExtractor

import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

# CONSTANTS used in this module
WARNING_TITLE_IN_HTML = "WARNING"
CAUTION_TITLE_IN_HTML = "CAUTION"
NOTE_TITLE_IN_HTML = "NOTE"
DOC_APPROACH = "doc"
KG_APPROACH = "kg"
WARNING = "warning"
NOTE = "note"
STEPS_TO_BE_FOLLOWED = "다음 지시사항을 따라해주세요."
# Related to _process_dynamic_threshold
TH_PERCENTILE=0.4
QUALIFYING_SCORE_TO_APPLY_DYNAMIC_THRESHOLD = 50

current_path = os.path.abspath(os.path.dirname(
    os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(current_path, 'knowledge_extraction', 'config', 'configuration.ini')


class KerResponseEngine(object):
    def __init__(self):
        """
        Class to create HTML responses for both KG Graph QA and Document based approach
        """

        # Variables for HTML Templates
        self.main_html_frame = """<html><body>{content}</body></html>"""
        self.html_template_for_ordered_list = """<ol>{list_content}</ol>"""
        self.html_template_for_unordered_list = """<ul>{list_content}</ul>"""
        self.html_template_for_each_element = """<li>{each_element}</li>"""
        self.html_template_for_images = """<img style='display: block;width:100%; margin: 0 auto;' src={image_path}><br>"""

        self.html_template_for_heading = """<h3>{heading}</h3>"""
        self.html_template_for_paragraph = """<p>{paragraph}</p>"""
        # https://stackoverflow.com/questions/5216020/give-border-title-in-div
        self.html_template_for_note_caution_warning = """<fieldset><legend>{title}</legend>{extra_info_content}</fieldset>"""

        self.normalized_section_names = {
            cs.IOConstants.HY_TROUBLESHOOTING: ["troubleshooting"],
            cs.IOConstants.HY_OPERATION: ["operation", "사용하기"],
            cs.IOConstants.HY_MAINTENANCE: ["maintenance", "관리하기"],
            cs.IOConstants.HY_INSTALLATION: ["installation", "설치하기"],
            cs.IOConstants.HY_LEARN: ["learn", "알아보기"],
            cs.IOConstants.HY_SAFETY_INSTRUCTIONS: ["safety", "안전을 위해 주의하기"],
            cs.IOConstants.HY_WARRANTY: ["warranty", "제품 보증서 보기"],
            cs.IOConstants.HY_APPENDIX: ["appendix", "부록"],
            cs.IOConstants.HY_USING_LG_THINQ: ["Using LG ThinQ", "LG ThinQ 사용하기"],
            cs.IOConstants.HY_SAFETY_PRECAUTION: ["safety precaution", "안전을 위한 주의 사항"]
        }

        self.invalid_elements = ["", "None"]
        self.image_folder_path, self.ip_address, self.port_number = cs.get_image_db_path()
        prefix_path_with_ip_and_port = "http://" + self.ip_address + ":" + self.port_number
        self.image_folder_path = os.path.join(prefix_path_with_ip_and_port, self.image_folder_path)
        logger.debug("image_folder_path: {} ".format(self.image_folder_path))
        config_parser = ConfigParser()
        config_parser.read(CONFIG_PATH)
        self.html_transformer_ip = config_parser.get("html_transformer_config", "html_transformer_ip")
        self.headers = {'Content-Type': 'application/json'}
        self.xmlextractor = XMLResultExtractor()

    def get_resp_for_mapped_keys(self, graph_qa_keys, doc_based_keys):
        """
        Get the nested dictionary of sections and mapped keys from both graph_qa and doc_based

        Args:
            graph_qa_keys (dict): key value pairs of mapped results and scores from graph_qa
            doc_based_keys (dict): key value pairs of mapped results and scores from doc_based

        Returns:
            dict: Nested dictionary of sections and mapped keys, Example: {
             "Operation":{
                "Fresh air filter description":"kg"
             },
             "Maintenance":{
                "Fresh air filter replacement":"doc",
                "Fresh Air filter replacing procedure steps":"kg"
             },
             "Troubleshooting":{
                "problem with Fresh Air filter replacement":"doc"
             }
          }
        """

        best_matches = []   # To have best matched keys and scores in descending order irrespective of section
        # Ex: [{'key': '건조물에 주름이 생겼어요', 'section': '문제 해결하기', 'approach': 'kg'}]
        flag_to_have_only_top_2_keys_for_operation_kg = 0
        logger.debug("graph_qa_keys: {} doc_based_keys: {}".format(graph_qa_keys, doc_based_keys))
        nested_dict_of_sections_and_mapped_keys = {}

        # Add the graph_qa_keys + doc_based_keys results to the dictionary
        combined_keys = {**graph_qa_keys, **doc_based_keys}
        combined_keys= self._process_dynamic_threshould(combined_keys)
        logger.debug("get_resp_for_mapped_keys combined_keys :%s", combined_keys)
        combined_keys = dict(sorted(combined_keys.items(), key=lambda item: float(item[1]), reverse=True))
        for each_graph_qa_key, score in combined_keys.items():

            section_temp = each_graph_qa_key.split(">>")[0].strip()

            normalized_section_name = self._get_normalized_section_name(section_temp)

            if normalized_section_name is None:
                continue

            # taking 2 items from KG approach if its operation section
            if normalized_section_name == cs.IOConstants.HY_OPERATION and each_graph_qa_key in graph_qa_keys:
                flag_to_have_only_top_2_keys_for_operation_kg += 1
            if normalized_section_name == cs.IOConstants.HY_OPERATION and flag_to_have_only_top_2_keys_for_operation_kg > 2:
                continue

            actual_matched_result = each_graph_qa_key.split(">>")[1].strip()
            if each_graph_qa_key in graph_qa_keys:
                temp_dict_to_update = {actual_matched_result: "kg"}
            else:
                temp_dict_to_update = {actual_matched_result: "doc"}
            # For give best matches
            best_matches.append({"key":actual_matched_result, "section": normalized_section_name,
                                 "approach": temp_dict_to_update[actual_matched_result],
                                 "score":score})
            if normalized_section_name in nested_dict_of_sections_and_mapped_keys:
                nested_dict_of_sections_and_mapped_keys[normalized_section_name].update(temp_dict_to_update)
            else:
                nested_dict_of_sections_and_mapped_keys[normalized_section_name] = temp_dict_to_update

        # Add the doc_based_keys results to the dictionary
        logger.debug("nested_dict_of_sections_and_mapped_keys: {} ".format(nested_dict_of_sections_and_mapped_keys))
        logger.debug("best_matches output: {} ".format(best_matches))
        return nested_dict_of_sections_and_mapped_keys, best_matches

    def get_resp_in_html(self, db_results, section, title, approach, standardized=1, section_hierarchy=None,
                         partnumber=None):
        """
        Create a response in HTML for the solution based on the approach kg or doc

        Args:
            db_results (dict): Raw results from doc based or KG qa based approach
            section (str): section of the user selected key
            title (str): the main title of the content to render in html
            approach (str): kg / doc
            standardized: In case of doc based approach this indicates the level of standardization, 1 - Simple,
            2 - Nested Format, 0 - Not Formatted

        Returns:
            dict: Response in a dictionary format Example:
                    { "title": "Diagnosing with beep",
                        "content": [{
                            "cause": "Steps to be followed",
                            "solution": "<html> <body> 1. Close the door and press the power button.<br><br>2. Touch the phone to the smart diagnostic logo (c, d).<br>
                            <br>3. Make sure the microphone is facing the product.<br><br><img style =
                            \"display: block;margin: 0 auto;\"src =\"/image_db/washing_machine/MFL71485465/troubleshooting/diagnosing_a_fault/smart_diagnosis. png\"/>
                            </body> </html>"
                        }
                        ]
                    }
        """
        # standardized indicates Levels of formatting describing the intermediate JSON i.e, db_results['features']
        # standardized = 1 : Indicates a list of Features
        # standardized = 2 : Indicates a list of Features along with title
        # standardized = 0 : Not standardized, a default HTML is sent
        # Create content without HTML
        logger.debug("db_results: {} section: {} title: {}, approach: {}".format(db_results, section, title, approach))
        # list of case and solutions
        # Integrate images
        final_dictionary_to_return = {}
        if approach == KG_APPROACH:
            final_dictionary_to_return = self._get_resp_in_html_kg_based(db_results, section, title, section_hierarchy,
                                                                         partnumber)
        elif approach == DOC_APPROACH:
            final_dictionary_to_return = self._get_resp_in_html_doc_based(db_results, section, title, standardized,
                                                                          section_hierarchy, partnumber)

        # For each solution apply _create_html_for_each_solution
        logger.debug("output: {} ".format(final_dictionary_to_return))
        return final_dictionary_to_return

    def _get_resp_in_html_kg_based(self, db_results, section, title, section_hierarchy=None, partnumber=None):
        """
        Create HTML response for KG QA approach based on the section
        """
        final_dictionary_to_return = {}
        if section.lower() == "troubleshooting":
            try:
                partialxml = self.xmlextractor.getpartialxml(partnumber, section_hierarchy)
                wholexml = self.xmlextractor.addnamespacetoxml(partialxml)
                logger.debug("wholexml : %s", wholexml)
                html = self._get_transformed_html(wholexml, section_hierarchy, partnumber)

                if html != None:
                    final_dictionary_to_return = {"title": title,
                                                  "content": [{"cause": STEPS_TO_BE_FOLLOWED, "solution": html}]}
                    return final_dictionary_to_return
            except Exception as e:
                logger.debug("Exception in HTML transformation : " + str(e))
            final_dictionary_to_return = self._get_resp_in_html_for_troubleshooting(db_results, title)
            # Put multiple causes into a single cause
        elif section.lower() == "operation":
            final_dictionary_to_return = self._get_resp_in_html_for_operation(db_results, title)
            # Default cause should be "cause": "Steps to be followed",
        return final_dictionary_to_return

    def _translate_title_name(self, main_title):
        for key, value in cs.ExtractionConstants.XSLT_SECTION_NAMING_LIST.items():
            if main_title in value:
                return key
        return None

    def _get_img_path(self, main_title, partnumber):
        trans_title = self._translate_title_name(main_title)

        if trans_title is not None:
            main_title = trans_title

        img_path = "http://"+self.ip_address+":"+self.port_number+"/static" + "/" + partnumber + "/"
        return img_path

    def _get_transformed_html(self, xml_string, section_hierarchy, partnumber):
        titles = self.xmlextractor.get_titles(section_hierarchy)
        fig_path = self._get_img_path(titles[0], partnumber)
        post_object = json.dumps({"fig_path": fig_path, "xml_string": xml_string})
        response_doc_results = requests.post(self.html_transformer_ip, data=post_object,
                                             headers=self.headers)
        # print("doc approach results : ", str(response_doc_results.json()))
        response_doc_results = json.loads(response_doc_results.text)
        response_code = response_doc_results["response_code"]
        logger.debug("html_response : %s", response_doc_results)

        if response_code == 0:
            return response_doc_results["html_response"]
        return None

    def _get_resp_in_html_doc_based(self, db_results, section, title, standardized=1, section_hierarchy=None,
                                    partnumber=None):
        """
        Create HTML response for Document based approach
        """
        logger.debug("\nPARSING DOC BASED RESULTS\n")
        logger.debug("db_results: {} ".format(db_results))
        logger.debug("section: {} ".format(section))
        logger.debug("title: {} ".format(title))
        logger.debug("standardized: {} ".format(standardized))
        html_response_for_doc_based = {"title": title}
        final_content_for_solution = ""
        html_transform_flag = False

        try:
            partialxml = self.xmlextractor.getpartialxml(partnumber, section_hierarchy)
            wholexml = self.xmlextractor.addnamespacetoxml(partialxml)
            logger.debug("wholexml : %s", wholexml)
            html = self._get_transformed_html(wholexml, section_hierarchy, partnumber)

            if html != None:
                final_content = [{"cause": STEPS_TO_BE_FOLLOWED, "solution": html}]
                html_transform_flag = True
        except Exception as e:
            logger.debug("Exception in HTML transformation : " + str(e))
            html_transform_flag = False

        if not html_transform_flag:
            if standardized == 1:
                feature_desc_list = db_results[list(db_results.keys())[0]][cs.FEATURES]

                # The first feature is always a heading
                heading_feature = feature_desc_list[0]
                heading = heading_feature.get(cs.FEATURE, None)
                html_for_heading, ending_info = self._get_resp_in_html_for_a_heading(heading_feature)
                html_response_for_doc_based["title"] = heading
                #
                feature_desc_list = feature_desc_list[1:]
                temp_content = self._get_intermediate_content_for_html_generation(feature_desc_list)

                # Call the HTML function to create the HTML for each solution
                final_content_for_solution = self._create_html_for_unstructured_info(temp_content,
                                                                                         heading=html_for_heading,
                                                                                     ending=ending_info)
                final_content = [{"cause": STEPS_TO_BE_FOLLOWED, "solution": final_content_for_solution}]
            elif standardized == 2:
                feature_desc_list = db_results[list(db_results.keys())[0]][cs.FEATURES]
                feature_desc_as_multiple_sections = self._split_features_as_multiple_sections(feature_desc_list)
                for i, each_feature_list in enumerate(feature_desc_as_multiple_sections):
                    # The first feature is always a heading
                    heading_feature = each_feature_list[0]
                    heading = heading_feature.get(cs.FEATURE, None)
                    html_for_heading, ending_info = self._get_resp_in_html_for_a_heading(heading_feature)
                    # Add the first feature as a title
                    if i == 0:
                        html_response_for_doc_based["title"] = heading
                    each_feature_list = each_feature_list[1:]
                    temp_content = self._get_intermediate_content_for_html_generation(each_feature_list)

                    # Call the HTML function to create the HTML for each solution
                    final_content_for_solution += self._create_html_for_unstructured_info(temp_content, heading=html_for_heading,
                                                                                         ending=ending_info)
                final_content = [{"cause": STEPS_TO_BE_FOLLOWED, "solution": final_content_for_solution}]
            else:
                html_content = db_results[list(db_results.keys())[0]][cs.FEATURES][1][cs.FEATURE]
                final_content = [{"cause": STEPS_TO_BE_FOLLOWED, "solution": html_content}]
        html_response_for_doc_based["content"] = final_content
        return html_response_for_doc_based

    def _split_features_as_multiple_sections(self, feature_desc_list):
        """Split the feature description list to multiple list based on the title i.e., as a list of lists"""
        final_feature_lists = []
        temp_feature_list = []
        for each_feature in feature_desc_list:
            is_title = each_feature.get("is_title", "")
            if is_title:
                if temp_feature_list: final_feature_lists.append(temp_feature_list)
                temp_feature_list = []
                temp_feature_list.append(each_feature)
            else:
                temp_feature_list.append(each_feature)
        final_feature_lists.append(temp_feature_list)
        return final_feature_lists

    def _get_intermediate_content_for_html_generation(self, features_list):
        """
        Create intermediate content for final html generation. To avoid duplicates the
        temp_content(return value) will be in the form:
        {feature: {"some_text":"text", "some_image_path":"img", tuple(list_of_notes):"notes"}}
        """
        logger.debug("input: {} ".format(features_list))
        temp_content = {}
        for feature in features_list:
            current_feature = feature[cs.FEATURE]
            current_desc = feature.get(cs.DESC_KEY, "")
            current_image = feature.get(cs.MEDIA, None)
            current_notes_list = feature.get(NOTE, None)
            current_caution_list = feature.get(cs.CAUTION, None)
            current_warning_list = feature.get(WARNING, None)
            # To handle any images inside the description
            # the current_desc can str and and also a list
            if isinstance(current_desc, str):
                current_desc = self._check_fill_image_details_in_desc(current_desc)
                new_content = current_desc
            elif isinstance(current_desc, list):
                current_desc = map(self._check_fill_image_details_in_desc, current_desc)
                new_content = tuple(current_desc)
            new_content_type = "text"
            self._add_new_content_to_intermediate_content(current_feature, new_content, new_content_type,
                                                          temp_content)
            # Add the image information as {"image_path":"img"}
            if current_image is not None:
                absolute_image_path = self._get_image_path(current_image)
                new_content_type = "img"
                self._add_new_content_to_intermediate_content(current_feature, absolute_image_path, new_content_type,
                                                              temp_content)
            # To handle extra info like notes caution or warning
            if current_notes_list is not None and isinstance(current_notes_list, list):
                new_content = tuple(current_notes_list)
                new_content_type = NOTE
                self._add_new_content_to_intermediate_content(current_feature, new_content, new_content_type,
                                                              temp_content)
            if current_caution_list is not None and isinstance(current_caution_list, list):
                new_content = tuple(current_caution_list)
                new_content_type = cs.CAUTION
                self._add_new_content_to_intermediate_content(current_feature, new_content, new_content_type,
                                                              temp_content)
            if current_warning_list is not None and isinstance(current_warning_list, list):
                new_content = tuple(current_warning_list)
                new_content_type = WARNING
                self._add_new_content_to_intermediate_content(current_feature, new_content, new_content_type,
                                                              temp_content)
        logger.debug("output: {} ".format(temp_content))
        return temp_content

    def _add_new_content_to_intermediate_content(self, current_feature, new_content, new_content_type, temp_content):
        """
        Utility function used to add new content to temp content
        """
        if current_feature in temp_content:
            temp_content[current_feature].update({new_content: new_content_type})
        else:
            temp_content[current_feature] = {new_content: new_content_type}

    def _get_resp_in_html_for_troubleshooting(self, db_results, title):
        """
        Utility function generate response for troubleshooting section in KG graph approach
        """
        final_dictionary_to_return = {"title": title}
        # Flag variable to know whether structured or unstructured
        unstructured = False
        cause_sols_list = db_results["troubleshooting"][cs.CAUSES_SOL_KEY]
        temp_content = {}
        unstructured = any("media" in each_reason_sol.keys() for each_reason_sol in cause_sols_list)
        for each_reason_solution in cause_sols_list:
            current_cause = each_reason_solution[cs.REASON_KEY]
            current_solution = each_reason_solution[cs.SOLUTION_KEY]
            current_image = each_reason_solution.get(cs.MEDIA, None)
            if current_cause in temp_content:
                temp_content[current_cause].update({current_solution: "text"})
            else:
                # Add the cause as a Title first to the current cause
                if not unstructured:
                    temp_content[current_cause] = {current_cause: "bold_text"}
                    temp_content[current_cause].update({current_solution: "text"})
                else:
                    temp_content[current_cause] = {current_solution: "text"}
            # Add the image information as {"image_path":"img"}
            if current_image is not None:
                unstructured = True
                absolute_image_path = self._get_image_path(current_image)
                temp_content[current_cause] = {absolute_image_path: "img"}
        # Call the HTML function to create the HTML for each solution
        if unstructured:
            # TODO uncomment if the heading is required
            # add_title_as_heading = self.html_template_for_heading.format(heading=title)
            final_content_for_solution = self._create_html_for_unstructured_info(temp_content)
            final_content = [{"cause": STEPS_TO_BE_FOLLOWED, "solution": final_content_for_solution}]
            final_dictionary_to_return["content"] = final_content
        else:
            temp_content = {key: self._create_html_for_structured_info(list_of_sols) for key, list_of_sols in
                            temp_content.items()}
            final_content = [{"cause": key, "solution": value} for key, value in temp_content.items()]
            final_dictionary_to_return["content"] = final_content
        return final_dictionary_to_return

    def _get_image_path(self, current_image):
        """To get the absolute image path"""
        img_path = current_image[cs.MEDIA_URL]
        absolute_image_path = os.path.join(self.image_folder_path, img_path)
        return absolute_image_path

    def _get_resp_in_html_for_operation(self, db_results, title):

        final_dictionary_to_return = {"title": title}
        feature_desc_list = db_results["operation"][cs.FEATURES]
        # The first feature is always a heading
        heading_feature = feature_desc_list[0]
        heading = heading_feature.get(cs.FEATURE, None)
        html_for_heading, _ = self._get_resp_in_html_for_a_heading(heading_feature)
        final_dictionary_to_return["title"] = heading
        feature_desc_list = feature_desc_list[1:]
        temp_content = self._get_intermediate_content_for_html_generation(feature_desc_list)

        # Call the HTML function to create the HTML for each solution
        final_content_for_solution = self._create_html_for_unstructured_info(temp_content, heading=html_for_heading)
        final_content = [{"cause": STEPS_TO_BE_FOLLOWED, "solution": final_content_for_solution}]
        final_dictionary_to_return["content"] = final_content
        return final_dictionary_to_return

    def _check_fill_image_details_in_desc(self, desc):
        """
        check the embedded image details in description text and frame the HTML image tags

        Ex: In desc the image details will be embedded like
        건조 중 발생하는 진동으로 건조물이 건조 선반에서 떨어질 수 있습니다.
        <img>{\"img_path\": \"dryer/MFL71424392/operation/건조_선반을_사용하여_건조하기/rack_dry_vivace_03.png\"
        , \"file_size\":6,\"type\": \"png\"}</img>

        Args:
            desc: Description string
        Return:
            Description embedded with HTML image tag details
        """
        img_html_tag = "</img>"
        while True:
            if ("<img>" in desc) and (img_html_tag in desc):
                idx = desc.index("<img>")
                # get the start index of <img>
                start = idx + 4
                logger.debug("index of img end : %s", desc.index(img_html_tag))
                # get the index of the </img> from the desc string
                end_idx = desc.index(img_html_tag) + 5
                # convert the image detail in string format to dict
                img_detail = eval(desc[start + 1:end_idx - 5].strip())
                logger.debug("img_detail : %s", img_detail)
                absolute_image_path = os.path.join(self.image_folder_path, img_detail['img_path'])
                image_in_html = self.html_template_for_images.format(image_path=absolute_image_path)
                desc = desc[:idx] + "<br>" + image_in_html + "<br>" + desc[end_idx + 1:]
            else:
                break
        return desc

    def _get_normalized_section_name(self, section_name):
        """
        Normalize the section name to standard section names in korean
        """
        for normalized_section_name, different_section_names in self.normalized_section_names.items():
            if any(section_name.lower() == x.lower() for x in different_section_names):
                return normalized_section_name
        return None

    def _create_html_for_structured_info(self, list_of_solutions, html_style_for_section="troubleshooting"):
        """
        Create html for structured info
        """
        final_html_response = ""
        if html_style_for_section == "troubleshooting":
            for each_solution, each_solution_type in list_of_solutions.items():
                if each_solution_type == "bold_text":
                    final_html_response += self.html_template_for_heading.format(heading=each_solution)
                else:
                    final_html_response += self.html_template_for_each_element.format(each_element=each_solution)

            final_html_response = self.html_template_for_unordered_list.format(list_content=final_html_response)

        final_html_response = self.main_html_frame.format(content=final_html_response)
        return final_html_response

    def _create_html_for_unstructured_info(self, content, heading=None, ending=None):
        """
        Create html for unstructured information
        """
        final_html_response = ""
        for each_reason_or_feature, each_sol_or_desc_list in content.items():
            # <ordered list start> Create a reason or feature list
            final_html_response += self.html_template_for_each_element.format(each_element=each_reason_or_feature)

            # <unordered list start> Create a solutions list
            content_under_feature_or_heading = ""
            for each_element, element_type in each_sol_or_desc_list.items():
                # Remove unnecessary info
                if self._element_is_not_valid(each_element):
                    continue
                content_under_feature_or_heading = self._create_desc_content_for_unstructured_info(
                    content_under_feature_or_heading, each_element, element_type)
            # <unordered list start>Enclose with a html_template_for_unordered_list
            final_html_response += self.html_template_for_unordered_list.format(
                list_content=content_under_feature_or_heading)

        # <ordered list ends> Enclose with a html_template_for_ordered_list
        final_html_response = self.html_template_for_ordered_list.format(list_content=final_html_response)

        # Add Heading if any
        if heading is not None:
            final_html_response = heading + final_html_response

        if ending is not None:
            final_html_response = final_html_response + ending

        # Enclose with a main_html_frame
        final_html_response = self.main_html_frame.format(content=final_html_response)
        return final_html_response

    def _create_desc_content_for_unstructured_info(self, content_under_feature_or_heading, each_element, element_type):
        extra_info = {}
        if element_type == "bold_text":
            # This is a description which can be both a string and also a tuple (collection of descriptions)
            heading_for_trob_unstructured_info = self.html_template_for_heading.format(heading = each_element)
            content_under_feature_or_heading += heading_for_trob_unstructured_info
        elif element_type == "text":
            # This is a description which can be both a string and also a tuple (collection of descriptions)
            desc_in_html = self._create_html_for_description(each_element)
            content_under_feature_or_heading += desc_in_html
        elif element_type == "img":
            content_under_feature_or_heading += self.html_template_for_images.format(image_path=each_element)
        # To handle extra info
        elif element_type in [NOTE, cs.CAUTION, WARNING]:
            extra_info[element_type] = list(each_element)
        if len(extra_info) > 0:
            content_under_feature_or_heading += self._create_html_for_extra_info(feature=extra_info)
        return content_under_feature_or_heading

    def _create_html_for_description(self, desc_in_str_or_list):
        """HTML response generation for a description tag"""
        desc_in_html = ""
        if isinstance(desc_in_str_or_list, str):
            # Split into bullet points based on the . character
            desc_in_str_or_list = desc_in_str_or_list.split(".")

            # To remove empty strings
            desc_in_str_or_list = list(map(lambda x: x.strip(), desc_in_str_or_list))
            desc_in_str_or_list = list(filter(len, desc_in_str_or_list))
        # elif isinstance(desc_in_str_or_list, tuple) or isinstance(desc_in_str_or_list, list):
        apply_html_li_tags = lambda x: self.html_template_for_each_element.format(each_element=x)
        desc_list_as_html_li_tags = map(apply_html_li_tags,
                                        desc_in_str_or_list)
        desc_list_as_html_li_tags = "".join(desc_list_as_html_li_tags)
        desc_in_html = desc_list_as_html_li_tags
        return desc_in_html

    def _get_resp_in_html_for_a_heading(self, heading_feature):
        """HTML response generation for a heading tag"""
        heading_html = ""
        # TODO Uncomment if the heading is required
        heading_title = heading_feature[cs.FEATURE]
        heading_desc = heading_feature.get(cs.DESC_KEY, None)
        heading_image = heading_feature.get(cs.MEDIA, None)
        # TODO Uncomment if the heading is required
        if heading_title is not None:
            heading_html += self.html_template_for_heading.format(heading=heading_title)
        if not self._element_is_not_valid(heading_desc):
            desc_in_html = self._create_html_for_description(heading_desc)
            heading_html += self.html_template_for_paragraph.format(paragraph=desc_in_html)
        if heading_image is not None:
            absolute_image_path = self._get_image_path(heading_image)
            heading_html += self.html_template_for_images.format(image_path=absolute_image_path)

        extra_info_in_html = self._create_html_for_extra_info(feature=heading_feature)
        # ending_info is any extra note caution or warning
        ending_info = extra_info_in_html

        return heading_html, ending_info

    def _element_is_not_valid(self, element):
        """Checks for the validity of desc elements"""
        checks_if_is_a_list = isinstance(element, list) and len(element) == 0
        checks_is_it_is_a_string = (isinstance(element, str) and element.strip() in self.invalid_elements)
        if element is None or checks_is_it_is_a_string or checks_if_is_a_list:
            return True

        return False

    def _create_html_for_extra_info(self, feature):
        """
        HTML content for extra info
        """
        extra_info_html = ""

        notes_list = feature.get(NOTE, None)
        caution_list = feature.get(cs.CAUTION, None)
        warning_list = feature.get(WARNING, None)

        if notes_list is not None and isinstance(notes_list, list):
            extra_info = notes_list
            title = NOTE_TITLE_IN_HTML
            extra_info_html += self._create_html_for_each_extra_info(extra_info, title)
        if caution_list is not None and isinstance(caution_list, list):
            extra_info = caution_list
            title = CAUTION_TITLE_IN_HTML
            extra_info_html += self._create_html_for_each_extra_info(extra_info, title)
        if warning_list is not None and isinstance(warning_list, list):
            extra_info = warning_list
            title = WARNING_TITLE_IN_HTML
            extra_info_html += self._create_html_for_each_extra_info(extra_info, title)

        return extra_info_html

    def _create_html_for_each_extra_info(self, extra_info, title):
        extra_info_html = ""
        convert_to_html_lists = lambda x: self.html_template_for_each_element.format(each_element=x)
        html_list = map(convert_to_html_lists, extra_info)
        html_unordered_list = "".join(html_list)
        html_unordered_list = self.html_template_for_unordered_list.format(list_content=html_unordered_list)
        extra_info_html += self.html_template_for_note_caution_warning.format(title=title,
                                                                              extra_info_content=html_unordered_list)
        return extra_info_html
        
        
    def _process_dynamic_threshould(self, combined_keys):
        """
        This function filters keys which are within top TH_PERCENTILE*100
        percentile withing current key with maximum score only if the maximum score is greater
        a qualifying score (50%)

        Parameters
        ----------
        combined_keys : Dictionary
            DESCRIPTION.

        Returns
        -------
        combined_keys: TYPE dictionary
            DESCRIPTION.

        """
        try:
            combined_keys_copy={}
            max_dynamic_score=max(combined_keys.values())
            if max_dynamic_score >= QUALIFYING_SCORE_TO_APPLY_DYNAMIC_THRESHOLD:
                dynamic_th= max_dynamic_score*(1-TH_PERCENTILE)
                for key, value in combined_keys.items():
                    if value >=dynamic_th or value==0.0:
                        combined_keys_copy[key]=value
            else:
                combined_keys_copy = combined_keys
        except Exception as e:
            logger.exception(e)
            combined_keys_copy=combined_keys
        logger.debug("_process_dynamic_threshould combined_keys_copy : %s", combined_keys_copy)
        return combined_keys_copy


if __name__ == "__main__":
    obj = KerResponseEngine()

    # For Sample testing
    test = {
        "operation": {
            "features":[{
        "desc": ["자주 사용하는 세탁 코스와 세탁 코스별 옵션들을 선택하여 저장하면 내마음 버튼만 누르면 간편하게 자주 사용하는 코스로 세탁할 수 있습니다."],
        "feature": "내마음 코스를 설정하기"
    }, {
        "desc": ["내마음 코스"],
        "feature": "내마음 코스 사용하기"
    }, {
        "desc": ["내마음 코스를"],
        "feature": "내마음 코스를 설정하기"
    }
]


        }
    }
    print(obj.get_resp_in_html(db_results=test, section="operation",
                               title="섬유 유연제 넣고",
                               approach="doc"))
