"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: senthil.sk@lge.com
"""
from rest_framework import serializers

class InputRequestSerializer(serializers.Serializer):
    """
    class is used to validate the input request details for datatype,Empty or Missing content in request
    """
    request_id = serializers.IntegerField(required=True)
    question = serializers.CharField()
    model_no = serializers.CharField()
    ker_context = serializers.DictField()