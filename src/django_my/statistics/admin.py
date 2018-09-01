from django.contrib import admin
from common.utils.admin import BaseModelAdmin
from jet.admin import CompactInline
from .models import Statistics
from .models import DownloadStatistics
from .models import VisitIP


@admin.register(Statistics)
class StatisticsModelAdmin(BaseModelAdmin):
    list_display = ('item', 'viewed_count', 'download_count', 'year', 'month', 'day')
    readonly_fields = ('item', 'year', 'month', 'day', 'viewed_count', 'download_count')
    date_hierarchy = 'dt_created'

    def has_add_permission(self, request):
        pass

    def has_delete_permission(self, request, obj=None):
        pass


class VisitIPInline(CompactInline):
    model = VisitIP
    fields = ('ip', 'user_agent', 'date')
    readonly_fields = ('ip', 'user_agent', 'date')
    extra = 0


@admin.register(DownloadStatistics)
class DownloadStatisticsModelAdmin(BaseModelAdmin):
    list_display = ('user', 'click_count', 'visitor_count', 'date')
    date_hierarchy = 'date'
    readonly_fields = ('user', 'click_count', 'visitor_count', 'date')
    inlines = [VisitIPInline, ]

