# -------------------------------------------------
# Copyright(c) 2021-2022 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------

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
        self.description = "설명"
        self.footnotegroup = "footnotegroup"
        self.is_title_key = "is_title"
        self.detailed_description = "상세 설명"
        self.STANDARDIZED_FLAG = 2
        self.NOT_STANDARDIZED_FLAG = 0
        self.extra_info_tags = [self.note_key, self.caution_key, self.warning_key]
        self.standard_tags = [self.step_key, self.explanation, self.figure_key, self.graphic_key,
                              self.note_key, self.caution_key, self.warning_key,
                              self.summary, self.procedure]
        self.custom_key_list = ["요약", "설명", "절차", "단계", "주의", "경고", "특징", "특징"]
        self.skip_table_key = ["세탁코스 (최대용량)", "세탁 코스", "최대 세탁 용량", '명칭']

    def standardize_doc_based_json(self, raw_json, section_title):

        # Fill the response code
        features_list = []
        standardized_flag = False
        try:
            raw_json = {section_title: raw_json}
            features_list, _, _, _, _, _, standardized_flag = self._get_list_of_feature_desc(raw_json)
        except Exception as e:
            logger.debug("EXCEPTION IN JSON standardize")
            logger.exception(e)
        return features_list, standardized_flag

    def _get_list_of_feature_desc(self, raw_json):

        features_list = []
        feature_desc_dict = {}
        _, feature, desc = self._dict_keys("")
        internal_features_list = []
        desc_list, figure, note, caution, warning = None, None, None, None, None
        standardized_flag = self.STANDARDIZED_FLAG
        idx = 0
        try:
            for each_key, each_value in raw_json.items():
                if each_key == self.procedure:
                    internal_features_list = self._parse_procedure(each_value)
                elif (each_key == self.footnotegroup) or (each_key in self.skip_table_key):
                    continue
                elif (isinstance(each_value, list)) and (each_key not in self.standard_tags):
                    if len(each_value) == 0:
                        if (desc_list is None):
                            desc_list = []
                        desc_list.append(each_key)
                    else:
                        feature_desc_dict[feature] = each_key
                        feature_desc_dict[desc] = each_value
                elif (each_key == self.summary) or (each_key == self.description) or (each_key == self.explanation):
                    if (desc_list is None):
                        desc_list = []
                    if len(each_value) > 0:
                        desc_list.extend(each_value)
                elif each_key == self.detailed_description:
                    internal_features_list += self._parse_detailed_description(each_value)
                elif self.figure_key in each_key:
                    figure = self._get_media_info_from_figure(each_key, each_value)
                elif each_key in self.extra_info_tags:
                    desc_list, note, caution, warning = self._get_content(each_key, each_value)
                elif (each_key == self.summary) or (each_key == self.explanation):
                    if desc_list is None:
                        desc_list = []
                    desc_list.extend(each_value)
                elif isinstance(each_value, dict):
                    feature_desc_dict[feature] = each_key
                    feature_desc_dict[self.is_title_key] = True
                    feature_desc_dict[desc] = []
                    # for reference desc_content_list, note, caution, warning = self._get_content(each_key, each_value)
                    # if desc_content_list is not None:
                    #     feature_desc_dict[desc] = desc_content_list
                    internal_features_list, int_desc_list, int_figure, int_note, int_caution, int_warning, int_std_flag = self._get_list_of_feature_desc(
                        each_value)
                    standardized_flag = int_std_flag
                    if int_desc_list is not None:
                        if desc not in feature_desc_dict:
                            feature_desc_dict[desc] = []
                        feature_desc_dict[desc] += int_desc_list
                    if int_note is not None:
                        feature_desc_dict["note"] = int_note
                    if int_caution is not None:
                        feature_desc_dict["caution"] = int_caution
                    if int_warning is not None:
                        feature_desc_dict["warning"] = int_warning
                    if int_figure is not None:
                        feature_desc_dict.update(int_figure)

                if not self._check_empty_dict(feature_desc_dict):
                    features_list.append(feature_desc_dict)
                    feature_desc_dict = {}

                if len(internal_features_list) > 0:
                    features_list.extend(internal_features_list)
                    internal_features_list = []

        except Exception as e:
            standardized_flag = self.NOT_STANDARDIZED_FLAG
        return features_list, desc_list, figure, note, caution, warning, standardized_flag

    def _parse_detailed_description(self, detailed_value):
        feature_desc_list = []
        _, feature, desc = self._dict_keys("")
        for key, value in detailed_value.items():
            feature_desc_list.append({feature: key, desc: value})

        return feature_desc_list

    def _dict_keys(self, section):
        if section == "troubleshootiing":
            return "cause_sol", "cause", "solution"
        else:
            return "features", "feature", "desc"

    def _parse_explanation(self, exp_list):

        desc = ""
        for exp_item in exp_list:
            if type(exp_item) is dict:
                for key, value in exp_item.items():
                    if key == self.figure_key:
                        desc += "<img>{\\\"img_path\\\": \\\"" + value + "\\\"}</img>"
                    else:
                        desc += exp_item

    def _parse_procedure(self, procedure_dict):
        steps = procedure_dict[self.step_key]
        feature_list = []
        main_key, feature, desc = self._dict_keys("")
        for step, dict_of_steps in steps.items():
            each_feature_desc_dict = {}
            each_feature_desc_dict[desc] = []
            for each_step_key, each_step_value in dict_of_steps.items():

                feature_temp = self._get_feature(each_step_key, each_step_value)
                desc_content_list, note, caution, warning = self._get_content(each_step_key, each_step_value)
                figure = self._get_media_info_from_figure(each_step_key, each_step_value)
                self._fill_feature_figure_details(desc, desc_content_list, each_feature_desc_dict, feature, feature_temp,
                                                  figure)
                if note is not None:
                    each_feature_desc_dict["note"] = note
                if caution is not None:
                    each_feature_desc_dict["caution"] = caution
                if warning is not None:
                    each_feature_desc_dict["warning"] = warning

            feature_list.append(each_feature_desc_dict)
        return feature_list

    def _fill_feature_figure_details(self, desc, desc_content_list, each_feature_desc_dict, feature, feature_temp,
                                     figure):
        if feature_temp is not None:
            each_feature_desc_dict[feature] = feature_temp
        if desc_content_list is not None:
            each_feature_desc_dict[desc] = desc_content_list
        if figure is not None:
            each_feature_desc_dict.update(figure)

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

    def _get_media_info_from_figure(self, each_step_key, each_step_value):

        media_dict = None
        # TODO Get the relative path
        if self.figure_key in each_step_key:
            media_dict = {}
            relative_path_from_img_db = each_step_value["graphic"][0]
            media_dict["media"] = {}
            media_dict["media"]["mediaUrl"] = relative_path_from_img_db
        elif isinstance(each_step_value, dict) and "figure" in each_step_value:
            media_dict = {}
            relative_path_from_img_db = each_step_value["figure"]["graphic"][0]
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

    def _get_content(self, each_step_key, each_step_value):

        desc, note, caution, warning = None, None, None, None
        if each_step_key not in self.standard_tags and isinstance(each_step_value, list):
            desc = each_step_value
        elif each_step_key in self.extra_info_tags:
            note, caution, warning = self._get_extra_info({each_step_key: each_step_value})
        elif each_step_key not in self.standard_tags and isinstance(each_step_value, dict):
            desc = [x for x in each_step_value if x not in self.standard_tags]
            note, caution, warning = self._get_extra_info(each_step_value)

        return desc, note, caution, warning

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


if __name__ == "__main__":
    json_parser = JSONParser()

    sample_input = {
        "버튼 잠금 기능 설정 또는 해제하기": {
            "note": ["버튼 잠금 기능이 설정되면 전원 버튼을 제외한 어떠한 버튼도 조작되지 않습니다.", "작동 중 설정하면 표시창에 버튼 잠금() 표시가 나타납니다."],
            "탈수 버튼과 물온도 버튼을 3초 정도 눌러 버튼 잠금을 설정 또는 해제할 수 있습니다": []
        },
        "버튼 잠금 기능이 설정되어 있는 상태에서 코스 또는 옵션 변경하기": {
            "note": ["세탁 종료된 후에도 버튼 잠금 기능은 자동 해제가 안 되므로 탈수 버튼과 물온도 버튼을 3초 간 눌러 잠금을 해제하세요.",
                     "부주의로 인해 버튼 잠금 기능이 설정될 경우 탈수 버튼과 물온도 버튼을 3초간 눌러 버튼 잠금 기능을 해제할 수 있습니다.",
                     "버튼 잠금 기능이  설정되어 있는 상태에서 전원을 켜면 버튼 잠금 표시가 깜빡거립니다."],
            "절차": {
                "단계": {
                    "단계 1": {
                        "탈수 버튼과 물온도 버튼을 3초 정도 눌러 버튼 잠금을 해제하세요.": []
                    },
                    "단계 2": {
                        "시작/일시정지 버튼을 눌러 작동을 정지하세요.": []
                    },
                    "단계 3": {
                        "변경하고 싶은 코스 또는 옵션을 선택한 후 다시 시작/일시정지 버튼을 누르세요.": []
                    }
                }
            }
        },
        "요약": ["세탁 진행 중 어린이나 반려동물 등에 의해 원하지 않 는 버튼 조작이 발생하는 것을 방지하고자 할 때 사용하세요."]
    }

    features_list, standardized_flag = json_parser.standardize_doc_based_json(sample_input, "버튼")
