# -*- coding:utf-8 -*-
from django.db import models


class BaseQuerySet(models.query.QuerySet):
    def delete(self):
        fields = (f.name for f in self.model._meta.fields)
        if 'is_deleted' in fields:
            return self.update(is_deleted=True)
        else:
            return super(BaseQuerySet, self).delete()


class ExcludeDeletedManager(models.manager.Manager.from_queryset(BaseQuerySet)):
    def get_queryset(self):
        queryset = super(ExcludeDeletedManager, self).get_queryset()
        fields = [f.name for f in self.model._meta.fields]
        if 'is_deleted' in fields:
            queryset = queryset.filter(is_deleted=False)
        return queryset


class WithDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    objects = ExcludeDeletedManager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class Audio(WithDeleteModel):
    title = models.CharField(max_length=32, blank=True, verbose_name='标题')
    author = models.CharField(max_length=32, blank=True, null=True, verbose_name='作者')
    performer = models.CharField(max_length=32, blank=True, null=True, verbose_name='表演者')
    file_url = models.URLField(max_length=600, null=True, blank=True, verbose_name='URL')
    size = models.FloatField(default=0, verbose_name='大小')
    duration = models.IntegerField(verbose_name='时长', default=0, blank=True, null=True, help_text='单位：秒')
    download_count = models.IntegerField(default=0, verbose_name='下载次数')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        abstract = True


class Image(WithDeleteModel):
    image = models.ImageField('图片')
    type = models.IntegerField('类型')
    sort = models.IntegerField('排序', default=0)
    file_url = models.URLField(max_length=512, null=True, blank=True, verbose_name='URL')
    size = models.FloatField(default=0, verbose_name='大小')
    description = models.CharField(max_length=1024, blank=True, verbose_name='描述')
    dt_created = models.DateTimeField(auto_now_add=True, verbose_name='创建于')
    dt_updated = models.DateTimeField(auto_now=True, verbose_name='更新于')

    class Meta:
        abstract = True


