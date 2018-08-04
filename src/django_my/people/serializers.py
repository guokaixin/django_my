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
from .models import Platform
from .models import UserPlatformShip

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


password_validators = [
        password_validation.MinimumLengthValidator().validate,
        password_validation.CommonPasswordValidator().validate,
        # password_validation.NumericPasswordValidator().validate,
        ]


class UserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj

    def has_permission(self, request, view):
        return request.method in ['POST', 'GET', 'PUT']


class CustomUserSerializer(serializers.ModelSerializer):
    # type = serializers.PrimaryKeyRelatedField(
    #         read_only=True,
    #         default=(UserType.objects.get_or_create(
    #             id=1,
    #             defaults={'code': 'default', 'name': 'default'},
    #             ))[0],
    #         )
    # comment while migrate tables
    default, is_create = UserRole.objects.get_or_create(code='DEFAULT', defaults={'name': 'DEFAULT'})
    indi_free, is_create = UserType.objects.get_or_create(code='INDI-FREE', defaults={'name': 'INDI-FREE'})
    audio_play, is_create = UserAuthority.objects.get_or_create(code='AUDIO-PLAY', defaults={'name': 'AUDIO-PLAY'})
    role = serializers.SlugRelatedField(slug_field='code', default=default, queryset=UserRole.objects.all())
    type = serializers.SlugRelatedField(slug_field='code', default=indi_free, queryset=UserType.objects.all())
    authority = serializers.SlugRelatedField(slug_field='code', default=audio_play, queryset=UserAuthority.objects.all())
    is_available = serializers.HiddenField(default=True)
    username = serializers.CharField(required=False)
    vip_date = serializers.DateField(required=False)
    email = serializers.EmailField(validators=[email_validator], required=False)
    mobile = serializers.RegexField('^1[3|4|5|7|8][0-9]\d{8}$', required=False)
    nickname = serializers.CharField(required=False)
    password = serializers.CharField(required=True, write_only=True, validators=password_validators)
    platforms = serializers.SerializerMethodField()
    token = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()


    class Meta:
        model = CustomUser
        read_only_fields = ('vip_date', 'type', 'authority')
        fields = ('id', 'username', 'email', 'mobile', 'nickname', 'avatar',
                  'vip_date', 'balance', 'role', 'type', 'authority', 'password',
                  'is_available', 'platforms', 'token', 'devicetoken', 'platform')

    def get_token(self, instance):
        try:
            return instance.auth_tokens.last().key
        except:
            return ''

    def get_platform(self, instance):
        return instance.platform

    def get_platforms(self, instance):
        data = instance.platforms.values_list('platform__code', flat=True)
        return list(data)

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).count():
            raise ValidationError('Username Already Exists.')
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).count():
            raise ValidationError('Email Already Exists.')
        return value


class CustomUserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False, write_only=True, validators=password_validators)

    class Meta:
        model = CustomUser
        fields = (
                'id',
                'nickname',
                'avatar',
                'password',
                'mobile',
                "devicetoken"
                )


class CommonCustomUserProfileSerializer(serializers.ModelSerializer):
    indi_free, is_create = UserType.objects.get_or_create(code='INDI-FREE', defaults={'name': 'INDI-FREE'})
    audio_play, is_create = UserAuthority.objects.get_or_create(code='AUDIO-PLAY', defaults={'name': 'AUDIO-PLAY'})
    type = serializers.SlugRelatedField(slug_field='code', default=indi_free, queryset=UserType.objects.all())

    class Meta:
        model = CustomUser
        fields = (
                'id',
                'nickname',
                'avatar',
                'type',
                )
        read_only_fields = ('nickname', 'avatar')


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform


class UserPlatformShipSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPlatformShip
