#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils.translation import gettext_lazy as _
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from .models import CustomUser
from common.utils.image_tag import _image_tag
from urllib import unquote

# Register your models here.


class CustomUserModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'nickname', 'avatar_image',
                    'mobile', 'vip_start', 'vip_date', 'vip_remind', 'type__name', 'authority', 'role',
                    'balance', 'is_available', 'devicetoken', 'dt_created', 'dt_updated')
    fields = ('username', 'nickname', 'avatar', 'mobile', 'email', 'gender', 'constellation',
              'introduction', 'balance', 'vip_start', 'vip_date', 'vip_remind', 'remind_content', "platform",
              'type', 'authority', 'role', 'devicetoken', 'is_available')
    # readonly_fields = ('username',)
    search_fields = ('id', 'username', 'nickname', 'mobile')
    list_filter = ('is_available', 'role', 'type', 'authority')

    def type__name(self, obj):
        return obj.type.name

    type__name.short_description = _('user type')

    def avatar_image(self, obj):
        url = obj.avatar.url if obj.avatar else ''
        print url
        url = unquote(url)
        print url
        img = '<img src="%s" height=25 width=25 />' % url
        print img
        return img
    avatar_image.allow_tags = True
    avatar_image.short_description = _('avatar')

    # def avatar_image(self, obj):
    #     if getattr(obj, 'images'):
    #         html = _image_tag.format(image_url=obj.avatar.url, height='20px')
    #     else:
    #         html = ''
    #     return html
    # avatar_image.allow_tags = True
    # avatar_image.short_description = _('avatar')


admin.site.register(CustomUser, CustomUserModelAdmin)