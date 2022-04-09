from django.shortcuts import render
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views.generic.base import View
from rest_framework import viewsets
import json
from engines.Engine import Engine
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import importlib
import os

from rest_api.version import version
from rest_framework import status
from rest_framework.views import APIView
from .serializers import RetrievePostSerializer, ConstructPostSerializer
from kms_error import KMSError

kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

engine = Engine()

class IndexView(APIView):
    """
    A class to process restful api
    """
    def get(self, request):
        """
        Process GET request
        :param str(json) request
        :returns: 200_OK, version
        :rtype: HttpResponse
        """
        return JsonResponse({'type': 'KMS', 'version': version}, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Process POST request
        :param str(json) request
        :returns: Response for POST request
        :rtype: JsonResponse
        """
        logger.debug("POST Retriever request")

        # To handle the invalid json format added try..catch
        try:
            retrieval_serializer = RetrievePostSerializer(data=request.data)
            construct_serializer = ConstructPostSerializer(data=request.data)

            if retrieval_serializer.is_valid() and retrieval_serializer.data['process'] == 'retrieval':
                logger.debug("Retrieval serializer is valid")
                try:
                    answer = engine.retrieve(request.data)
                except Exception as e:
                    e = KMSError(20)
                    return JsonResponse(self.make_error_body(e.code, e.emsg), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif construct_serializer.is_valid() and retrieval_serializer.data['process'] == 'global_construction':
                logger.debug("Construct serializer is valid")
                try:
                    answer = engine.construct(request.data)
                except:
                    e = KMSError(20)
                    return JsonResponse(self.make_error_body(e.code, e.emsg), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            else:
                logger.debug("error in serializer")
                logger.error(retrieval_serializer.errors)
                e = KMSError(10)
                return JsonResponse(self.make_error_body(e.code, e.emsg, retrieval_serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.debug("Exception in json parsing")
            logger.error(str(e))
            e = KMSError(10)
            return JsonResponse(self.make_error_body(e.code, e.emsg), status=status.HTTP_400_BAD_REQUEST)

        logger.debug("End of post")
        return JsonResponse(answer)

    def put(self, request):
        """
        Process PUT request
        :param str(json) request
        :returns: Response for GET request
        :rtype: HttpResponse
        """
        return HttpResponse("Received Put request")

    def delete(self, request):
        """
        Process DELETE request
        :param str(json) request
        :returns: Response for GET request
        :rtype: HttpResponse
        """
        return HttpResponse("Received Delete request")

    def make_error_body(self, code, result, response={}):
        return {
            'status': {
                'code': str(code),
                'message': result
            },
            'response': response
        }

# Create your views here.
class SpecTrobView(viewsets.ViewSet):
    """
        class used to inflate the repective template
    """
    template_name = engine.get_template_name()

    def getkerui(self, request):
        return render(request, self.template_name)

    def post_for_ker(self, request):
        logger.debug("post : %s", request.body)
        response = engine.process_request(request)
        return response

    def post_for_kms_ker(self, request):
        logger.debug("post : %s", request.body)
        response = engine.process_kms_ker_request(request)
        return response


class FileBasedTesting(TemplateView):
    def get(self, request):
        return render(request, "file_based_testing.html")

    def post(self, request):
        engine.process_uploaded_file(request.FILES["file_upload"].name)
        context = {"FILE_NAME": request.FILES["file_upload"].name}
        return render(request, "file_based_testing_download.html", context)

    def save_file(self, request):
        save_path = os.path.join(settings.MEDIA_ROOT, request.FILES["file_upload"].name)
        with open(save_path, "wb") as output_file:
            for chunk in request.FILES["file_upload"].chunks():
                output_file.write(chunk)
        return save_path

class PrefView(viewsets.ViewSet):
    """
        handle the request related to the preferences
    """
    def getpref(self, request):
        response = engine.process_pref_request()
        return response

    def resetpref(self, request):
        response = engine.reset_pref_request()
        return response


class HybridApproachView(viewsets.ViewSet):

    def process_user_query(self, request):
        request_json = request.data
        logger.debug("process_user_query request data : %s",request_json)
        response = engine.process_user_query(request_json)
        return response

    def get_common_problems(self, request):
        request_json = request.data
        logger.debug("process_user_query request data : %s",request_json)
        response = engine.get_common_problems(request_json)
        return response
