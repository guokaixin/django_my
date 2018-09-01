# -*- coding:utf-8 -*-
from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe
from .image_tag import image_tag


from django.contrib.admin import SimpleListFilter
from django.db import connection


class AdminImageWidget(admin.widgets.AdminFileWidget):
    """
    A ImageField Widget for admin that shows a thumbnail.
    """

    def __init__(self, attrs={}):
        super(AdminImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append(('<a target="_blank" href="%s">'
                           '<img src="%s" style="height: 50px; width: 100px" /></a> '
                           % (value.url, value.url)))
        output.append(super(AdminImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


def base_inline_admin_get_queryset(self, request):
    qs = super(admin.options.InlineModelAdmin, self).get_queryset(request)
    fields = [field.name for field in qs.model._meta.fields]
    if 'is_deleted' in fields:
        qs = qs.filter(is_deleted=False)
    return qs


class BaseModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
            models.ImageField: {'widget': AdminImageWidget},
        }
    list_per_page = 30

    def get_queryset(self, request):
        qs = super(admin.ModelAdmin, self).get_queryset(request)
        fields = [field.name for field in qs.model._meta.fields]
        if 'is_deleted' in fields:
            qs = qs.filter(is_deleted=False)
        return qs

    actions = ['bulk_delete_selected',
               'bulk_publish_selected',
               'bulk_unpublish_selected',
               ]

    def get_actions(self, request):
        actions = super(BaseModelAdmin, self).get_actions(request)
        field_names = [f.name for f in self.model._meta.fields]
        if actions:
            if 'is_deleted' not in field_names:
                del actions['bulk_delete_selected']
            else:
                del actions['delete_selected']
            if 'is_published' not in field_names:
                del actions['bulk_publish_selected']
                del actions['bulk_unpublish_selected']
        return actions
    
    def bulk_op_selected(field_name, value, short_description):
        def wrap(func):
            def op(self, request, queryset):
                if field_name in (f.name for f in queryset.model._meta.fields):
                    queryset.update(**{field_name: value})
                self.message_user(request, '成功')
            op.short_description = short_description
            return op
        return wrap

    @bulk_op_selected('is_deleted', True, '批量删除')
    def bulk_delete_selected(self, request, queryset):
        pass

    @bulk_op_selected('is_published', True, '批量发布')
    def bulk_publish_selected(self, request, queryset):
        pass

    @bulk_op_selected('is_published', False, '批量取消发布')
    def bulk_unpublish_selected(self, request, queryset):
        pass

    def image_admin(self, obj):
        if getattr(obj, 'image'):
            html = image_tag.format(image_url=obj.image.url, height='20px')
        else:
            html = ''
        return html
    image_admin.allow_tags = True
    image_admin.short_description = '图片'


class YearListFilter(SimpleListFilter):
    title = '年'
    parameter_name = 'dt_created__year'

    def lookups(self, request, model_admin):
        select = {'year': connection.ops.date_trunc_sql('year', 'dt_created')}
        qs = model_admin.get_queryset(request).extra(select=select).values('year').distinct()
        for item in qs:
            year = str(item['year']).split('-')[0]
            yield (year, year)

    def queryset(self, request, queryset):
        return queryset.filter(**self.used_parameters)


class MonthListFilter(SimpleListFilter):
    title = '月'
    parameter_name = 'dt_created__month'

    def lookups(self, request, model_admin):
        select = {'month': connection.ops.date_trunc_sql('month', 'dt_created')}
        qs = model_admin.get_queryset(request).extra(select=select).values('month').distinct()
        for item in qs:
            month = str(item['month']).split('-')[1]
            yield (month, month)

    def queryset(self, request, queryset):
        return queryset.filter(**self.used_parameters)


