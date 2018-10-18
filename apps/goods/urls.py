from django.urls import path,include
from apps.goods.views import *

app_name='goods'
urlpatterns=[
    path('',index,name='index')
]