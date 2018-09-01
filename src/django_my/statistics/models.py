# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from people.models import CustomUser


class Statistics(models.Model):

    item = models.ForeignKey('order.PurchaseItem', verbose_name=u'购买项目')
    year = models.PositiveSmallIntegerField(u'年', default=0)
    month = models.PositiveSmallIntegerField(u'月', default=0)
    day = models.PositiveSmallIntegerField(u'日', default=0)
    viewed_count = models.PositiveIntegerField(u'浏览量', default=0)
    download_count = models.PositiveIntegerField(u'下载量', default=0)
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        verbose_name = 'H5访问统计'
        verbose_name_plural = verbose_name


class DownloadStatistics(models.Model):
    """
    下载统计
    """
    user = models.ForeignKey(CustomUser, verbose_name='用户')
    click_count = models.PositiveIntegerField(default=0, verbose_name='点击量')
    visitor_count = models.PositiveIntegerField(default=0, verbose_name='访客量')
    date = models.DateField('日期')

    class Meta:
        verbose_name = 'APP访问统计'
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.user.username


class VisitIP(models.Model):
    """
    访问ip
    """
    download_data = models.ForeignKey(DownloadStatistics, verbose_name='下载统计', null=True, blank=True)
    ip = models.GenericIPAddressField('访问IP')
    user_agent = models.CharField('访问Agent', null=True, blank=True, max_length=500)
    date = models.DateField('日期')

    class Meta:
        verbose_name = '访问IP'
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.ip
