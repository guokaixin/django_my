#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Create your models here.

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import is_password_usable
from common.utils.manages import ExcludeDeleteManager
from django.db import models
from rest_framework.authtoken.models import Token
from hashlib import sha1


class UserToken(Token):
    user = models.ForeignKey('people.CustomUser', related_name='auth_tokens', on_delete=models.CASCADE, verbose_name=_('user'))
    key = models.CharField(max_length=40, primary_key=True, verbose_name=_('token'))
    device_uuid = models.CharField(max_length=60, null=True, blank=True, verbose_name=_('device uuid'))
    # device_info = models.TextField(blank=True, verbose_name=_('device info'))

    class Meta:
        app_label = 'people'
        verbose_name = _('user token')
        verbose_name_plural = _('user tokens')


class UserType(models.Model):
    code = models.CharField(max_length=32, unique=True, verbose_name=_('user type code'))
    name = models.CharField(max_length=32, unique=True, verbose_name=_('user type name'))
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name=_('created datetime'))
    dt_updated = models.DateTimeField(auto_now=True, verbose_name=_('updated datetime'))

    class Meta:
        app_label = 'people'
        verbose_name = _('user type')
        verbose_name_plural = _('user types')
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name


class UserRole(models.Model):
    code = models.CharField(max_length=32, unique=True, verbose_name=_('user type code'))
    name = models.CharField(max_length=32, unique=True, verbose_name=_('user type name'))
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name=_('created datetime'))
    dt_updated = models.DateTimeField(auto_now=True, verbose_name=_('updated datetime'))

    class Meta:
        app_label = 'people'
        verbose_name = _('user role')
        verbose_name_plural = _('user roles')
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name


class UserAuthority(models.Model):
    code = models.CharField(max_length=32, unique=True, verbose_name=_('user authority code'))
    name = models.CharField(max_length=32, unique=True, verbose_name=_('user authority name'))
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name=_('created datetime'))
    dt_updated = models.DateTimeField(auto_now=True, verbose_name=_('updated datetime'))

    class Meta:
        app_label = 'people'
        verbose_name = _('user authority')
        verbose_name_plural = _('user authoritis')
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name


def user_update_avatar_to(instance, filename):
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


class CustomUser(AbstractUser):

    UNKNOWN = 0
    MALE = 1
    FEMALE = 2

    CHOICES = (
        (UNKNOWN, _('unknown')),
        (MALE, _('male')),
        (FEMALE, _('female')),
    )
    gender = models.PositiveSmallIntegerField(choices=CHOICES, default=UNKNOWN, db_index=True, verbose_name=_('gender'))
    constellation = models.CharField(max_length=10, blank=True, null=True, verbose_name=_('constellation'))
    introduction = models.TextField(blank=True, null=True, verbose_name=_('about self'))
    mobile = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('mobile'))
    nickname = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('nickname'))
    avatar = models.ImageField(upload_to=user_update_avatar_to, blank=True, null=True, verbose_name=_('avatar'))
    vip_start = models.DateField(null=True, blank=True, verbose_name=_('vip start'))
    vip_date = models.DateField(null=True, blank=True, verbose_name=_('vip date'))
    type = models.ForeignKey(UserType, verbose_name=_('user type'))
    role = models.ForeignKey(UserRole, verbose_name=_('user role'), blank=True, null=True)
    authority = models.ForeignKey(UserAuthority, null=True, blank=True, verbose_name=_('user authority'))
    vip_remind = models.BooleanField(default=False, verbose_name=_("vip data end remind"))
    remind_content = models.CharField(max_length=512, null=True, blank=True, verbose_name=_('remind content'))
    platform = models.CharField(max_length=32, blank=True, null=True, verbose_name=_("platform"))
    balance = models.PositiveIntegerField(_('virtual balance'), default=0, help_text=_('unit: mei'))
    devicetoken = models.CharField(max_length=128, null=True, blank=True, verbose_name=_('devicetoken'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('is deleted'))
    is_available = models.BooleanField(default=False, verbose_name=_('user is available'))
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name=_('created datetime'))
    dt_updated = models.DateTimeField(auto_now=True, verbose_name=_('updated datetime'))

    groups = None  # models.ManyToManyField(Group, related_name='custom_users', verbose_name=_('group'))

    user_permissions = None  # models.ManyToManyField(Permission, related_name='custom_users')

    objects = UserManager()
    no_deleted = ExcludeDeleteManager()

    class Meta:
        app_label = 'people'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        get_latest_by = 'id'

    def __unicode__(self):
        return self.username

    def delete(self):
        self.is_deleted = True
        self.save()

    def save(self, *args, **kwargs):
        # update password to be hashed
        if not self.password:
            self.password = make_password(settings.DEFAULT_PASSWORD)
        if self.password and not is_password_usable(self.password):
            self.password = make_password(self.password)
        return super(CustomUser, self).save(*args, **kwargs)


class Platform(models.Model):
    code = models.CharField(max_length=32, unique=True, verbose_name=_('code'))
    name = models.CharField(max_length=32, unique=True, verbose_name=_('name'))
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name=_('created datetime'))
    dt_updated = models.DateTimeField(auto_now=True, verbose_name=_('updated datetime'))

    class Meta:
        app_label = 'people'
        verbose_name = _('user platform')
        verbose_name_plural = _('user platforms')
        get_latest_by = 'id'

    def __unicode__(self):
        return self.code


class UserPlatformShip(models.Model):
    user = models.ForeignKey('people.CustomUser', related_name='platforms', verbose_name=_('user'))
    platform = models.ForeignKey('people.Platform', related_name='users', verbose_name=_('platform'))
    identifier = models.CharField(max_length=512, verbose_name=_('user platform identifier'))
    # device_uuid = models.CharField(max_length=60, blank=True, verbose_name=_('device uuid'))
    # device_info = models.TextField(blank=True, verbose_name=_('device info'))
    # payload = models.TextField(verbose_name=_('user platform payload'))
    # info = models.TextField(blank=True, verbose_name=_('user platform info'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('is deleted'))
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name=_('created datetime'))
    dt_updated = models.DateTimeField(auto_now=True, verbose_name=_('updated datetime'))

    class Meta:
        app_label = 'people'
        verbose_name = _('user platform ship')
        verbose_name_plural = _('user platform ship')
        get_latest_by = 'id'

    def __unicode__(self):
        return '%s - %s: %s)' % (self.platform.name, self.user.username, self.identifier)

    def delete(self):
        self.is_deleted = True
        self.save()
