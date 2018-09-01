# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import hashlib
import sys
from django.conf import settings
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from rest_framework.authtoken.models import Token
from hashlib import sha1

from common.utils.models import WithDeleteModel
reload(sys)
sys.setdefaultencoding("utf-8")


def is_customuser(user):
    return type(user) == CustomUser and (not user.is_superuser)


def is_administrator(user):
    return type(user) == CustomUser and user.is_superuser


class UserToken(Token):
    user = models.OneToOneField('people.CustomUser', related_name='user_token', verbose_name='用户')
    key = models.CharField(max_length=40, primary_key=True, verbose_name='Token')

    class Meta:
        verbose_name = '用户Token'
        verbose_name_plural = '用户Token'


class UserAuthority(models.Model):
    code = models.CharField(max_length=32, unique=True, verbose_name='编码')
    name = models.CharField(max_length=32, unique=True, verbose_name='名称')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '用户权限'
        verbose_name_plural = '用户权限'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name


class UserType(models.Model):
    code = models.CharField(max_length=32, unique=True, verbose_name='编码')
    name = models.CharField(max_length=32, unique=True, verbose_name='名称')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '用户类型'
        verbose_name_plural = '用户类型'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name


class UserRole(models.Model):
    code = models.CharField(max_length=32, unique=True, verbose_name='编码')
    name = models.CharField(max_length=32, unique=True, verbose_name='名称')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name


class Business(models.Model):
    """
    业务类型
    """
    code = models.CharField(max_length=32, unique=True, verbose_name='编码')
    name = models.CharField(max_length=32, unique=True, verbose_name='名称')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '业务类型'
        verbose_name_plural = '业务类型'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name


def user_avatar_upload_to(instance, filename):
    content = instance.avatar.file.read()
    sha1_hash = sha1(content).hexdigest()
    suffix = filename.split('.')[-1]
    args = [
            settings.UPLOAD_ROOT,
            'people',
            'avatar',
            '%s.%s' % (sha1_hash, suffix)
            ]
    return '/'.join(args)


class AvailableUserManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        qs = super(AvailableUserManager, self).get_queryset(*args, **kwargs)
        return qs.filter(is_available=True, is_superuser=False).exclude(mobile=settings.DEFAULT_USER_MOBILE)

    def create_user(self, mobile, username, company, password, business_codes=None):
        user, created = self.get_or_create(mobile=mobile, defaults={'username': username,
                                                                    'company': company,
                                                                    'password': make_password(password),
                                                                    'is_available': True})
        for business_code in business_codes:
            UserBusiness.objects.get_or_create(user=user, business__code=business_code)
        return user


class CustomUser(AbstractUser):
    code = models.CharField(max_length=40, verbose_name='编码', blank=True)
    mobile = models.CharField(max_length=32, verbose_name='手机号码', blank=True, null=True)
    username = models.CharField(max_length=100, verbose_name='用户名', blank=True, null=True)
    nickname = models.CharField(max_length=100, verbose_name='昵称', blank=True, null=True)
    password = models.CharField(u'登录密码', max_length=128,
                                help_text=u'''请使用 '[algo]$[salt]$[hexdigest]' 这样的密码格式，或者 <a href="password/">点击此处</a> 修改该用户登录密码。''')
    company = models.CharField(max_length=50, verbose_name='公司', blank=True, null=True)
    avatar = models.ImageField(upload_to=user_avatar_upload_to, null=True, blank=True, verbose_name='用户头像')

    type = models.ForeignKey(UserType, verbose_name='用户类型', blank=True, null=True)
    role = models.ForeignKey(UserRole, verbose_name='用户角色', blank=True, null=True)
    authority = models.ForeignKey(UserAuthority, null=True, blank=True, verbose_name='用户权限')

    is_available = models.BooleanField(default=False, verbose_name='是否可用')
    is_superuser = models.BooleanField(default=False, verbose_name='是否管理员')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    groups = None  # models.ManyToManyField(Group, related_name='custom_users', verbose_name=_('group'))

    user_permissions = None  # models.ManyToManyField(Permission, related_name='custom_users')

    objects = UserManager()
    available_objects = AvailableUserManager()

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.username

    def generate_code(self):
        m5 = hashlib.md5()
        m5.update("%s-%s-%s-%s" % (
            self.username.encode('utf-8'),
            self.mobile,
            self.company.encode('utf-8'),
            self.dt_created.strftime('%Y-%m-%d %H:%M:%S')))
        return m5.hexdigest().upper()

    def save(self, *args, **kwargs):
        if not self.password:
            self.password = make_password(settings.DEFAULT_PASSWORD)
        if self.password and not is_password_usable(self.password):
            self.password = make_password(self.password)
        return super(CustomUser, self).save(*args, **kwargs)


def custom_user_post_save(sender, instance, created, **kwargs):
    if not instance.code:
        instance.code = instance.generate_code()
        instance.save()
    UserToken.objects.get_or_create(user=instance)


post_save.connect(custom_user_post_save, sender=CustomUser)


class AdministratorManager(models.manager.Manager):
    def get_queryset(self):
        queryset = super(AdministratorManager, self).get_queryset()
        queryset = queryset.filter(is_superuser=True)
        return queryset


class Administrator(CustomUser):
    objects = AdministratorManager()

    class Meta:
        verbose_name = '管理员'
        verbose_name_plural = verbose_name
        proxy = True


class UserBusiness(models.Model):
    user = models.ForeignKey(CustomUser, verbose_name='用户', related_name='businesses')
    business = models.ForeignKey(Business, verbose_name='业务类型')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '用户业务类型'
        verbose_name_plural = '用户业务类型'
        get_latest_by = 'id'

    def __unicode__(self):
        return u'%s: %s' % (self.user, self.business)

