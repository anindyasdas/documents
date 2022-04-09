from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from rest_api.views import SpecTrobView, PrefView, HybridApproachView, FileBasedTesting

app_name = 'rest_api'
urlpatterns = 'rest_api'

urlpatterns = [
        path('rest_api/', views.IndexView.as_view(), name='index'),
        path('ker/', SpecTrobView.as_view({'get': 'getkerui'})),
        path('ker_req/', SpecTrobView.as_view({'post': 'post_for_ker'})),
        path('kms_ker/', SpecTrobView.as_view({'post': 'post_for_kms_ker'})),
        path('get_pref/', PrefView.as_view({'post': 'getpref'})),
        path('reset_pref/', PrefView.as_view({'post': 'resetpref'})),
        path('prod_details/', HybridApproachView.as_view({'post': 'process_user_query'})),
        path('user_query/', HybridApproachView.as_view({'post': 'process_user_query'})),
        path('common_problems/', HybridApproachView.as_view({'post': 'get_common_problems'})),
        path('file_based/', FileBasedTesting.as_view()),
        ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,\
                          document_root=settings.MEDIA_ROOT)
