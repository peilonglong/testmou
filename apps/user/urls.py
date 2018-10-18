from django.urls import path,include
from apps.user.views import *

app_name='user'
urlpatterns=[
    path('register/',RegisterView.as_view(),name='register'),  #注册
    path('active<token>/)', ActiveView.as_view(), name='active'),  # 激活
    path('Login/', LoginView.as_view(), name='Login')  # 登录

]