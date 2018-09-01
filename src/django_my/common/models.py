# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import requests
from hashlib import sha1
from django.db import models
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework import status
# from .utils.models import WithDeleteModel
# from .signals import signal_update_banners
# from .signals import signal_update_versions


class Config(models.Model):
    """ 系统配置 """
    key = models.CharField(max_length=32, unique=True, verbose_name='键')
    value = models.TextField(blank=True, verbose_name='值')
    operator = models.ForeignKey('auth.user', null=True, verbose_name='操作人')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        get_latest_by = 'id'

    def __unicode__(self):
        return '%s: %s, operated by %s' % (self.key, self.value, self.operator.username if self.operator else 'System')


def image_upload_to(instance, filename):
    content = instance.image.file.read()
    hash_str = sha1(content).hexdigest()
    suffix = filename.split('.')[-1]
    args = [
        settings.UPLOAD_ROOT,
        'data',
        '%s.%s' % (hash_str, suffix)
    ]
    return '/'.join(args)


class Banner(models.Model):
    """ 首页Banner管理 """
    TOP = 1
    MIDDLE = 2
    FOOTER = 3
    LOCATION_CHOICES = (
        (TOP, '头部'),
        (MIDDLE, '中部'),
        (FOOTER, '底部')
    )

    WEB_PAGE = 1
    ACTIVITY_DETAIL = 2
    REDIRECT_CHOICES = (
        (WEB_PAGE, 'WEB页面'),
        (ACTIVITY_DETAIL, '活动详情'),
    )

    title = models.CharField(max_length=128, verbose_name='标题')
    code = models.CharField(max_length=32, unique=True, verbose_name='编码')
    location_type = models.PositiveSmallIntegerField('显示位置', choices=LOCATION_CHOICES, default=TOP)
    image = models.ImageField(upload_to=image_upload_to, verbose_name='图片')

    redirect_type = models.PositiveSmallIntegerField('跳转类型', choices=REDIRECT_CHOICES, blank=True, null=True)
    detail_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='详情ID或URL')

    valid = models.BooleanField(default=0, verbose_name='是否有效')
    sort = models.IntegerField(default=0, verbose_name='排序')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banner'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.code


class ServiceTerm(models.Model):
    """ 服务条款 """
    title = models.CharField('标题', max_length=30)
    content = models.TextField('条款内容')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '服务条款'
        verbose_name_plural = '服务条款'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.title


class VersionCategory(models.Model):
    """ 版本类型 """
    name = models.CharField(max_length=20, verbose_name='版本名称')
    code = models.CharField(max_length=20, verbose_name='版本编码', unique=True)
    can_preview_page = models.BooleanField('是否支持试听页面', default=True)
    can_customize_city = models.BooleanField('是否支持自定义城市', default=False)
    can_customize_logo = models.BooleanField('是否支持自定义Logo', default=False)
    valid_days = models.PositiveIntegerField(default=0, verbose_name='有效天数')
    price = models.FloatField(default=0, verbose_name='价格（元/次）')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = '版本类型'
        verbose_name_plural = '版本类型'
        get_latest_by = 'id'

    def __unicode__(self):
        return self.name

    def check_city(self, city_id):
        if self.code == 'free':
            resp = requests.get('{}/rest/location/freecity/?city_id={}'.format(settings.MJTT_BASE_URL, city_id))
            results = resp.json()['results']
            if not results:
                raise ValidationError('城市不存在')
            data = results[0]
            return city_id, data['city']['name'], data['country']['id'], data['country']['name']
        else:
            resp = requests.get('{}/rest/location/city/{}'.format(settings.MJTT_BASE_URL, city_id))
            if resp.status_code != status.HTTP_200_OK:
                raise ValidationError('城市不存在')
            data = resp.json()
            return city_id, data['name'], data['country'], data['country_name']
