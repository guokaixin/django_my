# -*- coding: utf-8 -*-
from django.db import models
from django import forms
from django.contrib import admin
from .utils.admin import BaseModelAdmin

from .models import Config
from .models import ServiceTerm
from .models import Banner
from .models import VersionCategory


@admin.register(Config)
class ConfigModelAdmin(BaseModelAdmin):
    list_display = ('key', 'value', 'dt_created')


@admin.register(ServiceTerm)
class ServiceTermModelAdmin(BaseModelAdmin):
    list_display = ('title', 'dt_created')
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 10, 'cols': 200, 'style': 'height: 100em;'})},
    }


@admin.register(VersionCategory)
class VersionCategoryModelAdmin(BaseModelAdmin):
    list_display = ('name', 'code', 'can_preview_page', 'can_customize_city', 'can_customize_logo',
                    'valid_days', 'price', 'dt_updated', 'dt_created')
    readonly_fields = ('name', 'code', 'can_preview_page', 'can_customize_city', 'can_customize_logo',
                       'valid_days')

    def has_add_permission(self, request):
        pass

    def has_delete_permission(self, request, obj=None):
        pass

    def get_actions(self, request):
        return []


@admin.register(Banner)
class BannerModelAdmin(BaseModelAdmin):
    list_display = ('title', 'code', 'image_admin', 'location_type', 'redirect_type',
                    'detail_id', 'valid', 'sort', 'dt_updated', 'dt_created')
    list_filter = ('location_type', 'redirect_type', 'valid')
    search_fields = ('title', )


