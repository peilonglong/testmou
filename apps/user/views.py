import re
from django.contrib.auth import authenticate, login  ,logout#登录判断
from django.core.mail import send_mail
from django.core.serializers.base import Serializer
from itsdangerous import SignatureExpired   #过期异常
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from apps.user.models import User,Address
from django.conf import settings
from apps.goods.views import *
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from celery_tasks.tasks import send_register_active_email

class RegisterView(View):
    '''注册'''
    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''进行注册处理'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html',{'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理: 进行用户注册
        user = User.objects.create_user(username,email,password)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接: http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息, 并且要把身份信息进行加密

        # 加密用户的身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info) # bytes
        token = token.decode()

        # 发邮件
        # send_register_active_email.delay(email, username, token)
        # subject = '天天生鲜欢迎信息'
        # message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>'
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
        #     username, token, token)

        # send_mail (subject, message, sender, receiver)

        send_register_active_email.delay(email, username, token)

        # 返回应答, 跳转到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')

# /user/login
class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整'})

        # 登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request, user)
                # 获取登录后所要跳转到的地址
                #默认挑转到首页
                next_url=request.GET.get('next',reverse('goods:index'))
                response=redirect(next_url) #HttpResponseRedirect

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 返回response
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg':'账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html',{'errmsg':'用户名或密码错误'})

class LogoutView(View):
    #退出登录
    def get(self,request):
        logout(request)
        #重定向到首页
        return redirect(reverse('goods:index'))



class UserInfoView(View):
    '''用户中心'''
    def get(self,request):
        '''显示'''
        # Django会给request对象添加一个属性request.user
        # 如果用户未登录->user是AnonymousUser类的一个实例对象
        # 如果用户登录->user是User类的一个实例对象
        # request.user.is_authenticated()
        #page='user
        return render(request,'user_center_info.html',{'page':'user'})

class UserOrderView(View):
    '''用户订单'''
    #page=order
    def get(self,request):
        return render(request,'user_center_order.html',{'page':'order'})

class AddressView(View):
    '''用户中心地址页'''
    #page=address
    def get(self,request):
        return render(request,'user_center_site.html',{'page':'address'})

    def post(self,request):
        #接受数据
        receiver=request.POST.get('receiver')
        addr=request.POST.get('addr')
        zip_code = request.POST.get ('zip_code')
        phone = request.POST.get ('phone')

        #校验数据
        if not all([receiver,addr,zip_code,phone]):
            return render(request,'user_center_site.html',{'errmsg':'数据结构不完整'})
        #校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$',phone):
        #业务处理：地址添加
            return render(request,'user_center_site.html ,{'errmsg':'手机号码不完整'})
        user=request.user
        address=Address.objects.get(user=user,is_default=True)



