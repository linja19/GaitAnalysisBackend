from django.urls import path, include
from . import views

urlpatterns = [
    path('get-data', views.get_data, name='get-data'),
    path('get-param/<str:userID>', views.get_param, name='get-param'),
    path('upload-data/<str:userID>',views.upload_data, name='upload-data'),
    path('upload-template/<str:userID>',views.create_template, name='create-template'),
]