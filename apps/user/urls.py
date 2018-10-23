from django.urls import path,include
from apps.user.views import *

app_name='user'
urlpatterns=[
    path('register/',RegisterView.as_view(),name='register'),  #注册
    path('active<token>/)', ActiveView.as_view(), name='active'),  # 激活
    path('login/', LoginView.as_view(), name='Login') ,# 登录
    path('logout/',LogoutView.as_view(),name='logout'),#退出

    path('user/',UserInfoView.as_view(),name='user'), #用户中心
    path('order/',UserOrderView.as_view(),name='order'), #用户中心订单页
    path('address/',AddressView.as_view(),name='address'),#用户中心地址页面

]