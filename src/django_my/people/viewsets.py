#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import random
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.decorators import api_view, detail_route
from rest_framework.decorators import throttle_classes as throttle_decorator
from rest_framework.throttling import AnonRateThrottle
from django.utils.translation import ugettext_lazy
from django.db.models import Q
from common.tasks import send_mail
from .models import UserAuthority
from .models import UserType
from .models import UserRole
from .models import UserToken
from .models import CustomUser

from .serializers import CustomUserSerializer
from .serializers import CommonCustomUserProfileSerializer
from .serializers import CustomUserProfileSerializer
from .serializers import UserPermission

logger = logging.getLogger('django.people')


class CustomUserViewSet(viewsets.ModelViewSet):
    model = CustomUser
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (UserPermission,)

    def get_queryset(self):
        queryset = self.model.objects.filter(is_available=True)
        return queryset

    def list(self, request, *args, **kwargs):
        raise PermissionDenied

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance:
            serializer = CustomUserSerializer(instance)
        else:
            serializer = CommonCustomUserProfileSerializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data
        device_uuid = data.get('device_uuid')
        if hasattr(data, '_mutable'):
            data._mutable = True
        if not data.get('username'):
            data['username'] = data.get('email')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        token, created = UserToken.objects.get_or_create(
            user=serializer.instance,
            device_uuid=device_uuid,
        )
        data = CustomUserSerializer(token.user).data
        data['token'] = token.key
        data['type_name'] = serializer.instance.type.name
        headers = self.get_success_headers(serializer.data)
        status = 201
        return Response(data, status=status, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance:
            raise PermissionDenied
        serializer = CustomUserProfileSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


@api_view(['POST'])
def user_signin(request):
    username = request.data.get('username')
    password = request.data.get('password')
    device_uuid = request.data.get('device_uuid')
    platform = request.META.get("HTTP_USER_AGENT")
    if 'iOS' in platform:
        platform = 'ios'
    else:
        platform = 'android'
    if not (username and password):
        raise AuthenticationFailed
    else:
        try:
            user = CustomUser.objects.get(username=username, is_available=True)
            if user.check_password(password):
                token, created = UserToken.objects.get_or_create(
                        user=user,
                        device_uuid=device_uuid,
                        )
                data = CustomUserSerializer(token.user).data
                data['token'] = token.key
                data['platform'] = platform
                user.platform = platform
                user.save()
                data["type_name"] = token.user.type.name
                status = 201 if created else 200
                return Response(data, status=status)
            else:
                raise AuthenticationFailed
        except CustomUser.DoesNotExist as error:
            raise AuthenticationFailed


@api_view(['POST'])
def user_email_signin(request):
    email = request.data.get('email')
    password = request.data.get('password')
    platform = request.META.get("HTTP_USER_AGENT")
    if 'iOS' in platform:
        platform = 'ios'
    else:
        platform = 'android'
    if not (email and password):
        raise AuthenticationFailed
    else:
        try:
            user = CustomUser.objects.get(email=email, is_available=True)
            if user.check_password(password):
                token, created = UserToken.objects.get_or_create(user=user)
                data = CustomUserSerializer(token.user).data
                data['token'] = token.key
                data['platform'] = platform
                user.platform = platform
                user.save()
                data["type_name"] = token.user.type.name
                status = 201 if created else 200
                return Response(data, status=status)
            else:
                raise AuthenticationFailed
        except:
            raise AuthenticationFailed


class ResetPasswordThrottle(AnonRateThrottle):
    scope = 'resetpassword'
    rate = '5/m'


@api_view(['POST'])
@throttle_decorator([ResetPasswordThrottle])
def user_reset_password_email(request):
    username = request.data.get('username')
    if not username:
        return Response({'username': 'without username'}, status=400)
    try:
        user = CustomUser.objects.get(
                Q(username=username)|Q(email=username)|Q(mobile=username),
                email__isnull=False,
                )
        if user.email:
            password = ''.join(random.sample(
                '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@# $%^&*()_+=-><:}{?/',
                8))
            user.set_password(password)
            subject = ugettext_lazy('password reset')
            content = ugettext_lazy('reset the password to: %s') % password
            try:
                send_mail.apply((subject, content, user.email))
                logger.info('reset password for %s' % user.email)
                user.save()
                return Response(None, status=200)
            except Exception as error:
                logger.error(error)
                return Response(None, status=500)
    except CustomUser.DoesNotExist as error:
        return Response({'username': 'invalid username'}, status=400)
    except Exception as error:
        logger.error(error)
        return Response(None, status=500)


@api_view(['GET', 'POST'])
def reset_password(request, pk):
    data = 'reset the password'
    return Response(data)