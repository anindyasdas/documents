"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import copy
import json
import os.path
from collections import defaultdict

from ..constants import params as cs
from ..constants.params import GenericProductNameMapping as products
from ..response.json_widget_utils import WidgetCards
# KMS Logger
import importlib

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

WIDGET_FOLDER = (os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..',
                 'resources', 'widget')))


class WidgetConstants(object):
    """
        constants used for to create RCS chatbot widget
    """
    INIT_PROD_REG = "new_bot_user_initiation"
    REPLY = "reply"
    DISP_TEXT = "displayText"
    POSTBACK = "postback"
    RESPONSE = "response"
    DATA = "data"
    ACTION = "action"
    SUGGESTIONS = "suggestions"
    TITLE = "title"
    CONTENT = "content"
    DESC = "description"
    MESSAGE = "message"
    PROD_REG_KEY = "register_product:"
    MODEL_REG_KEY = "register_model:"
    ALIAS_REG_KEY = "register_alias:"
    MESSAGE_HEADER = "messageHeader"
    GENERAL_PURP_CARD = "generalPurposeCard"
    CAROUSEL_CARD = "generalPurposeCardCarousel"
    # Korean string for "Please select any product listed below OR type the product name"
    PROD_REG_MSG = "아래에 나열된 제품을 선택하거나 제품 이름을 입력하십시오"
    # Korean string for "Please select any model listed below OR type the model number"
    MODEL_REG_MSG = "아래에 나열된 제품을 선택하거나 모델 넘버를 입력하십시오"
    # Korean string for "Thanks for the product registration"
    REG_COMPLETION = "제품을 등록해주셔서 감사합니다"
    # Korean string for "Below is the response:"
    MESSAGE_HEADER_MSG = "질문에 대한 답변입니다"
    # Korean string for "Product Register Fails"
    PROD_REG_FAIL = "제품 등록에 실패하였습니다/ 제품 등록 실패 "
    SUCCESS = "success"
    # Korean string for "Product is not valid"
    INVALID_PRODUCT = "올바른 제품이 아닙니다/ 올바른 제품명이 아닙니다 / 해당 제품이 존재하지 않습니다"
    # Korean string for "Product Alias is not valid"
    INVALID_ALIAS = "제품 별칭이 바르지 않습니다/ 제품 별칭이 잘 못 되었습니다. "
    # constants used for media
    MEDIA_HEIGHT_TAG = "height"
    MEDIA_MEDIUM_HEIGHT = "MEDIUM_HEIGHT"
    MEDIA_SHORT_HEIGHT = "SHORT_HEIGHT"
    # get ip address,port and image db
    image_path, ip_address, port_number = cs.get_image_db_path()
    MEDIA_DB = "/" + image_path + "/"
    # MEDIA_DB = "https://www.refrigerator.com/"
    # list of product register messages
    REGISTER_MSGS = [INIT_PROD_REG, "register product", "product register", "registration", "상품을 등록하다",
                     "상품등록", "등록", "등록하다"]
    # list to maintain supported products
    SUPPORTED_PRODUCTS = [products.WASHING_MACHINE_GEN_NAME, products.DRYER_GEN_NAME, products.STYLER_GEN_NAME]

class JsonBuilder(object):
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method to get the singleton instance"""
        if JsonBuilder.__instance is None:
            JsonBuilder.__instance = JsonBuilder()
        return JsonBuilder.__instance

    def __init__(self):
        if JsonBuilder.__instance is not None:
            logger.error("KerEngine is not instantiable")
            raise Exception("KerEngine is not instantiable")
        else:
            self.products_ko = {cs.ProductTypes.WASHING_MACHINE: products.WASHING_MACHINE_GEN_NAME,
                                cs.ProductTypes.DRYER: products.DRYER_GEN_NAME,
                                cs.ProductTypes.STYLER: products.STYLER_GEN_NAME,
                                cs.ProductTypes.KEPLER: products.PRD_KEPLER}
            # alias name table for products
            # "세탁기": {"Washing Machine": ["washing machine", "세탁기"]},
            self.product_alias = {
                cs.ProductTypes.WASHING_MACHINE: {cs.ProductTypes.WASHING_MACHINE:[products.WASHING_MACHINE_GEN_NAME,
                                                                                   cs.ProductTypes.WASHING_MACHINE]},
                cs.ProductTypes.DRYER: {cs.ProductTypes.DRYER:[products.DRYER_GEN_NAME, cs.ProductTypes.DRYER]},
                cs.ProductTypes.STYLER: {cs.ProductTypes.STYLER:[products.STYLER_GEN_NAME, cs.ProductTypes.STYLER]},
                cs.ProductTypes.KEPLER: {cs.ProductTypes.KEPLER: [products.PRD_KEPLER, cs.ProductTypes.KEPLER]}
            }

            # convert string to json string
            self.alias_for_products = self.product_alias

            # maximum carousel card supported is 10
            self._max_trob_widget_cards = 10
            self._carousel_identifier = u'\u00C22\u00C23'

            # file names
            self.prod_alias_file = "product_alias.json"
            self.prod_reg_status_file = "product_register_status.json"
            self.general_purpose_card_file = "general_purpose_card.json"
            self.carousel_card_file = "carousel.json"
            self.carousel_title_file = "carousel_title.json"
            self.product_register_file = "product_register.json"

            # template widgets for spec/ts/operation responses & register status
            self.general_purpose_card = {}
            self.carousel_card = {}
            self.prod_alias_temp = {}
            self.prod_reg_status = {}
            self.carousel_title_temp = {}
            self.init_prod_register = {}
            self.load_json_cards()

    # TODO get current context,product registration

    def __get_ko_product(self, product):
        for key, value in self.products_ko.items():
            if product == value:
                return key
        return None
    def __load_json_file(self, input_json_file):
        """
            loads predefined json card and store it in a variable
            Args:
                input_json_file : file to be read and loaded
            Returns:
                content : read content of given file
        """
        content = ""
        with open(input_json_file, 'r', encoding='utf-8') as f:
            # returns JSON object as a dictionary
            content = json.load(f)
        # Closing file
        f.close()
        return content

    def load_json_cards(self):
        """
            loads all predefined templates of json widget cards
        """
        logger.info("load json cards for RCS")
        # read & load prod alias
        widget_card_file = WIDGET_FOLDER + "/" + self.carousel_title_file
        self.carousel_title_temp = self.__load_json_file(widget_card_file)

        # read & load prod alias
        widget_card_file = WIDGET_FOLDER + "/" + self.prod_alias_file
        self.prod_alias_temp = self.__load_json_file(widget_card_file)

        # read & load prod register status
        widget_card_file = WIDGET_FOLDER + "/" + self.prod_reg_status_file
        self.prod_reg_status = self.__load_json_file(widget_card_file)

        # read & load spec widget
        widget_card_file = WIDGET_FOLDER + "/" + self.general_purpose_card_file
        self.general_purpose_card = self.__load_json_file(widget_card_file)

        # read & load carousel_card widget
        widget_card_file = WIDGET_FOLDER + "/" + self.carousel_card_file
        self.carousel_card = self.__load_json_file(widget_card_file)

        # read & load product register widget
        widget_card_file = WIDGET_FOLDER + "/" + self.product_register_file
        self.init_prod_register = self.__load_json_file(widget_card_file)
        logger.debug("load json cards for RCS END")

    def __create_reply_card(self, template, display_text, postback_data):
        """
            creates reply card for chiplist format
            and send dict
            Args:
                template : dict
                display_text : str
                postback_data : str
            Returns:
                reply_card:dict
        """
        reply_card = json.loads(template)
        logger.debug("replycard=%s", reply_card)
        reply_card[WidgetConstants.REPLY][WidgetConstants.DISP_TEXT] = display_text
        reply_card[WidgetConstants.REPLY][WidgetConstants.POSTBACK][WidgetConstants.DATA] = postback_data
        return reply_card

    def __create_text_display_action_card(self, template, display_text, postback_data):
        """
            creates response card with no action response card for spec response
            and send dict
            Args:
                template : dict
                display_text : str
                postback_data : str
            Returns:
                display_card:dict
        """
        display_card = json.loads(template)
        display_card[WidgetConstants.ACTION][WidgetConstants.DISP_TEXT] = display_text
        display_card[WidgetConstants.ACTION][WidgetConstants.POSTBACK][WidgetConstants.DATA] = postback_data
        return display_card

    def send_prod_types_for_registration(self, model_dict=None, context_not_valid=False):
        """
            get the all product types so far supported in KER
            and send as json string
            Args:
                model_dict : dict
                    dictionary of product and models
                context_not_valid : boolean
            Returns:
                content : json string
        """
        # fill title for product type
        title_content = copy.deepcopy(self.carousel_title_temp)
        logger.debug("model_dict=%s", model_dict)
        product_model_dict = model_dict[cs.resp_data]
        # if context is not valid start product register initiation
        if context_not_valid:
            reg_content = self.init_prod_register
            content = json.dumps(reg_content)
            return content
        else:
            title_content[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
                WidgetConstants.DESC] = WidgetConstants.PROD_REG_MSG
            title_content[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
                WidgetConstants.TITLE] = ''

            prod_list = []
            retrieved_prod_list = list(product_model_dict.keys())
            # get all prod types and create list of carousel entries
            for each_prod in retrieved_prod_list:
                logger.debug("each_prod=%s", each_prod)
                # check we have the product is supported or not in QA
                if each_prod in WidgetConstants.SUPPORTED_PRODUCTS:
                    # TODO spearate discuss logic for korean
                    logger.debug("Supported each_prod=(%s)", each_prod)
                    each_prod = self.__get_ko_product(each_prod)
                    logger.debug("Korean Supported each_prod=(%s)", each_prod)
                    product_short_name = list(self.alias_for_products[each_prod].keys())[0]
                    postback_data = WidgetConstants.PROD_REG_KEY + each_prod
                    each_prod_dict = self.__create_reply_card(WidgetCards.carousel_template, product_short_name, postback_data)
                    logger.debug("product each item=%s", each_prod_dict)
                    prod_list.append(each_prod_dict)

            # create dict and add prod_list for key 'suggestions'
            footer_content = dict()
            footer_content[WidgetConstants.SUGGESTIONS] = prod_list

            content = json.dumps(title_content, ensure_ascii=False) + self._carousel_identifier + json.dumps(footer_content, ensure_ascii=False)
            return content

    def send_prod_models_for_registration(self, prod_type=None, model_dict=None):
        """
            get the model numbers of specified product type
            and send as json string
            Args:
                prod_type : str
                        registered product type
                model_dict : dict
                    dictionary of product and models
            Returns:
                content : json string
        """
        logger.info("model_dict=%s", model_dict)
        product_model_dict = model_dict[cs.resp_data]
        # fill title for product type
        title_content = copy.deepcopy(self.carousel_title_temp)
        title_content[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.DESC] = WidgetConstants.MODEL_REG_MSG
        title_content[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.TITLE] = ''
        model_list = []
        # get models of given product
        # TODO discuss for korean
        logger.debug("1 prod_type=(%s)", prod_type)
        prod_type = self.products_ko[prod_type]
        logger.debug("2 prod_type=(%s)",prod_type)
        models_for_product = product_model_dict[prod_type]

        model_count = 0

        # get all prod types and create list of carousel entries
        for each_model in models_for_product:
            model_count += 1

            # if responses are more than 10, we are limiting to 10
            # as chatbot carousel card supports upto 10
            if model_count > self._max_trob_widget_cards:
                break

            postback_data = WidgetConstants.MODEL_REG_KEY + each_model
            each_model_dict = self.__create_reply_card(WidgetCards.carousel_template, each_model, postback_data)
            model_list.append(each_model_dict)

        # create dict and add prod_list for key 'suggestions'
        footer_content = dict()
        footer_content[WidgetConstants.SUGGESTIONS] = model_list

        content = json.dumps(title_content, ensure_ascii=False) + self._carousel_identifier + json.dumps(footer_content, ensure_ascii=False)
        return content

    def send_prod_alias_for_registration(self, prod_type=None):
        """
            get the alias name of specified product type
            and send as json string
            Args:
                prod_type : str
                        registered product type
            Returns:
                content : json string
        """
        alias_list = []

        # get dynamically product alias name and send
        alias_dict = self.alias_for_products[prod_type]
        for key, alias in alias_dict.items():
            for each_alias in alias:
                # fill each alias
                # product alias json entry is same as reply card(chiplist) json
                postback_data = WidgetConstants.ALIAS_REG_KEY + each_alias
                alias_template = self.__create_reply_card(WidgetCards.carousel_template, each_alias, postback_data)
                alias_list.append(alias_template)
        alias_resp = self.prod_alias_temp
        alias_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.SUGGESTIONS] = alias_list
        return json.dumps(alias_resp)

    def send_prod_registration_status(self, product_alias, model, product_name=None):
        """
            fill the registered product and model in predefined
            template and send it
            Args:
                product_alias : str
                        Alias product name
                model : str
                        registered model name
                product_name : str
                        registered product name
            Returns:
                content : json string
        """
        content = self.prod_reg_status
        content[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.TITLE] = WidgetConstants.REG_COMPLETION
        # sending Korean equivalent for Product: and Model:
        content[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.DESC] = "제품 : " + product_name.capitalize() + "\n" + "모델 : " + model
        return json.dumps(content)

    def __check_if_media(self, db_resp, topic):
        """
            check the input db response has image media tag or not

            Args:
                db_resp : dict
                       db results
            Returns:
                boolean : true if media is present
        """
        hasmedia = False
        key_ele = cs.FEATURES

        if topic == cs.Section.OPERATION:
            key_ele = cs.FEATURES
        elif topic == cs.Section.TROB:
            key_ele = cs.CAUSES_SOL_KEY

        features = db_resp[key_ele]
        # iterate over list of dictionaries, check if image url has image or not
        for key, value in enumerate(features):
            for mediakey, mediavalue in value.items():
                if mediakey == cs.MEDIA and isinstance(mediavalue, dict):
                    hasmedia = True
        return hasmedia

    def __form_imagetext_with_carousel(self, db_resp, topic):
        """
            fill the operation responses in the predefined
            template and returns dict

            Args:
                db_resp : dict
                           operation features db results
                topic : str
                        section of which the db responses belongs to Spec/trob/Oper
            Returns:
                oper_resp : dict
                          dict response for para in carousel card format
        """
        resp_list = []
        features = []
        key1, key2 = "", ""

        if topic == cs.Section.OPERATION:
            features = db_resp[cs.FEATURES]
            key1 = cs.FEATURE
            key2 = cs.DESC_KEY
        elif topic == cs.Section.TROB:
            features = db_resp[cs.CAUSES_SOL_KEY]
            key1 = cs.REASON_KEY
            key2 = cs.SOLUTION_KEY

        logger.info("Input db_resp=%s", str(db_resp))
        logger.debug("Input features=%s", str(features))
        # iterate over list of dictionaries
        for each_dict in features:
            logger.debug("each_dict=%s", str(each_dict))
            feature = each_dict.get(key1, "")
            desc = each_dict.get(key2, "")
            media = each_dict.get(cs.MEDIA, None)
            logger.debug("media=(%s)", media)
            logger.debug("1. feature=(%s) desc=(%s)", feature, desc)
            # for some responses , if we dont get desc or feature, assigning values
            # TODO None has to rechecked
            if (len(desc) == 0) or (desc == "None"):
                logger.debug("key2 is empty")
                desc = feature
                if topic == cs.Section.TROB:
                    desc = ""
            if (len(feature) == 0) or feature is None:
                logger.debug("key1 is empty")
                feature = desc
            logger.debug("2 feature=(%s) desc=(%s)", feature, desc)
            # load para template and fill with each para
            para_each_item = json.loads(WidgetCards.para_template)
            # add new line when dot find in responses
            feature = feature.replace(". ", ".\n")
            desc = desc.replace(". ", ".\n")
            para_each_item[WidgetConstants.TITLE] = feature
            para_each_item[WidgetConstants.DESC] = desc
            # check if media dict in operation response, add to carousel card
            if media is not None:
                para_each_item[cs.MEDIA] = media
                logger.debug("media tag=%s", media)
                # append predefined db server url with media url with
                # para_each_item[cs.MEDIA][cs.MEDIA_URL] = WidgetConstants.MEDIA_DB + \
                #                                          para_each_item[cs.MEDIA][cs.MEDIA_URL]
                para_each_item[cs.MEDIA][cs.MEDIA_URL] = "/image_db/" + para_each_item[cs.MEDIA][cs.MEDIA_URL]
                # para_each_item[cs.MEDIA][cs.MEDIA_URL] = para_each_item[cs.MEDIA][cs.MEDIA_URL]
                # update media height
                para_each_item[cs.MEDIA][WidgetConstants.MEDIA_HEIGHT_TAG] = WidgetConstants.MEDIA_MEDIUM_HEIGHT
            resp_list.append(para_each_item)

        # create the widget with carousel card
        carousel_card_resp = copy.deepcopy(self.carousel_card)
        # add para json in resp
        carousel_card_resp[WidgetConstants.MESSAGE][WidgetConstants.CAROUSEL_CARD][WidgetConstants.CONTENT] = resp_list
        carousel_card_resp[WidgetConstants.MESSAGE][WidgetConstants.CAROUSEL_CARD][WidgetConstants.MESSAGE_HEADER] = \
            WidgetConstants.MESSAGE_HEADER_MSG
        logger.debug("carousel_card_resp=(%s)", carousel_card_resp)
        return carousel_card_resp

    def __form_image_multitext_with_generalpurpose(self, db_resp):
        """
            fill the db responses in the predefined
            template and returns dict

            Args:
                db_resp : dict
                           operation features db results
            Returns:
                oper_resp : dict
                          dict response for para in general purpose card format
        """
        resp_list = []
        media = {}
        features = db_resp[cs.FEATURES]
        logger.debug("Input db_resp=%s", str(db_resp))
        logger.debug("Input features=%s", str(features))
        # create list of reply json card to show , on click of the keys in list
        for each_dict in features:
            media = each_dict.get(cs.MEDIA, None)
            feature = each_dict.get(cs.FEATURE, "")
            desc = each_dict.get(cs.DESC_KEY, "")
            # for some responses , if we dont get desc or feature, assigning values
            if len(desc) == 0:
                desc = feature
            if len(feature) == 0:
                feature = desc
            # add new line when dot find in responses
            feature = feature.replace(". ", ".\n")
            desc = desc.replace(". ", ".\n")
            # WidgetCards.spec_template is used for creating list of entries
            feature_each_item = self.__create_text_display_action_card(WidgetCards.spec_template, feature,
                                                                       desc)
            resp_list.append(feature_each_item)
        # update the outer json card
        img_txt_resp = copy.deepcopy(self.general_purpose_card)
        img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.TITLE] = db_resp[cs.RESPONSE_KEY][cs.PROP_VALUE]
        img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.DESC] = db_resp[cs.RESPONSE_KEY][cs.PROP_VALUE]
        img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.MESSAGE_HEADER] = \
            WidgetConstants.MESSAGE_HEADER_MSG
        img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.SUGGESTIONS] = resp_list

        # update image media
        img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][cs.MEDIA] = media
        # append predefined db server url with media url with
        img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][cs.MEDIA][
            cs.MEDIA_URL] = WidgetConstants.MEDIA_DB + \
                            img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][
                                WidgetConstants.CONTENT][cs.MEDIA][cs.MEDIA_URL]
        # update media height
        img_txt_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][cs.MEDIA][
            WidgetConstants.MEDIA_HEIGHT_TAG] = \
            WidgetConstants.MEDIA_SHORT_HEIGHT

        return img_txt_resp

    def __form_bot_response_for_operation(self, info_mapping, db_resp, template_resp):
        """
            fill the operation responses in the predefined
            template and returns json string
            Args:
                info_mapping : dict
                        extracted knowledge of user query
                db_resp : dict
                        results obtained from KG
                template_resp : str
                        template response created by response engine
                response_key : str
                        specific key info
            Returns:
                json string of widget card
        """
        # extract operation responses
        oper_db_resp = db_resp[cs.XMLTags.OPERATION_TAG]

        logger.debug("Intent=%s", db_resp[cs.XMLTags.OPERATION_TAG][cs.RESPONSE_KEY][cs.INTENT])
        # if response has media content
        if self.__check_if_media(oper_db_resp, cs.Section.OPERATION):
            logger.debug("Media tag is present")
            # check if its control panel response
            if db_resp[cs.XMLTags.OPERATION_TAG][cs.RESPONSE_KEY][cs.INTENT] == cs.HAS_CONTROL_PANEL_FEATURE or \
                    db_resp[cs.XMLTags.OPERATION_TAG][cs.RESPONSE_KEY][cs.INTENT] == cs.HAS_CONTROL_PANEL:
                logger.debug("Only for control panel, will be building one image + multi text")
                oper_resp = self.__form_image_multitext_with_generalpurpose(oper_db_resp)
            else:
                logger.debug("Form carousel card")
                oper_resp = self.__form_imagetext_with_carousel(oper_db_resp, cs.Section.OPERATION)
        # media content is not there and contains only text
        else:
            logger.debug("Media tag is not present")
            oper_resp = self.__form_imagetext_with_carousel(oper_db_resp, cs.Section.OPERATION)

        return oper_resp

    def __form_bot_response_for_troubleshooting(self, info_mapping, db_resp):
        """
            fill the operation responses in the predefined
            template and returns json string
            Args:
                info_mapping : dict
                        extracted knowledge of user query
                db_resp : dict
                        results obtained from KG
            Returns:
                trob_resp : json string of widget card
        """
        # extract operation responses
        trob_db_resp = db_resp[cs.XMLTags.TROUBLESHOOT_TAG]

        # if response has media content
        if self.__check_if_media(trob_db_resp, cs.Section.TROB):
            logger.debug("Media tag is present in troubleshooting section resp")
            logger.debug("Form carousel card")
            trob_rcs_resp = self.__form_imagetext_with_carousel(trob_db_resp, cs.Section.TROB)

        # media content is not there and contains only text
        else:
            trob_resp = db_resp[cs.XMLTags.TROUBLESHOOT_TAG][cs.CAUSES_SOL_KEY]

            # Using list comprehension
            # Get values of particular key in list of dictionaries
            reasons = [eachdict[cs.REASON_KEY] for eachdict in trob_resp]
            solutions = [eachdict[cs.SOLUTION_KEY] for eachdict in trob_resp]

            # converting causes,solutions list to dict and
            # grouping multiple solutions for same cause as key,value pair
            result_dict = defaultdict(list)
            for i in range(len(reasons)):
                result_dict[reasons[i]].append(solutions[i])

            resp_list = []
            cause_sol_count = 0

            for resp_cause, resp_solutions in result_dict.items():
                # if responses are more than 10, we are limiting to 10
                # as chatbot carousel card supports upto 10
                if cause_sol_count > self._max_trob_widget_cards:
                    break
                cause_sol_count += 1

                # remove duplicates if any from solutions list
                resp_solutions = list(set(resp_solutions))

                logger.debug("cause=%s", resp_cause)
                # converting all solutions in a list to string with new line separated
                resp_solutions = '\n'.join(resp_solutions)
                logger.debug("solution=%s", resp_solutions)

                trob_each_item = json.loads(WidgetCards.trob_template)
                # Adding korean tokens for Problem and Cause
                trob_each_item[WidgetConstants.TITLE] = "문제" + ": " + info_mapping[cs.PROP_VALUE]
                trob_each_item[WidgetConstants.DESC] = "원인" + ": " + resp_cause
                trob_each_item[WidgetConstants.SUGGESTIONS][0][WidgetConstants.ACTION][WidgetConstants.POSTBACK][
                    WidgetConstants.DATA] = resp_solutions
                resp_list.append(trob_each_item)

            trob_rcs_resp = copy.deepcopy(self.carousel_card)
            trob_rcs_resp[WidgetConstants.MESSAGE][WidgetConstants.CAROUSEL_CARD][WidgetConstants.CONTENT] = resp_list
        return trob_rcs_resp


    def __form_bot_response_for_specification(self, db_resp, template_resp, response_key):
        """
            fill the operation responses in the predefined
            template and returns json string
            Args:
                info_mapping : dict
                        extracted knowledge of user query
                db_resp : dict
                        results obtained from KG
                template_resp : str
                        template response created by response engine
                response_key : str
                        specific key info
            Returns:
                json string of widget card
        """
        results = db_resp[cs.SPECIFICATION_TAG][cs.VALUE]
        resp_list = []
        for value in results:
            display_text = response_key + ':' + value[cs.VALUE]
            postback_data = response_key + ':' + value[cs.VALUE]
            spec_each_item = self.__create_text_display_action_card(WidgetCards.spec_template, display_text,
                                                                    postback_data)
            resp_list.append(spec_each_item)
        logger.debug("self.general_purpose_card : %s",self.general_purpose_card)
        spec_resp = copy.deepcopy(self.general_purpose_card)
        logger.debug("spec_resp : %s", spec_resp)
        spec_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.TITLE] = template_resp
        spec_resp[WidgetConstants.MESSAGE][WidgetConstants.GENERAL_PURP_CARD][WidgetConstants.CONTENT][
            WidgetConstants.SUGGESTIONS] = resp_list
        return spec_resp

    def send_bot_response_for_userquery(self, info_mapping, db_resp, template_resp, response_key):
        """
            fill the spec/TS responses in the predefined
            template and returns json string
            Args:
                info_mapping : dict
                        extracted knowledge of user query
                db_resp : dict
                        results obtained from KG
                template_resp : str
                        template response created by response engine
                response_key : str
                        specific key info
            Returns:
                json string of widget card
        """
        logger.info("db_resp in get_bot_response_query" + str(db_resp))
        logger.debug("info_mapping={0}, db_resp={1}, template_resp={2}, response_key={3}".format(info_mapping, db_resp,
                                                                                    template_resp, response_key))

        section = info_mapping[cs.ProblemTypes.SECTION].lower()
        # form bot response for specification
        if section == cs.Section.SPEC.lower():
            spec_resp = self.__form_bot_response_for_specification(db_resp, template_resp, response_key)
            return json.dumps(spec_resp)
        # form bot response for troubleshooting
        elif section == cs.Section.TROB.lower():
            trob_resp = self.__form_bot_response_for_troubleshooting(info_mapping, db_resp)
            return json.dumps(trob_resp)
        # form bot response for operation
        elif section == cs.Section.OPERATION.lower():
            oper_resp = self.__form_bot_response_for_operation(info_mapping, db_resp, template_resp)
            return json.dumps(oper_resp)


class ProductRegister(object):
    """
       class defines setter and getter methods for product registration
    """

    def __init__(self):
        self._prod_type = ""
        self._prod_model = ""
        self._prod_alias = ""

    # setter method
    def set_product(self, product):
        """
           setter method to set product type
           Args:
               product : str
           Returns:
                None
        """
        self._prod_type = product

    def set_model(self, model):
        """
           setter method to set model number
           Args:
               model : str
           Returns:
                None
        """
        self._prod_model = model

    def set_alias(self, alias):
        """
           setter method to set alias name
           Args:
               alias : str
           Returns:
                None
        """
        self._prod_alias = alias

    # getter method
    def get_product(self):
        return self._prod_type

    def get_model(self):
        return self._prod_model

    def get_alias(self):
        return self._prod_alias


if __name__ == "__main__":
    resp = "{\"message\":{\"generalPurposeCard\":{\"layout\":{\"cardOrientation\":\"VERTICAL\"},\"content\":{\"description\":\"Please select suitable option from menu\"},\"copyAllowed\":true}}}\u00C22\u00C23{\"suggestions\":[{\"reply\":{\"displayText\":\"User Manual\",\"postback\":{\"data\":\"Hi\"}}},{\"reply\":{\"displayText\":\"Troubleshoot Guide\",\"postback\":{\"data\":\"richcard\"}}}]}"
    in_dict = json.loads(resp)
    print(in_dict)
