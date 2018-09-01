# -*- coding: utf-8 -*-
from django.contrib.auth import password_validation
from django.contrib.auth.models import User as Administrator


from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from libs.time_utils import datetime_to_localtime
from libs.utils import is_validate_username, is_validate_china_mobile

from common.utils.serializers import ModelSerializer
from .models import CustomUser
from .models import Business


class BusinessSerializer(ModelSerializer):
    code = serializers.CharField(max_length=32, required=True)
    name = serializers.CharField(max_length=32, required=False)

    class Meta:
        model = Business
        fields = ('code', 'name')

    def validate_code(self, code):
        if not Business.objects.filter(code=code).exists():
            raise ValidationError('业务类型不存在')
        return code


password_validators = [
        password_validation.MinimumLengthValidator(min_length=6).validate,
        password_validation.CommonPasswordValidator().validate,
        # password_validation.NumericPasswordValidator().validate,
        ]


class CustomUserSerializer(ModelSerializer):
    username = serializers.CharField(
        error_messages={'required': '姓名不能为空',
                        'max_length': '姓名长度不得多于10位'},
        required=True,
        max_length=50)
    mobile = serializers.CharField(
        error_messages={'required': '手机号不能为空',
                        'max_length': '手机号长度不得多于11位'},
        max_length=11,
        required=True)
    company = serializers.CharField(
        error_messages={'required': '公司名称不能为空',
                        'max_length': '公司名称长度不得多于30位'},
        required=False,
        max_length=50)
    password = serializers.CharField(required=False, validators=password_validators)
    token = serializers.SerializerMethodField()
    is_available = serializers.HiddenField(default=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'mobile', 'company', 'password', 'is_available', 'token')

    def get_token(self, instance):
        try:
            return instance.user_token.key
        except:
            return ''

    def validate_username(self, username):
        if not is_validate_username(username):
            raise ValidationError('姓名不合法')
        return username

    def validate_mobile(self, mobile):
        if not is_validate_china_mobile(mobile):
            raise ValidationError('手机号码不合法')
        elif CustomUser.objects.filter(mobile=mobile).exists():
            raise ValidationError('手机号码已占用')
        return mobile


class CustomUserProfileSerializer(ModelSerializer):
    businesses = serializers.SerializerMethodField()
    register_time = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'mobile', 'company', 'businesses', 'register_time')

    def get_businesses(self, instance):
        return instance.businesses.values_list('business__name', flat=True).distinct()

    def get_register_time(self, instance):
        return datetime_to_localtime(instance.dt_created)


class CommonCustomUserProfileSerializer(ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'mobile', 'company')
        read_only_fields = ('username', 'mobile', 'company')


class AdministratorProfileSerializer(ModelSerializer):

    class Meta:
        model = Administrator
        fields = ('id', 'username')


#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group
from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from .models import UserAuthority
from .models import UserRole
from .models import UserType
from .models import UserToken
from .models import CustomUser

from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated


class UserSerializers(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializers(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class UserTokenSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserToken
        fields = ('user', 'token')

    def get_token(self, obj):
        return obj.key

    def get_user(self, obj):
        return CustomUserSerializer(obj.user).data


class UserAuthoritySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuthority


class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType


def email_validator(value):
    if CustomUser.objects.filter(Q(username=value)|Q(email=value)).exists():
        raise ValidationError('User Aleady Exists.')


class UserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj

    def has_permission(self, request, view):
        return request.method in ['POST', 'GET', 'PUT']
