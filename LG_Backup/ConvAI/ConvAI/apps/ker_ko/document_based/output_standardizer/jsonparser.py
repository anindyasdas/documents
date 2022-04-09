# -------------------------------------------------
# Copyright(c) 2021-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------

import os

from .json_standardizer import JSONParser as jp
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)


class JSONParser(object):

    def __init__(self):

        self.step_key = "단계"
        self.explanation = "설명"
        self.figure_key = "figure"
        self.graphic_key = "graphic"
        self.note_key = "note"
        self.caution_key = "주의"
        self.warning_key = "경고"
        self.summary = "요약"
        self.procedure = "절차"
        self.extra_info_tags = [self.note_key, self.caution_key, self.warning_key]
        self.standard_tags = [self.step_key, self.explanation, self.figure_key, self.graphic_key,
                              self.note_key, self.caution_key, self.warning_key,
                              self.summary, self.procedure]
        self.custom_key_list = ["요약", "설명", "절차", "단계", "주의", "경고", "특징", "특징"]

        self.table_keys = ["세탁코스 (최대용량)", "최대 세탁 용량"]
        
        self.json_standardizer = jp()

    def standardize_doc_based_json(self, raw_json, section_title, section=None):
        logger.debug("***********CALLING STANDARDIZE_DOC_BASED_JSON**************")
        logger.debug("raw_json: {} \n\n section_title: {}  \n\n section: {}".format(raw_json, section_title, section))

        # TODO get the section (ex: Operation)
        # Fill the response code
        feature_list = None
        # standardized indicates Levels of formatting describing the intermediate JSON
        # standardized = 1 : Indicates a list of Features
        # standardized = 2 : Indicates a list of Features along with title information
        # standardized = 0 : Not standardized, a default HTML will be sent
        standardized = 1
        try:
            feature_list_tmp, standardized = self._get_list_of_feature_desc(raw_json, section_title)
            if standardized:
                feature_list = feature_list_tmp
            else:
                logger.debug("METHOD 2 OF STANDARDIZING ALSO FAILED")
                logger.debug("Could not Standardized Internally. Will be sending the HTML framed by QA Engine")
                feature_list = []
                first_feature = {"feature": section_title}
                feature_list.append(first_feature)
                feature_list.append({"feature": section_title})
        except Exception:
            logger.exception("Some exception in Standardizing")
            logger.debug("Could not Standardized Internally. Will be sending the HTML framed by QA Engine")
            standardized = 0
            feature_list = []
            first_feature = {"feature": section_title}
            feature_list.append(first_feature)
            feature_list.append({"feature": section_title})
        logger.debug("feature_list: {} \n\n standardized: {}".format(feature_list, standardized))
        return feature_list, standardized

    def _get_list_of_feature_desc(self, raw_json, section_title):
        # Default level is 1 (which can be standardized internally)
        standardized = 1
        features_list = []
        _, feature, desc = self._dict_keys("")
        if isinstance(raw_json, list):
            features_list_temp = {feature: section_title, desc: raw_json}
            features_list.append(features_list_temp)
        if isinstance(raw_json, dict):
            final_dictionary, new_title, multiple_features_available = self._collapse_the_dictionary(raw_json,
                                                                                                     section_title)

            logger.debug("Collapsed dictionary: {} \n\n new_title: {}".format(final_dictionary, new_title))
            if not multiple_features_available:
                # Process the final_dictionary to give list of features
                features_list = self._process_and_get_feature_desc(final_dictionary, new_title)
            else:
                logger.debug("METHOD 1 OF STANDARDIZING FAILED")
                # Call _collapse_the_dictionary for all the keys to remove unwanted keys
                final_dictionary_removing_repeated_titles = {}
                for each_title_key, each_content in final_dictionary.items():
                    # Clean the dictionary once again like removing the
                    if isinstance(each_content, dict):
                        final_content, final_title, multiple_features_available = self._collapse_the_dictionary(each_content,
                                                                                                                 each_title_key)
                        final_dictionary_removing_repeated_titles.update({final_title: final_content})
                    else:
                        final_dictionary_removing_repeated_titles.update({each_title_key: each_content})
                logger.debug("Collapsed dictionary after cleaning data modelling keys: {} \n\n new_title: {}".format(final_dictionary_removing_repeated_titles, new_title))
                features_list, standardized = self.json_standardizer.standardize_doc_based_json(final_dictionary_removing_repeated_titles,
                                                                                                   new_title)
        return features_list, standardized

    def _process_and_get_feature_desc(self, processed_json, final_title):

        feature_list = []
        _, feature, desc = self._dict_keys("")
        each_feature_desc_dict = {feature: final_title, desc: []}
        procedure_feature_list = None
        internal_feature_list = []
        for each_key, each_value in processed_json.items():

            if each_key == "footnotegroup" or each_key in self.table_keys:
                continue
            internal_feature_list_temp, desc_content_list, note, caution, warning = self._get_content(each_key,
                                                                                                      each_value,
                                                                                                      caller_is_process_and_get_feature_desc=True)
            if internal_feature_list_temp is not None:
                internal_feature_list.extend(internal_feature_list_temp)
            figure = self._get_media_info_from_figure(each_key, each_value)
            if desc_content_list is not None:
                each_feature_desc_dict[desc].extend(desc_content_list)
            if note is not None:
                each_feature_desc_dict["note"] = note
            if caution is not None:
                each_feature_desc_dict["caution"] = caution
            if warning is not None:
                each_feature_desc_dict["warning"] = warning
            if figure is not None:
                each_feature_desc_dict.update(figure)

            # To handle procedures
            if each_key == self.procedure:
                procedure_feature_list = self._parse_procedure(each_value)

        feature_list.append(each_feature_desc_dict)
        if procedure_feature_list is not None:
            feature_list.extend(procedure_feature_list)
        if len(internal_feature_list) > 0:
            feature_list.extend(internal_feature_list)
            internal_feature_list = []

        return feature_list

    def _collapse_the_dictionary(self, raw_json, section_title, multiple_features=False):
        final_dictionary = raw_json
        new_title = section_title

        len_of_the_current_raw_dict = len(raw_json.keys())
        current_list_of_keys = list(raw_json.keys())
        if len_of_the_current_raw_dict == 1:
            first_key_name = list(raw_json.keys())[0]
            new_title += self._create_title(str(first_key_name), existing_title=new_title)
            if first_key_name not in self.standard_tags:
                updated_json = raw_json[first_key_name]
                final_dictionary, new_title, multiple_features = self._collapse_the_dictionary(updated_json, new_title,
                                                                                               multiple_features)
            else:
                return final_dictionary, new_title, multiple_features
        elif len_of_the_current_raw_dict > 1:
            if all(each_current_key in self.standard_tags for each_current_key in current_list_of_keys)\
                    or self._check_for_format_standardizable_by_method_one(final_dictionary):
                return final_dictionary, new_title, multiple_features
            else:
                final_dictionary = raw_json
                multiple_features = True

        return final_dictionary, new_title, multiple_features

    def _check_for_format_standardizable_by_method_one(self, final_dictionary):

        standardizable_by_method_one = True
        for each_key, each_value in final_dictionary.items():
            if isinstance(each_value, dict):
                for each_2nd_level_key, each_2nd_level_value in each_value.items():
                    if isinstance(each_2nd_level_value, dict):
                        standardizable_by_method_one = False
        return standardizable_by_method_one

    def _create_title(self, title, existing_title):

        if existing_title is not None and (title in existing_title):
            return ""
        else:
            return ": " + title

    def _dict_keys(self, section):
        if section == "troubleshootiing":
            return "cause_sol", "cause", "solution"
        else:
            return "features", "feature", "desc"

    def _parse_procedure(self, procedure_dict):
        steps = procedure_dict[self.step_key]
        feature_list = []
        main_key, feature, desc = self._dict_keys("")
        for step, dict_of_steps in steps.items():
            each_feature_desc_dict = {}
            for each_step_key, each_step_value in dict_of_steps.items():

                feature_temp = self._get_feature(each_step_key, each_step_value)
                _, desc_content_list, note, caution, warning = self._get_content(each_step_key, each_step_value)
                figure = self._get_media_info_from_figure(each_step_key, each_step_value)
                if feature_temp is not None:
                    each_feature_desc_dict[feature] = feature_temp
                if desc_content_list is not None:
                    each_feature_desc_dict[desc] = desc_content_list
                if note is not None:
                    each_feature_desc_dict["note"] = note
                if caution is not None:
                    each_feature_desc_dict["caution"] = caution
                if warning is not None:
                    each_feature_desc_dict["warning"] = warning
                if figure is not None:
                    each_feature_desc_dict.update(figure)

            feature_list.append(each_feature_desc_dict)
        return feature_list

    def _check_empty_dict(self, ex_dict):
        if not ex_dict:
            return True
        return False

    def _convert_dict_to_desc(self, exp_dict):
        desc = ""
        for key, value in exp_dict.items():
            desc += key
            if not self._check_empty_dict(value):
                desc += self._convert_dict_to_desc(value)
        return desc

    def _parse_note_warn_caution_content(self, note_dict):
        notes = []
        for key, value in note_dict.items():
            notes.append(key)
            if not self._check_empty_dict(value):
                notes += self._parse_note_warn_caution_content(value)
        return notes

    def _parse_generic_structure(self, ex_dict):
        main_key, main_key1, main_key2 = self._dict_keys("")
        feature_desc = []
        for key, value in ex_dict.items():
            featue_desc_dict = {}
            featue_desc_dict[main_key1] = key
            feature_desc.append(featue_desc_dict)
            for int_key, int_value in value.items():
                int_featue_desc_dict = {}
                if self._check_empty_dict(int_value):
                    continue
                else:
                    int_featue_desc_dict[main_key1] = self._convert_dict_to_desc(int_value)

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
        absolute_image_path = desc
        while True:
            if ("<img>" in desc) and ("</img>" in desc):
                idx = desc.index("<img>")
                # get the start index of <img>
                start = idx + 4
                # get the index of the </img> from the desc string
                end_idx = desc.index("</img>") + 5
                # convert the image detail in string format to dict
                img_detail = eval(desc[start + 1:end_idx - 5].strip())
                absolute_image_path = os.path.join(img_detail['img_path'])
            else:
                break
        return absolute_image_path

    def _get_media_info_from_figure(self, each_step_key, each_step_value):

        media_dict = None
        # TODO Get the relative path
        if each_step_key == self.figure_key:
            media_dict = {}
            relative_path_from_img_db = each_step_value["graphic"][0]

            # Add the pre processing function
            relative_path_from_img_db = self._check_fill_image_details_in_desc(relative_path_from_img_db)
            media_dict["media"] = {}
            media_dict["media"]["mediaUrl"] = relative_path_from_img_db
        elif isinstance(each_step_value, dict) and "figure" in each_step_value:
            media_dict = {}
            relative_path_from_img_db = each_step_value["figure"]["graphic"][0]
            relative_path_from_img_db = self._check_fill_image_details_in_desc(relative_path_from_img_db)
            media_dict["media"] = {}
            media_dict["media"]["mediaUrl"] = relative_path_from_img_db

        return media_dict

    def _get_feature(self, each_step_key, each_step_value):

        feature = None
        if each_step_key == self.explanation:
            feature = " ".join(each_step_value)
        elif each_step_key not in self.standard_tags:
            feature = each_step_key
        return feature

    def _get_content(self, each_step_key, each_step_value, caller_is_process_and_get_feature_desc=False):
        internal_feature_list = None
        desc, note, caution, warning = None, None, None, None
        if each_step_key not in self.standard_tags and isinstance(each_step_value, list):
            if caller_is_process_and_get_feature_desc:
                # TODO Add a the combination key value pairs also for forming the desc
                if len(each_step_value) == 0:
                    desc = [each_step_key]
                else:
                    internal_feature_list = [{"feature": each_step_key, "desc": each_step_value}]
            else:
                desc = each_step_value
        elif each_step_key in [self.explanation, self.summary] and isinstance(each_step_value, list):
            desc = each_step_value
        elif each_step_key in self.extra_info_tags:
            note, caution, warning = self._get_extra_info({each_step_key: each_step_value})
        elif each_step_key not in self.standard_tags and isinstance(each_step_value, dict):

            if caller_is_process_and_get_feature_desc:
                if any(each_key in self.standard_tags for each_key in each_step_value.keys()):
                    internal_feature_list = self._process_and_get_feature_desc(each_step_value, each_step_key)
                else:
                    desc_if_not_all_are_standard_tags = []
                    desc_if_not_all_are_standard_tags.extend(list(each_step_value.keys()))
                    for each_value_in_dict_values in each_step_value.values():
                        if isinstance(each_value_in_dict_values, list):
                            desc_if_not_all_are_standard_tags.extend(each_value_in_dict_values)
                        elif isinstance(each_value_in_dict_values, str):
                            desc_if_not_all_are_standard_tags.append(each_value_in_dict_values)
                    internal_feature_list = [{"feature": each_step_key, "desc": desc_if_not_all_are_standard_tags}]
            else:
                desc = [x for x in each_step_value if x not in self.standard_tags]
                note, caution, warning = self._get_extra_info(each_step_value)

        return internal_feature_list, desc, note, caution, warning

    def _get_extra_info(self, each_step_value):
        note, caution, warning = None, None, None
        if self.note_key in each_step_value:
            extra_info_content = each_step_value[self.note_key]
            if isinstance(extra_info_content, list):
                note = extra_info_content
            if isinstance(extra_info_content, dict):
                note = self._get_extra_info_if_dict(extra_info_content)
        if self.caution_key in each_step_value:
            extra_info_content = each_step_value[self.caution_key]
            if isinstance(extra_info_content, list):
                caution = extra_info_content
            if isinstance(extra_info_content, dict):
                caution = self._get_extra_info_if_dict(extra_info_content)
        if self.warning_key in each_step_value:
            extra_info_content = each_step_value[self.warning_key]
            if isinstance(extra_info_content, list):
                warning = extra_info_content
            if isinstance(extra_info_content, dict):
                warning = self._get_extra_info_if_dict(extra_info_content)

        return note, caution, warning

    def _get_extra_info_if_dict(self, extra_info_content):
        extra_info_content_if_dict = ""
        extra_info_content_if_dict += " ".join(list(extra_info_content.keys()))
        extra_info_content_if_dict += " ".join([" ".join(x) for x in extra_info_content.values()])

        return extra_info_content_if_dict
