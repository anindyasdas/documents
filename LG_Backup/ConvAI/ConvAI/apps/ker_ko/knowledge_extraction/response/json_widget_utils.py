"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""


class WidgetCards(object):
    """
        jsons used for to create RCS chatbot response
    """
    # json used for specification section response
    spec_template = """{
                "action": {
                  "settingsAction": {
                    "disableAnonymization": {}
                  },
                  "displayText": "",
                  "postback": {
                    "data": ""
                  }
                }
              }"""

    # json used for troubleshooting section response
    trob_template = """{
              "title": "",
              "description": "",
              "suggestions": [
                {
                  "action": {
                    "settingsAction": {
                      "disableAnonymization": {}
                    },
                    "displayText": "해결책은 여기 있습니다",
                    "postback": {
                      "data": ""
                    }
                  }
                }
              ]        
            }"""

    # json used to form reply card
    carousel_template = """{
             "reply":{
                "displayText":"",
                "postback":{
                   "data":""
                }
             }
             }"""

    # json used for operation section response
    para_template = """{
                    "title": "",
                    "description": ""
                }"""
