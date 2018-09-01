# -*- coding: utf-8 -*-
"""django_my URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from people import views

admin.site.site_url = None
admin.site.site_header = 'JIA瑞美妆"订单管理后台'
admin.site.index_title = 'JIA瑞美妆"订单管理后台'

router = routers.DefaultRouter()
router.register(r'users', views.UserViewets)
router.register(r'groups', views.GroupViewets)

api_patterns = [
    url(r'', include('people.urls')),

]

urlpatterns = [
    url(r'^admin/jet', include('jet.urls', 'jet')),
    url(r'^admin/jet/dashboard', include('jet.dashboard.urls', 'jet-dashboard')),
    url(r'^admin/', admin.site.urls),

    url(r'^rest/', include(router.urls)),
    url(r'^rest/', include(api_patterns, namespace='rest_api', app_name='mjtt')),

]
